"""
Generate real branding images for the repository (no placeholders).

Outputs:
 - branding/banner_fullscreen.png (1920x420)
 - branding/screenshot_live_fullscreen.png (1280x720)

This script uses Pillow to create original visuals:
 - Banner: gradient background with subtle scanline pattern and title text.
 - Screenshot: procedural shader-like pattern with radial falloff and color cycling.

Run:
  python scripts/generate_branding_images.py

Requires:
  pip install pillow
"""

import os
from math import sin, cos, pi
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def gradient_image(size: Tuple[int, int], colors: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
    w, h = size
    img = Image.new("RGB", size)
    pixels = img.load()

    for y in range(h):
        t = y / (h - 1)
        r = int(lerp(colors[0][0], colors[1][0], t))
        g = int(lerp(colors[0][1], colors[1][1], t))
        b = int(lerp(colors[0][2], colors[1][2], t))
        for x in range(w):
            pixels[x, y] = (r, g, b)
    return img


def add_scanlines(img: Image.Image, intensity: int = 24, spacing: int = 3):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, 0), width=1)
    # Darken the scanlines slightly
    overlay = Image.new("RGB", img.size, (0, 0, 0))
    img = Image.blend(img, overlay, alpha=intensity / 255.0)
    return img


def try_load_font(size: int) -> ImageFont.FreeTypeFont:
    # Attempt to load a common Windows font, fallback to default
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/SegoeUI.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_banner(path: str):
    size = (1920, 420)
    # Gemini-inspired deep blue to purple gradient
    top = (38, 63, 135)   # deep blue
    bottom = (122, 58, 160)  # purple
    img = gradient_image(size, (top, bottom))
    img = add_scanlines(img, intensity=18, spacing=3)

    draw = ImageDraw.Draw(img)
    title = "Pixel Pusher Plus – Live VJ Engine"
    subtitle = "Rust • wgpu • Audio Reactive • Production Ready"
    title_font = try_load_font(64)
    subtitle_font = try_load_font(28)

    # Centered text
    w, h = size
    tw, th = draw.textlength(title, font=title_font), title_font.size + 12
    stw, sth = draw.textlength(subtitle, font=subtitle_font), subtitle_font.size + 8
    title_xy = ((w - tw) / 2, h * 0.40 - th)
    subtitle_xy = ((w - stw) / 2, h * 0.55 - sth)

    # Soft glow behind text
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for r in range(8, 0, -1):
        alpha = int(20 * (r / 8))
        gdraw.rounded_rectangle([
            title_xy[0] - 20 * r / 8,
            title_xy[1] - 18 * r / 8,
            title_xy[0] + tw + 20 * r / 8,
            title_xy[1] + th + 18 * r / 8,
        ], radius=12, fill=(255, 255, 255, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    img = img.convert("RGB")

    # Draw text
    draw = ImageDraw.Draw(img)
    draw.text(title_xy, title, font=title_font, fill=(240, 240, 255))
    draw.text(subtitle_xy, subtitle, font=subtitle_font, fill=(220, 220, 240))

    img.save(path, format="PNG", optimize=True)


def procedural_pattern(size: Tuple[int, int]):
    w, h = size
    img = Image.new("RGB", size)
    pixels = img.load()

    # Generate a shader-like pattern: rings + directional waves + color cycling
    cx, cy = w / 2.0, h / 2.0
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / w
            dy = (y - cy) / h
            r = (dx * dx + dy * dy) ** 0.5
            a = (pi * 8.0 * r) + sin(dx * 10.0) * 0.5 + cos(dy * 12.0) * 0.5
            s = (sin(a) * 0.5 + 0.5)
            t = (cos(a * 0.5) * 0.5 + 0.5)
            u = (sin(a * 0.25 + dx * 3.0) * 0.5 + 0.5)

            # Radial falloff for vignette
            falloff = max(0.0, 1.0 - r * 1.2)

            R = int(lerp(32, 220, s) * falloff)
            G = int(lerp(48, 180, t) * falloff)
            B = int(lerp(80, 255, u) * falloff)
            pixels[x, y] = (R, G, B)
    return img


def overlay_hud(img: Image.Image):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font = try_load_font(20)
    # Minimal HUD-like elements: FPS, Audio, State
    draw.rectangle([10, 10, 260, 90], fill=(0, 0, 0, 80))
    draw.text((20, 20), "HUD • Live Mode", fill=(255, 255, 255), font=font)
    draw.text((20, 45), "FPS: 60 • Audio: Beat/FFT", fill=(200, 230, 255), font=font)
    draw.text((20, 70), "Safety: FlashGuard ON", fill=(200, 255, 200), font=font)
    # Center watermark
    wm = "Pixel Pusher Plus"
    wmw = draw.textlength(wm, font=font)
    draw.text(((w - wmw) / 2, h - 40), wm, fill=(240, 240, 240), font=font)


def generate_screenshot(path: str):
    size = (1280, 720)
    base = procedural_pattern(size)
    overlay_hud(base)
    base.save(path, format="PNG", optimize=True)


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "branding")
    out_dir = os.path.abspath(out_dir)
    ensure_dir(out_dir)

    banner_path = os.path.join(out_dir, "banner_fullscreen.png")
    screenshot_path = os.path.join(out_dir, "screenshot_live_fullscreen.png")

    generate_banner(banner_path)
    generate_screenshot(screenshot_path)

    print("Generated:")
    print(f" - {banner_path}")
    print(f" - {screenshot_path}")


if __name__ == "__main__":
    main()