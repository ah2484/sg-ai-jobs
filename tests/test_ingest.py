"""Tests for ingestion pipeline."""

from pipeline.ingest import match_skillsfuture_to_mom, slugify
from pipeline.models import MomOccupation, SkillsFutureRole


class TestSlugify:
    def test_simple(self):
        assert slugify("Software Developer") == "software-developer"

    def test_special_chars(self):
        assert slugify("Nurse (Registered)") == "nurse-registered"

    def test_multiple_spaces(self):
        assert slugify("Data  Entry   Clerk") == "data-entry-clerk"

    def test_trailing_whitespace(self):
        assert slugify("  Cleaner  ") == "cleaner"

    def test_ampersand(self):
        assert slugify("Sales & Marketing Manager") == "sales-marketing-manager"


class TestFuzzyMatching:
    def test_exact_match(self):
        mom = [
            MomOccupation(
                title="Software Developer",
                slug="software-developer",
                ssoc_code="25121",
                category="professionals",
                category_label="Professionals",
                major_group=2,
                pay_monthly=6800,
                pay_annual=81600,
            )
        ]
        sf = [
            SkillsFutureRole(
                title="Software Developer",
                sector="ICT",
                tasks=["Design systems", "Write code"],
                skills=["Python", "Java"],
            )
        ]
        result = match_skillsfuture_to_mom(mom, sf)
        assert len(result) == 1
        assert result[0].tasks == ["Design systems", "Write code"]
        assert result[0].skillsfuture_funded is True

    def test_fuzzy_match(self):
        mom = [
            MomOccupation(
                title="Software Engineer",
                slug="software-engineer",
                ssoc_code="25121",
                category="professionals",
                category_label="Professionals",
                major_group=2,
                pay_monthly=7000,
                pay_annual=84000,
            )
        ]
        sf = [
            SkillsFutureRole(
                title="Software Developer / Engineer",
                sector="ICT",
                tasks=["Build software"],
                skills=["JavaScript"],
            )
        ]
        result = match_skillsfuture_to_mom(mom, sf)
        assert result[0].skillsfuture_funded is True
        assert result[0].tasks == ["Build software"]

    def test_no_match(self):
        mom = [
            MomOccupation(
                title="Refuse Collector",
                slug="refuse-collector",
                ssoc_code="96130",
                category="elementary",
                category_label="Elementary Occupations",
                major_group=9,
                pay_monthly=1800,
                pay_annual=21600,
            )
        ]
        sf = [
            SkillsFutureRole(
                title="Software Developer",
                sector="ICT",
                tasks=["Write code"],
                skills=["Python"],
            )
        ]
        result = match_skillsfuture_to_mom(mom, sf)
        assert result[0].skillsfuture_funded is False
        assert result[0].tasks == []

    def test_empty_skillsfuture(self):
        mom = [
            MomOccupation(
                title="Cleaner",
                slug="cleaner",
                ssoc_code="91120",
                category="elementary",
                category_label="Elementary Occupations",
                major_group=9,
                pay_monthly=1500,
                pay_annual=18000,
            )
        ]
        result = match_skillsfuture_to_mom(mom, [])
        assert len(result) == 1
        assert result[0].skillsfuture_funded is False
