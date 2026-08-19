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
8. Every generated post must include at least three original accessible images: one SVG cover image and at least two inline SVG editorial images. Each image requires meaningful Traditional Chinese alt text and a useful caption.
9. Store all three or more images under `assets/images/posts/`. Use 1200×630 for the cover and 1200×800 or 1200×630 for inline images.
10. Generated SVG files may contain static SVG primitives only. Never include scripts, `foreignObject`, embedded raster/base64 data, external URLs, third-party logos, real-person likenesses, or treatment claims.
11. Create the post and every required image in one atomic commit. If the post has fewer than three images, any image lacks alt text, or any required file fails validation, publish nothing.
12. If evidence conflicts or safety is uncertain, do not publish.

## Real-photo editorial standard

- Prefer authentic, legally reusable photographs over generated illustrations, especially for destinations, buildings, food, transport, events, and other subjects where visual accuracy matters.
- Use only user-owned photos or sources with explicit reusable terms such as CC0, CC BY, CC BY-SA, or another license that clearly permits this website's use. A public webpage or official social-media post is not sufficient permission by itself.
- Never hotlink. Download the permitted original, preserve its source record, create a local optimized WebP/JPEG derivative, and commit it under `assets/images/posts/`.
- Record each photo's creator, source URL, license name, license URL, and modifications in the post front matter under `photo_credits`. Display concise attribution when the license requires it.
- Allowed processing: responsive crop, straightening, exposure/contrast/color correction, light sharpening, and web compression. Never add or remove people, objects, signs, safety conditions, or landmark details in a way that misrepresents reality.
- Prefer non-identifiable scenery and place photography. Do not use identifiable private individuals without a clear model release or permission.
- For each post, aim for all three required images to be real photographs. If fewer than three suitably licensed real photos are available, do not mislabel an illustration as a real scene; either block publication or clearly use a non-deceptive editorial graphic only when the subject does not require factual visual accuracy.
