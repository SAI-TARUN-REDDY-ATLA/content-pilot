"""Upload a finished Short with the YouTube Data API (videos.insert, ~1,600 quota units)."""

import os
from pathlib import Path

from .auth import credentials

# Education. People & Blogs is 22, Howto & Style is 26.
CATEGORY_ID = os.getenv("CONTENT_PILOT_CATEGORY", "27")
PRIVACY = os.getenv("CONTENT_PILOT_PRIVACY", "public")


def shorts_title(title: str) -> str:
    """YouTube titles cap at 100 characters; #Shorts helps classification when there's room."""
    tagged = f"{title} #Shorts"
    return tagged if len(tagged) <= 100 else title[:100]


def build_body(title: str, description: str, hashtags: list[str]) -> dict:
    tags_line = " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    return {
        "snippet": {
            "title": shorts_title(title),
            "description": f"{description}\n\n{tags_line} #Shorts".strip(),
            "tags": [h.lstrip("#") for h in hashtags],
            "categoryId": CATEGORY_ID,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": PRIVACY,
            "selfDeclaredMadeForKids": False,
            # Narrated advice over background footage isn't "realistic altered content", so no
            # disclosure by default. Set CONTENT_PILOT_SYNTHETIC=1 if your videos change that.
            "containsSyntheticMedia": os.getenv("CONTENT_PILOT_SYNTHETIC") == "1",
        },
    }


def upload(video: Path, title: str, description: str, hashtags: list[str]) -> dict:
    """Upload and return {"id", "url", "privacy"}. Raises on API errors."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube = build("youtube", "v3", credentials=credentials(), cache_discovery=False)
    request = youtube.videos().insert(
        part="snippet,status",
        body=build_body(title, description, hashtags),
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    vid = response["id"]
    return {"id": vid, "url": f"https://youtube.com/shorts/{vid}",
            "privacy": response.get("status", {}).get("privacyStatus", PRIVACY)}
