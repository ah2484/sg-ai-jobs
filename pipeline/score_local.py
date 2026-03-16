"""Score occupations locally using keyword-based heuristics + task analysis.

This is a deterministic scoring alternative to the Batch API scorer.
It analyzes occupation titles, SkillsFuture tasks, and skills to estimate
AI exposure on the same 0-10 scale.
"""

import json
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
SCORED_DIR = Path("data/scored")

# Keywords that strongly indicate HIGH AI exposure (digital/cognitive/routine)
HIGH_EXPOSURE_TITLE = [
    "data entry",
    "bookkeeper",
    "bookkeeping",
    "transcri",
    "translator",
    "interpreter",
    "copywriter",
    "proofreader",
    "typist",
    "clerk",
    "filing",
    "record",
    "telemarket",
    "telesales",
    "call centre",
    "customer service officer",
]
HIGH_EXPOSURE_TASKS = [
    "data entry",
    "filing",
    "transcri",
    "translate",
    "proofread",
    "type ",
    "sort document",
    "update record",
    "maintain record",
    "key in",
    "process invoice",
    "process claim",
    "check document",
    "compile report",
    "prepare report",
    "generate report",
    "reconcil",
    "verify data",
    "data validation",
]

# Keywords indicating VERY HIGH exposure (mostly automatable digital work)
VERY_HIGH_TITLE = [
    "data entry",
    "software",
    "developer",
    "programmer",
    "coder",
    "web designer",
    "graphic design",
    "visual design",
    "ui design",
    "ux design",
    "content writ",
    "technical writ",
    "report writ",
    "data analyst",
    "data scien",
    "statistician",
    "financial analyst",
    "investment analyst",
    "research analyst",
    "paralegal",
    "legal assistant",
]
VERY_HIGH_TASKS = [
    "develop software",
    "write code",
    "programming",
    "debug",
    "design layout",
    "create visual",
    "design graphic",
    "analyse data",
    "analyze data",
    "data analy",
    "statistical analy",
    "draft document",
    "draft report",
    "draft contract",
    "draft letter",
    "financial model",
    "forecast",
    "prepare presentation",
]

# Keywords indicating MEDIUM exposure (mixed human + digital)
MEDIUM_TITLE = [
    "accountant",
    "auditor",
    "tax",
    "compliance",
    "human resource",
    "hr ",
    "recruitment",
    "marketing",
    "sales manager",
    "property agent",
    "project manager",
    "operations manager",
    "teacher",
    "lecturer",
    "tutor",
    "instructor",
    "engineer",
    "architect",
    "surveyor",
    "pharmacist",
    "dietitian",
    "therapist",
    "social worker",
    "counsellor",
]
MEDIUM_TASKS = [
    "manage project",
    "coordinate",
    "schedule",
    "counsel",
    "advise client",
    "consult",
    "teach",
    "train ",
    "coach",
    "mentor",
    "assess ",
    "evaluat",
    "review ",
    "plan ",
    "develop strategy",
    "implement policy",
    "supervise",
    "oversee",
]

# Keywords indicating LOW exposure (physical/interpersonal)
LOW_EXPOSURE_TITLE = [
    "nurse ",
    "nurses",
    "nursing",
    "midwi",
    "doctor",
    "physician",
    "surgeon",
    "dentist",
    "police",
    "firefight",
    "paramedic",
    "ambulance",
    "chef",
    "cook",
    "baker",
    "butcher",
    "driver",
    "pilot",
    "captain",
    "mechanic",
    "electrician",
    "plumber",
    "welder",
    "carpenter",
    "mason",
    "painter",
    "hairdress",
    "barber",
    "beautician",
    "security guard",
    "bouncer",
    "waiter",
    "bartender",
    "barista",
    "childcare",
    "nanny",
]
LOW_EXPOSURE_TASKS = [
    "physical",
    "manual",
    "lift ",
    "carry ",
    "operate machine",
    "operate equipment",
    "operate vehicle",
    "patrol",
    "guard",
    "inspect site",
    "clean ",
    "wash ",
    "sweep",
    "serve food",
    "prepare food",
    "cook ",
    "cut hair",
    "style hair",
    "administer medication",
    "patient care",
    "wound care",
    "drive ",
    "steer",
    "navigate",
    "install ",
    "repair ",
    "maintain equipment",
    "fix ",
    "assemble",
    "fabricat",
    "weld",
]

