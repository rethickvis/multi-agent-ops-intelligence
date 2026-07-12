"""FastAPI service exposing the multi-agent operations intelligence platform."""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agents.analysis_agent import AnalysisAgent
from app.agents.investigation_agent import InvestigationAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.graph import build_graph, run_task
from app.tools.cortex_tools import CortexAnalystTool, CortexConfig, CortexSearchTool
from app.tools.rest_tools import EnterpriseRestTool, RestToolConfig

app = FastAPI(title="Multi-Agent Operations Intelligence Platform")


class TaskRequest(BaseModel):
    task: str
    approved: bool = False


class TaskResponse(BaseModel):
    status: str
    analysis: Optional[dict]
    findings: list


def _build_app_graph():
    # NOTE: replace placeholder values below with real Snowflake and enterprise API
    # credentials, typically loaded from environment variables or a secrets manager.
    cortex_config = CortexConfig(
        account_url="https://<account>.snowflakecomputing.com",
        database="OPS_INTELLIGENCE",
        schema="PUBLIC",
        warehouse="OPS_WH",
        token="<token>",
    )
    rest_config = RestToolConfig(
        base_url="https://internal-api.example.com",
        token="<token>",
        sensitive_actions=("issue_credit", "escalate_incident"),
    )

    analyst_tool = CortexAnalystTool(cortex_config)
    search_tool = CortexSearchTool(cortex_config)
    rest_tool = EnterpriseRestTool(rest_config)

    retrieval_agent = RetrievalAgent(search_tool, service_name="ops_knowledge_base")
    investigation_agent = InvestigationAgent(analyst_tool, rest_tool, semantic_model="retail_ops_model")
    analysis_agent = AnalysisAgent(llm=None)

    return build_graph(analysis_agent, retrieval_agent, investigation_agent)


graph_app = _build_app_graph()


@app.post("/tasks", response_model=TaskResponse)
def create_task(request: TaskRequest) -> TaskResponse:
    """Run a new operations intelligence task through the multi-agent graph."""
    try:
        result = run_task(graph_app, task=request.task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return TaskResponse(
        status=result["status"],
        analysis=result.get("analysis_result"),
        findings=result.get("investigation_findings", []),
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
