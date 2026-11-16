
# Engineering Decisions

Significant, lasting project decisions belong here, using unique decision IDs. The entries below are new decisions for `BL-P001-000002`. **When integrating into an existing resident repository, append these entries and assign the next unused IDs; never remove or replace earlier decisions.**

---

### Decision: Use the dataset-wide calendar for each product's monthly series

**Decision ID:** `D001` (renumber if already used)
**Backlog:** `BL-P001-000002`
**Date:** `2026-11-16`

#### Context
Receipts for a product may be recorded in non-consecutive months. The requirement calls for a continuous per-product time series within the source dataset's minimum/maximum dates.

#### Decision
Aggregate at `(Product_ID, month(Receipt_Date))`, then reindex each observed product over the common dataset-wide monthly period range. Fill the inserted months with zero receipt frequency and zero quantity.

#### Reason
This makes periods with no recorded activity explicit and prevents a rolling average from inadvertently skipping calendar months. Product quantities remain isolated.

#### Alternatives Considered
Retaining only observed months would distort the time-series interpretation. Using each product's individual first/last month would omit leading/trailing inactive periods relative to the common reporting window.

#### Consequences
The result contains additional zero rows, including months before a product's first receipt and after its last receipt within the dataset window. Output size scales with the number of products times months.

---

### Decision: Require a complete three-month window for the quantity SMA

**Decision ID:** `D002` (renumber if already used)
**Backlog:** `BL-P001-000002`
**Date:** `2026-11-16`

#### Context
The first two months in a three-month rolling window do not have three complete calendar observations.

#### Decision
Compute the trailing monthly quantity mean with `window=3` and `min_periods=3`, grouped strictly by `Product_ID`. Missing receipt months have quantity zero and participate in subsequent windows. Export initial `NaN` values as empty SMA cells in CSV.

#### Reason
A complete-window SMA is consistent across months; silently using a partial window produces noncomparable figures.

#### Alternatives Considered
Partial-window means were considered, but they change the denominator over the first two months. Dropping those months would violate continuous monthly output.

#### Consequences
SMA is undefined for the first two rows of each product, including zero-activity rows. Downstream consumers must distinguish an empty SMA from a legitimate zero.

---

### Decision: Reject invalid populated inputs and reconcile monthly totals per product

**Decision ID:** `D003` (renumber if already used)
**Backlog:** `BL-P001-000002`
**Date:** `2026-11-16`

#### Context
Silently removing malformed receipts could make descriptive totals incorrect or prevent matching the cleaned source.

#### Decision
Require valid identifiers, dates and finite numeric quantities in nonempty inputs. Preserve receipt frequency using distinct IDs; sum quantities across every valid line within each product-month. Reconcile source versus aggregated quantity independently for each product and write a JSON report. For empty/header-only input, create an empty output with an informative report.

#### Reason
Validation and reconciliation reduce silent data loss or cross-product aggregation; an empty file should be handled predictably.

#### Alternatives Considered
Dropping malformed rows or silently filling invalid quantities with zero was rejected because that would distort the source totals.

#### Consequences
Invalid populated files return a nonzero exit code and must be corrected upstream. Reconciliation uses a small numerical tolerance for floating-point aggregation.
