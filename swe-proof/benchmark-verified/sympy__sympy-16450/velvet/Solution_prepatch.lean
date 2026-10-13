import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The property-closure engine: given a consistent set of declared boolean
   property facts for a symbol, it returns the full set of facts derivable from
   them under the domain's inference rules. It is an UNCHANGED callee, modeled
   deeply as an uninterpreted function (no property of it is consumed by the
   proof). Provenance + executable soundness check: mapping.md §3.1 /
   axiom_check.py (G-AX). -/
axiom closeProps : List (String × Bool) → List (String × Bool)
-- axioms-end

-- pure-start
/- A symbol, reduced to the only two observations the operation reads:

   * `props` — the symbol's already-declared property facts (each a `(name,
               value)` pair with a resolved boolean; undetermined facts are
               absent).
   * `sign`  — whether the symbol's sign is already determined: `some _` when it
               is known (positive or not), `none` when it is undetermined. -/
structure Sym where
  props : List (String × Bool)
  sign : Option Bool
  deriving Inhabited

/- The property set of a symbol's surrogate. A symbol whose sign is already
   determined is left as-is, keeping its own properties. A symbol whose sign is
   undetermined is replaced by a positive surrogate whose property set is the
   closure of "positive together with the symbol's already-declared properties":
   positivity is asserted WITHOUT discarding what was already known. -/
@[grind] noncomputable def surrogate (s : Sym) : List (String × Bool) :=
  if s.sign = none then
    closeProps (("positive", true) :: s.props)
  else
    s.props

/- The surrogate property set of every symbol, in input order. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
noncomputable def surrogatesAll : List Sym → List (List (String × Bool))
  | []      => []
  | s :: ss => surrogate s :: surrogatesAll ss

@[grind] lemma surrogatesAll_nil : surrogatesAll [] = [] := rfl
@[grind] lemma surrogatesAll_cons (s : Sym) (ss : List Sym) :
    surrogatesAll (s :: ss) = surrogate s :: surrogatesAll ss := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section
method makeSurrogates (symbols : List Sym)
    return (out : List (List (String × Bool)))
  ensures out = surrogatesAll symbols
  do
    -- impl-start
    -- Pre-image skeleton: the positive surrogate is built from positivity ALONE,
    -- discarding the symbol's already-declared properties (`closeProps
    -- [("positive", true)]` rather than `closeProps (("positive", true) ::
    -- s.props)`). The frozen spec requires `surrogate`, which preserves the
    -- declared properties, so prove_correct MUST fail.
    let mut result : List (List (String × Bool)) := []
    let mut i := symbols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ symbols.length
      invariant result = surrogatesAll (symbols.drop i)
      done_with i = 0
      decreasing i
    do
      let s := symbols[i - 1]!
      let r : List (String × Bool) :=
        if s.sign = none then closeProps [("positive", true)] else s.props
      result := r :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `surrogatesAll` peels one `surrogate`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma surrogatesAll_drop_step (symbols : List Sym) (i : Nat)
    (hi : 0 < i) (hle : i ≤ symbols.length) :
    surrogatesAll (symbols.drop (i - 1))
      = surrogate symbols[i - 1]! :: surrogatesAll (symbols.drop i) := by
  have hlt : i - 1 < symbols.length := by omega
  have hcons : symbols.drop (i - 1) = symbols[i - 1]! :: symbols.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, surrogatesAll_cons]

prove_correct makeSurrogates by
  loom_solve
  rw [surrogatesAll_drop_step symbols i (by omega) (by omega)]
  simp_all
