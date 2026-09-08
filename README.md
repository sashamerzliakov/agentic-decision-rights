# ADR

Agentic decision rights, as executable artefacts.

An agent loop's exit condition is a grant of authority: it decides what the agent settles
alone and what it hands back to a person. Most loops grant that authority to a number nobody
chose. This project turns the framework for choosing it into things you can run.

## What is here

| Path | What it is |
|---|---|
| `skills/agentic-decision-rights/SKILL.md` | A Claude Code skill. Audits a codebase for unowned grants, designs a grant for a new loop, and harvests escalation logs into promoted exit predicates. |
| `skills/agentic-decision-rights/references/` | The grant record template, the escalation log shape, the article's worked examples and the limits, loaded by the skill at point of need. |
| `skills/agentic-decision-rights/scripts/` | `detect.sh`, the exit-point detectors, and `scan.py`, the deterministic checks: candidates, silent exhaustion, register freshness, log shape. |
| `skills/agentic-decision-rights/LICENSE` | CC BY-NC-SA 4.0, so the licence travels with the installed folder. |
| `skills/agentic-decision-rights/NOTICE` | The attribution that has to travel with the work. |
| `PROCESS.md` | Step by step: what the skill does in each mode, how, and why each step matters. |

## Using the skill

Copy the folder to `~/.claude/skills/agentic-decision-rights/` and it becomes available to
any Claude Code session. The scripts need bash and Python 3, nothing else. For what happens
at each step, and why, read `PROCESS.md`.

### First run, in five lines

1. `cp -R skills/agentic-decision-rights ~/.claude/skills/`
2. Open Claude Code in the repo you want audited and confirm it loaded with `/skills`.
3. Say: **"audit this repo for agentic decision rights"**. Point it at a path if the loop lives
   in one place: "audit `src/agents/` for unowned grants".
4. It asks where the register goes, then writes `docs/decision-rights/README.md` plus one record
   per exit point that earns one. It never edits your source, and it proposes diffs in chat
   instead. In a scripted or scheduled run with nobody to ask, it defaults to
   `docs/decision-rights/` in the repo being audited and says so in the output.
5. You get back one row per exit point, in this shape:

```txt
| Exit | Demand x Knowledge | Gates | Settles | Bound | Hands back on | To | Owner | Status |
| src/review.js:88 | rule x risk | two-way, recurs | Estimate, score >= 0.8 | 3 rounds | score < 0.8 at round 3 | [UNOWNED] | [UNOWNED] | draft |
```

Two `[UNOWNED]` cells are the finding, not a failure: the skill proves an owner is missing and
will not invent one.

For a loop that does not exist yet, say **"design decision rights for this loop"** and describe
the decision. For an escalation log, say **"harvest this escalation log"** and give the path.

It also runs by hand: the questions, the matrix and the record template are a procedure a person
can follow without any agent tooling.

## Where the framework comes from

https://hcd.ai/agentic-ai/agentic-decision-rights/

## Licence

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Use it, adapt it,
share it, for non-commercial purposes, as long as you credit the source and release any
adaptation under the same licence. Full text in `LICENSE`, and a copy inside
`skills/agentic-decision-rights/` so an installed folder carries its own licence and
attribution.

Commercial use is not barred, it is by arrangement. If you want to use the skill or an
adaptation of it commercially, get in touch via https://hcd.ai/contact/.

Attribution means: "Sasha Merzliakov, https://hcd.ai/agentic-ai/agentic-decision-rights/".

## Contributing

Pull requests are welcome. By submitting one you license your contribution under
CC BY-NC-SA 4.0 and grant Sasha Merzliakov a perpetual, irrevocable right to use, adapt
and relicense it, including commercially, so the project can be maintained as one work.

## Status

Version 0.5.0. The skill has been through three Codex review lenses, five Opus review rounds
and one cold test from a fresh session, and every detector command has been run on JavaScript,
Python, Go, Rust and Java code. Findings go to the issue tracker on this repository.
