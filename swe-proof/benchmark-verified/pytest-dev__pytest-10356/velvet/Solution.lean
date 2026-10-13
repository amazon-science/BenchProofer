import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No foreign callee is consumed as an axiom, and none is folded away as a
   convenience. The canonicalizing step the collection finishes with — taking the
   annotation out of each assembled raw element, and REFUSING the whole
   collection when an element makes none available — is modeled DEEPLY below
   (`markOf` / `canonicalize`), as is the assembly it is applied to
   (`flattenSeq`). Both deep models are validated against the real
   sub-computations out of band (mapping.md §3, axiom_check.py / G-AX). -/
-- axioms-end

-- pure-start
/- A canonical annotation (an opaque identity token; equality is all that is
   observed). -/
abbrev Mark := Int

/- One RAW element of a source's attached-annotation list, as it is actually
   found there. The three shapes are distinguished because the collection treats
   them differently:

     * `canonical m` — already a canonical annotation; taken as it stands;
     * `wrapped m`   — an applicator object that carries the annotation `m`
       inside it; the annotation is taken OUT of it (this is the ordinary shape
       when a source's list is written by hand);
     * `foreign n`   — an element from which NO annotation can be obtained: it is
       no annotation itself and carries none. `n` is its own identity token, the
       one a refusal names.

   `canonical` and `wrapped` both make an annotation available; only `foreign`
   does not. -/
inductive Item where
  | canonical (m : Mark)
  | wrapped (m : Mark)
  | foreign (n : Int)
  deriving DecidableEq

/- What a collection yields. Either it produced a canonical annotation sequence,
   or it REFUSED, naming the offending element: an element it was asked to
   canonicalize makes no annotation available, and then the collection produces
   no sequence at all — the refusal is the observable result, not a
   silently-skipped element, not a substituted annotation, and not an empty
   sequence. -/
inductive Outcome where
  | refused (offending : Int)
  | collected (ms : List Mark)
  deriving DecidableEq

/- The annotation a raw element makes available, if any. -/
def markOf : Item → Option Mark
  | Item.canonical m => some m
  | Item.wrapped m   => some m
  | Item.foreign _   => none

/- The identity token a raw element is known by — for an element that makes no
   annotation available, this is what a refusal names. -/
def nameOf : Item → Int
  | Item.canonical m => m
  | Item.wrapped m   => m
  | Item.foreign n   => n

@[grind] lemma markOf_canonical (m : Mark) : markOf (Item.canonical m) = some m := rfl
@[grind] lemma markOf_wrapped (m : Mark) : markOf (Item.wrapped m) = some m := rfl
@[grind] lemma markOf_foreign (n : Int) : markOf (Item.foreign n) = none := rfl

/- The in-order concatenation of a sequence of per-source raw element lists: the
   elements contributed by the first source, then those of each subsequent
   source, and nothing else. A source that contributes none appears as an empty
   element and is simply skipped without ending the assembly. Front-recursive
   (one unfold per source) so a backward impl loop that prepends one source's
   elements each step can discharge the value equality (the fold pattern,
   plan §5.4). -/
def flattenSeq : List (List Item) → List Item
  | []      => []
  | g :: gs => g ++ flattenSeq gs

@[grind] lemma flattenSeq_nil : flattenSeq [] = [] := rfl
@[grind] lemma flattenSeq_cons (g : List Item) (gs : List (List Item)) :
    flattenSeq (g :: gs) = g ++ flattenSeq gs := rfl

/- A single-source assembly is just that source's own elements. -/
@[grind] lemma flattenSeq_singleton (g : List Item) : flattenSeq [g] = g := by
  simp [flattenSeq]

/- Put one annotation in front of a collection's outcome. A refusal stays that
   same refusal: once the collection has been refused, no annotation is carried
   out of it. -/
def consMark (m : Mark) (o : Outcome) : Outcome :=
  match o with
  | Outcome.collected ms => Outcome.collected (m :: ms)
  | Outcome.refused n    => Outcome.refused n

/- Canonicalize an assembled element sequence, IN ORDER: every element must make
   an annotation available, and that annotation — not the element it came out of
   — is what the resulting sequence carries, at the same position. If an element
   makes none available, the whole collection is REFUSED and yields no sequence,
   naming the FIRST such element: the obligation is discharged element by element
   from the front, never assumed away and never postponed. Front-recursive, one
   element per unfold. -/
def canonicalize : List Item → Outcome
  | [] => Outcome.collected []
  | it :: rest =>
      match markOf it with
      | none   => Outcome.refused (nameOf it)
      | some m => consMark m (canonicalize rest)

@[grind] lemma canonicalize_nil : canonicalize [] = Outcome.collected [] := rfl

/- Extend a collection's outcome with one further annotation at the end. A
   refusal stays that same refusal — nothing is recorded on top of a collection
   that was refused. -/
def withMark (o : Outcome) (mark : Mark) : Outcome :=
  match o with
  | Outcome.collected ms => Outcome.collected (ms ++ [mark])
  | Outcome.refused n    => Outcome.refused n

@[grind] lemma withMark_collected (ms : List Mark) (mark : Mark) :
    withMark (Outcome.collected ms) mark = Outcome.collected (ms ++ [mark]) := rfl
@[grind] lemma withMark_refused (n : Int) (mark : Mark) :
    withMark (Outcome.refused n) mark = Outcome.refused n := rfl
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; none are module-level)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Collect the annotations of a class. `lineage` is the ordered sequence of the
   per-source raw element lists that may contribute, the class's own list first.
   When `wholeLineage` is true every source in the lineage contributes (so
   annotations applied to any ancestor are kept, not just those of the nearest
   one); when false only the class's own list (the first element) does. The
   contributing sources are assembled in order, and the assembled elements are
   then canonicalized: each yields the annotation it makes available, and the
   collection is REFUSED as a whole — naming the first offender — if some
   assembled element makes none. Elements of sources that do NOT contribute are
   never canonicalized, so they cannot refuse a collection they take no part in.
   `lineage` is read-only. -/
