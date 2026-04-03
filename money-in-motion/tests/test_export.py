"""Tests for lead export."""

import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone

from src.export import LeadExporter
from src.models import Event, EventType, ScoredLead, Tier


class TestLeadExporter:
    def _make_lead(self, score: int, name: str, company: str) -> ScoredLead:
        return ScoredLead(
            event=Event(
                event_type=EventType.SEC_FORM4,
                person_name=name,
                company_name=company,
                filed_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
                url="https://sec.gov/filing/123",
            ),
            score=score,
            tier=ScoredLead.assign_tier(score),
            situation_brief=f"{name} sold stock",
            talking_points=["Point 1", "Point 2"],
        )

    def test_csv_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = LeadExporter(output_dir=tmpdir)
            leads = [
                self._make_lead(85, "Alice CEO", "TechCorp"),
                self._make_lead(55, "Bob VP", "FinCo"),
            ]
            path = exporter.export_csv(leads, "test-run-123")
            assert path.exists()
            content = path.read_text()
            assert "Alice CEO" in content
            assert "Bob VP" in content
            assert "TechCorp" in content
            # Should be sorted by score (highest first)
            assert content.index("Alice CEO") < content.index("Bob VP")

    def test_json_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = LeadExporter(output_dir=tmpdir)
            leads = [
                self._make_lead(90, "Jane CTO", "BigBank"),
            ]
            path = exporter.export_json(leads, "test-run-456")
            assert path.exists()
            data = json.loads(path.read_text())
            assert len(data) == 1
            assert data[0]["person_name"] == "Jane CTO"
            assert data[0]["score"] == 90
            assert data[0]["tier"] == "T1"

    def test_empty_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = LeadExporter(output_dir=tmpdir)
            path = exporter.export_csv([], "empty-run")
            content = path.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 1  # header only
