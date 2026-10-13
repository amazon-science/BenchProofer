# Formalize $task

Write the specification of this task and an implementation the checker accepts against it,
in one file. Adversarial reviewers will then try to break it: they write wrong
implementations the specification must refuse and correct ones it must accept, and the
gates run the repository's own code against it. You never weaken a contract to pass a gate;
a principled BLOCKED beats a faked specification.

## What you have

Everything is under `$workspace`:

* `$file` is the file you write. It holds a well-formed file for this checker, to show the
  shape; replace it with the complete file for this task, its sentinel comments included.
* `$task_file` is the task: its statement, the golden patch, and every FAIL_TO_PASS test
  (`oracle.tests`) and PASS_TO_PASS test (`oracle.regression`) by name.$reference
* `$repository/`, a copy of your own, holds $copy. ${tests_state}**The real function is
  the ground truth.**
$fixed* `$scratch/` is yours: put every file of your own there.

## Read before you write

Derive the specification from the statement, the golden patch, the tests and the real
source, and from nothing else. Before you write anything, read:

1. the statement;
2. the golden patch;
3. the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or edits, each in full
   as it reads in `$repository/`: the test, and the fixtures, helpers and data it uses, since
   what it asserts is what the specification has to state;
4. the PASS_TO_PASS tests that call a function the fix changes, found by searching
   `$repository/` for the calls: they are among the tests whose inputs the rule for the
   model's domain is about;
5. the changed functions AND their callees, and the state they read: the source of each
   callee the changed code calls, and each attribute, module-level name or setting the
   changed functions read.

$tests

$sites

$frame_rules

## Run the checker yourself

$tools_rules

Nothing else decides whether the file is accepted: run `./tools verify $file` after each
edit, and read what it prints before the next one, until it accepts the file or the budget
ends. Check a variation of your own in `$scratch/` the same way, and run a program with
`./tools run` to see what the real code does on an input.

A file the checker cannot finish in its time is not accepted: simplify the model, don't pile
on annotations. A verification failure is information: read the assertion location;
strengthen invariants or fix how the implementation translates the fix. If a
genuinely-required contract is unprovable in this checker's logic, that is BLOCKED, not a
license to delete it.

## What you may not do

* Do not read, search for, copy, or consult any pre-existing formalization of this task: no
  other tool's or run's bundle for it, and nothing from another run.
* Do not read the source of Benchproofer, which judges this file, or its prompts: they
  cannot tell you what is true of the real function.
* Write nothing but `$file` and the files under `$scratch/`: nothing in the task, the
  repository or the bundle beside the file. Run no git command that writes.

## Report

You have $budget, and no more: at that point the session is stopped wherever it is. Spend it
roughly so -- read, then write, then run the checker -- and if you have not run the checker
by the time half of it is gone you are on the path that runs out of time. What you leave in
`$file` is taken whatever you report, and the rest of the bundle is drafted against it once
the checker accepts it.

Call the submit tool once:

* the status: `VERIFIED` once `./tools verify` accepts the file, `BLOCKED` otherwise;
* two sentences saying what the specification models and how;
* each repository function it models;
* each unchanged callee the changed code calls: whether you modelled it under a `models`
  line or made it an axiom, where it is defined (file:line), and what it does;
* what the fix changes that the specification does not model, and why, and each input the
  model's domain leaves out as an `Outside the bridge` entry, of which of its three kinds:
  `correspondence.md`, drafted after you, starts its `Not modeled` and `Outside the bridge`
  from these two fields;
* when `BLOCKED`, what stands in the way and what you tried;
* the last lines the checker printed on your file.
