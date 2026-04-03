"""Base enrichment provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import EnrichmentData


class BaseEnrichmentProvider(ABC):
    """Interface for contact enrichment providers (Apollo, Prospeo, etc.)."""

    @abstractmethod
    def enrich(self, person_name: str, company_name: str) -> EnrichmentData | None:
        """Attempt to enrich a contact. Returns None if not found."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
