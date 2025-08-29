import argparse
import json
import sys
import yaml
import jsonschema
import datetime
import re
from pathlib import Path
from calculate_posture import calculate_posture


def parse_iso_duration(s: str) -> datetime.timedelta:
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(\d+)H)?", s)
    if not m:
        raise ValueError(f"Invalid duration {s}")
    days = int(m.group(1) or 0)
    hours = int(m.group(2) or 0)
    return datetime.timedelta(days=days, hours=hours)


def load_yaml(p: str):
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cmd_lint(args) -> int:
    data = load_yaml(args.note)
    with open(args.schema, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(data, schema)
    return 0


def cmd_check_evidence(args) -> int:
    data = load_yaml(args.note)
    max_age = parse_iso_duration(args.max_age)
    today = datetime.date.today()
    for ev in data.get("evidence", []):
        ev_date = datetime.date.fromisoformat(ev["date"])
        if today - ev_date > max_age:
            print(f"evidence {ev['id']} is stale", file=sys.stderr)
            return 1
    return 0


def cmd_generate_assurance_case(args) -> int:
    data = load_yaml(args.note)
    print(f"Goal: Mitigate risk {data['title']}")
    for ev in data.get("evidence", []):
        print(f"Solution: {ev['id']}")
    return 0


def cmd_prioritize(args) -> int:
    parse_iso_duration(args.budget)  # validate format
    path = Path(args.path)
    for note in sorted(path.glob("risk-note-*.yaml")):
        print(note.name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="safety_protocol")
    sub = p.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("lint")
    l.add_argument("note")
    l.add_argument("--schema", required=True)
    l.set_defaults(func=cmd_lint)

    c = sub.add_parser("check-evidence")
    c.add_argument("note")
    c.add_argument("--max-age", required=True)
    c.set_defaults(func=cmd_check_evidence)

    g = sub.add_parser("generate-assurance-case")
    g.add_argument("note")
    g.set_defaults(func=cmd_generate_assurance_case)

    pr = sub.add_parser("prioritize")
    pr.add_argument("path")
    pr.add_argument("--budget", required=True)
    pr.set_defaults(func=cmd_prioritize)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
