#!/usr/bin/env python3
"""Create self-owned editorial WebP illustrations for posts.

The images are intentionally stylized illustrations—not photographs—to avoid
misrepresenting scenes while keeping the site free of licensing risk.  The
visual direction is warm Nordic editorial: paper texture, soft geometry,
layered light, and category-specific still-life compositions.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Iterable

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/images/posts"
POSTS = ROOT / "_posts"

# bg, bg2, accent, ink, muted, warm highlight
PALETTE = {
    "nutrition": ((255, 247, 226), (244, 226, 188), (151, 111, 59), (55, 45, 34), (107, 137, 101), (255, 214, 143)),
    "clothing": ((246, 239, 226), (224, 213, 196), (132, 95, 70), (54, 45, 40), (108, 126, 128), (245, 203, 163)),
    "safety": ((255, 250, 238), (245, 230, 198), (209, 139, 41), (53, 45, 34), (116, 126, 105), (255, 221, 132)),
    "mobility": ((235, 247, 244), (211, 231, 226), (51, 105, 101), (38, 50, 47), (142, 113, 82), (246, 208, 145)),
    "learning": ((247, 242, 255), (226, 218, 244), (108, 91, 150), (48, 42, 58), (139, 120, 91), (255, 215, 156)),
    "leisure": ((255, 247, 232), (237, 224, 199), (190, 122, 58), (54, 45, 36), (91, 133, 102), (255, 221, 167)),
    "movement": ((239, 249, 239), (217, 236, 213), (74, 128, 86), (42, 53, 40), (111, 132, 154), (255, 217, 158)),
    "sleep": ((239, 242, 255), (218, 224, 246), (79, 86, 142), (42, 44, 67), (137, 113, 151), (255, 220, 162)),
    "wellbeing": ((255, 242, 246), (241, 218, 225), (174, 91, 120), (58, 43, 51), (102, 132, 109), (255, 220, 166)),
    "family": ((255, 247, 233), (238, 220, 198), (169, 96, 68), (57, 43, 36), (95, 126, 125), (255, 213, 160)),
    "supplements": ((244, 249, 253), (221, 235, 244), (53, 101, 133), (37, 50, 61), (122, 128, 91), (255, 221, 157)),
    "digital": ((240, 248, 255), (218, 233, 245), (40, 82, 123), (33, 48, 62), (110, 130, 137), (250, 211, 150)),
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        ("/System/Library/Fonts/PingFang.ttc", 1 if bold else 0),
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0),
    ]
    for path, index in candidates:
        try:
            return ImageFont.truetype(path, size=size, index=index)
        except Exception:
            pass
    return ImageFont.load_default()


def mix(a, b, t: float):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def rgba(c, alpha: int):
    return (*c, alpha)


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(tuple(map(int, box)), radius=int(radius), fill=fill, outline=outline, width=width)


def soft_shadow(base: Image.Image, box, radius: int, offset=(0, 18), blur=28, alpha=55):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shifted = (box[0] + offset[0], box[1] + offset[1], box[2] + offset[0], box[3] + offset[1])
    rounded(d, shifted, radius, (66, 45, 29, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def gradient(size, top, bottom, seed: int):
    """Fast vertical gradient with subtle paper lift."""
    w, h = size
    strip = Image.new("RGB", (1, h), top)
    px = strip.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = mix(top, bottom, t)
    img = strip.resize(size, Image.Resampling.BICUBIC)
    paper = Image.new("RGB", size, (255, 255, 255))
    return Image.blend(img, paper, 0.08).convert("RGBA")


def wrap_text(text: str, draw: ImageDraw.ImageDraw, fnt, max_width: int, max_lines: int) -> list[str]:
    chunks: list[str] = []
    line = ""
    for ch in text:
        trial = line + ch
        if ch in "：:，,、？?」』)）" and chunks:
            pass
        if draw.textlength(trial, font=fnt) <= max_width or not line:
            line = trial
        else:
            chunks.append(line.rstrip())
            line = ch.lstrip()
            if len(chunks) == max_lines - 1:
                break
    if line and len(chunks) < max_lines:
        chunks.append(line.rstrip())
    if len(chunks) == max_lines and draw.textlength(chunks[-1], font=fnt) > max_width:
        while chunks[-1] and draw.textlength(chunks[-1] + "…", font=fnt) > max_width:
            chunks[-1] = chunks[-1][:-1]
        chunks[-1] += "…"
    return chunks


def draw_blob(draw, center, radii, fill):
    cx, cy = center
    rx, ry = radii
    pts = [
        (cx - rx * .85, cy - ry * .25), (cx - rx * .52, cy - ry * .78),
        (cx + rx * .08, cy - ry * .9), (cx + rx * .72, cy - ry * .48),
        (cx + rx * .9, cy + ry * .08), (cx + rx * .55, cy + ry * .72),
        (cx - rx * .15, cy + ry * .86), (cx - rx * .78, cy + ry * .45),
    ]
    draw.polygon([(int(x), int(y)) for x, y in pts], fill=fill)


def draw_label_card(base, x, y, w, h, palette, label, title, cover: bool):
    accent, ink, muted = palette[2], palette[3], palette[4]
    soft_shadow(base, (x, y, x + w, y + h), 38, offset=(0, 20), blur=32, alpha=40)
    d = ImageDraw.Draw(base)
    rounded(d, (x, y, x + w, y + h), 38, (255, 253, 247, 214), outline=rgba(accent, 65), width=2)
    badge_h = 54 if cover else 48
    rounded(d, (x + 34, y + 34, x + 34 + min(300, 34 + len(label) * 30), y + 34 + badge_h), 24, rgba(mix(accent, (255, 255, 255), .72), 210))
    d.text((x + 58, y + 42), label, fill=accent, font=font(26 if cover else 23, True))
    title_font = font(49 if cover else 41, True)
    lines = wrap_text(title, d, title_font, w - 80, 3)
    ty = y + 120
    for line in lines:
        d.text((x + 44, ty), line, fill=ink, font=title_font)
        ty += 62 if cover else 54
    d.line((x + 44, y + h - 76, x + 188, y + h - 76), fill=rgba(accent, 145), width=4)
    d.text((x + 44, y + h - 56), "台灣樂齡好生活｜自製插圖", fill=muted, font=font(25 if cover else 23, True))


def draw_leaf(d, x, y, scale, fill, outline=None):
    d.ellipse((x, y, x + 42 * scale, y + 86 * scale), fill=fill, outline=outline)
    d.line((x + 20 * scale, y + 80 * scale, x + 28 * scale, y + 20 * scale), fill=outline or fill, width=max(2, int(3 * scale)))


def draw_scene(base: Image.Image, category: str, palette, variant: int, cover: bool):
    d = ImageDraw.Draw(base)
    w, h = base.size
    accent, ink, muted, hi = palette[2], palette[3], palette[4], palette[5]
    right = cover
    cx = int(w * (.73 if right else .52))
    cy = int(h * (.52 if cover else .50))
    scale = 1.0 if cover else 1.12

    # editorial stage: table / floor plane and sun wash
    draw_blob(d, (cx + 80, cy - 135), (230 * scale, 145 * scale), rgba(hi, 70))
    rounded(d, (cx - 270 * scale, cy + 120 * scale, cx + 285 * scale, cy + 170 * scale), 25, rgba(mix(accent, (255, 255, 255), .70), 150))
    d.line((cx - 340 * scale, cy + 170 * scale, cx + 340 * scale, cy + 170 * scale), fill=rgba(accent, 55), width=4)

    def card(dx, dy, ww, hh, rot=0):
        box = (cx + dx * scale, cy + dy * scale, cx + (dx + ww) * scale, cy + (dy + hh) * scale)
        soft_shadow(base, box, 22, offset=(0, 12), blur=18, alpha=30)
        rounded(d, box, 22, (255, 253, 248, 205), outline=rgba(accent, 55), width=2)
        return box

    if category == "nutrition":
        card(-185, -35, 190, 150)
        d.ellipse((cx - 225*scale, cy - 35*scale, cx - 25*scale, cy + 95*scale), fill=(255,253,248,230), outline=rgba(accent,150), width=5)
        d.arc((cx - 198*scale, cy - 5*scale, cx - 52*scale, cy + 77*scale), 0, 180, fill=rgba(muted,170), width=7)
        d.ellipse((cx - 145*scale, cy + 5*scale, cx - 90*scale, cy + 52*scale), fill=rgba(hi,190))
        rounded(d, (cx+30*scale, cy-120*scale, cx+180*scale, cy+105*scale), 20, (250,252,247,225), outline=rgba(muted,150), width=4)
        for i, col in enumerate([accent, muted, hi]):
            rounded(d, (cx+55*scale, cy+(-82+i*48)*scale, cx+155*scale, cy+(-58+i*48)*scale), 10, rgba(col,150))
    elif category == "clothing":
        d.polygon([(cx-185*scale,cy-75*scale),(cx-110*scale,cy-130*scale),(cx-40*scale,cy-98*scale),(cx+10*scale,cy-130*scale),(cx+92*scale,cy-70*scale),(cx+43*scale,cy+112*scale),(cx-135*scale,cy+112*scale)], fill=(252,250,244,220), outline=rgba(accent,150))
        d.line((cx-42*scale,cy-95*scale,cx-85*scale,cy+95*scale), fill=rgba(accent,125), width=6)
        d.arc((cx+5*scale,cy+42*scale,cx+210*scale,cy+150*scale), 185, 350, fill=rgba(muted,170), width=34)
        rounded(d, (cx+78*scale, cy+85*scale, cx+215*scale, cy+128*scale), 18, rgba(hi,170))
    elif category == "safety":
        rounded(d, (cx-210*scale, cy-105*scale, cx+160*scale, cy+118*scale), 26, (252,250,243,210), outline=rgba(accent,135), width=4)
        d.line((cx-165*scale,cy-8*scale,cx+120*scale,cy-8*scale), fill=rgba(muted,120), width=12)
        for i in range(4):
            d.ellipse((cx+(-135+i*70)*scale, cy-37*scale, cx+(-105+i*70)*scale, cy-7*scale), fill=rgba(hi,190))
        d.polygon([(cx-40*scale,cy+118*scale),(cx+25*scale,cy+20*scale),(cx+90*scale,cy+118*scale)], fill=rgba(accent,130))
    elif category == "mobility":
        rounded(d, (cx-230*scale, cy-80*scale, cx+180*scale, cy+80*scale), 34, (250,253,249,225), outline=rgba(accent,155), width=5)
        for i in range(3):
            rounded(d, (cx+(-170+i*98)*scale, cy-45*scale, cx+(-95+i*98)*scale, cy+8*scale), 12, rgba(mix(accent,(255,255,255),.72),210))
        d.ellipse((cx-170*scale,cy+55*scale,cx-112*scale,cy+113*scale), fill=rgba(ink,185))
        d.ellipse((cx+70*scale,cy+55*scale,cx+128*scale,cy+113*scale), fill=rgba(ink,185))
        rounded(d, (cx+170*scale, cy-145*scale, cx+260*scale, cy+15*scale), 20, rgba(hi,165), outline=rgba(accent,120), width=3)
    elif category == "learning":
        d.polygon([(cx-210*scale,cy-100*scale),(cx-30*scale,cy-45*scale),(cx-30*scale,cy+128*scale),(cx-210*scale,cy+70*scale)], fill=(255,253,248,225), outline=rgba(accent,130))
        d.polygon([(cx+190*scale,cy-100*scale),(cx-30*scale,cy-45*scale),(cx-30*scale,cy+128*scale),(cx+190*scale,cy+70*scale)], fill=(248,246,255,225), outline=rgba(accent,130))
        for yy in [-35, 10, 55]:
            d.line((cx+15*scale,cy+yy*scale,cx+145*scale,cy+(yy-22)*scale), fill=rgba(muted,100), width=4)
        rounded(d, (cx-260*scale, cy+70*scale, cx-150*scale, cy+150*scale), 18, rgba(hi,175))
    elif category == "leisure":
        rounded(d, (cx-190*scale, cy-10*scale, cx-40*scale, cy+115*scale), 38, (252,250,244,220), outline=rgba(accent,145), width=5)
        d.arc((cx-62*scale,cy+18*scale,cx+55*scale,cy+95*scale), -70, 80, fill=rgba(accent,150), width=12)
        d.line((cx+80*scale,cy+110*scale,cx+110*scale,cy-95*scale), fill=rgba(muted,150), width=8)
        for dx, dy in [(55,-110),(102,-130),(118,-72),(70,-55)]:
            draw_leaf(d, cx+dx*scale, cy+dy*scale, scale*.62, rgba(muted,145), rgba(muted,180))
        rounded(d, (cx+55*scale, cy+105*scale, cx+160*scale, cy+145*scale), 18, rgba(hi,170))
    elif category == "movement":
        d.arc((cx-230*scale,cy-78*scale,cx+195*scale,cy+210*scale), 185, 340, fill=rgba(accent,155), width=24)
        d.line((cx-55*scale,cy-55*scale,cx-2*scale,cy+24*scale,cx+72*scale,cy+15*scale), fill=rgba(ink,155), width=12, joint="curve")
        d.ellipse((cx-82*scale,cy-108*scale,cx-34*scale,cy-60*scale), fill=rgba(hi,185))
        d.line((cx-4*scale,cy+25*scale,cx-58*scale,cy+118*scale), fill=rgba(accent,170), width=12)
        d.line((cx+40*scale,cy+22*scale,cx+115*scale,cy+112*scale), fill=rgba(muted,170), width=12)
        rounded(d, (cx+125*scale, cy-110*scale, cx+195*scale, cy+35*scale), 18, rgba((255,255,255),190), outline=rgba(accent,100), width=3)
    elif category == "sleep":
        rounded(d, (cx-245*scale, cy+5*scale, cx+175*scale, cy+112*scale), 28, rgba((255,255,255),205), outline=rgba(accent,125), width=4)
        rounded(d, (cx-225*scale, cy-50*scale, cx-95*scale, cy+30*scale), 24, rgba(hi,165))
        d.arc((cx+55*scale,cy-150*scale,cx+175*scale,cy-30*scale), 90, 270, fill=rgba(accent,165), width=24)
        d.ellipse((cx+128*scale,cy-107*scale,cx+143*scale,cy-92*scale), fill=rgba(accent,140))
        d.line((cx+205*scale,cy-72*scale,cx+205*scale,cy+107*scale), fill=rgba(muted,140), width=8)
        d.ellipse((cx+158*scale,cy-118*scale,cx+252*scale,cy-48*scale), fill=rgba(hi,150))
    elif category == "wellbeing":
        rounded(d, (cx-205*scale, cy-105*scale, cx+90*scale, cy+125*scale), 30, (255,253,248,220), outline=rgba(accent,130), width=4)
        for i in range(3):
            d.line((cx-155*scale,cy+(-35+i*52)*scale,cx+40*scale,cy+(-35+i*52)*scale), fill=rgba(muted,95), width=5)
            d.ellipse((cx-183*scale,cy+(-47+i*52)*scale,cx-160*scale,cy+(-24+i*52)*scale), fill=rgba(hi,175))
        for dx, dy, col in [(145,-45,accent),(190,4,muted),(125,42,hi)]:
            d.ellipse((cx+dx*scale,cy+dy*scale,cx+(dx+58)*scale,cy+(dy+58)*scale), fill=rgba(col,155))
    elif category == "family":
        rounded(d, (cx-220*scale, cy+8*scale, cx+205*scale, cy+120*scale), 34, rgba(hi,145), outline=rgba(accent,80), width=3)
        for dx, col in [(-150, accent), (-35, muted), (80, hi)]:
            d.ellipse((cx+dx*scale, cy-115*scale, cx+(dx+78)*scale, cy-37*scale), fill=rgba(col,165))
            rounded(d, (cx+(dx-18)*scale, cy-35*scale, cx+(dx+96)*scale, cy+65*scale), 34, rgba((255,255,255),180), outline=rgba(col,105), width=3)
        d.line((cx-145*scale,cy+8*scale,cx+145*scale,cy+8*scale), fill=rgba(accent,115), width=5)
    elif category == "supplements":
        rounded(d, (cx-160*scale, cy-115*scale, cx-35*scale, cy+115*scale), 24, (250,253,249,225), outline=rgba(accent,145), width=5)
        rounded(d, (cx-133*scale, cy-68*scale, cx-62*scale, cy+26*scale), 12, rgba(hi,150))
        d.ellipse((cx+10*scale,cy-50*scale,cx+170*scale,cy+110*scale), outline=rgba(accent,160), width=16)
        d.line((cx+135*scale,cy+76*scale,cx+225*scale,cy+160*scale), fill=rgba(accent,160), width=16)
        for dx, dy in [(42,-8),(78,28),(103,-4)]:
            d.ellipse((cx+dx*scale,cy+dy*scale,cx+(dx+32)*scale,cy+(dy+20)*scale), fill=rgba(muted,130))
    elif category == "digital":
        rounded(d, (cx-110*scale, cy-145*scale, cx+85*scale, cy+125*scale), 30, (249,252,255,225), outline=rgba(accent,155), width=5)
        rounded(d, (cx-86*scale, cy-100*scale, cx+60*scale, cy+55*scale), 18, rgba(mix(accent,(255,255,255),.78),190))
        d.ellipse((cx-22*scale,cy+82*scale,cx+0*scale,cy+104*scale), fill=rgba(accent,155))
        d.polygon([(cx+125*scale,cy-78*scale),(cx+210*scale,cy-38*scale),(cx+190*scale,cy+67*scale),(cx+125*scale,cy+118*scale),(cx+60*scale,cy+67*scale),(cx+40*scale,cy-38*scale)], fill=rgba(hi,165), outline=rgba(accent,120))
        d.line((cx+86*scale,cy+19*scale,cx+116*scale,cy+51*scale,cx+174*scale,cy-18*scale), fill=rgba(accent,170), width=10)
    else:
        card(-185, -70, 290, 185)
        d.ellipse((cx+80*scale, cy-100*scale, cx+245*scale, cy+65*scale), fill=rgba(hi,150), outline=rgba(accent,90), width=3)
        d.line((cx-120*scale, cy+22*scale, cx+45*scale, cy+22*scale), fill=rgba(accent,145), width=8)
        d.line((cx-35*scale, cy-55*scale, cx-35*scale, cy+100*scale), fill=rgba(muted,125), width=8)

    # small editorial details vary by image index
    if variant == 1:
        for i in range(3):
            d.ellipse((cx + (205 + i*28)*scale, cy + (-20 + i*36)*scale, cx + (218 + i*28)*scale, cy + (-7 + i*36)*scale), fill=rgba(accent,100))
    elif variant == 2:
        for i in range(4):
            d.line((cx + (-265+i*34)*scale, cy + (-155+i*8)*scale, cx + (-220+i*34)*scale, cy + (-155+i*8)*scale), fill=rgba(muted,75), width=4)


def create(path: Path, title: str, category: str, label: str, size: tuple[int, int], variant: int = 0):
    pal = PALETTE.get(category, PALETTE["safety"])
    seed = sum(ord(c) for c in f"{path.name}:{title}:{category}:{variant}")
    scale = 2
    big = (size[0] * scale, size[1] * scale)
    sp = tuple(tuple(int(x * 1) for x in c) for c in pal)
    img = gradient(big, sp[0], sp[1], seed)
    d = ImageDraw.Draw(img)
    w, h = big
    accent, ink, muted, hi = sp[2], sp[3], sp[4], sp[5]

    rng = random.Random(seed)
    # Layered soft geometry and light, not icon-like.
    for _ in range(7):
        x = rng.randint(-120, w - 60)
        y = rng.randint(-90, h - 60)
        rw = rng.randint(120, 420)
        rh = rng.randint(80, 300)
        col = rng.choice([accent, muted, hi, (255, 255, 255)])
        if rng.random() < .55:
            draw_blob(d, (x, y), (rw, rh), rgba(col, rng.randint(24, 58)))
        else:
            rounded(d, (x, y, x + rw, y + rh), rng.randint(32, 90), rgba(col, rng.randint(20, 50)))
    for x in range(70, w, 170):
        d.line((x, 0, x - 180, h), fill=rgba((255, 255, 255), 22), width=3)

    cover = size == (1200, 630)
    draw_scene(img, category, sp, variant, cover)
    if cover:
        draw_label_card(img, 76*scale, 74*scale, 535*scale, 468*scale, sp, label, title, True)
    else:
        # Inline images get a different magazine layout so the three-image set is not repetitive.
        if variant == 1:
            draw_label_card(img, 76*scale, 70*scale, 500*scale, 370*scale, sp, label, title, False)
        else:
            draw_label_card(img, 610*scale, 92*scale, 500*scale, 360*scale, sp, label, title, False)
            d = ImageDraw.Draw(img)
            rounded(d, (92*scale, 600*scale, 492*scale, 662*scale), 31*scale, rgba((255,255,255),125), outline=rgba(accent,65), width=2*scale)
            d.text((122*scale, 613*scale), "柔和場景・生活提醒・非真實照片", fill=muted, font=font(23*scale, True))

    # Fine paper grain overlay after drawing.
    grain = Image.effect_noise(big, 14).convert("L")
    paper = Image.new("RGBA", big, (255, 255, 255, 0))
    paper.putalpha(grain.point(lambda p: int(max(0, p - 116) * 0.22)))
    img.alpha_composite(paper)

    img = img.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=91, method=6)


def create_set(slug: str, title: str, category: str, category_name: str, date_prefix: str) -> list[str]:
    OUT.mkdir(parents=True, exist_ok=True)
    specs = [
        (f"{date_prefix}-{slug}.webp", (1200, 630), category_name, 0),
        (f"{date_prefix}-{slug}-1.webp", (1200, 800), "今天可以怎麼做", 1),
        (f"{date_prefix}-{slug}-2.webp", (1200, 800), "安心生活小提醒", 2),
    ]
    files = []
    for filename, size, label, variant in specs:
        path = OUT / filename
        create(path, title, category, label, size, variant)
        files.append("/assets/images/posts/" + filename)
    return files


def owned_posts(date_prefix: str) -> Iterable[tuple[str, str, str, str]]:
    site = yaml.safe_load((ROOT / "_data/site.yml").read_text(encoding="utf-8"))
    category_names = {c["key"]: c["name"] for c in site.get("categories", [])}
    for post in sorted(POSTS.glob(f"{date_prefix}-*.md")):
        text = post.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        front = yaml.safe_load(text.split("---", 2)[1]) or {}
        # Only overwrite clearly self-owned illustration posts; leave Wikimedia/photo posts untouched.
        meta_blob = "\n".join(str(front.get(k, "")) for k in ("image_caption", "image_alt")) + str(front.get("photo_credits", ""))
        if "自製插圖" not in meta_blob and "self-owned://" not in meta_blob:
            continue
        slug = post.stem.removeprefix(f"{date_prefix}-")
        category = str(front.get("category") or "safety")
        title = str(front.get("title") or slug)
        yield slug, title, category, category_names.get(category, category)


def main():
    parser = argparse.ArgumentParser(description="Generate self-owned editorial WebP illustrations.")
    parser.add_argument("--date", default="2026-08-19", help="date prefix for posts/assets")
    parser.add_argument("--slug", help="regenerate one slug only")
    args = parser.parse_args()
    count = 0
    for slug, title, category, category_name in owned_posts(args.date):
        if args.slug and slug != args.slug:
            continue
        files = create_set(slug, title, category, category_name, args.date)
        count += len(files)
        print(f"{slug}: " + ", ".join(Path(f).name for f in files))
    print(f"Generated {count} self-owned illustration files.")


if __name__ == "__main__":
    main()
