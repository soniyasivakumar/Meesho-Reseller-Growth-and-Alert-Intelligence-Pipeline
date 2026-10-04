# Narrative report

All figures come from Part 1 (`monthly_category_revenue.csv`, `region_revenue.csv`,
`top_resellers.csv`) and Part 2 (`mom_growth`, `is_flagged`). Nothing is estimated.

## 3.2 Worked narratives

### May: Ethnic Wear (+77.1%, flagged)

**Context.** This update tracks Ethnic Wear revenue for May 2026 against April 2026, using
delivered, returned, cancelled and pending orders together as in the Part 1 revenue query.

**Insight (fact).** Ethnic Wear revenue rose 77.1% month on month, from INR 104520.77 in April to
INR 185107.61 in May, and orders grew from 64 to 104. This is the largest move of any category in
May and it is flagged by the 8% rule.

**Implication.** *Hypothesis (not proven by this data):* a festive-season promotion or a few trending
listings pulled demand into Ethnic Wear. *Recommended next step:* the Ethnic Wear category manager
should list the top-selling Ethnic Wear products in May, confirm those products have enough stock for
June, and check whether any promotion ran in May. If one did, plan June stock around that, because
the next month may fall back.

### June: Ethnic Wear (-58.74%, flagged)

**Context.** This update tracks Ethnic Wear revenue for June 2026 against May 2026, on the same
basis as the May update above.

**Insight (fact).** Ethnic Wear revenue fell 58.74% month on month, from INR 185107.61 in May to
INR 76371.53 in June, and orders dropped from 104 to 52. The fall is flagged by the 8% rule, in the
opposite direction to May.

**Implication.** *Hypothesis (not proven by this data):* May was lifted by a short-lived spike that has
now faded, rather than Ethnic Wear losing its customers. *Recommended next step:* compare the number
of active Ethnic Wear resellers and the out-of-stock Ethnic Wear listings between May and June. If
resellers stayed active and stock was available, treat June as the return to normal and keep
planning from there; if listings were out of stock, restock the best sellers first.

### Self-score against the refinement checklist

| Criterion | Result | Why |
|---|---|---|
| Specificity | Pass | Both blocks name the category (Ethnic Wear), the exact months, the exact percentages (77.1% and 58.74%) and the exact revenue figures from Part 1. |
| Audience fit | Pass | They are written for a regional or category manager in plain language, with no SQL, code or statistics terms. |
| Completeness | Pass | Each block has a Context, a labelled Insight and an Implication, in that order. |
| Actionability | Pass | Each Implication names a concrete check (best-selling listings and stock for June; active resellers and out-of-stock listings), not "look into Ethnic Wear". |

## 3.3 Chart-choice justification (text only)

**Q1. Which month had the highest total revenue? (April INR 419417.43, May INR 444594.25, June INR 398055.24)**
I would use a simple vertical bar chart with one bar per month, in calendar order. This is a
bivariate view (one categorical variable, month, against one numeric variable, total revenue), and
a bar lets the reader compare lengths and spot May as the tallest within 10 seconds. The y-axis must start at
zero: the three totals are less than 12% apart, and a truncated axis would make May look
several times bigger than June. It is a single series, so no legend is needed, and it stays 2D so
that no 3D effect distorts the bar heights.

**Q2. What share of April's total revenue is Ethnic Wear? (INR 104520.77 of INR 419417.43 = 24.92%)**
This is a part-to-whole question, so I would use a two-slice donut (or pie) chart: Ethnic Wear
versus all other categories, with "24.92%" printed directly on the Ethnic Wear slice. It is a
univariate composition of one measure (April revenue), and with only two slices the message, "about a
quarter", is clear within 10 seconds. Direct labels replace a legend, since there is effectively one series. A
five-slice pie would be harder to read, so I would drop it, and the chart would stay flat, never 3D, because tilt makes slice sizes
unreliable. If the manager wanted all five categories, I would switch to a single 100% stacked bar. An axis baseline is not an issue here because a pie has no y-axis.

**Q3. How do the four regions compare on total revenue? (North 337125.46, West 333106.33, South 316736.68, East 275098.45)**
I would use a horizontal bar chart with regions sorted from highest to lowest revenue. It is a bivariate
chart (region against revenue), and the sorted order lets the reader see that North leads, West is
close behind and East trails, in under 10 seconds. The value axis starts at zero because the gaps are
modest (East is the lowest, about 18% below North), and a truncated axis would exaggerate them. Single series, so no legend; labelled
with the exact INR values at the bar ends; no 3D. Adding a second variable such as month (a grouped bar
per region) would make it multivariate, which is only worth doing if the question were about change over time.

## 3.4 Top-reseller narrative (masked)

Resellers are referred to only by region and alias, in line with the masking policy in `masking.py`.

<!-- BEGIN TOP_RESELLER_NARRATIVE -->
Five resellers each spent more than INR 50000 between April and June 2026. In the West region,
ALIAS-19 leads with INR 75295.09 and ALIAS-22 follows with INR 73882.33. In the South region,
ALIAS-12 spent INR 69936.46. In the North region, ALIAS-06 spent INR 64238.97 and ALIAS-05 spent
INR 61825.02. These are facts taken from the Part 1 query. Hypothesis: the two West resellers at the
top may be benefitting from strong local demand, which this data cannot confirm. Recommended next
step: the West and North regional managers should check that these five resellers have enough stock
and support for the coming month, and ask the West manager what is working for ALIAS-19 and ALIAS-22
so it can be shared with other resellers in the region.
<!-- END TOP_RESELLER_NARRATIVE -->
