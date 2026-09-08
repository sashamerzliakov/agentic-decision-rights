#!/usr/bin/env python3
"""scan.py - deterministic checks for the agentic-decision-rights skill.

Does the mechanical half of an audit: enumerate exit-point candidates, flag fault
paths that return normally, check a register for the rules it is supposed to keep,
and report what an escalation log is missing before anyone tries to harvest it.

Judgement stays with the agent. Nothing here answers Q1 to Q6 or A1 to A8, decides a
number, names an owner, or proposes a promotion. Every subcommand reports shapes and
absences; reading them is the agent's job.

    scan.py candidates <path>            run detect.sh, emit the JSON candidate list
    scan.py silent-exhaustion <path>     fault paths that return a value and say nothing
    scan.py register-freshness <dir>     active records with no owner or an open gate
    scan.py log-shape <jsonl>            escalation log entries missing the fields

Every subcommand takes --json. Exit status is 0 whenever the command ran, including
when it found problems: a finding is a result, not a failure. Exit 2 is usage error.

Python 3 standard library only, no dependencies.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DETECT = os.path.join(HERE, "detect.sh")

EXCLUDE_DIRS = {
    "node_modules", ".git", "_site", "dist", "build", "vendor",
    "target", "__pycache__", ".venv",
}

# Extensions silent-exhaustion will read. An allowlist rather than "every text file":
# a syntax-highlighting corpus or a changelog is text, and matching a `catch` inside
# one produces a finding about a test fixture, not about a decision anyone made.
CODE_EXT = {
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".py", ".go", ".rs", ".java",
    ".rb", ".kt", ".kts", ".cs", ".php", ".scala", ".swift", ".c", ".cc", ".cpp", ".m",
}

MAX_BYTES = 1_000_000
MAX_BLOCK = 40


# --------------------------------------------------------------------------- utils

def walk_code(path):
    """Yield code files under path, honouring the shared exclusions."""
    if os.path.isfile(path):
        yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() not in CODE_EXT:
                continue
            full = os.path.join(root, name)
            try:
                if os.path.getsize(full) > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield full


def read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return []


def indent_of(line):
    return len(line) - len(line.lstrip(" \t"))


# ---------------------------------------------------------------- candidates

def cmd_candidates(args):
    if not os.path.exists(DETECT):
        die("detect.sh not found beside scan.py at %s" % DETECT)
    if not os.access(DETECT, os.X_OK):
        die("detect.sh is not executable: chmod +x %s" % DETECT)
    proc = subprocess.run(
        [DETECT, "--json", args.path],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        die("detect.sh failed (%d): %s" % (proc.returncode, proc.stderr.strip()))
    try:
        rows = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        die("detect.sh did not emit valid JSON: %s" % exc)

    if args.json:
        print(json.dumps(rows, indent=1))
        return 0

    titles = {
        1: "terminals and status returns",
        2: "threshold constants in comparisons",
        3: "fault paths that return normally",
        4: "thresholds in variables and argument defaults",
    }
    print("Exit-point candidates under %s" % args.path)
    print("%d candidates. Each is a shape, not yet a finding.\n" % len(rows))
    for det in (1, 2, 3, 4):
        group = [r for r in rows if r["detector"] == det]
        print("== Detector %d: %s  [%d] ==" % (det, titles[det], len(group)))
        for r in group:
            print("  %s:%s: %s" % (r["file"], r["line"], r["text"].strip()))
        if not group:
            print("  (none)")
        print()
    return 0


# ----------------------------------------------------------- silent exhaustion

ANCHORS = [
    ("catch", re.compile(r"catch\s*(\([^)]*\))?\s*\{")),
    ("except", re.compile(r"^\s*except\b")),
    ("rescue", re.compile(r"^\s*rescue\b")),
    ("go-err", re.compile(r"\bif\s+err\s*!=\s*nil\s*\{")),
    ("rust-unwrap_or", re.compile(r"\.unwrap_or(_else|_default)?\s*\(")),
    ("rust-ok", re.compile(r"\.ok\(\)")),
    ("rust-err-arm", re.compile(r"\bErr\(_\)\s*=>")),
]

SINGLE_LINE = {"rust-unwrap_or", "rust-ok", "rust-err-arm"}

RETHROW = re.compile(
    r"\bthrow\b|\braise\b|\bpanic\b|\brethrow\b|\breraise\b|\bre_raise\b"
    r"|\bexpect\s*\(|\?\s*;|return\s+Err\(|return\s+err\b|return\s+nil\s*,\s*err\b"
    r"|,\s*err\s*$|\bos\.Exit\(|\bsys\.exit\(|\bprocess\.exit\(|\bexit\s*\(\s*[1-9]"
    r"|\bSystem\.exit\(\s*[1-9]|\babort\(|\bfatal\b|\bFatal\b"
)

# Setting the state the caller reads is the thing that stops a fault being silent, and
# only a value that says "failed" does that. Matching the field name alone suppresses
# the finding it exists to make: `return {status: "ok"}` inside a catch names a state
# field and is exactly the silent success. The value has to carry the fault.
SETS_STATE = re.compile(
    # a failure-named field set to a truthy value: failed = True, "failed": 1
    r"\b(failed|failure|errored)\b[\'\"]?\s*[:=]\s*[\'\"]?"
    r"(true|1|yes|failed|failure|error|err|exception)\b"
    # a state-carrying field set to a failure value: state: "failed", ok: false
    r"|\b(state|status|result|outcome|verdict|ok|success)\b[\'\"]?\s*[:=]\s*[\'\"]?"
    r"(failed|failure|error|errored|err|exception|exhausted|escalated|false|0)\b"
    # or an explicit setter
    r"|\b(set_state|setState|set_status|setStatus|mark_failed|markFailed|"
    r"set_failed|setFailed)\s*\(",
    re.IGNORECASE,
)

# A return that hands something back. A bare `return` / `return;` / `return None` hands
# back nothing the caller can misread as a result, so it is not this finding.
RETURNS_VALUE = re.compile(r"\breturn\b(?!\s*(;|$|None\b|nil\s*$))\s*\S")


def block_extent(lines, i):
    """Lines i..end of the block opened at i, bounded by dedent and MAX_BLOCK."""
    base = indent_of(lines[i])
    end = i
    for j in range(i + 1, min(len(lines), i + 1 + MAX_BLOCK)):
        if not lines[j].strip():
            end = j
            continue
        if indent_of(lines[j]) <= base:
            break
        end = j
    return i, end


def cmd_silent_exhaustion(args):
    findings = []
    for path in walk_code(args.path):
        lines = read_lines(path)
        for i, line in enumerate(lines):
            kind = None
            for name, rx in ANCHORS:
                if rx.search(line):
                    kind = name
                    break
            if kind is None:
                continue

            if kind in SINGLE_LINE:
                # The fault is already collapsed into a value on this line. There is no
                # block to read: unwrap_or supplies a default in place of the error,
                # .ok() throws the error away, Err(_) => discards it by pattern.
                findings.append({
                    "file": path, "line": i + 1, "kind": kind,
                    "reason": "error discarded at the call site, no state reaches the caller",
                    "block": [line.rstrip()],
                })
                continue

            start, end = block_extent(lines, i)
            block = lines[start:end + 1]
            body = "\n".join(block)

            returns = any(RETURNS_VALUE.search(b) for b in block)
            if kind == "go-err":
                # Returning the err is the correct Go shape. Only a return that drops it
                # is the finding, and a bare `return` in a handler is not a value.
                returns = any(
                    RETURNS_VALUE.search(b) and "err" not in b for b in block
                )
            if not returns:
                continue
            if RETHROW.search(body):
                continue
            if SETS_STATE.search(body):
                continue

            findings.append({
                "file": path, "line": i + 1, "kind": kind,
                "reason": "returns a value; no rethrow, and no failed/error/state field set",
                "block": [b.rstrip() for b in block],
            })

    if args.json:
        print(json.dumps(findings, indent=1))
        return 0

    print("Silent exhaustion candidates under %s" % args.path)
    print("A fault path that returns a value the caller cannot tell from a result.")
    print("Heuristic: it reads indentation, not a parser. Confirm each against the")
    print("return path before it becomes a finding.\n")
    if not findings:
        print("  (none found. That is not evidence the loop reports its faults.)")
        return 0
    for f in findings:
        print("%s:%d  [%s]" % (f["file"], f["line"], f["kind"]))
        print("  %s" % f["reason"])
        for b in f["block"]:
            print("    | %s" % b)
        print()
    print("%d candidate(s)." % len(findings))
    return 0


# ---------------------------------------------------------- register freshness

STATUS_RE = re.compile(r"^\s*Status:\s*(.+?)\s*$", re.M)
OWNER_RE = re.compile(r"Owner:\s*([^\n·|]+)")
REVIEW_RE = re.compile(r"^\s*Review due:\s*(.+?)\s*$", re.M)
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def parse_table(text):
    """Return (headers, rows) for the first markdown table carrying an Exit column."""
    rows = []
    headers = None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if headers and rows:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        if headers is None:
            low = [c.lower().replace("*", "") for c in cells]
            if "exit" in low or "status" in low:
                headers = low
            continue
        rows.append(cells)
    return headers, rows


def cell(headers, row, *names):
    for n in names:
        for idx, h in enumerate(headers or []):
            if n in h and idx < len(row):
                return row[idx]
    return ""


def cmd_register_freshness(args):
    today = datetime.date.today()
    if args.today:
        try:
            today = datetime.date.fromisoformat(args.today)
        except ValueError:
            die("--today must be YYYY-MM-DD")

    reg = args.register_dir
    if not os.path.isdir(reg):
        die("not a directory: %s" % reg)

    breaches = []
    stale = []
    notes = []

    index = os.path.join(reg, "README.md")
    if not os.path.isfile(index):
        notes.append("no README.md index in %s: the register has records but no index" % reg)
    else:
        text = open(index, encoding="utf-8", errors="replace").read()
        headers, rows = parse_table(text)
        if headers is None:
            notes.append("%s: no index table found with an Exit or Status column" % index)
        for row in rows:
            status = cell(headers, row, "status").lower()
            owner = cell(headers, row, "owner")
            gates = cell(headers, row, "gates")
            exit_ = cell(headers, row, "exit")
            if "active" not in status:
                continue
            why = []
            if "[UNOWNED]" in owner.upper():
                why.append("Owner is [UNOWNED]")
            if "[UNKNOWN]" in gates.upper():
                why.append("Gates is [UNKNOWN]")
            if why:
                breaches.append({
                    "source": index, "record": exit_ or "(row)",
                    "status": status, "why": why,
                    "rule": "A row with [UNKNOWN] in Gates or [UNOWNED] in Owner is never active",
                })

    for name in sorted(os.listdir(reg)):
        if not name.endswith(".md") or name == "README.md":
            continue
        full = os.path.join(reg, name)
        text = open(full, encoding="utf-8", errors="replace").read()

        m = STATUS_RE.search(text)
        status = (m.group(1) if m else "").strip()
        status_l = status.lower()

        mo = OWNER_RE.search(text)
        owner = (mo.group(1) if mo else "").strip()

        gates_unknown = []
        headers, rows = parse_table(text)
        for row in rows:
            joined = " ".join(row)
            if re.search(r"\bQ2\b", joined) and "[UNKNOWN]" in joined.upper():
                gates_unknown.append("Q2")
            if re.search(r"\bQ3\b", joined) and "[UNKNOWN]" in joined.upper():
                gates_unknown.append("Q3")
        if "[UNRESOLVED GATE" in text.upper():
            gates_unknown.append("Settlement carries [UNRESOLVED GATE]")

        if status_l.startswith("active"):
            why = []
            if not owner or "[UNOWNED]" in owner.upper():
                why.append("Owner is [UNOWNED]")
            if gates_unknown:
                why.append("gate open: %s" % ", ".join(sorted(set(gates_unknown))))
            if why:
                breaches.append({
                    "source": full, "record": name, "status": status, "why": why,
                    "rule": "A record is draft until every gate is answered. "
                            "[UNKNOWN] gates or an [UNOWNED] owner is never active",
                })

        mr = REVIEW_RE.search(text)
        if mr:
            raw = mr.group(1).strip()
            md = DATE_RE.search(raw)
            if md:
                try:
                    due = datetime.date(int(md.group(1)), int(md.group(2)), int(md.group(3)))
                except ValueError:
                    notes.append("%s: unparseable Review due date %r" % (full, raw))
                    continue
                if due < today:
                    stale.append({
                        "source": full, "record": name, "status": status,
                        "review_due": due.isoformat(),
                        "days_overdue": (today - due).days,
                        "owner": owner,
                    })
            elif "reopens on" in raw.lower():
                notes.append("%s: no scheduled review, reopens on %s"
                             % (name, raw.split("reopens on", 1)[1].strip()))
            else:
                notes.append("%s: Review due is neither a date nor a reopens-on clause: %r"
                             % (name, raw))
        else:
            notes.append("%s: no Review due line" % name)

    result = {"as_at": today.isoformat(), "rule_breaches": breaches,
              "past_review": stale, "notes": notes}

    if args.json:
        print(json.dumps(result, indent=1))
        return 0

    print("Register freshness for %s (as at %s)\n" % (reg, today.isoformat()))
    print("== Rule breaches: active with an open gate or no owner  [%d] ==" % len(breaches))
    for b in breaches:
        print("  %s  (%s)" % (b["record"], b["source"]))
        print("    Status: %s" % b["status"])
        for w in b["why"]:
            print("    - %s" % w)
        print("    rule: %s" % b["rule"])
    if not breaches:
        print("  (none)")
    print()
    print("== Review date passed  [%d] ==" % len(stale))
    for s in stale:
        print("  %s  due %s, %d day(s) overdue, owner %s"
              % (s["record"], s["review_due"], s["days_overdue"], s["owner"] or "[UNOWNED]"))
    if not stale:
        print("  (none)")
    print()
    if notes:
        print("== Notes  [%d] ==" % len(notes))
        for n in notes:
            print("  %s" % n)
    return 0


# ------------------------------------------------------------------- log shape

REQUIRED = ["why", "reason", "inputs", "outcome"]


def cmd_log_shape(args):
    path = args.jsonl
    if not os.path.isfile(path):
        die("not a file: %s" % path)

    entries = []
    malformed = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, raw in enumerate(fh, 1):
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:
                malformed.append({"line": n, "error": str(exc), "text": raw.strip()[:160]})
                continue
            if not isinstance(obj, dict):
                malformed.append({"line": n, "error": "not a JSON object",
                                  "text": raw.strip()[:160]})
                continue
            missing = [f for f in REQUIRED
                       if f not in obj or obj[f] in (None, "", {}, [])]
            entries.append({"line": n, "obj": obj, "missing": missing})

    per_line = [{"line": e["line"], "ts": e["obj"].get("ts", ""),
                 "case": e["obj"].get("case", ""), "missing": e["missing"]}
                for e in entries]

    clusters = {}
    for e in entries:
        key = (str(e["obj"].get("why", "")), str(e["obj"].get("reason", "")))
        c = clusters.setdefault(key, {"why": key[0], "reason": key[1], "count": 0,
                                      "dates": [], "lines": [], "deciders": set(),
                                      "has_inputs": 0, "has_outcome": 0})
        c["count"] += 1
        c["lines"].append(e["line"])
        ts = str(e["obj"].get("ts", ""))
        md = DATE_RE.search(ts)
        if md:
            c["dates"].append(md.group(0))
        if e["obj"].get("by"):
            c["deciders"].add(str(e["obj"]["by"]))
        if e["obj"].get("inputs"):
            c["has_inputs"] += 1
        if e["obj"].get("outcome"):
            c["has_outcome"] += 1

    cl = []
    for c in clusters.values():
        ds = sorted(c["dates"])
        cl.append({
            "why": c["why"], "reason": c["reason"], "count": c["count"],
            "first": ds[0] if ds else "", "last": ds[-1] if ds else "",
            "lines": c["lines"], "deciders": sorted(c["deciders"]),
            "with_inputs": c["has_inputs"], "with_outcome": c["has_outcome"],
        })
    cl.sort(key=lambda x: (-x["count"], x["why"]))

    totals = {f: sum(1 for e in entries if f in e["missing"]) for f in REQUIRED}
    result = {"file": path, "entries": len(entries), "malformed": malformed,
              "missing_totals": totals, "per_entry": per_line, "clusters": cl}

    if args.json:
        print(json.dumps(result, indent=1))
        return 0

    print("Escalation log shape: %s" % path)
    print("%d entr(ies) read, %d malformed line(s).\n" % (len(entries), len(malformed)))
    for m in malformed:
        print("  line %d: %s -- %s" % (m["line"], m["error"], m["text"]))
    if malformed:
        print()

    print("== Missing fields, per entry ==")
    clean = 0
    for p in per_line:
        if not p["missing"]:
            clean += 1
            continue
        print("  line %d  %s  %s: missing %s"
              % (p["line"], p["ts"] or "(no ts)", p["case"] or "(no case)",
                 ", ".join(p["missing"])))
    print("  %d entr(ies) carry all four fields." % clean)
    print("  totals: " + ", ".join("%s missing in %d" % (f, totals[f]) for f in REQUIRED))
    print()

    print("== Clusters by (why, reason)  [%d] ==" % len(cl))
    for c in cl:
        span = ("%s to %s" % (c["first"], c["last"])) if c["first"] else "(no dates)"
        print("  count %d  %s" % (c["count"], span))
        print("    why:    %s" % (c["why"] or "[MISSING]"))
        print("    reason: %s" % (c["reason"] or "[MISSING]"))
        print("    decided by: %s" % (", ".join(c["deciders"]) or "[UNRECORDED]"))
        print("    replayable inputs: %d/%d   linked outcome: %d/%d"
              % (c["with_inputs"], c["count"], c["with_outcome"], c["count"]))
        if c["with_outcome"] < c["count"]:
            print("    -> consistent decisions are not evidence they were right.")
        if c["with_inputs"] < c["count"]:
            print("    -> the log does not carry the inputs to replay these cases.")
        print()
    print("Clustering is arithmetic. Whether a cluster has stabilised, and whether it")
    print("may be promoted, is the harvest procedure and stays with the agent.")
    return 0


# ------------------------------------------------------------------------ main

def die(msg):
    sys.stderr.write("scan.py: %s\n" % msg)
    raise SystemExit(2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="scan.py",
        description="Deterministic checks for the agentic-decision-rights skill.",
    )
    sub = ap.add_subparsers(dest="cmd")

    def add(name, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--json", action="store_true", help="machine-readable output")
        return p

    p = add("candidates", "run detect.sh and emit the JSON candidate list")
    p.add_argument("path", nargs="?", default=".")
    p.set_defaults(func=cmd_candidates)

    p = add("silent-exhaustion", "fault paths that return a value and set no state")
    p.add_argument("path", nargs="?", default=".")
    p.set_defaults(func=cmd_silent_exhaustion)

    p = add("register-freshness", "active records with no owner, an open gate, or a passed review")
    p.add_argument("register_dir")
    p.add_argument("--today", help="override today's date, YYYY-MM-DD, for testing")
    p.set_defaults(func=cmd_register_freshness)

    p = add("log-shape", "escalation log entries missing why, reason, inputs or outcome")
    p.add_argument("jsonl")
    p.set_defaults(func=cmd_log_shape)

    args = ap.parse_args(argv)
    if not getattr(args, "cmd", None):
        ap.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
