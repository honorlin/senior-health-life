#!/usr/bin/env python3
"""Replace self-owned editorial illustrations with locally cropped Wikimedia Commons photos.

Audit notes:
- Uses Wikimedia Commons API only for file metadata/download URLs.
- Writes local WebP files under assets/images/posts/ using existing article filenames.
- Updates front matter image fields, inline_images and photo_credits, plus body figure alt/captions.
"""
from __future__ import annotations

import html
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

import requests
import yaml
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "_posts"
IMAGE_DIR = ROOT / "assets/images/posts"
UA = "TaiwanSeniorHealthLife/1.0 Wikimedia Commons photo replacement audit"

ALLOWED_LICENSE_HINTS = ("CC0", "PUBLIC DOMAIN", "CC BY", "CC-BY", "CC BY-SA", "CC-BY-SA")
DISALLOWED_LICENSE_HINTS = ("NC", "ND", "NONCOMMERCIAL", "NO DERIV")

# Each article keeps its existing local filenames. Commons titles are deliberately
# general-context photos; captions must not imply a specific location unless the
# source title actually identifies it.
ARTICLES = {
    "2026-08-19-soft-but-not-mushy-senior-meals.md": [
        {
            "title": "File:Liat Portal for Foodie Disorder - Home cooked healthy meal.jpg",
            "alt": "桌上擺放含蔬菜與主食的家常料理",
            "caption_zh": "一般家庭餐桌上的料理與蔬菜，示意軟而不爛的餐盤安排",
        },
        {
            "title": "File:Liat Portal for Foodie Disorder - Home cooked seafood and vegetable meal.jpg",
            "alt": "含海鮮與蔬菜的家常餐點近照",
            "caption_zh": "含海鮮與蔬菜的家常餐點，可作為切小、煮透與濕潤度安排的參考",
        },
        {
            "title": "File:Dinner at Terre à Terre (top view) 2023-07-30.jpg",
            "alt": "從上方拍攝的多色餐盤與配菜",
            "caption_zh": "多色餐盤與配菜示意，提醒餐點的顏色與食慾也很重要",
        },
    ],
    "2026-08-19-fridge-storage-checklist.md": [
        {
            "title": "File:Fruits and Vegetables in Refrigerator.jpg",
            "alt": "冰箱中整齊擺放蔬菜與水果",
            "caption_zh": "冰箱中蔬果分層收納的一般情境",
        },
        {
            "title": "File:Vegetables in Refrigerator Bin.jpg",
            "alt": "冰箱抽屜中擺放多種蔬菜",
            "caption_zh": "冰箱蔬果抽屜收納示意，適合提醒買菜前先看庫存",
        },
        {
            "title": "File:Fruits and Vegetables in Refrigerator - 50838357101.jpg",
            "alt": "冰箱層架上的水果與蔬菜",
            "caption_zh": "冰箱層架上的蔬果保存示意，可搭配先進先出的整理習慣",
        },
    ],
    "2026-08-19-layered-warm-dressing.md": [
        {
            "title": "File:HK TKO 將軍澳 Tseung Kwan O PopCorn mall shop Uniqlo Clothing Store 冬季 winter top jacket December 2022 Px3 01.jpg",
            "alt": "服飾店內掛著冬季外套與上衣",
            "caption_zh": "冬季外套與上衣陳列，示意依氣溫準備外層衣物",
        },
        {
            "title": "File:HK TKO 將軍澳 Tseung Kwan O PopCorn mall shop Uniqlo Clothing Store 冬季 winter top jacket December 2022 Px3 07.jpg",
            "alt": "衣架上多件保暖外套與針織衣",
            "caption_zh": "多件保暖外套與針織衣，示意洋蔥式穿搭可依活動增減",
        },
        {
            "title": "File:A Winter man.jpg",
            "alt": "穿著冬季外套與圍巾的人物在戶外",
            "caption_zh": "冬季外套與圍巾的一般穿著情境，提醒脖子與外層保暖",
        },
    ],
    "2026-08-19-walking-shoes-socks-check.md": [
        {
            "title": "File:Womens pink running shoes (Unsplash).jpg",
            "alt": "一雙粉紅色運動鞋近照",
            "caption_zh": "運動鞋近照，示意外出鞋要合腳、好穿脫並保有支撐",
        },
        {
            "title": "File:Shoes 22 52 (30619988546).jpg",
            "alt": "一雙休閒鞋鞋面與鞋帶近照",
            "caption_zh": "休閒鞋鞋面與鞋帶細節，提醒檢查鞋帶與鞋面是否穩固",
        },
        {
            "title": "File:Vibram shoes close.jpg",
            "alt": "鞋底紋路與止滑鞋底近照",
            "caption_zh": "鞋底紋路近照，示意出門前可查看鞋底磨耗與止滑狀況",
        },
    ],
    "2026-08-19-rugs-and-clutter-safety.md": [
        {
            "title": "File:The living room inside the birthplace home features a fireplace, table and chairs, family photos, area rug and floor console (7f9f6e78-a966-4608-b9d0-d600db0b5f25).jpg",
            "alt": "客廳地板上鋪有區域地毯與家具",
            "caption_zh": "客廳區域地毯的一般情境，提醒熟齡居家可檢查地毯邊角是否固定",
        },
        {
            "title": "File:Mamluk Prayer Rug - Google Art Project.jpg",
            "alt": "鋪在地面的地毯與邊緣紋理",
            "caption_zh": "地毯與邊緣紋理示意，提醒地墊與地毯需要留意防滑與絆倒風險",
        },
        {
            "title": "File:Flatweave rug, Caucasus, 1875-1925.jpg",
            "alt": "平織地毯的邊緣與表面紋理",
            "caption_zh": "平織地毯紋理示意，可提醒薄地毯邊緣也要平整固定",
        },
    ],
    "2026-08-19-night-path-lighting.md": [
        {
            "title": "File:Bedside Table Lamp.jpg",
            "alt": "床邊桌上的檯燈近照",
            "caption_zh": "床邊檯燈示意，夜間起身前可先有柔和光源",
        },
        {
            "title": "File:Night light ball.jpg",
            "alt": "夜間發光的小型燈具",
            "caption_zh": "小型夜燈示意，適合提醒臥室到廁所路徑可保留低亮度照明",
        },
        {
            "title": "File:The Corridor at Night.jpg",
            "alt": "夜晚走廊中的燈光與通道",
            "caption_zh": "夜晚走廊照明的一般情境，示意動線需要看得清楚且不刺眼",
        },
    ],
    "2026-08-19-start-with-a-safer-home.md": [
        {
            "title": "File:Grab bar.jpg",
            "alt": "浴室牆面上的安全扶手",
            "caption_zh": "浴室安全扶手示意，提醒需要時可在容易起身的位置加裝穩固扶手",
        },
        {
            "title": "File:Herunterschwenkbarer Griffbügel an WC (Chromblende und 2 Schrauben wurden entfernt), Gundelfingen, Deutschland.jpg",
            "alt": "廁所旁可下拉的扶手設備",
            "caption_zh": "廁所旁扶手設備示意，提醒浴廁起身與轉身位置要特別留意",
        },
        {
            "title": "File:Herunterschwenkbarer Griffbügel an Badewanne (Chromblende wurde abgenommen), Gundelfingen, Deutschland.jpg",
            "alt": "浴缸旁可支撐起身的扶手",
            "caption_zh": "浴缸旁扶手示意，提醒濕滑空間可優先檢查支撐點與動線",
        },
    ],
    "2026-08-19-bus-mrt-calm-ride.md": [
        {
            "title": "File:Taipei MRT C371 interior March 2026 1.jpg",
            "alt": "台北捷運車廂內部與座位",
            "caption_zh": "台北捷運車廂內部，示意搭乘時可先觀察座位、扶手與車門位置",
        },
        {
            "title": "File:Taipei Bus Route 203 Interior.jpg",
            "alt": "台北公車車廂內部與扶手",
            "caption_zh": "台北公車車廂內部，示意上車後可優先站穩並抓好扶手",
        },
        {
            "title": "File:Priority Seats MRT Taipei.JPG",
            "alt": "台北捷運車廂內的博愛座區域",
            "caption_zh": "台北捷運博愛座區域，示意熟齡族可善用座位與扶手讓旅程更穩定",
        },
    ],
    "2026-08-19-outing-3-minute-check.md": [
        {
            "title": "File:EasyCard 2019.JPG",
            "alt": "悠遊卡卡片近照",
            "caption_zh": "悠遊卡近照，示意出門前可確認交通卡是否帶齊並有餘額",
        },
        {
            "title": "File:2023 Kasetka z lekami.jpg",
            "alt": "一週分格藥盒與藥品",
            "caption_zh": "分格藥盒示意，提醒出門前確認隨身藥袋或必要用品",
        },
        {
            "title": "File:Lined Up For Going To Work Early (169728603).jpeg",
            "alt": "桌上排列手機、鑰匙與日常出門物品",
            "caption_zh": "手機與日常出門物品示意，可搭配錢包、鑰匙與聯絡方式的出門檢查",
        },
    ],
    "2026-08-19-phishing-stop-check.md": [
        {
            "title": "File:Ríomhphost fioscaireachta as Gaeilge.png",
            "alt": "電子郵件收件匣中的釣魚訊息截圖",
            "caption_zh": "釣魚郵件截圖示意，提醒收到連結時先停一下再判斷",
        },
        {
            "title": "File:Edge-deals-with-phishing-website.png",
            "alt": "瀏覽器顯示釣魚網站警示畫面",
            "caption_zh": "瀏覽器釣魚網站警示畫面，提醒可疑連結可能導向偽冒頁面",
        },
        {
            "title": "File:Blackview A60 Smartphone Android mobile phone front face lock screen.jpg",
            "alt": "智慧型手機鎖定畫面近照",
            "caption_zh": "智慧型手機鎖定畫面示意，提醒陌生連結與簡訊不必急著點開",
        },
    ],
    "2026-08-19-phone-safety-checklist.md": [
        {
            "title": "File:Blackview A60 Smartphone Android mobile phone front face lock screen.jpg",
            "alt": "智慧型手機鎖定畫面近照",
            "caption_zh": "手機鎖定畫面示意，提醒設定密碼可增加日常使用安全",
        },
        {
            "title": "File:A11y smartphone 003 Unihertz Titan Slim 005.jpg",
            "alt": "手持智慧型手機操作畫面",
            "caption_zh": "智慧型手機操作示意，適合陪爸媽一起檢查基本設定",
        },
        {
            "title": "File:Senior smartphone XL-Viewer 5000.jpg",
            "alt": "大字體智慧型手機介面",
            "caption_zh": "大字體手機介面示意，提醒熟齡使用者可調整顯示與聯絡人設定",
        },
    ],
}


