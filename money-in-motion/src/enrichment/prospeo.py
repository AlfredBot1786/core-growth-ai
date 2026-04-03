"""Prospeo.io enrichment provider (fallback)."""

from __future__ import annotations

import logging

import httpx

from src.models import EnrichmentData, EnrichmentStatus
from src.settings import settings

from .base import BaseEnrichmentProvider

logger = logging.getLogger(__name__)


class ProspeoProvider(BaseEnrichmentProvider):
    """Prospeo.io contact enrichment ($39/mo for 1,000 credits)."""

    provider_name = "prospeo"

    def enrich(self, person_name: str, company_name: str) -> EnrichmentData | None:
        if not settings.prospeo_api_key:
            return None

        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    "https://api.prospeo.io/person-search",
                    json={
                        "first_name": person_name.split()[0] if person_name else "",
                        "last_name": " ".join(person_name.split()[1:]) if person_name else "",
                        "company": company_name,
                    },
                    headers={"X-KEY": settings.prospeo_api_key},
                )

                if response.status_code in (402, 429):
                    logger.warning(f"Prospeo credits exhausted: {response.status_code}")
                    return EnrichmentData(status=EnrichmentStatus.FAILED, provider="prospeo")

                response.raise_for_status()
                data = response.json()

                if not data.get("email"):
                    return None

                return EnrichmentData(
                    email=data.get("email", ""),
                    phone=data.get("phone", ""),
                    linkedin_url=data.get("linkedin", ""),
                    job_title=data.get("title", ""),
                    provider="prospeo",
                    status=EnrichmentStatus.SUCCESS,
                )

        except Exception as e:
            logger.warning(f"Prospeo enrichment failed for {person_name}: {e}")
            return EnrichmentData(status=EnrichmentStatus.FAILED, provider="prospeo")
