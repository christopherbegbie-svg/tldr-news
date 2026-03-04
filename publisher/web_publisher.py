"""
Generates static HTML pages for the TLDR website (docs/ → GitHub Pages).

Each posting cycle produces:
  docs/posts/YYYY-MM-DD-slug.html  — individual story page
  docs/stories.json                — lightweight data store for the index
  docs/index.html                  — rebuilt from stories.json
  docs/sitemap.xml                 — rebuilt from stories.json
"""

from __future__ import annotations

import html
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from news.models import Article
from summarizer.claude_client import SummaryResult

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
POSTS_DIR = DOCS_DIR / "posts"

X_HANDLE = "TLDRGlobalNews"
IG_HANDLE = "TLDRGlobalNews"
SITE_URL = "https://tldrglobalnews.com"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:60].rstrip("-")


def _parse_facts(instagram_caption: str) -> list[str]:
    """Extract the 🔹 bullet points from the Instagram caption."""
    return re.findall(r"🔹\s*(.+)", instagram_caption)[:5]


# ── HTML templates ─────────────────────────────────────────────────────────────

def _adsense_block(publisher_id: str) -> str:
    return f"""<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{html.escape(publisher_id)}"
     data-ad-slot="auto"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>"""


def _story_page(
    article: Article,
    summary: SummaryResult,
    image_url: Optional[str],
    adsense_id: Optional[str],
    slug: str,
    recent_stories: list[dict],
) -> str:
    headline = html.escape(summary.get("card_headline", article.title))
    subheadline = html.escape(summary.get("card_subheadline", ""))
    source = html.escape(article.source)
    category_class = html.escape(article.category.lower())
    category = html.escape(article.category.upper())
    article_url = html.escape(article.url)
    date_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    canonical_url = f"{SITE_URL}/posts/{slug}.html"

    facts = _parse_facts(summary.get("instagram_caption", ""))
    facts_html = "\n".join(f"<li>{html.escape(f)}</li>" for f in facts)
    description = html.escape(facts[0] if facts else subheadline)

    image_tag = (
        f'<img src="{html.escape(image_url)}" alt="{headline}" class="card-image">'
        if image_url else ""
    )

    adsense_script_tag = (
        f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
        f'?client={html.escape(adsense_id)}" crossorigin="anonymous"></script>'
        if adsense_id else ""
    )
    ad_block = _adsense_block(adsense_id) if adsense_id else ""

    og_image = f'<meta property="og:image" content="{html.escape(image_url)}">' if image_url else ""

    # JSON-LD NewsArticle schema
    schema_image = f'"{html.escape(image_url)}"' if image_url else 'null'
    schema_headline = summary.get('card_headline', article.title).replace('"', '&quot;')
    schema_description = (facts[0] if facts else subheadline).replace('"', '&quot;')
    json_ld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{schema_headline}",
  "description": "{schema_description}",
  "datePublished": "{date_iso}",
  "image": {schema_image},
  "url": "{canonical_url}",
  "author": {{
    "@type": "Organization",
    "name": "TLDR News",
    "url": "{SITE_URL}"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "TLDR News",
    "url": "{SITE_URL}"
  }}
}}
</script>"""

    # Recent stories section (up to 4, excluding current)
    recent_cards = []
    for s in recent_stories[:4]:
        r_slug = s.get("slug", "")
        r_title = html.escape(s.get("title", ""))
        r_cat = s.get("category", "world")
        r_cat_class = html.escape(r_cat.lower())
        r_cat_label = html.escape(r_cat.upper())
        r_date = s.get("date", "")
        r_source = html.escape(s.get("source", ""))
        r_img = s.get("image_url", "")
        r_thumb = (
            f'<img src="{html.escape(r_img)}" alt="{r_title}" class="card-thumb" loading="lazy">'
            if r_img else '<div class="card-thumb-placeholder">TLDR</div>'
        )
        recent_cards.append(f"""    <a href="{r_slug}.html" class="story-card">
      {r_thumb}
      <div class="card-body">
        <div class="card-top">
          <span class="chip {r_cat_class}">{r_cat_label}</span>
          <span class="source">{r_source}</span>
        </div>
        <h2>{r_title}</h2>
        <time class="date">{r_date}</time>
      </div>
    </a>""")

    recent_section = ""
    if recent_cards:
        recent_section = f"""
    <p class="section-label" style="margin-top:3rem">More Stories</p>
    <div class="grid" style="margin-bottom:2rem">
{"".join(recent_cards)}
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{headline} | TLDR News</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{headline} | TLDR News">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical_url}">
  {og_image}
  <meta property="og:type" content="article">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="../assets/style.css">
  {adsense_script_tag}
  {json_ld}
