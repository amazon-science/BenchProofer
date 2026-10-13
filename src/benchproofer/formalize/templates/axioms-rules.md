The `axioms` region represents each unchanged callee it names by an axiom, which the checker
took on trust, or by a definition under a `benchproofer:models` line, which it took to compute
what the callee computes. That makes the proof worth exactly what those are worth, so
`axioms.py` is a program that checks each of them against the callee it represents, in the
environment the benchmark's own tests run in.

Rules Benchproofer checks:

* $verbatim
* $protocol
* It calls every unchanged callee the `axioms` region names, the callee itself, imported from
  where the task's code imports it, and not a copy of its code: Benchproofer records which
  functions the run calls, and one the run never calls fails the bundle, as does one the
  program never reports `grounded`.
* It is a program, not a test suite. It runs with no arguments, prints its protocol
  lines, and exits.

How to write it: for each axiom, draw inputs that satisfy its own preconditions --
boundary values and random ones -- run the real callee on each, and check that every
observation meets what the axiom states. For each modeled callee, draw the inputs the
changed code can give it, run the real callee and the definition on each, and check that
they return, raise and modify the same things. Call the callee the way the task's code
calls it: find the call the axiom or the definition represents, and pass every argument
that call fixes exactly as it passes it -- a flag such as `html.escape`'s `quote=True`, a
class handed in by keyword, a mode or an encoding -- because a call with other arguments
tests a program the task never runs. Check only what the axiom or the definition states: a
property it does not state is not one the proof relies on, and a failure of it refutes
nothing the checker was given. Draw the awkward inputs too -- empty, boundary,
malformed, unicode -- because an assumption that only holds for tidy inputs is where a
proof about this task stops being about the program the benchmark ships.

$reference
