"""Scoring prompt templates — one per event type.

Prompts use structured data from SEC filings only. No third-party enrichment.
Contact lookup happens AFTER scoring, only for T1/T2 leads.

Scenario fix #23: sanitizes input to prevent prompt injection via filing text.
"""

from __future__ import annotations

from src.models import Event, EventType


def get_prompt_for_event(event: Event) -> str:
    """Return the appropriate scoring prompt for the event type."""
    builders = {
        EventType.SEC_FORM4: _form4_prompt,
        EventType.SEC_8K: _sec_8k_prompt,
        EventType.WARN_ACT: _warn_act_prompt,
        EventType.LINKEDIN: _linkedin_prompt,
    }
    builder = builders.get(event.event_type, _form4_prompt)
    return builder(event)


def _sanitize(text: str) -> str:
    """Sanitize text to prevent prompt injection."""
    if not text:
        return ""
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
    return text[:500]


def _form4_prompt(event: Event) -> str:
    raw = event.raw_data
    txn_type_map = {"S": "Sale", "P": "Purchase", "A": "Grant/Award", "M": "Exercise"}
    txn_type = txn_type_map.get(raw.get("transaction_type", ""), raw.get("transaction_type", "Unknown"))

    return f"""You are a financial advisor lead scoring assistant. Score this insider transaction for financial planning opportunity.

SEC FORM 4 DATA:
- Person: {_sanitize(event.person_name)}
- Company: {_sanitize(event.company_name)}
- Transaction Type: {txn_type}
- Shares: {raw.get('shares', 'Unknown')}
- Price Per Share: ${raw.get('price_per_share', 'Unknown')}
- Total Value: ${raw.get('total_value', 'Unknown')}
- Insider Title: {_sanitize(raw.get('insider_title', 'Unknown'))}
- Filing Date: {event.filed_at or 'Unknown'}

Score 0-100 based on:
- Transaction size (larger = higher opportunity for equity comp planning, tax optimization)
- Insider seniority (C-suite/VP = higher net worth, more complex planning needs)
- Transaction type (large sales = liquidity event, purchases = conviction signal)
- Timing (recent = more actionable)

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary of the opportunity for a financial advisor>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""


def _sec_8k_prompt(event: Event) -> str:
    raw = event.raw_data
    signal_type_map = {
        "executive_departure": "Executive Departure/Appointment",
        "restructuring": "Corporate Restructuring/Layoffs",
        "merger_acquisition": "Merger or Acquisition",
    }
    signal = signal_type_map.get(raw.get("signal_type", ""), "Corporate Event")

    return f"""You are a financial advisor lead scoring assistant. Score this corporate event for financial planning opportunity.

SEC 8-K DATA:
- Company: {_sanitize(event.company_name)}
- Event Type: {signal}
- Person (if identified): {_sanitize(event.person_name) or 'Not extracted'}
- Affected Employees: {raw.get('affected_employees', 'Not specified')}
- Filing Date: {event.filed_at or 'Unknown'}
- Item Code: {raw.get('item_code', '')}

IMPORTANT: Only use the data above. If person name shows "Not extracted", note limited data. Do NOT fabricate names or details.

Score 0-100 based on:
- Event significance (CEO departure > VP departure, large M&A > small)
- Financial planning opportunity (equity comp, severance, 401k rollover, estate planning)
- Scale (more affected employees = more potential clients)
- Reduce score if critical data is missing

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""


def _warn_act_prompt(event: Event) -> str:
    raw = event.raw_data

    return f"""You are a financial advisor lead scoring assistant. Score this workforce reduction for financial planning opportunity.

WARN ACT DATA:
- Company: {_sanitize(event.company_name)}
- Affected Employees: {raw.get('affected_employees', 'Not specified')}
- State: {raw.get('state', 'Unknown')}
- Filing Date: {event.filed_at or 'Unknown'}

Score 0-100 based on:
- Scale of layoff (more employees = more 401k rollovers, severance planning opportunities)
- Company profile (well-known company = employees likely have substantial retirement assets)
- Timing (recent = employees actively making financial decisions NOW)

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""


def _linkedin_prompt(event: Event) -> str:
    raw = event.raw_data

    return f"""You are a financial advisor lead scoring assistant. Score this job change for financial planning opportunity.

LINKEDIN DATA:
- Person: {_sanitize(event.person_name)}
- New Company: {_sanitize(event.company_name)}
- New Title: {_sanitize(raw.get('job_title', 'Unknown'))}

Score 0-100 based on:
- Seniority of new role (C-suite/VP = likely has old 401k to roll over, stock options to exercise)
- Career transition signals (new equity comp, relocation, benefits review needed)
- Company quality (well-funded companies = better compensation packages to plan around)

Respond in this exact JSON format:
{{"score": <int 0-100>, "situation_brief": "<2-3 sentence summary>", "talking_points": ["<point 1>", "<point 2>", "<point 3>"]}}"""
