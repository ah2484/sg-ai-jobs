"""Build final site/data.json from enriched occupations + scores."""

import json
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
SCORED_DIR = Path("data/scored")
SITE_DIR = Path("site")


def main() -> None:
    """Merge enriched occupations with averaged scores into site/data.json."""
    enriched_path = PROCESSED_DIR / "occupations_enriched.json"
    scores1_path = SCORED_DIR / "scores_run1.json"
    scores2_path = SCORED_DIR / "scores_run2.json"

    if not enriched_path.exists():
        raise FileNotFoundError(f"{enriched_path} not found. Run `make ingest` first.")
    if not scores1_path.exists():
        raise FileNotFoundError(f"{scores1_path} not found. Run `make score` first.")

    with open(enriched_path) as f:
        occupations = json.load(f)
    with open(scores1_path) as f:
        scores1 = json.load(f)

    scores2 = None
    if scores2_path.exists():
        with open(scores2_path) as f:
            scores2 = json.load(f)

    # Merge scores into occupations
    output = []
    for occ in occupations:
        slug = occ["slug"]
        s1 = scores1.get(slug, {"exposure": 5, "rationale": "Not scored"})

        if scores2 and slug in scores2:
            s2 = scores2[slug]
            exposure = round((s1["exposure"] + s2["exposure"]) / 2)
            rationale = s1["rationale"]  # Use run1 rationale
        else:
            exposure = s1["exposure"]
            rationale = s1["rationale"]

        output.append(
            {
                "title": occ["title"],
                "slug": slug,
                "ssoc_code": occ["ssoc_code"],
                "category": occ["category"],
                "category_label": occ["category_label"],
                "major_group": occ["major_group"],
                "sector": occ.get("sector"),
                "pay_monthly": occ["pay_monthly"],
                "pay_annual": occ["pay_annual"],
                "pay_p25": occ.get("pay_p25"),
                "pay_p75": occ.get("pay_p75"),
                "exposure": exposure,
                "exposure_rationale": rationale,
                "tasks": occ.get("tasks", []),
                "skills": occ.get("skills", []),
                "skillsfuture_funded": occ.get("skillsfuture_funded", False),
                "ep_spass_share": occ.get("ep_spass_share"),
            }
        )

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SITE_DIR / "data.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Built {len(output)} occupations → {output_path}")

    # Build methodology.json
    methodology = {
        "scoring_model": "claude-haiku-4-5-20251001",
        "temperature": 0.2,
        "scoring_prompt": "See pipeline/score.py SYSTEM_PROMPT",
        "data_sources": [
            "MOM Occupational Wage Survey 2024",
            "SkillsFuture Skills Framework Database",
        ],
        "dual_run": scores2 is not None,
        "total_occupations": len(output),
    }

    # Add divergence info if available
    divergence_path = SCORED_DIR / "divergence.json"
    if divergence_path.exists():
        with open(divergence_path) as f:
            methodology["divergent_occupations"] = json.load(f)

    methodology_path = SITE_DIR / "methodology.json"
    with open(methodology_path, "w") as f:
        json.dump(methodology, f, indent=2)

    print(f"Built methodology → {methodology_path}")

    # Distribution summary
    exposures = [o["exposure"] for o in output]
    from collections import Counter

    dist = Counter(exposures)
    print("\nExposure distribution:")
    for score in range(11):
        count = dist.get(score, 0)
        bar = "█" * count
        print(f"  {score:2d}: {bar} ({count})")


if __name__ == "__main__":
    main()
