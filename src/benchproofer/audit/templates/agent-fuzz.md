# Attack what the specification of $task assumes

The bundle is at `$bundle/`: `$solution` is the solution file, and `../task.json` beside
the bundle is the task, with the golden patch in `../reference.patch`. `$repository/`
is the repository at the task's base commit, a copy of your own. Work only in `$scratch/`.

The `axioms` region of `$solution` states something of these unchanged callees, by an axiom
or by a definition modeling one, rather than establishing it, so the proof holds only as far
as those do:

$callees

The bundle ships its own check of those, `axioms.py`, which agreed. Your job is
to disagree. For each callee, write a Python program that runs it for real, in the
environment the benchmark's own tests run in, and hunts for one input where it does
something the assumption does not allow.

$fuzz_rules

Each program has to follow this protocol, which is what the gate reads:

$protocol

$reference

$witnesses

## Your tools

$tools_rules

Run every program you submit at least once with `$tools fuzz`, and fix one that crashes: a
fuzzer that dies on its first input attacks nothing.

## Submit

Call the submit tool with one program per callee: its path under `$scratch/`, the callee
it attacks, and a claim saying what it tests, in one sentence.
