"""KSHAM/1 compiler: typed capabilities become a living GitHub profile."""

import argparse
import hashlib
import html
import json
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


def falling_petals(garden, digest):
    palette = [ROSE, ROSE_LIGHT, ROSE_PALE, "#c9798b", "#e2adb7"]
    petals = []
    index = 0
    for capability_index, capability in enumerate(garden.capabilities):
        for tool in capability.tools:
            for copy_index in range(2):
                seed = hashlib.sha256(
                    f"{digest}:{capability.name}:{tool}:{copy_index}".encode("utf-8")
                ).digest()
                x = 20 + int.from_bytes(seed[0:2], "big") % 1360
                drift = -140 + int.from_bytes(seed[2:4], "big") % 281
                bend = -80 + int.from_bytes(seed[4:6], "big") % 161
                duration = 14 + (seed[6] % 12)
                begin = -(seed[7] % duration)
                rotation = 240 + int.from_bytes(seed[8:10], "big") % 540
                scale = 0.42 + (seed[10] % 60) / 100
                color = palette[(capability_index + copy_index) % len(palette)]
                petal_shape = (
                    "M0,15 C-7,10 -13,2 -9,-5 C-6,-11 -1,-9 0,-4 "
                    "C1,-9 6,-11 9,-5 C13,2 7,10 0,15 Z"
                )
                petals.append(
                    f'''<g transform="translate({x} 0)">
  <g>
    <animateTransform attributeName="transform" type="translate"
      values="0 -90; {bend} 330; {drift} 810" dur="{duration}s"
      begin="{begin}s" repeatCount="indefinite" calcMode="spline"
      keyTimes="0;0.52;1" keySplines="0.35 0 0.65 1;0.35 0 0.65 1"/>
    <g transform="scale({scale:.2f})">
      <path d="{petal_shape}" fill="{color}" opacity="0.82">
        <animateTransform attributeName="transform" type="rotate"
          values="0; {rotation // 2}; {rotation}" dur="{duration}s"
          begin="{begin}s" repeatCount="indefinite"/>
      </path>
    </g>
  </g>
</g>'''
                )
                index += 1
    return "\n".join(petals)


