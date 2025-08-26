#!/usr/bin/env python3
import argparse, sys, json, os, datetime, hashlib, glob
try:
    import yaml
except Exception as e:
    print("PyYAML not available in runtime.", file=sys.stderr)
    raise
def _iso_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)
def lint_cmd(args):
    data = load_yaml(args.file)
    schema = load_json(args.schema)
    try:
        import jsonschema
    except ImportError:
        print("jsonschema not installed. Basic structural checks only.", file=sys.stderr)
        if "risk_note" not in data:
            print("ERROR: top-level 'risk_note' missing", file=sys.stderr)
            sys.exit(2)
        required = ["identity","scope","claim","evidence","uncertainty","triage","controls","next_investigation"]
        missing = [k for k in required if k not in data["risk_note"]]
        if missing:
            print("ERROR: missing required sections: " + ", ".join(missing), file=sys.stderr)
            sys.exit(2)
        print("BASIC LINT PASSED (schema validation skipped).")
        return
    jsonschema.validate(instance=data, schema=schema)
    print("SCHEMA LINT PASSED.")
def check_evidence_cmd(args):
    rn = load_yaml(args.file)["risk_note"]
    max_age = parse_iso_duration(args.max_age)
    stale = []
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    for src in rn.get("evidence",{}).get("sources",[]):
        created = parse_dt(src.get("created"))
        if created is None: 
            stale.append((src.get("id","<unknown>"), "missing created"))
            continue
        if now - created > max_age:
            stale.append((src.get("id","<unknown>"), f"age {(now-created)} > {args.max_age}"))
    if stale:
        print("STALE EVIDENCE:")
        for s in stale:
            print(f" - {s[0]}: {s[1]}")
        sys.exit(3)
    print("EVIDENCE FRESH.")
def calc_posture(sev, exp, rev):
    if sev >= 4 or rev <= 2:
        if exp >= 3:
            return "red"
        elif exp >= 2:
            return "amber"
    risk_score = (sev * exp) / max(rev, 1e-9)
    if risk_score >= 4.0:
        return "red"
    elif risk_score >= 2.0:
        return "amber"
    else:
        return "green"
def generate_assurance_case_cmd(args):
    rn = load_yaml(args.file)["risk_note"]
    lines = []
    lines.append(f"Goal: Safety claim for {rn['identity']['id']} v{rn['identity']['version']}")
    lines.append(f"  Strategy: Observation–Inference–Decision separation with defeasible claim and controls")
    lines.append(f"  Context: Scope={rn['scope']['operating_conditions']} | Dist={rn['scope']['input_distribution']} | Valid={rn['scope']['temporal_validity']}")
    lines.append(f"  Assumption: Shift budget={rn['claim']['shift_budget']} | Hazard={rn['claim']['hazard_class']}")
    lines.append(f"  Solution: Evidence sources -> {', '.join(s['id'] for s in rn['evidence']['sources'])}")
    lines.append(f"  Justification: Threshold={rn['claim']['threshold']} with CI={rn['claim']['credible_interval']}")
    lines.append(f"  Sub-Goal: Uncertainty ledger covers {len(rn['uncertainty']['entries'])} entries; total={rn['uncertainty'].get('total_contribution','n/a')}")
    lines.append(f"  Sub-Goal: Controls mapped [prevent/detect/contain/recover] with activation by posture")
    lines.append(f"  Strategy: Triage S×E×R => posture={rn['triage']['posture']} (calc={calc_posture(rn['triage']['severity'], rn['triage']['exploitability'], rn['triage']['reversibility'])})")
    lines.append(f"  Solution: Next investigation => {rn['next_investigation']['experiment']} (EVOI={rn['next_investigation']['evoi_score']})")
    print("\n".join(lines))
def prioritize_cmd(args):
    budget_hours = parse_duration_to_hours(args.budget)
    items = []
    for path in glob.glob(os.path.join(args.dir, "*.yaml")):
        try:
            rn = load_yaml(path)["risk_note"]
            ex = rn["next_investigation"]
            hours = duration_to_hours(ex.get("resource_estimate","PT0H"))
            score = ex.get("evoi_score", 0)
            if hours <= 0:
                value = float('inf')
            else:
                value = score / hours
            items.append((value, path, score, hours, ex.get("experiment","")))
        except Exception as e:
            continue
    items.sort(reverse=True, key=lambda t: t[0])
    total = 0.0
    selected = []
    for v, path, score, hours, exp in items:
        if total + hours <= budget_hours:
            selected.append((path, score, hours, exp))
            total += hours
    print(f"PRIORITIZED within budget {args.budget} ({budget_hours}h):")
    for p, s, h, e in selected:
        print(f" - {os.path.basename(p)} :: EVOI={s} hours={h} :: {e}")
    rem = budget_hours - total
    print(f"UNUSED BUDGET HOURS: {round(rem,2)}")
def gate_check_cmd(args):
    rn = load_yaml(args.file)["risk_note"]
    posture = rn["triage"]["posture"]
    if posture == "red":
        print("BLOCK: posture is RED. Release denied.")
        sys.exit(4)
    if args.posture == "green" and posture != "green":
        print(f"BLOCK: required posture green, found {posture}")
        sys.exit(4)
    print(f"PASS: posture {posture} satisfies gate {args.posture}")
def parse_iso_duration(s):
    # very light ISO-8601 duration parse (supports weeks/days/hours/minutes/seconds)
    if s is None:
        return datetime.timedelta(0)
    if not s.startswith("P"):
        raise ValueError("Invalid ISO-8601 duration")
    days = 0; seconds = 0
    time_part = False
    num = ""
    for ch in s[1:]:
        if ch == "T":
            time_part = True
            continue
        if ch.isdigit() or ch == ".":
            num += ch
            continue
        if ch == "W":
            days += float(num) * 7; num = ""
        elif ch == "D":
            days += float(num); num = ""
        elif ch == "H":
            seconds += float(num) * 3600; num = ""
        elif ch == "M" and time_part:
            seconds += float(num) * 60; num = ""
        elif ch == "S":
            seconds += float(num); num = ""
    return datetime.timedelta(days=days, seconds=seconds)
def duration_to_hours(s):
    return parse_iso_duration(s).total_seconds()/3600.0
def parse_duration_to_hours(s):
    return duration_to_hours(s)
def parse_dt(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
    except Exception:
        return None
def main():
    parser = argparse.ArgumentParser(prog="safety-protocol")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("lint", help="Validate Risk Note against schema")
    p1.add_argument("file")
    p1.add_argument("--schema", required=True)
    p1.set_defaults(func=lint_cmd)
    p2 = sub.add_parser("check-evidence", help="Check evidence staleness")
    p2.add_argument("file")
    p2.add_argument("--max-age", default="P30D")
    p2.set_defaults(func=check_evidence_cmd)
    p3 = sub.add_parser("generate-assurance-case", help="Emit a simple GSN-like view")
    p3.add_argument("file")
    p3.set_defaults(func=generate_assurance_case_cmd)
    p4 = sub.add_parser("prioritize", help="Rank investigations in a directory by EVOI/hour")
    p4.add_argument("dir")
    p4.add_argument("--budget", default="PT40H")
    p4.set_defaults(func=prioritize_cmd)
    p5 = sub.add_parser("gate-check", help="Enforce release posture")
    p5.add_argument("file")
    p5.add_argument("--posture", choices=["amber","green"], required=True)
    p5.set_defaults(func=gate_check_cmd)
    args = parser.parse_args()
    args.func(args)
if __name__ == "__main__":
    main()
