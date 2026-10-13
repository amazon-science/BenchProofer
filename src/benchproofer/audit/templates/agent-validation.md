# Rule on the attacks and controls for $task that execution cannot determine

The bundle is at `$bundle/`: `$solution` is the solution file, holding the specification,
the reference implementation and its proof, and `correspondence.md` says how its
implementation corresponds to the fix. `$statement` is the task's statement, and
`../task.json` beside the bundle is the task. The golden patch is `../reference.patch`, and
what it changes is this:

$fix

$tests

`$repository/` is the repository at the task's base commit, a copy of your own. Work only
in `$scratch/`.

## What you rule on

The attack auditor of this review wrote implementations to test the specification: attacks,
wrong implementations it should refuse, and controls, correct ones written differently from
the reference implementation that it should accept. Benchproofer ran each, with the files the
attack auditor filed in `$bundle/audit/`: through the checker, through `conformance.py` with
the implementation in place of the reference implementation, and, for an attack, its
equivalent patch through the benchmark's tests, and its witness test where it filed one. Each
attack and control below is one that cannot be determined by execution: those runs cannot tell
right from wrong, or contradict each other, so what remains is a question about the task or
about a proof, and you rule on it. Each comes with what
Benchproofer established and with the attack auditor's claim. Treat the claim as something to
check, never as a ruling you inherit.

Each is one of four kinds, named by what Benchproofer established:

* **The checker accepts it, and the benchmark's tests do not reject it.** An attack. Rule
  whether the behaviour it changes belongs to what the task requires: the task requires a
  behaviour when the statement asks for it, or when a FAIL_TO_PASS test, or a PASS_TO_PASS test
  the test patch adds or edits, checks it. What Benchproofer found may name an input on which it does
  something other than the reference implementation, or say that `conformance.py` agrees with
  it over the inputs it drew; neither decides it, since the specification may leave out a
  behaviour the statement does not ask for and no test checks. Rule `succeeds` when it breaks
  a behaviour of the fixed code the task requires, even though every test passes: the
  specification accepts a wrong implementation. Rule `fails` when it breaks nothing the task
  requires.
* **The checker accepts it, the benchmark's tests do not reject it, and its witness test passes
  on the fixed code and fails with its equivalent patch.** An attack, with a Python program
  Benchproofer ran twice where the benchmark's tests run: once on the fixed code, and once with
  the attack's equivalent patch in place of the golden patch. Rule whether what the test cites
  asks for the behaviour the test checks, on the input it runs. $citation_rules Rule `succeeds`
  when what it cites asks for that behaviour: the specification accepts a wrong
  implementation. Rule `fails` when it does not.
* **The checker accepts it, and the benchmark's tests reject its patch.** An attack a program
  found does what the reference implementation does: the two executed on the same drawn
  inputs, through `conformance.py`, or by proof. Rule whether the model or the patch is at
  fault. Rule `succeeds` when the patch does what the implementation does: the specification
  accepts a patch the tests reject, so the model cannot see a behaviour they check. Rule
  `fails` when the patch changes something its implementation does not, or fails only because
  a test replaces, on the object itself, a method whose model its implementation computes
  instead of calling it: that shows a call the model does not represent, not a wrong result.
* **The prover refuses it, and nothing shows the specification is what refuses it**, or **the
  checker refutes it, and nothing decided whether it is a correct implementation.** A control.
  Rule whether it is correct, and whether the specification is what refuses it. Correct means
  it does what the fixed code does on every input the repository can produce, and breaks
  nothing the statement asks for. Rule `too_strong` when it is correct and the specification
  refuses it: the specification then demands something the task does not, usually a behaviour
  of the golden patch it should leave open, an incidental one, which the statement does not
  ask for and neither the FAIL_TO_PASS tests nor the PASS_TO_PASS tests the test patch adds or
  edits check.
  Rule `unproved` when it is correct, but the checker rejected a step of its own proof rather
  than the specification: the attack auditor's claim says what it tried, and a proof you write that
  the checker accepts shows it. One whose open goal is about what an axiom returns, where the
  axiom says nothing that decides it, is not unproved: no body can supply that proof, the
  golden patch's included, so the specification is what refuses it. Rule `incorrect` when it
  does something other than the fixed code on an input the repository can produce.

## What a ruling names

Each ruling names the input it rests on, and what of the task it rests on: a sentence of the
statement, quoted character for character from `$statement`; the id of a FAIL_TO_PASS test,
or of a PASS_TO_PASS test the test patch adds or edits; or, for a control the specification
refuses, the obligation that refuses it, quoted. For an attack with a witness test, the input is
the one the test runs, with the behaviour it checks there, and what the ruling rests on is what
the test cites. A ruling that does not name both counts as no ruling.
Show the input: run the real code on it with `$tools run`, put a candidate to the checker
with `$tools verify`, and judge an implementation with `$tools try`. A candidate is a copy of
`$solution`:

$regions

Judge at the level the specification abstracts the code to. A model abstracts the
repository's values -- integers for characters, lists for arrays, an axiom for a callee the
fix leaves alone -- so a difference its types cannot express is not a behaviour an attack
breaks. Rule an attack successful only for a behaviour the task requires and the
specification leaves free.

## The faithfulness auditor's coverage table

$coverage

## The attacks and controls execution cannot determine

$cases

## Your tools

$tools_rules

## Submit

Call the submit tool with `rulings`, one entry for each attack or control above:

* `id`: the id of the attack or control;
* `ruling`: for an attack `succeeds` or `fails`; for a control `too_strong`, `unproved` or
  `incorrect`;
* `input`: the input the ruling rests on;
* `rests_on`: the sentence, the test or the obligation it rests on, as above;
* `why`: what you ran, and what it showed.

Rule on every attack and control above. One you leave without a ruling, or with a ruling that
does not name its input and what it rests on, is put to you once more; left so again, it counts
neither for nor against the specification.
