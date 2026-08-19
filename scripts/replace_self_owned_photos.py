#!/usr/bin/env python3
"""Replace self-owned editorial illustrations with audited Wikimedia Commons photos.

This script is intentionally explicit: every source image is listed in SOURCE_SETS
with a Commons file title and Chinese editorial caption/alt text. It downloads each
unique Commons original once, crops to the site-required dimensions, writes local
WebP files, and updates post front matter plus existing inline <figure> captions.
"""
from __future__ import annotations

import html
import io
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "_posts"
IMG_DIR = ROOT / "assets" / "images" / "posts"
CACHE = ROOT / ".openclaw-photo-cache"
UA = "senior-health-life-photo-replacement/0.1 (local editorial audit; Wikimedia Commons reuse)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

TARGET_SLUGS = {
    "ten-minute-reading-ritual": "learning_reading",
    "senior-learning-center-class": "learning_class",
    "home-slow-life-hobbies": "leisure_hobbies",
    "half-day-slow-trip-rest-stops": "leisure_trip",
    "seated-tv-break-stretches": "movement_stretch",
    "walking-warmup-pace-hydration": "movement_walk",
    "bedroom-light-sound-safety": "sleep_room",
    "bedtime-thirty-minute-ritual": "sleep_ritual",
    "loneliness-small-steps": "wellbeing_connection",
    "small-expectations": "wellbeing_calm",
    "caregiver-task-sharing": "family_care",
    "gentle-safety-conversation": "family_conversation",
    "five-rational-questions": "supplements_choice",
    "health-food-label-search": "supplements_label",
}

@dataclass(frozen=True)
class SourcePhoto:
    title: str
    alt: str
    scene: str

