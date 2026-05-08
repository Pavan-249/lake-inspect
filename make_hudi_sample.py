import os
import json
import time
from pathlib import Path

data_files = list(Path("sample_tables/iceberg_table/data").rglob("*.parquet"))
os.makedirs("sample_tables/hudi_table/.hoodie", exist_ok=True)

now_ms = int(time.time() * 1000)

for i in range(3):
    ts = str(now_ms + i * 60000)
    commit = {
        "operationType": "INSERT" if i == 0 else "UPSERT",
        "totalRecordsWritten": 3000,
        "totalBytesWritten": sum(f.stat().st_size for f in data_files),
        "partitionToWriteStats": {
            str(f.parent.name): [{
                "fileId": f"file-{i}-{j:03d}",
                "path": str(f),
                "totalWriteBytes": f.stat().st_size,
                "numWrites": 300,
                "numUpdateWrites": 0 if i == 0 else 50,
            }] for j, f in enumerate(data_files)
        }
    }
    with open(f"sample_tables/hudi_table/.hoodie/{ts}.commit", "w") as f:
        json.dump(commit, f, indent=2)

# one stuck inflight commit
with open(f"sample_tables/hudi_table/.hoodie/{now_ms + 999999}.commit.inflight", "w") as f:
    f.write("{}")

print(f"Hudi sample created. 3 commits, 1 inflight, {len(data_files)} files.")