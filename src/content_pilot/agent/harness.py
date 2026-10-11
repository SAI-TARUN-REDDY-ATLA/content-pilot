"""The producer: a Deep Agent that runs a team of YouTube specialists."""

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents.middleware import TodoListMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field

from ..config import STUDIO_DIR, Settings
from . import prompts
from .team import TEAM, skills
from .tools import check_script, list_videos, render_video


class DailyResult(BaseModel):
    """What an unattended run hands back; the daily job renders and uploads from it."""
    topic: str = Field(description="The topic in a few words")
    slug: str = Field(description="Slug used for every file of this video")
    script_path: str = Field(description="Studio path of the final script, e.g. /scripts/<slug>.json")
    research_path: str = Field(description="Studio path of the research notes")
    package_path: str = Field(description="Studio path of the package notes (thumbnail brief etc.)")
    thumbnail_text: str = Field(description="Three words at most")
    why: str = Field(description="One sentence: why this topic and hook should hold viewers")


def build_agent(model: str | None = None, checkpointer=None, autonomous: bool = False):
    """Interactive by default: rendering waits for a person. With autonomous=True there is no
    render tool and no interrupt; the agent stops at a packaged script and returns DailyResult."""
    model = model or f"anthropic:{Settings().claude_model}"
    extra = {"response_format": DailyResult} if autonomous else {
        "interrupt_on": {"render_video": {"allowed_decisions": ["approve", "edit", "reject"]}}}
    return create_deep_agent(
        name="content-pilot-producer",
        model=model,
        tools=[check_script, list_videos] + ([] if autonomous else [render_video]),
        system_prompt=prompts.PRODUCER + (prompts.AUTONOMOUS if autonomous else ""),
        middleware=[TodoListMiddleware()],
        subagents=TEAM,
        backend=FilesystemBackend(root_dir=STUDIO_DIR, virtual_mode=True),
        memory=["/AGENTS.md", "/voice.md"],
        skills=skills("planning"),
        checkpointer=checkpointer or InMemorySaver(),
        **extra,
    )
