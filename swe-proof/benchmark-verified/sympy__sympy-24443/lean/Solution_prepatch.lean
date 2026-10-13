import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature. The codomain is a genuine
-- group, so its multiplication, integer powers, and identity are modeled with
-- Mathlib's `Group` structure (not axiomatized). The two finite lookups
-- (symbol → generator, generator → codomain element) are modeled as ordinary
-- total functions supplied as inputs. The word-evaluation is modeled DEEPLY
-- (`evalWord`, a product over the word); it consumes no opaque callee, so there
-- is no A-consumed axiom and no A-reference `opaque` declaration. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The codomain element a relator word evaluates to under a valuation of
generators. A word is a list of `(symbol, exponent)` pairs; each symbol names a
generator (`genOf`) whose assigned codomain element is `imageOf`, and the word's
value is the ordered product of those elements raised to their exponents.
Front-recursive so the accumulator loop in the implementation can be related to
it by induction. -/
def evalWord {Sym Gen G : Type*} [Group G]
    (genOf : Sym → Gen) (imageOf : Gen → G) : List (Sym × Int) → G
  | [] => 1
  | (s, p) :: rest => imageOf (genOf s) ^ p * evalWord genOf imageOf rest
-- pure-end

-- post-conditions-start
/-- A valuation of generators (`genOf` mapping each symbol to a generator,
`imageOf` mapping each generator to an element of the codomain group) extends to
a homomorphism of the presented group exactly when every defining relator word
evaluates to the codomain identity. The decision result is `true` precisely in
that case. -/
def problem_spec_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) (result : Bool) : Prop :=
  (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
-- post-conditions-end

-- impl-start
def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) : Bool := Id.run do
  for r in rels do
    let w : G := Id.run do
      let mut acc : G := 1
      for sp in r do
        let g := genOf sp.1
        -- PRE-PATCH BUG: a word entry with a negative exponent (an inverted
        -- generator) fails the membership test that recovers its generator, so
        -- its factor is silently skipped — only non-negative-exponent entries
        -- contribute. A relator that depends on an inverted generator is then
        -- wrongly judged non-trivial.
        if sp.2 ≥ 0 then
          acc := acc * imageOf g ^ sp.2
      return acc
    if w ≠ 1 then
      return false
  return true
-- impl-end

-- proof-start
theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) :
    problem_spec_checkRelators genOf imageOf rels
      (implementation_checkRelators genOf imageOf rels) := by
  -- carries the gold proof obligation; UNCLOSABLE against the buggy impl: on a
  -- relator containing an inverted generator (a negative-exponent entry) whose
  -- omission makes the partial product non-identity, the spec demands `true`
  -- yet this impl returns `false` (G-DIFF signal; mirrors F2P `test_homomorphism`).
  sorry
-- proof-end
