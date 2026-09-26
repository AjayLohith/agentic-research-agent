import json
from pathlib import Path
from typing import Dict, Any
from app.models.report import ResearchReport


class ReportService:
    """
    Renders structured ResearchReport models into publication-ready Markdown
    and validates JSON output against the Pydantic schema.
    """

    @classmethod
    def generate_markdown(cls, report: ResearchReport) -> str:
        lines = []

        # Title & Metadata
        lines.append("# Autonomous Research & Competitive Intelligence Report")
        lines.append("")
        lines.append(f"**Research Goal:** {report.metadata.goal}  ")
        lines.append(f"**Generated At:** {report.metadata.generated_at} (UTC)  ")
        lines.append(f"**Execution Time:** {report.metadata.execution_time_seconds:.2f} seconds  ")
        lines.append(f"**Agent Version:** {report.metadata.agent_version}  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Executive Summary
        lines.append("## 1. Executive Summary")
        lines.append("")
        lines.append(report.executive_summary)
        lines.append("")

        # 2. Research Objective & Scope
        lines.append("## 2. Research Objective & Scope")
        lines.append("")
        lines.append(f"**Objective:** {report.metadata.goal}")
        lines.append("")
        if report.research_scope:
            assumptions = report.research_scope.get("assumptions", [])
            constraints = report.research_scope.get("constraints", [])
            if assumptions:
                lines.append("### Assumptions")
                for a in assumptions:
                    lines.append(f"- {a}")
                lines.append("")
            if constraints:
                lines.append("### Constraints")
                for c in constraints:
                    lines.append(f"- {c}")
                lines.append("")

        # 3. Key Findings
        lines.append("## 3. Key Findings")
        lines.append("")
        for finding in report.key_findings:
            conf_percent = int(finding.confidence * 100)
            lines.append(f"### • {finding.title} *(Category: {finding.category} | Confidence: {conf_percent}%)*")
            lines.append(f"{finding.summary}")
            if finding.supporting_evidence_ids:
                lines.append(f"*Supporting Evidence:* {', '.join(finding.supporting_evidence_ids)}")
            lines.append("")

        # 4. Entity / Competitor Overview Table
        lines.append("## 4. Entity / Competitor Overview")
        lines.append("")
        if report.entities:
            lines.append("| Entity | Category | Key Capabilities | Strengths | Tradeoffs | Primary Source | Confidence |")
            lines.append("|---|---|---|---|---|---|---|")
            for ent in report.entities:
                caps = "<br>".join([f"• {c}" for c in ent.key_capabilities[:3]]) or "N/A"
                strengths = "<br>".join([f"• {s}" for s in ent.strengths[:2]]) or "N/A"
                tradeoffs = "<br>".join([f"• {t}" for t in ent.tradeoffs[:2]]) or "N/A"
                source_link = f"[{ent.name} Source]({ent.authoritative_source_url})" if ent.authoritative_source_url else "N/A"
                conf = f"{int(ent.confidence * 100)}%"
                lines.append(f"| **{ent.name}** | {ent.category} | {caps} | {strengths} | {tradeoffs} | {source_link} | {conf} |")
            lines.append("")

            # Detailed Entity Analysis
            lines.append("### Detailed Entity Analysis")
            lines.append("")
            for ent in report.entities:
                lines.append(f"#### {ent.name}")
                lines.append(f"{ent.description}")
                lines.append("")
                lines.append(f"- **Key Capabilities:** {', '.join(ent.key_capabilities) if ent.key_capabilities else 'N/A'}")
                lines.append(f"- **Strengths:** {', '.join(ent.strengths) if ent.strengths else 'N/A'}")
                lines.append(f"- **Tradeoffs / Considerations:** {', '.join(ent.tradeoffs) if ent.tradeoffs else 'N/A'}")
                lines.append(f"- **Primary Reference:** [{ent.authoritative_source_url}]({ent.authoritative_source_url})")
                lines.append("")
        else:
            lines.append("No specific entities isolated during research.")
            lines.append("")

        # 5. Comparative Analysis
        lines.append("## 5. Comparative Analysis")
        lines.append("")
        if report.comparison:
            lines.append("| Dimension | Synthesized Analysis | Entity Ratings / Notes |")
            lines.append("|---|---|---|")
            for comp in report.comparison:
                notes = "<br>".join([f"**{k}:** {v}" for k, v in comp.entity_ratings_or_notes.items()]) or "N/A"
                lines.append(f"| **{comp.dimension}** | {comp.analysis} | {notes} |")
            lines.append("")

        # 6. Calculations & Quantitative Derived Metrics
        lines.append("## 6. Derived Calculations & Metrics")
        lines.append("")
        if report.calculations:
            lines.append("| Description | Safe Mathematical Expression | Computed Result | Interpretation |")
            lines.append("|---|---|---|---|")
            for calc in report.calculations:
                lines.append(f"| {calc.description} | `{calc.expression}` | **{calc.result}** | {calc.interpretation} |")
            lines.append("")
        else:
            lines.append("No derived quantitative calculations required for this research objective.")
            lines.append("")

        # 7. Disagreements and Conflicting Sources
        if report.conflicts:
            lines.append("## 7. Conflicting Information & Discrepancies")
            lines.append("")
            for conf in report.conflicts:
                lines.append(f"### Discrepancy: {conf.topic}")
                lines.append(f"- **Source A ({conf.source_a_url}):** {conf.source_a_claim}")
                lines.append(f"- **Source B ({conf.source_b_url}):** {conf.source_b_claim}")
                lines.append(f"- **Evaluation & Resolution:** {conf.resolution}")
                lines.append(f"- **Synthesized Fact:** {conf.resolved_claim}")
                lines.append("")

        # 8. Evidence & Sources (with citations [1], [2]...)
        lines.append("## 8. Grounded Evidence & Authoritative Sources")
        lines.append("")
        lines.append("### Evidence Register")
        lines.append("")
        for ev in report.evidence:
            conf_detail = ""
            if ev.confidence_factors:
                cf = ev.confidence_factors
                conf_detail = f"(Authority: {cf.source_authority}, Directness: {cf.evidence_directness}, Independent Sources: {cf.independent_sources})"
            lines.append(f"- **[{ev.id}] {ev.claim}**")
            lines.append(f"  - *Quote/Excerpt:* \"{ev.supporting_quote_or_excerpt}\"")
            lines.append(f"  - *Source:* [{ev.source_title}]({ev.source_url}) ({ev.source_type.value})")
            lines.append(f"  - *Confidence:* {int(ev.confidence * 100)}% {conf_detail}")
        lines.append("")

        lines.append("### Source Directory")
        lines.append("")
        for i, src in enumerate(report.sources, 1):
            lines.append(f"[{i}] [{src.title}]({src.url}) — Type: `{src.source_type.value}` (Authority Score: {src.authority_score})")
        lines.append("")

        # 9. Agent Execution Summary
        lines.append("## 9. Agent Execution Summary")
        lines.append("")
        es = report.execution_summary
        lines.append(f"- **Steps Planned / Completed:** {es.steps_planned} / {es.steps_completed}")
        lines.append(f"- **Total Tool Invocations:** {es.tool_calls_total}")
        lines.append(f"  - Web Searches: {es.search_queries_executed}")
        lines.append(f"  - Web Pages Fetched: {es.pages_fetched}")
        lines.append(f"  - Calculations Performed: {es.calculations_performed}")
        lines.append(f"- **Failures Detected:** {es.failures_detected}")
        lines.append(f"- **Recoveries Performed:** {es.recoveries_performed}")
        lines.append(f"- **Loop Detections Triggered:** {es.loop_detections_triggered}")
        lines.append("")

        # 10. Confidence Summary
        if report.confidence_summary:
            lines.append("## 10. Confidence Assessment")
            lines.append("")
            for k, v in report.confidence_summary.items():
                lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
            lines.append("")

        # 11. Limitations
        lines.append("## 11. Limitations")
        lines.append("")
        if report.limitations:
            for lim in report.limitations:
                lines.append(f"- **{lim.factor}:** {lim.impact} *(Note: {lim.mitigation_or_note})*")
        else:
            lines.append("- Public web access is subject to site rate limits and robot exclusions.")
            lines.append("- Time-bounded search horizon reflects publicly available documentation up to the present date.")
        lines.append("")

        # 12. Production Improvements
        lines.append("## 12. Production Improvements")
        lines.append("")
        lines.append("- **Persistent Vector & Document Graph:** Incorporate hierarchical indexing for deeper multi-page PDF/API exploration.")
        lines.append("- **Distributed Execution Workers:** Parallelize source fetching with async worker pools across multiple proxies.")
        lines.append("- **Continuous Evaluation & Monitoring:** Track automated hallucination and fact-verification metrics (RAGAS/TruLens).")
        lines.append("- **Human-in-the-Loop Approval:** Interactive checkpoints for critical domain assessments or high-budget tool runs.")
        lines.append("")

        return "\n".join(lines)

    @classmethod
    def save_reports(cls, report: ResearchReport, output_dir: Path) -> Dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save JSON
        json_path = output_dir / "report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        # 2. Save Markdown
        md_path = output_dir / "report.md"
        md_content = cls.generate_markdown(report)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {"json": json_path, "markdown": md_path}
