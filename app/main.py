import asyncio
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config import settings
from app.exceptions import ConfigurationError
from app.logging_config import setup_logging
from app.providers.llm import get_llm_provider
from app.providers.search import get_search_provider
from app.tools.search import SearchWebTool
from app.tools.fetch import FetchUrlTool
from app.tools.calculator import SafeCalculator
from app.tools.failure_injector import failure_injector
from app.agent.planner import AutonomousPlanner
from app.agent.executor import AutonomousExecutor
from app.agent.recovery import AutonomousReplanner
from app.agent.synthesizer import AutonomousSynthesizer
from app.agent.graph import ResearchAgentGraph
from app.agent.state import AgentState
from app.services.report_service import ReportService

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

app = typer.Typer(
    name="agentic-research",
    help="Autonomous Research & Competitive Intelligence Agent CLI",
    add_completion=False
)
console = Console(legacy_windows=False)


class ResearchAgent:
    """
    High-level agent interface independent of CLI frameworks.
    Wires configuration, tools, and the state graph for programmatic usage.
    """

    def __init__(
        self,
        mock_mode: bool = False,
        demo_failure_mode: str = "none"
    ):
        self.mock_mode = mock_mode
        self.demo_failure_mode = demo_failure_mode
        failure_injector.set_mode(demo_failure_mode)

        # Wire LLM Provider (Groq by default)
        if settings.LLM_PROVIDER.lower() == "groq":
            api_key = settings.GROQ_API_KEY
            base_url = settings.GROQ_BASE_URL
        else:
            api_key = settings.OPENAI_API_KEY
            base_url = settings.OPENAI_BASE_URL

        llm_provider = get_llm_provider(
            provider_name=settings.LLM_PROVIDER,
            api_key=api_key,
            model=settings.LLM_MODEL,
            base_url=base_url,
            mock_mode=self.mock_mode or settings.MOCK_MODE
        )

        # Wire Search Provider (Tavily by default)
        search_provider = get_search_provider(
            provider_name=settings.SEARCH_PROVIDER,
            tavily_key=settings.TAVILY_API_KEY,
            mock_mode=self.mock_mode or settings.MOCK_MODE
        )

        tools = {
            "search_web": SearchWebTool(provider=search_provider),
            "fetch_url": FetchUrlTool(
                max_content_length=settings.MAX_FETCH_CONTENT_LENGTH,
                mock_mode=self.mock_mode or settings.MOCK_MODE
            ),
            "calculator": SafeCalculator(),
        }

        planner = AutonomousPlanner(llm_provider=llm_provider)
        executor = AutonomousExecutor(
            llm_provider=llm_provider,
            tools=tools,
            max_tool_calls=settings.MAX_TOOL_CALLS
        )
        replanner = AutonomousReplanner(
            llm_provider=llm_provider,
            max_retries_per_tool=settings.MAX_RETRIES_PER_TOOL
        )
        synthesizer = AutonomousSynthesizer(llm_provider=llm_provider)

        self.graph = ResearchAgentGraph(
            planner=planner,
            executor=executor,
            replanner=replanner,
            synthesizer=synthesizer,
            max_agent_steps=settings.MAX_AGENT_STEPS,
            max_research_time_seconds=settings.MAX_RESEARCH_TIME_SECONDS
        )

    async def run(self, goal: str) -> AgentState:
        return await self.graph.run(goal=goal)


def create_agent(
    mock_mode: bool = False,
    demo_failure_mode: str = "none",
    output_dir: Path = Path("output")
) -> ResearchAgentGraph:
    """Factory helper preserving backward-compatible signature."""
    agent = ResearchAgent(mock_mode=mock_mode, demo_failure_mode=demo_failure_mode)
    return agent.graph