# Only Commons file pages. Search/news/social/general web images are deliberately absent.
SOURCE_SETS: dict[str, list[SourcePhoto]] = {
    "learning_reading": [
        SourcePhoto("Desk_with_notebook_pens_and_glasses.jpg", "桌面上的筆記本、筆與眼鏡", "閱讀時可搭配筆記與眼鏡"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "閱讀前讓節奏放慢的一杯茶"),
        SourcePhoto("Table_à_manger.jpg", "家中餐桌與餐椅空間", "可作為日常閱讀角落的家中桌面"),
    ],
    "learning_class": [
        SourcePhoto("Desk_with_notebook_pens_and_glasses.jpg", "桌面上的筆記本、筆與眼鏡", "課程筆記與學習準備"),
        SourcePhoto("Table_à_manger.jpg", "家中餐桌與餐椅空間", "在家整理上課資訊的桌面情境"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "課後休息與吸收內容的一般情境"),
    ],
    "leisure_hobbies": [
        SourcePhoto("Desk_with_notebook_pens_and_glasses.jpg", "桌面上的筆記本、筆與眼鏡", "在家安排興趣與小計畫"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "在家休閒時的溫茶陪伴"),
        SourcePhoto("Lothar_Path_-_Black_Forest_National_Park_-_bench_01.jpg", "森林步道旁可休息的長椅", "出門散步放鬆時可休息的長椅"),
    ],
    "leisure_trip": [
        SourcePhoto("Lothar_Path_-_Black_Forest_National_Park_-_bench_01.jpg", "森林步道旁可休息的長椅", "一般慢旅行中的休息長椅"),
        SourcePhoto("Walking_path_at_Newtown_Park,_Newtown_GA.jpg", "公園中平緩的步道", "慢旅行可選擇平緩步道的一般情境"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "旅途中坐下喝飲品休息的一般情境"),
    ],
    "movement_stretch": [
        SourcePhoto("Walking_path_at_Newtown_Park,_Newtown_GA.jpg", "公園中平緩的步道", "可用於暖身散步的公園步道"),
        SourcePhoto("Lothar_Path_-_Black_Forest_National_Park_-_bench_01.jpg", "森林步道旁可休息的長椅", "活動中途可停下休息的長椅"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "活動後坐下休息喝飲品的一般情境"),
    ],
    "movement_walk": [
        SourcePhoto("Walking_path_at_Newtown_Park,_Newtown_GA.jpg", "公園中平緩的步道", "可調整步伐的公園步道"),
        SourcePhoto("Lothar_Path_-_Black_Forest_National_Park_-_bench_01.jpg", "森林步道旁可休息的長椅", "散步途中可停下休息的長椅"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "散步後坐下補充飲品的一般情境"),
    ],
    "sleep_room": [
        SourcePhoto("Hearst_Castle_-_lamp_in_Marion_Davies'_bedroom_01.jpg", "臥室床邊燈與柔和室內照明", "臥室柔和照明情境"),
        SourcePhoto("Bedroom_in_loft_apartment.jpg", "明亮臥室中的床鋪與窗邊空間", "整潔明亮的臥室環境"),
        SourcePhoto("Bedroom_lamp?_(2284478474).jpg", "床邊小燈與臥室角落", "夜間床邊燈光情境"),
    ],
    "sleep_ritual": [
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "睡前放慢節奏的一般情境"),
        SourcePhoto("Bedroom_in_loft_apartment.jpg", "明亮臥室中的床鋪與窗邊空間", "睡前整理臥室環境"),
        SourcePhoto("Hearst_Castle_-_lamp_in_Marion_Davies'_bedroom_01.jpg", "臥室床邊燈與柔和室內照明", "睡前柔和燈光情境"),
    ],
    "wellbeing_connection": [
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "安靜喝茶與整理心情"),
        SourcePhoto("Lothar_Path_-_Black_Forest_National_Park_-_bench_01.jpg", "森林步道旁可休息的長椅", "外出散步時可坐下休息的情境"),
        SourcePhoto("Desk_with_notebook_pens_and_glasses.jpg", "桌面上的筆記本、筆與眼鏡", "寫下聯絡與生活安排的小筆記"),
    ],
    "wellbeing_calm": [
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "日常中給自己一點期待"),
        SourcePhoto("Desk_with_notebook_pens_and_glasses.jpg", "桌面上的筆記本、筆與眼鏡", "寫下小小期待與生活安排"),
        SourcePhoto("Lothar_Path_-_Black_Forest_National_Park_-_bench_01.jpg", "森林步道旁可休息的長椅", "外出坐下透氣的一般情境"),
    ],
    "family_care": [
        SourcePhoto("Table_à_manger.jpg", "家中餐桌與餐椅空間", "家人分工討論可從餐桌開始"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "照顧討論前可先放慢語氣"),
        SourcePhoto("Desk_with_notebook_pens_and_glasses.jpg", "桌面上的筆記本、筆與眼鏡", "用筆記整理照顧分工"),
    ],
    "family_conversation": [
        SourcePhoto("Table_à_manger.jpg", "家中餐桌與餐椅空間", "適合家人坐下談話的餐桌情境"),
        SourcePhoto("A_cup_of_warm_tea.jpg", "桌面上一杯溫熱茶飲", "以輕鬆喝茶開啟談話"),
        SourcePhoto("Desk_with_notebook_pens_and_glasses.jpg", "桌面上的筆記本、筆與眼鏡", "把安全提醒先寫成溫和重點"),
    ],
    "supplements_choice": [
        SourcePhoto("B_vitamin_supplement_tablets.jpg", "白色瓶旁的維生素錠劑", "保健食品錠劑與瓶身的一般情境"),
        SourcePhoto("Omega_3_capsules_in_white_bottle_(52715127894).jpg", "白色瓶中的魚油膠囊", "膠囊型保健品的一般情境"),
        SourcePhoto("Assorted_pharmaceuticals_by_LadyofProcrastination.jpg", "桌面上多種藥品與保健品包裝", "理性整理補充品與藥品清單"),
    ],
    "supplements_label": [
        SourcePhoto("B_vitamin_supplement_tablets.jpg", "白色瓶旁的維生素錠劑", "保健食品錠劑與瓶身的一般情境"),
        SourcePhoto("Omega_3_capsules_in_white_bottle_(52715127894).jpg", "白色瓶中的魚油膠囊", "膠囊型保健品的一般情境"),
        SourcePhoto("Assorted_pharmaceuticals_by_LadyofProcrastination.jpg", "桌面上多種藥品與保健品包裝", "整理補充品與藥品清單的一般情境"),
    ],
}


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<.*?>", "", value or "")).replace("\n", " ").strip()


