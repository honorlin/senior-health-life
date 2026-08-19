#!/usr/bin/env python3
"""Create simple self-owned editorial WebP illustrations for a post.

These are intentionally labeled as illustrations, not photographs, to avoid
misrepresenting scenes while keeping the site free of licensing risk.
"""
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/images/posts"
PALETTE = {
    "nutrition": (255, 244, 199, 138, 90, 0),
    "clothing": (245, 238, 223, 138, 90, 0),
    "safety": (255, 252, 242, 229, 160, 0),
    "mobility": (238, 246, 244, 49, 42, 29),
    "learning": (246, 242, 255, 138, 90, 0),
    "leisure": (255, 246, 230, 229, 160, 0),
    "movement": (239, 248, 239, 65, 118, 78),
    "sleep": (237, 240, 255, 70, 74, 123),
    "wellbeing": (255, 241, 245, 174, 91, 120),
    "family": (255, 246, 232, 153, 96, 67),
    "supplements": (243, 249, 255, 48, 93, 128),
    "digital": (240, 248, 255, 35, 70, 110),
}


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size=size, index=1 if bold else 0)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_icon(draw, category, w, h, accent):
    cx, cy = w - 245, h // 2 + 18
    if category == "nutrition":
        draw.ellipse((cx-90, cy-55, cx+90, cy+55), fill=(255,255,255), outline=accent, width=8)
        draw.arc((cx-50, cy-120, cx+70, cy+10), 190, 350, fill=accent, width=10)
        draw.ellipse((cx-25, cy-10, cx+25, cy+40), fill=accent)
    elif category == "clothing":
        draw.polygon([(cx-95,cy-55),(cx-35,cy-95),(cx+35,cy-95),(cx+95,cy-55),(cx+55,cy+85),(cx-55,cy+85)], fill=(255,255,255), outline=accent)
        draw.line((cx-35,cy-95,cx,cy-35,cx+35,cy-95), fill=accent, width=8)
    elif category == "safety":
        draw.rounded_rectangle((cx-80,cy-100,cx+80,cy+90), radius=18, fill=(255,255,255), outline=accent, width=8)
        draw.rectangle((cx-30,cy-5,cx+30,cy+90), fill=accent)
        draw.ellipse((cx+38,cy+35,cx+54,cy+51), fill=(255,255,255))
    elif category == "mobility":
        draw.rounded_rectangle((cx-110,cy-65,cx+110,cy+45), radius=22, fill=(255,255,255), outline=accent, width=8)
        draw.ellipse((cx-70,cy+35,cx-30,cy+75), fill=accent)
        draw.ellipse((cx+30,cy+35,cx+70,cy+75), fill=accent)
    elif category == "learning":
        draw.polygon([(cx-100,cy-70),(cx,cy-35),(cx,cy+85),(cx-100,cy+45)], fill=(255,255,255), outline=accent)
        draw.polygon([(cx+100,cy-70),(cx,cy-35),(cx,cy+85),(cx+100,cy+45)], fill=(255,255,255), outline=accent)
    elif category == "sleep":
        draw.arc((cx-95,cy-105,cx+95,cy+85), 90, 270, fill=accent, width=35)
        draw.ellipse((cx+30,cy-58,cx+52,cy-36), fill=accent)
    elif category == "digital":
        draw.rounded_rectangle((cx-65,cy-105,cx+65,cy+105), radius=22, fill=(255,255,255), outline=accent, width=8)
        draw.ellipse((cx-10,cy+68,cx+10,cy+88), fill=accent)
    else:
        draw.ellipse((cx-90,cy-90,cx+90,cy+90), fill=(255,255,255), outline=accent, width=8)
        draw.line((cx-45,cy,cx+45,cy), fill=accent, width=10)
        draw.line((cx,cy-45,cx,cy+45), fill=accent, width=10)


def create(path, title, category, label, size):
    bg_r, bg_g, bg_b, ar, ag, ab = PALETTE.get(category, PALETTE["safety"])
    accent = (ar, ag, ab)
    img = Image.new("RGB", size, (bg_r, bg_g, bg_b))
    draw = ImageDraw.Draw(img)
    w, h = size
    draw.rounded_rectangle((50, 50, w-50, h-50), radius=36, outline=accent, width=6)
    draw.rectangle((0, h-155, w, h), fill=accent)
    draw_icon(draw, category, w, h, accent)
    draw.text((80, 80), label, fill=accent, font=font(34, True))
    y = 145
    for line in textwrap.wrap(title, width=18 if w == 1200 and h == 630 else 16)[:3]:
        draw.text((80, y), line, fill=(51,42,29), font=font(54 if h == 630 else 48, True))
        y += 70
    draw.text((80, h-105), "台灣樂齡好生活｜自製插圖", fill=(255,255,255), font=font(32, True))
    img.save(path, "WEBP", quality=88, method=6)


def create_set(slug, title, category, category_name, date_prefix):
    OUT.mkdir(parents=True, exist_ok=True)
    specs = [
        (f"{date_prefix}-{slug}.webp", (1200,630), category_name),
        (f"{date_prefix}-{slug}-1.webp", (1200,800), "今天可以怎麼做"),
        (f"{date_prefix}-{slug}-2.webp", (1200,800), "安心生活小提醒"),
    ]
    files=[]
    for filename, size, label in specs:
        path = OUT / filename
        create(path, title, category, label, size)
        files.append("/assets/images/posts/" + filename)
    return files
