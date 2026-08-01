"""Build and verify the BIFORM self-carrying GitHub profile artifact."""

import argparse
import hashlib
import io
import json
import re
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "identity.biform"
ASSET_DIR = ROOT / "assets"
EXHIBIT_DIR = ASSET_DIR / "exhibits"
ARTIFACT_PATH = ASSET_DIR / "aashish.biform.png"
MANIFEST_PATH = ASSET_DIR / "biform-manifest.json"
README_PATH = ROOT / "README.md"
FONT_DIR = ROOT / "biform" / "fonts"

FONT_SANS = FONT_DIR / "DejaVuSans.ttf"
FONT_SANS_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_SERIF = FONT_DIR / "DejaVuSerif.ttf"
FONT_SERIF_ITALIC = FONT_DIR / "DejaVuSerif-Italic.ttf"
FONT_MONO = FONT_DIR / "DejaVuSansMono.ttf"

INK = "#11110f"
PAPER = "#f0ede4"
PAPER_DARK = "#ddd7ca"
BRASS = "#a9824c"
RED = "#b74335"
MUTED = "#777267"
WHITE = "#fffdf8"

TOKEN_PATTERN = re.compile(
    r"\s*(?:(?P<comment>\#[^\n]*)|(?P<string>\"(?:\\.|[^\"])*\")|"
    r"(?P<number>\d+)|(?P<name>[A-Za-z_][A-Za-z0-9_-]*)|(?P<punct>[{}\[\]:,]))"
)


class BiformSyntaxError(ValueError):
    """Raised when the identity source is not valid BIFORM/1."""


class TokenStream:
    def __init__(self, text):
        self.tokens = []
        position = 0
        while position < len(text):
            match = TOKEN_PATTERN.match(text, position)
            if not match:
                if text[position:].strip() == "":
                    break
                excerpt = text[position : position + 30].splitlines()[0]
                raise BiformSyntaxError(f"Unexpected source near: {excerpt!r}")
            position = match.end()
            kind = match.lastgroup
            value = match.group(kind)
            if kind != "comment":
                self.tokens.append((kind, value))
        self.index = 0

    def peek(self):
        if self.index >= len(self.tokens):
            return ("eof", "")
        return self.tokens[self.index]

    def take(self, expected_kind=None, expected_value=None):
        kind, value = self.peek()
        if expected_kind and kind != expected_kind:
            raise BiformSyntaxError(f"Expected {expected_kind}, found {value!r}")
        if expected_value and value != expected_value:
            raise BiformSyntaxError(f"Expected {expected_value!r}, found {value!r}")
        self.index += 1
        return value


def parse_value(tokens):
    kind, value = tokens.peek()
    if kind == "string":
        return json.loads(tokens.take("string"))
    if kind == "number":
        return int(tokens.take("number"))
    if value == "[":
        tokens.take("punct", "[")
        values = []
        while tokens.peek()[1] != "]":
            values.append(parse_value(tokens))
            if tokens.peek()[1] == ",":
                tokens.take("punct", ",")
            elif tokens.peek()[1] != "]":
                raise BiformSyntaxError("Expected ',' or ']' in list")
        tokens.take("punct", "]")
        return values
    if kind == "name":
        return tokens.take("name")
    raise BiformSyntaxError(f"Expected a value, found {value!r}")


def parse_block(tokens):
    values = {}
    tokens.take("punct", "{")
    while tokens.peek()[1] != "}":
        key = tokens.take("name")
        tokens.take("punct", ":")
        values[key] = parse_value(tokens)
        if tokens.peek()[1] == ",":
            tokens.take("punct", ",")
    tokens.take("punct", "}")
    return values


