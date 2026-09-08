<!-- Part of the agentic-decision-rights skill. Read from SKILL.md at point of need. Licence: CC BY-NC-SA 4.0, see LICENSE and NOTICE beside SKILL.md. -->

# The escalation log

One JSONL line per firing, written by the loop, not by this skill:

```json
{"ts":"2026-09-07T09:14:22Z","grant":"invoice-match","case":"INV-88213",
 "why":"3 rounds, no PO line within tolerance","decided":"approve at variance 1.4%",
 "reason":"freight surcharge, supplier contract clause 7","by":"a.chen","seconds":410,
 "inputs":{"invoice":"s3://ap/INV-88213.json","po":"s3://ap/PO-41190.json"},
 "outcome":{"held":true,"observed":"2026-10-04","source":"AP dispute register"}}
```

`why` and `reason` carry the clustering. A log without the reason records that a decision happened
and nothing about how to make it again.

`inputs` and `outcome` are what turn a cluster into a promotion. **A decision is not an outcome.**
Repeated agreement records that people agreed, not that they were right, and Q3 asks whether the
outcome came back. `inputs` has to be enough to replay the case, by reference or by value, or
saying what a predicate would have done to the history is a guess dressed as a backtest.

Most logs carry `why`, `decided` and `reason` and nothing else: enough to cluster, not to promote.
