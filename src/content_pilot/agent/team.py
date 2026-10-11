"""The producer's specialists: each gets only the tools and skill groups its job needs.

Skill groups are folders under studio/skills/, so an agent loads just its own skills:
    writing/      shorts-script, yt-script     scriptwriter, critic, repurposer
    packaging/    yt-package, yt-seo           packager
    trends/       yt-viral                     trend-scout
    repurposing/  yt-shorts, yt-chapters, yt-edit   repurposer
    analytics/    yt-retention, yt-audit       analyst
    community/    yt-comment                   community
    planning/     yt-plan                      producer
"""

from . import prompts
from .tools import check_script, list_videos
from .youtube_tools import (find_dead_air, lint_title, make_chapters, rank_outliers, read_retention,
                            score_hooks)

# Gemini's built-in Google Search grounding; no extra key needed.
WEB_SEARCH = {"google_search": {}}


def skills(*groups: str) -> list[str]:
    return [f"/skills/{g}/" for g in groups]


TEAM = [
    {
        "name": "trend-scout",
        "description": "Finds what is working in the niche now, ranked by how far each video beat its "
                       "own channel, and proposes Short topics. Give it the niche and a /research/ "
                       "path for the collected JSON.",
        "system_prompt": prompts.TREND_SCOUT,
        "tools": [WEB_SEARCH, rank_outliers],
        "skills": skills("trends"),
    },
    {
        "name": "researcher",
        "description": "Finds verified, surprising facts about a topic on the web and saves notes with "
                       "source links. Give it the topic, the angle, and the /research/ path to write.",
        "system_prompt": prompts.RESEARCHER,
        "tools": [WEB_SEARCH],
    },
    {
        "name": "scriptwriter",
        "description": "Writes a Short's script from research: five hooks scored, the best built out, "
                       "validated with check_script. Give it the research path and the /scripts/ path.",
        "system_prompt": prompts.SCRIPTWRITER,
        "tools": [score_hooks, check_script],
        "skills": skills("writing"),
    },
    {
        "name": "critic",
        "description": "Independent retention review of a script: scores and up to three rewrites. "
                       "Give it the script path.",
        "system_prompt": prompts.CRITIC,
        "tools": [score_hooks],
        "skills": skills("writing"),
    },
    {
        "name": "packager",
        "description": "Title and thumbnail as one pairing, plus description, hashtags and search "
                       "queries. Updates the script in place. Give it the script and /packages/ paths.",
        "system_prompt": prompts.PACKAGER,
        "tools": [lint_title, check_script],
        "skills": skills("packaging"),
    },
    {
        "name": "repurposer",
        "description": "Cuts Shorts, chapters or an edit decision list from a long video's transcript "
                       "in /inputs/. Say which of the three you want and where to write.",
        "system_prompt": prompts.REPURPOSER,
        "tools": [score_hooks, check_script, make_chapters, find_dead_air],
        "skills": skills("repurposing", "writing"),
    },
    {
        "name": "analyst",
        "description": "Reads a retention CSV or audits the channel and names the one fix. Give it "
                       "the input paths and a /reports/ path.",
        "system_prompt": prompts.ANALYST,
        "tools": [read_retention, lint_title, score_hooks, list_videos],
        "skills": skills("analytics"),
    },
    {
        "name": "community",
        "description": "Triages comments and drafts replies in the creator's voice; picks the one to "
                       "pin. Give it the comments file and a /reports/ path.",
        "system_prompt": prompts.COMMUNITY,
        "tools": [],  # without this it would inherit the producer's tools, render_video included
        "skills": skills("community"),
    },
]
