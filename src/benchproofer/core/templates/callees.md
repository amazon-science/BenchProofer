$callee_rules

An axiom is $how. A definition that models a callee sits under its `models` line, and an axiom
under its `axiom` line:

    $models
    $axiom

`<callee>` on either line is the callee itself, as the dotted Python path it is defined at --
its module, then its name, a method under its class: `json.loads`, `pkg.module.Class.method`
-- whatever this file calls the declaration under the line. The program that checks it
against the real callee imports it by that path, and runs against the fixed code when the
path leads into a file the golden patch changes.

A program drafted after this file runs each against the real callee where the benchmark's own
tests run; a disagreement fails the bundle, as does an assumption outside the `axioms` region,
where it would replace work the file was supposed to do.
