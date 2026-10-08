import pandas as pd
from sqlalchemy import text

from src.db_connection import get_engine
from src.quality_engine import (
    check_missing_customer_email,
    check_duplicate_customer_email,
    check_invalid_product_price,
    check_order_total_mismatch,
    check_payment_mismatch,
    check_return_before_order
)


engine = get_engine()


def load_table(table_name):
    return pd.read_sql(
        f"SELECT * FROM {table_name}",
        engine
    )


def save_issues(issues):
    if not issues:
        print("No quality issues found.")
        return

    with engine.begin() as connection:
        for issue in issues:
            connection.execute(
                text("""
                    INSERT INTO data_quality_issues
                    (table_name, record_id, issue_type, severity, details)
                    VALUES
                    (:table_name, :record_id, :issue_type, :severity, :details)
                """),
                issue
            )

    print(f"{len(issues)} quality issues saved to database.")


customers_df = load_table("customers")
products_df = load_table("products")
orders_df = load_table("orders")
order_items_df = load_table("order_items")
payments_df = load_table("payments")
returns_df = load_table("returns")


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
        orders_df,
        order_items_df
    )
)

all_issues.extend(
    check_payment_mismatch(
        orders_df,
        payments_df
    )
)

all_issues.extend(
    check_return_before_order(
        orders_df,
        returns_df
    )
)


print("Total Quality Issues:", len(all_issues))

save_issues(all_issues)