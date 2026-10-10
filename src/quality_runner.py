
import pandas as pd
from sqlalchemy import text

from src.db_connection import get_engine
from src.quality_engine import (
    check_missing_customer_email,
    check_duplicate_customer_email,
    check_invalid_product_price,
    check_order_total_mismatch,
    check_payment_mismatch,
    check_return_before_order,
)


ALLOWED_TABLES = {
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "returns",
}


def load_table(table_name, engine):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table not allowed: {table_name}")

    query = text(f"SELECT * FROM {table_name}")

    return pd.read_sql(query, engine)

def save_issues(issues, engine):
    if not issues:
        print("No quality issues found.")
        return

    insert_query = text("""
        INSERT INTO data_quality_issues
        (table_name, record_id, issue_type, severity, details)
        SELECT
            :table_name, :record_id, :issue_type, :severity, :details
        WHERE NOT EXISTS (
            SELECT 1
            FROM data_quality_issues
            WHERE table_name = :table_name
              AND record_id = :record_id
              AND issue_type = :issue_type
              AND details = :details
        )
    """)

    inserted_count = 0

    with engine.begin() as connection:
        for issue in issues:
            result = connection.execute(insert_query, issue)
            inserted_count += result.rowcount

    print(f"New quality issues saved: {inserted_count}")
    print(f"Issues detected in this run: {len(issues)}")

def main():
    engine = get_engine()

    try:
        customers_df = load_table("customers", engine)
        products_df = load_table("products", engine)
        orders_df = load_table("orders", engine)
        order_items_df = load_table("order_items", engine)
        payments_df = load_table("payments", engine)
        returns_df = load_table("returns", engine)

        all_issues = []

        all_issues.extend(
            check_missing_customer_email(customers_df)
        )
        all_issues.extend(
            check_duplicate_customer_email(customers_df)
        )
        all_issues.extend(
            check_invalid_product_price(products_df)
        )
        all_issues.extend(
            check_order_total_mismatch(
                orders_df, order_items_df
            )
        )
        all_issues.extend(
            check_payment_mismatch(
                orders_df, payments_df
            )
        )
        all_issues.extend(
            check_return_before_order(
                orders_df, returns_df
            )
        )

        print("Total Quality Issues:", len(all_issues))
        save_issues(all_issues, engine)

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()