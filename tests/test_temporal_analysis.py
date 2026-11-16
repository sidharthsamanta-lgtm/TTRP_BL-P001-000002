"""Synthetic tests for gaps, unique receipt counts, SMA, isolation and CLI."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.temporal_analysis import analyse, make_validation_report, read_receipt_lines, run

FIXTURE = Path(__file__).parent / "fixtures" / "supplier_receipt_lines.csv"


def test_missing_months_distinct_receipts_and_sma():
    data = read_receipt_lines(FIXTURE)
    result = analyse(data).set_index(["Product_ID", "Month"])
    assert list(result.loc["P001"].index) == [
        "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"
    ]
    assert result.loc[("P001", "2026-01"), "Receipt_Frequency"] == 1
    assert result.loc[("P001", "2026-01"), "Total_Quantity"] == 10
    for missing_month in ["2026-02", "2026-05"]:
        assert result.loc[("P001", missing_month), "Receipt_Frequency"] == 0
        assert result.loc[("P001", missing_month), "Total_Quantity"] == 0
    assert pd.isna(result.loc[("P001", "2026-01"), "SMA_3M_Quantity"])
    assert pd.isna(result.loc[("P001", "2026-02"), "SMA_3M_Quantity"])
    assert result.loc[("P001", "2026-03"), "SMA_3M_Quantity"] == pytest.approx(40 / 3)
    assert result.loc[("P001", "2026-04"), "SMA_3M_Quantity"] == pytest.approx(50 / 3)
    assert result.loc[("P001", "2026-05"), "SMA_3M_Quantity"] == pytest.approx(50 / 3)
    assert result.loc[("P001", "2026-06"), "SMA_3M_Quantity"] == pytest.approx(60 / 3)
    assert make_validation_report(data, analyse(data))["reconciliation_passed"] is True


def test_multiple_products_isolated_with_dataset_wide_range(tmp_path):
    csv = tmp_path / "two_products.csv"
    csv.write_text(
        "Product_ID,Receipt_ID,Receipt_Date,Quantity\n"
        "A,R1,2026-01-10,10\n"
        "A,R2,2026-03-10,30\n"
        "B,R3,2026-02-10,5\n"
        "B,R4,2026-04-10,8\n",
        encoding="utf-8",
    )
    data = read_receipt_lines(csv)
    summary = analyse(data)
    assert len(summary) == 8  # 2 products x Jan-Apr global dataset range
    a = summary.loc[summary.Product_ID == "A"].set_index("Month")
    b = summary.loc[summary.Product_ID == "B"].set_index("Month")
    assert list(a.Total_Quantity) == [10, 0, 30, 0]
    assert list(b.Total_Quantity) == [0, 5, 0, 8]
    assert a.loc["2026-03", "SMA_3M_Quantity"] == pytest.approx(40 / 3)
    assert b.loc["2026-03", "SMA_3M_Quantity"] == pytest.approx(5 / 3)
    assert make_validation_report(data, summary)["reconciliation_passed"] is True


def test_cli_writes_summary_and_report(tmp_path):
    out, report = tmp_path / "out.csv", tmp_path / "report.json"
    assert run(FIXTURE, out, report) == 0
    assert list(pd.read_csv(out).columns) == [
        "Product_ID", "Month", "Receipt_Frequency", "Total_Quantity", "SMA_3M_Quantity"
    ]
    validation = json.loads(report.read_text())
    assert validation["status"] == "passed"
    assert validation["per_product"][0]["source_quantity"] == 100
    assert validation["zero_activity_rows"] == 2


@pytest.mark.parametrize("content", ["", "Product_ID,Receipt_ID,Receipt_Date,Quantity\n"])
def test_empty_input_is_informative_not_a_failure(tmp_path, caplog, content):
    src = tmp_path / "empty.csv"
    src.write_text(content, encoding="utf-8")
    out, report = tmp_path / "empty_out.csv", tmp_path / "empty_report.json"
    assert run(src, out, report) == 0
    assert pd.read_csv(out).empty
    assert json.loads(report.read_text())["status"] == "empty_input"
    assert "no records" in caplog.text.lower()


def test_invalid_quantity_rejected(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text("Product_ID,Receipt_ID,Receipt_Date,Quantity\nA,R1,2026-01-01,unknown\n")
    with pytest.raises(ValueError, match="Quantity"):
        read_receipt_lines(csv)


def test_reconciliation_flags_tampered_result():
    data = read_receipt_lines(FIXTURE)
    summary = analyse(data)
    summary.loc[0, "Total_Quantity"] += 1
    report = make_validation_report(data, summary)
    assert report["reconciliation_passed"] is False
    assert report["status"] == "failed"
