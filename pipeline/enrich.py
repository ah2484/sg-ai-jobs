"""Build LLM prompt context for each occupation."""

import json
from pathlib import Path

from pipeline.models import Occupation

PROCESSED_DIR = Path("data/processed")


def build_prompt(occ: Occupation) -> str:
    """Generate structured prompt for a single occupation."""
    lines = [
        f"## {occ.title}",
        f"- SSOC Code: {occ.ssoc_code}",
        f"- Major Group: {occ.major_group} ({occ.category_label})",
    ]

    if occ.sector:
        lines.append(f"- Sector: {occ.sector}")

    lines.append(f"- Median Monthly Wage: SGD {occ.pay_monthly:,}")
    if occ.pay_p25 and occ.pay_p75:
        lines.append(f"- Wage Range (P25-P75): SGD {occ.pay_p25:,} – SGD {occ.pay_p75:,}")

    if occ.tasks:
        lines.append("\n### Key Tasks (from SkillsFuture Skills Framework)")
        for task in occ.tasks:
            lines.append(f"- {task}")

    if occ.skills:
        lines.append("\n### Technical Skills")
        for skill in occ.skills:
            lines.append(f"- {skill}")

    if not occ.tasks and not occ.skills:
        lines.append("\n(No task-level data available — score based on occupation title and typical duties.)")

    return "\n".join(lines)


def main() -> None:
    """Generate prompts for all occupations."""
    enriched_path = PROCESSED_DIR / "occupations_enriched.json"
    if not enriched_path.exists():
        raise FileNotFoundError(f"{enriched_path} not found. Run `make ingest` first.")

    with open(enriched_path) as f:
        data = json.load(f)

    occupations = [Occupation(**d) for d in data]
    prompts = {occ.slug: build_prompt(occ) for occ in occupations}

    output_path = PROCESSED_DIR / "prompts.json"
    with open(output_path, "w") as f:
        json.dump(prompts, f, indent=2)

    print(f"Generated {len(prompts)} prompts → {output_path}")

    # Spot-check
    sample_slugs = list(prompts.keys())[:5]
    print("\nSample prompts:")
    for slug in sample_slugs:
        print(f"\n--- {slug} ---")
        print(prompts[slug][:300])


if __name__ == "__main__":
    main()
