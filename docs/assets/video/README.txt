# The video assets

Served from this site and from nowhere else: no YouTube, no Vimeo, no embedded
player, no third-party script. `docs/start.md` references these files directly
in a raw `<video>` element, and mkdocs copies them into `site/` like any other
asset.

## Expected files

| File               | What it is                                  |
| ------------------ | ------------------------------------------- |
| `ep01.mp4`         | Episode 1, the video itself                 |
| `ep01-poster.jpg`  | The still shown before anyone presses play  |

The names in `docs/start.md` are these ones. A file delivered under a different
name is a file the page will not find — rename it here rather than editing the
page in two places.

## Encoding target

- **Video** — H.264, 720p, 2–3 Mbps, so that the file stays around 10 MB per
  episode. GitHub Pages refuses anything over 100 MB, and a reader on a phone
  pays for every one of them.
- **Audio** — AAC.
- **Poster** — JPG, under 100 KB. It is fetched on page load; the video is not,
  because the element carries `preload="none"`.
