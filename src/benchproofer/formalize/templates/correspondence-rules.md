`correspondence.md` says how the bundle's `impl` regions correspond to the golden patch,
operation by operation, so that a reviewer asking whether the implementation is a
translation of the golden patch has a claim to check rather than a program to
reverse-engineer. It has four sections, in this order, each under its own `##` heading.

**`## Symbols`.** One bullet per function the specification models: the repository function
it represents, as a dotted path and `file:line` at the base commit, and how each value it
takes and returns corresponds to the repository's own. Together these are the type bridge:
how each of the specification's types maps onto the repository's values. A value the model
spells in a different type than the repository does is where a comparison of the two goes
wrong, so state each correspondence rather than leaving it to be guessed.

**`## Operations`.** A table mapping every operation in the `impl` regions to the operation
the fix performs in its place, each tagged with one of the five kinds below, which leave
behavior alone, or with `changed`, which does not:

* `identical` -- the same concrete operation: integers, booleans, control flow. A different
  name for a variable or a helper, a different loop or recursion shape computing the same
  values in the same order, a helper inlined or a block factored out, is still the same
  operation.
* `refinement` -- the same operation over a refined type that represents the value; state
  the bijection. For example `row[j]` over `list[int]` for `self[i, j]` over a matrix, or
  `len(row)` for `other.cols`. Only the type that represents a value is refined: an
  operation the fix adds or edits is not a refinement of anything, whatever type it is
  spelled in. State the code reads that the model takes as a parameter -- an option the tests
  set, the rows of a table -- is a refinement of that state: say how the parameter maps onto
  it. So is a result the model states only part of: name the part.
* `modeled` -- a call of an unchanged callee the implementation computes itself, by the
  definition the `axioms` region holds under its `benchproofer:models <callee>` line. Name
  the definition.
* `axiom` -- an operation the implementation does not perform itself but assumes: a call of an
  unchanged callee represented by an assumption in the `axioms` region that states only what
  that callee really does. Name the assumption. Which callee is unchanged, and whether it is
  modeled or an axiom, is the system prompt's `Callees the fix does not change`.
* `unbridged` -- the operation does what the golden patch does on every input the type
  bridge covers, and differs only on inputs listed under `Outside the bridge`.

An operation that is none of these five is one the fix does not perform. Give it a row of
its own tagged `changed` and say what it does differently, rather than forcing it into
one of them: a reviewer reads this table to find exactly that row. Every hunk of the
fix that changes behavior needs a row, or an entry in the next section.

**`## Not modeled`.** Say what the fix changes that the specification does not model, and
why: documentation, configuration, a function with no behavior of its own to specify, or
code the checker cannot reach. Name each by its file or function. Write `Nothing.` if the
specification models all of it. A reviewer judging whether the specification covers the task
reads this section first, and an omission it does not state reads as one nobody noticed. A
behavior checked by the FAIL_TO_PASS tests or by the PASS_TO_PASS tests the test patch adds or
edits, and a change the statement asks for, are never ones to leave out: a specification that
leaves one out does not cover the task, whatever this section says about it.

**`## Outside the bridge`.** $outside_rules

When there is no such input, the section is the one line `Nothing.`, with no reason given:
anything else written under its heading is read as an entry. A reviewer comparing the
implementation with the fix sets a difference aside only on an input this section names,
and checks that it holds.
