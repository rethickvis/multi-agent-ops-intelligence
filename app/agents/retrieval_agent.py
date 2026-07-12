"""Retrieval agent: uses Cortex Search to pull relevant context for a task."""

from app.state import AgentState
from app.tools.cortex_tools import CortexSearchTool


class RetrievalAgent:
    """Fetches supporting context from Snowflake Cortex Search."""

    name = "retrieval_agent"

    def __init__(self, search_tool: CortexSearchTool, service_name: str):
        self.search_tool = search_tool
        self.service_name = service_name

    def run(self, state: AgentState) -> AgentState:
        results = self.search_tool.run(
            query=state["task"],
            service_name=self.service_name,
            top_k=5,
        )
        state["retrieved_context"] = results
        state["tool_calls_made"] = state.get("tool_calls_made", 0) + 1
        return state
