import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

def load_commits(table_path: str) -> tuple:
    hoodie_dir = Path(table_path) / ".hoodie"
    commits = []
    inflight = []
    for f in sorted(hoodie_dir.iterdir()):
        if f.suffix == ".inflight":
            inflight.append(f)
        elif f.suffix == ".commit":
            with open(f) as fh:
                commits.append(json.load(fh))
    return commits, inflight

def check_inflight(inflight: list) -> list:
    if inflight:
        return [("WARN", f"{len(inflight)} inflight commit(s) -- a write may be stuck or failed.")]
    return [("OK", "No inflight commits")]

def check_commit_count(commits: list) -> list:
    count = len(commits)
    if count > 50:
        return [("CRITICAL", f"{count} commits -- run clean to remove old file versions.")]
    elif count > 10:
        return [("WARN", f"{count} commits -- consider running cleaner.")]
    return [("OK", f"{count} commit(s)")]

def check_operation_types(commits: list) -> list:
    ops = [c.get("operationType", "UNKNOWN") for c in commits]
    upserts = ops.count("UPSERT")
    inserts = ops.count("INSERT")
    return [("OK", f"{inserts} inserts, {upserts} upserts")]

def check_bytes_written(commits: list) -> list:
    if not commits:
        return [("WARN", "No commits found.")]
    avg_bytes = sum(c.get("totalBytesWritten", 0) for c in commits) / len(commits)
    avg_mb = avg_bytes / 1024 / 1024
    if avg_mb < 10:
        return [("WARN", f"Avg {avg_mb:.2f} MB written per commit -- very small writes, consider batching.")]
    return [("OK", f"Avg {avg_mb:.2f} MB per commit")]

def scan(table_path: str, output=None, out_file=None):
    commits, inflight = load_commits(table_path)
    findings = (
        check_inflight(inflight)
        + check_commit_count(commits)
        + check_operation_types(commits)
        + check_bytes_written(commits)
    )
    console = Console()
    table = Table(title=f"Hudi -- {table_path}", show_header=True)
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
            "format": "hudi",
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