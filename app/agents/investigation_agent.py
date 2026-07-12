"""Investigation agent: runs NL-to-SQL queries and enterprise API calls to gather evidence."""

from app.state import AgentState
from app.tools.cortex_tools import CortexAnalystTool
from app.tools.rest_tools import ApprovalRequiredError, EnterpriseRestTool, StepLimitExceededError


class InvestigationAgent:
    """Runs Cortex Analyst SQL queries and REST tool calls to investigate a task."""

    name = "investigation_agent"

    def __init__(self, analyst_tool: CortexAnalystTool, rest_tool: EnterpriseRestTool, semantic_model: str):
        self.analyst_tool = analyst_tool
        self.rest_tool = rest_tool
        self.semantic_model = semantic_model

    def run(self, state: AgentState) -> AgentState:
        findings = state.get("investigation_findings", [])

        try:
            sql_result = self.analyst_tool.run(state["task"], self.semantic_model)
            findings.append({"type": "sql", "result": sql_result})
        except Exception as exc:
            findings.append({"type": "sql_error", "error": str(exc)})

        try:
            rest_result = self.rest_tool.invoke(
                action="lookup_retailer_metadata",
                path="/v1/retailers/search",
                method="GET",
                approved=state.get("approved", False),
                tool_calls_made=state.get("tool_calls_made", 0),
                max_tool_calls=state.get("max_tool_calls", 10),
                params={"query": state["task"]},
            )
            findings.append({"type": "rest", "result": rest_result.__dict__})
        except ApprovalRequiredError:
            state["requires_approval"] = True
            state["status"] = "awaiting_approval"
        except StepLimitExceededError:
            state["status"] = "failed"

        state["investigation_findings"] = findings
        state["tool_calls_made"] = state.get("tool_calls_made", 0) + 1
        return state
