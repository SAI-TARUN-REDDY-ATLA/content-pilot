"""Upload a finished video with the YouTube Data API (videos.insert ~1,600 quota units,
thumbnails.set ~50)."""

import os
from pathlib import Path

from .auth import credentials

# Education. Entertainment is 24, People & Blogs is 22.
CATEGORY_ID = os.getenv("CONTENT_PILOT_CATEGORY", "27")
PRIVACY = os.getenv("CONTENT_PILOT_PRIVACY", "public")


def build_body(title: str, description: str, hashtags: list[str], chapters: str = "") -> dict:
    tags_line = " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    parts = [description, chapters, tags_line]
    return {
        "snippet": {
            "title": title[:100],
            "description": "\n\n".join(p for p in parts if p).strip(),
            "tags": [h.lstrip("#") for h in hashtags],
            "categoryId": CATEGORY_ID,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": PRIVACY,
            "selfDeclaredMadeForKids": False,
            # Cartoon illustrations of history aren't "realistic altered content", so no disclosure
            # by default. Set CONTENT_PILOT_SYNTHETIC=1 if your videos change that.
            "containsSyntheticMedia": os.getenv("CONTENT_PILOT_SYNTHETIC") == "1",
        },
    }


def upload(video: Path, title: str, description: str, hashtags: list[str], chapters: str = "",
           thumbnail: Path | None = None) -> dict:
    """Upload and return {"id", "url", "privacy", "thumbnail"}. Raises on API errors.
    A rejected thumbnail (custom thumbnails need a phone-verified channel) is reported, not raised."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube = build("youtube", "v3", credentials=credentials(), cache_discovery=False)
    request = youtube.videos().insert(
        part="snippet,status",
        body=build_body(title, description, hashtags, chapters),
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    vid = response["id"]
    thumb_status = "none"
    if thumbnail and Path(thumbnail).exists():
        try:
            youtube.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumbnail), mimetype="image/jpeg")).execute()
            thumb_status = "set"
        except Exception as e:
            thumb_status = f"failed: {e}"
    return {"id": vid, "url": f"https://www.youtube.com/watch?v={vid}",
            "privacy": response.get("status", {}).get("privacyStatus", PRIVACY), "thumbnail": thumb_status}
