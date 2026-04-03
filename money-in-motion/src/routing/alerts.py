"""Email alerting for T1 leads.

Scenario fix #6, #16: caps alerts per run to prevent alert fatigue.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.models import ScoredLead
from src.settings import settings

logger = logging.getLogger(__name__)


class EmailAlerter:
    """Sends HTML email alerts for T1 leads."""

    def __init__(self):
        self.alerts_sent = 0

    def send_t1_alerts(self, leads: list[ScoredLead]) -> int:
        """Send email alerts for T1 leads. Returns count sent.

        Scenario fix #16: caps at max_t1_alerts_per_run to prevent alert fatigue.
        """
        if not settings.has_email_alerts:
            logger.info("Email alerts disabled: SMTP not configured")
            return 0

        sent = 0
        for lead in leads:
            if sent >= settings.max_t1_alerts_per_run:
                logger.warning(
                    f"T1 alert cap reached ({settings.max_t1_alerts_per_run}). "
                    f"{len(leads) - sent} alerts suppressed. "
                    f"Increase MAX_T1_ALERTS_PER_RUN to send more."
                )
                break

            try:
                self._send_alert(lead)
                sent += 1
                self.alerts_sent += 1
            except Exception as e:
                logger.error(f"Failed to send alert for {lead.event.person_name}: {e}")
                continue

        return sent

    def _send_alert(self, lead: ScoredLead) -> None:
        """Send a single HTML email alert."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"[T1 Lead] {lead.event.person_name or lead.event.company_name} — "
            f"Score {lead.score}"
        )
        msg["From"] = settings.smtp_user
        msg["To"] = settings.alert_email

        html = self._build_html(lead)
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)

        logger.info(f"T1 alert sent for {lead.event.person_name} (score: {lead.score})")

    def _build_html(self, lead: ScoredLead) -> str:
        """Build HTML email body for a T1 lead alert."""
        talking_points_html = "".join(
            f"<li>{tp}</li>" for tp in lead.talking_points
        )

        correlation_note = ""
        if lead.event.raw_data.get("correlation_note"):
            correlation_note = f"""
            <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0;">
                <strong>Cross-signal:</strong> {lead.event.raw_data['correlation_note']}
            </div>
            """

        enrichment_section = ""
        if lead.enrichment.email:
            enrichment_section = f"""
            <h3>Contact Info</h3>
            <p>
                Email: {lead.enrichment.email}<br>
                Phone: {lead.enrichment.phone or 'N/A'}<br>
                LinkedIn: {lead.enrichment.linkedin_url or 'N/A'}<br>
                Title: {lead.enrichment.job_title or 'N/A'}
            </p>
            """

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">Money in Motion Alert</h1>
                <p style="margin: 5px 0 0; opacity: 0.8;">Score: {lead.score}/100 | Tier: T1</p>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
                <h2>{lead.event.person_name or 'Unknown'} @ {lead.event.company_name}</h2>
                <p><strong>Event:</strong> {lead.event.event_type.value}</p>
                <p><strong>Filed:</strong> {lead.event.filed_at or 'Unknown'}</p>

                {correlation_note}

                <h3>Situation Brief</h3>
                <p>{lead.situation_brief}</p>

                <h3>Talking Points</h3>
                <ul>{talking_points_html}</ul>

                {enrichment_section}

                <p><a href="{lead.event.url}" style="color: #0066cc;">View SEC Filing</a></p>
            </div>
        </body>
        </html>
        """
