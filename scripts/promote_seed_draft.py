#!/usr/bin/env python3
"""Promote a vetted seed draft into _posts with local licensed images."""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import create_owned_images  # noqa: E402
import generate_article  # noqa: E402
import validate_content  # noqa: E402


def split_doc(path):
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SystemExit(f"missing front matter: {path}")
    _, front, body = text.split("---", 2)
    return yaml.safe_load(front) or {}, body.strip()


def query_terms(meta):
    notes = str(meta.get("image_notes") or "")
    title = str(meta.get("title") or "")
    category = str(meta.get("category") or "")
    # Conservative generic lifestyle terms; avoid implying exact Taiwan scenes.
    category_terms = {
        "nutrition": ["vegetables on table", "home cooked meal", "steamed vegetables"],
        "clothing": ["walking shoes", "socks drawer", "sweater scarf"],
        "safety": ["hallway night light", "non slip mat", "tidy living room"],
        "mobility": ["bus handrail", "train station bench", "wallet keys phone"],
        "learning": ["public library reading room", "open book", "notebook pencil"],
        "leisure": ["tea cup table", "balcony plants", "park bench"],
        "movement": ["walking path park", "water bottle towel", "chair exercise"],
        "sleep": ["bedroom lamp", "curtains bedroom", "quiet bedroom"],
        "wellbeing": ["calendar flowers", "tea cup window", "garden bench"],
        "family": ["family table conversation", "notebook checklist", "kitchen table"],
        "supplements": ["food label", "nutrition facts label", "bottle label close up"],
        "digital": ["smartphone lock", "mobile phone table", "password keyboard"],
    }
    terms = [title, notes, *category_terms.get(category, []), category]
    out=[]
    for term in terms:
        for part in re.split(r"[；;、,，。:：|/]+", term):
            part = part.strip()
            if part and part not in out:
                out.append(part)
    return out[:12]


def write_owned_illustration_post(meta, body, slug, date):
    date_prefix = f"{date:%Y-%m-%d}"
    category = meta["category"]
    category_name = meta.get("category_name") or generate_article.CATEGORIES.get(category, category)
    files = create_owned_images.create_set(slug, meta["title"], category, category_name, date_prefix)
    cover, inline1, inline2 = files
    inline_images = [
        {"file": inline1, "alt": f"{meta['title']}相關生活細節自製插圖", "caption": "台灣樂齡好生活自製插圖；非真實照片，用於說明生活情境。"},
        {"file": inline2, "alt": f"{meta['title']}的日常實踐自製插圖", "caption": "台灣樂齡好生活自製插圖；非真實照片，用於說明生活情境。"},
    ]
    credit_yaml = "\n".join(
        f"  - file: {generate_article.safe_yaml(file)}\n    creator: \"台灣樂齡好生活編輯部\"\n    source: \"self-owned://taiwan-senior-wellbeing/editorial-illustration\"\n    license: \"Self-owned editorial illustration\"\n    license_url: \"self-owned://taiwan-senior-wellbeing/editorial-illustration\"\n    modifications: \"以品牌視覺製作為 WebP 自製插圖；非真實照片。\""
        for file in files
    )
    source_yaml = "\n".join(
        f"  - title: {generate_article.safe_yaml(s.get('title',''))}\n    url: {generate_article.safe_yaml(s.get('url',''))}\n    date: {generate_article.safe_yaml(s.get('date','unknown'))}"
        for s in (meta.get("sources") or [])
    )
    tags = ", ".join(generate_article.safe_yaml(t) for t in meta.get("tags", []))
    inline_yaml = "\n".join(
        f"  - file: {generate_article.safe_yaml(i['file'])}\n    alt: {generate_article.safe_yaml(i['alt'])}\n    caption: {generate_article.safe_yaml(i['caption'])}"
        for i in inline_images
    )
    post_body = generate_article.ensure_inline_figures(body, [
        {"file": inline1, "alt": inline_images[0]["alt"], "caption": inline_images[0]["caption"], "width": 1200, "height": 800},
        {"file": inline2, "alt": inline_images[1]["alt"], "caption": inline_images[1]["caption"], "width": 1200, "height": 800},
    ])
    front = f'''---
layout: post
title: {generate_article.safe_yaml(meta['title'])}
slug: {slug}
description: {generate_article.safe_yaml(meta['description'])}
category: {category}
category_name: {generate_article.safe_yaml(category_name)}
tags: [{tags}]
risk_level: {meta['risk_level']}
image: {generate_article.safe_yaml(cover)}
image_alt: {generate_article.safe_yaml(meta['title'] + '自製插圖')}
image_caption: "台灣樂齡好生活自製插圖；非真實照片，用於說明生活情境。"
inline_images:
{inline_yaml}
photo_credits:
{credit_yaml}
sources:
{source_yaml}
---
'''
    path = ROOT / "_posts" / f"{date_prefix}-{slug}.md"
    if path.exists():
        raise SystemExit(f"post already exists: {path}")
    path.write_text(front + "\n" + post_body + "\n", encoding="utf-8")
    return path


def promote(draft_path, date, owned_illustrations=False):
    meta, body = split_doc(draft_path)
    slug = generate_article.slugify(meta.get("slug") or Path(draft_path).stem)
    if not slug:
        raise SystemExit("invalid slug")
    post_path = ROOT / "_posts" / f"{date:%Y-%m-%d}-{slug}.md"
    if post_path.exists():
        raise SystemExit(f"post already exists: {post_path}")
    data = {
        "status": "approved",
        "title": meta["title"],
        "slug": slug,
        "description": meta["description"],
        "category": meta["category"],
        "risk_level": meta["risk_level"],
        "tags": meta.get("tags") or [],
        "sources": meta.get("sources") or [],
        "content_markdown": body,
        "image_queries": query_terms(meta),
        "cover_image": {"alt": f"{meta['title']}的樂齡生活情境照片", "caption": "授權照片，經裁切與網頁壓縮。"},
        "inline_images": [
            {"alt": f"{meta['title']}相關生活細節", "caption": "授權照片，經裁切與網頁壓縮。"},
            {"alt": f"{meta['title']}的日常實踐情境", "caption": "授權照片，經裁切與網頁壓縮。"},
        ],
    }
    if owned_illustrations:
        path = write_owned_illustration_post(meta, body, slug, date)
    else:
        try:
            path = generate_article.write_post(data, date)
        except SystemExit as exc:
            if "could not download three reusable Wikimedia" not in str(exc):
                raise
            path = write_owned_illustration_post(meta, body, slug, date)
    errors = validate_content.validate(path)
    if errors:
        path.unlink(missing_ok=True)
        raise SystemExit("validation failed: " + "; ".join(errors))
    return path


def main():
    parser = argparse.ArgumentParser(description="Promote seed draft with licensed images.")
    parser.add_argument("draft", nargs="+", help="Draft path(s) under _drafts/seed")
    parser.add_argument("--date", help="Publish date YYYY-MM-DD; default Asia/Taipei today")
    parser.add_argument("--owned-illustrations", action="store_true", help="Use self-owned labeled illustrations instead of Wikimedia photos.")
    args = parser.parse_args()
    date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Taipei")) if args.date else datetime.now(ZoneInfo("Asia/Taipei"))
    generate_article.POST_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    promoted=[]
    for draft in args.draft:
        promoted.append(promote(ROOT / draft if not str(draft).startswith("/") else Path(draft), date, args.owned_illustrations))
    for path in promoted:
        print(path)


if __name__ == "__main__":
    main()
