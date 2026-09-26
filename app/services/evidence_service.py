from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse
from app.models.evidence import (
    Evidence,
    Source,
    SourceType,
    ConflictRecord,
    ConfidenceBreakdown
)
from app.services.source_service import SourceClassificationService


class EvidenceService:
    """
    Manages evidence extraction, explainable confidence calculation,
    conflict detection between competing sources, and coverage validation.
    """

    @staticmethod
    def calculate_confidence(
        source_type: SourceType,
        is_direct_quote: bool,
        corroborating_domains_count: int,
        has_conflict: bool = False
    ) -> ConfidenceBreakdown:
        """
        Calculates an explainable, grounded confidence score based on objective dimensions:
        1. source_authority (0.40 - 0.95)
        2. evidence_directness (0.70 - 0.95)
        3. independent_sources (0.60 - 0.95)
        4. conflict_penalty (0.00 or 0.15)
        """
        source_authority = SourceClassificationService.calculate_authority_score(source_type)
        evidence_directness = 0.95 if is_direct_quote else 0.75

        if corroborating_domains_count >= 3:
            independent_sources = 0.95
        elif corroborating_domains_count == 2:
            independent_sources = 0.85
        else:
            independent_sources = 0.65

        conflict_penalty = 0.15 if has_conflict else 0.0

        # Weighted calculation
        # Formula: (authority * 0.40) + (directness * 0.35) + (independent * 0.25) - penalty
        raw_score = (
            (source_authority * 0.40)
            + (evidence_directness * 0.35)
            + (independent_sources * 0.25)
            - conflict_penalty
        )
        overall = max(0.1, min(1.0, round(raw_score, 2)))

        return ConfidenceBreakdown(
            source_authority=round(source_authority, 2),
            evidence_directness=round(evidence_directness, 2),
            independent_sources=round(independent_sources, 2),
            conflict_penalty=round(conflict_penalty, 2),
            overall=overall
        )

    @classmethod
    def register_evidence(
        cls,
        claim: str,
        supporting_quote: str,
        source_url: str,
        source_title: str,
        entity_name: Optional[str] = None,
        existing_evidence: Optional[List[Evidence]] = None,
        has_conflict: bool = False
    ) -> Evidence:
        stype = SourceClassificationService.classify_url(source_url)

        # Count corroborating independent domains for this claim/entity
        distinct_domains = set()
        if source_url:
            distinct_domains.add(urlparse(source_url).netloc.lower())

        if existing_evidence:
            for item in existing_evidence:
                if entity_name and item.entity_name and entity_name.lower() in item.entity_name.lower():
                    domain = urlparse(item.source_url).netloc.lower()
                    if domain:
                        distinct_domains.add(domain)

        is_direct = bool(supporting_quote and len(supporting_quote.strip()) > 15)
        breakdown = cls.calculate_confidence(
            source_type=stype,
            is_direct_quote=is_direct,
            corroborating_domains_count=len(distinct_domains),
            has_conflict=has_conflict
        )

        evidence_id = f"ev-{len(existing_evidence or []) + 1}"
        return Evidence(
            id=evidence_id,
            claim=claim.strip(),
            supporting_quote_or_excerpt=supporting_quote.strip() if supporting_quote else "Direct textual observation recorded.",
            source_url=source_url,
            source_title=source_title or source_url,
            source_type=stype,
            confidence=breakdown.overall,
            confidence_factors=breakdown,
            entity_name=entity_name
        )

    @staticmethod
    def validate_coverage(evidence_list: List[Evidence]) -> Tuple[bool, List[str]]:
        """
        Validates whether current evidence collection meets quality thresholds:
        - Must have at least 1 valid source URL per evidence
        - Checks for completely unsupported empty quotes
        """
        issues: List[str] = []
        if not evidence_list:
            issues.append("Zero evidence items gathered.")
            return False, issues

        for i, ev in enumerate(evidence_list, 1):
            if not ev.source_url or not ev.source_url.startswith("http"):
                issues.append(f"Evidence {ev.id or i} missing valid HTTP source URL.")
            if not ev.supporting_quote_or_excerpt or len(ev.supporting_quote_or_excerpt) < 5:
                issues.append(f"Evidence {ev.id or i} has no verifiable supporting excerpt.")

        is_valid = len(issues) == 0
        return is_valid, issues
