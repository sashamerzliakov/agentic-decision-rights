#!/usr/bin/env bash
# detect.sh - exit-point detectors for the agentic-decision-rights skill.
#
# Runs the enumeration detectors from SKILL.md "Mode: audit" step 1 against a path,
# with the shared exclusions applied to every detector, and the node_modules
# self-check the skill requires.
#
# Usage:
#   ./detect.sh [--json] [--detector N] [--quiet] [PATH]
#
#   PATH          directory or file to scan. Default: .
#   --json        emit [{"detector":N,"file":...,"line":...,"text":...}] instead of text
#   --detector N  run only detector N (1..4). Repeatable.
#   --quiet       suppress the self-check banner in text mode
#
# Detectors:
#   1  terminals and status returns
#   2  threshold constants in comparisons
#   3  fault paths that return normally (JS/TS, Python, Go, Rust, Java, Ruby)
#   4  thresholds held in variables and argument defaults
#
# grep is invoked as /usr/bin/grep on purpose. On the machine this skill was written
# on, `grep` was a shell function wrapping ugrep, which silently changes the flags and
# the output. Override with ADR_GREP=/path/to/grep if /usr/bin/grep is not the one you
# want. Patterns are POSIX ERE only, so they run on both BSD grep (macOS) and GNU grep.
#
# Exit status: 0 when the run completed, whether or not it found anything. 2 on usage
# error. A detector finding nothing is a result, not a failure.

set -u

GREP="${ADR_GREP:-/usr/bin/grep}"
AWK="${ADR_AWK:-awk}"

TARGET="."
JSON=0
QUIET=0
WANT=""

usage() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --json)     JSON=1; shift ;;
    --quiet)    QUIET=1; shift ;;
    --detector) [ $# -ge 2 ] || usage; WANT="$WANT $2"; shift 2 ;;
    -h|--help)  usage ;;
    --)         shift; break ;;
    -*)         echo "detect.sh: unknown option $1" >&2; usage ;;
    *)          TARGET="$1"; shift ;;
  esac
done
[ $# -gt 0 ] && TARGET="$1"

if [ ! -e "$TARGET" ]; then
  echo "detect.sh: no such path: $TARGET" >&2
  exit 2
fi

if [ ! -x "$GREP" ]; then
  echo "detect.sh: $GREP is not executable. Set ADR_GREP to a real grep binary." >&2
  exit 2
fi

wanted() {
  [ -z "$WANT" ] && return 0
  case " $WANT " in *" $1 "*) return 0 ;; esac
  return 1
}

# Every detector repeats the full exclusion set. They share no variable in SKILL.md
# because each is meant to survive being copied into a fresh shell on its own; here they
# share one function, which is the same list in one place.
EXCL="--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=_site \
--exclude-dir=dist --exclude-dir=build --exclude-dir=vendor --exclude-dir=target \
--exclude-dir=__pycache__ --exclude-dir=.venv"

# --- patterns ---------------------------------------------------------------

# SKILL.md's detector 1 verbatim, then an extension. The skill's pattern knows
# process.exit, sys.exit and os._exit, which is JS and Python; it does not know Go's
# os.Exit, Rust's process::exit or Java's System.exit, and its `return 0` alternative
# requires end-of-line, so `return 0;  // done` is missed. EXTENSION, not in SKILL.md.
P1_SKILL='process\.exit|sys\.exit|os\._exit|return[[:space:]]+(0|1|2|-1)[[:space:]]*(;|$)|return[[:space:]]*\{[^}]*(error|status|state|ok|success|verdict)'
P1_EXT='os\.Exit|process::exit|System\.exit|std::process::exit|exit\([0-9]\)|return[[:space:]]+(0|1|2|-1)[[:space:]]*(;|$|//|#|/\*)|return[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]*\{[^}]*(error|status|state|ok|success|verdict)'
P1="$P1_SKILL|$P1_EXT"

# SKILL.md's detector 2 verbatim, then an extension. The skill's third alternative is
# `[1-9][0-9]*`, chosen to skip the `> 0` emptiness guards. That also skips every
# decimal, so `if score >= 0.92` (the shape an Estimate settlement almost always takes)
# is missed. The extension adds decimals while still skipping a bare `> 0`.
# EXTENSION, not in SKILL.md.
P2_SKILL='(>=|<=|>|<)[[:space:]]*[^[:space:];)]*(limit|threshold|max|min|cap|budget|tolerance)|(limit|threshold|max|min|cap|budget|tolerance)[^[:space:]]*[[:space:]]*(>=|<=|>|<)|(>=|<=|>|<)[[:space:]]*[1-9][0-9]*'
P2_EXT='(>=|<=|>|<)[[:space:]]*(0*\.[0-9]+|[0-9]+\.[0-9]+)'
P2="$P2_SKILL|$P2_EXT"

