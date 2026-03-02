"""
Curated list of high-quality global RSS news feeds.
Each entry has a name, URL, category, and source trust score (0-1).
Higher trust = more likely to be selected when stories score equally.
"""

RSS_FEEDS = [
    # ── World / Top News ──────────────────────────────────────────────────
    {
        "name": "Reuters",
        "url": "https://feeds.reuters.com/reuters/topNews",
        "category": "world",
        "trust": 1.0,
    },
    {
        "name": "AP News",
        "url": "https://feeds.apnews.com/rss/apf-topnews",
        "category": "world",
        "trust": 1.0,
    },
    {
        "name": "BBC World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "world",
        "trust": 0.95,
    },
    {
        "name": "The Guardian World",
        "url": "https://www.theguardian.com/world/rss",
        "category": "world",
        "trust": 0.9,
    },
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "world",
        "trust": 0.85,
    },
    {
        "name": "NPR News",
        "url": "https://feeds.npr.org/1001/rss.xml",
        "category": "world",
        "trust": 0.9,
    },
    {
        "name": "Deutsche Welle",
        "url": "https://rss.dw.com/xml/rss-en-world",
        "category": "world",
        "trust": 0.85,
    },
    {
        "name": "France 24",
        "url": "https://www.france24.com/en/rss",
        "category": "world",
        "trust": 0.85,
    },
    # ── Technology ────────────────────────────────────────────────────────
    {
        "name": "BBC Technology",
        "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "category": "technology",
        "trust": 0.9,
    },
    {
        "name": "Reuters Technology",
        "url": "https://feeds.reuters.com/reuters/technologyNews",
        "category": "technology",
        "trust": 1.0,
    },
    # ── Business / Economy ────────────────────────────────────────────────
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "category": "business",
        "trust": 1.0,
    },
    {
        "name": "BBC Business",
        "url": "http://feeds.bbci.co.uk/news/business/rss.xml",
        "category": "business",
        "trust": 0.9,
    },
    # ── Science ───────────────────────────────────────────────────────────
    {
        "name": "BBC Science",
        "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "category": "science",
        "trust": 0.9,
    },
    {
        "name": "Reuters Science",
        "url": "https://feeds.reuters.com/reuters/scienceNews",
        "category": "science",
        "trust": 1.0,
    },
    # ── Regional voices ───────────────────────────────────────────────────
    {
        "name": "The Hindu",
        "url": "https://www.thehindu.com/news/international/?service=rss",
        "category": "world",
        "trust": 0.8,
    },
]
