This checker reports whether the file elaborates, and $shape. A rejection therefore
proves nothing by itself. The witness is what makes it evidence: a claim, at one concrete
input, that $claim.

It is checked in a copy of the file with the proof region emptied, so nothing the bundle
proves can interfere, and it is appended to two files -- the $subject, where it has to
hold, and the reference implementation, where it has to fail. So:

* State it as an `example`, `theorem` or `lemma`, and prove it. A claim you cannot close
  against the $subject is not a witness.
$placement$where
* Assume nothing: the claim is about one concrete input, so it binds no hypothesis and no
  value, and a binder is refused.$unassumable
* Write it with no `benchproofer:` sentinel of any kind. The witness is not a region of the
  file but a claim beside it, and a sentinel in it names a region the format does not have,
  which Benchproofer refuses.
* Name $anchors in the statement itself, not only in the proof. A claim that merely tells
  the two implementations apart shows they differ, which is not a defect in either.
* Use only names the solution file also declares. A claim about a helper your $subject
  added fails against the solution file as an unknown name, which is not the same as
  failing because the specification holds there.
* No `sorry`, no `axiom`, no `native_decide`. Those hold of anything, so they would make
  the witness elaborate against the reference implementation too, defeating both halves
  at once.
* Prefer an input on which `decide` succeeds: concrete literals, small values, nothing
  opaque. Where the type that represents the value will not reduce -- a loop the checker
  resolves through classical choice, a rational's inverse -- state the refutation over a
  projection whose reduction does not go through it (a sum, a length, one coordinate), or
  hand the blocked arithmetic over as `decide +kernel` rewrites.
* A claim over `String` operations does not reduce under `decide`: they are compiled
  constants the kernel will not unfold, so `decide` reports the proposition is not
  decidable however concrete the input is. Close such a claim with
  `by simp +ground +decide` instead, naming the definitions `simp` has to unfold.
* $none
