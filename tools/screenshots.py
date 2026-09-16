#!/usr/bin/env -S uv run python
"""Full-page screenshots of the site, and a check that no <pre> scrolls sideways.

A tool, not a gate: nothing in `make build` or CI runs it. Use it when a page's
look changed, to see the change at the widths and in the themes that matter,
before and after the push.

    uv run tools/screenshots.py --out ~/Desktop/digline-shots \\
        --page / --page /start/ --widths 1280,390 --themes light,dark

    # the live site instead of site/
    uv run tools/screenshots.py --base https://digline.dev --name-suffix=-live \\
        --out ~/Desktop/digline-shots --page / --widths 1280 --themes light

    # measure a width without keeping a picture of it
    uv run tools/screenshots.py --out /tmp/shots --page / --widths 1280,390 \\
        --measure-widths 900

What it does, for every page × width × theme:

  * serves site/ (or --site) on a free local port, or uses --base as it is;
  * opens the page in chrome-headless-shell, with prefers-color-scheme set to
    the theme, at deviceScaleFactor 1 (mobile emulation below 600px);
  * forces every lazy <img> to load and waits for each to decode, for the
    fonts, and for every CSS animation that ends, so a picture below the fold
    is not a blank box and an animated mark is where it settles;
  * measures scrollWidth and clientWidth of every <pre> inside <main> and prints
    both — a <pre> whose scrollWidth is larger scrolls sideways inside itself;
  * writes <page>-<width>-<theme><suffix>.png in --out, the full page, where
    <page> is "home" for / and the path's last segment otherwise.

--measure-widths adds widths that are measured but not photographed.

Exit status: 0 when every <pre> fits, 1 when one scrolls (the screenshots are
still written), 2 on a usage or browser error or an interruption, 3 on the
timeout.

The browser: --chrome, or $CHROME_HEADLESS_SHELL, or the one Playwright
installs (`npx playwright install chromium-headless-shell`) under
~/Library/Caches/ms-playwright or ~/.cache/ms-playwright. It is started with a
throwaway profile and a DevTools port of its own choosing; it is killed, and
the profile removed, on every way out — success, failure, Ctrl-C, SIGTERM and
the --timeout (default 120 s for the whole run).
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import functools
import glob
import http.server
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urljoin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAYWRIGHT_GLOBS = [
    "~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
    "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
]

# Every lazy image loads and decodes, the fonts are ready, and every CSS
# animation that ends has ended (the verdict card's run marker would otherwise
# be caught on its way). Endless ones and SVG's own SMIL are not waited for.
LOAD_EVERYTHING = """
Promise.all([...document.images].map(img => {
  img.loading = "eager";
  return img.decode().then(() => null, () => img.currentSrc || img.src);
})).then(failed => document.fonts.ready
  .then(() => Promise.all(document.getAnimations()
    .filter(a => a.effect && a.effect.getComputedTiming().endTime !== Infinity)
    .map(a => a.finished.catch(() => null))))
  .then(() => failed.filter(Boolean)))