</head>
<body>
  <header>
    <a href="../index.html" class="logo">TLDR</a>
    <span class="tagline">Your daily global news digest</span>
  </header>

  <main class="story">
    <div class="meta">
      <span class="chip {category_class}">{category}</span>
      <time class="date">{date_str}</time>
    </div>
    <h1>{headline}</h1>
    {f'<p class="subheadline">{subheadline}</p>' if subheadline else ""}

    {image_tag}

    {ad_block}

    <ul class="facts">
      {facts_html}
    </ul>

    <div class="source-link">
      <a href="{article_url}" target="_blank" rel="noopener noreferrer">
        Read full story at {source} &rarr;
      </a>
    </div>

    {ad_block}
    {recent_section}
  </main>

  <footer>
    <p>
      TLDR News &mdash;
      <a href="../index.html">All stories</a> &mdash;
      <a href="https://twitter.com/{X_HANDLE}" target="_blank">@{X_HANDLE}</a> &mdash;
      <a href="https://instagram.com/{IG_HANDLE}" target="_blank">{IG_HANDLE}</a> &mdash;
      <a href="../privacy.html">Privacy Policy</a>
    </p>
  </footer>
</body>
</html>"""


def _index_page(stories: list[dict]) -> str:
    year = datetime.utcnow().year
    hero_html = ""
    grid_html = ""

    if stories:
        s = stories[0]
        slug = s.get("slug", "")
        headline = html.escape(s.get("title", ""))
        cat = s.get("category", "world")
        cat_class = html.escape(cat.lower())
        cat_label = html.escape(cat.upper())
        date = html.escape(s.get("date", ""))
        source = html.escape(s.get("source", ""))
        img_url = s.get("image_url", "")

        img_html = (
            f'<img src="{html.escape(img_url)}" alt="{headline}" class="hero-img" loading="lazy">'
            if img_url else '<div class="hero-img-placeholder">TLDR</div>'
        )

        hero_html = f"""  <p class="section-label">Latest</p>
  <a href="posts/{slug}.html" class="hero">
    {img_html}
    <div class="hero-body">
      <div class="hero-eyebrow">
        <span class="chip {cat_class}">{cat_label}</span>
      </div>
      <h2>{headline}</h2>
      <div class="hero-meta">
        <span>{source}</span><span>{date}</span>
      </div>
      <span class="hero-arrow">Read story &rarr;</span>
    </div>
  </a>"""

    if len(stories) > 1:
        cards = []
        for s in stories[1:]:
            slug = s.get("slug", "")
            headline = html.escape(s.get("title", ""))
            cat = s.get("category", "world")
            cat_class = html.escape(cat.lower())
            cat_label = html.escape(cat.upper())
            date = s.get("date", "")
            source = html.escape(s.get("source", ""))
            img_url = s.get("image_url", "")

            thumb = (
                f'<img src="{html.escape(img_url)}" alt="{headline}" class="card-thumb" loading="lazy">'
                if img_url else '<div class="card-thumb-placeholder">TLDR</div>'
            )

            cards.append(f"""    <a href="posts/{slug}.html" class="story-card">
      {thumb}
      <div class="card-body">
        <div class="card-top">
          <span class="chip {cat_class}">{cat_label}</span>
          <span class="source">{source}</span>
        </div>
        <h2>{headline}</h2>
        <time class="date">{date}</time>
      </div>
    </a>""")

        cards_html = "\n".join(cards)
        grid_html = f"""
  <p class="section-label" style="margin-top:2.5rem">More Stories</p>
  <div class="grid">
{cards_html}
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TLDR News &mdash; Your daily global news digest</title>
  <meta name="description" content="TLDR: factual, neutral global news digest. Updated every few hours.">
  <link rel="canonical" href="{SITE_URL}/">
  <meta property="og:title" content="TLDR News">
  <meta property="og:description" content="Factual, neutral global news digest. Updated every few hours.">
  <meta property="og:url" content="{SITE_URL}/">
  <meta name="twitter:card" content="summary">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header class="home-header">
    <div class="logo">TLDR</div>
    <p class="tagline">Your daily global news digest</p>
    <p class="follow">
      <a href="https://twitter.com/{X_HANDLE}" target="_blank">X / Twitter</a>
      &bull;
      <a href="https://instagram.com/{IG_HANDLE}" target="_blank">Instagram</a>
    </p>
  </header>

  <main class="index">
{hero_html}{grid_html}
  </main>

  <footer>
    <p>TLDR News &copy; {year} &mdash; Updated automatically throughout the day &mdash; <a href="privacy.html">Privacy Policy</a></p>
  </footer>
