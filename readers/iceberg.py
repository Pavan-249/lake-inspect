import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

THRESHOLDS = {
    "snapshot_warn": 10,
    "snapshot_critical": 100,
    "small_file_bytes": 10 * 1024 * 1024,
    "small_file_warn_pct": 0.5,
}

def load_metadata(table_path: str) -> dict:
    meta_dir = Path(table_path) / "metadata"
    
    # try version-hint.text first (hand-crafted tables)
    hint_file = meta_dir / "version-hint.text"
    if hint_file.exists():
        version = hint_file.read_text().strip()
        with open(meta_dir / f"v{version}.metadata.json") as f:
            return json.load(f)
    
    # real pyiceberg tables use 00000-xxx.metadata.json -- pick the latest
    meta_files = sorted(meta_dir.glob("*.metadata.json"))
    if not meta_files:
        raise FileNotFoundError(f"No metadata files found in {meta_dir}")
    with open(meta_files[-1]) as f:
        return json.load(f)

def check_snapshots(metadata: dict) -> list:
    snapshots = metadata.get("snapshots", [])
    count = len(snapshots)
    if count >= THRESHOLDS["snapshot_critical"]:
        return [("CRITICAL", f"{count} snapshots -- query planner reads all of them. Run expire_snapshots().")]
    elif count >= THRESHOLDS["snapshot_warn"]:
        return [("WARN", f"{count} snapshots -- consider expire_snapshots().")]
    return [("OK", f"{count} snapshot(s)")]

def check_small_files(table_path: str) -> list:
    data_dir = Path(table_path) / "data"
    all_files = list(data_dir.rglob("*.parquet"))
    if not all_files:
        return [("WARN", "No data files found.")]
    small = [f for f in all_files if f.stat().st_size < THRESHOLDS["small_file_bytes"]]
    pct = len(small) / len(all_files)
    avg_mb = sum(f.stat().st_size for f in all_files) / len(all_files) / 1024 / 1024
    if pct >= THRESHOLDS["small_file_warn_pct"]:
        return [("WARN", f"{len(small)}/{len(all_files)} files under 10MB ({pct:.0%}). Avg: {avg_mb:.2f} MB.")]
    return [("OK", f"{len(all_files)} files, avg {avg_mb:.2f} MB")]

def check_schema_versions(metadata: dict) -> list:
    count = len(metadata.get("schemas", []))
    if count > 3:
        return [("WARN", f"{count} schema versions -- high schema drift.")]
    return [("OK", f"{count} schema version(s)")]

def check_partition_spec(metadata: dict) -> list:
    specs = metadata.get("partition-specs", [])
    if not specs or not specs[0].get("fields"):
        return [("WARN", "No partition spec -- full scans on every query.")]
    fields = [f["name"] for f in specs[0]["fields"]]
    return [("OK", f"Partitioned by: {', '.join(fields)}")]

def scan(table_path: str, output=None, out_file=None):
    metadata = load_metadata(table_path)
    findings = (
        check_snapshots(metadata)
        + check_small_files(table_path)
        + check_schema_versions(metadata)
        + check_partition_spec(metadata)
    )
    console = Console()
    table = Table(title=f"Iceberg -- {table_path}", show_header=True)
    table.add_column("Status", width=10)
    table.add_column("Finding")
    colors = {"OK": "green", "WARN": "yellow", "CRITICAL": "red"}
    for level, msg in findings:
        table.add_row(f"[{colors[level]}]{level}[/{colors[level]}]", msg)
    console.print(table)
    warnings = sum(1 for l, _ in findings if l in ("WARN", "CRITICAL"))
    if warnings:
        console.print(f"[yellow]{warnings} issue(s) found.[/yellow]")
    if output == "json":
        report = {
            "format": "iceberg",
            "path": table_path,
            "findings": [{"level": l, "message": m} for l, m in findings],
            "total_issues": warnings,
        }
        out = json.dumps(report, indent=2)
        if out_file:
            with open(out_file, "w") as f:
                f.write(out)
        else:
            print(out)