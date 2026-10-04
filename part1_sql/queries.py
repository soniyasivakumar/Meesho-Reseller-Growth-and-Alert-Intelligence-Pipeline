"""Part 1: SQL business query engine (queries.py variant of queries.sql).

Runs the five standing business queries against data/meesho_reseller.db with Python's
sqlite3 module and saves each result under part1_sql/output/.

Usage (from the repo root):
    python data/generate_dataset.py
    python part1_sql/queries.py
"""
import csv
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "..", "data", "meesho_reseller.db")
OUT_DIR = os.path.join(HERE, "output")

QUERIES = {}

# Q1. Revenue and order count per month x category. Direct input to Parts 2 and 4.
# ORDER BY uses CASE so rows come out in calendar / catalogue order, not alphabetical
# (alphabetical would list April, June, May).
QUERIES["monthly_category_revenue"] = """
SELECT month,
       category,
       ROUND(SUM(quantity * unit_price), 2) AS revenue,
       COUNT(*)                             AS n_orders
FROM orders
GROUP BY month, category
ORDER BY CASE month WHEN 'April' THEN 1 WHEN 'May' THEN 2 WHEN 'June' THEN 3 END,
         CASE category WHEN 'Ethnic Wear' THEN 1 WHEN 'Western Wear' THEN 2
                       WHEN 'Kids Wear' THEN 3 WHEN 'Home & Kitchen' THEN 4
                       WHEN 'Beauty & Personal Care' THEN 5 END
"""

# Q2. Total revenue and order count per region (orders joined to resellers).
QUERIES["region_revenue"] = """
SELECT r.region,
       ROUND(SUM(o.quantity * o.unit_price), 2) AS revenue,
       COUNT(*)                                 AS n_orders
FROM orders o
JOIN resellers r ON r.reseller_id = o.reseller_id
GROUP BY r.region
ORDER BY revenue DESC
"""

# Q3. Resellers with total spend above INR 50,000, top 5 by spend.
# HAVING (not WHERE) because the filter is on an aggregate.
QUERIES["top_resellers"] = """
SELECT r.reseller_id,
       r.reseller_name,
       r.region,
       ROUND(SUM(o.quantity * o.unit_price), 2) AS total_spend
FROM orders o
JOIN resellers r ON r.reseller_id = o.reseller_id
GROUP BY r.reseller_id, r.reseller_name, r.region
HAVING SUM(o.quantity * o.unit_price) > 50000
ORDER BY total_spend DESC
LIMIT 5
"""

# Q4a. Resellers who have never placed an order: LEFT JOIN, keep only the unmatched rows.
QUERIES["never_ordered"] = """
SELECT r.reseller_id, r.reseller_name, r.region
FROM resellers r
LEFT JOIN orders o ON o.reseller_id = r.reseller_id
WHERE o.order_id IS NULL
"""

# Q4b. Why COUNT(*) is the WRONG way to test for a zero-match LEFT JOIN row.
# A LEFT JOIN never drops a left-side row. For a reseller with no orders it emits ONE row
# in which every order column is NULL. COUNT(*) counts rows, so it counts that all-NULL
# row and reports 1. COUNT(o.order_id) skips NULLs, so it reports the true answer, 0.
# For RS024 this query returns count_star = 1 and count_order_id = 0 in the same row,
# which is exactly why COUNT(*) cannot be used to detect "no matching orders".
QUERIES["never_ordered_count_demo"] = """
SELECT r.reseller_id,
       COUNT(*)          AS count_star,
       COUNT(o.order_id) AS count_order_id
FROM resellers r
LEFT JOIN orders o ON o.reseller_id = r.reseller_id
WHERE r.reseller_id = 'RS024'
GROUP BY r.reseller_id
"""

# Q5. Average order value for June, Delivered orders only.
QUERIES["june_delivered_aov"] = """
SELECT ROUND(SUM(quantity * unit_price) / COUNT(*), 2) AS aov_june_delivered
FROM orders
WHERE month = 'June' AND status = 'Delivered'
"""


def fmt(value):
    # two decimals always (104520.70, not 104520.7) so figures match the brief exactly
    return f"{value:.2f}" if isinstance(value, float) else value


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    results = {}
    for name, sql in QUERIES.items():
        cur = conn.execute(sql)
        headers = [d[0] for d in cur.description]
        rows = [[fmt(v) for v in row] for row in cur.fetchall()]
        results[name] = rows
        with open(os.path.join(OUT_DIR, f"{name}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)
        print(f"{name}: {len(rows)} row(s) -> part1_sql/output/{name}.csv")
    conn.close()

    # quick check against the acceptance values in the brief
    monthly = results["monthly_category_revenue"]
    assert len(monthly) == 15
    assert round(sum(float(r[2]) for r in monthly), 2) == 1262066.92
    assert [r[0] for r in results["top_resellers"]] == ["RS019", "RS022", "RS012", "RS006", "RS005"]
    assert results["never_ordered"] == [["RS024", "Ahmedabad Reseller 6", "West"]]
    assert results["never_ordered_count_demo"] == [["RS024", 1, 0]]
    assert float(results["june_delivered_aov"][0][0]) == 1267.69
    print("Part 1 acceptance checks passed.")


if __name__ == "__main__":
    main()
