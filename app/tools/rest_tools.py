"""Enterprise REST tool wrapper with retries, approval gating, and step-limit enforcement."""

from dataclasses import dataclass, field
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class ApprovalRequiredError(Exception):
    """Raised when a tool call requires human approval before executing."""


class StepLimitExceededError(Exception):
    """Raised when an agent exceeds its configured tool-call budget."""


@dataclass
class ToolCallResult:
    tool_name: str
    success: bool
    output: Optional[dict] = None
    error: Optional[str] = None
    attempts: int = 1


@dataclass
class RestToolConfig:
    base_url: str
    token: str
    sensitive_actions: tuple = field(default_factory=tuple)


class EnterpriseRestTool:
    """Wraps enterprise REST endpoints with retry, approval gating, and call budgeting."""

    def __init__(self, config: RestToolConfig, client: Optional[httpx.Client] = None):
        self.config = config
        self.client = client or httpx.Client(timeout=20.0, base_url=config.base_url)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config.token}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _call(self, method: str, path: str, **kwargs) -> httpx.Response:
        response = self.client.request(method, path, headers=self._headers(), **kwargs)
        response.raise_for_status()
        return response

    def invoke(
        self,
        action: str,
        path: str,
        method: str = "GET",
        approved: bool = False,
        tool_calls_made: int = 0,
        max_tool_calls: int = 10,
        **kwargs,
    ) -> ToolCallResult:
        """Invoke an enterprise REST action, enforcing approvals and step limits."""
        if tool_calls_made >= max_tool_calls:
            raise StepLimitExceededError(f"Tool call budget of {max_tool_calls} exceeded.")

        if action in self.config.sensitive_actions and not approved:
            raise ApprovalRequiredError(f"Action '{action}' requires explicit approval.")

        try:
            response = self._call(method, path, **kwargs)
            return ToolCallResult(tool_name=action, success=True, output=response.json())
        except Exception as exc:
            return ToolCallResult(tool_name=action, success=False, error=str(exc))
