# Attack the specification of $task

The bundle is at `$bundle/`: `$solution` is the solution file, holding the specification,
the reference implementation and its proof, and `../task.json` beside the bundle is the
task, with its statement and the golden patch as a unified diff (`../reference.patch`).
`$repository/` is the repository at the task's base commit, a copy of your own. Work only
in `$scratch/`: every file you submit is written there.

$tests

$tests_rules

Your job is two-sided, and the two sides are not the same check.

## Wrong implementations the specification must refuse

Write at least $attacks distinct **wrong** implementations, each a copy of `$solution`
that writes only the regions named below, and put each to the specification. Across them,
try the kinds of wrong implementation a specification most often lets through:

$attack_rules

## Correct implementations the specification must accept

Write $controls **correct** implementations, each written differently from `$solution` and
from one another, and put each to the specification. At least $min_controls of them must be
accepted; one you are sure is correct but cannot get accepted is still filed, as the rules
below say, and counts toward the $controls.

$control_rules

$regions

## Your tools

$tools_rules

Put each submission to the checker with `$tools verify` and judge it with `$tools try`, and
run a program with `$tools run` when you want to see what the real code does. Under this
checker, $kind_note A row of `try` reading `verified` and `wrong` is an attack that succeeds:
a wrong implementation the specification accepts, the finding. A file the checker cannot read
decides nothing, and one it refutes because its proof is missing a step is evidence about what
you wrote, not about the specification.

File each attack with its equivalent patch, a diff to the repository making the same change, in
a file of its own passed with `--patch`. An attack the checker accepts is then judged by one
rule. Where `conformance.py` with your implementation in it tells it apart from the repository,
the attack succeeds: its implementation is wrong. Where a program shows it does what the
reference implementation does -- the two executed on the same drawn inputs, `conformance.py`
over what it compares, or a proof -- and no input they were executed on tells the two apart,
the attack fails: its implementation is correct, since the specification accepted that behavior
in its own implementation. Otherwise its patch decides: the attack succeeds where the
benchmark's tests reject the patch. One whose patch they pass is left to the attack validation
auditor, who rules whether the behaviour it changes belongs to what the task requires, even
where the two, executed on the same drawn inputs, differ on an input; where it files a witness
test that passes on the fixed code and fails with the patch (below), that auditor rules whether
what the test cites asks for what the test checks. An attack shown to do what the reference
implementation does, whose patch the tests reject, is left to that auditor too. `try` says
which.

$patch_rules

## Witness tests

The benchmark's tests can be weak: an attack whose equivalent patch they pass may still break
a behaviour the statement asks for, or one a test checks, on an input no test builds. A witness
test shows it. It is a Python program in a file of its own, passed to `$tools try` with
`--test`, that Benchproofer runs twice where the benchmark's tests run: once on the fixed code,
with the golden patch applied, and once with the attack's equivalent patch applied in place of
the golden patch. It has to pass the first time and fail the second, and it cites what it
checks, passed with `--cites` and filed in a field of its own: a sentence of the statement,
quoted character for character, or the id of a FAIL_TO_PASS test, or of a PASS_TO_PASS test
the test patch adds or edits. When it passes the first time, fails the second and cites
something, the attack validation auditor rules whether what it cites asks for the behaviour it
checks, and the attack succeeds where it does. $citation_rules A witness test that fails on the fixed code, passes with the patch, or cites nothing is
evidence of nothing, and the attack is judged as though it had none. It runs as `$tools run`
runs a program, so it sets up first what the repository's own tests set up, and it checks the
behaviour it cites rather than the text of the code.
$refutation

$on_record

## Submit

Call the submit tool with every attack and control you wrote, each as its path under
`$scratch/` and a claim: for an attack, what it gets wrong and on which input; for a
control, how it computes the result and how that differs from the reference
implementation, and for one the checker still refuses, what you tried. Give an attack's
equivalent patch as the path of its diff file, and its witness test, where it has one, as the
path of the program, with what it cites.

A defect you showed by running code that no attack of yours shows -- an input the
specification admits on which it promises what the repository does not do -- goes under
`defects`: what is wrong; the function `conformance.py` compares it on, by the name its
`compared` lines print; the input, as the arguments that function is called with, written as a
Python tuple literal that `ast.literal_eval` reads back; what the repository does on it as you
ran it; and what the specification states there. $compared Benchproofer hands the input to
`conformance.py` with the inputs on record, so where the implementation and the repository
disagree on it, `impl.conformance` fails. A defect without such a function and input is not
filed.
