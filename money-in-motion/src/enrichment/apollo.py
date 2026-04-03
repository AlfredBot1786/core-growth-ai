"""Apollo.io enrichment provider."""

from __future__ import annotations

import logging

import httpx

from src.models import EnrichmentData, EnrichmentStatus
from src.settings import settings

from .base import BaseEnrichmentProvider

logger = logging.getLogger(__name__)


class ApolloProvider(BaseEnrichmentProvider):
    """Apollo.io contact enrichment (free tier: 10k credits/month)."""

    provider_name = "apollo"

    def enrich(self, person_name: str, company_name: str) -> EnrichmentData | None:
        if not settings.apollo_api_key:
            return None

        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    "https://api.apollo.io/v1/people/match",
                    json={
                        "name": person_name,
                        "organization_name": company_name,
                    },
                    headers={"X-Api-Key": settings.apollo_api_key},
                )

                if response.status_code in (402, 429):
                    # Scenario fix #3: credit exhaustion — don't retry, signal failure
                    logger.warning(f"Apollo credits exhausted or rate limited: {response.status_code}")
                    return EnrichmentData(
                        status=EnrichmentStatus.FAILED,
                        provider="apollo",
                    )

                response.raise_for_status()
                data = response.json()

                person = data.get("person", {})
                if not person:
                    return None

                return EnrichmentData(
                    email=person.get("email", ""),
                    phone=person.get("phone_number", ""),
                    linkedin_url=person.get("linkedin_url", ""),
                    job_title=person.get("title", ""),
                    company_size=str(person.get("organization", {}).get("estimated_num_employees", "")),
                    location=person.get("city", ""),
                    provider="apollo",
                    status=EnrichmentStatus.SUCCESS if person.get("email") else EnrichmentStatus.PARTIAL,
                )

        except httpx.HTTPStatusError as e:
            logger.warning(f"Apollo enrichment failed for {person_name}: {e}")
            return EnrichmentData(status=EnrichmentStatus.FAILED, provider="apollo")
        except Exception as e:
            logger.error(f"Apollo enrichment error for {person_name}: {e}")
            return None
