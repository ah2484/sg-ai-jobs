"""Tests for validation logic."""

import json
from pathlib import Path
from unittest.mock import patch

from pipeline.validate import validate


class TestValidate:
    def _write_scores(self, scores: dict, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(scores, f)

    def test_valid_scores(self, tmp_path: Path):
        scores = {}
        # Create a distribution with good spread
        for i in range(50):
            scores[f"occ-{i}"] = {"exposure": i % 11, "rationale": f"Rationale for occ-{i}"}
        # Add sanity anchors
        scores["cleaner"] = {"exposure": 1, "rationale": "Manual labor"}
        scores["software-developer"] = {"exposure": 9, "rationale": "Digital work"}
        scores["nurse-enrolled"] = {"exposure": 4, "rationale": "Mixed work"}

        scored_dir = tmp_path / "data" / "scored"
        self._write_scores(scores, scored_dir / "scores_run1.json")

        with patch("pipeline.validate.SCORED_DIR", scored_dir):
            result = validate()
        assert result is True

    def test_narrow_distribution_fails(self, tmp_path: Path):
        # All scores the same
        scores = {f"occ-{i}": {"exposure": 5, "rationale": "Same"} for i in range(50)}
        scored_dir = tmp_path / "data" / "scored"
        self._write_scores(scores, scored_dir / "scores_run1.json")

        with patch("pipeline.validate.SCORED_DIR", scored_dir):
            result = validate()
        assert result is False

    def test_out_of_range_fails(self, tmp_path: Path):
        scores = {"occ-1": {"exposure": 15, "rationale": "Bad"}}
        scored_dir = tmp_path / "data" / "scored"
        self._write_scores(scores, scored_dir / "scores_run1.json")

        with patch("pipeline.validate.SCORED_DIR", scored_dir):
            result = validate()
        assert result is False
