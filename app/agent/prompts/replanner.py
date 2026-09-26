REPLANNING_SYSTEM_PROMPT = """You are an autonomous recovery and replanning controller.
A research tool execution has encountered a failure, timeout, or information gap.

Task:
1. Analyze the root cause of the failure.
2. Choose the most effective recovery action:
   - 'retry': Transient error and retry budget remaining.
   - 'alternative_source': Search for alternative documentation or mirror.
   - 'adjust_query': Refine search keywords to avoid dead ends.
   - 'skip': Non-critical information that can be omitted.
   - 'complete': Sufficient evidence exists to answer the goal.
3. Return valid JSON matching the ReplanningDecision schema.
"""

REPLANNING_USER_PROMPT = """A failure or anomaly was observed. Formulate a recovery plan.

GOAL:
{goal}

FAILED STEP:
Step ID: {step_id}
Description: {step_description}

ERROR DETAILS:
Tool: {tool_name}
Error: {error_message}
Retry Attempt: {retry_count} / {max_retries}

DISCOVERED SOURCES:
{sources}

Return the ReplanningDecision JSON.
"""
