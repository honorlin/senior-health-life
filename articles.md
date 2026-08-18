---
layout: default
title: 最新文章
permalink: /articles/
---
<section class="page-hero"><div class="wrap"><p class="eyebrow"><span></span>健康知識庫</p><h1>熟齡健康生活文章</h1><p class="lead">清楚、可信、容易實踐。從日常小事開始，找到適合自己的生活節奏。</p></div></section>
<section><div class="wrap"><div class="article-grid">{% for post in site.posts %}<article class="article-card" id="{{ post.category }}"><a class="article-image" href="{{ post.url | relative_url }}">{% if post.image %}<img src="{{ post.image | relative_url }}" alt="{{ post.image_alt | default: post.title | escape }}" width="1200" height="630" loading="lazy">{% else %}<span class="image-placeholder"><i></i></span>{% endif %}</a><div class="article-body"><span class="article-category">{{ post.category_name | default: post.category }}</span><h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2><p>{{ post.description }}</p><div class="article-meta"><time>{{ post.date | date: "%Y年%m月%d日" }}</time><a href="{{ post.url | relative_url }}">閱讀 →</a></div></div></article>{% else %}<p>文章準備中。</p>{% endfor %}</div></div></section>