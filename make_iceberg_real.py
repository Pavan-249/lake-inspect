from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType, DoubleType, TimestampType
import pyarrow as pa
import numpy as np
import pandas as pd

import os
os.makedirs("sample_tables/iceberg_real", exist_ok=True)

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

catalog = SqlCatalog(
    "default",
    **{
        "uri": "sqlite:///sample_tables/iceberg_real/catalog.db",
        "warehouse": "sample_tables/iceberg_real",
    }
)

catalog.create_namespace("nyc")

schema = Schema(
    NestedField(1, "tpep_pickup_datetime", StringType()),
    NestedField(2, "passenger_count", DoubleType()),
    NestedField(3, "trip_distance", DoubleType()),
    NestedField(4, "fare_amount", DoubleType()),
    NestedField(5, "trip_date", StringType()),
)

table = catalog.create_table("nyc.taxi", schema=schema)

arrow_table = pa.Table.from_pandas(df)

# 3 real commits
table.append(arrow_table.slice(0, 3000))
table.append(arrow_table.slice(3000, 6000))
table.append(arrow_table.slice(6000, 10000))

print(f"Real Iceberg table written.")
print(f"Snapshots: {len(list(table.snapshots()))}")
print(f"Location: sample_tables/iceberg_real")