def parse_spec(path=SPEC_PATH):
    tokens = TokenStream(path.read_text(encoding="utf-8"))
    tokens.take("name", "biform")
    version = int(tokens.take("number"))
    if version != 1:
        raise BiformSyntaxError(f"Unsupported BIFORM version: {version}")

    identity = None
    exhibits = []
    while tokens.peek()[0] != "eof":
        block_type = tokens.take("name")
        if block_type == "identity":
            if identity is not None:
                raise BiformSyntaxError("Only one identity block is allowed")
            identity = parse_block(tokens)
        elif block_type == "exhibit":
            exhibit_id = tokens.take("name")
            exhibit = parse_block(tokens)
            exhibit["id"] = exhibit_id
            exhibits.append(exhibit)
        else:
            raise BiformSyntaxError(f"Unknown block type: {block_type}")

    if identity is None:
        raise BiformSyntaxError("The identity block is required")
    if not exhibits:
        raise BiformSyntaxError("At least one exhibit block is required")

    required_identity = {"name", "place", "role", "thesis", "statement", "artifact", "github"}
    missing_identity = sorted(required_identity - set(identity))
    if missing_identity:
        raise BiformSyntaxError(f"Missing identity fields: {', '.join(missing_identity)}")

    required_exhibit = {"number", "mode", "title", "description", "image", "repository", "materials"}
    for exhibit in exhibits:
        missing = sorted(required_exhibit - set(exhibit))
        if missing:
            raise BiformSyntaxError(
                f"Exhibit {exhibit['id']!r} is missing: {', '.join(missing)}"
            )
        image_path = ROOT / exhibit["image"]
        if not image_path.is_file():
            raise BiformSyntaxError(f"Exhibit image does not exist: {exhibit['image']}")

    return {"version": version, "identity": identity, "exhibits": exhibits}


def font(path, size):
    return ImageFont.truetype(str(path), size=size)


def text_width(draw, text, text_font):
    box = draw.textbbox((0, 0), text, font=text_font)
    return box[2] - box[0]


def fit_font(draw, text, path, max_size, min_size, max_width):
    for size in range(max_size, min_size - 1, -1):
        candidate = font(path, size)
        if text_width(draw, text, candidate) <= max_width:
            return candidate
    return font(path, min_size)


def wrap_text(draw, text, text_font, max_width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        candidate = " ".join(current + [word])
        if current and text_width(draw, candidate, text_font) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def draw_tracking_text(draw, position, text, text_font, fill, tracking):
    x, y = position
    for character in text:
        draw.text((x, y), character, font=text_font, fill=fill)
        x += text_width(draw, character, text_font) + tracking


def draw_rule(draw, xy, fill, width=1):
    draw.line(xy, fill=fill, width=width)


def image_bytes(image, optimize=True):
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=optimize)
    return stream.getvalue()


def load_cover_image(path, size):
    with Image.open(path) as source:
        source = source.convert("RGB")
        return ImageOps.fit(source, size, Image.Resampling.LANCZOS)