def commons_page(title: str) -> str:
    return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(title, safe="()_',-àéłóąńŻś’")


def fetch_metadata(photo: SourcePhoto) -> dict:
    url = commons_page(photo.title)
    r = SESSION.get(url, timeout=45)
    r.raise_for_status()
    text = r.text
    media = re.search(r'<div class="fullMedia">.*?<a href="([^"]+)"', text, re.S)
    if not media:
        raise RuntimeError(f"Cannot find original file link: {photo.title}")
    creator_m = re.search(r'id="fileinfotpl&#95;aut".*?</td>\s*<td[^>]*>(.*?)</td>', text, re.S)
    creator = strip_tags(creator_m.group(1)) if creator_m else "Wikimedia Commons contributor"
    lic_m = re.search(r'<link rel="license" href="([^"]+)"', text)
    license_url = html.unescape(lic_m.group(1)) if lic_m else url + "#Licensing"
    if "/licenses/by-sa/" in license_url:
        license_name = "CC BY-SA " + license_url.split("/licenses/by-sa/", 1)[1].strip("/")
    elif "/licenses/by/" in license_url:
        license_name = "CC BY " + license_url.split("/licenses/by/", 1)[1].strip("/")
    elif "zero/1.0" in license_url.lower():
        license_name = "CC0"
    elif "public_domain" in license_url.lower() or "publicdomain" in license_url.lower() or "Public_domain" in license_url:
        license_name = "Public Domain"
    else:
        license_name = license_url
    if any(token in license_name.upper() or token in license_url.upper() for token in ("NC", "ND", "NONCOMMERCIAL", "NO DERIV")):
        raise RuntimeError(f"Disallowed license for {photo.title}: {license_name} {license_url}")
    # The file page provides an already-generated index thumbnail (usually 1280px) that is still a real
    # Wikimedia derivative and avoids repeatedly pulling very large originals during batch maintenance.
    thumb = None
    decoded_title = photo.title.replace(" ", "_")
    for candidate in re.findall(r'(?:https:)?//upload\.wikimedia\.org/[^\" ]+|upload\.wikimedia\.org/[^\" ]+', text):
        candidate = html.unescape(candidate).split("?", 1)[0]
        if candidate.startswith("//"):
            candidate = "https:" + candidate
        elif candidate.startswith("upload."):
            candidate = "https://" + candidate
        if "/thumb/" in candidate and decoded_title in urllib.parse.unquote(candidate):
            thumb = candidate
            break
    return {"title": photo.title, "page": url, "download": html.unescape(media.group(1)), "thumb": thumb, "creator": creator, "license": license_name, "license_url": license_url}


def download_original(meta: dict) -> Path:
    CACHE.mkdir(exist_ok=True)
    suffix = Path(urllib.parse.urlparse(meta["download"]).path).suffix or ".jpg"
    out = CACHE / (re.sub(r"[^A-Za-z0-9_.-]+", "_", meta["title"]) + suffix)
    if out.exists() and out.stat().st_size > 1024:
        return out
    urls = [meta["download"].split("?", 1)[0]]
    if meta.get("thumb"):
        urls.append(meta["thumb"])
    last_status = None
    for url in urls:
        resp = SESSION.get(url, timeout=120)
        last_status = resp.status_code
        if resp.status_code == 429:
            print(f"429 from Wikimedia for {meta['title']} via {url}; trying fallback if available", file=sys.stderr)
            continue
        resp.raise_for_status()
        if not str(resp.headers.get("content-type", "")).startswith("image/"):
            continue
        out.write_bytes(resp.content)
        return out
    raise RuntimeError(f"Could not download {meta['title']} (last status {last_status})")


