"""This site's own assets, linked with a hash of their content.

A browser, and the CDN in front of GitHub Pages, keep a stylesheet or a font
for as long as they like. A change to pages.css that reaches the server can
sit behind yesterday's copy for hours, and a page then draws today's markup
with yesterday's rules. So every asset this repository writes — the
stylesheets in docs/assets/ and the Plex subsets in docs/assets/fonts/ — is
linked as ``<path>?v=<hash>``, the hash taken from the file's content at build
time. A changed file is a new URL; an unchanged one keeps its cache.

  * the stylesheets Material loads, mkdocs.yml's ``extra_css``, get the query
    here, in ``on_config``;
  * the presentation pages link theirs through the ``versioned`` filter, in
    overrides/_shell.html;
  * the fonts are linked from fonts.css, which is rewritten on its way into
    site/ with each ``url(fonts/….woff2)`` versioned. Its own hash is the hash
    of what is served, so a new font is also a new fonts.css.

The source files are not touched: docs/assets/fonts.css keeps its plain URLs,
which tools/subset-fonts.py and tools/check-glyphs.py read.

tools/check-assets.py checks the result after the build: every link to one of
these assets carries a hash, and the hash is the file's.

Material's own assets are not this hook's business: their names already carry
a hash (main.<hash>.min.css). The site has no script file of its own; its
scripts are inline.
"""

from __future__ import annotations

import hashlib
import os
import re

from mkdocs.exceptions import PluginError

ASSETS = "assets"
FONTS_CSS = "assets/fonts.css"
_FONT_URL = re.compile(r"""url\(\s*(["']?)(fonts/[^"')?#]+\.woff2)\1\s*\)""")

# path under docs/ → hash; and fonts.css as it is served.
_versions: dict[str, str] = {}
_fonts_css: str | None = None


def digest(data: bytes) -> str:
    """Twelve hex digits of the content's SHA-256: enough to tell two versions
    of a file apart, short enough to read in a URL."""
    return hashlib.sha256(data).hexdigest()[:12]


def versioned_fonts_css(css: str, font_hash) -> str:
    """fonts.css with every url(fonts/….woff2) carrying its font's hash."""
    def replace(match):
        quote, path = match.group(1), match.group(2)
        return f"url({quote}{path}?v={font_hash(path)}{quote})"
    return _FONT_URL.sub(replace, css)


def compute(docs_dir: str) -> tuple[dict[str, str], str]:
    """The hash of every own stylesheet and font, and fonts.css as served."""
    versions: dict[str, str] = {}
    assets = os.path.join(docs_dir, ASSETS)
    for folder, _, names in os.walk(assets):
        for name in sorted(names):
            if name.endswith((".woff2", ".css")):
                path = os.path.join(folder, name)
                with open(path, "rb") as fh:
                    versions[os.path.relpath(path, docs_dir).replace(os.sep, "/")] = digest(fh.read())

    def font_hash(url_path: str) -> str:
        key = f"{ASSETS}/{url_path}"
        if key not in versions:
            raise PluginError(f"assets: fonts.css links {url_path}, which docs/{key} does not have.")
        return versions[key]

    with open(os.path.join(docs_dir, FONTS_CSS), encoding="utf-8") as fh:
        served = versioned_fonts_css(fh.read(), font_hash)
    versions[FONTS_CSS] = digest(served.encode("utf-8"))
    return versions, served


def versioned(path: str) -> str:
    """``assets/pages.css`` as ``assets/pages.css?v=<hash>``."""
    if path not in _versions:
        raise PluginError(
            f"assets: {path} is linked as one of this site's own assets, and docs/{path} "
            "does not exist."
        )
    return f"{path}?v={_versions[path]}"


def on_config(config, **kwargs):
    global _fonts_css
    versions, served = compute(config["docs_dir"])
    _versions.clear()
    _versions.update(versions)
    _fonts_css = served
    config["extra_css"] = [versioned(str(path).split("?")[0]) for path in config["extra_css"]]
    return config


def on_env(env, config, files, **kwargs):
    env.filters["versioned"] = versioned
    return env


def on_post_build(config, **kwargs):
    """fonts.css as served: the one mkdocs copied, with its fonts versioned."""
    with open(os.path.join(config["site_dir"], FONTS_CSS), "w", encoding="utf-8") as fh:
        fh.write(_fonts_css)
