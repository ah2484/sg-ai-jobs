"""Parse MOM wage data and SkillsFuture task-level data from Excel files."""

import json
import re
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

from pipeline.models import MomOccupation, Occupation, SkillsFutureRole

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# SSOC major group labels
MAJOR_GROUP_LABELS = {
    1: ("managers", "Managers"),
    2: ("professionals", "Professionals"),
    3: ("associate_professionals", "Associate Professionals & Technicians"),
    4: ("clerical", "Clerical Support Workers"),
    5: ("service_sales", "Service & Sales Workers"),
    6: ("agricultural", "Skilled Agricultural & Fishery Workers"),
    7: ("craft", "Craft & Related Trades Workers"),
    8: ("plant_machine", "Plant & Machine Operators & Assemblers"),
    9: ("elementary", "Elementary Occupations"),
}


def slugify(title: str) -> str:
    """Convert occupation title to URL-safe slug."""
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    return s.strip("-")


def parse_mom_wages(filepath: Path | None = None) -> list[MomOccupation]:
    """Parse MOM Occupational Wage Survey Excel (Table T4).

    Expected columns: SSOC code, occupation title, gross wage percentiles.
    """
    if filepath is None:
        candidates = list(RAW_DIR.glob("*wage*T4*.*")) + list(RAW_DIR.glob("*MOM*.*")) + list(RAW_DIR.glob("*mom*.*"))
        if not candidates:
            raise FileNotFoundError(
                f"No MOM wage file found in {RAW_DIR}/. "
                "Download from MOM Occupational Wage Survey and place in data/raw/."
            )
        filepath = candidates[0]

    print(f"Parsing MOM wages from: {filepath}")
    df = pd.read_excel(filepath, sheet_name=None)

    # Find the right sheet — look for one with "SSOC" or "occupation" in headers
    target_sheet = None
    target_df = None
    for sheet_name, sheet_df in df.items():
        # Check first few rows for SSOC-like content
        header_text = " ".join(str(v) for v in sheet_df.iloc[:5].values.flatten() if pd.notna(v)).lower()
        if "ssoc" in header_text or "occupation" in header_text:
            target_sheet = sheet_name
            target_df = sheet_df
            break

    if target_df is None:
        # Fall back to largest sheet
        target_sheet = max(df.keys(), key=lambda k: len(df[k]))
        target_df = df[target_sheet]

    print(f"  Using sheet: {target_sheet} ({len(target_df)} rows)")

    # Find header row (row containing "SSOC" or "Occupation")
    header_row = 0
    for i, row in target_df.iterrows():
        row_text = " ".join(str(v) for v in row.values if pd.notna(v)).lower()
        if "ssoc" in row_text or "occupation" in row_text:
            header_row = i
            break

    # Re-read with correct header
    target_df.columns = target_df.iloc[header_row]
    target_df = target_df.iloc[header_row + 1 :].reset_index(drop=True)

    # Normalize column names
    col_map = {}
    for col in target_df.columns:
        col_lower = str(col).lower().strip()
        if "ssoc" in col_lower and "code" in col_lower:
            col_map[col] = "ssoc_code"
        elif "occupation" in col_lower or "title" in col_lower:
            col_map[col] = "title"
        elif "median" in col_lower or "50th" in col_lower:
            col_map[col] = "median"
        elif "25th" in col_lower:
            col_map[col] = "p25"
        elif "75th" in col_lower:
            col_map[col] = "p75"

    target_df = target_df.rename(columns=col_map)

    occupations = []
    for _, row in target_df.iterrows():
        ssoc = str(row.get("ssoc_code", "")).strip()
        title = str(row.get("title", "")).strip()
        median = row.get("median")

        if not ssoc or not title or title.lower() == "nan" or ssoc.lower() == "nan":
            continue
        if pd.isna(median):
            continue

        # Clean SSOC code
        ssoc = re.sub(r"[^0-9]", "", ssoc)
        if not ssoc:
            continue

        major_group = int(ssoc[0]) if ssoc else 0
        if major_group < 1 or major_group > 9:
            continue

        category, category_label = MAJOR_GROUP_LABELS.get(major_group, ("other", "Other"))

        monthly = int(float(median))
        p25 = int(float(row["p25"])) if "p25" in row and pd.notna(row.get("p25")) else None
        p75 = int(float(row["p75"])) if "p75" in row and pd.notna(row.get("p75")) else None

        occupations.append(
            MomOccupation(
                title=title,
                slug=slugify(title),
                ssoc_code=ssoc,
                category=category,
                category_label=category_label,
                major_group=major_group,
                pay_monthly=monthly,
                pay_annual=monthly * 12,
                pay_p25=p25,
                pay_p75=p75,
            )
        )

    print(f"  Parsed {len(occupations)} occupations")
    return occupations


