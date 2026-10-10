
from pathlib import Path

import pandas as pd

from src.quality_runner import get_engine, load_table

REPORT_DIR = Path("reports")


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    try:
        tables = {
            name: load_table(name, engine)
            for name in [
                "customers",
                "products",
                "orders",
                "order_items",
                "payments",
                "returns",
            ]
        }

        customers = tables["customers"]
        orders = tables["orders"].copy()
        items = tables["order_items"].copy()
        products = tables["products"][["product_id", "category"]]
        payments = tables["payments"]
        returns = tables["returns"]

        orders["total_amount"] = pd.to_numeric(
            orders["total_amount"], errors="coerce"
        )
        orders["order_date"] = pd.to_datetime(
            orders["order_date"], errors="coerce"
        )

        completed = orders[
            orders["order_status"].astype(str).str.lower() == "completed"
        ].copy()

        successful_payments = (
            payments["payment_status"].astype(str).str.lower() == "success"
        ).sum()

        payment_success_rate = (
            successful_payments / len(payments) * 100
            if len(payments) else 0
        )

        return_rate = (
            returns["order_id"].nunique() / len(orders) * 100
            if len(orders) else 0
        )

        kpis = pd.DataFrame([
            {"metric": "total_orders", "value": len(orders)},
            {"metric": "completed_orders", "value": len(completed)},
            {
                "metric": "completed_order_revenue",
                "value": round(completed["total_amount"].sum(), 2),
            },
            {
                "metric": "average_order_value",
                "value": round(
                    completed["total_amount"].mean(), 2
                ) if not completed.empty else 0,
            },
            {
                "metric": "payment_success_rate_pct",
                "value": round(payment_success_rate, 2),
            },
            {
                "metric": "orders_with_returns_pct",
                "value": round(return_rate, 2),
            },
            {"metric": "total_customers", "value": len(customers)},
            {"metric": "total_returns", "value": len(returns)},
        ])

        completed["month"] = completed["order_date"].dt.to_period("M").astype(str)
        monthly = (
            completed.groupby("month", as_index=False)
            .agg(
                revenue=("total_amount", "sum"),
                completed_orders=("order_id", "nunique"),
            )
            .sort_values("month")
        )

        if items.empty:
            category_report = pd.DataFrame(
                columns=["category", "units_sold", "sales_value"]
            )
        else:
            items["quantity"] = pd.to_numeric(
                items["quantity"], errors="coerce"
            )
            items["unit_price"] = pd.to_numeric(
                items["unit_price"], errors="coerce"
            )
            items["discount"] = pd.to_numeric(
                items["discount"], errors="coerce"
            ).fillna(0)

            items["sales_value"] = (
                items["quantity"] * items["unit_price"] - items["discount"]
            )

            category_report = (
                items.merge(
                    completed[["order_id"]], on="order_id", how="inner"
                )
                .merge(products, on="product_id", how="left")
                .groupby("category", dropna=False, as_index=False)
                .agg(
                    units_sold=("quantity", "sum"),
                    sales_value=("sales_value", "sum"),
                )
                .sort_values("sales_value", ascending=False)
            )

        if completed.empty:
            rfm = pd.DataFrame(
                columns=[
                    "customer_id", "full_name", "recency_days",
                    "frequency", "monetary", "segment"
                ]
            )
        else:
            reference_date = (
                completed["order_date"].max().normalize()
                + pd.Timedelta(days=1)
            )

            rfm = (
                completed.groupby("customer_id", as_index=False)
                .agg(
                    last_order_date=("order_date", "max"),
                    frequency=("order_id", "nunique"),
                    monetary=("total_amount", "sum"),
                )
            )

            rfm["recency_days"] = (
                reference_date - rfm["last_order_date"].dt.normalize()
            ).dt.days

            rfm = rfm.merge(
                customers[["customer_id", "full_name"]],
                on="customer_id",
                how="left",
            )

            def assign_segment(row):
                if row["recency_days"] <= 30 and row["frequency"] >= 3:
                    return "Champions"
                if row["recency_days"] <= 60 and row["frequency"] >= 2:
                    return "Loyal"
                if row["recency_days"] <= 90:
                    return "Potential Loyalists"
                if row["recency_days"] > 180:
                    return "At Risk / Lost"
                return "Needs Attention"

            rfm["segment"] = rfm.apply(assign_segment, axis=1)
            rfm = rfm[
                [
                    "customer_id", "full_name", "recency_days",
                    "frequency", "monetary", "segment"
                ]
            ].sort_values("monetary", ascending=False)

        reports = {
            "kpi_summary.csv": kpis,
            "monthly_revenue.csv": monthly,
            "category_performance.csv": category_report,
            "customer_rfm.csv": rfm,
        }

        for filename, dataframe in reports.items():
            output_path = REPORT_DIR / filename
            dataframe.to_csv(output_path, index=False)
            print(f"\n--- {filename} ---")
            print(dataframe.head(10).to_string(index=False))
            print(f"Saved: {output_path}")

        print("\nBusiness analytics completed successfully.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()