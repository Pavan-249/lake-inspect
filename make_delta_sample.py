from deltalake.writer import write_deltalake
import pandas as pd
import numpy as np

np.random.seed(42)
n = 10000
base_date = pd.Timestamp("2024-01-15")
pickup_times = [base_date + pd.Timedelta(minutes=int(m)) for m in np.random.randint(0, 43200, n)]

df = pd.DataFrame({
    "tpep_pickup_datetime": [str(t) for t in pickup_times],
    "passenger_count": np.random.choice([1, 2, 3, 4], n).astype(float),
    "trip_distance": np.round(np.random.exponential(3, n), 2),
    "fare_amount": np.round(np.random.uniform(5, 80, n), 2),
    "trip_date": [t.date().isoformat() for t in pickup_times],
})

# 3 real commits
write_deltalake("sample_tables/delta_table_real", df.head(3000), partition_by=["trip_date"])
write_deltalake("sample_tables/delta_table_real", df.iloc[3000:6000], partition_by=["trip_date"], mode="append")
write_deltalake("sample_tables/delta_table_real", df.iloc[6000:], partition_by=["trip_date"], mode="append")

print("Real Delta table written with 3 commits.")