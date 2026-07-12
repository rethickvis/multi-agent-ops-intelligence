"""Shared state schema for the multi-agent supervisor graph."""

from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state passed between the supervisor and worker agents."""

    messages: Annotated[list, add_messages]
    next_agent: Optional[str]
    task: str
    investigation_findings: list
    retrieved_context: list
    analysis_result: Optional[dict]
    tool_calls_made: int
    max_tool_calls: int
    requires_approval: bool
    approved: bool
    retries: int
    max_retries: int
    status: Literal["in_progress", "awaiting_approval", "completed", "failed"]


def new_state(task: str, max_tool_calls: int = 10, max_retries: int = 2) -> AgentState:
    """Factory that returns a fresh AgentState for a new task."""
    return AgentState(
        messages=[],
        next_agent=None,
        task=task,
        investigation_findings=[],
        retrieved_context=[],
        analysis_result=None,
        tool_calls_made=0,
        max_tool_calls=max_tool_calls,
        requires_approval=False,
        approved=False,
        retries=0,
        max_retries=max_retries,
        status="in_progress",
    )
