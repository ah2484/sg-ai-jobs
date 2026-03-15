"""Validate scored data for quality and consistency."""

import json
import statistics
import sys
from pathlib import Path

SCORED_DIR = Path("data/scored")

# Sanity anchors: occupation slug patterns → expected score ranges
SANITY_ANCHORS = {
    "cleaner": (0, 2),
    "refuse-collector": (0, 2),
    "software": (7, 10),
    "data-entry": (8, 10),
    "nurse": (2, 5),
    "teacher": (3, 6),
    "security-guard": (1, 3),
}


def validate() -> bool:
    """Run all validation checks. Returns True if all pass."""
    errors: list[str] = []
    warnings: list[str] = []

    # Load scores (average of two runs)
    scores1_path = SCORED_DIR / "scores_run1.json"
    scores2_path = SCORED_DIR / "scores_run2.json"

    if not scores1_path.exists():
        print("ERROR: scores_run1.json not found. Run `make score` first.")
        return False

    with open(scores1_path) as f:
        scores1 = json.load(f)

    scores2 = None
    if scores2_path.exists():
        with open(scores2_path) as f:
            scores2 = json.load(f)

    # Check 1: All scores in 0-10 range
    print("Check 1: Score range (0-10)...")
    for slug, s in scores1.items():
        if not (0 <= s["exposure"] <= 10):
            errors.append(f"  {slug}: exposure={s['exposure']} out of range")
    if scores2:
        for slug, s in scores2.items():
            if not (0 <= s["exposure"] <= 10):
                errors.append(f"  {slug} (run2): exposure={s['exposure']} out of range")

    # Check 2: Distribution not degenerate
    print("Check 2: Distribution quality...")
    exposures = [s["exposure"] for s in scores1.values()]
    std = statistics.stdev(exposures) if len(exposures) > 1 else 0
    mean = statistics.mean(exposures) if exposures else 0
    print(f"  Mean: {mean:.2f}, Std: {std:.2f}, Min: {min(exposures)}, Max: {max(exposures)}")

    if std < 1.5:
        errors.append(f"  Distribution too narrow (std={std:.2f}, expected > 1.5)")

    # Check 3: Mean in reasonable range
    print("Check 3: Mean exposure range...")
    if not (3.5 <= mean <= 6.5):
        warnings.append(f"  Mean exposure {mean:.2f} outside expected range 3.5-6.5")

    # Check 4: Sanity anchors
    print("Check 4: Sanity anchors...")
    for pattern, (low, high) in SANITY_ANCHORS.items():
        matching = [(slug, s["exposure"]) for slug, s in scores1.items() if pattern in slug]
        for slug, exposure in matching:
            if not (low <= exposure <= high):
                warnings.append(f"  Anchor violation: {slug} scored {exposure}, expected {low}-{high}")

    # Check 5: No missing rationales
    print("Check 5: Rationale completeness...")
    missing_rationale = [slug for slug, s in scores1.items() if not s.get("rationale")]
    if missing_rationale:
        warnings.append(f"  {len(missing_rationale)} occupations missing rationale")

    # Check 6: Dual-run divergence
    if scores2:
        print("Check 6: Dual-run divergence...")
        divergent = 0
        for slug in scores1:
            if slug in scores2:
                diff = abs(scores1[slug]["exposure"] - scores2[slug]["exposure"])
                if diff >= 3:
                    divergent += 1
        if divergent > 0:
            warnings.append(f"  {divergent} occupations with run divergence >= 3 (review data/scored/divergence.json)")

    # Report
    print(f"\n{'=' * 40}")
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
    if not errors and not warnings:
        print("All checks passed.")

    passed = len(errors) == 0
    print(f"\nValidation {'PASSED' if passed else 'FAILED'}")
    return passed


def main() -> None:
    """Run validation and exit with appropriate code."""
    if not validate():
        sys.exit(1)


if __name__ == "__main__":
    main()
