"""Topic -> script -> voice -> captions -> render. Each stage is its own module."""

from .run import make_video

__all__ = ["make_video"]
