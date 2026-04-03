"""Base detector interface."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from src.models import Event

logger = logging.getLogger(__name__)


class BaseDetector(ABC):
    """Base class for all event detectors."""

    @abstractmethod
    def detect(self, lookback_hours: int = 24) -> list[Event]:
        """Detect events within the lookback window. Must handle errors per-event."""
        ...

    def _retry_request(
        self,
        func,
        max_attempts: int = 3,
        backoff: float = 2.0,
        description: str = "request",
    ):
        """Retry a callable with exponential backoff. (Scenario fix #2: EDGAR retry)"""
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except Exception as e:
                last_error = e
                if attempt < max_attempts:
                    wait = backoff ** attempt
                    logger.warning(
                        f"{description} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"{description} failed after {max_attempts} attempts: {e}")
        raise last_error
