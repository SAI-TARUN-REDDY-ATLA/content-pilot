"""The producer: a Deep Agent that researches, writes, critiques and renders Shorts."""

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents.middleware import TodoListMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from ..config import STUDIO_DIR, Settings
from .prompts import CRITIC, PRODUCER_PROMPT, RESEARCHER
from .tools import check_script, list_videos, render_video


def build_agent(model: str | None = None, checkpointer=None):
    model = model or f"anthropic:{Settings().claude_model}"
    return create_deep_agent(
        name="content-pilot-producer",
        model=model,
        tools=[check_script, render_video, list_videos],
        system_prompt=PRODUCER_PROMPT,
        middleware=[TodoListMiddleware()],
        subagents=[RESEARCHER, CRITIC],
        backend=FilesystemBackend(root_dir=STUDIO_DIR, virtual_mode=True),
        memory=["/AGENTS.md"],
        skills=["/skills/"],
        interrupt_on={"render_video": {"allowed_decisions": ["approve", "edit", "reject"]}},
        checkpointer=checkpointer or InMemorySaver(),
    )
