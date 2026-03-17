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
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
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
    {
        "name": "Scientific American",
        "url": "https://www.scientificamerican.com/feed/",
        "category": "science",
        "trust": 0.9,
    },
    # ── Economics ─────────────────────────────────────────────────────────
    {
        "name": "Economist Free",
        "url": "https://www.economist.com/finance-and-economics/rss.xml",
        "category": "economics",
        "trust": 0.95,
    },
    {
        "name": "NPR Economics",
        "url": "https://feeds.npr.org/1017/rss.xml",
        "category": "economics",
        "trust": 0.9,
    },
    # ── History ───────────────────────────────────────────────────────────
    {
        "name": "BBC History",
        "url": "http://feeds.bbci.co.uk/history/rss.xml",
        "category": "history",
        "trust": 0.9,
    },
    {
        "name": "Smithsonian Magazine",
        "url": "https://www.smithsonianmag.com/rss/latest_articles/",
        "category": "history",
        "trust": 0.85,
    },
    # ── Math ──────────────────────────────────────────────────────────────
    {
        "name": "AMS News",
        "url": "https://www.ams.org/rss/news.xml",
        "category": "math",
        "trust": 0.9,
    },
    # ── Literature ────────────────────────────────────────────────────────
    {
        "name": "The Guardian Books",
        "url": "https://www.theguardian.com/books/rss",
        "category": "literature",
        "trust": 0.9,
    },
    # ── Physics ───────────────────────────────────────────────────────────
    {
        "name": "Physics World",
        "url": "https://physicsworld.com/feed/",
        "category": "physics",
        "trust": 0.9,
    },
    # ── Engineering ───────────────────────────────────────────────────────
    {
        "name": "IEEE Spectrum",
        "url": "https://spectrum.ieee.org/rss",
        "category": "engineering",
        "trust": 0.9,
    },
    # ── Farming/Agriculture ───────────────────────────────────────────────
    {
        "name": "USDA News",
        "url": "https://www.usda.gov/rss/usda.xml",
        "category": "farming",
        "trust": 0.8,
    },
    # ── AI ────────────────────────────────────────────────────────────────
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "category": "ai",
        "trust": 0.9,
    },
    {
        "name": "AI News",
        "url": "https://artificialintelligence-news.com/feed/",
        "category": "ai",
        "trust": 0.8,
    },
    # ── Coding ────────────────────────────────────────────────────────────
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "category": "coding",
        "trust": 0.7,
    },
    {
        "name": "Reddit Programming",
        "url": "https://www.reddit.com/r/programming/.rss",
        "category": "coding",
        "trust": 0.6,
    },
    # ── Regional voices ───────────────────────────────────────────────────
    {
        "name": "The Hindu",
        "url": "https://www.thehindu.com/news/international/?service=rss",
        "category": "world",
        "trust": 0.8,
    },
    # ── Politics ──────────────────────────────────────────────────────────
    {
        "name": "Politico",
        "url": "https://rss.politico.com/politics-news.xml",
        "category": "politics",
        "trust": 0.95,
    },
    {
        "name": "NPR Politics",
        "url": "https://feeds.npr.org/1014/rss.xml",
        "category": "politics",
        "trust": 0.9,
    },
    {
        "name": "The Guardian World Politics",
        "url": "https://www.theguardian.com/world/rss",
        "category": "politics",
        "trust": 0.9,
    },
    {
        "name": "BBC Politics",
        "url": "http://feeds.bbci.co.uk/news/politics/rss.xml",
        "category": "politics",
        "trust": 0.9,
    },
]
