
import pandas as pd
from src.data_profiler import profile_dataframe


def test_profile_dataframe():
    df = pd.DataFrame({
        "name": ["Asha", "Ravi", "Asha"],
        "email": ["a@test.com", None, "a@test.com"]
    })

    result = profile_dataframe(df)

    assert result["rows"] == 3
    assert result["columns"] == 2
    assert result["duplicate_rows"] == 1
    assert result["null_percent"]["email"] == 33.33
    assert result["unique_values"]["name"] == 2