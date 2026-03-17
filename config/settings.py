from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str

    # X / Twitter
    x_api_key: Optional[str] = None
    x_api_secret: Optional[str] = None
    x_access_token: Optional[str] = None
    x_access_secret: Optional[str] = None
    x_bearer_token: Optional[str] = None

    # Meta / Instagram
    meta_page_access_token: Optional[str] = None
    instagram_account_id: Optional[str] = None
    imgbb_api_key: Optional[str] = None

    # NewsAPI
    newsapi_key: Optional[str] = None

    # Website / AdSense (optional — add once AdSense account approved)
    adsense_publisher_id: Optional[str] = None  # e.g. ca-pub-XXXXXXXXXXXXXXXX

    # Scheduling (comma-separated 24h times, UTC)
    post_times: str = "09:00,18:00"

    # Behaviour
    dry_run: bool = False

    @property
    def post_times_list(self) -> list[str]:
        return [t.strip() for t in self.post_times.split(",") if t.strip()]

    @property
    def x_enabled(self) -> bool:
        return all([self.x_api_key, self.x_api_secret,
                    self.x_access_token, self.x_access_secret])

    @property
    def instagram_enabled(self) -> bool:
        return all([self.meta_page_access_token, self.instagram_account_id, self.imgbb_api_key])

    @property
    def newsapi_enabled(self) -> bool:
        return bool(self.newsapi_key)

    @property
    def data_dir(self) -> Path:
        d = BASE_DIR / "data"
        d.mkdir(exist_ok=True)
        return d

    @property
    def db_path(self) -> Path:
        return self.data_dir / "posted_stories.db"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
