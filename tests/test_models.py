"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from pipeline.models import MomOccupation, Occupation, ScoredOccupation, SkillsFutureRole


class TestMomOccupation:
    def test_valid(self):
        occ = MomOccupation(
            title="Software Developer",
            slug="software-developer",
            ssoc_code="25121",
            category="professionals",
            category_label="Professionals",
            major_group=2,
            pay_monthly=6800,
            pay_annual=81600,
        )
        assert occ.title == "Software Developer"
        assert occ.major_group == 2

    def test_major_group_range(self):
        with pytest.raises(ValidationError):
            MomOccupation(
                title="Test",
                slug="test",
                ssoc_code="99999",
                category="test",
                category_label="Test",
                major_group=0,
                pay_monthly=1000,
                pay_annual=12000,
            )

    def test_optional_percentiles(self):
        occ = MomOccupation(
            title="Cleaner",
            slug="cleaner",
            ssoc_code="91120",
            category="elementary",
            category_label="Elementary Occupations",
            major_group=9,
            pay_monthly=1500,
            pay_annual=18000,
        )
        assert occ.pay_p25 is None
        assert occ.pay_p75 is None


class TestSkillsFutureRole:
    def test_valid(self):
        role = SkillsFutureRole(
            title="Data Analyst",
            sector="ICT",
            tasks=["Analyze data", "Build dashboards"],
            skills=["Python", "SQL"],
        )
        assert len(role.tasks) == 2

    def test_empty_tasks(self):
        role = SkillsFutureRole(title="General Worker", sector="Manufacturing")
        assert role.tasks == []
        assert role.skills == []


class TestOccupation:
    def test_enriched(self):
        occ = Occupation(
            title="Nurse",
            slug="nurse",
            ssoc_code="32210",
            category="associate_professionals",
            category_label="Associate Professionals & Technicians",
            major_group=3,
            sector="Healthcare",
            pay_monthly=4200,
            pay_annual=50400,
            tasks=["Patient care", "Administer medication"],
            skills=["Clinical assessment"],
            skillsfuture_funded=True,
        )
        assert occ.skillsfuture_funded is True
        assert occ.sector == "Healthcare"
        assert occ.ep_spass_share is None


class TestScoredOccupation:
    def test_valid(self):
        occ = ScoredOccupation(
            title="Data Entry Clerk",
            slug="data-entry-clerk",
            ssoc_code="41320",
            category="clerical",
            category_label="Clerical Support Workers",
            major_group=4,
            pay_monthly=2500,
            pay_annual=30000,
            exposure=10,
            exposure_rationale="Fully routine digital tasks.",
        )
        assert occ.exposure == 10

    def test_exposure_range(self):
        with pytest.raises(ValidationError):
            ScoredOccupation(
                title="Test",
                slug="test",
                ssoc_code="11111",
                category="test",
                category_label="Test",
                major_group=1,
                pay_monthly=1000,
                pay_annual=12000,
                exposure=11,
            )
