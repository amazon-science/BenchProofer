# Prove `$file`

`$file` is a $language file the checker has not accepted. What it said:

```
$diagnostics
```

$kind

## What is yours to write

$editable

## Your tools

$tools_rules

Nothing else decides whether the file is accepted: run `$tools verify $file` after every
edit, and read the goal it prints before the next one.

Write every file of your own under `$scratch/` -- a variation you elaborate by hand, a
scratch lemma, a note. The checker's workspace is shared with other runs, so nothing goes
there, and nothing outside `$workspace` is yours to write.

$playbook

## Submit

Call the submit tool with `status` -- `ok` once `verify` accepts the file, `stuck` with the
goal and the property you would need, or `fail` when what the file claims is false, as
above, with the input that shows it -- and `notes` on the strategy you used.
