"""
Generates static HTML pages for the TLDR website (docs/ → GitHub Pages).

Each posting cycle produces:
  docs/posts/YYYY-MM-DD-slug.html  — individual story page
  docs/stories.json                — lightweight data store for the index
  docs/index.html                  — rebuilt from stories.json
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
) -> str:
    headline = html.escape(summary.get("card_headline", article.title))
    subheadline = html.escape(summary.get("card_subheadline", ""))
    source = html.escape(article.source)
    category_class = html.escape(article.category.lower())
    category = html.escape(article.category.upper())
    article_url = html.escape(article.url)
    date_str = datetime.utcnow().strftime("%B %d, %Y")

    facts = _parse_facts(summary.get("instagram_caption", ""))
    facts_html = "\n".join(f"<li>{html.escape(f)}</li>" for f in facts)

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
    description = html.escape(facts[0] if facts else subheadline)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{headline} | TLDR News</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{headline} | TLDR News">
  <meta property="og:description" content="{description}">
  {og_image}
  <meta property="og:type" content="article">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="../assets/style.css">
  {adsense_script_tag}
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
  <meta property="og:title" content="TLDR News">
  <meta property="og:description" content="Factual, neutral global news digest. Updated every few hours.">
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


# ── Public API ─────────────────────────────────────────────────────────────────

def publish_story(
    article: Article,
    summary: SummaryResult,
    image_url: Optional[str] = None,
    adsense_id: Optional[str] = None,
) -> Optional[str]:
    """
    Generate the story HTML page and rebuild the index.
    Returns the story slug, or None on failure.
    """
    try:
        DOCS_DIR.mkdir(exist_ok=True)
        POSTS_DIR.mkdir(exist_ok=True)
        (DOCS_DIR / "assets").mkdir(exist_ok=True)

        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
        slug = f"{date_prefix}-{_slug(summary.get('card_headline', article.title))}"

        # Write story page
        story_html = _story_page(article, summary, image_url, adsense_id)
        (POSTS_DIR / f"{slug}.html").write_text(story_html, encoding="utf-8")

        # Update stories index (JSON)
        stories_file = DOCS_DIR / "stories.json"
        stories: list[dict] = (
            json.loads(stories_file.read_text(encoding="utf-8"))
            if stories_file.exists() else []
        )
        # Avoid duplicates if cycle runs twice
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

        # Rebuild index.html
        (DOCS_DIR / "index.html").write_text(_index_page(stories), encoding="utf-8")

        logger.info("Web story published: docs/posts/%s.html", slug)
        return slug

    except Exception as exc:
        logger.error("Web publish failed: %s", exc)
        return None
