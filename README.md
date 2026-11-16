
# Receipt Volume Analysis — TTRP Project Workspace

This repository is a persistent TTRP engineering workspace. It currently includes a temporal receipt-volume analysis capability for the assigned receipt-line dataset. Previously accepted project functionality must be preserved when integrating this backlog into an existing resident repository.

Start with the permanent [Resident Guide](TTRP_GUIDE.md). The original workspace instructions are preserved in [docs/README_ORIGINAL.md](docs/README_ORIGINAL.md).

## Project overview

The implemented capability reads cleaned `supplier_receipt_lines.csv` data and produces descriptive monthly receipt-frequency and quantity trends **independently for each product**. It computes a strict trailing 3-calendar-month SMA of quantities. It does not estimate supplier performance, costs, delivery timeliness or future demand.

The broader project overview and requirements of earlier backlogs are not available in this standalone package; maintain them in your existing repository README when merging.

## Current backlog

- **Backlog code:** `BL-P001-000002`
- **Title:** Build a Temporal Receipt Analysis Module
- **Implemented behaviour:** group receipts by `Product_ID` and calendar month, count distinct `Receipt_ID` values, sum `Quantity`, add missing months with zero activity, compute a trailing 3-month SMA for each product, and generate a reconciliation report.

## Requirements and configuration

- Python 3.10+ recommended (type hints use modern union syntax).
- Dependencies: `pandas`, `numpy`; `pytest` is included for testing. See `requirements.txt`.
- Input file: `supplier_receipt_lines.csv` (not supplied; place your real cleaned source at the repository root or point `--input` elsewhere).
- Mandatory columns: `Product_ID`, `Receipt_ID`, `Receipt_Date`, `Quantity`.
- Credentials or external services: none.

Product and receipt IDs are treated as strings to preserve leading zeros. `Receipt_Date` must be parseable, preferably `YYYY-MM-DD`. Quantity must be numeric and finite; invalid nonempty input is rejected, not silently dropped. Duplicate receipt IDs within one product/month count once toward frequency; all valid receipt lines contribute to quantity.

## Setup

From the repository root:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python src/temporal_analysis.py --input supplier_receipt_lines.csv --output outputs/monthly_receipt_summary.csv --report outputs/validation_report.json
```

You may substitute another `--input` path. Output directories are created automatically. The summary CSV contains one row for every `(Product_ID, YYYY-MM)` pair within the **dataset-wide** minimum/maximum month range, even when the product has no receipts in a month.

| Output field | Interpretation |
| --- | --- |
| `Product_ID` | Product identifier; quantities are never summed across products |
| `Month` | Month in `YYYY-MM` notation |
| `Receipt_Frequency` | Distinct receipts for the product and month |
| `Total_Quantity` | Sum of receipt-line quantities for the product/month; zero in missing months |
| `SMA_3M_Quantity` | Mean quantity for current month and two previous calendar months; empty/`NaN` for each product's first two months |

The JSON validation report gives one reconciliation result per product (`source_quantity`, `monthly_quantity_sum`, `difference`, `reconciled`), plus an overall `status`. Empty inputs produce an informative warning, an empty summary and `status: empty_input` without a crash.

## Verify

Run all automated tests:

```bash
python -m pytest -q
```

Run the analysis on the included **synthetic fixture only**:

```bash
python src/temporal_analysis.py --input tests/fixtures/supplier_receipt_lines.csv --output outputs/monthly_receipt_summary.csv --report outputs/validation_report.json
```

The fixture has receipts in January, March, April and June, with zero-activity February/May rows in the output. Quantity totals for the sample product reconcile to 100. The tests also cover repeated receipt IDs, independent product series, first-two-month SMA, empty files, invalid quantities, and deliberate reconciliation failure. Example outputs are available under [`evidence/BL-P001-000002/`](evidence/BL-P001-000002/).

**Real-data validation remains pending** because the actual cleaned dataset was not supplied with this package.

## Repository structure

- `src/temporal_analysis.py` — implementation and CLI
- `tests/test_temporal_analysis.py` — automated tests
- `tests/fixtures/supplier_receipt_lines.csv` — synthetic fixture, not real resident data
- `docs/reflections/BL-P001-000002.md` — backlog reflection in the standard TTRP 10-section format
- `docs/reflections/REFLECTION_TEMPLATE.md` — permanent TTRP reflection template
- `docs/DECISIONS.md` — durable engineering decisions using stable IDs
- `evidence/BL-P001-000002/` — synthetic example results
- `TTRP_GUIDE.md` — permanent resident instructions

## Known limitations

- It expects a cleaned, valid CSV and does not infer physical units or repair malformed records.
- No source data was supplied, so only synthetic fixture reconciliation is verified.
- Source timestamps with mixed timezone conventions are not explicitly normalised into a single business timezone.
- It does not run submitted code as part of any TTRP evaluator; run the included tests yourself.
- No predictive modelling, financial analysis, dashboard or API endpoint is implemented.

## Backlog handoffs

- [`BL-P001-000002` — Temporal Receipt Analysis](docs/reflections/BL-P001-000002.md)

Keep older handoff links and earlier accepted work when merging this module into your existing project repository.
