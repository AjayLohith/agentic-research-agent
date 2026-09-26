import logging
from typing import Dict

logger = logging.getLogger("agentic_research.failure_injector")


class FailureInjector:
    """
    Simulates deliberate real-world failures for demonstration and testing.
    Can be configured via DEMO_FAILURE_MODE env var or CLI --demo-failure flag.
    Fails ONCE on targeted tools, enabling the agent's retry and replanning mechanisms to demonstrate recovery.
    """

    def __init__(self, mode: str = "none"):
        self.mode = mode.lower()
        self._has_failed_map: Dict[str, bool] = {}

    def set_mode(self, mode: str):
        self.mode = mode.lower()
        self._has_failed_map.clear()

    def should_fail(self, tool_name: str) -> bool:
        if self.mode == "none":
            return False

        if not self._has_failed_map.get(tool_name, False):
            # Check if this tool is targeted (fetch_url is primary demo target)
            if tool_name in ["fetch_url", "search_web"]:
                self._has_failed_map[tool_name] = True
                return True
        return False

    def trigger_failure_if_needed(self, tool_name: str):
        if self.should_fail(tool_name):
            logger.warning(
                f"[FAILURE INJECTOR ACTIVE] Intentionally injecting '{self.mode}' error into '{tool_name}' (First Attempt)"
            )
            if self.mode == "timeout":
                raise TimeoutError(f"Simulated HTTP connection timeout while calling {tool_name} (read timed out after 10.0s)")
            elif self.mode == "http_500":
                raise RuntimeError(f"Simulated HTTP 500 Internal Server Error returned from remote host for {tool_name}")
            elif self.mode == "empty_response":
                raise ValueError(f"Simulated network truncation: {tool_name} returned 0 bytes (Empty Response)")
            else:
                raise RuntimeError(f"Simulated failure: mode='{self.mode}' in {tool_name}")


# Global singleton instance
failure_injector = FailureInjector()
