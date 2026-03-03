"""
Anthropic Claude wrapper — summarizes articles into structured post content.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TypedDict

import anthropic

from config.settings import get_settings
from news.models import Article
from summarizer.prompts import SYSTEM_PROMPT, build_prompt

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"  # Fast and cost-efficient


class SummaryResult(TypedDict):
    headline: str
    x_thread: list[str]
    instagram_caption: str
    card_headline: str
    card_subheadline: str


_FALLBACK: SummaryResult = {
    "headline": "Breaking news",
    "x_thread": ["🌍 TLDR | WORLD — Breaking news. Check the source for details. #TLDR"],
    "instagram_caption": "• Breaking news — details emerging.\n\n#tldr #news #worldnews",
    "card_headline": "Breaking news",
    "card_subheadline": "Details emerging",
}


def summarize(article: Article) -> SummaryResult:
    """Call Claude to summarize the article. Returns a SummaryResult dict."""
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = build_prompt(
        title=article.title,
        source=article.source,
        category=article.category,
        summary=article.summary,
        url=article.url,
    )

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        # Extract JSON (handle any leading/trailing noise)
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in Claude response")

        data = json.loads(json_match.group())
        result: SummaryResult = {
            "headline": data.get("headline", article.title[:80]),
            "x_thread": data.get("x_thread", [_FALLBACK["x_thread"][0]]),
            "instagram_caption": data.get("instagram_caption", _FALLBACK["instagram_caption"]),
            "card_headline": data.get("card_headline", article.title[:50]),
            "card_subheadline": data.get("card_subheadline", article.source),
        }
        return result

    except Exception as exc:
        logger.error("Claude summarization failed for '%s': %s", article.title, exc)
        return None
