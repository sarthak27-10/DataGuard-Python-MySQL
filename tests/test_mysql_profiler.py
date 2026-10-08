import pandas as pd
from src.data_profiler import profile_dataframe
from src.db_connection import get_engine


engine = get_engine()

query = "SELECT * FROM customers"

df = pd.read_sql(query, engine)

result = profile_dataframe(df)

print("Customer Data Profile:")
print(result)