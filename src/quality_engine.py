import pandas as pd


def check_missing_customer_email(df):
    issues = []

    for _, row in df.iterrows():
        if pd.isna(row["email"]) or str(row["email"]).strip() == "":
            issues.append({
                "table_name": "customers",
                "record_id": row["customer_id"],
                "issue_type": "CUSTOMER_EMAIL_MISSING",
                "severity": "MEDIUM",
                "details": "Customer email is missing"
            })

    return issues


def check_duplicate_customer_email(df):
    issues = []

    duplicate_emails = df[
        df["email"].notna() &
        df["email"].duplicated(keep=False)
    ]

    for _, row in duplicate_emails.iterrows():
        issues.append({
            "table_name": "customers",
            "record_id": row["customer_id"],
            "issue_type": "CUSTOMER_DUPLICATE_EMAIL",
            "severity": "HIGH",
            "details": f"Duplicate email found: {row['email']}"
        })

    return issues



def check_invalid_product_price(df):
    issues = []

    invalid_products = df[
        df["price"].isna() | (df["price"] <= 0)
    ]

    for _, row in invalid_products.iterrows():
        issues.append({
            "table_name": "products",
            "record_id": row["product_id"],
            "issue_type": "PRODUCT_INVALID_PRICE",
            "severity": "CRITICAL",
            "details": f"Invalid product price: {row['price']}"
        })

    return issues


def check_order_total_mismatch(orders_df, order_items_df):
    issues = []

    item_totals = (
        order_items_df
        .assign(
            calculated_amount=lambda x:
            x["quantity"] * x["unit_price"] - x["discount"]
        )
        .groupby("order_id")["calculated_amount"]
        .sum()
    )

    for _, order in orders_df.iterrows():
        order_id = order["order_id"]
        expected_total = item_totals.get(order_id, 0)

        if round(order["total_amount"], 2) != round(expected_total, 2):
            issues.append({
                "table_name": "orders",
                "record_id": order_id,
                "issue_type": "ORDER_TOTAL_MISMATCH",
                "severity": "HIGH",
                "details": (
                    f"Order total: {order['total_amount']}, "
                    f"Calculated total: {expected_total}"
                )
            })

    return issues

def check_payment_mismatch(orders_df, payments_df):
    issues = []

    successful_payments = payments_df[
        payments_df["payment_status"].str.lower() == "success"
    ]

    payment_totals = (
        successful_payments
        .groupby("order_id")["amount"]
        .sum()
    )

    for _, order in orders_df.iterrows():
        order_id = order["order_id"]
        order_total = order["total_amount"]
        payment_total = payment_totals.get(order_id, 0)

        if round(order_total, 2) != round(payment_total, 2):
            issues.append({
                "table_name": "payments",
                "record_id": order_id,
                "issue_type": "PAYMENT_MISMATCH",
                "severity": "CRITICAL",
                "details": (
                    f"Order total: {order_total}, "
                    f"Successful payment total: {payment_total}"
                )
            })

    return issues


def check_return_before_order(orders_df, returns_df):
    issues = []

    order_dates = orders_df.set_index("order_id")["order_date"]

    for _, return_row in returns_df.iterrows():
        order_id = return_row["order_id"]

        if order_id in order_dates.index:
            order_date = order_dates[order_id]
            return_date = return_row["return_date"]

            if return_date < order_date:
                issues.append({
                    "table_name": "returns",
                    "record_id": return_row["return_id"],
                    "issue_type": "RETURN_BEFORE_ORDER",
                    "severity": "HIGH",
                    "details": (
                        f"Return date: {return_date}, "
                        f"Order date: {order_date}"
                    )
                })

    return issues