"""Compile a reference image into a text-only animated SVG portrait."""

import argparse
import hashlib
import html
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


CHARACTERS = "  .`',:;i1tfLCG08@"
SVG_WIDTH = 1000
SVG_HEIGHT = 1760
TEXT_LEFT = 20
TEXT_TOP = 24
TEXT_WIDTH = 960
COLUMNS = 160
FONT_SIZE = 10.2
LINE_HEIGHT = 10.65


def image_rows(image_path):
    image = Image.open(image_path).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.18)

    character_width = TEXT_WIDTH / COLUMNS
    character_aspect = character_width / LINE_HEIGHT
    rows = round((image.height / image.width) * COLUMNS * character_aspect)
    sampled = image.resize((COLUMNS, rows), Image.Resampling.LANCZOS)

    output = []
    for y in range(rows):
        line = []
        for x in range(COLUMNS):
            value = sampled.getpixel((x, y))
            normalized = (value / 255) ** 0.82
            index = min(round(normalized * (len(CHARACTERS) - 1)), len(CHARACTERS) - 1)
            line.append(CHARACTERS[index])
        output.append("".join(line))
    return output


def background_streams(digest):
    rng = random.Random(int(digest[:16], 16))
    symbols = ["01", "{}", "[]", "//", "::", "if", "fn", "&&", "||", "<>" ]
    streams = []
    for index in range(30):
        x = rng.randint(18, SVG_WIDTH - 30)
        duration = rng.randint(13, 27)
        begin = -rng.randint(0, duration)
        symbol = symbols[index % len(symbols)]
        streams.append(
            f'''<text x="{x}" y="-30" class="stream">{html.escape(symbol)}
  <animate attributeName="y" values="-30;1790" dur="{duration}s"
    begin="{begin}s" repeatCount="indefinite"/>
</text>'''
        )
    return "\n".join(streams)


def render_svg(rows, digest):
    text_rows = []
    for index, row in enumerate(rows):
        y = TEXT_TOP + FONT_SIZE + index * LINE_HEIGHT
        text_rows.append(
            f'<text x="{TEXT_LEFT}" y="{y:.2f}" textLength="{TEXT_WIDTH}" '
            f'lengthAdjust="spacingAndGlyphs" class="portrait">{html.escape(row)}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" role="img" aria-labelledby="title desc" xml:space="preserve">
<title id="title">Live terminal character portrait</title>
<desc id="desc">A supplied monochrome portrait reconstructed entirely from terminal characters with slow background code motion.</desc>
<style>
  .portrait, .stream {{ font-family: "Cascadia Mono", Consolas, "Courier New", monospace; letter-spacing: 0; white-space: pre; }}
  .portrait {{ fill: #f1f1ed; font-size: {FONT_SIZE}px; font-weight: 700; }}
  .stream {{ fill: #777772; font-size: 9px; opacity: 0.20; }}
</style>
<rect width="1000" height="1760" fill="#000000"/>
<g aria-label="slow falling code behind the portrait">
{background_streams(digest)}
</g>
<g aria-label="portrait reconstructed from terminal characters">
{''.join(text_rows)}
</g>
<line x1="12" y1="0" x2="988" y2="0" stroke="#ffffff" stroke-width="1" opacity="0.22">
  <animate attributeName="y1" values="0;1760" dur="11s" repeatCount="indefinite"/>
  <animate attributeName="y2" values="0;1760" dur="11s" repeatCount="indefinite"/>
</line>
</svg>
'''


def compile_portrait(input_path, output_path):
    source = Path(input_path).read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    rows = image_rows(input_path)
    svg = render_svg(rows, digest)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(svg, encoding="utf-8", newline="\n")
    return len(rows), digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows, digest = compile_portrait(args.input, args.output)
    print(f"Compiled {rows} rows of live ASCII portrait")
    print(f"Source SHA-256: {digest}")


if __name__ == "__main__":
    main()
