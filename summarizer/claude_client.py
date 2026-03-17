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
    video_script: str


_FALLBACK: SummaryResult = {
    "headline": "Fascinating discovery",
    "x_thread": ["🌍 60 Seconds of Wisdom | SCIENCE — Did you know this amazing fact? Check it out. #60SecondsWisdom #BroadKnowledge"],
    "instagram_caption": "• Fascinating topic — learn something new.\n\nWatch daily for broad knowledge!\n\n#60secondsofwisdom #wisdom #learn #broadknowledge",
    "card_headline": "Fascinating discovery",
    "card_subheadline": "Learn something new today",
    "video_script": "Today we're exploring a fascinating topic. Here's what you need to know in simple terms. This concept matters because... Check the source for more details."
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

    for attempt in range(2):
        try:
            messages = [{"role": "user", "content": prompt}]
            if attempt == 1:
                # Second attempt: reinforce JSON-only instruction
                messages.append({"role": "assistant", "content": "{"})

            message = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            raw = message.content[0].text.strip()
            if attempt == 1:
                raw = "{" + raw

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
            logger.warning("Claude attempt %d failed for '%s': %s", attempt + 1, article.title, exc)

    logger.error("Claude summarization failed after 2 attempts for '%s'", article.title)
    return None
