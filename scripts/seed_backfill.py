#!/usr/bin/env python3
"""Backfill seed articles until each category has a target count.

This script is intentionally conservative: it generates a bounded number of new
posts per run, validates only newly-created posts, and exits non-zero if no post
can be safely generated. The daily/operator can rerun it until all categories hit
the target.
"""
import argparse
import collections
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_article  # noqa: E402
import validate_content  # noqa: E402


def post_counts():
    counts = collections.Counter()
    for path in sorted((ROOT / "_posts").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        meta = yaml.safe_load(text.split("---", 2)[1]) or {}
        category = meta.get("category")
        if category:
            counts[category] += 1
    return counts


def ordered_categories():
    site = yaml.safe_load((ROOT / "_data/site.yml").read_text(encoding="utf-8"))
    return [c["key"] for c in site.get("categories", [])]


def main():
    parser = argparse.ArgumentParser(description="Backfill senior-life seed content safely.")
    parser.add_argument("--target-per-category", type=int, default=2)
    parser.add_argument("--max-new", type=int, default=3, help="Maximum new posts in this run.")
    parser.add_argument("--category", choices=sorted(generate_article.CATEGORIES), help="Only backfill one category.")
    parser.add_argument("--fresh", action="store_true", help="Generate target-per-category fresh posts even if category already has posts.")
    parser.add_argument("--sleep", type=float, default=8.0, help="Seconds between article attempts.")
    args = parser.parse_args()

    if args.target_per_category < 1 or args.target_per_category > 5:
        raise SystemExit("--target-per-category must be between 1 and 5")
    if args.max_new < 1 or args.max_new > 8:
        raise SystemExit("--max-new must be between 1 and 8")

    if not generate_article.os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not configured; no seed content generated.")

    today = datetime.now(ZoneInfo("Asia/Taipei"))
    generate_article.POST_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("Missing dependency: install requirements.txt before generating seed content.") from exc
    client = OpenAI()

    categories = [args.category] if args.category else ordered_categories()
    counts = post_counts()
    created = []
    failures = []

    for category in categories:
        if len(created) >= args.max_new:
            break
        need = args.target_per_category if args.fresh else max(0, args.target_per_category - counts.get(category, 0))
        for _ in range(need):
            if len(created) >= args.max_new:
                break
            try:
                data = generate_article.generate_one(client, today, category)
                path = generate_article.write_post(data, today)
                errs = validate_content.validate(path)
                if errs:
                    path.unlink(missing_ok=True)
                    failures.append(f"{category}: generated post failed validation: {'; '.join(errs)}")
                    continue
                created.append(path)
                counts[category] += 1
                print(path)
            except Exception as exc:  # keep batch rerunnable; report precise blocker
                failures.append(f"{category}: {exc}")
            if args.sleep and len(created) < args.max_new:
                time.sleep(args.sleep)

    if failures:
        print("Blocked/failed attempts:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
    if not created:
        raise SystemExit("No safe seed posts were generated in this run.")
    print(f"Generated {len(created)} safe seed post(s).")


if __name__ == "__main__":
    main()
