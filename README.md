# Singapore AI Jobs: AI Exposure Treemap

Interactive Canvas-based treemap visualizing AI automation exposure across ~560 Singapore occupations, scored by Claude via the Anthropic Batch API using SkillsFuture task-level data, sized by MOM employment/wage data.

Inspired by [karpathy.ai/jobs](https://karpathy.ai/jobs) and [najibninaba/jobs-sg](https://github.com/najibninaba/jobs-sg).

## Key Differentiators

- **Task-level SkillsFuture data** for richer, more accurate scoring (not just SSOC titles)
- **Anthropic Batch API** (not CLI subprocess) for reproducible, cost-effective scoring
- **Dual-run averaging** with divergence detection for score stability
- **SkillsFuture reskilling badges** highlighting funded training pathways
- **Methodology transparency panel** showing full scoring prompt and data sources

## Data Sources

1. **MOM Occupational Wage Survey 2024** — ~560 occupations with SSOC codes, gross monthly wage percentiles
2. **SkillsFuture Skills Framework Database** — Task-level data per role across 38 sectors

## Setup

```bash
# Install dependencies
make setup

# Place data files in data/raw/
# - MOM wage survey Excel (T4 table)
# - SkillsFuture database (template_sfw_database---combined.xlsx)

# Run full pipeline
make pipeline

# Serve locally
make serve
# Open http://localhost:8888
```

## Pipeline Steps

| Step | Command | Description |
|------|---------|-------------|
| Ingest | `make ingest` | Parse MOM + SkillsFuture Excel files |
| Enrich | `make enrich` | Build LLM prompt context per occupation |
| Score | `make score` | Batch API scoring (dual run) |
| Validate | `make validate` | QC checks + divergence report |
| Build | `make build` | Merge into `site/data.json` |

## Data Downloads

### MOM Occupational Wage Survey
Download Table T4 from the [MOM Statistical Tables](https://stats.mom.gov.sg/Pages/Occupational-Wages-Tables.aspx) page.

### SkillsFuture Skills Framework
Download the combined database from the [SkillsFuture portal](https://www.skillsfuture.gov.sg/skills-framework).

Place both files in `data/raw/` (gitignored).

## Stack

- **Pipeline**: Python 3.12+, pandas, pydantic, anthropic, rapidfuzz
- **Frontend**: Single-file Canvas 2D treemap (vanilla JS)
- **Deploy**: Vercel (static site)
- **Scoring**: Claude Haiku 4.5 via Anthropic Batch API (~$0.50-1.00 total)

## Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-...
```

## License

MIT
