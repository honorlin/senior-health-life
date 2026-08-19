#!/usr/bin/env python3
"""Small post-deploy smoke check for GitHub Pages output."""
import re
import sys
import time
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def fetch(url):
    req = Request(url, headers={"User-Agent": "senior-health-life-deploy-check/1.0"})
    with urlopen(req, timeout=20) as r:
        if r.status >= 400:
            raise RuntimeError(f"HTTP {r.status} for {url}")
        return r.read().decode("utf-8", errors="replace")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: verify_deploy.py <page_url>")
    base = sys.argv[1].rstrip("/") + "/"
    last_error = None
    for _ in range(6):
        try:
            html = fetch(base)
            if "台灣樂齡好生活" not in html:
                raise RuntimeError("home page title not found")
            links = re.findall(r'href=["\']([^"\']+/[^"\']*\.html)["\']', html)
            if links:
                post_url = urljoin(base, links[0])
                post = fetch(post_url)
                images = re.findall(r'<img\b[^>]*src=["\']([^"\']+)["\']', post, re.I)
                local_post_images = [src for src in images if "/assets/images/posts/" in src]
                if len(local_post_images) < 3:
                    raise RuntimeError(f"latest post has fewer than 3 local images: {len(local_post_images)}")
                for src in local_post_images[:3]:
                    fetch(urljoin(base, src))
            print(f"Verified deployed site: {base}")
            return
        except Exception as exc:
            last_error = exc
            time.sleep(10)
    raise SystemExit(f"Deploy verification failed: {last_error}")


if __name__ == "__main__":
    main()
