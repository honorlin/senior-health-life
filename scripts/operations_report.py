#!/usr/bin/env python3
"""Emit a compact daily automation summary for Jarvis/OpenClaw schedulers."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", choices=["published", "blocked", "failed", "draft_only"], default=None)
    parser.add_argument("--reason", default="")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    changed = git("status", "--short").splitlines()
    posts = [line for line in changed if "_posts/" in line]
    images = [line for line in changed if "assets/images/posts/" in line]
    status = args.status
    if not status:
        status = "draft_only" if posts else "blocked"
    report = {
        "time": datetime.now(ZoneInfo("Asia/Taipei")).isoformat(timespec="seconds"),
        "status": status,
        "reason": args.reason,
        "posts_changed": len(posts),
        "post_files": posts,
        "images_changed": len(images),
        "image_files": images,
        "commit": git("rev-parse", "--short", "HEAD"),
    }
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"狀態：{report['status']}")
        if report["reason"]:
            print(f"原因：{report['reason']}")
        print(f"文章異動：{report['posts_changed']}")
        print(f"圖片異動：{report['images_changed']}")
        print(f"Commit：{report['commit']}")


if __name__ == "__main__":
    main()
