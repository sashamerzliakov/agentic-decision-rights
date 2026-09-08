<!-- Part of the agentic-decision-rights skill. Read from SKILL.md at point of need. Licence: CC BY-NC-SA 4.0, see LICENSE and NOTICE beside SKILL.md. -->

# The grant record

The full record template, the rules for filling it, the compact register row, and the return shape a loop must emit.

## The compact row

Every exit point gets a row, including those earning a full record. Nine columns, and a row
missing one is not a complete answer:

| Column | What goes in it |
|---|---|
| **Exit** | `file:line`, or the job or service that runs it |
| **Demand x Knowledge** | Q1 by Q4, the two matrix axes, as `skill x risk` |
| **Gates** | Q2 and Q3: `two-way, recurs` / `recurs, uncaptured` / `one-way` / `rare` / `[UNKNOWN]` |
| **Settles** | The settling family and the actual test, short enough for a cell |
| **Bound** | The Exhaustion bound and its value: cap, deadline, cost ceiling, no-change |
| **Hands back on** | The trigger, true or false at run time |
| **To** | The named person it reaches, to decide or to gather |
| **Owner** | A named person, or `[UNOWNED]`, which is the finding |
| **Status** | `draft` / `active` / `superseded by <slug>`, under the rule below |

**A record is `draft` until every gate is answered.** A row with `[UNKNOWN]` in `Gates`,
`[UNOWNED]` in `Owner`, or no settlement, is never `active`.

## The full record

```markdown
# Grant: <loop or exit point>

Status: draft | active | superseded by <slug>   (draft while any gate, owner or
        settlement is open)
Version: <n>  ·  Date: <YYYY-MM-DD>  ·  Owner: <named person, not a team>
Loop: <repo path, file:line, service or job that runs it>

## The decision
<One sentence. What this loop settles without a person.>

## Classification
| Question | Answer | Evidence |
|---|---|---|
| Q1 Demands | skill / rule / knowledge | |
| Q2 GATE Reversible at act time | two-way / one-way / [UNKNOWN] | |
| Q3 GATE Recurs with feedback | yes, ~<n> per <period>, outcome known within <time> / no, rare / no, feedback absent in domain / no, feedback exists but uncaptured / [UNKNOWN] | |
| Q4 Can know | risk / uncertainty / ambiguity | |
| Q5 Stage granted | acquire / analyse / select / act | |
| Q6 Holds the information | agent / person / neither | |

Matrix read: <demand column> x <knowledge column>
Dots in both: <candidates, Exhaustion and Authority excluded from candidacy>
Passed over: <candidate with a dot in both that a stronger one beat, and what it would add>
Rings: <family, column, and what it contributes rather than settles>
Dashes: <family, and the column that emptied it>
Devalued: <family, and whether Q5 or Q6 counted against it>
Not affordable: <family you could build but did not, and why>

## The grant
Settlement: <family and the actual test, precisely enough to implement; or
             [UNRESOLVED GATE, Q2|Q3] with the missing evidence named>
Contributes: <ring families, and what each adds without settling>
Bounds: <cap, deadline, cost ceiling, or no-change-between-rounds, and the value of each>
Trigger: <the condition that hands it back>
Destination: <the named person it lands on when the bound is hit, the trigger fires, or a
          gate closed the grant. Authority is this field, never a rung below the bound>
On fire: <who receives it, in what form, how fast, and whether they are asked to
          decide or to gather missing information>
End states: converged | exhausted | escalated | failed
Caller reads: <how the caller tells the four apart>
Cascade: <does this loop spawn agents; if so, how the bound, the owner and the trail
          reach each child; "does not spawn" is valid and must be written>
Audit trail: <path or system where each firing is recorded>

## Limits
<What this grant does not settle. The known weakness of the family chosen, and
 the gate closest to failing.>

## Harvest
Escalation log: <path>
Promotion rule: <replay or shadow, and what would move a case from escalation into the
             predicate; the order or tie rule once more than one rule can match a case>
Keeps in practice: <a sample of settled cases reviewed on a stated cadence, or the reasoning
             shown with each escalation; who reviews it>
Review due: <YYYY-MM-DD>, owner <name>
             or: no scheduled review, reopens on <the named evidence>
<If Q3 landed on the rare or no-feedback branch: the evidence that would reopen it.
 If Q3 landed on the uncaptured-feedback branch: the instrumentation change, its owner,
 and the date the branch gets re-read.>
```

Rules for filling it:

- **Owner is a person.** A team, a rota or a Slack channel is `[UNOWNED]`.
- **Trigger is testable.** If you cannot write it as something true or false at run time, it is
  not a trigger yet.
- **End states go in the return value.** The record is not enough on its own: the loop says which
  state it ended in, and the caller receives it.

A minimal return shape for that last rule:

```json
{
  "state": "converged | exhausted | escalated | failed",
  "grant": "<grant slug>",
  "evidence": "<what settled it, what was still failing, or what threw>",
  "escalated_to": "<owner, when state is escalated>",
  "rounds": 3
}
```

`failed` is the state a fault path must report. A loop that catches an exception and returns a
result-shaped object without setting `failed` has converted a crash into a quiet success: silent
exhaustion arriving by a different route.
