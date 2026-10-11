"""Pull retention numbers for uploaded videos from the YouTube Analytics API."""

from datetime import date, timedelta

from .auth import credentials

METRICS = "views,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained"


def video_stats(video_ids: list[str], since: date) -> dict[str, dict]:
    """Lifetime-to-date metrics per video id. Analytics lags ~2 days, so new videos may be missing."""
    from googleapiclient.discovery import build

    if not video_ids:
        return {}
    api = build("youtubeAnalytics", "v2", credentials=credentials(), cache_discovery=False)
    out: dict[str, dict] = {}
    for start in range(0, len(video_ids), 200):  # the video filter takes up to 200 ids
        batch = video_ids[start:start + 200]
        resp = api.reports().query(
            ids="channel==MINE", startDate=since.isoformat(),
            endDate=(date.today() - timedelta(days=1)).isoformat(),
            metrics=METRICS, dimensions="video", filters=f"video=={','.join(batch)}",
        ).execute()
        names = [h["name"] for h in resp.get("columnHeaders", [])]
        for row in resp.get("rows", []):
            rec = dict(zip(names, row))
            out[rec.pop("video")] = rec
    return out
