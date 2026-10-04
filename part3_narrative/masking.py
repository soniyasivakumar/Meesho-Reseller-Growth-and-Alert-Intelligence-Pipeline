"""Part 3.4: masking policy for anything that could leave the internal team.

External-facing text refers to resellers by region + alias only, never by name.

Self-test (from the repo root):  python part3_narrative/masking.py
"""
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def alias_for(reseller_id: str) -> str:
    """RS019 -> ALIAS-19, RS006 -> ALIAS-06."""
    return f"ALIAS-{reseller_id[3:]}"


def assert_no_raw_names_leak(text: str, reseller_names: list[str]) -> bool:
    """True if the text is clean; False if any raw reseller_name appears verbatim."""
    return not any(name and name in text for name in reseller_names)


def load_reseller_names(path: str | None = None) -> list[str]:
    """Read every reseller_name from data/resellers.csv."""
    if path is None:
        path = os.path.join(HERE, "..", "data", "resellers.csv")
    with open(path, newline="") as f:
        return [row["reseller_name"] for row in csv.DictReader(f)]


def _top_reseller_narrative() -> str:
    """The masked top-reseller block inside narrative_report.md."""
    with open(os.path.join(HERE, "narrative_report.md")) as f:
        text = f.read()
    m = re.search(r"<!-- BEGIN TOP_RESELLER_NARRATIVE -->(.*?)<!-- END TOP_RESELLER_NARRATIVE -->", text, re.S)
    return m.group(1).strip()


def run_checks() -> None:
    names = load_reseller_names()
    assert len(names) == 24

    # alias format
    assert alias_for("RS019") == "ALIAS-19"
    assert alias_for("RS006") == "ALIAS-06"

    # positive case: the final top-reseller narrative is clean
    narrative = _top_reseller_narrative()
    assert assert_no_raw_names_leak(narrative, names) is True

    # the whole report is clean too
    with open(os.path.join(HERE, "narrative_report.md")) as f:
        assert assert_no_raw_names_leak(f.read(), names) is True

    # negative case: put one raw name back in and the check must fail
    leaked = narrative.replace("ALIAS-19", "Mumbai Reseller 1")
    assert "Mumbai Reseller 1" in leaked
    assert assert_no_raw_names_leak(leaked, names) is False
    print("Masking checks passed (alias format, clean narrative, negative leak case).")


if __name__ == "__main__":
    run_checks()
