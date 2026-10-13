The task is the task as the golden patch resolves it: a specification is compared against
the repository with the golden patch applied, because the benchmark's tests vouch for that
code and for nothing else. The code before the fix is what a specification is compared
against only for what the fix does not touch: compared with it, a correct specification
differs on exactly what the fix changes, and reporting that as a defect condemns a correct
specification.

$tests_rules Ask of each obligation: could an implementation satisfy this specification and
still fail one of the FAIL_TO_PASS tests or of the PASS_TO_PASS tests the test patch adds or
edits?

$task_rules

A specification fails this question in three ways, and they are not the same:

* **Interface too narrow.** Name a behaviour those tests require, or a change the fix makes
  that the statement asks for -- an output, a side effect, an input dimension, a downstream
  consequence -- that the specification's signatures and obligations do not constrain at
  all. Faithfulness is to what the fixed code actually computes and calls, transitively, not
  to the shape of the diff.
* **Contract too weak in scope.** An obligation about such a behaviour that a result other
  than the fixed code's also meets, on an input those tests build, does not state it: name
  the input and the other result.
* **The specification demands something the task does not:** a particular algorithm, a
  stricter precondition than the task allows, an output shape the task leaves open. A
  correct implementation would then be marked wrong. A domain that leaves out an input the
  domain rule below has it admit is this case: no attack can reach those inputs, so the
  tests that use them hold the specification to nothing. So is a specification that pins an
  incidental behavior, as above.

For each, name the input that shows it: one on which the obligations admit a result the fixed
code does not return, or one on which what the fixed code does is something the specification
refuses. A defect you cannot put an input to is a matter of wording, not of behavior, and is not
a finding.

Judge the specification region, not the implementation: the question is what the
specification would accept, not what this implementation happens to do. Ignore anything the
task does not decide, and ignore matters of taste.

$domain_rules

## Coverage first

List every behaviour of a function the fix changes -- what it returns, raises or modifies,
for which inputs -- including in a function the specification does not model at all. A
function the fix touches only in its layout, its comments or its docstring is not one it
changes, and neither is one whose only change is a refactor that keeps its behaviour -- a
helper inlined, a value computed in another order -- unless undoing that refactor fails one
of the benchmark's tests: list no row for either. One row per behaviour, with the test that
checks it and the obligation that states it: these rows are the coverage table, and a
behaviour an obligation states is covered. Name a test by its id as the task lists it, and
leave that field empty -- not `none` -- when neither a FAIL_TO_PASS test nor a PASS_TO_PASS
test the test patch adds or edits checks the behaviour. A behaviour only another PASS_TO_PASS
test checks is such a row: what holds the specification to it is the contract above, over a
domain that admits the inputs that test hands the function.

A behaviour on inputs for which the fixed function runs only what the golden patch leaves as it
was, and which neither the FAIL_TO_PASS tests nor the PASS_TO_PASS tests the test patch adds or
edits check, is outside the table as well: an `Outside the bridge` entry of the third kind
naming those inputs accounts for it.

Not everything a fix changes is the task: an incidental behaviour's row has the test field
empty, and leaving it out of the obligations is not a finding, though leaving its inputs out
of the domain can be, as above. A change the statement asks for has no test either, and
leaving it out is a finding.

$frame_rules A callee whose behaviour the fix leaves as it was may be modeled, or represented
by an axiom the result passes through, which keeps the model small; what may not happen is that
no obligation constrains it at all. A model handed the callee's result cannot get the call
wrong:

$callee_rules

For each FAIL_TO_PASS test, name the input it builds and every value its assertions compare,
with the obligation that states each -- a compared value no obligation states is interface
too narrow -- and say what the bundle's pre-fix implementation, in `twins/`, returns on that
input. The test fails on the code before the fix, so on that input the pre-fix
implementation should give a result the test rejects. One that already passes the test does
not have the bug: either the model cannot tell the buggy result from the fixed one there,
so the interface is too narrow, or the pre-fix implementation is not the code before the
fix. Either is a finding. A test that fails on the code before the fix only because it uses
a name the golden patch adds -- an import of it, a constant it defines, a function the
test's fixture calls -- or only because the fixed code returns the same content in another
Python type the model's types do not represent, the integer 5 where the code before it
returns the string "5", is set aside from this check, since no specification may write those
names or tell those types apart, and still counts for coverage; one whose failure before the
fix is a different value, a missing behaviour or a wrong exception is not.

A row is checked whether or not the fix changes the behaviour, so a test naming it needs an
obligation either way. `Not modeled` and `Outside the bridge` in `correspondence.md` are the
author's account of what was left out. `Not modeled` excuses neither a tested behaviour no
obligation states nor an input the domain leaves out, and an `Outside the bridge` entry that
fails its check excuses neither: a row with a test and no obligation is a finding, whatever
that document says about it.

$outside_rules