# Detector 3 anchors. The first four need a window read (a return inside the block);
# the Rust three and the bare `catch {` are findings on the matching line alone.
P3='catch[[:space:]]*\([^)]*\)[[:space:]]*\{?|catch[[:space:]]*\{|^[[:space:]]*except([[:space:]]|:)|^[[:space:]]*rescue([[:space:]]|$)|if[[:space:]]+err[[:space:]]*!=[[:space:]]*nil[[:space:]]*\{|unwrap_or|\.ok\(\)|Err\(_\)[[:space:]]*=>'

# Detector 4. The name set SKILL.md's detector 2 already knows, plus the ones that only
# ever appear on the left of an assignment: retries, attempts, timeout, deadline, window,
# ttl, and the argument-default names. `default|due|until|backoff|interval|iter|rounds`
# are an extension beyond the skill text, added so that `due_until = 300` is found at the
# assignment when `now > due_until` hides the number from detector 2.
N4='limit|threshold|max|min|cap|budget|tolerance|retries|attempts|timeout|deadline|window|ttl|default|due|until|backoff|interval'
P4="(^|[^[:alnum:]_])($N4)[[:alnum:]_]*([[:space:]]*(:=|=|<-)[[:space:]]*-?[0-9]|[[:space:]]*:[[:space:]]*-?[0-9]|[[:space:]]*:[[:space:]]*[[:alnum:]_<>,[:space:]]*=[[:space:]]*-?[0-9])"

# --- runners ----------------------------------------------------------------

# $1 = detector number, $2 = pattern, $3 = extra grep flags
run_simple() {
  # shellcheck disable=SC2086
  "$GREP" -rnI $3 $EXCL -E -e "$2" -- "$TARGET" 2>/dev/null
}

# Detector 3 needs a six-line window, which grep cannot express. grep -rlI still selects
# the files (so the exclusions and the binary skip are grep's, not ours) and awk joins
# the window. Reading whole files by name keeps file:line unambiguous, which parsing
# grep -A output does not: a path containing `-` or `:` is indistinguishable from the
# separator grep puts between a context line and its number.
run_detector3() {
  # shellcheck disable=SC2086
  "$GREP" -rlI $EXCL -E -e "$P3" -- "$TARGET" 2>/dev/null \
  | tr '\n' '\0' \
  | xargs -0 -n 200 "$AWK" '
    function indent(s,   n) {
      n = 0
      while (n < length(s) && (substr(s, n + 1, 1) == " " || substr(s, n + 1, 1) == "\t")) n++
      return n
    }
    function flush(f,   i, j, hi, t, kind, win, has, base) {
      for (i = 1; i <= nl; i++) {
        t = L[i]
        kind = ""
        if (t ~ /unwrap_or|\.ok\(\)|Err\(_\)[[:space:]]*=>/) {
          # Rust: a fault collapsed into a value on the spot. The line is the finding.
          print f ":" i ":" t
          continue
        }
        if (t ~ /if[[:space:]]+err[[:space:]]*!=[[:space:]]*nil[[:space:]]*\{/) kind = "go"
        else if (t ~ /catch[[:space:]]*\([^)]*\)[[:space:]]*\{?|catch[[:space:]]*\{/) kind = "catch"
        else if (t ~ /^[[:space:]]*except([[:space:]]|:)/) kind = "except"
        else if (t ~ /^[[:space:]]*rescue([[:space:]]|$)/) kind = "rescue"
        else continue

        hi = i + 6; if (hi > nl) hi = nl
        has = 0
        base = indent(t)
        for (j = i; j <= hi; j++) {
          win = L[j]
          # Stop at the end of the block. Six lines of context runs straight past a
          # closing brace and reads the next statement as if it were inside the handler,
          # which reports the correct Go shape (`return nil, err` then a later clean
          # return) as a fault path. A dedent to the anchor column ends the block in
          # every language here: `}` in Go, Java, JS and Rust, the next statement in
          # Python and Ruby.
          if (j > i && win ~ /[^[:space:]]/ && indent(win) <= base) break
          if (kind == "go") {
            # Go: err checked, then a return that does not carry the err. Returning the
            # err is the correct shape and is not a finding.
            if (win ~ /return/ && win !~ /err/) { has = 1; break }
          } else {
            if (win ~ /return|^[[:space:]]*pass[[:space:]]*$|^[[:space:]]*continue|^[[:space:]]*break/) { has = 1; break }
          }
        }
        if (has) print f ":" i ":" t
      }
    }
    FNR == 1 {
      if (nl > 0) flush(prevfile)
      for (k in L) delete L[k]
      nl = 0; prevfile = FILENAME
    }
    { L[FNR] = $0; nl = FNR }
    END { if (nl > 0) flush(prevfile) }
  ' 2>/dev/null
}

emit_detector() {
  case "$1" in
    1) run_simple 1 "$P1" "" ;;
    2) run_simple 2 "$P2" "-i" ;;
    3) run_detector3 ;;
    4) run_simple 4 "$P4" "-i" ;;
  esac
}

