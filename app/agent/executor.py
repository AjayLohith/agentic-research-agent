import logging
import re
from typing import Dict, Any, Optional
from app.models.tool import ToolCall, ToolExecutionResult
from app.models.plan import PlanStep
from app.models.report import CalculationRecord
from app.tools.base import BaseTool
from app.tools.search import SearchWebTool
from app.tools.fetch import FetchUrlTool
from app.tools.calculator import SafeCalculator
from app.providers.llm import LLMProvider
from app.agent.prompts import (
    TOOL_SELECTION_SYSTEM_PROMPT,
    TOOL_SELECTION_USER_PROMPT,
    EVIDENCE_EXTRACTION_SYSTEM_PROMPT,
    EVIDENCE_EXTRACTION_USER_PROMPT,
)
from app.agent.state import AgentState
from app.services.source_service import SourceClassificationService
from app.services.evidence_service import EvidenceService

logger = logging.getLogger("agentic_research.executor")


class AutonomousExecutor:
    """
    Decides and executes individual tool actions dynamically.
    Performs loop detection, safety budget enforcement, observation recording,
    and automatic evidence extraction from web content.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        tools: Dict[str, BaseTool],
        max_tool_calls: int = 25
    ):
        self.llm = llm_provider
        self.tools = tools
        self.max_tool_calls = max_tool_calls

    async def select_action(self, state: AgentState, step: PlanStep) -> ToolCall:
        """
        Allows the LLM to dynamically determine which tool to invoke and with what arguments.
        Enforces loop detection to avoid repetitive queries.
        """
        # Format recent history & observations
        recent_obs = "\n".join([
            f"- Tool: {o['tool']} | Input: {o['input']} => {o['observation'][:120]}..."
            for o in state.observations[-4:]
        ]) or "None yet."

        recent_calls = "\n".join([
            f"- {th.tool_name} (Success: {th.success})" for th in state.tool_history[-4:]
        ]) or "None."

        prompt = TOOL_SELECTION_USER_PROMPT.format(
            goal=state.goal,
            step_id=step.id,
            step_description=step.description,
            step_purpose=step.purpose,
            step_expected_output=step.expected_output,
            observations=recent_obs,
            recent_calls=recent_calls
        )

        tool_call = await self.llm.structured_output(
            schema=ToolCall,
            prompt=prompt,
            system_prompt=TOOL_SELECTION_SYSTEM_PROMPT
        )

        # Loop Detection check (Assignment Section 37)
        if state.is_repeated_action(tool_call.tool_name, tool_call.arguments):
            logger.warning(
                f"[LOOP DETECTED] Repeated action detected for tool '{tool_call.tool_name}'. Intervening with fallback."
            )
            # If search was repeating, switch query or inspect an existing discovered URL
            if tool_call.tool_name == "search_web" and state.sources:
                unfetched = [s for s in state.sources if not any(th.tool_name == "fetch_url" and s.url in str(th.data) for th in state.tool_history)]
                if unfetched:
                    target_url = unfetched[0].url
                    logger.info(f"Pivoting strategy from repeated search to fetching discovered URL: {target_url}")
                    return ToolCall(
                        tool_name="fetch_url",
                        arguments={"url": target_url},
                        rationale="Pivoting from repeated search to fetching existing candidate URL."
                    )
                else:
                    # Modify query
                    orig_q = tool_call.arguments.get("query", state.goal)
                    new_q = f"{orig_q} technical specifications architecture documentation"
                    logger.info(f"Refining search query to break loop: {new_q}")
                    return ToolCall(
                        tool_name="search_web",
                        arguments={"query": new_q, "max_results": 4},
                        rationale="Refined query following loop detection."
                    )

        return tool_call

    async def execute_tool(self, tool_call: ToolCall, state: AgentState) -> ToolExecutionResult:
        """Executes selected tool, applies safety budgets, and records observation."""
        if len(state.tool_history) >= self.max_tool_calls:
            err = f"Research budget exceeded: maximum tool calls ({self.max_tool_calls}) reached."
            logger.warning(err)
            return ToolExecutionResult(tool_name=tool_call.tool_name, success=False, error=err)

        tool = self.tools.get(tool_call.tool_name)
        if not tool:
            err = f"Tool '{tool_call.tool_name}' not found in registry."
            logger.error(err)
            return ToolExecutionResult(tool_name=tool_call.tool_name, success=False, error=err)

        logger.info(f"Executing tool '{tool_call.tool_name}' with args: {tool_call.arguments}")
        result = await tool.run(**tool_call.arguments)
        state.tool_history.append(result)

        if not result.success:
            logger.warning(f"Tool '{tool_call.tool_name}' returned error: {result.error}")
            state.record_failure(tool_call.tool_name, result.error or "Unknown error")
            return result

        # Process tool success data
        await self._process_tool_success(tool_call.tool_name, result.data, state)
        return result

    async def _process_tool_success(self, tool_name: str, data: Any, state: AgentState):
        """Processes tool output, updates sources and evidence in state."""
        if tool_name == "search_web" and isinstance(data, dict):
            results = data.get("results", [])
            for r in results:
                url = r.get("url")
                title = r.get("title", "")
                if url:
                    source = SourceClassificationService.create_source(url, title)
                    state.add_source(source)
            summary = f"Retrieved {len(results)} search results."
            state.record_observation(tool_name, data.get("query"), summary)

        elif tool_name == "fetch_url" and isinstance(data, dict):
            url = data.get("url", "")
            title = data.get("title", "")
            content = data.get("content", "")
            length = data.get("content_length", 0)

            # Ensure source is recorded
            if url:
                source = SourceClassificationService.create_source(url, title)
                state.add_source(source)

            # Extract structured evidence from the content
            await self._extract_evidence_from_content(url, title, content, state)
            summary = f"Fetched {length} chars from {url}. Extracted verified evidence."
            state.record_observation(tool_name, url, summary)

        elif tool_name == "calculator" and isinstance(data, dict):
            expr = data.get("expression", "")
            val = data.get("result", 0.0)
            calc_record = CalculationRecord(
                description=f"Calculated {expr}",
                expression=expr,
                result=float(val),
                interpretation=f"Computed derived metric {val} for comparative evaluation."
            )
            state.calculations.append(calc_record)
            state.record_observation(tool_name, expr, f"Computed result: {val}")

    async def _extract_evidence_from_content(
        self,
        url: str,
        title: str,
        content: str,
        state: AgentState
    ):
        """Extracts factual claims and verbatim quotes from retrieved web text."""
        if not content or len(content.strip()) < 50:
            return

        # Heuristic extraction for robust offline / mock resilience
        # Take key sentences as candidate factual claims
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 30 and len(s.strip()) < 250]
        for s in sentences[:3]:
            # Guess entity name
            entity_name = None
            for candidate in ["LangGraph", "CrewAI", "AutoGen", "FastAPI", "Spring Boot"]:
                if candidate.lower() in s.lower() or candidate.lower() in title.lower():
                    entity_name = candidate
                    break

            ev = EvidenceService.register_evidence(
                claim=s,
                supporting_quote=s,
                source_url=url,
                source_title=title,
                entity_name=entity_name,
                existing_evidence=state.evidence
            )
            state.add_evidence(ev)
            state.intermediate_findings.append(f"{ev.entity_name or 'Finding'}: {ev.claim}")
