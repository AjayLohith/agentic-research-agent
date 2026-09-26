import re
from urllib.parse import urlparse
from app.models.evidence import SourceType, Source


class SourceClassificationService:
    """
    Classifies URLs into standardized source quality tiers and calculates an objective authority score.
    Supports arbitrary domains without hardcoding single companies.
    """

    OFFICIAL_DOC_PATTERNS = [
        re.compile(r"docs?\.", re.IGNORECASE),
        re.compile(r"/docs?(?:/|$)", re.IGNORECASE),
        re.compile(r"documentation", re.IGNORECASE),
        re.compile(r"developer\.", re.IGNORECASE),
        re.compile(r"api\.", re.IGNORECASE),
        re.compile(r"read(?:the)?docs\.io", re.IGNORECASE),
        re.compile(r"pkg\.go\.dev", re.IGNORECASE),
        re.compile(r"pypi\.org", re.IGNORECASE),
    ]

    ACADEMIC_GOV_PATTERNS = [
        re.compile(r"\.gov(?:\.[a-z]{2})?$", re.IGNORECASE),
        re.compile(r"\.edu(?:\.[a-z]{2})?$", re.IGNORECASE),
        re.compile(r"arxiv\.org", re.IGNORECASE),
        re.compile(r"acm\.org", re.IGNORECASE),
        re.compile(r"ieee\.org", re.IGNORECASE),
        re.compile(r"springer\.com", re.IGNORECASE),
        re.compile(r"nature\.com", re.IGNORECASE),
    ]

    REPUTABLE_PUB_PATTERNS = [
        re.compile(r"techcrunch\.com", re.IGNORECASE),
        re.compile(r"venturebeat\.com", re.IGNORECASE),
        re.compile(r"wired\.com", re.IGNORECASE),
        re.compile(r"theverge\.com", re.IGNORECASE),
        re.compile(r"reuters\.com", re.IGNORECASE),
        re.compile(r"bloomberg\.com", re.IGNORECASE),
        re.compile(r"infoworld\.com", re.IGNORECASE),
        re.compile(r"zdnet\.com", re.IGNORECASE),
    ]

    COMMUNITY_PATTERNS = [
        re.compile(r"reddit\.com", re.IGNORECASE),
        re.compile(r"medium\.com", re.IGNORECASE),
        re.compile(r"dev\.to", re.IGNORECASE),
        re.compile(r"stackoverflow\.com", re.IGNORECASE),
        re.compile(r"hackernews\.com|news\.ycombinator\.com", re.IGNORECASE),
        re.compile(r"substack\.com", re.IGNORECASE),
        re.compile(r"hashnode\.dev", re.IGNORECASE),
    ]

    @classmethod
    def classify_url(cls, url: str) -> SourceType:
        if not url:
            return SourceType.UNKNOWN
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            full_url = f"{domain}{path}"
        except Exception:
            return SourceType.UNKNOWN

        for pattern in cls.ACADEMIC_GOV_PATTERNS:
            if pattern.search(domain):
                return SourceType.ACADEMIC_GOV

        for pattern in cls.OFFICIAL_DOC_PATTERNS:
            if pattern.search(full_url):
                return SourceType.OFFICIAL_DOCS

        for pattern in cls.REPUTABLE_PUB_PATTERNS:
            if pattern.search(domain):
                return SourceType.REPUTABLE_PUB

        for pattern in cls.COMMUNITY_PATTERNS:
            if pattern.search(domain):
                return SourceType.COMMUNITY

        # If it's a root organizational/company domain (e.g. github.com, organization domain)
        if any(keyword in domain for keyword in ["github.com", "gitlab.com", "apache.org", "python.org"]):
            return SourceType.OFFICIAL_PAGE

        return SourceType.UNKNOWN

    @classmethod
    def calculate_authority_score(cls, source_type: SourceType) -> float:
        scoring_matrix = {
            SourceType.OFFICIAL_DOCS: 0.95,
            SourceType.OFFICIAL_API: 0.95,
            SourceType.ACADEMIC_GOV: 0.92,
            SourceType.OFFICIAL_PAGE: 0.85,
            SourceType.REPUTABLE_PUB: 0.75,
            SourceType.COMMUNITY: 0.50,
            SourceType.UNKNOWN: 0.40,
        }
        return scoring_matrix.get(source_type, 0.40)

    @classmethod
    def create_source(cls, url: str, title: str) -> Source:
        stype = cls.classify_url(url)
        score = cls.calculate_authority_score(stype)
        return Source(
            url=url,
            title=title or url,
            source_type=stype,
            authority_score=score
        )