TITLE_1="Detector 1: terminals and status returns"
TITLE_2="Detector 2: threshold constants in comparisons"
TITLE_3="Detector 3: fault paths that return normally"
TITLE_4="Detector 4: thresholds in variables and argument defaults"

title_for() {
  case "$1" in
    1) echo "$TITLE_1" ;; 2) echo "$TITLE_2" ;;
    3) echo "$TITLE_3" ;; 4) echo "$TITLE_4" ;;
  esac
}

TMPDIR_RUN="${TMPDIR:-/tmp}/adr-detect.$$"
mkdir -p "$TMPDIR_RUN" || exit 2
trap 'rm -rf "$TMPDIR_RUN"' EXIT INT TERM

SELF_CHECK_FAILED=0
for d in 1 2 3 4; do
  wanted "$d" || continue
  emit_detector "$d" > "$TMPDIR_RUN/$d.out" 2>/dev/null
  # The self-check SKILL.md asks for: pipe each detector through `grep -c node_modules`
  # and expect 0. A failed --exclude-dir is silent, so this count is the only signal.
  leaked=$("$GREP" -c node_modules "$TMPDIR_RUN/$d.out" 2>/dev/null || echo 0)
  leaked=$(echo "$leaked" | tr -d '[:space:]')
  [ -z "$leaked" ] && leaked=0
  echo "$leaked" > "$TMPDIR_RUN/$d.leak"
  [ "$leaked" -ne 0 ] && SELF_CHECK_FAILED=1
done

# --- output -----------------------------------------------------------------

if [ "$JSON" -eq 1 ]; then
  # One awk pass over every detector's output, so the commas between objects are the
  # responsibility of one loop instead of being stitched together afterwards.
  for d in 1 2 3 4; do
    wanted "$d" || continue
    [ -f "$TMPDIR_RUN/$d.out" ] || continue
    "$AWK" -v det="$d" '{ print det "\t" $0 }' "$TMPDIR_RUN/$d.out" >> "$TMPDIR_RUN/all.tsv"
  done
  [ -f "$TMPDIR_RUN/all.tsv" ] || : > "$TMPDIR_RUN/all.tsv"
  "$AWK" -F'\t' '
    function jesc(s,   i, n, c, o) {
      o = ""; n = length(s)
      for (i = 1; i <= n; i++) {
        c = substr(s, i, 1)
        if (c == "\\") o = o "\\\\"
        else if (c == "\"") o = o "\\\""
        else if (c == "\t") o = o "\\t"
        else if (c < " ") o = o " "
        else o = o c
      }
      return o
    }
    BEGIN { printf("[") }
    {
      det = $1
      rest = $0
      sub(/^[^\t]*\t/, "", rest)
      # grep -n gives file:line:text. Take the leftmost `:<digits>:` as the split, so a
      # path containing a colon only misparses when the next segment is numeric.
      if (!match(rest, /:[0-9]+:/)) next
      file = substr(rest, 1, RSTART - 1)
      line = substr(rest, RSTART + 1, RLENGTH - 2)
      text = substr(rest, RSTART + RLENGTH)
      if (length(text) > 200) text = substr(text, 1, 200)
      printf("%s\n {\"detector\":%s,\"file\":\"%s\",\"line\":%s,\"text\":\"%s\"}",
             (n++ ? "," : ""), det, jesc(file), line, jesc(text))
    }
    END { printf("%s]\n", (n ? "\n" : "")) }
  ' "$TMPDIR_RUN/all.tsv"
  exit 0
fi

echo "# agentic-decision-rights: exit-point detectors"
echo "# path: $TARGET"
echo "# grep: $GREP"
echo
for d in 1 2 3 4; do
  wanted "$d" || continue
  n=$(wc -l < "$TMPDIR_RUN/$d.out" | tr -d '[:space:]')
  echo "== $(title_for "$d")  [$n hits] =="
  if [ "$n" = "0" ]; then
    echo "  (no hits. An exit point with no hit anywhere is still an exit point.)"
  else
    cat "$TMPDIR_RUN/$d.out"
  fi
  echo
done

if [ "$QUIET" -eq 0 ]; then
  echo "== self-check: node_modules leaked into output (expect 0 on each) =="
  for d in 1 2 3 4; do
    wanted "$d" || continue
    l=$(cat "$TMPDIR_RUN/$d.leak")
    if [ "$l" -eq 0 ]; then
      echo "  detector $d: 0  ok"
    else
      echo "  detector $d: $l  WARNING: an exclusion did not take. Hits from dependencies"
      echo "               are not decisions anyone made. Narrow by path and rerun."
    fi
  done
  [ "$SELF_CHECK_FAILED" -eq 1 ] && echo "  SELF-CHECK FAILED"
fi

exit 0
