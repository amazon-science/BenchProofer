You are formalizing one task from a software benchmark into a machine-checked
artifact. The checker is $backend, which reads $language, and it is a $kind:
$kind_note

What you write is read by a program. Every rule below is enforced mechanically, so
breaking one gains nothing.

## The file you write

One file, divided into regions by sentinel comments:

```
$comment benchproofer:begin spec
$comment benchproofer:end spec
```

The regions are: `axioms`, `helpers`, `spec`, `impl`, `proof`. `spec` and `impl` are
required; the others are optional. Nothing outside a region is read, except
imports and other file-level preamble, which stay outside every region. A file that
models several functions gives each further one its own `spec`, `impl` and `proof`,
numbered from 2 (`spec.2`, `impl.2`, `proof.2`, then `spec.3`); `axioms` and `helpers`
appear once.

$imports

The split matters: the `spec` region is what Benchproofer shows whoever solves the
formalized task and what "two files share a specification" means, and `impl` is the only
region that later stages are allowed to vary (every `impl` region, where there are
several). Putting part of the specification in `impl`, or part of the implementation in
`spec`, makes every later judgment about this bundle wrong.

## What a good specification is

$tests_rules

* It states what the task requires, in terms of the task's own inputs and outputs.
  It does not restate the golden patch's steps: a specification that
  says "does what this code does" is satisfied by that code and by nothing else,
  which is useless in both directions.
* It is strong enough that a wrong implementation fails it. If a plausible wrong
  implementation satisfies your specification, the specification is the defect.
* It is weak enough that any correct implementation passes it. Pinning down one
  algorithm marks a different correct implementation wrong.
* Its preconditions and parameter types admit every input the task allows, and no more.

$domain_rules

## Callees the fix does not change

$assumptions

## Never

* $banned
* Do not weaken an obligation to make the checker accept the file. A rejected file
  that states the right property is worth more than an accepted file that does not.
* Do not compute the expected result inside the specification and require the
  implementation to agree with it. The `spec` region is shown to whoever solves the
  formalized task, so a specification that contains a working solution gives away the
  implementation and the bundle is rejected for it. State the properties the result has
  instead.
* Do not leave a placeholder, a `TODO`, or an unproved assumption in place of work.

$guidance
