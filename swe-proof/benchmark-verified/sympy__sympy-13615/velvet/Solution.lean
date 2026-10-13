import Velvet.Std
-- imports-end

set_option maxHeartbeats 1000000
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The three possible verdicts of the membership oracle. -/
inductive Trit where
  | inside
  | outside
  | unknown
  deriving DecidableEq, Inhabited

/- The ambient set's membership oracle, as a deterministic three-valued map over
   element handles. For one element it answers: decided-positive (the element is
   in the ambient set), decided-negative (the element is not in the ambient set),
   or undetermined (membership cannot be decided from the element alone — e.g. a
   free symbol whose value is unknown). It is an UNCHANGED callee the operation
   consults; declared `opaque` (not `axiom`) so it carries no asserted value
   contract — only determinism (a given element handle denotes a single
   determinate verdict) — and so it is computable inside the executable `do`
   block. There is
   thus nothing to over-claim; the trit ↔ real-oracle bijection is validated by
   axiom_check.py (G-AX) and mapping.md §3. -/
opaque contains : Int → Trit
-- axioms-end

-- pure-start
/- The definite members of the relative complement: exactly the elements the
   oracle decides are NOT in the ambient set. An element kept here is asserted to
   belong to the result. Front-recursive so a single unfold is available per loop
   step (the fold pattern, plan §5.4). -/
def definiteOut : List Int → List Int
  | []      => []
  | el :: rest =>
      (if contains el = Trit.outside then [el] else []) ++ definiteOut rest

/- The undetermined elements: exactly those the oracle can decide neither way.
   They are retained separately so they are held for symbolic handling rather
   than asserted to be members of the result. Front-recursive (same pattern). -/
def symbolicUnknown : List Int → List Int
  | []      => []
  | el :: rest =>
      (if contains el = Trit.unknown then [el] else []) ++ symbolicUnknown rest

@[grind] lemma definiteOut_nil : definiteOut [] = [] := rfl
@[grind] lemma definiteOut_cons (el : Int) (rest : List Int) :
    definiteOut (el :: rest)
      = (if contains el = Trit.outside then [el] else []) ++ definiteOut rest := rfl
@[grind] lemma symbolicUnknown_nil : symbolicUnknown [] = [] := rfl
@[grind] lemma symbolicUnknown_cons (el : Int) (rest : List Int) :
    symbolicUnknown (el :: rest)
      = (if contains el = Trit.unknown then [el] else []) ++ symbolicUnknown rest := rfl

/- The result of the operation: the elements split into the definite members and
   the elements retained for symbolic handling. The third class — those decided
   to be inside the ambient set — appears in neither field (they are excluded). -/
structure Partition where
  definite : List Int
  symbolic : List Int
  deriving Inhabited

/- Generic drop/peel: dropping one fewer element exposes the element at `i-1` on
   the front. Used to peel one element off the input per loop step. -/
lemma drop_pred_cons (xs : List Int) (i : Nat)
    (hi : 0 < i) (hlt : i - 1 < xs.length) :
    xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The relative complement of a finite collection of element handles against an
   ambient set, computed from the ambient set's three-valued membership oracle.
   Each element is classified once: a decided-positive element is excluded from
   the result entirely; a decided-negative element is a definite member; an
   element whose membership is undetermined is retained for symbolic handling
   rather than asserted to be a member. The collection is read-only (`elems` is
   not `mut`): the routine reads it and assembles a fresh two-part result
   (directive 5). The two fields are pinned exactly as the two membership-keyed
   selections of the input. -/
method complementFinite (elems : List Int) return (out : Partition)
  ensures out.definite = definiteOut elems
  ensures out.symbolic = symbolicUnknown elems
  do
    -- impl-start
    let mut def_ : List Int := []
    let mut sym : List Int := []
    let mut i := elems.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ elems.length
      invariant def_ = definiteOut (elems.drop i)
      invariant sym = symbolicUnknown (elems.drop i)
      done_with i = 0
      decreasing i
    do
      let el := elems[i - 1]!
      def_ := (if contains el = Trit.outside then [el] else []) ++ def_
      sym := (if contains el = Trit.unknown then [el] else []) ++ sym
      i := i - 1
    return { definite := def_, symbolic := sym }
    -- impl-end

/- The backward-fold step for the definite selection: dropping one fewer element
   exposes the element at `i-1` on the front, so `definiteOut` peels one keyed
   entry. One of the two goals `loom_solve` leaves for the loop body. -/
lemma definiteOut_drop_step (xs : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    definiteOut (xs.drop (i - 1))
      = (if contains xs[i - 1]! = Trit.outside then [xs[i - 1]!] else [])
          ++ definiteOut (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  rw [drop_pred_cons xs i hi hlt, definiteOut_cons]

/- The backward-fold step for the undetermined selection (same shape). -/
lemma symbolicUnknown_drop_step (xs : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    symbolicUnknown (xs.drop (i - 1))
      = (if contains xs[i - 1]! = Trit.unknown then [xs[i - 1]!] else [])
          ++ symbolicUnknown (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  rw [drop_pred_cons xs i hi hlt, symbolicUnknown_cons]

prove_correct complementFinite by
  loom_solve
  · rw [definiteOut_drop_step elems i (by omega) (by omega)]; simp_all
  · rw [symbolicUnknown_drop_step elems i (by omega) (by omega)]; simp_all
