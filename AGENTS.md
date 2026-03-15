# Project Guidelines for Codex

> Singapore AI Jobs Exposure Treemap — Python pipeline + static HTML Canvas frontend.

---

## Core Principles

- **Simplicity over complexity.** Minimum changes needed for the task.
- **No laziness.** Find root causes. Senior developer standards.
- **DRY.** Flag repetition aggressively.
- **Well-tested code is non-negotiable.**
- **Minimal diff.** Explicit over clever.

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
- Type hints on all function signatures.
- Never commit secrets. Use `.env` for sensitive config.

---

## Git Workflow

- Clear commit messages explaining the "why."
- Commit logical units. Stage specific files.
- Always push immediately after committing.

---

## Shell Commands

- DO NOT pipe through `head`, `tail`, `less`, `more`.
- Use command-specific flags (e.g., `git log -n 10`).

---

## Anti-Patterns

- No helpers/abstractions for one-time operations.
- No designing for hypothetical future requirements.
- If unused, delete completely.
- Don't "improve" adjacent code while fixing a bug.

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup | `make setup` |
| Lint | `make lint` |
| Test | `make test` |
| Full pipeline | `make pipeline` |
| Serve locally | `make serve` |
