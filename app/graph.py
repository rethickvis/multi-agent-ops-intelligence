"""Supervisor LangGraph workflow coordinating analysis, retrieval, and investigation agents."""

from langgraph.graph import END, StateGraph

from app.agents.analysis_agent import AnalysisAgent
from app.agents.investigation_agent import InvestigationAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.state import AgentState, new_state


def route_next(state: AgentState) -> str:
    """Supervisor routing logic: decide which agent runs next based on current state."""
    if state["status"] in ("awaiting_approval", "failed", "completed"):
        return END

    if not state.get("retrieved_context"):
        return "retrieval_agent"

    if not state.get("investigation_findings"):
        return "investigation_agent"

    if not state.get("analysis_result"):
        return "analysis_agent"

    return END


def build_graph(
    analysis_agent: AnalysisAgent,
    retrieval_agent: RetrievalAgent,
    investigation_agent: InvestigationAgent,
):
    """Builds and compiles the supervisor-coordinated multi-agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("retrieval_agent", retrieval_agent.run)
    graph.add_node("investigation_agent", investigation_agent.run)
    graph.add_node("analysis_agent", analysis_agent.run)

    graph.set_conditional_entry_point(route_next)
    graph.add_conditional_edges("retrieval_agent", route_next)
    graph.add_conditional_edges("investigation_agent", route_next)
    graph.add_conditional_edges("analysis_agent", route_next)

    return graph.compile()


def run_task(app, task: str, max_tool_calls: int = 10, max_retries: int = 2) -> AgentState:
    """Convenience helper to run a task through the compiled graph."""
    state = new_state(task=task, max_tool_calls=max_tool_calls, max_retries=max_retries)
    return app.invoke(state)
