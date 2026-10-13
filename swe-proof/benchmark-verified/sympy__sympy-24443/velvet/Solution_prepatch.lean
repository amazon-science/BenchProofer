import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"
set_option linter.unusedSectionVars false

open TotalCorrectness DemonicChoice

/- The codomain is an arbitrary group `G`. A *word* is presented by its
   syllables — a list of `(symbol, exponent)` pairs, where `symbol : Nat`
   identifies a generator and `exponent : Int` is the (possibly negative)
   power that generator is raised to in that syllable. An *assignment*
   `assign : Nat → G` sends each generator symbol to a codomain element. -/
variable {G : Type} [Group G] [Inhabited G]

-- axioms-start
-- axioms-end

-- pure-start
/- The value of a word under an assignment: the ordered product, syllable by
   syllable from left to right, of each generator's assigned codomain element
   raised to that syllable's exponent. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). The exponent is a
   signed integer (`zpow`), so a syllable's contribution is `assign sym ^ p`
   for every `p : Int` — negative exponents invert. The group `G` need not be
   abelian, so the left-to-right order is significant. -/
def wordProd (assign : Nat → G) : List (Nat × Int) → G
  | []               => 1
  | (sym, p) :: rest => assign sym ^ p * wordProd assign rest

omit [Inhabited G] in
@[grind] lemma wordProd_nil (assign : Nat → G) :
    wordProd assign ([] : List (Nat × Int)) = 1 := rfl

omit [Inhabited G] in
@[grind] lemma wordProd_cons (assign : Nat → G) (sym : Nat) (p : Int)
    (rest : List (Nat × Int)) :
    wordProd assign ((sym, p) :: rest) = assign sym ^ p * wordProd assign rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method evalWord (assign : Nat → G) (syllables : List (Nat × Int)) return (out : G)
  ensures out = wordProd assign syllables
  do
    -- impl-start
    -- Pre-image skeleton: a syllable whose exponent is negative is silently
    -- skipped — its factor never enters the running product. The frozen spec
    -- requires the full ordered product over every syllable (including the
    -- ones with negative exponent), so prove_correct MUST fail.
    let mut result : G := 1
    let mut i := syllables.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ syllables.length
      invariant result = wordProd assign (syllables.drop i)
      done_with i = 0
      decreasing i
    do
      let s := syllables[i - 1]!
      let factor : G := if s.2 ≥ 0 then assign s.1 ^ s.2 else 1
      result := factor * result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer syllable exposes the syllable at
   `i-1` on the front, so `wordProd` peels one factor. This is the single goal
   `loom_solve` leaves for the loop body. -/
omit [Inhabited G] in
lemma wordProd_drop_step (assign : Nat → G) (syllables : List (Nat × Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ syllables.length) :
    wordProd assign (syllables.drop (i - 1))
      = assign (syllables[i - 1]!).1 ^ (syllables[i - 1]!).2
          * wordProd assign (syllables.drop i) := by
  have hlt : i - 1 < syllables.length := by omega
  have hcons : syllables.drop (i - 1) = syllables[i - 1]! :: syllables.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, wordProd_cons]

prove_correct evalWord by
  loom_solve
  rw [wordProd_drop_step assign syllables i (by omega) (by omega)]
  simp_all
