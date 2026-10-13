## How these proofs usually go

`prove_correct <method> by loom_solve` asks Loom for the method's verification conditions
and discharges what it can. What it leaves is closed after it, one bullet per goal
(`· simp_all [...]`, `omega`, a `rw` with a lemma of yours), in the order Loom states them.

* A `while` loop needs an `invariant` for every fact the postcondition rests on -- the
  bounds of the index, and what the accumulated state equals so far (`st = (xs.take
  i).foldl step init` is the usual shape) -- a `decreasing` measure, and `done_with` for
  the exit condition when it is not the negated guard. These annotations are yours to
  change; the statements of the loop are not.
* A fact about one more step of a fold (`(l.take (i + 1)).foldl f b = f ((l.take i).foldl
  f b) l[i]!`) is the usual lemma a loop body leaves; prove it once, before
  `prove_correct`, inside the `proof` region.
* Unfold a pure definition the goal mentions with `simp [name]` or `unfold name`, and let
  `omega` close linear arithmetic over the indices.
* Never cite `trust_smt`, and never reach for `loom_solve_async`, which admits what it
  solved: let `loom_solve` and the tactics after it prove every goal.
