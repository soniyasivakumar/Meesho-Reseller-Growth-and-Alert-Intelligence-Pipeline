"""Part 2: guardrail and growth-detection engine.

Three small functions that turn "significant change" into a numeric rule:

* mom_growth      - month-on-month growth in percent
* is_flagged      - three-way decision (flagged / not_flagged / escalate_exact_boundary)
* validate_feed   - input guardrail for a month,category,revenue,n_orders CSV

Part 4's agent imports these as they are; nothing here is re-implemented elsewhere.
"""
import csv
import math

DEFAULT_THRESHOLD = 8.0


def mom_growth(previous: float, current: float) -> float:
    """Month-on-month growth in percent, rounded to 2 decimals."""
    if previous == 0:
        # A percentage change from zero is undefined; fail loudly instead of
        # returning inf/nan that could slip into a report.
        raise ValueError("previous revenue is 0, MoM growth is undefined")
    return round((current - previous) / previous * 100, 2)


def is_flagged(mom_pct: float, threshold: float = DEFAULT_THRESHOLD) -> str:
    """Return 'flagged', 'not_flagged' or 'escalate_exact_boundary'.

    A string is returned instead of a bool on purpose: a move that lands exactly on
    the threshold is neither of the first two and is held for a human to decide.
    """
    size = abs(mom_pct)
    if size > threshold:
        return "flagged"
    if size < threshold:
        return "not_flagged"
    return "escalate_exact_boundary"


def validate_feed(csv_path: str) -> tuple[bool, list[str]]:
    """Check a month,category,revenue,n_orders CSV row by row.

    Line numbers are 1-indexed with the header on line 1, so the first data row is
    line 2. Returns (True, []) only when no errors were found.
    """
    errors: list[str] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            month = (row.get("month") or "").strip()
            category = (row.get("category") or "").strip()
            revenue = (row.get("revenue") or "").strip()

            if category == "":
                errors.append(f"line {line_no}: missing category (month={month})")

            if revenue == "":
                errors.append(f"line {line_no}: missing revenue (category={category})")
                continue

            try:
                value = float(revenue)
                if math.isnan(value) or math.isinf(value):
                    raise ValueError
            except ValueError:
                errors.append(f"line {line_no}: revenue not numeric: {revenue!r}")
                continue

            if value < 0:
                errors.append(f"line {line_no}: negative revenue ({value}) for category={category}")

    return (len(errors) == 0, errors)
