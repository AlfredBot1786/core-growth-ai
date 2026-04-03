"""Claude AI lead scorer with per-lead error handling.

Scenario fix #9: each lead scored independently — one failure doesn't kill the batch.
"""

from __future__ import annotations

import json
import logging
import re

import anthropic

from src.models import CostTracker, Event, ScoredLead
from src.settings import settings

from .prompts import get_prompt_for_event

logger = logging.getLogger(__name__)


class ClaudeScorer:
    """Scores leads using Claude with per-lead error handling and cost tracking."""

    def __init__(self, cost_tracker: CostTracker | None = None):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.scoring_model
        self.cost_tracker = cost_tracker or CostTracker()

    def score_lead(self, event: Event) -> ScoredLead | None:
        """Score a single lead. Returns None on failure."""
        budget_error = self.cost_tracker.check_budget(settings.max_claude_calls_per_run)
        if budget_error:
            logger.warning(f"Cost circuit breaker triggered: {budget_error}")
            return None

        prompt = get_prompt_for_event(event)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            self.cost_tracker.claude_calls += 1
            usage = response.usage
            self.cost_tracker.claude_tokens += usage.input_tokens + usage.output_tokens

            text = response.content[0].text
            result = self._parse_response(text)

            if result is None:
                logger.warning(f"Failed to parse scoring response for {event.person_name}")
                return None

            score = result["score"]
            tier = ScoredLead.assign_tier(score)

            return ScoredLead(
                event=event,
                score=score,
                tier=tier,
                situation_brief=result.get("situation_brief", ""),
                talking_points=result.get("talking_points", []),
            )

        except anthropic.RateLimitError:
            logger.warning(f"Claude rate limited while scoring {event.person_name}")
            return None
        except anthropic.APIError as e:
            logger.error(f"Claude API error scoring {event.person_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scoring {event.person_name}: {e}")
            return None

    def score_batch(self, events: list[Event]) -> list[ScoredLead]:
        """Score a batch of events. Continues on per-lead failures."""
        scored = []
        failures = 0

        for event in events:
            result = self.score_lead(event)
            if result:
                scored.append(result)
            else:
                failures += 1

        if failures > 0:
            logger.info(
                f"Scoring complete: {len(scored)} scored, {failures} failed "
                f"(Claude calls: {self.cost_tracker.claude_calls}, "
                f"est cost: ${self.cost_tracker.estimated_claude_cost:.4f})"
            )

        return scored

    def _parse_response(self, text: str) -> dict | None:
        """Parse Claude's JSON response, handling various formats."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        json_match = re.search(r"\{[^}]*\"score\"[^}]*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None
