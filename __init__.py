import json
import argparse
from pathlib import Path
from readers.iceberg import scan as iceberg_scan
from readers.delta import scan as delta_scan
from readers.hudi import scan as hudi_scan

READERS = {
    "iceberg": iceberg_scan,
    "delta": delta_scan,
    "hudi": hudi_scan,
}

def detect_format(path: str) -> str:
    p = Path(path)
    if (p / "metadata").exists():
        return "iceberg"
    if (p / "_delta_log").exists():
        return "delta"
    if (p / ".hoodie").exists():
        return "hudi"
    return None

def main():
    parser = argparse.ArgumentParser(prog="lake-inspect")
    parser.add_argument("--path", help="Path to single table")
    parser.add_argument("--scan-dir", help="Scan all tables in a directory")
    parser.add_argument("--format", choices=["iceberg", "delta", "hudi"])
    parser.add_argument("--output", choices=["json"])
    parser.add_argument("--out-file", help="Path to save JSON report")
    args = parser.parse_args()

    if args.scan_dir:
        for table_dir in sorted(Path(args.scan_dir).iterdir()):
            if not table_dir.is_dir():
                continue
            fmt = detect_format(str(table_dir))
            if fmt:
                READERS[fmt](str(table_dir), output=args.output, out_file=args.out_file)
    elif args.path:
        fmt = args.format or detect_format(args.path)
        if not fmt:
            print(f"Could not detect format for {args.path}")
            return
        READERS[fmt](args.path, output=args.output, out_file=args.out_file)

if __name__ == "__main__":
    main()