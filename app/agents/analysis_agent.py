"""Analysis agent: synthesizes retrieved context and investigation findings into a summary."""

from typing import Any

from app.state import AgentState


SYSTEM_PROMPT = (
    "You are the Analysis agent in a retail operations intelligence system. "
    "Summarize findings from retrieval and investigation into a concise, "
    "actionable analysis with clear next steps."
)


class AnalysisAgent:
    """Synthesizes retrieved context and investigation findings into an analysis result."""

    name = "analysis_agent"

    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        context_summary = self._summarize(state.get("retrieved_context", []))
        findings_summary = self._summarize(state.get("investigation_findings", []))

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Task: {state['task']}\n\n"
                    f"Retrieved context:\n{context_summary}\n\n"
                    f"Investigation findings:\n{findings_summary}"
                ),
            },
        ]
        response = self.llm.invoke(messages)

        state["analysis_result"] = {
            "summary": response.content,
            "sources": len(state.get("retrieved_context", [])),
        }
        state["status"] = "completed"
        return state

    @staticmethod
    def _summarize(items: list) -> str:
        if not items:
            return "None available."
        return "\n".join(f"- {item}" for item in items[:10])
