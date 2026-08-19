#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import textwrap
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
import yaml
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (ROOT / "automation/prompts/article-prompt.md").read_text(encoding="utf-8")
SOURCES = (ROOT / "automation/trusted-sources.yml").read_text(encoding="utf-8")
SITE = yaml.safe_load((ROOT / "_data/site.yml").read_text(encoding="utf-8"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
POST_IMAGE_DIR = ROOT / "assets/images/posts"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
ALLOWED_LICENSE_TOKENS = ("CC0", "PUBLIC DOMAIN", "PD", "CC BY", "CC-BY", "CC BY-SA", "CC-BY-SA")
DISALLOWED_LICENSE_TOKENS = ("NC", "ND", "NONCOMMERCIAL", "NO DERIV")

CATEGORIES = {c["key"]: c["name"] for c in SITE.get("categories", [])}


def extract_json(text):
    text = text.strip()
    text = re.sub(r"^\`\`\`(?:json)?\s*", "", text)
    text = re.sub(r"\s*\`\`\`$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model did not return a JSON object")
    return json.loads(text[start:end + 1])


def safe_yaml(value):
    return json.dumps(str(value), ensure_ascii=False)


def slugify(value):
    return re.sub(r"[^a-z0-9-]+", "-", str(value).lower()).strip("-")


def strip_html(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(str(value or "")))).strip()


def commons_query(search):
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": 6,
        "gsrsearch": search,
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "origin": "*",
    }
    try:
        r = requests.get(COMMONS_API, params=params, timeout=25, headers={"User-Agent": "senior-health-life-bot/1.0 (https://honorlin.github.io/senior-health-life/)"})
        if r.status_code == 429:
            time.sleep(8)
            return []
        r.raise_for_status()
    except requests.RequestException:
        return []
    pages = (r.json().get("query") or {}).get("pages") or {}
    return list(pages.values())


def allowed_license(name, url):
    combined = f"{name} {url}".upper()
    disallowed_patterns = (r"\bNC\b", r"\bND\b", r"NONCOMMERCIAL", r"NO DERIV")
    if any(re.search(pattern, combined) for pattern in disallowed_patterns):
        return False
    return any(token in combined for token in ALLOWED_LICENSE_TOKENS)


def image_candidate(page):
    info = (page.get("imageinfo") or [{}])[0]
    if not str(info.get("mime", "")).startswith("image/"):
        return None
    if info.get("width", 0) < 900 or info.get("height", 0) < 600:
        return None
    meta = info.get("extmetadata") or {}
    license_name = strip_html((meta.get("LicenseShortName") or {}).get("value"))
    license_url = strip_html((meta.get("LicenseUrl") or {}).get("value")) or info.get("descriptionurl", "") + "#Licensing"
    if not allowed_license(license_name, license_url):
        return None
    creator = strip_html((meta.get("Artist") or meta.get("Credit") or {}).get("value")) or "Wikimedia Commons contributor"
    if len(creator) > 120:
        creator = creator[:117] + "..."
    return {
        "url": info.get("url"),
        "source": info.get("descriptionurl"),
        "creator": creator,
        "license": license_name or "reusable Wikimedia Commons license",
        "license_url": license_url,
        "width": info.get("width"),
        "height": info.get("height"),
    }


def download_and_convert(candidate, dest, size):
    tmp = dest.with_suffix(".source")
    with requests.get(candidate["url"], stream=True, timeout=45, headers={"User-Agent": "senior-health-life-bot/1.0"}) as r:
        r.raise_for_status()
        total = 0
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1024 * 64):
                if chunk:
                    total += len(chunk)
                    if total > 25 * 1024 * 1024:
                        raise RuntimeError("image download exceeds 25MB safety limit")
                    f.write(chunk)
    try:
        with Image.open(tmp) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im = ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            im.save(dest, "WEBP", quality=82, method=6)
    finally:
        tmp.unlink(missing_ok=True)


def build_image_queries(data, category):
    raw = data.get("image_queries") or []
    if isinstance(raw, str):
        raw = [raw]
    for item in (data.get("cover_image"), *(data.get("inline_images") or [])):
        if isinstance(item, dict):
            raw.extend([item.get("search_query"), item.get("alt"), item.get("caption")])
    raw.extend([data.get("title"), category])
    queries = []
    for q in raw:
        q = str(q or "").strip()
        if q and q not in queries:
            queries.append(q)
    return queries


def prepare_images(data, slug, today):
    images = []
    specs = [
        ("cover", f"{today:%Y-%m-%d}-{slug}.webp", (1200, 630)),
        ("inline", f"{today:%Y-%m-%d}-{slug}-1.webp", (1200, 800)),
        ("inline", f"{today:%Y-%m-%d}-{slug}-2.webp", (1200, 800)),
    ]
    queries = build_image_queries(data, data.get("category"))
    used_sources = set()
    for kind, filename, size in specs:
        found = None
        dest = POST_IMAGE_DIR / filename
        if dest.exists():
            raise SystemExit(f"Image already exists: {dest}")
        for query in queries:
            for page in commons_query(query):
                candidate = image_candidate(page)
                if not candidate or candidate["source"] in used_sources:
                    continue
                try:
                    download_and_convert(candidate, dest, size)
                except Exception:
                    dest.unlink(missing_ok=True)
                    dest.with_suffix(".source").unlink(missing_ok=True)
                    continue
                found = candidate
                break
            if found:
                break
            time.sleep(0.2)
        if not found:
            raise SystemExit(f"Blocked: could not download three reusable Wikimedia Commons photos; missing {filename}")
        used_sources.add(found["source"])
        base = data.get("cover_image") if kind == "cover" else None
        inline_idx = len([i for i in images if i["kind"] == "inline"])
        if kind == "inline" and len(data.get("inline_images") or []) > inline_idx:
            base = data["inline_images"][inline_idx]
        base = base or {}
        images.append({
            "kind": kind,
            "file": "/assets/images/posts/" + filename,
            "alt": base.get("alt") or data.get("title") or "樂齡生活情境照片",
            "caption": base.get("caption") or "授權照片，經裁切與網頁壓縮。",
            "width": size[0],
            "height": size[1],
            "credit": {
                "file": "/assets/images/posts/" + filename,
                "creator": found["creator"],
                "source": found["source"],
                "license": found["license"],
                "license_url": found["license_url"],
                "modifications": f"裁切為 {size[0]}×{size[1]}、移除中繼資料並轉為 WebP 壓縮。",
            },
        })
    return images


