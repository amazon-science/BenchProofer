# Does the specification of $task give away the implementation?

`$spec` holds everything a solver, whoever solves this formalized task, is shown besides
the task statement, which is `$statement`: the bundle's specification, with the
implementation and the proof of it elided. `$before` is the code as it stood before the
fix, which a solver has in front of it too. There is nothing else in this workspace, on
purpose.

Decide one question: **could a solver recover an implementation from the specification
itself, without solving the task?**

$disclosure_rules

## Submit

Call the submit tool with `verdict` (`sound` when the specification describes the requirement
without disclosing an implementation, `unsound` when a solver could read an implementation
off it, `uncertain` only when you cannot tell), `summary` (one sentence), `findings` (one
per place that gives away the implementation, none when the verdict is `sound`), and
`checked` (one entry per place you checked and found discloses nothing, which is recorded
and is not a finding). Each finding opens with the construct it names -- `loop:`,
`intermediate:`, `table:`, `literal:` or `oracle:` -- and quotes the line of `$spec` it
rests on.
