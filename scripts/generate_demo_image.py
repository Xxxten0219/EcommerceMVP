#!/usr/bin/env python3
"""Create an ignored local product-style image for the Mock image-edit demo."""

from pathlib import Path

from PIL import Image, ImageDraw

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "runtime" / "demo-product.png"


def generate() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (960, 720), "#e7e5da")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((210, 100, 750, 620), radius=24, fill="#f7f6ef")
    draw.line((315, 545, 405, 205, 555, 205, 645, 545), fill="#172016", width=28)
    draw.line((365, 390, 595, 390), fill="#518bea", width=24)
    draw.ellipse((435, 330, 525, 420), fill="#ff775f")
    draw.text((36, 36), "DEMO PRODUCT / POWER RACK", fill="#172016")
    image.save(OUTPUT, format="PNG", optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    generate()
