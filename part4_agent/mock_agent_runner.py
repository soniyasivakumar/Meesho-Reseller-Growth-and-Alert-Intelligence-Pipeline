"""Part 4: mock monitoring agent. Drafts and holds messages; never sends anything.

Entry point:  run(month, previous_month_csv, current_month_csv) -> dict

Part 2's growth_engine functions and Part 3's masking helper are imported, not copied.
The Part 3 prompt-pack template-fill (draft_message) lives in this file. No network call,
no API key and no message-sending code anywhere.

From the repo root:
    python part4_agent/mock_agent_runner.py may         # April -> May
    python part4_agent/mock_agent_runner.py june        # May -> June
    python part4_agent/mock_agent_runner.py corrupted   # June -> corrupted July feed
    python part4_agent/mock_agent_runner.py all         # all three
    python part4_agent/mock_agent_runner.py check       # run the acceptance checks
"""
import calendar
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "part2_engine"))
sys.path.insert(0, os.path.join(ROOT, "part3_narrative"))

from growth_engine import is_flagged, mom_growth, validate_feed  # noqa: E402
from masking import assert_no_raw_names_leak, load_reseller_names  # noqa: E402

MAX_DRAFTS = 3  # notification-flooding cap

PART1_CSV = os.path.join(ROOT, "part1_sql", "output", "monthly_category_revenue.csv")
CORRUPTED_CSV = os.path.join(ROOT, "part2_engine", "fixtures", "corrupted_feed.csv")

# ---------------------------------------------------------------------------
# Part 3 template-fill (offline). Mirrors part3_narrative/prompt_pack.md.
# Only the supplied values are inserted; all other words are fixed text without digits,
# so no figure can appear that was not supplied.
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE = (
    "You are writing a short stakeholder update for a Meesho category manager.\n"
    "A category was flagged because its month-on-month revenue change crossed the threshold.\n"
    "Facts you may use (and no others): category = {category}; {month} revenue = INR {current_revenue}; "
    "{prev_month} revenue = INR {previous_revenue}; MoM change = {mom_pct}%.\n"
    "Write exactly three labelled parts:\n"
    "Context: say what is measured ({category} revenue) and the period ({month} vs. {prev_month}).\n"
    "Insight: state the MoM change of {mom_pct}% and label it as a fact.\n"
    "Implication: give one specific next step. If it suggests a cause, label it a hypothesis.\n"
    "Rules: never state a number that is not one of the facts above; do not mention any reseller by name; "
    "do not claim a cause as proven; keep it under 120 words."
)

_UP = (
    "Implication (hypothesis, not proven by this data): the jump may come from a campaign, a trending "
    "product or retailers stocking up early. Next step: pull the best-selling {category} listings for {month}, "
    "check that stock cover for them is healthy, and confirm with the category manager whether a promotion ran."
)
_DOWN = (
    "Implication (hypothesis, not proven by this data): the drop may reflect a short-lived spike in {prev_month} "
    "fading out, or stock-outs and fewer active resellers in {month}. Next step: compare active {category} resellers "
    "and out-of-stock listings between {prev_month} and {month}, then decide whether a restock or reseller "
    "re-engagement push is needed."
)
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def draft_message(category, month, prev_month, previous_revenue, current_revenue, mom_pct) -> str:
    """Fill the Context -> Insight -> Implication template for one flagged category."""
    v = dict(category=category, month=month, prev_month=prev_month,
             previous_revenue=f"{previous_revenue:.2f}",
             current_revenue=f"{current_revenue:.2f}", mom_pct=mom_pct)
    return (
        "Context: {category} revenue is tracked month on month; this update compares {month} with {prev_month}.\n"
        "Insight (fact): {category} revenue changed by {mom_pct}% in {month} vs. {prev_month}, "
        "from INR {previous_revenue} to INR {current_revenue}.\n"
    ).format(**v) + (_UP if mom_pct > 0 else _DOWN).format(**v)


def fill_prompt(**kw) -> str:
    """The prompt text with placeholders filled (what you would send to an LLM, if you used one)."""
    kw["previous_revenue"] = f"{kw['previous_revenue']:.2f}"
    kw["current_revenue"] = f"{kw['current_revenue']:.2f}"
    return PROMPT_TEMPLATE.format(**kw)


def numbers_trace_ok(message, mom_pct, previous_revenue, current_revenue) -> bool:
    """Output guardrail: every number in the message is one of the three supplied values."""
    allowed = {str(mom_pct), f"{previous_revenue:.2f}", f"{current_revenue:.2f}"}
    return all(tok in allowed for tok in _NUMBER.findall(message))


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------
def _read_revenue(csv_path, wanted_month):
    """({category: revenue}, month_label) for one month of a feed.

    A feed may hold one month or several (the full Part 1 CSV). If rows for wanted_month
    exist only those are used; otherwise the whole file is treated as that month.
    """
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    chosen = [r for r in rows if r["month"].strip() == wanted_month] or rows
    label = chosen[0]["month"].strip() if chosen else wanted_month
    return {r["category"].strip(): float(r["revenue"]) for r in chosen}, label


def _result(month, status, errors, flagged, suppressed, escalated, action):
    return {
        "run_month": month,
        "validation_status": status,
        "validation_errors": errors,
        "flagged_categories": flagged,
        "suppressed_categories": suppressed,
        "escalated_categories": escalated,
        "action_taken": action,
    }


