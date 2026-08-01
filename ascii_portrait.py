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
SVG_WIDTH = 1900
SVG_HEIGHT = 2150
PORTRAIT_LEFT = 820
PORTRAIT_TOP = 18
PORTRAIT_WIDTH = 1060
PORTRAIT_COLUMNS = 260
PORTRAIT_ROWS = 485
PORTRAIT_FONT_SIZE = 4.45
PORTRAIT_LINE_HEIGHT = 4.36


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
    for index in range(56):
        x = rng.randint(18, SVG_WIDTH - 30)
        duration = rng.randint(11, 25)
        begin = -rng.randint(0, duration)
        symbol = symbols[index % len(symbols)]
        streams.append(
            f'''<text x="{x}" y="-30" class="stream">{html.escape(symbol)}
  <animate attributeName="y" values="-30;{SVG_HEIGHT + 30}" dur="{duration}s"
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


def animated_skill_icons(digest):
    """Render a monochrome terminal icon grid with staggered motion."""

    rng = random.Random(int(digest[16:32], 16))
    skills = [
        ("HTML", "</>"),
        ("CSS", "{ }"),
        ("JAVASCRIPT", "JS"),
        ("REACT", "(*)"),
        ("PYTHON", "Py"),
        ("SQL", "[=]"),
        ("TAILWIND", "~~"),
        ("SUPABASE", "//"),
        ("NODE", "N"),
        ("AI", "o-o"),
    ]
    icons = []

    for index, (label, mark) in enumerate(skills):
        column = index % 5
        row = index // 5
        x = 68 + column * 140
        y = 800 + row * 148
        duration = rng.uniform(4.8, 7.5)
        begin = -rng.uniform(0, duration)
        icons.append(
            f'''<g transform="translate({x} {y})" aria-label="{label} skill icon">
  <g>
    <rect x="0" y="0" width="118" height="118" rx="3" class="skill-frame"
      stroke-dasharray="13 8">
      <animate attributeName="stroke-dashoffset" values="0;-42" dur="{duration:.2f}s"
        begin="{begin:.2f}s" repeatCount="indefinite"/>
    </rect>
    <text x="59" y="54" text-anchor="middle" class="skill-mark">{html.escape(mark)}</text>
    <line x1="18" y1="72" x2="100" y2="72" class="skill-rule"/>
    <text x="59" y="98" text-anchor="middle" class="skill-label">{label}</text>
    <animateTransform attributeName="transform" type="translate"
      values="0 0;0 -6;0 0;0 3;0 0" dur="{duration:.2f}s"
      begin="{begin:.2f}s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.76;1;0.88;1;0.76"
      dur="{duration * 1.16:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/>
  </g>
</g>'''
        )

    return "\n".join(icons)


def portrait_particles(digest):
    """Move loose terminal fragments around the portrait's face and hands."""

    rng = random.Random(int(digest[32:48], 16))
    symbols = ["0", "1", "{", "}", "/", ";", "+", "<", ">", "::"]
    regions = [
        (930, 210, 1320, 620),
        (1030, 590, 1610, 1030),
        (1390, 330, 1790, 900),
    ]
    particles = []

    for index in range(34):
        left, top, right, bottom = regions[index % len(regions)]
        x = rng.randint(left, right)
        y = rng.randint(top, bottom)
        dx = rng.randint(-90, 110)
        dy = rng.randint(150, 390)
        bend = rng.randint(-90, 90)
        duration = rng.uniform(7.0, 15.0)
        begin = -rng.uniform(0, duration)
        symbol = symbols[index % len(symbols)]
        particles.append(
            f'''<text x="{x}" y="{y}" class="portrait-particle" opacity="0">{html.escape(symbol)}
  <animateMotion path="M 0 0 C {bend} {dy * 0.32:.1f}, {dx - bend} {dy * 0.68:.1f}, {dx} {dy}"
    dur="{duration:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/>
  <animate attributeName="opacity" values="0;0.48;0.24;0"
    keyTimes="0;0.18;0.76;1" dur="{duration:.2f}s" begin="{begin:.2f}s"
    repeatCount="indefinite"/>
</text>'''
        )

    return "\n".join(particles)


def profile_source_text():
    lines = [
        ("prompt", 68, 66, "aashish@github:~$ ./profile --from aashishthakuri.com"),
        ("name", 68, 164, "Aashish"),
        ("name", 68, 258, "Thakuri"),
        ("role", 72, 316, "DATA SCIENCE STUDENT / PRODUCT BUILDER"),
        ("muted", 72, 352, "KATHMANDU UNIVERSITY  ::  NEPAL  ::  UTC+05:45"),
        ("section", 68, 430, "01 / About me"),
        ("about", 72, 482, "I see every interface as a piece of art with a purpose."),
        ("about", 72, 520, "I love turning symbols, stories, and ideas into visual language,"),
        ("about", 72, 558, "then building them into websites people can feel and understand."),
        ("about", 72, 610, "For me, design is never decoration."),
        ("about", 72, 648, "Every line, movement, and interaction should symbolize something"),
        ("about", 72, 686, "and make the experience more human, memorable, and meaningful."),
        ("section", 68, 758, "02 / Languages and tools"),
        ("section", 68, 1152, "03 / What I think"),
        ("about", 72, 1204, "Technology should not flatten creativity; it should give ideas form."),
        ("about", 72, 1242, "I build to make difficult systems visible, intuitive, and expressive."),
        ("about", 72, 1294, "I want every interaction to carry intention, not just function."),
        ("section", 68, 1380, "04 / Exploring now"),
        ("skill", 72, 1434, "GENERATIVE UI / RAG PATTERNS / LIGHTWEIGHT MLOPS"),
        ("about", 72, 1478, "I am exploring how intelligent systems can become useful creative material."),
        ("section", 68, 1570, "05 / Beyond code"),
        ("about", 72, 1622, "Music and writing keep my imagination moving."),
        ("about", 72, 1660, "I am always observing, learning, testing, and refining."),
        ("section", 68, 1752, "06 / Principle"),
        ("quote", 72, 1812, "Every interface can carry a symbol."),
        ("quote", 72, 1854, "Every interaction can tell part of the story."),
        ("prompt", 68, 2048, "aashish@github:~$ open --portfolio"),
        ("output", 68, 2094, "https://www.aashishthakuri.com/"),
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
<desc id="desc">An expanded developer profile with animated skill symbols beside a living high-density character portrait reconstructed entirely from terminal glyphs.</desc>
<defs>
  <linearGradient id="portrait-sheen" gradientUnits="userSpaceOnUse"
    x1="{PORTRAIT_LEFT - 430}" y1="0" x2="{PORTRAIT_LEFT - 40}" y2="0">
    <stop offset="0" stop-color="#000000"/>
    <stop offset="0.5" stop-color="#ffffff"/>
    <stop offset="1" stop-color="#000000"/>
    <animate attributeName="x1" values="{PORTRAIT_LEFT - 430};{SVG_WIDTH + 80}"
      dur="13s" begin="-3.4s" repeatCount="indefinite"/>
    <animate attributeName="x2" values="{PORTRAIT_LEFT - 40};{SVG_WIDTH + 470}"
      dur="13s" begin="-3.4s" repeatCount="indefinite"/>
  </linearGradient>
  <mask id="portrait-sheen-mask">
    <rect x="{PORTRAIT_LEFT - 20}" y="0" width="{PORTRAIT_WIDTH + 40}"
      height="{SVG_HEIGHT}" fill="url(#portrait-sheen)"/>
  </mask>
</defs>
<style>
  @font-face {{ font-family: "Profile Sans"; src: url(data:font/woff2;base64,{inter_data}) format("woff2"); font-weight: 100 900; }}
  @font-face {{ font-family: "Profile Serif"; src: url(data:font/woff2;base64,{playfair_data}) format("woff2"); font-weight: 400 900; }}
  text {{ font-family: "Cascadia Mono", Consolas, "Courier New", monospace; letter-spacing: 0; white-space: pre; }}
  .portrait {{ fill: #f0f0ec; font-size: {PORTRAIT_FONT_SIZE}px; font-weight: 700; }}
  .stream {{ fill: #777772; font-size: 9px; opacity: 0.13; }}
  .portrait-particle {{ fill: #f2f2ed; font-size: 11px; font-weight: 700; }}
  .prompt {{ fill: #aaa9a3; font-size: 17px; }}
  .name {{ font-family: "Profile Serif", Georgia, serif; fill: #f5f5f0; font-size: 92px; font-weight: 700; }}
  .role {{ font-family: "Profile Sans", Arial, sans-serif; fill: #deded8; font-size: 20px; font-weight: 700; }}
  .muted {{ fill: #777772; font-size: 14px; }}
  .section {{ font-family: "Profile Serif", Georgia, serif; fill: #f0f0eb; font-size: 32px; font-weight: 700; }}
  .about {{ font-family: "Profile Sans", Arial, sans-serif; fill: #d5d5cf; font-size: 20px; font-weight: 450; }}
  .skill {{ font-family: "Profile Sans", Arial, sans-serif; fill: #e7e7e1; font-size: 19px; font-weight: 650; }}
  .quote {{ font-family: "Profile Serif", Georgia, serif; fill: #edede7; font-size: 28px; font-style: italic; }}
  .output {{ font-family: "Profile Sans", Arial, sans-serif; fill: #eeeeea; font-size: 21px; font-weight: 700; }}
  .skill-frame {{ fill: #050505; stroke: #5f5f5a; stroke-width: 1.5; }}
  .skill-rule {{ stroke: #4a4a46; stroke-width: 1; }}
  .skill-mark {{ fill: #f3f3ee; font-size: 27px; font-weight: 700; }}
  .skill-label {{ font-family: "Profile Sans", Arial, sans-serif; fill: #cfcfc9; font-size: 13px; font-weight: 700; }}
</style>
<rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="#000000"/>
<rect x="18" y="18" width="{SVG_WIDTH - 36}" height="{SVG_HEIGHT - 36}" fill="none" stroke="#30302e" stroke-width="1"/>
<g aria-label="slow falling code behind the portrait">
{background_streams(digest)}
</g>
<line x1="790" y1="48" x2="790" y2="2102" stroke="#343432" stroke-width="1"/>
<g aria-label="profile identity and capabilities written as terminal source">
{profile_source_text()}
{animated_skill_icons(digest)}
</g>
<g aria-label="portrait reconstructed from terminal characters">
  <g aria-label="the complete character portrait breathing as one continuous field">
    <animateTransform attributeName="transform" type="translate"
      values="0 0;2.8 -3.0;0 0;-2.0 1.8;0 0" dur="14s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.965;1;0.982;1;0.965"
      dur="9s" begin="-2.7s" repeatCount="indefinite"/>
    {portrait_text(rows)}
    <g mask="url(#portrait-sheen-mask)" opacity="0.34" aria-label="soft character light moving through the portrait">
      {portrait_text(rows)}
    </g>
  </g>
  <g aria-label="terminal fragments moving around the living portrait">
    {portrait_particles(digest)}
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
