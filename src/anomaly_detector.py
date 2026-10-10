
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.quality_runner import get_engine, load_table


REPORT_DIR = Path("reports")
DEVIATION_THRESHOLD = 30.0
MINIMUM_HISTORY = 3


def monthly_series(df, date_column, value_column=None):
    """Aggregate records into monthly counts or sums."""
    if df.empty:
        return pd.Series(dtype=float)

    data = df.copy()
    data[date_column] = pd.to_datetime(
        data[date_column], errors="coerce"
    )
    data = data.dropna(subset=[date_column])

    if data.empty:
        return pd.Series(dtype=float)

    data["month"] = data[date_column].dt.to_period("M")

    if value_column:
        data[value_column] = pd.to_numeric(
            data[value_column], errors="coerce"
        ).fillna(0)
        result = data.groupby("month")[value_column].sum()
    else:
        result = data.groupby("month").size()

    if result.empty:
        return result

    complete_months = pd.period_range(
        result.index.min(), result.index.max(), freq="M"
    )
    return result.reindex(complete_months, fill_value=0).astype(float)


def build_metrics(orders, payments, returns):
    """Build monthly revenue, payment-failure, and return metrics."""
    completed = orders[
        orders["order_status"].astype(str).str.lower() == "completed"
    ].copy()

    revenue = monthly_series(
        completed, "order_date", "total_amount"
    )
    failure_rate = pd.Series(dtype=float)

    if not payments.empty:
        payment_data = payments.copy()
        payment_data["payment_date"] = pd.to_datetime(
            payment_data["payment_date"], errors="coerce"
        )
        payment_data = payment_data.dropna(subset=["payment_date"])
        payment_data["month"] = (
            payment_data["payment_date"].dt.to_period("M")
        )
        payment_data["failed"] = (
            payment_data["payment_status"].astype(str).str.lower()
            == "failed"
        ).astype(int)

        if not payment_data.empty:
            grouped = payment_data.groupby("month").agg(
                total=("payment_id", "count"),
                failures=("failed", "sum"),
            )
            failure_rate = (
                grouped["failures"] / grouped["total"] * 100
            )
            all_months = pd.period_range(
                grouped.index.min(), grouped.index.max(), freq="M"
            )
            failure_rate = failure_rate.reindex(all_months)

    return_count = monthly_series(returns, "return_date")

    return {
        "monthly_revenue": revenue,
        "payment_failure_rate_pct": failure_rate,
        "monthly_returns": return_count,
    }


def detect_anomalies(metrics):
    """Compare each month with the mean of the previous three months."""
    findings = []

    for metric_name, series in metrics.items():
        series = series.sort_index()

        for index in range(MINIMUM_HISTORY, len(series)):
            actual = series.iloc[index]
            history = series.iloc[index - MINIMUM_HISTORY:index]
            expected = history.mean()

            if pd.isna(actual) or pd.isna(expected) or expected <= 0:
                continue

            deviation = (actual - expected) / expected * 100

            if abs(deviation) < DEVIATION_THRESHOLD:
                continue

            severity = "HIGH" if abs(deviation) >= 60 else "MEDIUM"

            findings.append({
                "metric_name": metric_name,
                "metric_date": series.index[index].start_time.date(),
                "expected_value": round(float(expected), 2),
                "actual_value": round(float(actual), 2),
                "deviation_pct": round(float(deviation), 2),
                "severity": severity,
            })

    return pd.DataFrame(findings)


def save_anomalies(engine, anomalies):
    """Save new findings without duplicating identical records."""
    saved = 0

    if anomalies.empty:
        return saved

    insert_sql = text("""
        INSERT INTO anomaly_results
        (
            metric_name, metric_date, expected_value,
            actual_value, deviation_pct, severity
        )
        SELECT
            :metric_name, :metric_date, :expected_value,
            :actual_value, :deviation_pct, :severity
        WHERE NOT EXISTS (
            SELECT 1
            FROM anomaly_results
            WHERE metric_name = :metric_name
              AND metric_date = :metric_date
              AND actual_value = :actual_value
              AND deviation_pct = :deviation_pct
        )
    """)

    with engine.begin() as connection:
        for record in anomalies.to_dict(orient="records"):
            result = connection.execute(insert_sql, record)
            saved += result.rowcount

    return saved


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    engine = get_engine()

    try:
        orders = load_table("orders", engine)
        payments = load_table("payments", engine)
        returns = load_table("returns", engine)

        metrics = build_metrics(orders, payments, returns)
        anomalies = detect_anomalies(metrics)

        output_path = REPORT_DIR / "anomaly_report.csv"
        anomalies.to_csv(output_path, index=False)

        saved = save_anomalies(engine, anomalies)

        print(f"Anomalies detected: {len(anomalies)}")
        print(f"New anomaly records saved: {saved}")

        if anomalies.empty:
            print("No anomalies met the configured threshold.")
        else:
            print(anomalies.to_string(index=False))

        print(f"Report saved: {output_path}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()