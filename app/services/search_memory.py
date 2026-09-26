import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.deduplication import DeduplicationService

logger = logging.getLogger("agentic_research.memory")


class SearchMemoryStore:
    """
    Lightweight local search memory store for recording completed research sessions
    and retrieving relevant prior findings.
    Persists records to data/search_history.json.
    """

    def __init__(self, storage_path: str = "data/search_history.json"):
        self.file_path = Path(storage_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.file_path.exists():
            try:
                self.file_path.write_text("[]", encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not initialize search memory file: {e}")

    def _load_history(self) -> List[Dict[str, Any]]:
        try:
            if not self.file_path.exists():
                return []
            content = self.file_path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            return json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to read search memory from {self.file_path}: {e}")
            return []

    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        try:
            self.file_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write search memory to {self.file_path}: {e}")

    def save_session(
        self,
        goal: str,
        summary: str,
        key_points: List[str],
        sources: List[Dict[str, Any]],
        execution_time_seconds: float = 0.0
    ) -> None:
        """Saves a completed research session to local memory."""
        history = self._load_history()

        record = {
            "session_id": f"sess-{len(history) + 1:04d}",
            "goal": goal.strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary[:600] if summary else "",
            "key_points": key_points[:6] if key_points else [],
            "sources_count": len(sources),
            "sources_preview": [s.get("url") for s in sources[:5] if isinstance(s, dict)],
            "execution_time_seconds": round(execution_time_seconds, 2)
        }

        # Keep last 50 sessions
        history.append(record)
        if len(history) > 50:
            history = history[-50:]

        self._save_history(history)
        logger.info(f"Saved session '{record['session_id']}' to search memory ({self.file_path}).")

    def lookup_previous_research(
        self,
        query: str,
        min_similarity: float = 0.50
    ) -> Optional[Dict[str, Any]]:
        """
        Looks up a previous search session with significant keyword or semantic similarity.
        Returns the matching session or None.
        """
        history = self._load_history()
        best_match = None
        best_score = 0.0

        for item in reversed(history):
            past_goal = item.get("goal", "")
            sim = DeduplicationService.calculate_jaccard_similarity(query, past_goal)
            if sim > best_score:
                best_score = sim
                best_match = item

        if best_match and best_score >= min_similarity:
            logger.info(
                f"[SEARCH MEMORY MATCH] Found prior research for query (Similarity: {best_score:.2f}): "
                f"'{best_match['goal']}' from {best_match['timestamp']}"
            )
            return best_match

        return None

    def list_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the most recent research sessions."""
        history = self._load_history()
        return list(reversed(history[-limit:]))