def clean_html(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or "Wikimedia Commons contributor"


def commons_page(title: str) -> str:
    name = title.removeprefix("File:").replace(" ", "_")
    return "https://commons.wikimedia.org/wiki/File:" + quote(name, safe="/:()-,._~%")


def api_query(titles: list[str]) -> dict[str, dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": "2400",
        "format": "json",
    }
    for attempt in range(5):
        resp = session.get("https://commons.wikimedia.org/w/api.php", params=params, timeout=60)
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", "30")) + 5)
            continue
        resp.raise_for_status()
        if not resp.text.startswith("{"):
            raise RuntimeError(f"Unexpected Commons API response: {resp.status_code} {resp.text[:120]}")
        pages = resp.json().get("query", {}).get("pages", {})
        out = {}
        for page in pages.values():
            if "missing" in page:
                raise RuntimeError(f"Missing Commons file: {page.get('title')}")
            ii = (page.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            lic = clean_html(meta.get("LicenseShortName", {}).get("value", ""))
            lic_url = clean_html(meta.get("LicenseUrl", {}).get("value", ""))
            combined = f"{lic} {lic_url}".upper()
            if any(x in combined for x in DISALLOWED_LICENSE_HINTS) or not any(x in combined for x in ALLOWED_LICENSE_HINTS):
                raise RuntimeError(f"License not allowed for {page['title']}: {lic} {lic_url}")
            mime = ii.get("mime", "")
            if not mime.startswith("image/"):
                raise RuntimeError(f"Not an image: {page['title']} ({mime})")
            if (ii.get("width") or 0) < 1200 or (ii.get("height") or 0) < 800:
                raise RuntimeError(f"Image too small for {page['title']}: {ii.get('width')}x{ii.get('height')}")
            out[page["title"]] = {
                "url": (ii.get("thumburl") or ii["url"]).split("?", 1)[0],
                "creator": clean_html(meta.get("Artist", {}).get("value", "")),
                "license": lic,
                "license_url": lic_url,
                "source": commons_page(page["title"]),
            }
        return out
    raise RuntimeError("Commons API rate limited after retries")


def crop_webp(source_bytes: bytes, dest: Path, size: tuple[int, int]) -> None:
    tmp = dest.with_suffix(dest.suffix + ".download")
    tmp.write_bytes(source_bytes)
    try:
        with Image.open(tmp) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            target_w, target_h = size
            target_ratio = target_w / target_h
            w, h = im.size
            ratio = w / h
            if ratio > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                im = im.crop((left, 0, left + new_w, h))
            elif ratio < target_ratio:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                im = im.crop((0, top, w, top + new_h))
            im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            im.save(dest, "WEBP", quality=86, method=6)
    finally:
        tmp.unlink(missing_ok=True)


def update_figure(body: str, file_path: str, alt: str, caption: str) -> str:
    file_re = re.escape(file_path)
    pattern = re.compile(r"(<figure\b[^>]*>.*?" + file_re + r".*?</figure>)", re.S)

    def repl(match: re.Match) -> str:
        fig = match.group(1)
        fig = re.sub(r'(<img\b[^>]*\balt=")[^"]*(")', r"\1" + alt.replace('\\', '\\\\').replace('"', '&quot;') + r"\2", fig, count=1, flags=re.S)
        fig = re.sub(r"(<figcaption\b[^>]*>).*?(</figcaption>)", r"\1" + caption + r"\2", fig, count=1, flags=re.S)
        return fig

    new_body, n = pattern.subn(repl, body, count=1)
    if n != 1:
        raise RuntimeError(f"Could not update figure for {file_path}")
    return new_body


def main() -> None:
    titles = sorted({item["title"] for items in ARTICLES.values() for item in items})
    meta_by_title = api_query(titles)
    download_session = requests.Session()
    download_session.headers.update({"User-Agent": UA})

    for post_name, photos in ARTICLES.items():
        path = POSTS / post_name
        text = path.read_text(encoding="utf-8")
        if "self-owned" not in text:
            print(f"skipping already-updated {post_name}", flush=True)
            continue
        if not text.startswith("---"):
            raise RuntimeError(f"Missing front matter: {post_name}")
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        local_files = [meta["image"]] + [img["file"] for img in meta.get("inline_images", [])]
        if len(local_files) != 3:
            raise RuntimeError(f"Expected exactly 3 image slots in {post_name}; got {len(local_files)}")

        credits = []
        for idx, (file_path, photo) in enumerate(zip(local_files, photos)):
            info = meta_by_title[photo["title"]]
            target_size = (1200, 630) if idx == 0 else (1200, 800)
            local_rel = file_path.lstrip("/")
            dest = ROOT / local_rel
            print(f"  downloading {photo['title']} -> {file_path}", flush=True)
            tmp_download = dest.with_suffix(dest.suffix + ".commons-download")
            if dest.exists() and dest.stat().st_size > 10_000:
                print(f"  reusing existing converted image {file_path}", flush=True)
                data = None
            else:
                result = None
                for curl_attempt in range(4):
                    result = subprocess.run(
                        [
                            "curl",
                            "--fail",
                            "--location",
                            "--max-time",
                            "90",
                            "--retry",
                            "1",
                            "--retry-delay",
                            "5",
                            "--user-agent",
                            UA,
                            "--output",
                            str(tmp_download),
                            info["url"],
                        ],
                        text=True,
                        capture_output=True,
                    )
                    if result.returncode == 0:
                        break
                    if "429" in result.stderr:
                        time.sleep(180)
                        continue
                    break
                if result is None or result.returncode != 0:
                    raise RuntimeError(f"curl failed for {photo['title']}: {result.stderr[:500]}")
                data = tmp_download.read_bytes()
                tmp_download.unlink(missing_ok=True)
                if len(data) > 50 * 1024 * 1024:
                    raise RuntimeError(f"Download too large for {photo['title']}")
                crop_webp(data, dest, target_size)
                time.sleep(8)
            caption = f"{photo['caption_zh']}。攝影／作者：{info['creator']}；來源：Wikimedia Commons；授權：{info['license']}。"
            if idx == 0:
                meta["image_alt"] = photo["alt"]
                meta["image_caption"] = caption
            else:
                inline = meta["inline_images"][idx - 1]
                inline["alt"] = photo["alt"]
                inline["caption"] = caption
                body = update_figure(body, file_path, photo["alt"], caption)
            credits.append({
                "file": file_path,
                "creator": info["creator"],
                "source": info["source"],
                "license": info["license"],
                "license_url": info["license_url"],
                "modifications": f"Downloaded original from Wikimedia Commons; center-cropped, resized to {target_size[0]}x{target_size[1]}, and converted to WebP quality 86. No objects or people were added or removed.",
            })
        meta["photo_credits"] = credits
        new_text = "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, width=120) + "---" + body
        path.write_text(new_text, encoding="utf-8")
        print(f"updated {post_name}", flush=True)

if __name__ == "__main__":
    main()
