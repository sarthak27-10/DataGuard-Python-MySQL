
import pandas as pd
from src.quality_engine import check_return_before_order


def test_check_return_before_order():
    orders_data = {
        "order_id": [1, 2],
        "order_date": pd.to_datetime([
            "2026-10-10",
            "2026-10-15"
        ])
    }

    returns_data = {
        "return_id": [101, 102],
        "order_id": [1, 2],
        "return_date": pd.to_datetime([
            "2026-10-05",
            "2026-10-20"
        ])
    }

    orders_df = pd.DataFrame(orders_data)
    returns_df = pd.DataFrame(returns_data)

    issues = check_return_before_order(
        orders_df,
        returns_df
    )

    assert issues is not None
    assert len(issues) == 1