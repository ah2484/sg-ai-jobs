"""Tests for prompt enrichment."""

from pipeline.enrich import build_prompt
from pipeline.models import Occupation


class TestBuildPrompt:
    def test_with_tasks(self):
        occ = Occupation(
            title="Software Developer",
            slug="software-developer",
            ssoc_code="25121",
            category="professionals",
            category_label="Professionals",
            major_group=2,
            sector="ICT",
            pay_monthly=6800,
            pay_annual=81600,
            pay_p25=5200,
            pay_p75=9500,
            tasks=["Design software systems", "Write code", "Debug applications"],
            skills=["Python", "Java"],
            skillsfuture_funded=True,
        )
        prompt = build_prompt(occ)
        assert "Software Developer" in prompt
        assert "25121" in prompt
        assert "ICT" in prompt
        assert "SGD 6,800" in prompt
        assert "SGD 5,200" in prompt
        assert "Design software systems" in prompt
        assert "Python" in prompt

    def test_without_tasks(self):
        occ = Occupation(
            title="Cleaner",
            slug="cleaner",
            ssoc_code="91120",
            category="elementary",
            category_label="Elementary Occupations",
            major_group=9,
            pay_monthly=1500,
            pay_annual=18000,
        )
        prompt = build_prompt(occ)
        assert "Cleaner" in prompt
        assert "No task-level data" in prompt

    def test_without_wage_range(self):
        occ = Occupation(
            title="Bus Driver",
            slug="bus-driver",
            ssoc_code="83210",
            category="plant_machine",
            category_label="Plant & Machine Operators & Assemblers",
            major_group=8,
            pay_monthly=2800,
            pay_annual=33600,
        )
        prompt = build_prompt(occ)
        assert "SGD 2,800" in prompt
        assert "P25-P75" not in prompt
