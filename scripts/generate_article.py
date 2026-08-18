#!/usr/bin/env python3
import json, os, re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (ROOT / "automation/prompts/article-prompt.md").read_text(encoding="utf-8")
SOURCES = (ROOT / "automation/trusted-sources.yml").read_text(encoding="utf-8")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

def extract_json(text):
    text = text.strip()
    text = re.sub(r"^\`\`\`(?:json)?\s*", "", text)
    text = re.sub(r"\s*\`\`\`$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model did not return a JSON object")
    return json.loads(text[start:end+1])

def safe_yaml(value):
    return json.dumps(str(value), ensure_ascii=False)

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not configured; no article was generated.")
    today = datetime.now(ZoneInfo("Asia/Taipei"))
    existing = "\n".join(p.stem for p in sorted((ROOT / "_posts").glob("*.md"))[-30:])
    request = f"""{PROMPT}

可信來源設定：
{SOURCES}

今天日期：{today:%Y-%m-%d}
最近文章檔名，請避免重複：
{existing}

請使用 web search 查找最新可用的核准來源，最後只輸出規定的 JSON。"""
    client = OpenAI()
    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search"}],
        input=request,
    )
    data = extract_json(response.output_text)
    if data.get("status") != "approved":
        raise SystemExit("The editorial agent blocked today's article.")
    if data.get("risk_level") not in {"green", "blue"}:
        raise SystemExit("Risk level is not eligible for automatic publishing.")
    slug = re.sub(r"[^a-z0-9-]+", "-", data["slug"].lower()).strip("-")
    if not slug:
        raise SystemExit("Invalid slug")
    sources = data.get("sources", [])
    source_yaml = "\n".join(
        f"  - title: {safe_yaml(s.get('title',''))}\n    url: {safe_yaml(s.get('url',''))}\n    date: {safe_yaml(s.get('date','unknown'))}"
        for s in sources
    )
    tags = ", ".join(safe_yaml(t) for t in data.get("tags", []))
    front = f"""---
layout: post
title: {safe_yaml(data['title'])}
slug: {slug}
description: {safe_yaml(data['description'])}
category: {data['category']}
tags: [{tags}]
risk_level: {data['risk_level']}
generated_with_ai: true
sources:
{source_yaml}
---
"""
    path = ROOT / "_posts" / f"{today:%Y-%m-%d}-{slug}.md"
    if path.exists():
        raise SystemExit("Article already exists")
    path.write_text(front + "\n" + data["content_markdown"].strip() + "\n", encoding="utf-8")
    print(path)

if __name__ == "__main__":
    main()