"""

MEASURE_PRE = """
JSON.stringify([...document.querySelectorAll("main pre")].map((pre, index) => {
  const section = pre.closest("section[aria-labelledby], section[id], article, main");
  const where = section.getAttribute("aria-labelledby") || section.id || section.className || section.tagName.toLowerCase();
  return { index, where, cls: pre.className || "", scrollWidth: pre.scrollWidth, clientWidth: pre.clientWidth };
}))
"""


class Timeout(Exception):
    pass


def find_chrome(explicit: str | None) -> str:
    for candidate in [explicit, os.environ.get("CHROME_HEADLESS_SHELL")]:
        if candidate:
            if os.access(candidate, os.X_OK):
                return candidate
            raise SystemExit(f"screenshots: {candidate} is not an executable")
    found = sorted(p for g in PLAYWRIGHT_GLOBS for p in glob.glob(os.path.expanduser(g)))
    if not found:
        raise SystemExit("screenshots: no chrome-headless-shell; pass --chrome, set "
                         "CHROME_HEADLESS_SHELL, or `npx playwright install chromium-headless-shell`")
    return found[-1]


def serve(site: str) -> tuple[http.server.ThreadingHTTPServer, str]:
    handler = functools.partial(QuietHandler, directory=site)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".woff2": "font/woff2", ".svg": "image/svg+xml"}

    def log_message(self, *args):
        pass


class Browser:
    """chrome-headless-shell and one page target, over the DevTools protocol."""

    def __init__(self, chrome: str):
        self.profile = tempfile.mkdtemp(prefix="screenshots-profile-")
        self.process = subprocess.Popen(
            [chrome, "--remote-debugging-port=0", f"--user-data-dir={self.profile}",
             "--no-first-run", "--hide-scrollbars", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        )
        self.ws = None
        self.stack = contextlib.ExitStack()
        self.next_id = 0

    def connect(self) -> None:
        from urllib.request import urlopen
        from websockets.sync.client import connect

        port_file = os.path.join(self.profile, "DevToolsActivePort")
        for _ in range(100):
            if self.process.poll() is not None:
                raise RuntimeError(f"the browser exited with {self.process.returncode}")
            if os.path.exists(port_file):
                lines = open(port_file).read().split()
                if lines:
                    break
            time.sleep(0.1)
        else:
            raise RuntimeError("the browser never opened its DevTools port")
        targets = json.load(urlopen(f"http://127.0.0.1:{lines[0]}/json/list", timeout=10))
        page = next(t for t in targets if t["type"] == "page")
        self.ws = self.stack.enter_context(
            connect(page["webSocketDebuggerUrl"], max_size=None, open_timeout=10))
        self.send("Page.enable")

    def send(self, method: str, **params):
        self.next_id += 1
        mine = self.next_id
        self.ws.send(json.dumps({"id": mine, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == mine:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})

    def wait_for(self, event: str) -> None:
        while True:
            if json.loads(self.ws.recv()).get("method") == event:
                return

    def evaluate(self, expression: str):
        result = self.send("Runtime.evaluate", expression=expression,
                           awaitPromise=True, returnByValue=True)
        if "exceptionDetails" in result:
            raise RuntimeError(f"page script failed: {result['exceptionDetails']}")
        return result["result"].get("value")

    def open(self, url: str, width: int, theme: str) -> None:
        self.send("Emulation.setDeviceMetricsOverride", width=width, height=900,
                  deviceScaleFactor=1, mobile=width < 600)
        self.send("Emulation.setEmulatedMedia",
                  features=[{"name": "prefers-color-scheme", "value": theme}])
        # Page.navigate answers before the load event, so the event is read after.
        self.send("Page.navigate", url=url)
        self.wait_for("Page.loadEventFired")

    def close(self) -> None:
        try:
            self.stack.close()
        except Exception:
            pass
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        shutil.rmtree(self.profile, ignore_errors=True)


def page_name(path: str) -> str:
    segments = [s for s in path.split("?")[0].split("/") if s]
    return "home" if not segments else segments[-1].removesuffix(".html")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True, help="folder for the PNG files")
    parser.add_argument("--page", action="append", default=[], help="a path, e.g. / or /start/; repeatable")
    parser.add_argument("--widths", default="1280,390", help="comma-separated, photographed and measured")
    parser.add_argument("--measure-widths", default="", help="comma-separated, measured only")
    parser.add_argument("--themes", default="light,dark", help="light, dark, or both")
    parser.add_argument("--site", default=os.path.join(ROOT, "site"), help="the built site to serve")
    parser.add_argument("--base", help="a URL to use instead of serving --site, e.g. https://digline.dev")
    parser.add_argument("--name-suffix", default="", help="appended to each file name, e.g. --name-suffix=-live")
    parser.add_argument("--chrome", help="path to chrome-headless-shell")
    parser.add_argument("--timeout", type=int, default=120, help="seconds for the whole run")
    args = parser.parse_args(argv)

    pages = args.page or ["/"]
    widths = [int(w) for w in args.widths.split(",") if w]
    measured_only = [int(w) for w in args.measure_widths.split(",") if w]
    themes = [t for t in args.themes.split(",") if t]
    if any(t not in ("light", "dark") for t in themes):
        parser.error("--themes takes light and dark")
    if not args.base and not os.path.isfile(os.path.join(args.site, "index.html")):
        parser.error(f"{args.site} has no index.html; build first, or pass --base")
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)
    chrome = find_chrome(args.chrome)

    # The first signal starts the way out; any later one is ignored, so the
    # cleanup in `finally` is not itself interrupted.
    def leaving(error):
        def handler(signum, frame):
            for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, signal.SIG_IGN)
            raise error()
        return handler

    signal.signal(signal.SIGALRM, leaving(Timeout))
    signal.signal(signal.SIGTERM, leaving(KeyboardInterrupt))
    signal.signal(signal.SIGINT, leaving(KeyboardInterrupt))
    signal.alarm(args.timeout)

    server = None
    browser = None
    overflowing = 0
    try:
        if args.base:
            base = args.base.rstrip("/")
        else:
            server, base = serve(args.site)
        browser = Browser(chrome)
        browser.connect()
        stamp = int(time.time())
        jobs = [(p, w, t, True) for p in pages for w in widths for t in themes]
        jobs += [(p, w, themes[0], False) for p in pages for w in measured_only]
        for path, width, theme, photograph in jobs:
            url = urljoin(base + "/", path.lstrip("/"))
            url += ("&" if "?" in url else "?") + f"shot={stamp}-{width}-{theme}"
            browser.open(url, width, theme)
            failed = browser.evaluate(LOAD_EVERYTHING)
            if failed:
                print(f"screenshots: {path} {width}px: images that did not load: {failed}",
                      file=sys.stderr)
            for pre in json.loads(browser.evaluate(MEASURE_PRE)):
                scrolls = pre["scrollWidth"] > pre["clientWidth"]
                overflowing += scrolls
                print(f"pre  {path} {width}px {theme}  #{pre['index']} {pre['where']} "
                      f"{pre['cls'] or '(no class)'}: scrollWidth={pre['scrollWidth']} "
                      f"clientWidth={pre['clientWidth']}{'  SCROLLS' if scrolls else ''}")
            if not photograph:
                continue
            size = browser.send("Page.getLayoutMetrics")["cssContentSize"]
            height = int(-(-size["height"] // 1))
            shot = browser.send("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                                clip={"x": 0, "y": 0, "width": width, "height": height, "scale": 1})
            name = f"{page_name(path)}-{width}-{theme}{args.name_suffix}.png"
            target = os.path.join(out, name)
            with open(target, "wb") as fh:
                fh.write(base64.b64decode(shot["data"]))
            print(f"shot {target}  {width}x{height}  {os.path.getsize(target):,} bytes")
    except Timeout:
        print(f"screenshots: timed out after {args.timeout} s", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("screenshots: interrupted", file=sys.stderr)
        return 2
    except (RuntimeError, OSError, StopIteration) as error:
        print(f"screenshots: {error}", file=sys.stderr)
        return 2
    finally:
        signal.alarm(0)
        if browser:
            browser.close()
        if server:
            server.shutdown()
    if overflowing:
        print(f"screenshots: {overflowing} <pre> scroll sideways", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
