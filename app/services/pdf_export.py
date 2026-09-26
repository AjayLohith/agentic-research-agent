import logging
from pathlib import Path
from typing import Optional

from app.models.report import ResearchReport

logger = logging.getLogger("agentic_research.pdf")


class PdfExportService:
    """
    Renders structured ResearchReport data into a publication-ready PDF document
    using ReportLab.
    """

    @staticmethod
    def export_report_to_pdf(report: ResearchReport, output_file: Path) -> Optional[Path]:
        """
        Exports a ResearchReport object to the designated PDF path.
        Returns the output Path on success, or None on failure.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        except ImportError:
            logger.warning("reportlab is not installed. PDF export skipped.")
            return None

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            doc = SimpleDocTemplate(
                str(output_file),
                pagesize=letter,
                leftMargin=40,
                rightMargin=40,
                topMargin=40,
                bottomMargin=40
            )

            styles = getSampleStyleSheet()

            # Custom typography styles
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=20,
                leading=24,
                textColor=colors.HexColor('#0f172a'),
                alignment=TA_LEFT,
                spaceAfter=6
            )
            subtitle_style = ParagraphStyle(
                'DocSubTitle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=11,
                leading=15,
                textColor=colors.HexColor('#475569'),
                spaceAfter=12
            )
            h1_style = ParagraphStyle(
                'SectionH1',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#1e293b'),
                spaceBefore=12,
                spaceAfter=6
            )
            h2_style = ParagraphStyle(
                'SectionH2',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=11,
                leading=15,
                textColor=colors.HexColor('#334155'),
                spaceBefore=8,
                spaceAfter=4
            )
            body_style = ParagraphStyle(
                'BodyDark',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=9.5,
                leading=14,
                textColor=colors.HexColor('#1e293b'),
                alignment=TA_LEFT,
                spaceAfter=6
            )
            bullet_style = ParagraphStyle(
                'BulletDark',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=9,
                leading=13,
                textColor=colors.HexColor('#1e293b'),
                leftIndent=15,
                firstLineIndent=-10,
                spaceAfter=3
            )
            callout_style = ParagraphStyle(
                'Callout',
                parent=styles['Normal'],
                fontName='Helvetica-Oblique',
                fontSize=9,
                leading=13,
                textColor=colors.HexColor('#0369a1'),
                spaceAfter=4
            )

            story = []

            # 1. Header & Title
            story.append(Paragraph("Autonomous Research & Intelligence Report", title_style))
            goal_text = f"<b>Research Goal:</b> {report.metadata.goal}"
            story.append(Paragraph(goal_text, subtitle_style))
            meta_info = (
                f"Generated: {report.metadata.generated_at[:19]} UTC &nbsp;|&nbsp; "
                f"Execution: {report.metadata.execution_time_seconds:.2f}s &nbsp;|&nbsp; "
                f"Agent Version: {report.metadata.agent_version}"
            )
            story.append(Paragraph(meta_info, subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#cbd5e1'), spaceAfter=10))

            # 2. Executive Summary
            story.append(Paragraph("1. Executive Summary", h1_style))
            story.append(Paragraph(report.executive_summary, body_style))
            story.append(Spacer(1, 8))

            # 3. Methodology
            if report.methodology:
                story.append(Paragraph("2. Research Methodology", h1_style))
                story.append(Paragraph(report.methodology, body_style))
                story.append(Spacer(1, 6))

            # 4. Key Points (Takeaways)
            if report.key_points:
                story.append(Paragraph("3. Core Key Points", h1_style))
                for pt in report.key_points:
                    story.append(Paragraph(f"• &nbsp;{pt}", bullet_style))
                story.append(Spacer(1, 8))

            # 5. Important Findings
            if report.key_findings:
                sec_num = "4" if report.key_points else "3"
                story.append(Paragraph(f"{sec_num}. Important Findings", h1_style))
                for kf in report.key_findings:
                    conf_pct = int(kf.confidence * 100)
                    story.append(Paragraph(f"<b>{kf.title}</b> <i>(Category: {kf.category} | Confidence: {conf_pct}%)</i>", h2_style))
                    story.append(Paragraph(kf.summary, body_style))
                story.append(Spacer(1, 8))

            # 6. Actionable Insights
            if report.actionable_insights:
                story.append(Paragraph("Actionable Insights & Recommendations", h1_style))
                for ins in report.actionable_insights:
                    story.append(Paragraph(f"→ &nbsp;<b>{ins}</b>", callout_style))
                story.append(Spacer(1, 8))

            # 7. Comparison Matrix
            if report.comparison:
                story.append(Paragraph("Comparative Analysis", h1_style))
                comp_data = [["Dimension", "Synthesized Comparative Overview"]]
                for cd in report.comparison[:4]:
                    comp_data.append([
                        Paragraph(f"<b>{cd.dimension}</b>", body_style),
                        Paragraph(cd.analysis, body_style)
                    ])

                comp_table = Table(comp_data, colWidths=[130, 400])
                comp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(comp_table)
                story.append(Spacer(1, 10))

            # 8. Grounded Evidence & Sources
            if report.sources:
                story.append(Paragraph("Authoritative Sources & Provenance", h1_style))
                source_data = [["#", "Title", "Type", "Authority", "URL"]]
                for idx, src in enumerate(report.sources[:8], 1):
                    source_data.append([
                        str(idx),
                        Paragraph(src.title[:35] if src.title else "Source Page", body_style),
                        src.source_type.value if hasattr(src.source_type, 'value') else str(src.source_type),
                        f"{src.authority_score:.2f}",
                        Paragraph(f"<a href='{src.url}'>{src.url[:45]}...</a>", body_style)
                    ])

                src_table = Table(source_data, colWidths=[20, 160, 110, 50, 190])
                src_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(src_table)
                story.append(Spacer(1, 10))

            # 9. Execution Summary Table
            story.append(Paragraph("Execution Audit Summary", h1_style))
            es = report.execution_summary
            audit_data = [
                ["Metric", "Value", "Metric", "Value"],
                ["Steps Planned", str(es.steps_planned), "Tool Invocations", str(es.tool_calls_total)],
                ["Steps Completed", str(es.steps_completed), "Sources Gathered", str(len(report.sources))],
                ["Evidence Items", str(len(report.evidence)), "Duplicates Removed", str(es.sources_deduplicated)],
                ["Failures Detected", str(es.failures_detected), "Recoveries Performed", str(es.recoveries_performed)],
                ["Execution Time", f"{report.metadata.execution_time_seconds:.2f}s", "Irrelevant Filtered", str(es.items_filtered_for_irrelevance)]
            ]
            audit_table = Table(audit_data, colWidths=[130, 135, 130, 135])
            audit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(audit_table)

            # Build document
            doc.build(story)
            logger.info(f"Successfully generated PDF report at: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}", exc_info=True)
            return None
