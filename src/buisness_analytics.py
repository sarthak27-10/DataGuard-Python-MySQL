
from pathlib import Path

import pandas as pd

from src.quality_runner import get_engine, load_table


REPORT_DIR = Path("reports")


def load_data(engine):
    """Load the source tables needed for business analytics."""
    tables = [
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "returns",
    ]
    return {table: load_table(table, engine) for table in tables}


def calculate_kpis(data):
    """Calculate headline business performance metrics."""
    orders = data["orders"]
    payments = data["payments"]
    returns = data["returns"]

    completed = orders[
        orders["order_status"].astype(str).str.lower() == "completed"
    ]

    revenue = pd.to_numeric(
        completed["total_amount"], errors="coerce"
    ).sum()

    order_count = len(orders)
    completed_count = len(completed)
    average_order_value = (
        revenue / completed_count if completed_count else 0
    )

    payment_count = len(payments)
    successful_payments = (
        payments["payment_status"].astype(str).str.lower() == "success"
    ).sum()

    payment_success_rate = (
        successful_payments / payment_count * 100
        if payment_count else 0
    )

    returned_orders = returns["order_id"].nunique()
    return_rate = (
        returned_orders / order_count * 100
        if order_count else 0
    )

    return pd.DataFrame([
        {"metric": "total_orders", "value": order_count},
        {"metric": "completed_orders", "value": completed_count},
        {"metric": "completed_order_revenue", "value": round(revenue, 2)},
        {"metric": "average_order_value", "value": round(average_order_value, 2)},
        {"metric": "payment_success_rate_pct", "value": round(payment_success_rate, 2)},
        {"metric": "orders_with_returns_pct", "value": round(return_rate, 2)},
        {"metric": "total_returns", "value": len(returns)},
    ])


def monthly_revenue(data):
    """Calculate completed-order revenue by month."""
    orders = data["orders"].copy()
    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )
    orders["total_amount"] = pd.to_numeric(
        orders["total_amount"], errors="coerce"
    )

    completed = orders[
        orders["order_status"].astype(str).str.lower() == "completed"
    ].dropna(subset=["order_date"])

    completed["month"] = completed["order_date"].dt.to_period("M").astype(str)

    return (
        completed.groupby("month", as_index=False)
        .agg(
            revenue=("total_amount", "sum"),
            completed_orders=("order_id", "nunique"),
        )
        .sort_values("month")
    )


def category_performance(data):
    """Calculate sales value and quantity by product category."""
    items = data["order_items"].copy()
    products = data["products"][["product_id", "category"]].copy()
    orders = data["orders"][["order_id", "order_status"]].copy()

    if items.empty:
        return pd.DataFrame(
            columns=["category", "units_sold", "sales_value"]
        )

    items["quantity"] = pd.to_numeric(items["quantity"], errors="coerce")
    items["unit_price"] = pd.to_numeric(
        items["unit_price"], errors="coerce"
    )
    items["discount"] = pd.to_numeric(
        items["discount"], errors="coerce"
    ).fillna(0)

    items["sales_value"] = (
        items["quantity"] * items["unit_price"] - items["discount"]
    )

    completed_orders = orders[
        orders["order_status"].astype(str).str.lower() == "completed"
    ][["order_id"]]

    sales = (
        items.merge(completed_orders, on="order_id", how="inner")
        .merge(products, on="product_id", how="left")
    )

    return (
        sales.groupby("category", dropna=False, as_index=False)
        .agg(
            units_sold=("quantity", "sum"),
            sales_value=("sales_value", "sum"),
        )
        .sort_values("sales_value", ascending=False)
    )


def customer_rfm(data):
    """Calculate recency, frequency, monetary value, and simple segments."""
    customers = data["customers"][["customer_id", "full_name"]].copy()
    orders = data["orders"].copy()

    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )
    orders["total_amount"] = pd.to_numeric(
        orders["total_amount"], errors="coerce"
    )

    orders = orders[
        orders["order_status"].astype(str).str.lower() == "completed"
    ].dropna(subset=["order_date"])

    if orders.empty:
        return pd.DataFrame(
            columns=[
                "customer_id", "full_name", "recency_days",
                "frequency", "monetary", "segment"
            ]
        )

    reference_date = orders["order_date"].max().normalize() + pd.Timedelta(days=1)

    rfm = (
        orders.groupby("customer_id", as_index=False)
        .agg(
            last_order_date=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("total_amount", "sum"),
        )
    )

    rfm["recency_days"] = (
        reference_date - rfm["last_order_date"].dt.normalize()
    ).dt.days

    rfm = rfm.merge(customers, on="customer_id", how="left")

    def segment_customer(row):
        if row["recency_days"] <= 30 and row["frequency"] >= 3:
            return "Champions"
        if row["recency_days"] <= 60 and row["frequency"] >= 2:
            return "Loyal"
        if row["recency_days"] <= 90:
            return "Potential Loyalists"
        if row["recency_days"] > 180:
            return "At Risk / Lost"
        return "Needs Attention"

    rfm["segment"] = rfm.apply(segment_customer, axis=1)

    return rfm[
        [
            "customer_id", "full_name", "recency_days",
            "frequency", "monetary", "segment"
        ]
    ].sort_values("monetary", ascending=False)


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    try:
        data = load_data(engine)

        reports = {
            "kpi_summary.csv": calculate_kpis(data),
            "monthly_revenue.csv": monthly_revenue(data),
            "category_performance.csv": category_performance(data),
            "customer_rfm.csv": customer_rfm(data),
        }

        for filename, report in reports.items():
            output_path = REPORT_DIR / filename
            report.to_csv(output_path, index=False)
            print(f"\n{filename}")
            print(report.head(10).to_string(index=False))
            print(f"Saved: {output_path}")

        print("\nBusiness analytics completed successfully.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()