import os
import json
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# --- pull NYC taxi data directly ---
print("Downloading NYC Taxi data...")
url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
df = pd.read_parquet(url)

# keep it small and clean
df = df[["tpep_pickup_datetime", "tpep_dropoff_datetime", "passenger_count", "trip_distance", "fare_amount", "tip_amount", "total_amount"]].dropna()
df = df.head(10000)
df["trip_date"] = df["tpep_pickup_datetime"].dt.date.astype(str)

print(f"Got {len(df)} rows, {len(df.columns)} columns")

# --- create folder structure ---
os.makedirs("sample_tables/iceberg_table/data", exist_ok=True)
os.makedirs("sample_tables/iceberg_table/metadata", exist_ok=True)

# --- write real Parquet files partitioned by date ---
table = pa.Table.from_pandas(df)
pq.write_to_dataset(table, root_path="sample_tables/iceberg_table/data", partition_cols=["trip_date"])
print("Parquet files written.")

# --- write Iceberg metadata on top ---
now_ms = int(time.time() * 1000)

metadata = {
    "format-version": 2,
    "table-uuid": "nyc-taxi-iceberg-001",
    "last-updated-ms": now_ms,
    "current-schema-id": 0,
    "schemas": [{
        "schema-id": 0,
        "fields": [
            {"id": 1, "name": "tpep_pickup_datetime",  "type": "timestamptz"},
            {"id": 2, "name": "tpep_dropoff_datetime", "type": "timestamptz"},
            {"id": 3, "name": "passenger_count",       "type": "double"},
            {"id": 4, "name": "trip_distance",         "type": "double"},
            {"id": 5, "name": "fare_amount",           "type": "double"},
            {"id": 6, "name": "tip_amount",            "type": "double"},
            {"id": 7, "name": "total_amount",          "type": "double"},
        ]
    }],
    "partition-specs": [{
        "spec-id": 0,
        "fields": [
            {"source-id": 1, "field-id": 1000, "name": "trip_date", "transform": "day"}
        ]
    }],
    "current-snapshot-id": 1,
    "snapshots": [
        {"snapshot-id": 1, "timestamp-ms": now_ms, "summary": {"operation": "append", "total-records": str(len(df))}}
    ]
}

with open("sample_tables/iceberg_table/metadata/v1.metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

with open("sample_tables/iceberg_table/metadata/version-hint.text", "w") as f:
    f.write("1")

print("Done! Run: lakehouse-lint scan --path sample_tables/iceberg_table --format iceberg")