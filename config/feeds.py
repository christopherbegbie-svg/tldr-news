"""
Curated list of high-quality global RSS news feeds.
Each entry has a name, URL, category, and source trust score (0-1).
Higher trust = more likely to be selected when stories score equally.
"""

RSS_FEEDS = [
    # ── World / Top News ──────────────────────────────────────────────────
    {
        "name": "AP News",
        "url": "https://feeds.apnews.com/rss/apf-topnews",
        "category": "world",
        "trust": 1.0,
    },
    {
        "name": "Sky News",
        "url": "https://feeds.skynews.com/feeds/rss/world.xml",
        "category": "world",
        "trust": 0.9,
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
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "technology",
        "trust": 0.9,
    },
    # ── Business / Economy ────────────────────────────────────────────────
    {
        "name": "BBC Business",
        "url": "http://feeds.bbci.co.uk/news/business/rss.xml",
        "category": "business",
        "trust": 0.9,
    },
    {
        "name": "Financial Times",
        "url": "https://www.ft.com/world?format=rss",
        "category": "business",
        "trust": 0.95,
    },
    # ── Science ───────────────────────────────────────────────────────────
    {
        "name": "BBC Science",
        "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "category": "science",
        "trust": 0.9,
    },
    {
        "name": "New Scientist",
        "url": "https://www.newscientist.com/feed/home/",
        "category": "science",
        "trust": 0.9,
    },
    # ── Regional voices ───────────────────────────────────────────────────
    {
        "name": "The Hindu",
        "url": "https://www.thehindu.com/news/international/?service=rss",
        "category": "world",
        "trust": 0.8,
    },
]
