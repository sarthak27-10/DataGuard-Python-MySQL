
import pandas as pd

from src.quality_engine import (
    check_return_before_order,
    check_missing_customer_email,
    check_duplicate_customer_email,
    check_invalid_product_price,
)

from src.quality_engine import (
    check_return_before_order,
    check_missing_customer_email,
    check_duplicate_customer_email,
    check_invalid_product_price,
    check_order_total_mismatch,
)


from src.quality_engine import (
    check_return_before_order,
    check_missing_customer_email,
    check_duplicate_customer_email,
    check_invalid_product_price,
    check_order_total_mismatch,
    check_payment_mismatch,         
)


def test_check_return_before_order():
    orders_df = pd.DataFrame({
        "order_id": [1, 2],
        "order_date": pd.to_datetime([
            "2026-10-10",
            "2026-10-15",
        ]),
    })

    returns_df = pd.DataFrame({
        "return_id": [101, 102],
        "order_id": [1, 2],
        "return_date": pd.to_datetime([
            "2026-10-05",
            "2026-10-20",
        ]),
    })

    issues = check_return_before_order(orders_df, returns_df)

    assert len(issues) == 1
    assert issues[0]["record_id"] == 101
    assert issues[0]["issue_type"] == "RETURN_BEFORE_ORDER"


def test_check_missing_customer_email():
    customers_df = pd.DataFrame({
        "customer_id": [101, 102, 103],
        "email": ["asha@test.com", None, "   "],
    })

    issues = check_missing_customer_email(customers_df)

    assert len(issues) == 2
    assert issues[0]["record_id"] == 102
    assert issues[1]["record_id"] == 103
    assert all(
        issue["issue_type"] == "CUSTOMER_EMAIL_MISSING"
        for issue in issues
    )


    
def test_check_duplicate_customer_email():
    customers_df = pd.DataFrame({
        "customer_id": [101, 102, 103],
        "email": [
            "asha@test.com",
            "asha@test.com",
            "ravi@test.com",
        ],
    })

    issues = check_duplicate_customer_email(customers_df)

    assert len(issues) == 2
    assert {issue["record_id"] for issue in issues} == {101, 102}
    assert all(
        issue["issue_type"] == "CUSTOMER_DUPLICATE_EMAIL"
        for issue in issues
    )


def test_check_invalid_product_price():
    products_df = pd.DataFrame({
        "product_id": [201, 202, 203],
        "price": [100.0, 0.0, -5.0],
    })

    issues = check_invalid_product_price(products_df)

    assert len(issues) == 2
    assert {issue["record_id"] for issue in issues} == {202, 203}
    assert all(
        issue["issue_type"] == "PRODUCT_INVALID_PRICE"
        for issue in issues
    )


def test_check_order_total_mismatch():
    orders_df = pd.DataFrame({
        "order_id": [1, 2],
        "total_amount": [100.0, 50.0],
    })

    order_items_df = pd.DataFrame({
        "order_id": [1, 2],
        "quantity": [2, 1],
        "unit_price": [50.0, 60.0],
        "discount": [0.0, 0.0],
    })

    issues = check_order_total_mismatch(
        orders_df,
        order_items_df,
    )

    assert len(issues) == 1
    assert issues[0]["record_id"] == 2
    assert issues[0]["issue_type"] == "ORDER_TOTAL_MISMATCH"






def test_check_payment_mismatch():
    orders_df = pd.DataFrame({
        "order_id": [1, 2],
        "total_amount": [100.0, 200.0],
    })

    payments_df = pd.DataFrame({
        "order_id": [1, 2, 2],
        "amount": [100.0, 100.0, 50.0],
        "payment_status": ["success", "success", "failed"],
    })

    issues = check_payment_mismatch(orders_df, payments_df)

    assert len(issues) == 1
    assert issues[0]["record_id"] == 2
    assert issues[0]["issue_type"] == "PAYMENT_MISMATCH"
    assert issues[0]["severity"] == "CRITICAL"