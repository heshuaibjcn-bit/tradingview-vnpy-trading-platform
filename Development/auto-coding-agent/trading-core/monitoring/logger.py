"""
System logger for monitoring logs.
"""

import asyncio
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional
import json

from .models import LogEntry, LogLevel


class SystemLogger:
    """Centralized system logger with in-memory buffering."""

    def __init__(self, max_entries: int = 1000, log_dir: str = "logs"):
        self.max_entries = max_entries
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self._logs: Deque[LogEntry] = deque(maxlen=max_entries)
        self._service_loggers: dict[str, List[str]] = {}

    def log(
        self,
        level: LogLevel,
        service: str,
        message: str,
        details: dict | None = None,
    ) -> LogEntry:
        """Add a log entry."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            service=service,
            message=message,
            details=details or {},
        )

        self._logs.append(entry)

        # Add to service-specific log
        if service not in self._service_loggers:
            self._service_loggers[service] = []
        self._service_loggers[service].append(json.dumps(entry.to_dict(), ensure_ascii=False))

        # Write to file
        self._write_to_file(entry)

        return entry

    def debug(self, service: str, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.DEBUG, service, message, kwargs)

    def info(self, service: str, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.INFO, service, message, kwargs)

    def warning(self, service: str, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.WARNING, service, message, kwargs)

    def error(self, service: str, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.ERROR, service, message, kwargs)

    def critical(self, service: str, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.CRITICAL, service, message, kwargs)

    def get_logs(
        self,
        service: Optional[str] = None,
        level: Optional[LogLevel] = None,
        limit: int = 100,
    ) -> List[LogEntry]:
        """Get filtered logs."""
        logs = list(self._logs)

        if service:
            logs = [l for l in logs if l.service == service]
        if level:
            logs = [l for l in logs if l.level == level]

        return sorted(logs, key=lambda l: l.timestamp, reverse=True)[:limit]

    def get_recent_logs(self, count: int = 50) -> List[LogEntry]:
        """Get most recent log entries."""
        return list(self._logs)[-count:]

    def get_error_logs(self, limit: int = 100) -> List[LogEntry]:
        """Get only error and critical logs."""
        return [
            l for l in self._logs
            if l.level in (LogLevel.ERROR, LogLevel.CRITICAL)
        ][:limit]

    def clear(self) -> None:
        """Clear all in-memory logs."""
        self._logs.clear()

    def _write_to_file(self, entry: LogEntry) -> None:
        """Write log entry to file."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"system_{today}.log"

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass  # Silently fail to avoid loops

    def get_service_names(self) -> List[str]:
        """Get list of services that have logged."""
        return list(self._service_loggers.keys())
