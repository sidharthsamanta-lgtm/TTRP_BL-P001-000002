"""Monthly per-product receipt volume analysis.

Output grain: Product_ID x Month (YYYY-MM), including zero-activity months
for *every* observed product across the dataset-wide month range.

No quantities are combined across different Product_ID values.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("temporal_analysis")
REQUIRED_COLUMNS = ("Product_ID", "Receipt_ID", "Receipt_Date", "Quantity")
OUTPUT_COLUMNS = (
    "Product_ID", "Month", "Receipt_Frequency", "Total_Quantity", "SMA_3M_Quantity"
)


def read_receipt_lines(path: str | Path) -> pd.DataFrame:
    """Read and validate receipt lines; accept truly empty or header-only files."""
    try:
        data = pd.read_csv(
            path,
            dtype={"Product_ID": "string", "Receipt_ID": "string"},
            low_memory=False,
        )
    except pd.errors.EmptyDataError:
        LOGGER.warning("Input file is empty: %s. No records to analyse.", path)
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    absent = [name for name in REQUIRED_COLUMNS if name not in data.columns]
    if absent:
        raise ValueError("Missing required column(s): " + ", ".join(absent))

    data = data.loc[:, REQUIRED_COLUMNS].copy()
    if data.empty:
        LOGGER.warning("Input has no receipt rows: %s. No records to analyse.", path)
        return data

    for column in ("Product_ID", "Receipt_ID"):
        data[column] = data[column].str.strip()
        invalid = data[column].isna() | data[column].eq("")
        if invalid.any():
            raise ValueError(f"{column} is blank on {int(invalid.sum())} row(s).")

    # 'mixed' handles conventional date/datetime strings; ISO 8601 is recommended.
    dates = pd.to_datetime(data["Receipt_Date"], errors="coerce", format="mixed")
    if dates.isna().any():
        raise ValueError(
            f"Receipt_Date is missing or invalid on {int(dates.isna().sum())} row(s)."
        )
    if isinstance(dates.dtype, pd.DatetimeTZDtype):
        # Preserve the calendar date in the source's own time zone.
        dates = dates.dt.tz_localize(None)
    data["Receipt_Date"] = dates

    quantities = pd.to_numeric(data["Quantity"], errors="coerce")
    invalid_quantity = quantities.isna() | ~np.isfinite(quantities.astype(float))
    if invalid_quantity.any():
        raise ValueError(
            f"Quantity is missing or nonnumeric on {int(invalid_quantity.sum())} row(s)."
        )
    data["Quantity"] = quantities.astype(float)
    return data


def analyse(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per product/month and compute a strict trailing 3-month SMA.

    For the first two months of *each* product, SMA_3M_Quantity is NaN.
    Missing months are represented by Receipt_Frequency=0 and Total_Quantity=0.
    The common month range uses the min/max dates from the entire input dataset.
    """
    if data.empty:
        return pd.DataFrame(columns=list(OUTPUT_COLUMNS))

    source = data.copy()
    source["Month"] = source["Receipt_Date"].dt.to_period("M")
    monthly = source.groupby(["Product_ID", "Month"], observed=True).agg(
        Receipt_Frequency=("Receipt_ID", "nunique"),
        Total_Quantity=("Quantity", "sum"),
    )

    periods = pd.period_range(source["Month"].min(), source["Month"].max(), freq="M")
    products = sorted(source["Product_ID"].unique().tolist())
    complete_index = pd.MultiIndex.from_product(
        [products, periods], names=["Product_ID", "Month"]
    )
    monthly = monthly.reindex(complete_index, fill_value=0).reset_index()
    monthly["Receipt_Frequency"] = monthly["Receipt_Frequency"].astype("int64")
    monthly["Total_Quantity"] = monthly["Total_Quantity"].astype(float)
    monthly["SMA_3M_Quantity"] = monthly.groupby("Product_ID", sort=False)[
        "Total_Quantity"
    ].transform(lambda group: group.rolling(window=3, min_periods=3).mean())
    monthly["Month"] = monthly["Month"].astype(str)
    return monthly.loc[:, OUTPUT_COLUMNS]


def make_validation_report(data: pd.DataFrame, summary: pd.DataFrame) -> dict:
    """Return reconciliation details against original input quantities."""
    if data.empty:
        return {
            "status": "empty_input", "reconciliation_passed": None,
            "message": "No receipt records were provided; nothing to reconcile.",
            "source_rows": 0, "summary_rows": 0, "products": 0,
            "months": {"first": None, "last": None},
            "zero_activity_rows": 0, "per_product": [],
        }

    source_totals = data.groupby("Product_ID", observed=True)["Quantity"].sum()
    summary_totals = summary.groupby("Product_ID", observed=True)["Total_Quantity"].sum()
    breakdown = []
    for product, original in source_totals.items():
        result = float(summary_totals.loc[product])
        original = float(original)
        matched = bool(np.isclose(original, result, rtol=1e-10, atol=1e-8))
        breakdown.append({
            "Product_ID": str(product),
            "source_quantity": original,
            "monthly_quantity_sum": result,
            "difference": result - original,
            "reconciled": matched,
        })

    passed = all(item["reconciled"] for item in breakdown)
    return {
        "status": "passed" if passed else "failed",
        "reconciliation_passed": passed,
        "source_rows": int(len(data)),
        "summary_rows": int(len(summary)),
        "products": int(data["Product_ID"].nunique()),
        "months": {
            "first": str(summary["Month"].min()),
            "last": str(summary["Month"].max()),
        },
        "zero_activity_rows": int((summary["Receipt_Frequency"] == 0).sum()),
        "per_product": breakdown,
    }


def run(input_path: str | Path, output_path: str | Path, report_path: str | Path) -> int:
    input_path, output_path, report_path = map(Path, (input_path, output_path, report_path))
    if not input_path.exists():
        LOGGER.error("Input file does not exist: %s", input_path)
        return 2
    try:
        data = read_receipt_lines(input_path)
        summary = analyse(data)
        report = make_validation_report(data, summary)
    except (ValueError, pd.errors.ParserError, TypeError) as exc:
        LOGGER.error("Input validation failed: %s", exc)
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    LOGGER.info("Wrote %s row(s) to %s", len(summary), output_path)
    LOGGER.info("Validation status: %s. Report: %s", report["status"], report_path)
    return 0 if report["reconciliation_passed"] is not False else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="supplier_receipt_lines.csv", help="Source receipt-line CSV")
    parser.add_argument("--output", default="outputs/monthly_receipt_summary.csv", help="Output summary CSV")
    parser.add_argument("--report", default="outputs/validation_report.json", help="Output validation JSON")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    return run(args.input, args.output, args.report)


if __name__ == "__main__":
    sys.exit(main())
