<!-- Part of the agentic-decision-rights skill. Read from SKILL.md at point of need. Licence: CC BY-NC-SA 4.0, see LICENSE and NOTICE beside SKILL.md. -->

# Limits

Carry these into the output. They are the parts of the framework that do not solve the problem,
and the things this skill will not do for you.

- **This skill does not decide the number, or the owner.** How many rounds, what threshold, what
  deadline, how many consistent decisions justify a promotion: all the owner's call, dependent on
  the cost of being wrong and how clean the feedback was. Any number you were not given is
  `[UNOWNED]`, and the skill can prove an owner is missing but cannot supply one.
- **Reference is bounded by what it was told to check.** A passing suite settles that the suite
  passed; a schema settles shape, not truth.
- **Estimate fails quietly.** A badly calibrated number looks like a well calibrated one: under
  uncertainty a guess with a decimal point, under ambiguity theatre however precise.
- **Challenge buys independence, not verification.** Huang et al. (2023) found language models
  cannot reliably self-correct without external feedback, and Panickssery et al. (2024) found LLM
  evaluators recognise and favour their own generations. Song (2026) measured fresh-session review
  beating same-session by F1, 28.6% against 24.6%, a real gain and not a big one, so do
  not treat a second model as verification solved. At minimum give the reviewer a new session and
  a clean context. A different vendor's model is a risk-reduction preference, not something either
  study establishes.
- **Authority is a claim to accountability, not knowledge.** Routing to a person makes the call
  owned, not correct, and costs the throughput the loop existed to buy.
- **Reversibility is the gate with the least prior art.** Published loop-failure taxonomies mostly
  do not interrogate it, so expect less to lean on.
- **A static read cannot see run time.** Whether the escalation gets read, and the owner is there
  when it fires, needs the run.
- **Classification is not permission.** A clean pass narrows the options; it is not evidence that
  automating the decision is a good idea.
- **Tool access is declared, not enforced.** `allowed-tools` grants Read, Grep, Glob, Bash and
  Write, and Write is needed for the register, so the promise never to edit your source is a rule
  this skill follows, not one the harness can stop it breaking. Review the register diff.
