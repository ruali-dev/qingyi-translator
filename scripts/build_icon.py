from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icon"
PNG_PATH = ICON_DIR / "qingyi-icon.png"
ICO_PATH = ICON_DIR / "qingyi.ico"
CANVAS_SIZE = 1024
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def _mix(start: tuple[int, int, int], end: tuple[int, int, int], amount: float) -> tuple[int, int, int, int]:
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end)) + (255,)


def _rounded_line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    *,
    width: int,
    fill: tuple[int, int, int, int],
) -> None:
    draw.line(points, fill=fill, width=width, joint="curve")
    radius = width // 2
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def render_icon() -> Image.Image:
    image = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))

    shadow_mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(shadow_mask).rounded_rectangle((76, 80, 948, 964), radius=216, fill=92)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(30))
    shadow = Image.new("RGBA", image.size, (37, 48, 107, 0))
    shadow.putalpha(shadow_mask)
    image.alpha_composite(shadow)

    shape_mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(shape_mask).rounded_rectangle((64, 52, 960, 948), radius=224, fill=255)

    gradient = Image.new("RGBA", image.size)
    gradient_draw = ImageDraw.Draw(gradient)
    top = (120, 134, 255)
    bottom = (71, 88, 217)
    for y in range(CANVAS_SIZE):
        gradient_draw.line((0, y, CANVAS_SIZE, y), fill=_mix(top, bottom, y / (CANVAS_SIZE - 1)))
    image.paste(gradient, (0, 0), shape_mask)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-160, -250, 880, 560), fill=(255, 255, 255, 27))
    glow.putalpha(Image.composite(glow.getchannel("A"), Image.new("L", image.size), shape_mask))
    image.alpha_composite(glow)

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (69, 57, 955, 943), radius=219, outline=(255, 255, 255, 46), width=10
    )
    white = (255, 255, 255, 255)
    mint = (215, 249, 228, 255)
    _rounded_line(draw, [(258, 314), (754, 314)], width=72, fill=white)
    _rounded_line(draw, [(258, 496), (608, 496)], width=72, fill=white)
    _rounded_line(draw, [(258, 678), (466, 678)], width=72, fill=white)
    _rounded_line(draw, [(570, 680), (676, 782), (846, 538)], width=78, fill=mint)
    return image


def build_icon() -> tuple[Path, Path]:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    image = render_icon()
    image.save(PNG_PATH, optimize=True)
    image.save(ICO_PATH, format="ICO", sizes=[(size, size) for size in ICO_SIZES])
    return PNG_PATH, ICO_PATH


if __name__ == "__main__":
    png, ico = build_icon()
    print(f"Built {png}")
    print(f"Built {ico}")