def render_exhibit(exhibit, index):
    width, height = 1400, 500
    canvas = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(canvas)
    image = load_cover_image(ROOT / exhibit["image"], (760, height))
    reverse = index % 2 == 1

    if reverse:
        image_x = 0
        text_x = 830
        text_width_limit = 490
    else:
        image_x = 640
        text_x = 72
        text_width_limit = 490

    canvas.paste(image, (image_x, 0))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    if reverse:
        for x in range(520, 820):
            alpha = int(255 * (x - 520) / 300)
            overlay_draw.line((x, 0, x, height), fill=(240, 237, 228, alpha))
    else:
        for x in range(570, 770):
            alpha = int(255 * (770 - x) / 200)
            overlay_draw.line((x, 0, x, height), fill=(240, 237, 228, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    label_font = font(FONT_MONO, 18)
    number_font = font(FONT_SERIF, 78)
    title_font = fit_font(draw, exhibit["title"], FONT_SERIF, 52, 40, text_width_limit)
    body_font = font(FONT_SANS, 23)
    material_font = font(FONT_MONO, 16)

    draw_tracking_text(draw, (text_x, 48), exhibit["mode"], label_font, RED, 4)
    draw.text((text_x + text_width_limit - 92, 34), exhibit["number"], font=number_font, fill=PAPER_DARK)
    draw_rule(draw, (text_x, 88, text_x + text_width_limit, 88), INK, 2)
    draw.text((text_x, 122), exhibit["title"], font=title_font, fill=INK)

    body_y = 205
    for line in wrap_text(draw, exhibit["description"], body_font, text_width_limit):
        draw.text((text_x, body_y), line, font=body_font, fill="#33312c")
        body_y += 34

    draw_rule(draw, (text_x, 350, text_x + text_width_limit, 350), PAPER_DARK, 2)
    material_text = "  /  ".join(exhibit["materials"])
    material_y = 378
    for line in wrap_text(draw, material_text, material_font, text_width_limit):
        draw.text((text_x, material_y), line, font=material_font, fill=MUTED)
        material_y += 24

    draw.text((text_x, 448), "OPEN THE REPOSITORY", font=label_font, fill=INK)
    draw.line((text_x, 474, text_x + 235, 474), fill=RED, width=4)
    return canvas


def render_proof_plate(identity, exhibits):
    width, height = 1400, 380
    canvas = Image.new("RGB", (width, height), INK)
    draw = ImageDraw.Draw(canvas)

    draw_tracking_text(draw, (64, 48), "BIFORM / OPERATING PRINCIPLE", font(FONT_MONO, 17), BRASS, 3)
    draw.text((64, 92), "The surface is also the source.", font=font(FONT_SERIF, 48), fill=PAPER)
    statement_font = font(FONT_SANS, 21)
    statement_y = 164
    for line in wrap_text(draw, identity["artifact"], statement_font, 1260):
        draw.text((64, statement_y), line, font=statement_font, fill="#c9c3b6")
        statement_y += 31

    columns = [
        (64, "01", "WRITE", "identity.biform"),
        (410, "02", "COMPILE", "python biform.py build"),
        (756, "03", "DISPLAY", "GitHub reads the PNG"),
        (1102, "04", "INSPECT", "archive reads the source"),
    ]
    for x, number, title, detail in columns:
        draw.text((x, 270), number, font=font(FONT_SERIF, 30), fill=BRASS)
        draw.text((x + 50, 274), title, font=font(FONT_SANS_BOLD, 16), fill=PAPER)
        draw.text((x + 50, 306), detail, font=font(FONT_MONO, 13), fill="#aaa396")
    return canvas


def render_cover(identity, payload_root, file_count):
    width, height = 1400, 680
    canvas = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, width, 74), fill=INK)
    draw_tracking_text(draw, (54, 25), "BIFORM / IDENTITY ARTIFACT 001", font(FONT_MONO, 16), PAPER, 3)
    draw.text((1135, 24), "AASHISH THAKURI", font=font(FONT_MONO, 16), fill=BRASS)

    split_x = 880
    draw.rectangle((split_x, 74, width, height), fill=INK)
    draw.line((split_x, 74, split_x, height), fill=BRASS, width=3)

    draw_tracking_text(draw, (58, 112), "READING ONE / SURFACE", font(FONT_MONO, 16), RED, 3)
    draw.text((56, 158), "One identity.", font=font(FONT_SERIF, 68), fill=INK)
    draw.text((56, 238), "Two valid readings.", font=font(FONT_SERIF, 68), fill=INK)

    statement_font = font(FONT_SERIF_ITALIC, 30)
    for line_index, line in enumerate(wrap_text(draw, identity["thesis"], statement_font, 710)):
        draw.text((60, 350 + line_index * 42), line, font=statement_font, fill="#48443d")

    draw_rule(draw, (58, 494, 804, 494), PAPER_DARK, 2)
    draw.text((58, 520), identity["name"], font=font(FONT_SANS_BOLD, 27), fill=INK)
    draw.text((58, 559), identity["role"], font=font(FONT_SANS, 18), fill=MUTED)
    draw.text((58, 602), identity["place"], font=font(FONT_MONO, 15), fill=RED)

    draw_tracking_text(draw, (930, 112), "READING TWO / SOURCE", font(FONT_MONO, 15), BRASS, 2)
    draw.text((930, 158), "Rename this", font=font(FONT_SERIF, 38), fill=PAPER)
    draw.text((930, 205), ".png as .zip", font=font(FONT_SERIF, 38), fill=PAPER)
    draw.text((930, 269), "The same physical file opens as", font=font(FONT_SANS, 17), fill="#bbb4a8")
    draw.text((930, 296), "a complete, inspectable source archive.", font=font(FONT_SANS, 17), fill="#bbb4a8")

    file_lines = [
        "identity.biform",
        "biform.py",
        "README.md",
        "manifest.json",
        f"{file_count:02d} verified payload files",
    ]
    for line_index, line in enumerate(file_lines):
        y = 360 + line_index * 37
        draw.text((930, y), "+", font=font(FONT_MONO, 16), fill=RED)
        draw.text((956, y), line, font=font(FONT_MONO, 15), fill=PAPER)

    draw_rule(draw, (930, 563, 1340, 563), "#3d3a34", 1)
    draw.text((930, 584), "PAYLOAD PROOF / SHA-256", font=font(FONT_MONO, 13), fill="#8f887d")
    draw.text((930, 612), payload_root[:32], font=font(FONT_MONO, 15), fill=BRASS)
    draw.text((930, 638), payload_root[32:], font=font(FONT_MONO, 15), fill=BRASS)
    return canvas


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_posix(path):
    return path.relative_to(ROOT).as_posix()


