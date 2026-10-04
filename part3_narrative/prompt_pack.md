# Prompt pack: flagged-category stakeholder update

One reusable pack. Its offline template-fill is implemented as `draft_message` in `part4_agent/mock_agent_runner.py`, which is how Part 4's agent uses it.

## Trigger

Start this prompt when a category's `is_flagged(mom_pct)` result is `"flagged"`, meaning the
month-on-month revenue change is more than 8% in either direction. It is **not** started for
`"not_flagged"`, and it is not started for `"escalate_exact_boundary"` either; that case goes to a
human first.

## Input list

| Placeholder | Meaning | Source |
|---|---|---|
| `{category}` | Category name, e.g. Ethnic Wear | `monthly_category_revenue.csv` (Part 1) |
| `{month}` | Month being reported, e.g. May | Agent run argument |
| `{prev_month}` | Month compared against, e.g. April | Previous-month feed |
| `{previous_revenue}` | Revenue in `{prev_month}`, INR, 2 decimals | Part 1 CSV |
| `{current_revenue}` | Revenue in `{month}`, INR, 2 decimals | Part 1 CSV |
| `{mom_pct}` | Month-on-month change in %, from `mom_growth` | Part 2 |

No other variable is allowed into the prompt. In particular there is no reseller name, no
order-level data and no free-text field.

## Prompt

```text
You are writing a short stakeholder update for a Meesho category manager.
A category was flagged because its month-on-month revenue change crossed the threshold.
Facts you may use (and no others): category = [{category}]; [{month}] revenue = INR [{current_revenue}];
[{prev_month}] revenue = INR [{previous_revenue}]; MoM change = [{mom_pct}]%.
Write exactly three labelled parts:
Context: say what is measured ([{category}] revenue) and the period ([{month}] vs. [{prev_month}]).
Insight: state the MoM change of [{mom_pct}]% and label it as a fact.
Implication: give one specific next step. If it suggests a cause, label it a hypothesis.
Rules: never state a number that is not one of the facts above; do not mention any reseller by name;
do not claim a cause as proven; keep it under 120 words.
```

(In the code the square brackets are replaced by Python `{}` placeholders; the wording is identical.)

## Checklist (run on every draft before it is used)

1. **Numbers match exactly.** Every number in the draft equals one of `{previous_revenue}`,
   `{current_revenue}` or `{mom_pct}` character for character. (Automated: `numbers_trace_ok` in `mock_agent_runner.py`.)
2. **Fact vs hypothesis.** The percentage is labelled a fact; any proposed cause is labelled a hypothesis.
3. **Specific next step.** The implication names what to check or do (which listings, which
   comparison, who to ask), not just "look into it".
4. **No raw reseller names.** Resellers appear only as region + `alias_for(reseller_id)`.
   (Automated: `assert_no_raw_names_leak` in `masking.py`.)
5. **Direction is right.** Growth is not described as a decline, or vice versa, and the correct
   months are named (`{month}` vs. `{prev_month}`).
6. **Human approval pending.** The draft is marked as held for approval; nothing is treated as sent.
