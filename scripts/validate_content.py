#!/usr/bin/env python3
import re, sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
policy = yaml.safe_load((ROOT / "automation/content-policy.yml").read_text(encoding="utf-8"))
trusted = yaml.safe_load((ROOT / "automation/trusted-sources.yml").read_text(encoding="utf-8"))
approved = trusted["approved_domains"]
PUBLIC_HEALTH_DOMAINS = ("gov.tw", "who.int", "nhs.uk", "mayoclinic.org", "health.harvard.edu")
ALLOWED_IMAGE_SOURCE_DOMAINS = ("commons.wikimedia.org", "upload.wikimedia.org", "wikimedia.org")
ALLOWED_LICENSE_TOKENS = ("CC0", "PUBLIC DOMAIN", "PD", "CC BY", "CC-BY", "CC BY-SA", "CC-BY-SA")
DISALLOWED_LICENSE_TOKENS = ("NC", "ND", "NONCOMMERCIAL", "NO DERIV")
IMAGE_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png", ".svg")
REQUIRED_IMAGE_SIZES = {(1200, 630), (1200, 800)}


def host_matches(url, domains):
    host = (urlparse(str(url)).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in domains)


def approved_url(url):
    return host_matches(url, approved)


def public_health_url(url):
    return host_matches(url, PUBLIC_HEALTH_DOMAINS)


def local_path(value):
    value = str(value or "").strip()
    if value.startswith("http://") or value.startswith("https://"):
        return None
    value = value.split("?", 1)[0]
    if value.startswith("{{"):
        m = re.search(r"['\"](/assets/images/posts/[^'\"]+)['\"]", value)
        value = m.group(1) if m else value
    if value.startswith("/"):
        value = value[1:]
    if not value.startswith("assets/images/posts/"):
        return None
    return ROOT / value


def body_images(body):
    images = []
    seen_srcs = set()
    for m in re.finditer(r"<img\b([^>]+)>", body, re.I):
        tag = m.group(1)
        attrs = dict(re.findall(r"([\w:-]+)=[\"']([^\"']*)[\"']", tag))
        liquid_src = re.search(r"['\"](/assets/images/posts/[^'\"]+)['\"]", tag)
        if liquid_src:
            attrs["src"] = liquid_src.group(1)
        if attrs.get("src"):
            seen_srcs.add(attrs["src"])
            images.append(attrs)
    for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", body):
        seen_srcs.add(m.group(2))
        images.append({"alt": m.group(1), "src": m.group(2)})
    for src in re.findall(r"['\"](/assets/images/posts/[^'\"]+)['\"]", body):
        if src not in seen_srcs:
            images.append({"alt": None, "src": src})
    return images


def captions(body):
    return [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<figcaption\b[^>]*>(.*?)</figcaption>", body, re.I | re.S)]


def figure_caption_files(body):
    files = set()
    for figure in re.findall(r"<figure\b[^>]*>.*?</figure>", body, re.I | re.S):
        if not re.search(r"<figcaption\b", figure, re.I):
            continue
        for src in re.findall(r"['\"](/assets/images/posts/[^'\"]+)['\"]", figure):
            files.add(src)
    return files


def image_size(path):
    if path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"<script|foreignObject|base64,|https?://", text, re.I):
            raise ValueError("SVG contains forbidden active/external content")
        m = re.search(r"<svg[^>]*\bwidth=[\"'](\d+)[\"'][^>]*\bheight=[\"'](\d+)[\"']", text, re.I)
        if not m:
            m = re.search(r"viewBox=[\"']\s*\S+\s+\S+\s+(\d+)\s+(\d+)\s*[\"']", text, re.I)
        if not m:
            raise ValueError("cannot determine SVG size")
        return int(m.group(1)), int(m.group(2))
    with Image.open(path) as im:
        return im.size


def license_allowed(name, url):
    combined = f"{name} {url}".upper()
    disallowed_patterns = (r"\bNC\b", r"\bND\b", r"NONCOMMERCIAL", r"NO DERIV")
    if any(re.search(pattern, combined) for pattern in disallowed_patterns):
        return False
    return any(token in combined for token in ALLOWED_LICENSE_TOKENS)


