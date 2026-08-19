# Repository instructions

This repository publishes a Traditional Chinese senior wellbeing site for Taiwan.

## Non-negotiable rules

1. Never add medical diagnosis, treatment, medication adjustment, or emergency triage advice.
2. Never claim that food or supplements prevent, improve, or treat disease.
3. Auto-published content must be green or blue risk only and cite approved sources.
4. Keep Taiwanese Traditional Chinese, senior-friendly typography, short paragraphs, and calm tone.
5. Cover the full senior-life scope: 食、衣、住、行、育、樂、活動、睡眠、心情、陪伴、保健知識與數位安全. Prefer categories underrepresented in the previous 30 days.
6. Never commit API keys, credentials, personal health data, customer data, or .env files.
7. Run `python scripts/validate_content.py <file>` before committing a generated post.
8. Every generated post must include one original accessible SVG cover image at `assets/images/posts/YYYY-MM-DD-slug.svg`, plus `image` and meaningful Traditional Chinese `image_alt` front matter.
9. Generated SVG files must use a 1200×630 viewBox and static SVG primitives only. Never include scripts, `foreignObject`, embedded raster/base64 data, external URLs, third-party logos, real-person likenesses, or treatment claims.
10. Create the post and its cover image together. If either file fails validation or cannot be committed, publish neither.
11. If evidence conflicts or safety is uncertain, do not publish.
