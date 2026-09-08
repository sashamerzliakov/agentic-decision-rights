# How the skill works, step by step

Every agent loop has an exit condition, and every exit condition is a grant of authority: what the agent settles alone, how long it may keep trying, and what it hands back to a person. Most loops grant that authority to a number nobody chose. A loop ends converged, exhausted, escalated or failed, and the failure worth preventing is one that runs out of budget or hits a fault and reports as though it converged.

The skill turns the unwritten grant into a written one. Its output is a register: one grant record per exit point, naming what the loop settles alone, its bound, the trigger that hands it back, the person it lands on, and who owns the number. Where the code cannot answer, the record says `[UNOWNED]`, and that is the finding.

The register has a lifecycle across three modes. **Audit** reads existing code and produces the register as it stands, gaps and all. **Grant** writes the record for a new decision before the loop ships. **Harvest** reads what people decided when the loop escalated and proposes what has stabilised enough to move into the predicate. The framework is the article [Agentic Decision Rights](https://hcd.ai/agentic-ai/agentic-decision-rights/).

Three rules hold throughout. The skill never edits source, never invents an owner or a number, and never runs an unfamiliar loop to see what it does.

## Before any mode runs

| Step | What happens | How | Why it matters |
|---|---|---|---|
| Choose the mode | The request is read for audit, grant or harvest. | Code means audit, a described decision means grant, a log means harvest. | A wrong mode answers a question nobody asked. |
| Name the five settlements | Reference, Estimate, Challenge, Exhaustion and Authority are defined once. | Before any is used by name, with its strength and its weakness. | A reader without the article would otherwise hit a wall. |
| Fix the location | The skill asks where the register goes. | Beside architecture decision records if present. With nobody to ask, `docs/decision-rights/` by stated default. | A register scattered next to code is never read again. |

## Mode: audit

Read-only against the code. Diffs are proposed in chat. The register is the only thing written.

| Step | What happens | How | Why it matters |
|---|---|---|---|
| 1. Enumerate the exit points | Every place the program stops and reports, by file and line. | Five shapes: terminals, threshold constants in comparisons, fault paths that return normally, boolean gate fields, early returns. A bundled detector script with dependency folders excluded and a self-check that the exclusion took, then framework defaults such as `max_iter` by name. | The exit that matters is usually unnamed. |
| 2. Run the eight audit questions | Each exit is asked whether it tests the work or the budget, which end states it can produce, whether the caller can tell them apart, where an escalation lands, whether the action is reversible when taken, who owns the numbers, whether the grant travels to spawned agents, and whether it recurs with the outcome coming back. | From the code, with evidence. Reversibility and recurrence are gates and run on every exit. Evidence not in the repo gives `[UNKNOWN]`, a finding rather than a pass. Each exit is placed on the two matrix axes. | A cap that tests nothing about the work is a budget dressed as a completion test. The gate skipped on the safe-looking exit is the one that fails. |
| 3. Trace the return path | The path from cap to caller is read statically. | The loop runs only against a fixture, with the owner's go-ahead. | If the caller ignores the state field, the state does not exist. |
| 4. Name the findings | One of seven per exit, ordered by what to fix first: gate breach, unbounded grant, unresolved gate, silent exhaustion, escalation to nowhere, cascade leak, unowned grant. | Each carries `file:line` and observed behaviour. | An ordered list is a work plan. |
| 5. Apply the triage rule | How much record each exit earns. | A full record only where the exit can act irreversibly or visibly, more than one person could own the number, or the loop will outlive its author. Otherwise one index row. | A full record costs half an hour, and most exits do not earn it. |
| 6. Emit the register | Index and records are written, and findings are reported in chat. | A record with `[UNOWNED]` or `[UNKNOWN]` in gates, owner or settlement is `draft`, never `active`. | The audit is the first draft of the register, in the form the owner can finish. |

## Mode: grant

Runs before a loop ships. An answer the skill does not have is reported first, never filled with a plausible value.

| Step | What happens | How | Why it matters |
|---|---|---|---|
| 1. State the decision | One sentence: what the loop settles without a person. | Two sentences means two records. | A grant covering two decisions has a bound that fits neither. |
| 2. Run the gates first | Can the action be undone when taken? Does the decision recur? | A one-way door goes to a person, and seen by a third party counts as one-way. A case too rare to have a history goes to a person until named evidence reopens it. The skill adds a second condition to recurrence, that the outcome comes back clearly enough to validate a rule, labelled as its own extension. An unanswerable gate stops the procedure with `[UNKNOWN]`. | A score that weighs everything lets the one thing that mattered through. A gate filled in with a guess is the arbitrary cap one step further up. |
| 3. Classify both axes | What does settling it demand: skill, rule or knowledge? What can be known: risk, uncertainty or ambiguity? | One answer each, naming the two matrix columns. | The matrix narrows rather than picks. |
| 4. Read the matrix | The five families are read down the two columns. | A dot in both settles alone, a ring contributes, a dash is out. Exhaustion and Authority are never candidates. The strongest affordable candidate is taken: Reference, then Estimate, then Challenge. No candidate means a person takes it. | Exhaustion says when to stop, never whether the work was right. Authority is where the decision lands, not a rung a cap can outrank. |
| 5. Record what devalues | Which stage is granted, and who holds the better information? | Both devalue rather than veto. Where neither holds the information, the escalation asks a person to gather it. | An escalation without the missing input moves the problem. |
| 6. Bound and destine | Exhaustion bounds the chosen family. Authority is the named person it lands on. | Every record names both. | A settlement with no bound runs forever. A bound with no settlement is the cap this skill exists to find. |
| 7. Answer the cascade question | Does the loop spawn agents, and do the bound, owner and trail travel with them? | Recorded even as "does not spawn". | A child without the bound is an unbounded grant. |
| 8. Write the record and its limits | At the depth the triage rule earns, then what the grant does not settle. | The chosen family's weakness and the gate closest to failing. | A right nobody recorded is the arbitrary cap in better clothes. |

## Mode: harvest

Nobody can author the whole predicate up front. The running loop finds the hard cases faster. So the loop escalates wherever unsure, the person's reason is logged, and harvest proposes what has stabilised. It proposes only: a grant change is the owner's signature.

| Step | What happens | How | Why it matters |
|---|---|---|---|
| 1. Read the escalation log | One line per firing: why, the decision, the reason, the inputs, the outcome. | No reason means no clustering, no inputs means no replay, and no outcome means people agreed, not that they were right. | A log without the reason says a decision happened and nothing about how to make it again. |
| 2. Cluster by reason | Entries grouped by why they escalated, then by the reason given. | Count, date range, consistency, who decided, time to decide. | The reason is the rule in the making. |
| 3. Screen against the gates | Reversibility and recurrence run on every cluster. | One-way actions and clusters with no outcome feedback are never promoted. | A gate that closes a grant closes a promotion. |
| 4. Check the evidence | Linked outcomes and replayable inputs, per cluster. | Missing either: report descriptively, name the instrumentation, propose nothing. | A replay without the inputs is a guess dressed as a backtest. |
| 5. Classify and read the matrix | As in grant mode. | The proposed family must be one the columns allow. | A promotion routed around the existing check is a removed control. |
| 6. Propose the change | A diff to the grant record with the evidence and the replay result. | Where two rules can match one case, the diff states the order or tie rule and confirms unmatched cases still escalate. Where replay evidence is thin, a shadow run comes first: the predicate proposes, the person decides, both are logged, and the owner sets the agreement count that ends it. | Overlapping rules with no order are not a predicate. A rule that fit history can drift on arrival. |
| 7. Keep the person in practice | How the person stays competent once routine cases leave them. | A sample of settled cases to review, or the reasoning shown with each escalation. | Automate the routine and the person is left the hard cases with the least practice. |
| 8. Report the rest | Unstable and unassessable clusters, with the missing field named. | Those keep escalating. | How many consistent decisions justify a promotion is the owner's number, never the skill's. |

## The record

| Field | What it protects against |
|---|---|
| Status, version, date, owner | A record nobody can tell is current, or that names a team instead of a person. |
| The decision, one sentence | Two decisions sharing one bound. |
| Classification with evidence | A gate answered from memory. |
| Matrix read: candidates, passed over, rings, devalued, not affordable | A family chosen without saying what stronger one was not built. |
| Settlement, with the actual test | A settlement that cannot be implemented. |
| Bounds, with values | A loop that runs forever. |
| Trigger, testable at run time | A hand-back condition that is a sentiment. |
| Destination and what happens on fire | An escalation to a log nobody reads. |
| End states and how the caller reads them | Exhausted or failed read as converged. `failed` is the skill's fourth state beyond the article's three, labelled as its own. |
| Cascade | A child agent without the bound. |
| Audit trail | A firing with no record. |
| Limits | A grant read as stronger than it is. |
| Harvest: log, promotion rule, review due, keep-in-practice | A predicate that never learns, and a person who loses the skill the loop depends on. |

Writing a decision down with its authority is not new. The Decision Model and Notation standard has done it for business rules since 2015. What it leaves out is the loop: the bound, the trigger, and where the case lands when the agent gives up.

## What you get

- **A threshold with a name on it.** Every number the loop stops on has an owner and a review date, or a record saying plainly that it has neither.
- **A caller that can tell exhausted from converged.** The loop reports its end state and the caller receives it.
- **An escalation that lands on a person.** A testable trigger, a named destination, and whether they decide or gather what is missing.
- **A promotion path with evidence.** What people decided, why, and whether they were right accumulates in a form that can move into the predicate, one owned diff at a time.

Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Attribution: Sasha Merzliakov, https://hcd.ai/agentic-ai/agentic-decision-rights/.
