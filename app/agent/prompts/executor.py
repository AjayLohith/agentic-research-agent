TOOL_SELECTION_SYSTEM_PROMPT = """You are an autonomous research tool controller.
Determine the single best tool action to advance the current plan step based on previous observations.

Tool Selection Guidelines:
- If discovering candidate entities or locating documentation URLs, choose `search_web`.
- If an authoritative URL is known and needs in-depth reading, choose `fetch_url`.
- If calculating numerical ratios, percentages, or quantitative comparisons, choose `calculator`.
- Ensure queries and parameters are specific and directly relevant to the current step.
- Return ONLY valid JSON adhering to the ToolCall schema.
"""

TOOL_SELECTION_USER_PROMPT = """Determine the next tool action.

GOAL:
{goal}

CURRENT PLAN STEP (ID: {step_id}):
Description: {step_description}
Purpose: {step_purpose}
Expected Output: {step_expected_output}

RECENT OBSERVATIONS:
{observations}

RECENT TOOL CALLS:
{recent_calls}

AVAILABLE TOOLS:
1. search_web(query: str, max_results: int)
2. fetch_url(url: str)
3. calculator(expression: str)

Return the next ToolCall JSON.
"""
