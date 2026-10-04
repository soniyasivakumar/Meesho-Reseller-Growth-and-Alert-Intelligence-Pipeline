# Agent specification: monthly category growth monitor

## 4.1 The five components

**Goal.** Keep Meesho category managers informed of any category whose month-on-month revenue moves
by more than 8% (up or down), with a human approving every message before anything goes out.

**Tools.** All are plain Python functions, already written in earlier Parts:

* `validate_feed(csv_path)` (Part 2) to check a monthly feed before anything else.
* `mom_growth(previous, current)` (Part 2) for the MoM percentage.
* `is_flagged(mom_pct)` (Part 2) for `flagged` / `not_flagged` / `escalate_exact_boundary`.
* `draft_message(...)`, the offline template-fill from the Part 3 prompt pack (implemented in `mock_agent_runner.py`).
* `numbers_trace_ok(...)` (in `mock_agent_runner.py`) and `assert_no_raw_names_leak(...)` (Part 3, `masking.py`) as output checks.

**Memory / state.** The agent keeps nothing in its own head between runs; the state it needs is the
**previous month's revenue per category**, which lives in the previous-month feed (Part 1's
`monthly_category_revenue.csv`). Each run reads it fresh, so the next run needs that file and nothing
else. The run's JSON is also saved, which is the record of what was drafted and what was suppressed.

**Planner.** Subtasks 1 to 8 in section 4.2, always in that order.

**Feedback loop.** The human-approval checkpoint. The runner never sends anything; a successful
run ends with `action_taken = "drafted_and_held_for_approval"`, which is the simulated flag that says
"a person must read and approve these drafts". There is no email, Slack or SMTP code.

## Guardrails

| Type | Rule in this project |
|---|---|
| **Input** | `validate_feed` must pass for both feeds before anything else runs. Blank category, blank or non-numeric revenue and negative revenue are all rejected. |
| **Action** | No message is ever auto-sent; messages are only drafted and held. At most 3 drafts per run, so a month where everything moves cannot flood managers. Exact-boundary cases are never auto-decided. |
| **Output** | Every number in a draft must be the `mom_pct`, `previous_revenue` or `current_revenue` taken from Part 1/Part 2 (checked by `numbers_trace_ok`), and no raw reseller name may appear (`assert_no_raw_names_leak`). |

## Stopping conditions

* **Success:** drafts are produced for up to the top 3 flagged categories, or correctly zero drafts
  if nothing crossed the threshold, with every number traceable. `validation_status = "valid"`,
  `action_taken = "drafted_and_held_for_approval"`.
* **Error:** `validate_feed` returns `False` for either feed. The run is a **Hard Stop**:
  `validation_status = "invalid"`, `action_taken = "hard_stop"`, the validation errors are
  returned in `validation_errors`, and no MoM is computed. It is never a silent skip.

## Given-When-Then specs (the four Part 2 cases, phrased for the agent)

1. **GIVEN** the April feed shows Ethnic Wear at 104520.77 and the May feed shows 185107.61,
   **WHEN** the agent runs for May, **THEN** it computes a MoM of 77.1, classifies Ethnic Wear as
   `flagged`, and drafts a message for it (ranked first in `flagged_categories`).
2. **GIVEN** the May feed shows Beauty & Personal Care at 35542.11 and the June feed shows 37559.07,
   **WHEN** the agent runs for June, **THEN** it computes 5.67, classifies the category as
   `not_flagged`, and the category appears in neither `flagged_categories` nor `suppressed_categories`.
3. **GIVEN** a category whose previous revenue is 100000 and current revenue is 108000 (exactly 8.0%),
   **WHEN** the agent runs, **THEN** it computes exactly 8.0, gets `escalate_exact_boundary`, drafts nothing
   for it and lists it in `escalated_categories` for human review, never treating it as flagged or not flagged.
4. **GIVEN** a current-month feed with a negative revenue row, a missing-category row and a
   missing-revenue row (`corrupted_feed.csv`), **WHEN** the agent runs, **THEN** it hard-stops with
   `validation_status = "invalid"`, returns exactly those three errors in file order, and leaves
   `flagged_categories`, `suppressed_categories` and `escalated_categories` empty.

## 4.2 Ordered subtasks (the planner)

1. Load the previous-month and current-month revenue feeds and run `validate_feed` on both.
2. If either is invalid: **Hard Stop** and report the errors.
3. If valid: compute `mom_growth` for every category against the previous month.
4. Run `is_flagged` on every category.
5. Sort the flagged categories by `abs(mom_pct)` descending.
6. Draft a message (Part 3 template) for **at most the top 3** by magnitude. The cap prevents the
   notification-flooding failure mode of one message per flagged item with no limit.
7. Log any remaining flagged categories as `suppressed_categories` ("suppressed, review manually"),
   with no message drafted.
   * 7b. Separately, log every category whose result is `escalate_exact_boundary` in
     `escalated_categories`, with no message drafted. It is neither flagged nor not flagged, so it must
     never be dropped from both lists or mistaken for either.
8. Emit one structured JSON object for the run.

## 4.3 JSON output schema

One object per run, success or Hard Stop, with exactly these top-level keys:

```json
{
  "run_month": "May",
  "validation_status": "valid | invalid",
  "validation_errors": [],
  "flagged_categories": [
    {"category": "Ethnic Wear", "mom_pct": 77.1,
     "previous_revenue": 104520.77, "current_revenue": 185107.61,
     "drafted": true, "message": "..."}
  ],
  "suppressed_categories": ["Home & Kitchen"],
  "escalated_categories": [],
  "action_taken": "drafted_and_held_for_approval | hard_stop"
}
```

`flagged_categories` holds the drafted entries (the top 3). `message` is present only when `drafted`
is true. `suppressed_categories` holds names only.

## Known limits

The mock reads CSVs and writes JSON; it does not know which promotions ran or which listings sold, so
every cause in a draft is a labelled hypothesis. A real deployment would add a person to approve
drafts, which is the part this spec deliberately leaves as a held flag.
