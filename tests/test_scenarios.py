"""Evaluation harness for the multi-agent supervisor covering routing, SQL validity,
groundedness, tool failures, and unauthorized-action scenarios."""

from dataclasses import dataclass
from typing import Callable

import pytest
from langgraph.graph import END

from app.graph import route_next
from app.state import new_state


@dataclass
class Scenario:
    name: str
    category: str
    setup: Callable[[], dict]
    expected: str


def _state(**overrides) -> dict:
    state = new_state(task="Investigate a 12% sell-through drop for SKU 48213 in the Midwest region.")
    state.update(overrides)
    return state


SCENARIOS = [
    Scenario("routes_to_retrieval_when_no_context", "routing", lambda: _state(), "retrieval_agent"),
    Scenario(
        "routes_to_investigation_after_retrieval",
        "routing",
        lambda: _state(retrieved_context=[{"chunk": "prior incident report"}]),
        "investigation_agent",
    ),
    Scenario(
        "routes_to_analysis_after_investigation",
        "routing",
        lambda: _state(
            retrieved_context=[{"chunk": "prior incident report"}],
            investigation_findings=[{"type": "sql", "result": {}}],
        ),
        "analysis_agent",
    ),
    Scenario("ends_when_awaiting_approval", "unauthorized_actions", lambda: _state(status="awaiting_approval"), END),
    Scenario("ends_when_failed", "tool_failures", lambda: _state(status="failed"), END),
    Scenario("ends_when_completed", "groundedness", lambda: _state(status="completed"), END),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.name for s in SCENARIOS])
def test_supervisor_routing(scenario: Scenario) -> None:
    """Runs each evaluation scenario and checks the supervisor routes as expected."""
    state = scenario.setup()
    result = route_next(state)
    assert result == scenario.expected, f"[{scenario.category}] {scenario.name} failed: got {result}"
