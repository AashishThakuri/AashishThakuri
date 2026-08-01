"""KSHAM/1 compiler: typed capabilities become a living GitHub profile."""

import argparse
import hashlib
import html
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "profile.ksham"
ASSET_DIR = ROOT / "assets"
GARDEN_PATH = ASSET_DIR / "capability-garden.svg"
MAP_PATH = ASSET_DIR / "capability-grammar.svg"
README_PATH = ROOT / "README.md"

PAPER = "#f4efe5"
PAPER_DEEP = "#e5ddcf"
INK = "#181715"
INK_SOFT = "#575047"
BRANCH = "#59483d"
MOSS = "#596b4d"
ROSE = "#a94d62"
ROSE_LIGHT = "#d79aa7"
ROSE_PALE = "#e8c4ca"

TOKEN_RE = re.compile(
    r"(?P<space>\s+)|(?P<comment>//[^\n]*)|"
    r"(?P<string>\"(?:\\.|[^\"\\])*\")|"
    r"(?P<arrow>->)|(?P<pipe>\|>)|(?P<number>\d+)|"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_-]*)|(?P<punct>[{}\[\]:,])"
)


class KshamError(ValueError):
    """Base class for KSHAM compilation errors."""


class KshamSyntaxError(KshamError):
    """The source text does not follow the KSHAM/1 grammar."""