async def run_research_pipeline(
    goal: str,
    output_dir: Path,
    mock: bool,
    demo_failure: bool
):
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "sample_run.log"
    setup_logging(log_level=settings.LOG_LEVEL, log_file_path=log_file)

    failure_mode = "timeout" if demo_failure else settings.DEMO_FAILURE_MODE

    console.print(Panel.fit(
        f"[bold cyan]AUTONOMOUS RESEARCH & COMPETITIVE INTELLIGENCE AGENT[/bold cyan]\n"
        f"[yellow]Goal:[/yellow] {goal}\n"
        f"[dim]Provider: {settings.LLM_PROVIDER} ({settings.LLM_MODEL}) | Search: {settings.SEARCH_PROVIDER}\n"
        f"Mode: {'MOCK (Deterministic Offline)' if (mock or settings.MOCK_MODE) else 'LIVE'}"
        f" | Failure Injection: {failure_mode}[/dim]",
        border_style="cyan"
    ))

    agent = ResearchAgent(
        mock_mode=mock,
        demo_failure_mode=failure_mode
    )

    with console.status("[bold green]Agent Planning & Initializing...", spinner="dots"):
        state = await agent.run(goal=goal)

    if state.plan:
        console.print("\n[bold green][+] Execution Plan Generated:[/bold green]")
        for s in state.plan.steps:
            tools_str = ", ".join(s.preferred_tools) or "dynamic"
            console.print(f"  [cyan]{s.id}.[/cyan] {s.description} [dim]({tools_str})[/dim]")

    console.print("\n[bold green][+] Execution & Evidence Synthesis Finished![/bold green]\n")

    if state.final_report:
        paths = ReportService.save_reports(state.final_report, output_dir)

        console.print(Panel(
            state.final_report.executive_summary,
            title="[bold blue]Executive Summary Preview[/bold blue]",
            border_style="blue"
        ))

        es = state.final_report.execution_summary
        table = Table(title="Agent Execution Summary", border_style="dim")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Steps Planned", str(es.steps_planned))
        table.add_row("Steps Completed", str(es.steps_completed))
        table.add_row("Total Tool Invocations", str(es.tool_calls_total))
        table.add_row("Sources Gathered", str(len(state.sources)))
        table.add_row("Evidence Items Extracted", str(len(state.evidence)))
        table.add_row("Calculations Performed", str(es.calculations_performed))
        table.add_row("Failures Detected", str(es.failures_detected))
        table.add_row("Recoveries Performed", str(es.recoveries_performed))
        table.add_row("Total Execution Time", f"{state.execution_time_seconds:.2f}s")
        console.print(table)

        console.print(f"\n[bold green]Report Artifacts Written:[/bold green]")
        console.print(f"  Markdown: [bold underline]{paths['markdown']}[/bold underline]")
        console.print(f"  JSON:     [bold underline]{paths['json']}[/bold underline]")
        console.print(f"  Log:      [bold underline]{log_file}[/bold underline]\n")


@app.command()
def main(
    goal: Optional[str] = typer.Option(
        None,
        "--goal",
        "-g",
        help="High-level research goal or question to investigate autonomously"
    ),
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Output directory where report artifacts and logs will be saved"
    ),
    demo_failure: bool = typer.Option(
        False,
        "--demo-failure",
        "-d",
        help="Simulate an intentional tool failure to demonstrate autonomous recovery and replanning"
    ),
    mock: bool = typer.Option(
        False,
        "--mock",
        "-m",
        help="Run in deterministic mock mode using offline fixtures without calling external APIs"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Launch interactive prompt to enter research goals dynamically"
    )
):
    """
    Autonomous Research & Competitive Intelligence Agent CLI.
    Runs autonomous planning, tool orchestration, failure recovery, and structured report synthesis.
    """
    if interactive:
        console.print("[bold cyan]Autonomous Research Agent (Interactive Mode)[/bold cyan]")
        user_input = typer.prompt("Enter your research goal")
        if not user_input.strip():
            console.print("[red]Goal cannot be empty.[/red]")
            raise typer.Exit(code=1)
        goal = user_input.strip()

    if not goal:
        goal = (
            "Analyze the current competitive landscape for AI agent frameworks and identify the major players, "
            "their capabilities, positioning, recent developments, and important differences."
        )

    # Validate configuration if not running in mock mode
    if not mock and not settings.MOCK_MODE:
        try:
            settings.validate_runtime(is_mock=False)
        except ConfigurationError as ce:
            console.print(f"\n[bold red]Configuration Error:[/bold red]\n{ce}\n")
            raise typer.Exit(code=1)

    asyncio.run(
        run_research_pipeline(
            goal=goal,
            output_dir=output,
            mock=mock or settings.MOCK_MODE,
            demo_failure=demo_failure
        )
    )


if __name__ == "__main__":
    app()
