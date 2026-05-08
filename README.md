# lake-inspect

Health inspector for Iceberg, Delta, and Hudi lakehouse tables. No Spark, no catalog, no cluster needed.

## Install

```bash
pip install git+https://github.com/yourname/lake-inspect
```

## Usage

```bash
# single table
lake-inspect --path /path/to/table --format iceberg
lake-inspect --path /path/to/table --format delta
lake-inspect --path /path/to/table --format hudi

# auto-detect format and scan entire directory
lake-inspect --scan-dir /path/to/tables

# export as JSON
lake-inspect --path /path/to/table --format iceberg --output json
lake-inspect --path /path/to/table --format iceberg --output json --out-file report.json
```

## What it checks

**Iceberg**
- Snapshot count -- too many slows query planning
- Small files -- impacts read performance
- Schema drift -- too many schema versions
- Partition spec -- missing means full scans

**Delta**
- Commit count -- too many without checkpoint slows reads
- Small files
- Schema changes
- Remove/add file ratio

**Hudi**
- Inflight commits -- stuck or failed writes
- Commit count
- Operation types (insert vs upsert)
- Write sizes -- too small means unbatched writes