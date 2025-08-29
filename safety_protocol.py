import argparse, json, yaml, datetime, re
from pathlib import Path
import sys
import jsonschema


def lint(note_path: str, schema_path: str):
    with open(note_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(data, schema)


def parse_duration_days(iso: str) -> int:
    m = re.match(r"P(\d+)D", iso)
    if not m:
        raise ValueError("Invalid ISO-8601 duration")
    return int(m.group(1))


def check_evidence(note_path: str, max_age: str):
    with open(note_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    days = parse_duration_days(max_age)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    for ev in data.get("evidence", []):
        ts = datetime.datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
        if ts < cutoff:
            print(f"stale evidence: {ev['id']}", file=sys.stderr)
            raise SystemExit(1)


def generate_assurance_case(note_path: str):
    with open(note_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    print(f"Goal: Assure system {data['system']['name']}")


def prioritize(path: str, budget: str):
    # Placeholder implementation
    return


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_lint = sub.add_parser("lint")
    p_lint.add_argument("note")
    p_lint.add_argument("--schema", required=True)

    p_check = sub.add_parser("check-evidence")
    p_check.add_argument("note")
    p_check.add_argument("--max-age", required=True)

    p_gen = sub.add_parser("generate-assurance-case")
    p_gen.add_argument("note")

    p_prio = sub.add_parser("prioritize")
    p_prio.add_argument("path")
    p_prio.add_argument("--budget", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "lint":
        lint(args.note, args.schema)
    elif args.cmd == "check-evidence":
        check_evidence(args.note, args.max_age)
    elif args.cmd == "generate-assurance-case":
        generate_assurance_case(args.note)
    elif args.cmd == "prioritize":
        prioritize(args.path, args.budget)


if __name__ == "__main__":
    main()
