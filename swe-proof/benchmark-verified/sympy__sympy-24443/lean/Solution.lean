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
  have inner_loop : ∀ (r : List (Sym × Int)) (acc : G),
      (forIn r acc (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)
        = acc * evalWord genOf imageOf r := by
    intro r
    induction r with
    | nil => intro acc; simp [evalWord]; rfl
    | cons hd tl ih =>
      intro acc
      rw [List.forIn_cons]
      show forIn tl (acc * imageOf (genOf hd.1) ^ hd.2) _ = _
      rw [ih]
      obtain ⟨s, p⟩ := hd
      simp [evalWord, mul_assoc]
  simp only [problem_spec_checkRelators, implementation_checkRelators, Id.run, bind, pure]
  have key : ∀ r : List (Sym × Int),
      (forIn r 1 (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)
        = evalWord genOf imageOf r := by
    intro r; rw [inner_loop]; simp
  simp only [key]
  induction rels with
  | nil => simp
  | cons hd tl ih =>
    rw [List.forIn_cons]
    by_cases hw : evalWord genOf imageOf hd = 1
    · simp only [hw, ne_eq, not_true_eq_false, if_false]
      simp only [List.forall_mem_cons, hw, true_and]; exact ih
    · simp [hw]

-- proof-end
