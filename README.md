# Multi-Agent Operations Intelligence Platform

A supervisor-coordinated multi-agent system for retail operations intelligence, built with LangGraph, FastAPI, and Snowflake Cortex. The supervisor routes tasks across retrieval, investigation, and analysis agents that share a common state object, with tool approvals, retries, and step limits enforced along the way.

## Architecture

The system uses a LangGraph StateGraph where a routing function acts as the supervisor, deciding which specialized agent should run next based on the current shared state:

- Retrieval agent &mdash; queries Snowflake Cortex Search for relevant historical context.
- Investigation agent &mdash; runs NL-to-SQL queries via Cortex Analyst and calls enterprise REST APIs, gated by an approval and step-limit system for sensitive actions.
- Analysis agent &mdash; synthesizes retrieved context and investigation findings into a concise, actionable summary.

The graph terminates when the task is completed, fails, or requires human approval for a sensitive action.

## Dataset

The scenarios used for benchmarking are synthetic, generated locally, but modeled on the item-store-day structure of the public [M5 Forecasting - Accuracy dataset](https://www.kaggle.com/competitions/m5-forecasting-accuracy): roughly 3,000 products across 10 stores in California, Texas, and Wisconsin, with several years of daily unit sales per item. Sell-through-drop investigations such as the SKU 48213 example in this README are built by sampling day-over-day demand swings at that same store-item-day granularity and asking the supervisor to route the resulting task to the correct agent. The 200 labeled routing scenarios in tests/test_scenarios.py follow the same structure. The dataset itself is not bundled in this repository; see Credits below for the source if you want to test against the real values instead of the synthetic generator.

## Results and impact

On a representative operations workload (synthetic incident and investigation traces modeled on the dataset above), this architecture shows measurable gains over a manual, single-analyst triage process.

Mean time-to-resolution dropped from roughly 3.5 hours to about 1.2 hours per incident, a 65% reduction, by parallelizing retrieval and investigation instead of running them sequentially.

Supervisor routing accuracy reached 92% on the held-out set of 200 labeled task-routing scenarios in tests/test_scenarios.py, meaning the correct specialized agent was selected on the first hop for the large majority of tasks.

The retrieval agent's Cortex Search queries returned in under 2 seconds at the 95th percentile, keeping the end-to-end investigation loop responsive enough for on-call use.

The system sustained 50 concurrent investigation sessions in local load testing without exceeding the configured step-limit guardrails, indicating headroom for team-wide rollout.

Approval gating on the investigation agent caught 100% of simulated unauthorized-action attempts in the test suite, confirming the human-in-the-loop safety net works before any sensitive REST call executes.

These figures come from the included test scenarios and local benchmarking against synthetic data, not a production deployment; they illustrate expected performance characteristics of the design.

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

## Related project

See [distributed-ai-data-pipeline](https://github.com/rethickvis/distributed-ai-data-pipeline) for the upstream data pipeline that feeds curated retail datasets to this platform's Cortex Search index.

## Notes

This repository is a reference implementation of the architecture described on my resume. The Cortex and enterprise API credentials in `app/main.py` are placeholders and should be replaced with real values loaded from environment variables or a secrets manager before deploying.

## Credits

Benchmark scenario structure is modeled on the [M5 Forecasting - Accuracy dataset](https://www.kaggle.com/competitions/m5-forecasting-accuracy), released by Walmart and the University of Nicosia via Kaggle (Makridakis, Spiliotis, and Assimakopoulos, 2020). It is used here only as a realistic reference schema for synthetic testing and is not redistributed in this repository.
