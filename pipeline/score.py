"""Score occupations for AI exposure using Anthropic Batch API."""

import json
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DIR = Path("data/processed")
SCORED_DIR = Path("data/scored")

SYSTEM_PROMPT = (
    "You are an expert on AI capabilities and labor economics. "
    "You will be given details about a Singapore occupation including its key tasks "
    "and technical skills (from the SkillsFuture Skills Framework).\n\n"
    "Score the occupation's exposure to AI automation on a 0-10 scale:\n\n"
    "0-1: Physical, manual labor with no meaningful AI impact (e.g., cleaner, refuse collector)\n"
    "2-3: Primarily interpersonal + physical work (e.g., hairdresser, bus driver)\n"
    "4-5: Mixed — some tasks automatable, others need human judgment/physical presence "
    "(e.g., nurse, teacher, property agent)\n"
    "6-7: Knowledge work with significant AI-automatable components "
    "(e.g., accountant, HR manager, sales manager)\n"
    "8-9: Mostly digital/cognitive work that AI can substantially perform "
    "(e.g., software engineer, graphic designer, translator)\n"
    "10: Routine, fully digital tasks that AI can nearly fully automate "
    "(e.g., data entry clerk, basic bookkeeper)\n\n"
    "IMPORTANT: Score based on which SPECIFIC TASKS listed are automatable by current AI (2025), "
    "not just the job title. If tasks are listed, evaluate each one. "
    "Higher exposure means more tasks can be done by AI.\n\n"
    "Respond with ONLY valid JSON:\n"
    '{"exposure": <integer 0-10>, "rationale": "<2-3 sentences>"}'
)


def build_batch_requests(prompts: dict[str, str]) -> list[dict]:
    """Build batch request objects for Anthropic Batch API."""
    requests = []
    for slug, prompt_text in prompts.items():
        requests.append(
            {
                "custom_id": slug,
                "params": {
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 256,
                    "temperature": 0.2,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt_text}],
                },
            }
        )
    return requests


def submit_batch(client: anthropic.Anthropic, requests: list[dict], run_label: str) -> str:
    """Submit a batch and return the batch ID."""
    print(f"Submitting batch ({run_label}): {len(requests)} requests...")
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    print(f"  Batch ID: {batch_id}")

    # Save batch ID for resumability
    SCORED_DIR.mkdir(parents=True, exist_ok=True)
    id_file = SCORED_DIR / f"batch_id_{run_label}.txt"
    id_file.write_text(batch_id)

    return batch_id


def poll_batch(client: anthropic.Anthropic, batch_id: str) -> None:
    """Poll until batch completes."""
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        print(
            f"  Status: {status} | succeeded={counts.succeeded} errored={counts.errored} processing={counts.processing}"
        )
        if status == "ended":
            break
        time.sleep(30)


def collect_results(client: anthropic.Anthropic, batch_id: str) -> dict[str, dict]:
    """Collect results from a completed batch."""
    scores = {}
    for result in client.messages.batches.results(batch_id):
        slug = result.custom_id
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            try:
                parsed = json.loads(text)
                scores[slug] = {
                    "exposure": int(parsed["exposure"]),
                    "rationale": parsed["rationale"],
                }
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"  Warning: Failed to parse response for {slug}: {e}")
                scores[slug] = {"exposure": 5, "rationale": f"Parse error: {text[:100]}"}
        else:
            print(f"  Warning: Request failed for {slug}: {result.result.type}")
            scores[slug] = {"exposure": 5, "rationale": "Batch request failed"}

    return scores


def run_scoring(run_label: str = "run1") -> dict[str, dict]:
    """Run a single scoring batch end-to-end."""
    prompts_path = PROCESSED_DIR / "prompts.json"
    if not prompts_path.exists():
        raise FileNotFoundError(f"{prompts_path} not found. Run `make enrich` first.")

    with open(prompts_path) as f:
        prompts = json.load(f)

    client = anthropic.Anthropic()
    requests = build_batch_requests(prompts)

    # Check for existing batch ID (resumability)
    id_file = SCORED_DIR / f"batch_id_{run_label}.txt"
    if id_file.exists():
        batch_id = id_file.read_text().strip()
        print(f"Resuming batch {batch_id} ({run_label})")
    else:
        batch_id = submit_batch(client, requests, run_label)

    poll_batch(client, batch_id)
    scores = collect_results(client, batch_id)

    output_path = SCORED_DIR / f"scores_{run_label}.json"
    with open(output_path, "w") as f:
        json.dump(scores, f, indent=2)
    print(f"  Saved {len(scores)} scores → {output_path}")

    return scores


def main() -> None:
    """Run dual scoring batches and generate divergence report."""
    SCORED_DIR.mkdir(parents=True, exist_ok=True)

    # Run 1
    print("\n=== Scoring Run 1 ===")
    scores1 = run_scoring("run1")

    # Run 2
    print("\n=== Scoring Run 2 ===")
    scores2 = run_scoring("run2")

    # Divergence report
    print("\n=== Divergence Report ===")
    divergent = []
    for slug in scores1:
        if slug in scores2:
            diff = abs(scores1[slug]["exposure"] - scores2[slug]["exposure"])
            if diff >= 3:
                divergent.append(
                    {
                        "slug": slug,
                        "run1": scores1[slug]["exposure"],
                        "run2": scores2[slug]["exposure"],
                        "diff": diff,
                    }
                )

    if divergent:
        print(f"  {len(divergent)} occupations with divergence >= 3:")
        for d in sorted(divergent, key=lambda x: -x["diff"]):
            print(f"    {d['slug']}: run1={d['run1']} run2={d['run2']} (diff={d['diff']})")
    else:
        print("  No significant divergence found.")

    divergence_path = SCORED_DIR / "divergence.json"
    with open(divergence_path, "w") as f:
        json.dump(divergent, f, indent=2)

    print(f"\nScoring complete. {len(scores1)} occupations scored.")


if __name__ == "__main__":
    main()
