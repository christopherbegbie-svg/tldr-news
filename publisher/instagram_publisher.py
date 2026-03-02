"""
Posts images to Instagram via the official Meta Graph API.

Flow:
  1. Upload image as a media container  →  container_id
  2. Poll until container status = FINISHED
  3. Publish the container              →  post_id
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import requests

from config.settings import get_settings

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0"
POLL_INTERVAL = 5    # seconds between status polls
POLL_MAX = 12        # max polls (60s total)


def _api(method: str, path: str, **kwargs) -> dict:
    """Helper for Meta Graph API calls."""
    settings = get_settings()
    kwargs.setdefault("params", {})["access_token"] = settings.meta_page_access_token
    resp = requests.request(method, f"{GRAPH_URL}/{path}", **kwargs)
    resp.raise_for_status()
    return resp.json()


def _upload_image_to_cdn(image_path: Path) -> str:
    """
    Instagram Graph API requires the image to be at a publicly accessible URL.
    For local files we use the Graph API's file upload endpoint via form-data.

    Returns the media container ID.
    """
    settings = get_settings()
    ig_id = settings.instagram_account_id

    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{GRAPH_URL}/{ig_id}/media",
            params={"access_token": settings.meta_page_access_token},
            files={"image_file": (image_path.name, f, "image/png")},
            data={"media_type": "IMAGE"},
        )
    resp.raise_for_status()
    return resp.json()["id"]


def _wait_for_ready(container_id: str) -> bool:
    """Poll until the media container is FINISHED."""
    for attempt in range(POLL_MAX):
        data = _api("GET", container_id, params={"fields": "status_code"})
        status = data.get("status_code", "")
        logger.debug("Container %s status: %s (attempt %d)", container_id, status, attempt + 1)
        if status == "FINISHED":
            return True
        if status == "ERROR":
            logger.error("Media container %s failed with ERROR", container_id)
            return False
        time.sleep(POLL_INTERVAL)
    logger.error("Timed out waiting for media container %s", container_id)
    return False


def post(image_path: Path, caption: str, dry_run: bool = False) -> Optional[str]:
    """
    Upload image and caption to Instagram.
    Returns the post ID, or None on failure.
    """
    if dry_run:
        safe = lambda s: s.encode("ascii", errors="replace").decode("ascii")
        print("\n-- Instagram Post (DRY RUN) --------------------------------")
        print(f"  Image: {image_path}")
        print(f"  Caption:\n{safe(caption)}")
        print("-----------------------------------------------------------\n")
        return "dry-run://instagram/post"

    settings = get_settings()
    if not settings.instagram_enabled:
        logger.warning("Instagram not configured — skipping.")
        return None

    ig_id = settings.instagram_account_id

    try:
        # Step 1: Create media container
        container_id = _upload_image_to_cdn(image_path)
        logger.info("Instagram media container created: %s", container_id)

        # Step 2: Wait for processing
        if not _wait_for_ready(container_id):
            return None

        # Step 3: Add caption (update container)
        _api(
            "POST",
            container_id,
            data={"caption": caption[:2200]},  # Instagram caption limit
        )

        # Step 4: Publish
        result = _api(
            "POST",
            f"{ig_id}/media_publish",
            data={"creation_id": container_id},
        )
        post_id = result.get("id")
        logger.info("Instagram post published: %s", post_id)
        return post_id

    except requests.HTTPError as exc:
        logger.error("Instagram API HTTP error: %s — %s", exc.response.status_code, exc.response.text)
        return None
    except Exception as exc:
        logger.error("Instagram post failed: %s", exc)
        return None
