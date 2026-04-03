"""SEC Form 4 insider transaction detector using EDGAR EFTS API."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import httpx

from src.models import Event, EventType
from src.settings import settings

from .base import BaseDetector

logger = logging.getLogger(__name__)

EFTS_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_FULL_TEXT_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

# Use the documented full-text search endpoint
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_API_URL = "https://efts.sec.gov/LATEST/search-index"

# Correct EDGAR EFTS endpoint for full-text search
SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"


class SecForm4Detector(BaseDetector):
    """Detects SEC Form 4 insider trading filings via EDGAR EFTS."""

    def __init__(self):
        self.headers = {
            "User-Agent": f"MoneyInMotion/1.0 ({settings.contact_email})",
            "Accept": "application/json",
        }
        self.rate_limit_delay = 1.0 / settings.sec_rate_limit

    def detect(self, lookback_hours: int = 24) -> list[Event]:
        """Query EDGAR for Form 4 filings within lookback window."""
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        date_str = since.strftime("%Y-%m-%d")

        events = []
        try:
            filings = self._search_filings(date_str)
            logger.info(f"Found {len(filings)} Form 4 filings since {date_str}")
        except Exception as e:
            logger.error(f"EDGAR EFTS search failed: {e}")
            return []

        for filing in filings:
            try:
                event = self._parse_filing(filing)
                if event:
                    # Attempt XML enrichment (optional, per scenario fix #4)
                    self._enrich_from_xml(event)
                    events.append(event)
            except Exception as e:
                # Scenario fix #4: per-filing error handling — one bad filing doesn't kill the batch
                logger.warning(
                    f"Failed to parse filing {filing.get('accession_number', 'unknown')}: {e}"
                )
                continue

        return events

    def _search_filings(self, date_from: str) -> list[dict]:
        """Search EDGAR EFTS for Form 4 filings."""

        def _do_search():
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    "https://efts.sec.gov/LATEST/search-index",
                    params={
                        "q": '"FORM 4"',
                        "dateRange": "custom",
                        "startdt": date_from,
                        "forms": "4",
                    },
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("hits", {}).get("hits", [])

        # Scenario fix #2: retry with backoff on EDGAR failures
        return self._retry_request(
            _do_search,
            max_attempts=settings.sec_retry_attempts,
            backoff=settings.sec_retry_backoff,
            description="EDGAR EFTS search",
        )

    def _parse_filing(self, filing: dict) -> Event | None:
        """Parse an EFTS search result into an Event."""
        source = filing.get("_source", filing)

        accession = source.get("file_num", "") or source.get("accession_no", "")
        if not accession:
            return None

        # Extract person and company from filing data
        display_names = source.get("display_names", [])
        entity_name = display_names[0] if display_names else source.get("entity_name", "")
        company_name = display_names[1] if len(display_names) > 1 else source.get("company_name", "")

        filed_str = source.get("file_date", "") or source.get("period_of_report", "")
        filed_at = None
        if filed_str:
            try:
                filed_at = datetime.strptime(filed_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        url = source.get("file_url", "")
        if not url and accession:
            clean = accession.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{clean}"

        return Event(
            event_type=EventType.SEC_FORM4,
            source_id=accession,
            person_name=entity_name,
            company_name=company_name,
            filed_at=filed_at,
            url=url,
            raw_data=source,
        )

    def _enrich_from_xml(self, event: Event) -> None:
        """Attempt to extract detailed transaction data from Form 4 XML.

        This is optional enrichment — if it fails, the event still has metadata.
        Scenario fix #4: catches all XML parsing errors gracefully.
        """
        xml_url = event.raw_data.get("xml_url", "")
        if not xml_url:
            return

        time.sleep(self.rate_limit_delay)

        try:

            def _fetch_xml():
                with httpx.Client(timeout=30) as client:
                    resp = client.get(xml_url, headers=self.headers)
                    resp.raise_for_status()
                    return resp.text

            xml_text = self._retry_request(
                _fetch_xml,
                max_attempts=2,
                backoff=2.0,
                description=f"XML fetch {xml_url}",
            )

            root = ET.fromstring(xml_text)
            ns = {"": "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"}

            # Try to extract transaction details (handles missing elements gracefully)
            for txn in root.iter():
                if "nonDerivativeTransaction" in txn.tag or "derivativeTransaction" in txn.tag:
                    self._extract_transaction(txn, event)
                    break  # take first transaction

        except Exception as e:
            logger.debug(f"XML enrichment skipped for {event.source_id}: {e}")

    def _extract_transaction(self, txn_elem, event: Event) -> None:
        """Extract transaction details from XML element into event.raw_data."""
        def _find_text(elem, *tags):
            """Safely find nested text in XML, returns empty string if missing."""
            current = elem
            for tag in tags:
                found = None
                for child in current:
                    if tag in child.tag:
                        found = child
                        break
                if found is None:
                    return ""
                current = found
            return current.text or ""

        try:
            shares_str = _find_text(txn_elem, "transactionAmounts", "transactionShares", "value")
            price_str = _find_text(txn_elem, "transactionAmounts", "transactionPricePerShare", "value")
            code = _find_text(txn_elem, "transactionCoding", "transactionCode")

            shares = float(shares_str) if shares_str else 0
            price = float(price_str) if price_str else 0

            event.raw_data.update({
                "transaction_type": code,
                "shares": shares,
                "price_per_share": price,
                "total_value": shares * price,
                "xml_enriched": True,
            })

            # Extract insider title if available
            for elem in txn_elem.iter():
                if "officerTitle" in elem.tag and elem.text:
                    event.raw_data["insider_title"] = elem.text
                    break

        except (ValueError, AttributeError) as e:
            logger.debug(f"Transaction extraction partial for {event.source_id}: {e}")