</body>
</html>"""


def _sitemap(stories: list[dict]) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    urls = [f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>"""]
    for s in stories:
        slug = s.get("slug", "")
        # Extract date from slug prefix (YYYY-MM-DD-...)
        date_part = slug[:10] if len(slug) >= 10 else today
        urls.append(f"""  <url>
    <loc>{SITE_URL}/posts/{slug}.html</loc>
    <lastmod>{date_part}</lastmod>
    <changefreq>never</changefreq>
    <priority>0.8</priority>
  </url>""")
    url_block = "\n".join(urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{url_block}
</urlset>"""


# ── Public API ─────────────────────────────────────────────────────────────────

def publish_story(
    article: Article,
    summary: SummaryResult,
    image_url: Optional[str] = None,
    adsense_id: Optional[str] = None,
) -> Optional[str]:
    """
    Generate the story HTML page and rebuild the index + sitemap.
    Returns the story slug, or None on failure.
    """
    try:
        DOCS_DIR.mkdir(exist_ok=True)
        POSTS_DIR.mkdir(exist_ok=True)
        (DOCS_DIR / "assets").mkdir(exist_ok=True)

        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
        slug = f"{date_prefix}-{_slug(summary.get('card_headline', article.title))}"

        # Update stories index (JSON) first so recent_stories is available
        stories_file = DOCS_DIR / "stories.json"
        stories: list[dict] = (
            json.loads(stories_file.read_text(encoding="utf-8"))
            if stories_file.exists() else []
        )
        if not any(s.get("slug") == slug for s in stories):
            stories.insert(0, {
                "slug": slug,
                "title": summary.get("card_headline", article.title),
                "category": article.category,
                "source": article.source,
                "date": datetime.utcnow().strftime("%B %d, %Y"),
                "image_url": image_url or "",
            })
        stories = stories[:100]  # keep last 100
        stories_file.write_text(json.dumps(stories, indent=2), encoding="utf-8")

        # Recent stories for "More Stories" section (exclude current)
        recent = [s for s in stories if s.get("slug") != slug]

        # Write story page
        story_html = _story_page(article, summary, image_url, adsense_id, slug, recent)
        (POSTS_DIR / f"{slug}.html").write_text(story_html, encoding="utf-8")

        # Rebuild index.html
        (DOCS_DIR / "index.html").write_text(_index_page(stories), encoding="utf-8")

        # Rebuild sitemap.xml
        (DOCS_DIR / "sitemap.xml").write_text(_sitemap(stories), encoding="utf-8")

        logger.info("Web story published: docs/posts/%s.html", slug)
        return slug

    except Exception as exc:
        logger.error("Web publish failed: %s", exc)
        return None
