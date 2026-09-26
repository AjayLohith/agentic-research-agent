import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class SafeJsonFormatter(logging.Formatter):
    """
    Structured JSON log formatter that redacts sensitive credentials and formats logs as JSON lines.
    """
    SENSITIVE_PATTERNS = [
        re.compile(r"(sk-[a-zA-Z0-9_\-]{20,})"),
        re.compile(r"(api[-_]?key\s*[:=]\s*['\"]?)([^'\"\s]+)", re.IGNORECASE),
        re.compile(r"(bearer\s+)([a-zA-Z0-9_\-\.]+)", re.IGNORECASE),
    ]

    def _sanitize(self, text: str) -> str:
        for pattern in self.SENSITIVE_PATTERNS:
            text = pattern.sub(r"\1***REDACTED***", text)
        return text

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self._sanitize(record.getMessage()),
        }
        if hasattr(record, "event_type"):
            data["event_type"] = record.event_type
        if hasattr(record, "payload") and record.payload is not None:
            # ensure payload strings are sanitized if json dumped
            try:
                raw_json = json.dumps(record.payload, default=str)
                data["payload"] = json.loads(self._sanitize(raw_json))
            except Exception:
                data["payload"] = self._sanitize(str(record.payload))
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Clean console formatter with timestamp and level."""
    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        # Redact keys in console as well
        for pattern in SafeJsonFormatter.SENSITIVE_PATTERNS:
            msg = pattern.sub(r"\1***REDACTED***", msg)
        return f"[{record.levelname}] {record.name}: {msg}"


def setup_logging(log_level: str = "INFO", log_file_path: Path = Path("output/sample_run.log")) -> logging.Logger:
    """Configures application-wide logging with both file JSON logging and console logging."""
    logger = logging.getLogger("agentic_research")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    # Ensure log file parent directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # File Handler - JSON lines
    file_handler = logging.FileHandler(str(log_file_path), encoding="utf-8", mode="a")
    file_handler.setFormatter(SafeJsonFormatter())
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ConsoleFormatter())
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.addHandler(console_handler)

    # Avoid duplicate root logs
    logger.propagate = False
    return logger
