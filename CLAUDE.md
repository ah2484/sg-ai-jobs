# Project Guidelines for Claude

> Singapore AI Jobs Exposure Treemap — Python pipeline + static HTML Canvas frontend.

---

## Core Principles

### Simplicity Over Complexity
- **Avoid over-engineering.** Only make changes that are directly requested or clearly necessary.
- Prefer 3 similar lines of code over a premature abstraction.
- The right amount of complexity is the minimum needed for the current task.

### No Laziness
- **Find root causes.** No temporary fixes. Senior developer standards.
- Changes should only touch what's necessary.

### Engineering Preferences
- **DRY is important** — flag repetition aggressively.
- **Well-tested code is non-negotiable.**
- Bias toward explicit over clever.
- **Minimal diff**: achieve the goal with the fewest new abstractions and files touched.

### Ask Before Assuming
- **Never make assumptions on my behalf.** If requirements are unclear, ask.
- Surface inconsistencies. Present tradeoffs. Push back when a request seems problematic.

### Code Hygiene
- Remove dead code, unused imports, obsolete comments.
- Do not leave `TODO` comments for things you could fix now.
- Do not modify unrelated code.

### Respect Existing Code
- **Read before writing.** Follow existing patterns and conventions.

---

## Workflow

### Architect Then Execute
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- Get approval before writing code.
- If something goes sideways, STOP and re-plan immediately.

### Iterative Refinement
- Small, incremental changes. Commit logical units separately. Test each change.

### Subagents
- Use liberally to keep main context clean. One task per subagent.

### Verification Before Done
- Never mark a task complete without proving it works. Run tests, demonstrate correctness.

---

## Stack

- **Python 3.12+** with `uv` for dependency management
- **Linting**: `ruff` (check + format)
- **Testing**: `pytest`
- **Data**: pandas, openpyxl, pydantic
- **LLM**: Anthropic Batch API (claude-haiku-4-5)
- **Frontend**: Single-file Canvas 2D treemap (vanilla JS, no build step)
- **Deploy**: Vercel (static site from `site/` directory)

---

## Code Quality

- Error handling only at system boundaries (file I/O, API calls).
- Testing is non-negotiable. TDD when implementing new features.
- Never commit secrets. Use `.env` for sensitive config.
- Type hints on all function signatures.

---

## Git Workflow

- Clear commit messages explaining the "why."
- Commit logical units. Stage specific files.
- Always push to GitHub immediately after committing.

---

## Bash Guidelines

- DO NOT pipe through `head`, `tail`, `less`, `more`.
- Use command-specific flags (e.g., `git log -n 10`).

---

## Project Structure

```
sg-ai-jobs/
├── data/raw/           # Manual downloads (gitignored)
├── data/processed/     # Intermediate JSON
├── data/scored/        # Final scored output
├── pipeline/
│   ├── __init__.py
│   ├── ingest.py       # Parse SkillsFuture + MOM Excel
│   ├── enrich.py       # Build LLM prompt context per occupation
│   ├── score.py        # Anthropic Batch API scoring
│   ├── validate.py     # QC + dual-run divergence
│   └── build.py        # Merge into site/data.json
├── site/
│   ├── index.html      # Single-file Canvas treemap
│   └── data.json       # Generated
├── tests/
├── Makefile
├── pyproject.toml
└── README.md
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup | `make setup` |
| Lint | `make lint` |
| Test | `make test` |
| Full pipeline | `make pipeline` |
| Serve locally | `make serve` |
| Deploy | `vercel --prod` |
