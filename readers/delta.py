import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

THRESHOLDS = {
    "commit_warn": 10,
    "commit_critical": 50,
    "small_file_bytes": 10 * 1024 * 1024,
    "small_file_warn_pct": 0.5,
}

def load_commits(table_path: str) -> list:
    log_dir = Path(table_path) / "_delta_log"
    commits = []
    for f in sorted(log_dir.glob("*.json")):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    commits.append(json.loads(line))
    return commits

def check_commit_count(commits: list) -> list:
    count = len(commits)
    if count >= THRESHOLDS["commit_critical"]:
        return [("CRITICAL", f"{count} commits -- table read is slow. Checkpoint needed.")]
    elif count >= THRESHOLDS["commit_warn"]:
        return [("WARN", f"{count} commits -- consider checkpointing.")]
    return [("OK", f"{count} commit(s)")]

def check_small_files(commits: list) -> list:
    all_files = []
    for commit in commits:
        add = commit.get("add")
        if add and isinstance(add, dict):
            all_files.append(add)
    if not all_files:
        return [("WARN", "No files tracked in delta log.")]
    small = [f for f in all_files if f.get("size", 0) < THRESHOLDS["small_file_bytes"]]
    pct = len(small) / len(all_files)
    avg_mb = sum(f.get("size", 0) for f in all_files) / len(all_files) / 1024 / 1024
    if pct >= THRESHOLDS["small_file_warn_pct"]:
        return [("WARN", f"{len(small)}/{len(all_files)} files under 10MB ({pct:.0%}). Avg: {avg_mb:.2f} MB.")]
    return [("OK", f"{len(all_files)} files, avg {avg_mb:.2f} MB")]

def check_schema_changes(commits: list) -> list:
    schema_commits = [c for c in commits if c.get("metaData")]
    count = len(schema_commits)
    if count > 3:
        return [("WARN", f"Schema changed {count} times -- high schema drift.")]
    return [("OK", f"Schema changed {count} time(s)")]

def check_removed_files(commits: list) -> list:
    removed = sum(1 for c in commits if c.get("remove") and isinstance(c.get("remove"), dict))
    added = sum(1 for c in commits if c.get("add") and isinstance(c.get("add"), dict))
    if added == 0:
        return [("WARN", "No files added -- empty table?")]
    ratio = removed / added if added else 0
    if ratio > 0.5:
        return [("WARN", f"{removed} removed vs {added} added -- lots of deleted data sitting around.")]
    return [("OK", f"{removed} removed, {added} added")]

def scan(table_path: str, output=None, out_file=None):
    commits = load_commits(table_path)
    findings = (
        check_commit_count(commits)
        + check_small_files(commits)
        + check_schema_changes(commits)
        + check_removed_files(commits)
    )
    console = Console()
    table = Table(title=f"Delta -- {table_path}", show_header=True)
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
            "format": "delta",
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