"""Code is not prose: every <pre> and <code> a page renders says so.

A browser that translates a page — Chrome's own translation, a reader's
extension — translates every text node it is not told to leave alone, and code
is text. `pip install digline` comes back as an instruction in Italian, a
command name as a verb, an output line as a sentence nobody's terminal ever
printed. The HTML attribute ``translate="no"`` is how a page tells it not to,
and what it covers is kept exactly as written.

This hook puts it on every ``<pre>`` and ``<code>`` in the rendered Markdown of
every page — the documentation Material renders and the reading pages alike,
the code blocks Pygments writes included — in ``on_page_content``, before any
other hook or template sees the HTML. A tag that already carries a
``translate`` attribute is left as it is.

What the templates in overrides/ write themselves is not rendered Markdown, and
carries the attribute in the template: on the home, the install command, the
command names, the output and the terminal, the packages and the image in the
stack band, the names of the checks and the ids of the cases; in the bar, the
"digline" of the brand.

tools/check-translate.py checks the result after the build: no <pre> and no
<code> in site/ without ``translate="no"``, and ``<html lang="en">`` on every
page.
"""

from __future__ import annotations

import re

# The opening tag of a <pre> or a <code>, with no translate attribute of its
# own. Code inside them is escaped (&lt;code&gt;), so only real tags match.
_TAG = re.compile(r"<(pre|code)\b(?![^>]*\btranslate=)", re.I)


def no_translate(html: str) -> str:
    """Every <pre> and <code> opening tag in ``html`` with translate="no"."""
    return _TAG.sub(lambda m: f'<{m.group(1)} translate="no"', html)


def on_page_content(html, page, config, files, **kwargs):
    return no_translate(html)