def source_payload_paths():
    paths = [ROOT / "identity.biform", ROOT / "biform.py", ROOT / "requirements.txt", README_PATH]
    paths.extend(sorted((ROOT / "biform" / "source").glob("*")))
    paths.extend(sorted((ROOT / "biform" / "fonts").glob("*")))
    paths.extend(sorted(EXHIBIT_DIR.glob("*.png")))
    paths.append(ASSET_DIR / "biform-principle.png")
    return [path for path in paths if path.is_file()]


def payload_manifest(paths):
    entries = []
    for path in sorted(paths, key=relative_posix):
        entries.append(
            {
                "path": relative_posix(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    canonical = "".join(f"{entry['path']}:{entry['sha256']}\n" for entry in entries)
    payload_root = sha256_bytes(canonical.encode("utf-8"))
    return {
        "format": "BIFORM/1",
        "artifact": "assets/aashish.biform.png",
        "proof_rule": "SHA-256 of sorted path:sha256 lines for every payload file",
        "payload_root": payload_root,
        "files": entries,
    }


def write_readme(spec):
    identity = spec["identity"]
    exhibit_blocks = []
    for exhibit in spec["exhibits"]:
        exhibit_blocks.append(
            "\n".join(
                [
                    f'<a href="{exhibit["repository"]}">',
                    f'  <img src="./assets/exhibits/{exhibit["number"]}-{exhibit["id"]}.png" width="100%" alt="{exhibit["title"]}">',
                    "</a>",
                ]
            )
        )

    readme = f'''<p align="center">
  <img src="./assets/aashish.biform.png" width="100%" alt="BIFORM identity artifact for {identity['name']}">
</p>

<p align="center">
  <strong>This is not only a picture.</strong><br>
  The file above is simultaneously a GitHub-renderable PNG and an inspectable source archive.
</p>

<p align="center">
  <a href="https://raw.githubusercontent.com/AashishThakuri/AashishThakuri/main/assets/aashish.biform.png">Download the artifact</a>
  &nbsp;/&nbsp;
  <a href="./identity.biform">Read the identity source</a>
  &nbsp;/&nbsp;
  <a href="./assets/biform-manifest.json">Verify the payload</a>
</p>

## BIFORM

Most profile images hide how they were made. This one carries its construction inside itself. Rename `aashish.biform.png` to `aashish.biform.zip` and open it. The archive contains the identity source, compiler, visual sources, generated profile, and a SHA-256 proof manifest.

The image is the interface. The archive is the implementation. They are the same bytes.

<img src="./assets/biform-principle.png" width="100%" alt="How the BIFORM profile artifact works">

## Selected Experiments

{chr(10).join(exhibit_blocks)}

## Open The Other Reading

```powershell
Copy-Item assets/aashish.biform.png aashish.biform.zip
Expand-Archive aashish.biform.zip biform-profile
python biform-profile/biform.py verify --artifact aashish.biform.zip
```

`identity.biform` is the single human-edited source. `biform.py build` compiles the cover, project plates, README, manifest, and dual-valid artifact deterministically.

<p align="center">
  <sub>{identity['place']} / {identity['thesis']}</sub>
</p>
'''
    README_PATH.write_text(readme, encoding="utf-8", newline="\n")


def deterministic_zip(files, manifest):
    stream = io.BytesIO()
    fixed_time = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        open_me = (
            "BIFORM/1\n\n"
            "This archive and the profile image you opened are the same physical file.\n"
            "Run `python biform.py verify --artifact ../aashish.biform.zip` to verify the original file.\n"
            "Run `python biform.py build` to compile the profile again.\n"
        ).encode("utf-8")
        archive_writestr(archive, "OPEN_ME.txt", open_me, fixed_time)
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        archive_writestr(archive, "manifest.json", manifest_bytes, fixed_time)
        for path in sorted(files, key=relative_posix):
            archive_writestr(archive, relative_posix(path), path.read_bytes(), fixed_time)
    return stream.getvalue()


def rebase_zip_offsets(archive_data, prefix_length):
    """Make ZIP directory offsets absolute inside a prefixed polyglot file."""

    data = bytearray(archive_data)
    end_signature = b"PK\x05\x06"
    central_signature = b"PK\x01\x02"
    end_offset = data.rfind(end_signature)
    if end_offset < 0:
        raise ValueError("ZIP end-of-central-directory record was not found")

    central_size = struct.unpack_from("<I", data, end_offset + 12)[0]
    central_offset = struct.unpack_from("<I", data, end_offset + 16)[0]
    cursor = central_offset
    central_end = central_offset + central_size

    while cursor < central_end:
        if data[cursor : cursor + 4] != central_signature:
            raise ValueError("Invalid ZIP central-directory entry")
        local_offset = struct.unpack_from("<I", data, cursor + 42)[0]
        struct.pack_into("<I", data, cursor + 42, local_offset + prefix_length)
        name_length = struct.unpack_from("<H", data, cursor + 28)[0]
        extra_length = struct.unpack_from("<H", data, cursor + 30)[0]
        comment_length = struct.unpack_from("<H", data, cursor + 32)[0]
        cursor += 46 + name_length + extra_length + comment_length

    if cursor != central_end:
        raise ValueError("ZIP central-directory size does not match its entries")
    struct.pack_into("<I", data, end_offset + 16, central_offset + prefix_length)
    return bytes(data)


def archive_writestr(archive, name, data, timestamp):
    info = zipfile.ZipInfo(name, date_time=timestamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build():
    spec = parse_spec()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    EXHIBIT_DIR.mkdir(parents=True, exist_ok=True)

    for index, exhibit in enumerate(spec["exhibits"]):
        output_path = EXHIBIT_DIR / f"{exhibit['number']}-{exhibit['id']}.png"
        output_path.write_bytes(image_bytes(render_exhibit(exhibit, index)))

    principle = render_proof_plate(spec["identity"], spec["exhibits"])
    (ASSET_DIR / "biform-principle.png").write_bytes(image_bytes(principle))
    write_readme(spec)

    payload_paths = source_payload_paths()
    manifest = payload_manifest(payload_paths)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    cover = render_cover(spec["identity"], manifest["payload_root"], len(payload_paths))
    png_data = image_bytes(cover)
    archive_data = rebase_zip_offsets(
        deterministic_zip(payload_paths, manifest),
        len(png_data),
    )
    ARTIFACT_PATH.write_bytes(png_data + archive_data)
    verify(quiet=True)
    return manifest


def verify(artifact_path=ARTIFACT_PATH, quiet=False):
    artifact_path = Path(artifact_path).resolve()
    if not artifact_path.is_file():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    with Image.open(artifact_path) as image:
        image.verify()
        if image.format != "PNG":
            raise ValueError("The artifact is not a valid PNG")

    with zipfile.ZipFile(artifact_path, "r") as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise ValueError(f"Archive CRC failed for {bad_file}")
        manifest = json.loads(archive.read("manifest.json"))
        computed_entries = []
        for entry in manifest["files"]:
            data = archive.read(entry["path"])
            digest = sha256_bytes(data)
            if digest != entry["sha256"]:
                raise ValueError(f"Hash mismatch for {entry['path']}")
            computed_entries.append((entry["path"], digest))
        canonical = "".join(f"{path}:{digest}\n" for path, digest in computed_entries)
        payload_root = sha256_bytes(canonical.encode("utf-8"))
        if payload_root != manifest["payload_root"]:
            raise ValueError("Payload root does not match the embedded manifest")

    if not quiet:
        print("BIFORM verification passed")
        print(f"PNG: valid")
        print(f"Archive: valid")
        print(f"Payload files: {len(manifest['files'])}")
        print(f"Payload root: {manifest['payload_root']}")
    return manifest


def prove_reproducible():
    build()
    first = ARTIFACT_PATH.read_bytes()
    build()
    second = ARTIFACT_PATH.read_bytes()
    if first != second:
        raise ValueError("Two consecutive builds produced different artifact bytes")
    print("Reproducibility check passed")
    print(f"Artifact SHA-256: {sha256_bytes(second)}")


def extract(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "r") as archive:
        archive.extractall(destination)
    print(f"Extracted BIFORM payload to {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["build", "verify", "prove", "extract"], default="build")
    parser.add_argument("destination", nargs="?", default="biform-extracted")
    parser.add_argument("--artifact", default=str(ARTIFACT_PATH), help="BIFORM artifact to verify")
    args = parser.parse_args()

    if args.command == "build":
        manifest = build()
        print(f"Built {ARTIFACT_PATH}")
        print(f"Payload root: {manifest['payload_root']}")
    elif args.command == "verify":
        verify(args.artifact)
    elif args.command == "prove":
        prove_reproducible()
    else:
        extract(args.destination)


if __name__ == "__main__":
    main()
