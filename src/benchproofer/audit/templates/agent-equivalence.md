# Is the implementation of $task the one in the golden patch?

The bundle is at `$bundle/`: `$solution` is the solution file, and `correspondence.md` sets
each operation of the implementation against the one the fix performs in its place. It also
gives the type bridge -- how each of the specification's types maps onto the repository's
values -- with what the implementation leaves out under `Not modeled`, and the inputs on
which it is not set against the golden patch under `Outside the bridge`. `../task.json`
beside the bundle is the task, and `../reference.patch` is the benchmark's fix, the golden
patch. `$repository/` is the repository at the task's base commit, a copy of your own.
Work only in `$scratch/`.

$equivalence_rules

${inputs_rules}$modeled

$added

$port

$conformance

$programs

## Your tools

$tools_rules

Where you are unsure whether two operations agree, run them, in the one environment the
rules above describe: with `$tools run`, or judge an implementation as the gates will with
`$tools try --as control`. An implementation you put to it is a copy of `$solution`:

$regions

$findings

## Submit

Call the submit tool with `verdict` (`sound` when the two agree on every input, `unsound`
when they do not, `uncertain` only when the golden patch is too incomplete to compare
against), `summary` (one sentence), `operations` (one entry per operation of the
implementation, with its kind and the implementation's operation set against the golden
patch's), `findings` (one per difference in behavior), and `checked` (one entry per thing
you checked and found clean, with what you ran, which is recorded and is not a finding).
Account for the whole implementation: a `sound` verdict with no operation behind it is an
opinion nobody can check.