def render_garden(garden, digest):
    capability_names = [capability.name.upper() for capability in garden.capabilities]
    left_names = capability_names[:3]
    right_names = capability_names[3:]

    branch_points = [
        (1015, 185, 0.78),
        (1190, 245, 0.60),
        (940, 345, 0.67),
        (1235, 430, 0.82),
        (995, 535, 0.58),
        (1260, 600, 0.68),
    ]
    blossoms = "".join(
        blossom(x, y, scale, ROSE_LIGHT if i % 2 == 0 else ROSE_PALE)
        for i, (x, y, scale) in enumerate(branch_points)
    )

    ability_rows = []
    for index, capability in enumerate(garden.capabilities):
        x = 72 if index < 3 else 390
        y = 430 + (index % 3) * 58
        ability_rows.append(
            f'<text x="{x}" y="{y}" class="ability">{esc(capability.name.upper())}</text>'
            f'<text x="{x + 118}" y="{y}" class="type">'
            f'{esc(capability.input_type)} -> {esc(capability.output_type)}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="720" viewBox="0 0 1400 720" role="img" aria-labelledby="title desc">
<title id="title">KSHAM capability garden for {esc(garden.name)}</title>
<desc id="desc">A code-generated cherry blossom garden with continuously falling petals and six typed capabilities.</desc>
<style>
  .sans {{ font-family: Inter, "Segoe UI", Arial, sans-serif; letter-spacing: 0; }}
  .serif {{ font-family: Georgia, "Times New Roman", serif; letter-spacing: 0; }}
  .mono {{ font-family: Consolas, "Courier New", monospace; letter-spacing: 0; }}
  .ability {{ font: 700 19px Inter, "Segoe UI", Arial, sans-serif; fill: {INK}; letter-spacing: 0; }}
  .type {{ font: 15px Consolas, "Courier New", monospace; fill: {INK_SOFT}; letter-spacing: 0; }}
</style>
<rect width="1400" height="720" fill="{PAPER}"/>
<path d="M0 83 H1400 M0 681 H1400" stroke="{PAPER_DEEP}" stroke-width="2"/>
<text x="58" y="51" class="mono" font-size="15" fill="{ROSE}">KSHAM/1 :: CAPABILITY GARDEN</text>
<text x="1342" y="51" class="mono" font-size="14" text-anchor="end" fill="{INK_SOFT}">{esc(digest[:16])}</text>

<g fill="none" stroke="{BRANCH}" stroke-linecap="round">
  <path d="M1415 742 C1270 675 1185 620 1110 520 C1030 415 1080 302 985 178" stroke-width="18"/>
  <path d="M1180 620 C1115 570 1065 555 995 535" stroke-width="9"/>
  <path d="M1122 527 C1200 510 1230 475 1235 430" stroke-width="8"/>
  <path d="M1074 426 C1000 405 960 382 940 345" stroke-width="7"/>
  <path d="M1062 328 C1130 310 1175 280 1190 245" stroke-width="6"/>
  <path d="M1006 238 C1030 220 1025 198 1015 185" stroke-width="5"/>
</g>
<g fill="none" stroke="{MOSS}" stroke-width="3">
  <path d="M1175 619 C1135 600 1115 580 1098 548"/>
  <path d="M1119 526 C1160 500 1192 472 1208 438"/>
  <path d="M1076 426 C1034 397 990 370 951 350"/>
</g>
{blossoms}

<text x="58" y="158" class="serif" font-size="74" fill="{INK}">{esc(garden.name)}</text>
<text x="61" y="204" class="sans" font-size="20" fill="{INK_SOFT}">{esc(garden.role)}</text>
{svg_text_lines(split_lines(garden.vow, 48), 61, 278, 39, "serif")}
<line x1="61" y1="382" x2="690" y2="382" stroke="{ROSE}" stroke-width="4"/>
{''.join(ability_rows)}
<text x="61" y="655" class="mono" font-size="14" fill="{INK_SOFT}">{esc(garden.place)} / COMPILED FROM profile.ksham</text>

<g aria-label="continuously falling capability petals">
{falling_petals(garden, digest)}
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
    capability_sections = "\n\n".join(
        capability_markdown(capability) for capability in garden.capabilities
    )
    composition_lines = []
    for composition in garden.compositions:
        expression = " |> ".join(composition.capabilities)
        composition_lines.append(f"compose {expression} as \"{composition.label}\"")
    composition_source = "\n".join(composition_lines)
    example = garden.capabilities[0]
    example_tools = ", ".join(f'\"{tool}\"' for tool in example.tools)
    language_example = (
        f"capability {example.name}: {example.input_type} -> {example.output_type} {{\n"
        f"  can \"{example.statement}\"\n"
        f"  using [{example_tools}]\n"
        f"}}\n\n"
        f"{composition_source}"
    )

    return f'''<p align="center">
  <img src="./assets/capability-garden.svg" width="100%" alt="KSHAM capability garden for {garden.name}">
</p>

<p align="center">
  <strong>My profile begins with verbs.</strong><br>
  Here is what I can transform.
</p>

## KSHAM/1

KSHAM is a small capability language created for this profile. It introduces semantic botany: source code is compiled as a living plant. A capability has an input type, an output type, an outcome, and the tools that make it possible. Capabilities compose with `|>` only when their types match.

The cherry tree is the syntax tree. Its branches are parsed capabilities. Its blossoms come from the `using` declarations. Every continuously falling petal is deterministically generated from the source and its SHA-256 identity.

<img src="./assets/capability-grammar.svg" width="100%" alt="Typed KSHAM capability compositions">

## What I Can Do

{capability_sections}

## The Language

```ksham
{language_example}
```

The first composition means I can take raw human or camera input, turn it into a signal, reason over it, engineer a complete product, and shape that product into an experience. The second means I can turn a real-world question into a numerical mechanism and then make that mechanism understandable.

## Compile The Profile

```powershell
python ksham.py check
python ksham.py build
python ksham.py test
```

The human-edited source is [`profile.ksham`](./profile.ksham). The lexer, parser, semantic checker, composition type system, cherry-blossom animation, capability map, and README compiler are implemented in [`ksham.py`](./ksham.py) using only the Python standard library.

<p align="center">
  <sub>{garden.place} / {garden.vow}</sub>
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
