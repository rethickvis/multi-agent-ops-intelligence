# Multi-Agent Operations Intelligence Platform

A supervisor-coordinated multi-agent system for retail operations intelligence, built with LangGraph, FastAPI, and Snowflake Cortex. The supervisor routes tasks across retrieval, investigation, and analysis agents that share a common state object, with tool approvals, retries, and step limits enforced along the way.

## Architecture

The system uses a LangGraph StateGraph where a routing function acts as the supervisor, deciding which specialized agent should run next based on the current shared state:

- Retrieval agent &mdash; queries Snowflake Cortex Search for relevant historical context.
- Investigation agent &mdash; runs NL-to-SQL queries via Cortex Analyst and calls enterprise REST APIs, gated by an approval and step-limit system for sensitive actions.
- Analysis agent &mdash; synthesizes retrieved context and investigation findings into a concise, actionable summary.

The graph terminates when the task is completed, fails, or requires human approval for a sensitive action.

## Project layout

app/state.py &mdash; shared AgentState schema and factory function.
app/tools/cortex_tools.py &mdash; Snowflake Cortex Analyst and Cortex Search client wrappers.
app/tools/rest_tools.py &mdash; enterprise REST tool wrapper with retries, approval gating, and step limits.
app/agents/ &mdash; retrieval, investigation, and analysis agent implementations.
app/graph.py &mdash; supervisor routing logic and compiled LangGraph workflow.
app/main.py &mdash; FastAPI service exposing the platform as an HTTP API.
k8s/deployment.yaml &mdash; Kubernetes Deployment and Service for containerized rollout.
tests/test_scenarios.py &mdash; evaluation harness covering routing, groundedness, tool failures, and unauthorized-action scenarios.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then send a task to the API:

```bash
curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"task": "Investigate a 12% sell-through drop for SKU 48213 in the Midwest region."}'
```

## Running tests

```bash
pytest tests/
```

## Deploying

Build the image and apply the Kubernetes manifest:

```bash
docker build -t ghcr.io/rethickvis/multi-agent-ops-intelligence:latest .
kubectl apply -f k8s/deployment.yaml
```

## Notes

This repository is a reference implementation of the architecture described on my resume. The Cortex and enterprise API credentials in `app/main.py` are placeholders and should be replaced with real values loaded from environment variables or a secrets manager before deploying.
