import argparse
from readers.iceberg import scan

def main():
    parser = argparse.ArgumentParser(prog="lake-inspect")
    parser.add_argument("--path", required=True, help="Path to table")
    parser.add_argument("--format", default="iceberg", choices=["iceberg"])
    args = parser.parse_args()
    scan(args.path)

if __name__ == "__main__":
    main()