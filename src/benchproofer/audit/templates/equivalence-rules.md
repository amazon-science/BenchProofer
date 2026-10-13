This matters because everything else rests on it. The benchmark's tests vouch for the
golden patch, not for whatever else might satisfy the specification. If the implementation
quietly does something else -- handles a kind of input the golden patch does not, returns a
different value on some input, fixes a second defect along the way -- then a proof about
this file is a proof about a task the benchmark never posed.

Compare each function of the implementation with the function of the fixed code it
corresponds to, as `correspondence.md` maps them. What the golden patch changes in a
function the bundle does not model, and `correspondence.md` lists under `Not modeled`, is
not this question: whether leaving it out loses part of the task is judged separately,
against the task.

$tests_rules

Compare behavior, not text, and do it operation by operation. For each operation the
implementation performs, name the operation the golden patch performs in its place, and say
which of exactly six kinds of correspondence the two stand in:

* `identical` -- the same concrete operation: integers, booleans, control flow. A different
  name for a variable or a helper, a different loop or recursion shape computing the same
  values in the same order, a helper inlined or a block factored out, is still the same
  operation.
* `refinement` -- the same operation over a type that spells the values more precisely than
  the original could, where every value the original admits is still admitted and no new one
  is. State the operation reads that the model takes as a parameter -- an option the tests
  set, the rows of a table -- is a refinement of that state where `correspondence.md` says how
  the parameter maps onto it, and so is a result the model states only part of where
  `correspondence.md` names the part.
* `modeled` -- a call of a callee whose behavior the golden patch does not change, computed
  by a definition under its `benchproofer:models <callee>` line in the `axioms` region, which
  `axioms.py` and an independent fuzzer put to the real callee. A definition anywhere else or
  without that line, or one representing a function the golden patch adds or changes, is not
  `modeled`: the row is `changed`.
* `axiom` -- an operation the implementation does not perform itself but assumes: a call of a
  callee whose behavior the golden patch does not change, represented by an assumption that
  states only what that callee really does. A callee's result the model takes as a parameter
  is not an `axiom`, and where nothing below allows it, its row is `changed`. Never assume the function under spec or an operation the golden patch changes: an
  assumption about a callee the golden patch changes takes the fixed behavior as given, so the
  proof assumes the fix, and its row is `changed`, whatever else holds of it. Behavior decides
  whether the golden patch changes a callee, not whether the patch touches its text: it changes
  the callee when what the call reaches in the fixed tree -- the callee's own code or a
  function it calls -- is code the golden patch adds or edits, and on some input the call can
  pass its result differs from what the call reached before the fix -- it raises where that
  returned, or returns another value or a value of another type. So a callee the golden patch
  only makes reachable under a new module or name, where what runs is code that was there
  before the fix, is unchanged although the patch wrote the binding, and a function the golden
  patch adds with code of its own is changed.
* `unchanged` -- behavior the fix leaves as it was, which the implementation leaves out or
  abstracts and `correspondence.md` lists under `Not modeled`: an option the fix does not
  touch that the model takes no parameter for, formatting the fix does not change. The code
  before the fix is what it is compared against, as for anything the fix does not touch, and
  the fixed code does there what that code did. Behavior the fix changes is never
  `unchanged`, and neither is a departure `Not modeled` does not name. Nor is behavior on an
  input the model's domain has to admit, as below, and leaves out: unless an `Outside the
  bridge` entry names it and passes its check, the domain leaves out an input the tests use,
  which is a finding: give the verdict `unsound`.
* `unbridged` -- the operation does what the golden patch does on every input the type
  bridge covers, and differs only on inputs listed under `Outside the bridge`. An entry that
  fails its check (below) is not outside the bridge, and neither is an input the list does
  not name: a difference there is `changed`.

Those six are the only correspondences that leave behavior alone. Anything else is an operation
the golden patch does not perform, `changed`, and one is enough to make these two different
programs: report it as a finding and give the verdict `unsound`, however small it looks -- a
guard the golden patch does not have, a different result on an empty input, a different error,
a different order of observable effects. Check the rows of `correspondence.md` rather than
trusting them: a row it calls `identical` that is not is the finding this review exists for.

`conformance.py` compares the implementation against the real patched repository function,
and its repository side is trusted code: a disagreement between that side and the
implementation fails the conformance gate, and nothing mechanically checks that it is the
repository's code. For each function the golden patch changes that the specification
models, the repository side of `conformance.py` must call the repository's code -- the
function itself, imported from the repository, or the repository's code that runs it, as the
benchmark's tests reach it. A copy of that code written into `conformance.py`, or a
comparison that would agree with the code before the fix on what the fix changes, is a
finding: give the verdict `unsound`, and quote the lines.

Which callees the fix leaves unchanged, and how one is stated:

$callee_rules

What the model's domain has to admit, and what `Outside the bridge` may name:

$domain_rules

$outside_rules

Where you are shown what repairs changed since the bundle was drafted, hold each
precondition and each `Outside the bridge` entry a repair added to the same check. One that
excludes only inputs of the three kinds above, and passes its check, is not a narrowing. Nor is
a change that widens the domain -- an input case added, a precondition dropped, a parameter
type that admits every value it admitted and more: it shuts out nothing. One that shuts out any
other input the specification admitted before -- an input on which the repository returns,
or raises -- is a narrowing, whatever reason it gives: there the implementation is no longer
set against the golden patch at all. Report it as a finding and give the verdict `unsound`.
Where you are shown inputs `conformance.py` did not compare because an `Outside the bridge`
entry names them, trace each through the function before the fix and after it: one on which
they run different lines, apart from the false test of a condition the golden patch adds, is
outside no entry, and skipping it is a narrowing, reported the same way.

$environment_rules A difference of any of these kinds is not `changed` either.
