from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str          # Raw excerpt / description from feed
    category: str
    trust_score: float = 0.8   # Source trust (0-1)
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        # Hash on normalised title so near-duplicate headlines from different
        # sources share the same hash.
        normalised = self.title.lower().strip()
        self.content_hash = hashlib.sha256(normalised.encode()).hexdigest()

    @property
    def age_seconds(self) -> float:
        return (datetime.utcnow() - self.published_at).total_seconds()

    def score(self) -> float:
        """
        Higher = more worth posting.
        Combines source trust with a recency decay (half-life ≈ 6 hours).
        """
        import math
        half_life = 6 * 3600  # 6 hours in seconds
        recency = math.exp(-0.693 * self.age_seconds / half_life)
        return self.trust_score * recency
