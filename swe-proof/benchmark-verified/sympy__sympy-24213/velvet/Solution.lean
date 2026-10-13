import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The combination step under specification consults, for
--  each addend, its already-collected scale factor and dimension — the results
--  of an UNCHANGED recursive sub-collection, taken here as read-only inputs (a
--  factor and a dimension carrier), not re-derived. The one comparison the step
--  performs — whether two dimensions are dimensionally equivalent — is modeled
--  DEEPLY below (equality of their canonical dimensional-dependency signatures),
--  so it is an A-reference validated against the real dimension-equivalence
--  callee by axiom_check.py (G-AX), NOT a consumed contract. Nothing is borrowed
--  from an outside contract, so there is no axiom to discharge.)
-- axioms-end

-- pure-start
/- A physical dimension, as the combination step observes it. Two distinct
   pieces of information travel with a dimension:

     * `surf` — a handle for the dimension's surface expression identity: two
       dimensions written as the same expression share this handle;
     * `deps` — a handle for the dimension's canonical dimensional-dependency
       signature (the powers of the base dimensions it reduces to), when the
       dimension HAS one: two dimensions that both have a signature are
       *dimensionally equivalent* exactly when this handle is equal, even if
       their surface expressions differ.

   Reducing a dimension to base-dimension powers is a PARTIAL operation: some
   dimensions admit no signature at all, and `deps = none` carries that. Asking
   whether such a dimension is dimensionally equivalent to another is not a
   question the equivalence test answers — the reduction fails before any
   comparison happens.

   Surface-expression equality implies equal signatures, but two surface-distinct
   dimensions can still be dimensionally equivalent (share a signature). -/
structure Dim where
  surf : Int
  deps : Option Int
  deriving DecidableEq, Inhabited

/- One addend handed to the combination step: the scale factor and the dimension
   that have already been collected for it (read-only sub-results). -/
structure Addend where
  factor : Int
  dim : Dim
  deriving Inhabited

/- How the addend-by-addend equivalence test came out. The three cases are
   OBSERVABLY DIFFERENT to a caller and must not be conflated:

     * `equivalent`  — every addend was certified against the reference;
     * `disagreeing` — the test RAN and returned a verdict of "not equivalent":
       both signatures were available and they are different. A caller told this
       learns that the addends' dimensions disagree;
     * `unreducible` — the test could not run at all, because a dimension in play
       admits no signature, so the reduction the test is built on fails before
       any comparison happens. No verdict about equivalence exists here, and a
       caller told this only learns the combination could not be carried
       through. -/
inductive Check where
  | equivalent
  | disagreeing
  | unreducible
  deriving DecidableEq, Inhabited

/- The equivalence test at ONE addend, given how the REMAINING addends came out.
   Which of the three cases holds is decided at this addend, and only falls
   through to the rest when this addend is certified:

     * the reduction is attempted on the reference and on this addend BEFORE any
       comparison, so a missing signature on either side yields `unreducible`
       here — whatever the remaining addends would have given;
     * otherwise both signatures exist, so the test genuinely runs, and unequal
       signatures yield `disagreeing` here;
     * an equal signature certifies this addend and defers to the rest.

   Consequently the LEFTMOST addend that is not certified decides the outcome,
   and it decides it in the manner in which IT failed: an earlier disagreement is
   not overridden by a later missing signature, and an earlier missing signature
   is not overridden by a later disagreement. -/
def checkStep (refDeps : Option Int) (a : Addend) (rest : Check) : Check :=
  if refDeps.isNone || a.dim.deps.isNone then Check.unreducible
  else if a.dim.deps == refDeps then rest
  else Check.disagreeing

/- The equivalence test applied addend by addend against the reference
   signature `refDeps`. Front-recursive, so a single unfold is available per
   loop step and the leftmost addend's verdict is the one that survives. -/
def checkAddends (refDeps : Option Int) : List Addend → Check
  | []       => Check.equivalent
  | a :: xs  => checkStep refDeps a (checkAddends refDeps xs)

/- The total of the addends' scale factors. Front-recursive, matching
   `checkAddends` so the same per-step unfold serves both accumulators. -/
def sumFactors : List Addend → Int
  | []       => 0
  | a :: xs  => a.factor + sumFactors xs

@[grind] lemma checkAddends_nil (r : Option Int) :
    checkAddends r [] = Check.equivalent := rfl
@[grind] lemma checkAddends_cons (r : Option Int) (a : Addend) (xs : List Addend) :
    checkAddends r (a :: xs) = checkStep r a (checkAddends r xs) := rfl
@[grind] lemma sumFactors_nil : sumFactors [] = 0 := rfl
@[grind] lemma sumFactors_cons (a : Addend) (xs : List Addend) :
    sumFactors (a :: xs) = a.factor + sumFactors xs := rfl

