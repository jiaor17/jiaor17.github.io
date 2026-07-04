#!/usr/bin/env python3
from __future__ import annotations

import os
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "images"
OUTPUT_DIR = ROOT / "assets" / "works"
DPI = 220
PADDING = 28
WHITE_THRESHOLD = 14
logging.getLogger("pypdf").setLevel(logging.ERROR)


def find_pdftoppm() -> str:
    configured = os.environ.get("PDFTOPPM")
    if configured:
        return configured
    found = shutil.which("pdftoppm")
    if found:
        return found
    bundled = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pdftoppm"
    )
    if bundled.exists():
        return str(bundled)
    raise RuntimeError("pdftoppm not found. Set PDFTOPPM=/path/to/pdftoppm.")


def crop_white_border(path: Path) -> tuple[int, int, int, int]:
    image = Image.open(path).convert("RGB")
    background = Image.new("RGB", image.size, (255, 255, 255))
    diff = ImageChops.difference(image, background).convert("L")
    mask = diff.point(lambda value: 255 if value > WHITE_THRESHOLD else 0)
    bbox = mask.getbbox()

    if bbox is None:
        image.save(path)
        return (0, 0, image.width, image.height)

    left, top, right, bottom = bbox
    left = max(0, left - PADDING)
    top = max(0, top - PADDING)
    right = min(image.width, right + PADDING)
    bottom = min(image.height, bottom + PADDING)

    cropped = image.crop((left, top, right, bottom))
    cropped.save(path, optimize=True)
    return (left, top, right, bottom)


def has_crop_box(pdf: Path) -> bool:
    page = PdfReader(str(pdf), strict=False).pages[0]
    media = page.mediabox
    crop = page.cropbox
    return tuple(media) != tuple(crop)


def render_pdf(pdftoppm: str, pdf: Path, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="work-image-render-") as temp_dir:
        prefix = Path(temp_dir) / pdf.stem
        subprocess.run(
            [
                pdftoppm,
                "-png",
                "-singlefile",
                "-cropbox",
                "-r",
                str(DPI),
                str(pdf),
                str(prefix),
            ],
            check=True,
        )
        rendered = prefix.with_suffix(".png")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rendered, output)


def main() -> None:
    pdftoppm = find_pdftoppm()
    pdfs = sorted(SOURCE_DIR.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {SOURCE_DIR}")

    for pdf in pdfs:
        output = OUTPUT_DIR / f"{pdf.stem}.png"
        render_pdf(pdftoppm, pdf, output)
        # If a PDF has a CropBox, respect the author's manual crop exactly.
        # Otherwise, trim the large white canvas that often comes from figure exports.
        crop_box = None if has_crop_box(pdf) else crop_white_border(output)
        with Image.open(output) as image:
            print(
                f"{pdf.name:14s} -> {output.relative_to(ROOT)} "
                f"{image.width}x{image.height} crop={crop_box}"
            )


if __name__ == "__main__":
    main()
