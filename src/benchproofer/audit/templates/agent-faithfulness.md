# Does the specification of $task describe the task?

The bundle is at `$bundle/`: `$solution` is the solution file, `correspondence.md` says how
its implementation corresponds to the fix and what it leaves out under `Not modeled`, and
`../task.json` beside the bundle is the task, with its statement. The golden patch is
`../reference.patch`, and what it changes is what is below, not what the specification or
the repository suggests:

$fix

Read off its code, the functions it changes are these; one it touches only in its layout,
its comments or its docstring is not among them:

$functions

$tests

`$repository/` is the repository at the task's base commit, a copy of your own. Work only
in `$scratch/`.

$faithfulness_rules

${inputs_rules}## Your tools

$tools_rules

Show each input you name: run the real code on it with `$tools run`, or put a candidate to the
checker with `$tools verify`. A candidate is a copy of `$solution`:

$regions

$findings

$earlier

## Submit

Call the submit tool with:

* `verdict`: `sound` when every behavior those tests check, and every change the statement
  asks of the fix, is covered and the specification demands nothing beyond them, `unsound`
  when it does not, and `uncertain` only when the task itself is too vague to say;
* `summary`: one sentence saying why;
* `coverage`: the table, one row per behavior;
* `findings`: one entry per defect, each with the input that shows it and what you ran, and
  none when the verdict is `sound`;
* `checked`: one entry per thing you checked and found clean, each with what you ran. It is
  recorded with your judgment, and nothing in it is a finding.