/- What the combination step hands back. A reported value and the two
   value-less outcomes are three DISTINCT results, because a caller can tell
   them apart:

     * `reported f d` — a value comes back: scale factor `f`, dimension `d`;
     * `disagreement` — no value comes back, and what the caller is told is
       specifically that the addends' dimensions disagree: the equivalence test
       ran, on signatures it had, and returned "not equivalent". This is the
       report a consumer checking a sum for dimensional consistency relies on,
       so it is a REQUIRED observation and not interchangeable with the one
       below;
     * `noSignature` — no value comes back and no equivalence verdict was ever
       produced, because a dimension in play admits no signature and the
       reduction the test is built on failed first. Nothing about dimensional
       agreement is claimed here; the only obligation is that no value is
       reported. -/
inductive Combined where
  | reported (factor : Int) (dim : Dim)
  | disagreement
  | noSignature
  deriving DecidableEq, Inhabited

/- The result of combining a sum's addends: take the first addend as the
   reference and apply the equivalence test to the rest. If every remaining
   addend is certified, the combined value is reported — its scale factor is the
   total of all addends' factors and its dimension is the reference addend's
   dimension. If the test ran and found an addend not equivalent, the outcome is
   the dimensional-disagreement report. If the test could not run because a
   dimension in play admits no signature, the outcome is the signature-less one.
   The two value-less outcomes are kept apart: which one holds is determined by
   the leftmost addend that is not certified and by the manner of its failure. -/
def combineSpec (first : Addend) (rest : List Addend) : Combined :=
  match checkAddends first.dim.deps rest with
  | Check.equivalent  => Combined.reported (first.factor + sumFactors rest) first.dim
  | Check.disagreeing => Combined.disagreement
  | Check.unreducible => Combined.noSignature
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combining the addends of a sum into a single scale factor and dimension.

   The first addend supplies the reference dimension. Every other addend must be
   dimensionally equivalent to it — two dimensions are equivalent when their
   canonical dimensional-dependency signatures are equal, even if their surface
   expressions are written differently. When all addends are equivalent, the
   reported result is the total of the addends' scale factors paired with the
   reference dimension.

   Otherwise no value is reported, and WHICH of the two value-less outcomes the
   caller is handed is itself observable, so the step must produce the right one.
   When the equivalence test ran and returned "not equivalent" — both signatures
   present, and different — the outcome is the dimensional-disagreement report.
   When the test could not run at all, because a dimension in play has no
   signature and the reduction fails before any comparison, the outcome is the
   signature-less one. The leftmost addend that is not certified decides which,
   in the manner in which it failed.

   `first` and `rest` are read-only: the step consults each addend's
   already-collected factor and dimension and mutates none of them (directive 5);
   it builds a fresh result. -/
method combineAddends (first : Addend) (rest : List Addend)
    return (out : Combined)
  ensures out = combineSpec first rest
  ensures checkAddends first.dim.deps rest = Check.equivalent
            → out = Combined.reported (first.factor + sumFactors rest) first.dim
  ensures checkAddends first.dim.deps rest = Check.disagreeing
            → out = Combined.disagreement
  ensures checkAddends first.dim.deps rest = Check.unreducible
            → out = Combined.noSignature
  do
    -- impl-start
    let mut factor := first.factor
    let mut chk : Check := Check.equivalent
    let mut i := rest.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rest.length
      invariant chk = checkAddends first.dim.deps (rest.drop i)
      invariant factor = first.factor + sumFactors (rest.drop i)
      done_with i = 0
      decreasing i
    do
      let a := rest[i - 1]!
      chk := checkStep first.dim.deps a chk
      factor := factor + a.factor
      i := i - 1
    match chk with
    | Check.equivalent  => return Combined.reported factor first.dim
    | Check.disagreeing => return Combined.disagreement
    | Check.unreducible => return Combined.noSignature
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so a front-recursive fold over `rest.drop (i-1)` peels one
   element. This is the single goal `loom_solve` leaves for the loop body. -/
lemma drop_cons_step {α : Type} [Inhabited α] (xs : List α) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
  have hlt : i - 1 < xs.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct combineAddends by
  loom_solve
  · -- invariant_2 maintained: peel the front element exposed by drop (i-1)
    rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,
        ← invariant_2]
  · -- invariant_3 maintained: the factor accumulator gains rest[i-1]
    rw [drop_cons_step rest i (by omega) (by omega), sumFactors_cons]
    omega
  all_goals (
    -- final: each of the three outcomes matches combineSpec's own case split
    subst done_1
    simp only [List.drop_zero] at invariant_2 invariant_3
    simp only [combineSpec] at *
    simp_all)