def parse_skillsfuture(filepath: Path | None = None) -> list[SkillsFutureRole]:
    """Parse SkillsFuture Skills Framework database.

    Expected structure: multi-sheet Excel with sector tabs, each containing
    roles with key tasks and technical skills.
    """
    if filepath is None:
        candidates = list(RAW_DIR.glob("*skillsfuture*.*")) + list(RAW_DIR.glob("*sfw*.*"))
        if not candidates:
            raise FileNotFoundError(
                f"No SkillsFuture file found in {RAW_DIR}/. "
                "Download template_sfw_database---combined.xlsx from SkillsFuture portal."
            )
        filepath = candidates[0]

    print(f"Parsing SkillsFuture from: {filepath}")
    df = pd.read_excel(filepath, sheet_name=None)
    print(f"  Found {len(df)} sheets")

    roles: list[SkillsFutureRole] = []
    for sheet_name, sheet_df in df.items():
        if sheet_name.lower() in ("readme", "instructions", "legend", "contents"):
            continue

        sector = sheet_name.strip()

        # Try to identify role title, tasks, and skills columns
        # SkillsFuture format varies — try common patterns
        cols = [str(c).lower().strip() for c in sheet_df.columns]

        title_col = None
        task_col = None
        skill_col = None

        for i, c in enumerate(cols):
            if "job" in c or "role" in c or "title" in c or "occupation" in c:
                title_col = sheet_df.columns[i]
            if "task" in c or "key task" in c or "critical work" in c:
                task_col = sheet_df.columns[i]
            if "skill" in c or "competenc" in c or "technical" in c:
                skill_col = sheet_df.columns[i]

        if title_col is None:
            # Try first column as title
            title_col = sheet_df.columns[0]

        for _, row in sheet_df.iterrows():
            title = str(row.get(title_col, "")).strip()
            if not title or title.lower() == "nan":
                continue

            tasks = []
            if task_col is not None:
                task_val = str(row.get(task_col, ""))
                if task_val and task_val.lower() != "nan":
                    # Split on newlines, bullets, or semicolons
                    tasks = [t.strip().lstrip("•-·").strip() for t in re.split(r"[\n;•·]", task_val) if t.strip()]

            skills = []
            if skill_col is not None:
                skill_val = str(row.get(skill_col, ""))
                if skill_val and skill_val.lower() != "nan":
                    skills = [s.strip().lstrip("•-·").strip() for s in re.split(r"[\n;•·]", skill_val) if s.strip()]

            roles.append(
                SkillsFutureRole(
                    title=title,
                    sector=sector,
                    tasks=tasks,
                    skills=skills,
                )
            )

    print(f"  Parsed {len(roles)} roles across sectors")
    return roles


def match_skillsfuture_to_mom(
    mom_occupations: list[MomOccupation],
    sf_roles: list[SkillsFutureRole],
    threshold: int = 70,
) -> list[Occupation]:
    """Fuzzy-match SkillsFuture roles to MOM occupations by title."""
    sf_titles = [r.title for r in sf_roles]
    sf_by_title = {r.title: r for r in sf_roles}

    matched = 0
    occupations: list[Occupation] = []

    for mom in mom_occupations:
        best_match = process.extractOne(mom.title, sf_titles, scorer=fuzz.token_sort_ratio)

        sf_role = None
        if best_match and best_match[1] >= threshold:
            sf_role = sf_by_title[best_match[0]]
            matched += 1

        occupations.append(
            Occupation(
                title=mom.title,
                slug=mom.slug,
                ssoc_code=mom.ssoc_code,
                category=mom.category,
                category_label=mom.category_label,
                major_group=mom.major_group,
                sector=sf_role.sector if sf_role else None,
                pay_monthly=mom.pay_monthly,
                pay_annual=mom.pay_annual,
                pay_p25=mom.pay_p25,
                pay_p75=mom.pay_p75,
                tasks=sf_role.tasks if sf_role else [],
                skills=sf_role.skills if sf_role else [],
                skillsfuture_funded=sf_role is not None,
            )
        )

    print(f"  Matched {matched}/{len(mom_occupations)} occupations to SkillsFuture roles")
    return occupations


def save_json(data: list, filepath: Path) -> None:
    """Save list of Pydantic models to JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump([item.model_dump() if hasattr(item, "model_dump") else item for item in data], f, indent=2)
    print(f"  Saved {len(data)} records to {filepath}")


def main() -> None:
    """Run the ingestion pipeline."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Parse MOM wages
    print("\n=== Step 1: Parsing MOM wages ===")
    mom_occupations = parse_mom_wages()
    save_json(mom_occupations, PROCESSED_DIR / "mom_occupations.json")

    # Step 2: Parse SkillsFuture
    print("\n=== Step 2: Parsing SkillsFuture ===")
    try:
        sf_roles = parse_skillsfuture()
        save_json(sf_roles, PROCESSED_DIR / "skillsfuture_roles.json")
    except FileNotFoundError as e:
        print(f"  Warning: {e}")
        print("  Proceeding without SkillsFuture data (title-only scoring)")
        sf_roles = []

    # Step 3: Merge
    print("\n=== Step 3: Merging MOM + SkillsFuture ===")
    occupations = match_skillsfuture_to_mom(mom_occupations, sf_roles)
    save_json(occupations, PROCESSED_DIR / "occupations_enriched.json")

    print(f"\n✓ Ingestion complete: {len(occupations)} occupations")


if __name__ == "__main__":
    main()
