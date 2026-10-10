
import pandas as pd
from src.data_profiler import profile_dataframe
from src.db_connection import get_engine


def test_mysql_customer_profiler():
    engine = get_engine()

    try:
        with engine.connect() as connection:
            df = pd.read_sql(
                "SELECT * FROM customers LIMIT 10",
                connection
            )

        result = profile_dataframe(df)

        assert result is not None
        assert len(result) > 0

    finally:
        engine.dispose()