class KshamSemanticError(KshamError):
    """The source parses, but its capability graph is not valid."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


@dataclass(frozen=True)
class Capability:
    name: str
    input_type: str
    output_type: str
    statement: str
    tools: tuple


@dataclass(frozen=True)
class Composition:
    capabilities: tuple
    label: str


@dataclass(frozen=True)
class Garden:
    identifier: str
    name: str
    place: str
    role: str
    vow: str
    capabilities: tuple
    compositions: tuple


def lex(source):
    tokens = []
    position = 0
    line = 1
    column = 1

    while position < len(source):
        match = TOKEN_RE.match(source, position)
        if not match:
            excerpt = source[position : position + 20].splitlines()[0]
            raise KshamSyntaxError(
                f"Unexpected text at line {line}, column {column}: {excerpt!r}"
            )

        text = match.group(0)
        kind = match.lastgroup
        if kind not in {"space", "comment"}:
            tokens.append(Token(kind, text, line, column))

        newline_count = text.count("\n")
        if newline_count:
            line += newline_count
            column = len(text.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(text)
        position = match.end()

    tokens.append(Token("eof", "", line, column))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    @property
    def current(self):
        return self.tokens[self.index]

    def take(self, kind=None, value=None):
        token = self.current
        if kind and token.kind != kind:
            self.fail(f"expected {kind}, found {token.value!r}")
        if value and token.value != value:
            self.fail(f"expected {value!r}, found {token.value!r}")
        self.index += 1
        return token

    def fail(self, message):
        token = self.current
        raise KshamSyntaxError(
            f"Line {token.line}, column {token.column}: {message}"
        )

    def string(self):
        token = self.take("string")
        return json.loads(token.value)

    def string_list(self):
        values = []
        self.take("punct", "[")
        while self.current.value != "]":
            values.append(self.string())
            if self.current.value == ",":
                self.take("punct", ",")
            elif self.current.value != "]":
                self.fail("expected ',' or ']' in tool list")
        self.take("punct", "]")
        return tuple(values)

    def capability(self):
        self.take("name", "capability")
        name = self.take("name").value
        self.take("punct", ":")
        input_type = self.take("name").value
        self.take("arrow", "->")
        output_type = self.take("name").value
        self.take("punct", "{")

        statement = None
        tools = None
        while self.current.value != "}":
            field = self.take("name").value
            if field == "can":
                if statement is not None:
                    self.fail("duplicate 'can' field")
                statement = self.string()
            elif field == "using":
                if tools is not None:
                    self.fail("duplicate 'using' field")
                tools = self.string_list()
            else:
                self.fail(f"unknown capability field {field!r}")
        self.take("punct", "}")

        if statement is None or tools is None:
            self.fail(f"capability {name!r} requires 'can' and 'using'")
        return Capability(name, input_type, output_type, statement, tools)

    def composition(self):
        self.take("name", "compose")
        names = [self.take("name").value]
        while self.current.kind == "pipe":
            self.take("pipe", "|>")
            names.append(self.take("name").value)
        if len(names) < 2:
            self.fail("a composition requires at least two capabilities")
        self.take("name", "as")
        return Composition(tuple(names), self.string())

    def garden(self):
        self.take("name", "ksham")
        version = int(self.take("number").value)
        if version != 1:
            self.fail(f"unsupported KSHAM version {version}")

        self.take("name", "garden")
        identifier = self.take("name").value
        self.take("punct", "{")

        fields = {}
        capabilities = []
        compositions = []
        while self.current.value != "}":
            keyword = self.current.value
            if keyword in {"name", "place", "role", "vow"}:
                self.take("name")
                if keyword in fields:
                    self.fail(f"duplicate garden field {keyword!r}")
                fields[keyword] = self.string()
            elif keyword == "capability":
                capabilities.append(self.capability())
            elif keyword == "compose":
                compositions.append(self.composition())
            else:
                self.fail(f"unknown garden statement {keyword!r}")
        self.take("punct", "}")
        self.take("eof")

        missing = [name for name in ("name", "place", "role", "vow") if name not in fields]
        if missing:
            raise KshamSemanticError(
                f"Garden is missing required fields: {', '.join(missing)}"
            )
        return Garden(
            identifier,
            fields["name"],
            fields["place"],
            fields["role"],
            fields["vow"],
            tuple(capabilities),
            tuple(compositions),
        )


def parse(source):
    garden = Parser(lex(source)).garden()
    check_semantics(garden)
    return garden


def check_semantics(garden):
    if not garden.capabilities:
        raise KshamSemanticError("A garden requires at least one capability")
    if not garden.compositions:
        raise KshamSemanticError("A garden requires at least one composition")

    by_name = {}
    for capability in garden.capabilities:
        if capability.name in by_name:
            raise KshamSemanticError(
                f"Capability {capability.name!r} is declared more than once"
            )
        if not capability.tools:
            raise KshamSemanticError(
                f"Capability {capability.name!r} must name at least one tool"
            )
        by_name[capability.name] = capability

    used = set()
    for composition in garden.compositions:
        for name in composition.capabilities:
            if name not in by_name:
                raise KshamSemanticError(
                    f"Composition {composition.label!r} uses unknown capability {name!r}"
                )
            used.add(name)
        for left_name, right_name in zip(
            composition.capabilities, composition.capabilities[1:]
        ):
            left = by_name[left_name]
            right = by_name[right_name]
            if left.output_type != right.input_type:
                raise KshamSemanticError(
                    f"Cannot graft {left.name} |> {right.name}: "
                    f"{left.output_type!r} does not match {right.input_type!r}"
                )

    unused = sorted(set(by_name) - used)
    if unused:
        raise KshamSemanticError(
            f"Every capability must belong to a composition; unused: {', '.join(unused)}"
        )


def source_hash(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def esc(value):
    return html.escape(str(value), quote=True)


def split_lines(text, width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        candidate = " ".join(current + [word])
        if current and len(candidate) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def svg_text_lines(lines, x, y, line_height, css_class, anchor="start"):
    parts = [
        f'<text x="{x}" y="{y}" class="{css_class}" text-anchor="{anchor}">'
    ]
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_height
        parts.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


def blossom(x, y, scale, color=ROSE_LIGHT):
    """Draw the small vector blossom used by the capability map."""

    petal = "M0,-3 C-10,-16 -7,-29 0,-27 C7,-29 10,-16 0,-3 Z"
    petals = []
    for angle in (0, 72, 144, 216, 288):
        petals.append(
            f'<path d="{petal}" transform="rotate({angle})" fill="{color}"/>'
        )
    return (
        f'<g transform="translate({x} {y}) scale({scale})">'
        + "".join(petals)
        + f'<circle r="4" fill="{PAPER}"/><circle r="2" fill="{ROSE}"/></g>'
    )


def terminal_tree_characters(digest):
    """Build a deterministic cherry tree from terminal characters."""

    columns = 118
    rows = 35
    characters = [[" " for _ in range(columns)] for _ in range(rows)]
    colors = [["" for _ in range(columns)] for _ in range(rows)]
    priorities = [[-1 for _ in range(columns)] for _ in range(rows)]
    rng = random.Random(int(digest[:16], 16))

    def put(x, y, character, color, priority):
        if 0 <= x < columns and 0 <= y < rows and priority >= priorities[y][x]:
            characters[y][x] = character
            colors[y][x] = color
            priorities[y][x] = priority

    def draw_segment(start, end, width=0):
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy), 1)
        if abs(dx) < abs(dy) * 0.4:
            character = "|"
        elif abs(dy) < abs(dx) * 0.28:
            character = "_"
        elif dx * dy > 0:
            character = "\\"
        else:
            character = "/"

        for step in range(steps + 1):
            x = round(x1 + dx * step / steps)
            y = round(y1 + dy * step / steps)
            put(x, y, character, "bark", 3)
            for offset in range(1, width + 1):
                if abs(dy) >= abs(dx):
                    put(x - offset, y, "#", "bark-shadow", 2)
                    put(x + offset, y, "#", "bark-light", 2)
                else:
                    put(x, y - offset, "=", "bark-shadow", 2)
                    put(x, y + offset, "_", "bark-light", 2)

    blossom_fields = [
        (20, 12, 14, 6),
        (35, 7, 13, 5),
        (50, 6, 14, 5),
        (68, 5, 13, 5),
        (88, 8, 15, 6),
        (103, 13, 12, 6),
        (39, 14, 12, 5),
        (55, 11, 11, 5),
        (80, 13, 13, 5),
        (101, 24, 11, 5),
    ]
    blossom_characters = ["*", "*", "+", ".", "o", "@"]
    blossom_colors = ["blossom-pale", "blossom-soft", "blossom-deep"]

    for center_x, center_y, radius_x, radius_y in blossom_fields:
        for y in range(center_y - radius_y, center_y + radius_y + 1):
            for x in range(center_x - radius_x, center_x + radius_x + 1):
                distance = ((x - center_x) / radius_x) ** 2 + (
                    (y - center_y) / radius_y
                ) ** 2
                if distance > 1:
                    continue
                density = 0.18 + (1 - distance) * 0.34
                if rng.random() < density:
                    character = rng.choice(blossom_characters)
                    color = rng.choice(blossom_colors)
                    put(x, y, character, color, 1)

    trunk = [(79, 34), (77, 31), (74, 28), (72, 24), (69, 21), (68, 17), (66, 13), (68, 9)]
    branches = [
        (trunk, 2),
        ([(74, 28), (63, 25), (52, 22), (41, 19), (31, 16), (21, 12)], 1),
        ([(53, 22), (47, 18), (42, 13), (36, 8)], 0),
        ([(68, 17), (60, 14), (54, 10), (50, 6)], 0),
        ([(68, 17), (76, 15), (83, 12), (89, 8)], 0),
        ([(66, 13), (64, 10), (68, 5)], 0),
        ([(69, 21), (80, 20), (91, 17), (102, 13)], 0),
        ([(77, 31), (87, 29), (96, 26), (102, 23)], 0),
        ([(79, 34), (67, 34), (56, 32)], 0),
        ([(79, 34), (91, 34), (104, 32)], 0),
        ([(76, 33), (69, 31), (63, 29)], 0),
    ]
    for points, width in branches:
        for start, end in zip(points, points[1:]):
            draw_segment(start, end, width)

    for center_x, center_y, _radius_x, _radius_y in blossom_fields:
        put(center_x, center_y, "@", "blossom-pale", 4)
        put(center_x - 1, center_y, "*", "blossom-soft", 4)
        put(center_x + 1, center_y, "*", "blossom-soft", 4)

    runs = []
    x_start = 48
    y_start = 54
    character_width = 11.1
    line_height = 18.2
    for row in range(rows):
        column = 0
        while column < columns:
            if characters[row][column] == " ":
                column += 1
                continue
            color = colors[row][column]
            start = column
            text = []
            while column < columns and colors[row][column] == color and characters[row][column] != " ":
                text.append(characters[row][column])
                column += 1
            x = x_start + start * character_width
            y = y_start + row * line_height
            runs.append(
                f'<text x="{x:.1f}" y="{y:.1f}" class="ascii {color}">{esc("".join(text))}</text>'
            )
    return "\n".join(runs)


def terminal_falling_petals(digest):
    """Create continuously moving ASCII petals with staggered start times."""

    rng = random.Random(int(digest[16:32], 16))
    petals = []
    characters = ["*", "+", ".", "`", "'"]
    colors = ["#ead0d4", "#d6a0ab", "#b86f82"]
    for index in range(54):
        start_x = rng.randint(25, 1375)
        end_x = max(15, min(1385, start_x + rng.randint(-250, 170)))
        control_x_1 = max(15, min(1385, start_x + rng.randint(-130, 130)))
        control_x_2 = max(15, min(1385, end_x + rng.randint(-150, 150)))
        duration = rng.randint(10, 22)
        begin = -rng.randint(0, duration)
        font_size = rng.randint(13, 23)
        character = characters[index % len(characters)]
        color = colors[index % len(colors)]
        petals.append(
            f'''<text class="falling" font-size="{font_size}" fill="{color}">{esc(character)}
  <animateMotion path="M {start_x} -28 C {control_x_1} 210, {control_x_2} 500, {end_x} 760"
    dur="{duration}s" begin="{begin}s" repeatCount="indefinite" rotate="auto"/>
</text>'''
        )
    return "\n".join(petals)


def render_garden(garden, digest):
    tree = terminal_tree_characters(digest)
    petals = terminal_falling_petals(digest)
    scanlines = "".join(
        f'<line x1="22" y1="{y}" x2="1378" y2="{y}"/>' for y in range(36, 706, 20)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="720" viewBox="0 0 1400 720" role="img" aria-labelledby="title desc">
<title id="title">Animated terminal cherry blossom tree</title>
<desc id="desc">A cherry blossom tree drawn entirely with terminal characters while ASCII petals fall continuously.</desc>
<style>
  .ascii, .falling {{ font-family: "Cascadia Mono", Consolas, "Courier New", monospace; font-weight: 700; letter-spacing: 0; }}
  .ascii {{ font-size: 18px; }}
  .bark {{ fill: #9b8172; }}
  .bark-light {{ fill: #b19a8d; }}
  .bark-shadow {{ fill: #65544d; }}
  .blossom-pale {{ fill: #ead0d4; }}
  .blossom-soft {{ fill: #d6a0ab; }}
  .blossom-deep {{ fill: #a85f73; }}
  .falling {{ opacity: 0.9; }}
</style>
<rect width="1400" height="720" fill="#080a0a"/>
<rect x="18" y="18" width="1364" height="684" rx="4" fill="#101312" stroke="#3b3634" stroke-width="2"/>
<g stroke="#d9d1c5" stroke-width="1" opacity="0.035">{scanlines}</g>
<g aria-label="ASCII cherry blossom tree">
{tree}
</g>
<g aria-label="continuously falling ASCII petals">
{petals}
</g>
</svg>
'''


def pipeline_svg(composition, by_name, y, label):
    names = composition.capabilities
    count = len(names)
    margin = 170 if count >= 4 else 275
    start_x = margin
    end_x = 1400 - margin
    step = (end_x - start_x) / max(count - 1, 1)
    pieces = [
        f'<text x="70" y="{y - 88}" class="label">{esc(label.upper())}</text>',
        f'<line x1="{start_x}" y1="{y}" x2="{end_x}" y2="{y}" stroke="{PAPER_DEEP}" stroke-width="3"/>',
    ]

    for index, name in enumerate(names):
        capability = by_name[name]
        x = start_x + step * index
        pieces.append(f'<circle cx="{x:.1f}" cy="{y}" r="7" fill="{ROSE}"/>')
        pieces.append(blossom(f"{x:.1f}", y - 38, 0.34, ROSE_LIGHT))
        pieces.append(
            f'<text x="{x:.1f}" y="{y + 42}" class="cap" text-anchor="middle">'
            f'{esc(capability.name.upper())}</text>'
        )
        pieces.append(
            f'<text x="{x:.1f}" y="{y + 68}" class="type" text-anchor="middle">'
            f'{esc(capability.input_type)} -> {esc(capability.output_type)}</text>'
        )
        statement_lines = split_lines(capability.statement, 31)
        pieces.append(
            svg_text_lines(statement_lines, f"{x:.1f}", y + 104, 24, "statement", "middle")
        )
        tools = " / ".join(capability.tools)
        pieces.append(
            svg_text_lines(split_lines(tools, 34), f"{x:.1f}", y + 176, 21, "tools", "middle")
        )
        if index < count - 1:
            next_capability = by_name[names[index + 1]]
            midpoint = x + step / 2
            pieces.append(
                f'<text x="{midpoint:.1f}" y="{y - 13}" class="graft" text-anchor="middle">'
                f'{esc(capability.output_type)} = {esc(next_capability.input_type)}</text>'
            )
    return "".join(pieces)


def render_grammar(garden, digest):
    by_name = {capability.name: capability for capability in garden.capabilities}
    first = pipeline_svg(garden.compositions[0], by_name, 225, garden.compositions[0].label)
    second = pipeline_svg(garden.compositions[1], by_name, 620, garden.compositions[1].label)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="880" viewBox="0 0 1400 880" role="img" aria-labelledby="title desc">
<title id="title">KSHAM typed capability grammar</title>
<desc id="desc">Two valid capability compositions showing what Aashish can transform and the tools used.</desc>
<style>
  .label {{ font: 16px Consolas, "Courier New", monospace; fill: {ROSE}; letter-spacing: 0; }}
  .cap {{ font: 700 21px Inter, "Segoe UI", Arial, sans-serif; fill: {INK}; letter-spacing: 0; }}
  .type {{ font: 14px Consolas, "Courier New", monospace; fill: {INK_SOFT}; letter-spacing: 0; }}
  .statement {{ font: 17px Georgia, "Times New Roman", serif; fill: {INK}; letter-spacing: 0; }}
  .tools {{ font: 13px Consolas, "Courier New", monospace; fill: {INK_SOFT}; letter-spacing: 0; }}
  .graft {{ font: 12px Consolas, "Courier New", monospace; fill: {MOSS}; letter-spacing: 0; }}
</style>
<rect width="1400" height="880" fill="{PAPER}"/>
<text x="70" y="65" font-family="Georgia, serif" font-size="44" fill="{INK}">What I can transform</text>
<text x="1330" y="62" text-anchor="end" font-family="Consolas, monospace" font-size="13" fill="{INK_SOFT}">TYPE-CHECKED / {esc(digest[:12])}</text>
<line x1="70" y1="92" x2="1330" y2="92" stroke="{ROSE}" stroke-width="3"/>
{first}
<line x1="70" y1="470" x2="1330" y2="470" stroke="{PAPER_DEEP}" stroke-width="2"/>
{second}
<text x="70" y="842" font-family="Consolas, monospace" font-size="13" fill="{INK_SOFT}">A graft compiles only when the output type on the left equals the input type on the right.</text>
</svg>
'''


def capability_markdown(capability):
    tools = " ".join(f"`{tool}`" for tool in capability.tools)
    return (
        f"**{capability.name.upper()}**<br>\n"
        f"I can {capability.statement}.<br>\n"
        f"{tools}"
    )


def render_readme(garden, source):
    return f'''<p align="center">
  <img src="./assets/ascii-terminal-portrait.svg" width="100%" alt="Animated terminal profile and high-density character portrait for {garden.name}">
</p>
'''


def compile_profile(source_path=SOURCE_PATH):
    source = source_path.read_text(encoding="utf-8")
    garden = parse(source)
    digest = source_hash(source)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    GARDEN_PATH.write_text(render_garden(garden, digest), encoding="utf-8", newline="\n")
    MAP_PATH.write_text(render_grammar(garden, digest), encoding="utf-8", newline="\n")
    README_PATH.write_text(render_readme(garden, source), encoding="utf-8", newline="\n")
    return garden, digest


def run_tests():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    garden = parse(source)
    assert len(garden.capabilities) == 6
    assert len(garden.compositions) == 2

    broken = source.replace("capability reason: signal -> decision", "capability reason: noise -> decision")
    try:
        parse(broken)
    except KshamSemanticError as error:
        assert "does not match" in str(error)
    else:
        raise AssertionError("Type mismatch was not rejected")

    malformed = source.replace("ksham 1", "ksham ?", 1)
    try:
        parse(malformed)
    except KshamSyntaxError:
        pass
    else:
        raise AssertionError("Malformed source was not rejected")

    compile_profile()
    first = (GARDEN_PATH.read_bytes(), MAP_PATH.read_bytes(), README_PATH.read_bytes())
    compile_profile()
    second = (GARDEN_PATH.read_bytes(), MAP_PATH.read_bytes(), README_PATH.read_bytes())
    assert first == second, "Compiler output is not deterministic"
    assert b'repeatCount="indefinite"' in first[0]
    print("KSHAM tests passed")
    print("Lexer and parser: valid")
    print("Composition type mismatch: rejected")
    print("Deterministic compilation: valid")
    print("Continuous petal animation: present")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["build", "check", "test"], default="build")
    args = parser.parse_args()

    if args.command == "build":
        garden, digest = compile_profile()
        print(f"Compiled KSHAM profile for {garden.name}")
        print(f"Source SHA-256: {digest}")
    elif args.command == "check":
        source = SOURCE_PATH.read_text(encoding="utf-8")
        garden = parse(source)
        print(f"KSHAM source is valid: {len(garden.capabilities)} capabilities, {len(garden.compositions)} compositions")
    else:
        run_tests()


if __name__ == "__main__":
    main()
