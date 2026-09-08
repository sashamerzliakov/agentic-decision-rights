<!-- Part of the agentic-decision-rights skill. Read from SKILL.md at point of need. Licence: CC BY-NC-SA 4.0, see LICENSE and NOTICE beside SKILL.md. -->

# Worked examples, from the source article

## Reading the matrix: the invoice check

An invoice check asks whether the bill matches what was
ordered and what arrived. The purchase order already fixed what correct looks like, so the demand
is **Skill**, and a trusted order says whether the numbers match, so the knowledge is **Risk**.
Down those two columns, Reference and Authority both hold dots. Reference settles, Exhaustion's
ring is the budget setting the ceiling, and Authority is who the loop hands to once that ceiling
is hit.

## Promotion: the invoice loop in three builds

The source article's invoice loop, in three builds. **Checker only**: a working agent matches
the invoice, a separate checker validates the match, and a failure goes back to the same agent to
correct, with no ceiling on how many times. **Ceiling plus person**: a fourth failure stops the
loop and hands the case to a named person, whose decision goes on to payment and is logged with
their reason. **Precedent in front of the person**: failures over three go to a third agent,
*resolve*, reading settled cases and proposing a match that returns to the checker to confirm.

The ceiling, once set, never moved. What moved is where a failure lands once it hits it, and every
mismatch a person resolves becomes another store entry.

Note what promotion did **not** do. Run the procedure on the proposal, Rule x Uncertainty, and
the matrix settles it on **Challenge**, a second checker build three does not add; **Estimate**
holds only a ring there, so it proposes and cannot settle. Build three routes the proposal into
the existing Reference check instead of straight to payment, only an unmatched case reaches a
person, and the missing Challenge is recorded as the gap. A promotion that routes around the
check rather than into it is a removed control.