def run(month: str, previous_month_csv: str, current_month_csv: str) -> dict:
    # Subtask 1: load and validate both feeds (input guardrail)
    ok_cur, errors = validate_feed(current_month_csv)
    ok_prev, prev_errors = validate_feed(previous_month_csv)
    errors = errors + [f"previous feed: {e}" for e in prev_errors]

    # Subtask 2: invalid -> Hard Stop, errors surfaced, no MoM attempted
    if not (ok_cur and ok_prev):
        return _result(month, "invalid", errors, [], [], [], "hard_stop")

    # Subtask 3: MoM for every category against the previous month
    idx = list(calendar.month_name).index(month)
    prev_calendar = calendar.month_name[(idx - 2) % 12 + 1]
    previous, prev_month = _read_revenue(previous_month_csv, prev_calendar)
    current, _ = _read_revenue(current_month_csv, month)

    rows = []
    for category, cur_rev in current.items():
        if category not in previous:
            continue
        prev_rev = previous[category]
        if prev_rev == 0:
            return _result(month, "invalid",
                           [f"previous revenue is 0 for category={category}, MoM undefined"],
                           [], [], [], "hard_stop")
        rows.append({"category": category, "previous_revenue": prev_rev,
                     "current_revenue": cur_rev, "mom_pct": mom_growth(prev_rev, cur_rev)})

    # Subtask 4: decide for every category
    flagged_rows, escalated = [], []
    for r in rows:
        decision = is_flagged(r["mom_pct"])
        if decision == "flagged":
            flagged_rows.append(r)
        elif decision == "escalate_exact_boundary":
            escalated.append(r["category"])  # subtask 7b: never drafted, never silently dropped

    # Subtask 5: biggest movers first (stable sort keeps feed order on ties)
    flagged_rows.sort(key=lambda r: abs(r["mom_pct"]), reverse=True)

    # Subtask 6: draft for the top MAX_DRAFTS only
    names = load_reseller_names() if os.path.exists(
        os.path.join(ROOT, "data", "resellers.csv")) else []
    drafted = []
    for r in flagged_rows[:MAX_DRAFTS]:
        msg = draft_message(r["category"], month, prev_month,
                            r["previous_revenue"], r["current_revenue"], r["mom_pct"])
        # output guardrails: numbers must trace; no raw reseller name may appear
        assert numbers_trace_ok(msg, r["mom_pct"], r["previous_revenue"], r["current_revenue"]), \
            f"untraceable number in draft for {r['category']}"
        assert assert_no_raw_names_leak(msg, names), "raw reseller name in draft"
        drafted.append({"category": r["category"], "mom_pct": r["mom_pct"],
                        "previous_revenue": r["previous_revenue"],
                        "current_revenue": r["current_revenue"],
                        "drafted": True, "message": msg})

    # Subtask 7: everything past the cap is suppressed for manual review (no draft)
    suppressed = [r["category"] for r in flagged_rows[MAX_DRAFTS:]]

    # Subtask 8: one structured object per run. Drafts are held; nothing is sent.
    return _result(month, "valid", [], drafted, suppressed, escalated, "drafted_and_held_for_approval")


SCENARIOS = {
    "may": lambda: run("May", PART1_CSV, PART1_CSV),
    "june": lambda: run("June", PART1_CSV, PART1_CSV),
    "corrupted": lambda: run("July", PART1_CSV, CORRUPTED_CSV),
}


def check() -> None:
    """Acceptance checks from the brief."""
    keys = ["run_month", "validation_status", "validation_errors", "flagged_categories",
            "suppressed_categories", "escalated_categories", "action_taken"]

    may = SCENARIOS["may"]()
    assert list(may.keys()) == keys and may["validation_status"] == "valid"
    assert [(f["category"], f["mom_pct"], f["drafted"]) for f in may["flagged_categories"]] == [
        ("Ethnic Wear", 77.1, True), ("Western Wear", -23.6, True), ("Kids Wear", -23.48, True)]
    assert sorted(may["suppressed_categories"]) == ["Beauty & Personal Care", "Home & Kitchen"]
    assert may["escalated_categories"] == []

    june = SCENARIOS["june"]()
    assert [(f["category"], f["mom_pct"]) for f in june["flagged_categories"]] == [
        ("Ethnic Wear", -58.74), ("Home & Kitchen", 42.59), ("Kids Wear", 23.9)]
    assert june["suppressed_categories"] == ["Western Wear"]
    assert june["escalated_categories"] == []
    listed = [f["category"] for f in june["flagged_categories"]] + june["suppressed_categories"]
    assert "Beauty & Personal Care" not in listed

    bad = SCENARIOS["corrupted"]()
    assert bad["validation_status"] == "invalid" and bad["action_taken"] == "hard_stop"
    assert bad["validation_errors"] == [
        "line 3: negative revenue (-4200.0) for category=Western Wear",
        "line 4: missing category (month=July)",
        "line 6: missing revenue (category=Home & Kitchen)"]
    assert bad["flagged_categories"] == [] and bad["suppressed_categories"] == [] \
        and bad["escalated_categories"] == []

    for out in (may, june):
        for f in out["flagged_categories"]:
            assert f["category"] in f["message"] and f"{f['mom_pct']}%" in f["message"]
            assert numbers_trace_ok(f["message"], f["mom_pct"], f["previous_revenue"], f["current_revenue"])

    print("Part 4 acceptance checks passed (May, June, corrupted feed, message traceability).")


def main(argv):
    which = argv[1] if len(argv) > 1 else "all"
    if which == "check":
        check()
        return
    for name in (["may", "june", "corrupted"] if which == "all" else [which]):
        print(json.dumps(SCENARIOS[name](), indent=2))


if __name__ == "__main__":
    main(sys.argv)
