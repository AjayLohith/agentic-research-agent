import re
import hashlib
import logging
from typing import List, Tuple, Set, Optional, Dict
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from app.models.evidence import Source, Evidence

logger = logging.getLogger("agentic_research.deduplication")

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "source", "fbclid", "gclid", "mc_cid", "mc_eid", "ved"
}


class DeduplicationService:
    """
    Handles both URL-level and content-level duplicate detection.
    Normalizes web URLs to strip tracking tokens and fragments,
    and fingerprints text using SHA-256 and Jaccard token similarity
    to filter out redundant syndicated or mirrored content.
    """

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        """
        Normalizes a URL by lowercasing scheme/netloc, removing tracking query params,
        stripping fragments, and normalizing trailing slashes.
        """
        if not raw_url:
            return ""

        url = raw_url.strip()
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            scheme = parsed.scheme.lower() or "https"

            # Filter tracking query parameters
            query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
            filtered_query = [
                (k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS
            ]
            clean_query = urlencode(filtered_query)

            # Normalize path: remove trailing slash if path is longer than '/'
            path = parsed.path
            if len(path) > 1 and path.endswith("/"):
                path = path[:-1]

            normalized = urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
            return normalized
        except Exception:
            return url.strip().rstrip("/")

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Computes a SHA-256 fingerprint of normalized text."""
        normalized = re.sub(r"\s+", " ", text.lower().strip())
        normalized = re.sub(r"[^\w\s]", "", normalized)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def calculate_jaccard_similarity(text_a: str, text_b: str) -> float:
        """Computes token-level Jaccard similarity between two passages."""
        words_a = set(re.findall(r"\b\w{3,}\b", text_a.lower()))
        words_b = set(re.findall(r"\b\w{3,}\b", text_b.lower()))
        if not words_a or not words_b:
            return 0.0

        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return len(intersection) / len(union)

    @classmethod
    def is_duplicate_content(
        cls,
        candidate_text: str,
        seen_hashes: Set[str],
        seen_texts: Optional[List[str]] = None,
        similarity_threshold: float = 0.85
    ) -> Tuple[bool, str]:
        """
        Checks whether content is identical (via SHA-256) or substantially similar (via Jaccard).
        Returns: (is_duplicate: bool, reason: str)
        """
        content_hash = cls.compute_content_hash(candidate_text)
        if content_hash in seen_hashes:
            return True, "Exact duplicate content matched by SHA-256 fingerprint"

        if seen_texts:
            for past_text in seen_texts:
                sim = cls.calculate_jaccard_similarity(candidate_text, past_text)
                if sim >= similarity_threshold:
                    return True, f"Near-duplicate content detected (Jaccard similarity: {sim:.2f})"

        return False, "Unique content"

    @classmethod
    def deduplicate_sources(cls, sources: List[Source]) -> Tuple[List[Source], int]:
        """
        Deduplicates a list of Source objects by normalized URL.
        Preserves the source with highest authority score.
        """
        unique_by_url: Dict[str, Source] = {}
        duplicates_count = 0

        for s in sources:
            norm_url = cls.normalize_url(s.url)
            if norm_url in unique_by_url:
                duplicates_count += 1
                # If current source has higher authority, keep it
                if s.authority_score > unique_by_url[norm_url].authority_score:
                    unique_by_url[norm_url] = s
            else:
                s.url = norm_url
                unique_by_url[norm_url] = s

        return list(unique_by_url.values()), duplicates_count

    @classmethod
    def deduplicate_evidence(cls, evidence_items: List[Evidence]) -> Tuple[List[Evidence], int]:
        """
        Deduplicates evidence items by URL and text content fingerprint.
        """
        seen_hashes: Set[str] = set()
        seen_texts: List[str] = []
        unique_evidence: List[Evidence] = []
        duplicates_count = 0

        for ev in evidence_items:
            # Check content duplication
            is_dup, _ = cls.is_duplicate_content(
                ev.supporting_quote_or_excerpt or ev.claim,
                seen_hashes=seen_hashes,
                seen_texts=seen_texts,
                similarity_threshold=0.85
            )

            if is_dup:
                duplicates_count += 1
                logger.debug(f"Filtered duplicate evidence: '{ev.claim[:60]}...'")
            else:
                ev_hash = cls.compute_content_hash(ev.supporting_quote_or_excerpt or ev.claim)
                ev.content_hash = ev_hash
                seen_hashes.add(ev_hash)
                seen_texts.append(ev.supporting_quote_or_excerpt or ev.claim)
                ev.source_url = cls.normalize_url(ev.source_url)
                unique_evidence.append(ev)

        return unique_evidence, duplicates_count
