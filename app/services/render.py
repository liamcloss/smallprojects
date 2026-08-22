from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from app.config import Settings


def _font_candidates(bold: bool) -> list[str]:
    if bold:
        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    return [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in _font_candidates(bold):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _cover_resize(image: Image.Image, width: int, height: int) -> Image.Image:
    src_ratio = image.width / image.height
    target_ratio = width / height
    if src_ratio > target_ratio:
        new_height = height
        new_width = int(height * src_ratio)
    else:
        new_width = width
        new_height = int(width / src_ratio)
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (new_width - width) // 2
    top = (new_height - height) // 2
    return image.crop((left, top, left + width, top + height))


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        proposed = f"{current} {word}".strip()
        box = draw.textbbox((0, 0), proposed, font=font)
        if box[2] - box[0] <= max_width or not current:
            current = proposed
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int):
    for size in range(104, 49, -2):
        font = _font(size, bold=True)
        lines = _wrap_text(draw, text, font, max_width)
        spacing = int(size * 0.28)
        heights = []
        for line in lines:
            box = draw.textbbox((0, 0), line, font=font)
            heights.append(box[3] - box[1])
        total_height = sum(heights) + spacing * max(0, len(lines) - 1)
        if len(lines) <= 6 and total_height <= max_height:
            return font, lines, spacing, total_height
    font = _font(48, bold=True)
    lines = _wrap_text(draw, text, font, max_width)
    spacing = 14
    total_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)
    return font, lines, spacing, total_height


def render_slide(
    background_path: Path,
    text: str,
    slide_number: int,
    destination: Path,
    settings: Settings,
) -> Path:
    image = Image.open(background_path).convert("RGB")
    image = _cover_resize(image, settings.canvas_width, settings.canvas_height)
    image = ImageEnhance.Contrast(image).enhance(0.92)

    # Dark translucent wash for consistent text legibility.
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 74))
    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(image)

    max_width = settings.canvas_width - (settings.text_margin * 2)
    max_height = 920
    font, lines, spacing, total_height = _fit_text(draw, text, max_width, max_height)

    y = (settings.canvas_height - total_height) / 2
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        line_width = box[2] - box[0]
        line_height = box[3] - box[1]
        x = (settings.canvas_width - line_width) / 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 120),
        )
        y += line_height + spacing

    small_font = _font(30, bold=False)
    handle = settings.account_handle.strip()
    if handle:
        draw.text(
            (settings.watermark_margin, settings.canvas_height - 96),
            handle,
            font=small_font,
            fill=(255, 255, 255, 175),
        )
    number_text = f"{slide_number}/6"
    number_box = draw.textbbox((0, 0), number_text, font=small_font)
    draw.text(
        (
            settings.canvas_width - settings.watermark_margin - (number_box[2] - number_box[0]),
            settings.canvas_height - 96,
        ),
        number_text,
        font=small_font,
        fill=(255, 255, 255, 175),
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(destination, format="JPEG", quality=94, optimize=True)
    return destination
