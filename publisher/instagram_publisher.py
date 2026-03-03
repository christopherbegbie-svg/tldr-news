"""
Posts images to Instagram via the Instagram Business Login API (graph.instagram.com).

Flow:
  1. Upload image to imgbb to get a public URL
  2. Create a media container with the image URL + caption
  3. Poll until container status = FINISHED
  4. Publish the container  →  post_id
"""

from __future__ import annotations

import base64
import logging
import time
from pathlib import Path
from typing import Optional

import requests

from config.settings import get_settings

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.instagram.com/v21.0"
POLL_INTERVAL = 5    # seconds between status polls
POLL_MAX = 12        # max polls (60s total)


def _upload_to_imgbb(image_path: Path, api_key: str) -> str:
    """Upload image to imgbb and return a public URL (expires after 1 hour)."""
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": image_b64, "expiration": 3600},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]["url"]


def upload_for_web(image_path: Path) -> Optional[str]:
    """Upload image to imgbb permanently (no expiry) for use on the website."""
    settings = get_settings()
    if not settings.imgbb_api_key:
        return None
    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": settings.imgbb_api_key, "image": image_b64},
            timeout=30,
        )
        resp.raise_for_status()
        url = resp.json()["data"]["url"]
        logger.info("Image uploaded permanently for web: %s", url)
        return url
    except Exception as exc:
        logger.error("imgbb permanent upload failed: %s", exc)
        return None


def _create_container(ig_id: str, image_url: str, caption: str, token: str) -> str:
    """Create an Instagram media container and return its ID."""
    resp = requests.post(
        f"{GRAPH_URL}/{ig_id}/media",
        params={"access_token": token},
        data={
            "image_url": image_url,
            "caption": caption[:2200],
            "media_type": "IMAGE",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _wait_for_ready(container_id: str, token: str) -> bool:
    """Poll until the media container is FINISHED."""
    for attempt in range(POLL_MAX):
        resp = requests.get(
            f"{GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=15,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code", "")
        logger.debug("Container %s status: %s (attempt %d)", container_id, status, attempt + 1)
        if status == "FINISHED":
            return True
        if status == "ERROR":
            logger.error("Media container %s failed with ERROR", container_id)
            return False
        time.sleep(POLL_INTERVAL)
    logger.error("Timed out waiting for media container %s", container_id)
    return False


def _publish(ig_id: str, container_id: str, token: str) -> str:
    """Publish a ready media container and return the post ID."""
    resp = requests.post(
        f"{GRAPH_URL}/{ig_id}/media_publish",
        params={"access_token": token},
        data={"creation_id": container_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


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
    token = settings.meta_page_access_token

    try:
        # Step 1: Get a public URL for the image
        image_url = _upload_to_imgbb(image_path, settings.imgbb_api_key)
        logger.info("Image hosted at: %s", image_url)

        # Step 2: Create media container
        container_id = _create_container(ig_id, image_url, caption, token)
        logger.info("Instagram media container created: %s", container_id)

        # Step 3: Wait for processing
        if not _wait_for_ready(container_id, token):
            return None

        # Step 4: Publish
        post_id = _publish(ig_id, container_id, token)
        logger.info("Instagram post published: %s", post_id)
        return post_id

    except requests.HTTPError as exc:
        logger.error(
            "Instagram API HTTP error: %s — %s",
            exc.response.status_code,
            exc.response.text,
        )
        return None
    except Exception as exc:
        logger.error("Instagram post failed: %s", exc)
        return None