method collectMarks (lineage : List (List Item)) (wholeLineage : Bool)
    return (out : Outcome)
  ensures out =
    canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
  do
    -- impl-start
    -- Select which sources contribute: the whole lineage, or only the class's
    -- own list; then concatenate the selected sources in order. The fold runs
    -- from the back, prepending each source's elements before those already
    -- gathered, yielding their in-order concatenation. The assembled elements
    -- are canonicalized before they leave.
    let selected : List (List Item) :=
      if wholeLineage then lineage else [lineage.headD []]
    let mut gathered : List Item := []
    let mut i := selected.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ selected.length
      invariant gathered = flattenSeq (selected.drop i)
      done_with i = 0
      decreasing i
    do
      let g := selected[i - 1]!
      gathered := g ++ gathered
      i := i - 1
    return canonicalize gathered
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `flattenSeq` peels one source's elements off the
   front of its output. This is the single goal `loom_solve` leaves. -/
lemma flattenSeq_drop_step (xs : List (List Item)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    flattenSeq (xs.drop (i - 1)) = xs[i - 1]! ++ flattenSeq (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, flattenSeq_cons]

prove_correct collectMarks by
  loom_solve
  rw [flattenSeq_drop_step
        (if wholeLineage = true then lineage else [lineage.headD []]) i
        (by omega) (by omega)]
  simp_all

/- Record a freshly-applied annotation on a class: the class's new own list is
   the canonicalization of its existing own list, extended with the new
   annotation at the end. The existing own elements are obtained by collecting
   WITHOUT the lineage (only the class's own), so applying an annotation never
   absorbs ancestors' annotations into the class's own list; and if that own list
   holds an element making no annotation available, the whole recording is
   REFUSED — the new annotation is not recorded on top of a refusal, and the
   offending element is not dropped. `lineage` and `mark` are read-only. -/
method attachMark (lineage : List (List Item)) (mark : Mark)
    return (out : Outcome)
  ensures out = withMark (canonicalize (lineage.headD [])) mark
  do
    -- impl-start
    let own ← collectMarks lineage false
    return withMark own mark
    -- impl-end

prove_correct attachMark by
  loom_solve
