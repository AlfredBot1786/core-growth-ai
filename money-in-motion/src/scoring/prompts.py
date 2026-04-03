"""Scoring prompt templates — one per event type.

Scenario fix #23: prompts use structured data fields, not raw filing text,
to prevent prompt injection via SEC filing content.
"""

from __future__ import annotations

from src.models import EnrichmentData, Event, EventType


def get_prompt_for_event(event: Event, enrichment: EnrichmentData) -> str:
    """Return the appropriate scoring prompt for the event type."""
    builders = {
        EventType.SEC_FORM4: _form4_prompt,
        EventType.SEC_8K: _sec_8k_prompt,
        EventType.WARN_ACT: _warn_act_prompt,
        EventType.LINKEDIN: _linkedin_prompt,
    }
    builder = builders.get(event.event_type, _form4_prompt)
    return builder(event, enrichment)


def _sanitize(text: str) -> str:
    """Sanitize text to prevent prompt injection.

    Scenario fix #23: strips potential injection patterns from filing text.
    """
    if not text:
        return ""
    # Remove common injection patterns
    dangerous_patterns = [
        "ignore all previous",
        "ignore above",
        "disregard",
        "new instructions",
        "system prompt",
        "you are now",
        "forget everything",
    ]
    lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in lower:
            return "[CONTENT FILTERED]"
    # Truncate to prevent context overflow
    return text[:500]


def _form4_prompt(event: Event, enrichment: EnrichmentData) -> str:
    raw = event.raw_data
    txn_type_map = {"S": "Sale", "P": "Purchase", "A": "Grant/Award", "M": "Exercise"}
    txn_type = txn_type_map.get(raw.get("transaction_type", ""), raw.get("transaction_type", "Unknown"))

    return f"""You are a financial advisor lead scoring assistant. Score this insider transaction event for financial planning opportunity.

STRUCTURED DATA (verified from SEC filing):
- Person: {_sanitize(event.person_name)}
- Company: {_sanitize(event.company_name)}
- Transaction Type: {txn_type}
- Shares: {raw.get('shares', 'Unknown')}
- Price Per Share: ${raw.get('price_per_share', 'Unknown')}
- Total Value: ${raw.get('total_value', 'Unknown')}
- Insider Title: {_sanitize(raw.get('insider_title', 'Unknown'))}
- Filing Date: {event.filed_at or 'Unknown'}

CONTACT ENRICHMENT:
- Job Title: {enrichment.job_title or 'Not available'}
- Company Size: {enrichment.company_size or 'Not available'}
- Location: {enrichment.location or 'Not available'}

Score 0-100 based on:
- Transaction size (larger = higher opportunity)
- Insider seniority (C-suite/VP = higher)
- Transaction type (large sales = equity comp planning needs)
- Contact availability (enriched contacts = actionable)

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary of the opportunity>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""


def _sec_8k_prompt(event: Event, enrichment: EnrichmentData) -> str:
    raw = event.raw_data
    signal_type_map = {
        "executive_departure": "Executive Departure/Appointment",
        "restructuring": "Corporate Restructuring/Layoffs",
        "merger_acquisition": "Merger or Acquisition",
    }
    signal = signal_type_map.get(raw.get("signal_type", ""), "Corporate Event")

    return f"""You are a financial advisor lead scoring assistant. Score this corporate event for financial planning opportunity.

STRUCTURED DATA (verified from SEC filing):
- Company: {_sanitize(event.company_name)}
- Event Type: {signal}
- Person (if identified): {_sanitize(event.person_name) or 'Not extracted'}
- Affected Employees: {raw.get('affected_employees', 'Not specified')}
- Filing Date: {event.filed_at or 'Unknown'}
- Item Code: {raw.get('item_code', '')}

IMPORTANT: Only use the structured data above. If person name shows "Not extracted", note limited data in your brief. Do NOT infer or fabricate executive names.

CONTACT ENRICHMENT:
- Job Title: {enrichment.job_title or 'Not available'}
- Location: {enrichment.location or 'Not available'}

Score 0-100 based on:
- Event significance (CEO departure > VP departure)
- Financial planning opportunity (equity comp, severance, 401k rollover)
- Contact actionability (enriched = higher score)
- Reduce score if key data is missing (no person name, no employee count)

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""


def _warn_act_prompt(event: Event, enrichment: EnrichmentData) -> str:
    raw = event.raw_data

    return f"""You are a financial advisor lead scoring assistant. Score this workforce reduction event for financial planning opportunity.

STRUCTURED DATA:
- Company: {_sanitize(event.company_name)}
- Affected Employees: {raw.get('affected_employees', 'Not specified')}
- State: {raw.get('state', 'Unknown')}
- Filing Date: {event.filed_at or 'Unknown'}
- Signal Type: {raw.get('signal_type', 'workforce_reduction')}

CONTACT ENRICHMENT:
- Contact Name: {_sanitize(event.person_name) or 'Not available'}
- Job Title: {enrichment.job_title or 'Not available'}
- Location: {enrichment.location or 'Not available'}

Score 0-100 based on:
- Scale of layoff (more employees = more 401k rollovers to capture)
- Company profile (known company = employees likely have substantial 401k balances)
- Geographic match to advisor's market
- Timing (recent = more actionable)

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""


def _linkedin_prompt(event: Event, enrichment: EnrichmentData) -> str:
    raw = event.raw_data

    return f"""You are a financial advisor lead scoring assistant. Score this job change event for financial planning opportunity.

STRUCTURED DATA:
- Person: {_sanitize(event.person_name)}
- New Company: {_sanitize(event.company_name)}
- New Title: {_sanitize(raw.get('job_title', 'Unknown'))}
- LinkedIn: {raw.get('linkedin_url', 'Not available')}

CONTACT ENRICHMENT:
- Email: {enrichment.email or 'Not available'}
- Phone: {enrichment.phone or 'Not available'}
- Location: {enrichment.location or 'Not available'}

Score 0-100 based on:
- Seniority of new role (C-suite/VP moving = likely has old 401k to roll over)
- Company quality (well-funded companies = better compensation packages)
- Contact accessibility (email + LinkedIn = highly actionable)
- Career transition signals (new equity comp, relocation, benefits review)

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""
