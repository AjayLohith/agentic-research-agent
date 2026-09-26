import re
import logging
from typing import List, Tuple, Set, Optional

logger = logging.getLogger("agentic_research.relevance")

# Common web boilerplate to reject immediately
IRRELEVANT_PATTERNS = [
    r"cookie\s+policy",
    r"accept\s+(all\s+)?cookies",
    r"privacy\s+policy",
    r"terms\s+(and\s+conditions|of\s+service)",
    r"sign\s+up\s+for\s+(our\s+)?newsletter",
    r"all\s+rights\s+reserved",
    r"enable\s+javascript",
    r"subscribe\s+to\s+our\s+mailing\s+list",
    r"click\s+here\s+to\s+login",
    r"sponsored\s+content",
    r"advertisement",
]

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


class RelevanceFilter:
    """
    Evaluates and filters web content and candidate evidence snippets for semantic relevance
    relative to the user's research objective.
    Explicitly drops boilerplate, advertisement text, and off-topic information.
    """

    def __init__(self, min_relevance_score: float = 0.30):
        self.min_relevance_score = min_relevance_score

    @staticmethod
    def extract_keywords(text: str) -> Set[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", text.lower())
        return {w for w in words if w not in STOPWORDS}

    def is_boilerplate(self, text: str) -> bool:
        lower = text.lower()
        for pat in IRRELEVANT_PATTERNS:
            if re.search(pat, lower):
                return True
        return False

    def evaluate_relevance(
        self,
        candidate_text: str,
        goal: str,
        context_keywords: Optional[Set[str]] = None
    ) -> Tuple[bool, float, str]:
        """
        Calculates relevance score of candidate text against research goal.
        Returns: (is_relevant: bool, score: float, reason: str)
        """
        clean_text = candidate_text.strip()
        if len(clean_text) < 25:
            return False, 0.0, "Content too short or devoid of substantive claims"

        if self.is_boilerplate(clean_text):
            return False, 0.05, "Classified as web boilerplate, navigation, or cookie notice"

        goal_keywords = self.extract_keywords(goal)
        if context_keywords:
            goal_keywords.update(context_keywords)

        text_keywords = self.extract_keywords(clean_text)

        if not text_keywords or not goal_keywords:
            return True, 0.5, "Insufficient keyword context for strict rejection"

        # Overlap score
        overlap = goal_keywords.intersection(text_keywords)
        overlap_ratio = len(overlap) / max(len(goal_keywords), 1)

        # Entity / Technical Term Bonus
        bonus = 0.0
        # If any specialized capitalized or numeric token from goal matches text
        for token in goal.split():
            if len(token) > 3 and token.lower() in text_keywords:
                bonus += 0.15

        score = min(round(overlap_ratio * 0.7 + bonus, 2), 1.0)

        # Baseline floor for substantive sentences with at least one direct goal keyword
        if len(overlap) >= 1 and score < 0.35:
            score = 0.40

        is_relevant = score >= self.min_relevance_score
        reason = (
            f"Matches core keywords: {list(overlap)[:4]}"
            if is_relevant
            else f"Insufficient alignment with goal (score {score} < {self.min_relevance_score})"
        )

        return is_relevant, score, reason

    def filter_sentences(
        self,
        sentences: List[str],
        goal: str,
        max_sentences: int = 5
    ) -> List[Tuple[str, float, str]]:
        """
        Filters a list of sentences, returning only those that meet relevance criteria.
        Returns list of (sentence, score, reason).
        """
        relevant_items = []
        for s in sentences:
            is_rel, score, reason = self.evaluate_relevance(s, goal)
            if is_rel:
                relevant_items.append((s, score, reason))

        # Sort by relevance score descending
        relevant_items.sort(key=lambda x: x[1], reverse=True)
        return relevant_items[:max_sentences]