def make_webp(src: Path, dest: Path, size: tuple[int, int]) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width < size[0] or im.height < size[1]:
            raise RuntimeError(f"Source too small for {dest.name}: {im.size}")
        fitted = ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        dest.parent.mkdir(parents=True, exist_ok=True)
        fitted.save(dest, "WEBP", quality=86, method=6)


def replace_figure(body: str, file_path: str, alt: str, caption: str) -> str:
    def repl(match: re.Match) -> str:
        fig = match.group(0)
        if file_path not in fig:
            return fig
        fig = re.sub(r'alt="[^"]*"', f'alt="{html.escape(alt, quote=True)}"', fig, count=1)
        fig = re.sub(r'<figcaption>.*?</figcaption>', f'<figcaption>{html.escape(caption, quote=False)}</figcaption>', fig, flags=re.S, count=1)
        return fig
    return re.sub(r'<figure class="article-figure">.*?</figure>', repl, body, flags=re.S)


def update_post(path: Path, metas: list[dict], photos: list[SourcePhoto]) -> None:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    data = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    slug = data["slug"]
    date_prefix = path.name.split("-" + slug)[0]
    files = [f"/assets/images/posts/{date_prefix}-{slug}.webp", f"/assets/images/posts/{date_prefix}-{slug}-1.webp", f"/assets/images/posts/{date_prefix}-{slug}-2.webp"]
    captions = [f"{p.scene}。照片：{m['creator']}／Wikimedia Commons／{m['license']}；經裁切與網頁壓縮。" for p, m in zip(photos, metas)]
    data["image"] = files[0]
    data["image_alt"] = photos[0].alt
    data["image_caption"] = captions[0]
    data["inline_images"] = [
        {"file": files[1], "alt": photos[1].alt, "caption": captions[1]},
        {"file": files[2], "alt": photos[2].alt, "caption": captions[2]},
    ]
    data["photo_credits"] = [
        {
            "file": file,
            "creator": m["creator"],
            "source": m["page"],
            "license": m["license"],
            "license_url": m["license_url"],
            "modifications": f"裁切為 {'1200×630' if i == 0 else '1200×800'}、移除中繼資料並轉為 WebP 壓縮。衍生圖片依 {m['license']} 授權。",
        }
        for i, (file, m) in enumerate(zip(files, metas))
    ]
    for file, p, cap in zip(files[1:], photos[1:], captions[1:]):
        body = replace_figure(body, file, p.alt, cap)
    new_fm = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000).strip()
    path.write_text("---\n" + new_fm + "\n---" + body, encoding="utf-8")


def main() -> int:
    audit = []
    for post in sorted(POSTS.glob("*.md")):
        txt = post.read_text(encoding="utf-8")
        if not txt.startswith("---"):
            continue
        data = yaml.safe_load(txt.split("---", 2)[1]) or {}
        slug = data.get("slug")
        if slug not in TARGET_SLUGS:
            continue
        key = TARGET_SLUGS[slug]
        photos = SOURCE_SETS[key]
        print(f"Processing {post.name} <- {key}")
        metas = [fetch_metadata(p) for p in photos]
        originals = [download_original(m) for m in metas]
        date_prefix = post.name.split("-" + slug)[0]
        outs = [IMG_DIR / f"{date_prefix}-{slug}.webp", IMG_DIR / f"{date_prefix}-{slug}-1.webp", IMG_DIR / f"{date_prefix}-{slug}-2.webp"]
        for idx, (src, out) in enumerate(zip(originals, outs)):
            make_webp(src, out, (1200, 630) if idx == 0 else (1200, 800))
        update_post(post, metas, photos)
        audit.append({"post": post.name, "sources": [{k: m[k] for k in ("title", "page", "creator", "license", "license_url")} for m in metas]})
        time.sleep(1.0)
    (ROOT / "photo-replacement-audit.yml").write_text(yaml.safe_dump(audit, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    print(f"Updated {len(audit)} posts. Audit: photo-replacement-audit.yml")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
