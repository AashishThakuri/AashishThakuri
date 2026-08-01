"""Compile a reference image into a text-only animated SVG portrait."""

import argparse
import hashlib
import html
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


CHARACTERS = "  .`',:;i1tfLCG08@"
SVG_WIDTH = 1400
SVG_HEIGHT = 820
PORTRAIT_LEFT = 560
PORTRAIT_TOP = 18
PORTRAIT_WIDTH = 820
PORTRAIT_COLUMNS = 190
PORTRAIT_ROWS = 174
PORTRAIT_FONT_SIZE = 4.9
PORTRAIT_LINE_HEIGHT = 4.52


def image_rows(image_path):
    image = Image.open(image_path).convert("L")
    crop_left = round(image.width * 0.12)
    crop_bottom = round(image.height * 0.62)
    image = image.crop((crop_left, 0, image.width, crop_bottom))
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.22)
    sampled = image.resize(
        (PORTRAIT_COLUMNS, PORTRAIT_ROWS),
        Image.Resampling.LANCZOS,
    )

    output = []
    for y in range(PORTRAIT_ROWS):
        line = []
        for x in range(PORTRAIT_COLUMNS):
            value = sampled.getpixel((x, y))
            normalized = (value / 255) ** 0.78
            index = min(round(normalized * (len(CHARACTERS) - 1)), len(CHARACTERS) - 1)
            line.append(CHARACTERS[index])
        output.append("".join(line))
    return output


def background_streams(digest):
    rng = random.Random(int(digest[:16], 16))
    symbols = ["01", "{}", "[]", "//", "::", "if", "fn", "&&", "||", "<>"]
    streams = []
    for index in range(42):
        x = rng.randint(18, SVG_WIDTH - 30)
        duration = rng.randint(11, 25)
        begin = -rng.randint(0, duration)
        symbol = symbols[index % len(symbols)]
        streams.append(
            f'''<text x="{x}" y="-30" class="stream">{html.escape(symbol)}
  <animate attributeName="y" values="-30;850" dur="{duration}s"
    begin="{begin}s" repeatCount="indefinite"/>
</text>'''
        )
    return "\n".join(streams)


def profile_source_text():
    lines = [
        ("prompt", 54, 52, "aashish@github:~$ ./identity --verbose"),
        ("name", 54, 116, "AASHISH"),
        ("name", 54, 169, "THAKURI"),
        ("role", 57, 207, "FULL-STACK ENGINEER / APPLIED AI BUILDER"),
        ("muted", 57, 234, "KATHMANDU, NEPAL  ::  UTC+05:45"),
        ("rule", 54, 274, "01  CAPABILITIES {"),
        ("code", 76, 309, 'product     : "interface -> api -> database";'),
        ("code", 76, 339, 'vision      : "camera -> gesture -> interaction";'),
        ("code", 76, 369, 'intelligence: "signal -> model -> decision";'),
        ("code", 76, 399, 'simulation  : "question -> numerical system";'),
        ("code", 76, 429, 'explanation : "complexity -> visible mechanism";'),
        ("rule", 54, 459, "}"),
        ("rule", 54, 506, "02  STACK [ACTIVE] {"),
        ("code", 76, 541, "PYTHON      TYPESCRIPT    REACT"),
        ("code", 76, 571, "FASTAPI     MYSQL         OPENCV"),
        ("code", 76, 601, "MEDIAPIPE   NUMPY         PANDAS"),
        ("code", 76, 631, "THREE.JS    GSAP          CSS"),
        ("rule", 54, 661, "}"),
        ("prompt", 54, 713, "aashish@github:~$ transform --input idea"),
        ("output", 54, 751, "> WORKING SYSTEM / CLEAR INTERFACE / EXPLAINABLE CORE"),
        ("muted", 54, 790, "github.com/AashishThakuri  ::  LEARN / BUILD / SHIP"),
    ]
    return "\n".join(
        f'<text x="{x}" y="{y}" class="{css_class}">{html.escape(text)}</text>'
        for css_class, x, y, text in lines
    )


def render_svg(rows, digest):
    text_rows = []
    for index, row in enumerate(rows):
        y = PORTRAIT_TOP + PORTRAIT_FONT_SIZE + index * PORTRAIT_LINE_HEIGHT
        text_rows.append(
            f'<text x="{PORTRAIT_LEFT}" y="{y:.2f}" textLength="{PORTRAIT_WIDTH}" '
            f'lengthAdjust="spacingAndGlyphs" class="portrait">{html.escape(row)}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" role="img" aria-labelledby="title desc" xml:space="preserve">
<title id="title">Aashish Thakuri terminal profile</title>
<desc id="desc">A full developer profile in terminal syntax beside a supplied portrait reconstructed entirely from high-density monospace characters.</desc>
<style>
  text {{ font-family: "Cascadia Mono", Consolas, "Courier New", monospace; letter-spacing: 0; white-space: pre; }}
  .portrait {{ fill: #f0f0ec; font-size: {PORTRAIT_FONT_SIZE}px; font-weight: 700; }}
  .stream {{ fill: #777772; font-size: 8px; opacity: 0.13; }}
  .prompt {{ fill: #c4c4be; font-size: 15px; }}
  .name {{ fill: #f5f5f0; font-size: 49px; font-weight: 700; }}
  .role {{ fill: #deded8; font-size: 15px; font-weight: 700; }}
  .muted {{ fill: #777772; font-size: 12px; }}
  .rule {{ fill: #b0b0aa; font-size: 14px; font-weight: 700; }}
  .code {{ fill: #d0d0ca; font-size: 13px; }}
  .output {{ fill: #eeeeea; font-size: 13px; font-weight: 700; }}
</style>
<rect width="1400" height="820" fill="#000000"/>
<rect x="18" y="18" width="1364" height="784" fill="none" stroke="#30302e" stroke-width="1"/>
<g aria-label="slow falling code behind the portrait">
{background_streams(digest)}
</g>
<line x1="526" y1="42" x2="526" y2="778" stroke="#343432" stroke-width="1"/>
<g aria-label="profile identity and capabilities written as terminal source">
{profile_source_text()}
</g>
<g aria-label="portrait reconstructed from terminal characters">
{''.join(text_rows)}
</g>
<line x1="20" y1="0" x2="1380" y2="0" stroke="#ffffff" stroke-width="1" opacity="0.16">
  <animate attributeName="y1" values="0;820" dur="10s" repeatCount="indefinite"/>
  <animate attributeName="y2" values="0;820" dur="10s" repeatCount="indefinite"/>
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
