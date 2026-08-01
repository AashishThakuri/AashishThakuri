"""Compile a reference image into a text-only animated SVG portrait."""

import argparse
import base64
import hashlib
import html
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


CHARACTERS = "  .`',:;i1tfLCG08@"
ROOT = Path(__file__).resolve().parent
SVG_WIDTH = 1600
SVG_HEIGHT = 1650
PORTRAIT_LEFT = 710
PORTRAIT_TOP = 18
PORTRAIT_WIDTH = 870
PORTRAIT_COLUMNS = 220
PORTRAIT_ROWS = 370
PORTRAIT_FONT_SIZE = 4.55
PORTRAIT_LINE_HEIGHT = 4.32


def image_rows(image_path):
    image = Image.open(image_path).convert("L")
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
  <animate attributeName="y" values="-30;1680" dur="{duration}s"
    begin="{begin}s" repeatCount="indefinite"/>
</text>'''
        )
    return "\n".join(streams)


def portrait_text(rows):
    """Render every portrait row as one continuous character field."""

    text_rows = []
    for index, row in enumerate(rows):
        y = PORTRAIT_TOP + PORTRAIT_FONT_SIZE + index * PORTRAIT_LINE_HEIGHT
        text_rows.append(
            f'<text x="{PORTRAIT_LEFT}" y="{y:.2f}" '
            f'textLength="{PORTRAIT_WIDTH}" lengthAdjust="spacingAndGlyphs" '
            f'class="portrait">{html.escape(row)}</text>'
        )
    return "".join(text_rows)


def profile_source_text():
    lines = [
        ("prompt", 60, 56, "aashish@github:~$ ./profile --from aashishthakuri.com"),
        ("name", 60, 145, "Aashish"),
        ("name", 60, 228, "Thakuri"),
        ("role", 64, 276, "DATA SCIENCE STUDENT / PRODUCT BUILDER"),
        ("muted", 64, 308, "KATHMANDU UNIVERSITY  ::  NEPAL  ::  UTC+05:45"),
        ("section", 60, 378, "01 / About me"),
        ("about", 64, 425, "I turn ideas into fast, accessible web interfaces"),
        ("about", 64, 455, "and reliable data applications."),
        ("about", 64, 500, "I care about performance, thoughtful micro-interactions,"),
        ("about", 64, 530, "and products that feel precise without feeling complicated."),
        ("section", 60, 610, "02 / Skills"),
        ("skill", 64, 660, "WEB      HTML / CSS / JAVASCRIPT / REACT / TAILWIND"),
        ("skill", 64, 700, "DATA     PYTHON / SQL / SUPABASE"),
        ("skill", 64, 740, "SYSTEMS  NODE.JS / VERCEL / AI"),
        ("section", 60, 825, "03 / What I think"),
        ("about", 64, 872, "Artificial Intelligence is more than technology to me."),
        ("about", 64, 902, "It is a way to reimagine how we interact with the world."),
        ("about", 64, 947, "I like challenges where design and engineering meet,"),
        ("about", 64, 977, "and where difficult mechanisms become understandable."),
        ("section", 60, 1062, "04 / Exploring now"),
        ("skill", 64, 1112, "GENERATIVE UI / RAG PATTERNS / LIGHTWEIGHT MLOPS"),
        ("about", 64, 1154, "The goal is to deploy intelligent systems responsibly."),
        ("section", 60, 1239, "05 / Beyond code"),
        ("about", 64, 1286, "Music and writing keep me creative."),
        ("about", 64, 1316, "I am always learning, testing, and refining."),
        ("section", 60, 1401, "06 / Principle"),
        ("quote", 64, 1455, "Remember, every model is a human opinion"),
        ("quote", 64, 1490, "embedded in mathematics."),
        ("prompt", 60, 1574, "aashish@github:~$ open --portfolio"),
        ("output", 60, 1612, "https://www.aashishthakuri.com/"),
    ]
    return "\n".join(
        f'<text x="{x}" y="{y}" class="{css_class}">{html.escape(text)}</text>'
        for css_class, x, y, text in lines
    )


def render_svg(rows, digest):
    inter_data = base64.b64encode(
        (ROOT / "assets" / "fonts" / "inter-latin.woff2").read_bytes()
    ).decode("ascii")
    playfair_data = base64.b64encode(
        (ROOT / "assets" / "fonts" / "playfair-display-latin.woff2").read_bytes()
    ).decode("ascii")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" role="img" aria-labelledby="title desc" xml:space="preserve">
<title id="title">Aashish Thakuri terminal profile</title>
<desc id="desc">A full developer profile beside a living high-density character portrait reconstructed entirely from terminal glyphs.</desc>
<style>
  @font-face {{ font-family: "Profile Sans"; src: url(data:font/woff2;base64,{inter_data}) format("woff2"); font-weight: 100 900; }}
  @font-face {{ font-family: "Profile Serif"; src: url(data:font/woff2;base64,{playfair_data}) format("woff2"); font-weight: 400 900; }}
  text {{ font-family: "Cascadia Mono", Consolas, "Courier New", monospace; letter-spacing: 0; white-space: pre; }}
  .portrait {{ fill: #f0f0ec; font-size: {PORTRAIT_FONT_SIZE}px; font-weight: 700; }}
  .stream {{ fill: #777772; font-size: 8px; opacity: 0.13; }}
  .prompt {{ fill: #aaa9a3; font-size: 15px; }}
  .name {{ font-family: "Profile Serif", Georgia, serif; fill: #f5f5f0; font-size: 76px; font-weight: 700; }}
  .role {{ font-family: "Profile Sans", Arial, sans-serif; fill: #deded8; font-size: 17px; font-weight: 700; }}
  .muted {{ fill: #777772; font-size: 13px; }}
  .section {{ font-family: "Profile Serif", Georgia, serif; fill: #f0f0eb; font-size: 28px; font-weight: 700; }}
  .about {{ font-family: "Profile Sans", Arial, sans-serif; fill: #d5d5cf; font-size: 18px; font-weight: 450; }}
  .skill {{ font-family: "Profile Sans", Arial, sans-serif; fill: #e7e7e1; font-size: 17px; font-weight: 650; }}
  .quote {{ font-family: "Profile Serif", Georgia, serif; fill: #ededE7; font-size: 24px; font-style: italic; }}
  .output {{ font-family: "Profile Sans", Arial, sans-serif; fill: #eeeeea; font-size: 18px; font-weight: 700; }}
</style>
<rect width="1600" height="1650" fill="#000000"/>
<rect x="18" y="18" width="1564" height="1614" fill="none" stroke="#30302e" stroke-width="1"/>
<g aria-label="slow falling code behind the portrait">
{background_streams(digest)}
</g>
<line x1="680" y1="42" x2="680" y2="1608" stroke="#343432" stroke-width="1"/>
<g aria-label="profile identity and capabilities written as terminal source">
{profile_source_text()}
</g>
<g aria-label="portrait reconstructed from terminal characters">
  <g aria-label="the complete character portrait breathing as one continuous field">
    <animateTransform attributeName="transform" type="translate"
      values="0 0;2.8 -3.0;0 0;-2.0 1.8;0 0" dur="14s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.965;1;0.982;1;0.965"
      dur="9s" begin="-2.7s" repeatCount="indefinite"/>
    {portrait_text(rows)}
  </g>
</g>
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
