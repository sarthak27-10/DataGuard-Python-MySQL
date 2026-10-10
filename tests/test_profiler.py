import pandas as pd
from src.data_profiler import profile_dataframe


def test_profile_dataframe():
    data = {
        "name": ["Sarthak", "Akash", "Sarthak", None],
        "age": [23, 22, 23, 25],
        "city": ["Pune", "Mumbai", "Pune", None]
    }

    df = pd.DataFrame(data)
    result = profile_dataframe(df)

    assert result is not None
    assert len(result) > 0