# Keywords indicating VERY LOW exposure (purely physical/manual)
VERY_LOW_TITLE = [
    "cleaner",
    "janitor",
    "refuse collector",
    "garbage",
    "labourer",
    "laborer",
    "general worker",
    "sweeper",
    "dishwash",
    "mover",
    "porter",
]


def _keyword_score(text: str, keywords: list[str]) -> int:
    """Count how many keywords appear in text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def score_occupation(occ: dict) -> tuple[int, str]:
    """Score a single occupation for AI exposure (0-10)."""
    title = occ["title"].lower()
    tasks_text = " ".join(occ.get("tasks", [])).lower()
    skills_text = " ".join(occ.get("skills", [])).lower()
    has_tasks = len(occ.get("tasks", [])) > 0

    # Start with a baseline by major group
    mg = occ["major_group"]
    baselines = {1: 6, 2: 6, 3: 5, 4: 7, 5: 3, 6: 1, 7: 2, 8: 2, 9: 1}
    score = baselines.get(mg, 5)

    # Adjust based on title keywords (check most specific first)
    if _keyword_score(title, VERY_HIGH_TITLE) > 0:
        score = max(score, 8)
    elif _keyword_score(title, VERY_LOW_TITLE) > 0:
        score = 1
    elif _keyword_score(title, LOW_EXPOSURE_TITLE) > 0:
        score = min(score, 3)
        score -= 1
    elif _keyword_score(title, HIGH_EXPOSURE_TITLE) > 0:
        score = max(score, 7)
    elif _keyword_score(title, MEDIUM_TITLE) > 0:
        score = max(min(score, 6), 4)

    # Fine-tune with task analysis if available
    if has_tasks:
        low_task_hits = _keyword_score(tasks_text, LOW_EXPOSURE_TASKS)
        med_task_hits = _keyword_score(tasks_text, MEDIUM_TASKS)
        high_task_hits = _keyword_score(tasks_text, HIGH_EXPOSURE_TASKS)
        vhigh_task_hits = _keyword_score(tasks_text, VERY_HIGH_TASKS)

        # Weight task evidence
        task_signal = vhigh_task_hits * 2 + high_task_hits * 1.5 + med_task_hits * 0.5 - low_task_hits * 1.5
        if task_signal > 4:
            score = min(score + 2, 10)
        elif task_signal > 2:
            score = min(score + 1, 10)
        elif task_signal < -3:
            score = max(score - 2, 0)
        elif task_signal < -1:
            score = max(score - 1, 0)

    # Skill-based adjustments
    digital_skills = _keyword_score(
        skills_text,
        [
            "programming",
            "coding",
            "software",
            "data analy",
            "machine learning",
            "artificial intelligence",
            "cloud",
            "cyber",
            "digital",
            "automation",
            "robotic process",
            "natural language",
        ],
    )
    physical_skills = _keyword_score(
        skills_text,
        [
            "patient care",
            "clinical",
            "surgical",
            "emergency",
            "electrical",
            "mechanical",
            "plumbing",
            "welding",
            "food preparation",
            "food safety",
            "housekeep",
            "fire safety",
            "first aid",
            "rescue",
        ],
    )

    if digital_skills >= 3:
        score = min(score + 1, 10)
    if physical_skills >= 2:
        score = max(score - 1, 0)

    # Clamp
    score = max(0, min(10, score))

    # Generate rationale
    rationale = _generate_rationale(occ, score, has_tasks)

    return score, rationale


def _generate_rationale(occ: dict, score: int, has_tasks: bool) -> str:
    """Generate a brief rationale for the score."""
    title = occ["title"]
    tasks = occ.get("tasks", [])

    if score <= 1:
        return (
            f"{title} involves primarily physical, manual work that requires human presence "
            f"and dexterity. AI has minimal impact on core job functions."
        )
    elif score <= 3:
        if has_tasks:
            physical_kws = [
                "physical",
                "manual",
                "operate",
                "drive",
                "patrol",
                "clean",
                "serve",
                "prepare food",
                "install",
                "repair",
                "patient",
                "care",
            ]
            physical_tasks = [t for t in tasks[:3] if any(kw in t.lower() for kw in physical_kws)]
            if physical_tasks:
                return (
                    f"{title} involves substantial physical/interpersonal work. "
                    f"Tasks like '{physical_tasks[0][:60]}' require human presence. "
                    f"Some administrative tasks may be AI-assisted but core duties remain human."
                )
        return (
            f"{title} requires significant physical presence, interpersonal interaction, "
            f"or hands-on skills that AI cannot readily replicate."
        )
    elif score <= 5:
        if has_tasks:
            return (
                f"{title} has a mix of automatable and non-automatable tasks. "
                f"While some tasks like reporting and analysis can be AI-assisted, "
                f"others requiring judgment, physical presence, or human interaction remain essential."
            )
        return (
            f"{title} involves a mix of cognitive and interpersonal/physical work. "
            f"AI can assist with data analysis and documentation, but human judgment "
            f"and interaction remain central to the role."
        )
    elif score <= 7:
        if has_tasks:
            return (
                f"{title} involves significant knowledge work with AI-automatable components. "
                f"Tasks involving analysis, reporting, and routine decision-making are increasingly "
                f"handled by AI, though strategic judgment and stakeholder management remain human."
            )
        return (
            f"{title} is primarily knowledge work with substantial AI exposure. "
            f"Routine analysis, documentation, and decision-support tasks can be "
            f"automated, while strategic and interpersonal aspects require humans."
        )
    elif score <= 9:
        if has_tasks:
            return (
                f"{title} involves mostly digital/cognitive work that AI can substantially perform. "
                f"Many core tasks around analysis, content creation, and information processing "
                f"are within current AI capabilities, though complex judgment calls remain human."
            )
        return (
            f"{title} is highly exposed to AI automation. Core tasks are primarily digital "
            f"and cognitive, falling within current AI capabilities for analysis, generation, "
            f"and processing."
        )
    else:
        return (
            f"{title} involves routine, fully digital tasks that AI can nearly fully automate. "
            f"Core functions are repetitive information processing with minimal need for "
            f"human judgment or physical presence."
        )


def main() -> None:
    """Score all occupations locally and save results."""
    enriched_path = PROCESSED_DIR / "occupations_enriched.json"
    if not enriched_path.exists():
        raise FileNotFoundError(f"{enriched_path} not found. Run `make ingest` first.")

    with open(enriched_path) as f:
        occupations = json.load(f)

    SCORED_DIR.mkdir(parents=True, exist_ok=True)

    scores = {}
    for occ in occupations:
        exposure, rationale = score_occupation(occ)
        scores[occ["slug"]] = {"exposure": exposure, "rationale": rationale}

    # Save as both run1 and run2 (deterministic, so identical)
    for run in ["run1", "run2"]:
        output_path = SCORED_DIR / f"scores_{run}.json"
        with open(output_path, "w") as f:
            json.dump(scores, f, indent=2)
        print(f"Saved {len(scores)} scores → {output_path}")

    # Empty divergence (deterministic scoring)
    with open(SCORED_DIR / "divergence.json", "w") as f:
        json.dump([], f)

    # Distribution summary
    from collections import Counter

    dist = Counter(s["exposure"] for s in scores.values())
    exposures = [s["exposure"] for s in scores.values()]
    mean = sum(exposures) / len(exposures)
    print(f"\nDistribution (mean={mean:.1f}):")
    for score in range(11):
        count = dist.get(score, 0)
        bar = "█" * count
        print(f"  {score:2d}: {bar} ({count})")


if __name__ == "__main__":
    main()
