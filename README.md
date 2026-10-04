# Meesho Reseller Growth & Alert Intelligence Pipeline

A small monthly monitoring pipeline for a reseller-ops team. It answers the standing SQL questions,
turns "significant change" into a testable rule, drafts a fact-checked update for each category that
moved, and holds every draft for a human to approve. Python standard library (3.10+) and SQLite only.
**No API keys, accounts, network access or paid services are needed.**

## How to run each stage (in order, from the repo root)

| # | Stage | Command | Result |
|---|---|---|---|
| 0 | Regenerate the dataset (seed 42, script unchanged) | `python data/generate_dataset.py` | `data/resellers.csv` (24 rows), `data/orders.csv` (900 rows), `data/meesho_reseller.db` |
| 1 | SQL queries | `python part1_sql/queries.py` | six CSVs in `part1_sql/output/`, plus acceptance checks |
| 2 | Copy the validated feed into the fixtures | `cp part1_sql/output/monthly_category_revenue.csv part2_engine/fixtures/` | the file used by Part 2's tests |
| 2 | Engine tests | `python -m unittest discover -s part2_engine -v` | 10 Given-When-Then tests |
| 3 | Masking self-test | `python part3_narrative/masking.py` | alias format, clean narrative, negative leak case |
| 4 | Agent acceptance checks | `python part4_agent/mock_agent_runner.py check` | May, June, corrupted-feed scenarios |
| 4 | Run the agent | `python part4_agent/mock_agent_runner.py all` | one JSON object per scenario (or `may`, `june`, `corrupted`) |

## How the Parts connect

```
data/generate_dataset.py ──► data/meesho_reseller.db
                                   │
                    Part 1: part1_sql/queries.py
                                   │  monthly_category_revenue.csv  (month,category,revenue,n_orders)
                                   ▼
          Part 2: growth_engine.py  (validate_feed, mom_growth, is_flagged)
                                   │
                                   ▼
          Part 4: mock_agent_runner.py ◄── Part 3: prompt_pack.md (template-fill is
                      │                     implemented here) + masking.py
                      ▼
            one JSON object per run
```

* Part 1's `monthly_category_revenue.csv` is validated and used by Part 2 (also copied to its fixtures) and is the feed Part 4 reads. It holds all three months; the agent picks the right month from it.
* Part 2's three functions are imported by Part 4 exactly as written.
* Part 3's template-fill is `draft_message` in the agent runner, written to match `prompt_pack.md`; `masking.py` is used as an output guardrail.

## Zero API keys

Every "AI narrative" step is a deterministic template-fill. There is no LLM call, network request or
email/SMTP code anywhere, and everything runs with no environment variables set.

## Mapping each Part to the workflow pattern it implements

* **Part 1 -> Part 2:** "compute real numbers via SQL first, then hand off." Models never produce figures; SQL does.
* **Part 2:** guardrail-first. Validate input, apply an explicit numeric rule, and send the exact-boundary case to a human.
* **Part 3:** prompt-pack pattern (Trigger -> Input list -> Prompt -> Checklist) with Context -> Insight -> Implication narratives, and masking before anything could go external.
* **Part 4:** Intake -> Summary -> Report Draft -> Validate: load and validate feeds, compute and rank changes, draft up to 3 messages, check numbers and names, hold for human approval.

## Design notes

* An invalid feed is a Hard Stop (`action_taken = "hard_stop"`) with the errors listed, never a partial result.
* At most 3 drafts per run; remaining flagged categories are listed as suppressed for manual review.
* An exact 8.0% move returns `"escalate_exact_boundary"` and goes to `escalated_categories`: never drafted and never dropped.
* `mom_growth` raises an error if previous revenue is 0 instead of returning infinity.
* Revenue is `SUM(quantity * unit_price)` over all order statuses, as the brief defines it.
* The brief allows `queries.py` in place of `queries.sql`; I used `queries.py` so the queries and their saved CSVs come from one command. The explanation of why `COUNT(*)` fails on a zero-match LEFT JOIN is in the inline comments of that file.

## Documentation referenced

Official Python standard-library docs for `csv`, `sqlite3`, `random`, `json`, `re`, `calendar`, `tempfile` and
`unittest`, and the SQLite documentation on `LEFT JOIN`, `COUNT()` and `HAVING`.
