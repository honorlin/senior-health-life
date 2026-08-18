#!/usr/bin/env python3
import re, sys
from pathlib import Path
from urllib.parse import urlparse
import yaml

ROOT = Path(__file__).resolve().parents[1]
policy = yaml.safe_load((ROOT / "automation/content-policy.yml").read_text(encoding="utf-8"))
trusted = yaml.safe_load((ROOT / "automation/trusted-sources.yml").read_text(encoding="utf-8"))
approved = trusted["approved_domains"]

def approved_url(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in approved)

def validate(path):
    text = Path(path).read_text(encoding="utf-8")
    errors = []
    if not text.startswith("---"):
        errors.append("missing front matter")
        return errors
    parts = text.split("---", 2)
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    if meta.get("risk_level") not in policy["auto_publish"]["allowed_risk_levels"]:
        errors.append("risk level is not auto-publishable")
    for phrase in policy["blocked_phrases"]:
        if phrase in body or phrase in str(meta.get("title", "")):
            errors.append(f"blocked phrase: {phrase}")
    for section in policy["required_sections"]:
        if section not in body:
            errors.append(f"missing section: {section}")
    sources = meta.get("sources") or []
    if len(sources) < policy["auto_publish"]["minimum_sources"]:
        errors.append("not enough sources")
    if sources and not any(approved_url(s.get("url", "")) for s in sources):
        errors.append("no approved source domain")
    for s in sources:
        if not s.get("title") or not s.get("url"):
            errors.append("incomplete source")
    if re.search(r"(?i)https?://[^\s]+(?:openai|chatgpt)", body):
        errors.append("AI service is not a health evidence source")
    return sorted(set(errors))

if __name__ == "__main__":
    targets = [Path(p) for p in sys.argv[1:]] or sorted((ROOT / "_posts").glob("*.md"))
    all_errors = []
    for target in targets:
        errs = validate(target)
        if errs:
            all_errors.append(f"{target}: " + "; ".join(errs))
    if all_errors:
        print("\n".join(all_errors), file=sys.stderr)
        raise SystemExit(1)
    print(f"Validated {len(targets)} article(s).")