def figure_markdown(image):
    return textwrap.dedent(f"""

<figure class="article-figure">
  <img src="{{{{ '{image['file']}' | relative_url }}}}" alt="{html.escape(image['alt'])}" width="{image['width']}" height="{image['height']}" loading="lazy">
  <figcaption>{html.escape(image['caption'])}</figcaption>
</figure>
""")


def ensure_inline_figures(markdown, inline_images):
    text = markdown.strip()
    for image in inline_images:
        if image["file"] in text:
            continue
        headings = list(re.finditer(r"^##\s+.+$|^###\s+.+$", text, flags=re.M))
        if headings:
            idx = min(len(headings) - 1, 1 + inline_images.index(image))
            insert = headings[idx].end()
            text = text[:insert] + figure_markdown(image) + text[insert:]
        else:
            text += figure_markdown(image)
    return text


def write_post(data, today):
    if data.get("status") != "approved":
        raise SystemExit("The editorial agent blocked today's article.")
    if data.get("risk_level") not in {"green", "blue"}:
        raise SystemExit("Risk level is not eligible for automatic publishing.")
    slug = slugify(data["slug"])
    if not slug:
        raise SystemExit("Invalid slug")
    path = ROOT / "_posts" / f"{today:%Y-%m-%d}-{slug}.md"
    if path.exists():
        raise SystemExit("Article already exists")
    images = prepare_images(data, slug, today)
    cover = images[0]
    inline_images = images[1:]
    sources = data.get("sources", [])
    source_yaml = "\n".join(
        f"  - title: {safe_yaml(s.get('title',''))}\n    url: {safe_yaml(s.get('url',''))}\n    date: {safe_yaml(s.get('date','unknown'))}"
        for s in sources
    )
    tags = ", ".join(safe_yaml(t) for t in data.get("tags", []))
    inline_yaml = "\n".join(
        f"  - file: {safe_yaml(i['file'])}\n    alt: {safe_yaml(i['alt'])}\n    caption: {safe_yaml(i['caption'])}"
        for i in inline_images
    )
    credit_yaml = "\n".join(
        f"  - file: {safe_yaml(c['file'])}\n    creator: {safe_yaml(c['creator'])}\n    source: {safe_yaml(c['source'])}\n    license: {safe_yaml(c['license'])}\n    license_url: {safe_yaml(c['license_url'])}\n    modifications: {safe_yaml(c['modifications'])}"
        for c in [i["credit"] for i in images]
    )
    body = ensure_inline_figures(data["content_markdown"], inline_images)
    front = f"""---
layout: post
title: {safe_yaml(data['title'])}
slug: {slug}
description: {safe_yaml(data['description'])}
category: {data['category']}
category_name: {safe_yaml(CATEGORIES.get(data['category'], data['category']))}
tags: [{tags}]
risk_level: {data['risk_level']}
image: {safe_yaml(cover['file'])}
image_alt: {safe_yaml(cover['alt'])}
image_caption: {safe_yaml(cover['caption'])}
inline_images:
{inline_yaml}
photo_credits:
{credit_yaml}
sources:
{source_yaml}
---
"""
    path.write_text(front + "\n" + body + "\n", encoding="utf-8")
    return path


def generate_one(client, today, category_hint=None):
    existing = "\n".join(p.stem for p in sorted((ROOT / "_posts").glob("*.md"))[-30:])
    category_line = f"\n本次指定分類：{category_hint}。請只產出此分類。" if category_hint else ""
    request = f"""{PROMPT}
{category_line}

請額外輸出 image_queries: 至少 6 個適合 Wikimedia Commons 搜尋、偏真實照片且與主題相關的英文/中文搜尋詞。
圖片欄位可先提供 alt/caption/search_query；實際圖片路徑、授權與 attribution 會由本地 Wikimedia 授權圖片管線覆寫。

可信來源設定：
{SOURCES}

今天日期：{today:%Y-%m-%d}
最近文章檔名，請避免重複：
{existing}

請使用 web search 查找最新可用的核准來源，最後只輸出規定的 JSON。"""
    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search"}],
        input=request,
    )
    return extract_json(response.output_text)


def main():
    parser = argparse.ArgumentParser(description="Generate safe senior-life article(s) with local licensed images.")
    parser.add_argument("--category", choices=sorted(CATEGORIES), help="Category hint/constraint for generated articles.")
    parser.add_argument("--count", type=int, default=1, help="Number of article candidates to generate.")
    args = parser.parse_args()
    if args.count < 1 or args.count > 5:
        raise SystemExit("--count must be between 1 and 5")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not configured; no article was generated.")
    today = datetime.now(ZoneInfo("Asia/Taipei"))
    POST_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("Missing dependency: install requirements.txt before generating articles.") from exc
    client = OpenAI()
    paths = []
    for _ in range(args.count):
        data = generate_one(client, today, args.category)
        paths.append(write_post(data, today))
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