def validate_images(meta, body, errors):
    if re.search(r"https?://[^\s'\")]+\.(?:webp|jpe?g|png|svg|gif)", body, re.I):
        errors.append("hotlinked image in body")
    image_entries = []
    if meta.get("image"):
        image_entries.append({"file": meta.get("image"), "alt": meta.get("image_alt"), "caption": meta.get("image_caption"), "role": "cover"})
    for idx, item in enumerate(meta.get("inline_images") or []):
        image_entries.append({"file": item.get("file") or item.get("path"), "alt": item.get("alt"), "caption": item.get("caption"), "role": f"inline {idx+1}"})
    for attrs in body_images(body):
        src = attrs.get("src") or attrs.get("data-src")
        if src and src.startswith(("http://", "https://")):
            errors.append(f"hotlinked image: {src}")
        if src:
            image_entries.append({"file": src, "alt": attrs.get("alt"), "caption": None, "role": "body"})
    credits = meta.get("photo_credits") or []
    credit_by_file = {str(c.get("file") or c.get("path") or ""): c for c in credits if isinstance(c, dict)}
    figure_captions = captions(body)
    captioned_files = figure_caption_files(body)
    normalized = {}
    for entry in image_entries:
        file_value = str(entry.get("file") or "")
        if file_value.startswith(("http://", "https://")):
            errors.append(f"hotlinked image in front matter: {file_value}")
            continue
        path = local_path(file_value)
        if not path:
            errors.append(f"image must be local under assets/images/posts: {file_value}")
            continue
        key = "/" + path.relative_to(ROOT).as_posix()
        normalized.setdefault(key, {"path": path, "alts": [], "captions": [], "roles": []})
        normalized[key]["roles"].append(entry.get("role"))
        if entry.get("alt"):
            normalized[key]["alts"].append(str(entry.get("alt")).strip())
        if entry.get("caption"):
            normalized[key]["captions"].append(str(entry.get("caption")).strip())
    if len(normalized) < 3:
        errors.append("fewer than three local images")
    if len(set(normalized)) != len(normalized):
        errors.append("duplicate image references")
    for key, item in normalized.items():
        path = item["path"]
        if not path.exists():
            errors.append(f"image file does not exist: {key}")
            continue
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            errors.append(f"unsupported image format: {key}")
        try:
            size = image_size(path)
            if size not in REQUIRED_IMAGE_SIZES:
                errors.append(f"invalid image dimensions for {key}: {size[0]}x{size[1]}")
        except Exception as exc:
            errors.append(f"cannot inspect image {key}: {exc}")
        if not any(item["alts"]):
            errors.append(f"missing alt text for {key}")
        if not (any(item["captions"]) or key in captioned_files or any(key in c for c in figure_captions)):
            errors.append(f"missing caption for {key}")
        credit = credit_by_file.get(key) or credit_by_file.get(key.lstrip("/"))
        if not credit:
            errors.append(f"missing photo credit for {key}")
            continue
        for field in ("creator", "source", "license", "license_url", "modifications"):
            if not credit.get(field):
                errors.append(f"incomplete photo credit {field} for {key}")
        if credit.get("source") and not host_matches(credit.get("source"), ALLOWED_IMAGE_SOURCE_DOMAINS):
            errors.append(f"unapproved image source for {key}: {credit.get('source')}")
        if not license_allowed(credit.get("license", ""), credit.get("license_url", "")):
            errors.append(f"image license is not clearly reusable for {key}")


def validate(path):
    text = Path(path).read_text(encoding="utf-8")
    errors = []
    if not text.startswith("---"):
        errors.append("missing front matter")
        return errors
    parts = text.split("---", 2)
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    if "generated_with_ai" in meta or "generated_with_ai" in text:
        errors.append("generated_with_ai must not appear in public content")
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
    if sources and not any(public_health_url(s.get("url", "")) for s in sources):
        errors.append("no government/WHO/approved public-health source")
    for s in sources:
        if not s.get("title") or not s.get("url"):
            errors.append("incomplete source")
        elif not approved_url(s.get("url", "")):
            errors.append(f"unapproved source domain: {s.get('url')}")
    if re.search(r"(?i)https?://[^\s]+(?:openai|chatgpt)", body):
        errors.append("AI service is not a health evidence source")
    validate_images(meta, body, errors)
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
