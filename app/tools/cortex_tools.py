"""Wrappers around Snowflake Cortex Analyst and Cortex Search for the agent toolset."""

from dataclasses import dataclass
from typing import Any, Optional
import httpx


@dataclass
class CortexConfig:
    account_url: str
    database: str
    schema: str
    warehouse: str
    token: str


class CortexAnalystTool:
    """Calls Snowflake Cortex Analyst to translate natural language into SQL and run it."""

    name = "cortex_analyst"

    def __init__(self, config: CortexConfig, client: Optional[httpx.Client] = None):
        self.config = config
        self.client = client or httpx.Client(timeout=30.0)

    def run(self, question: str, semantic_model: str) -> dict:
        """Send a natural language question to Cortex Analyst and return SQL plus results."""
        payload = {
            "question": question,
            "semantic_model": semantic_model,
            "warehouse": self.config.warehouse,
        }
        response = self.client.post(
            f"{self.config.account_url}/api/v2/cortex/analyst/message",
            json=payload,
            headers={"Authorization": f"Bearer {self.config.token}"},
        )
        response.raise_for_status()
        return response.json()


class CortexSearchTool:
    """Calls Snowflake Cortex Search for retrieval-augmented generation over curated datasets."""

    name = "cortex_search"

    def __init__(self, config: CortexConfig, client: Optional[httpx.Client] = None):
        self.config = config
        self.client = client or httpx.Client(timeout=30.0)

    def run(self, query: str, service_name: str, top_k: int = 5) -> list:
        """Query a Cortex Search service and return the top matching documents."""
        payload = {"query": query, "columns": ["chunk", "source"], "limit": top_k}
        response = self.client.post(
            f"{self.config.account_url}/api/v2/cortex/search/{service_name}/query",
            json=payload,
            headers={"Authorization": f"Bearer {self.config.token}"},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data.get("results", [])
