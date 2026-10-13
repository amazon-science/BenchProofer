import Mathlib
-- imports-end

/-!
Composing two arrangements.

An arrangement is a finite reindexing (a permutation of `0 … n-1`) carried as its
mapping together with a tag identifying the *family* it belongs to — a base
family and any number of distinct specialised families that refine it.

Composing arrangement `self` with arrangement `other` produces a new arrangement
whose two observable parts are determined as follows:

  * its **mapping** is the composition of the two mappings: where the second
    operand has fewer entries than the first it is first completed by the
    identity so both range over the same indices, and then the first mapping is
    applied through the second (with any trailing entries of the completed second
    mapping carried over). When the second operand is empty the first mapping is
    returned unchanged.

  * its **family** is the family of the left operand: the arrangement obtained
    from a composition belongs to the same family as the value the composition
    was taken on, so a value of a specialised family composes to a value of that
    same specialised family.

Both parts are pinned to the inputs, so no component of the result is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The two observable parts of the
-- result — the composed mapping and the family tag — are both built directly
-- from the inputs (a list computation and a field copy), so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- An arrangement: its `arr` mapping (a list of indices) together with a `fam`
tag identifying its family (`0` is the base family; any other value a distinct
specialised family). -/
structure Arr where
  arr : List Int
  fam : Nat
deriving Repr, DecidableEq

/-- Complete the shorter mapping `b` with identity entries so it ranges over at
least the indices `0 … a.length-1`, leaving it unchanged when it is already at
least that long. -/
def completeTo (b : List Int) (n : Nat) : List Int :=
  b ++ (List.range' b.length (n - b.length)).map (fun k => (k : Int))

/-- The composition of two mappings, matching the index-wise definition: the
first mapping `a` is applied through the completed second mapping, and any
trailing entries of the completed second mapping beyond `a`'s length are carried
over. An empty second mapping leaves the first unchanged. -/
def composeArr (a b : List Int) : List Int :=
  if b = [] then a
  else
    let bc := completeTo b a.length
    (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
-- pure-end

-- post-conditions-start
/-- The produced arrangement is fully pinned to the two operands:

  * its mapping is exactly the composition of the two mappings, and
  * its family is exactly the family of the left operand.

Both components are determined for every input, so nothing is left free. -/
def problem_spec_mul (self other : Arr) (result : Arr) : Prop :=
  result.arr = composeArr self.arr other.arr ∧ result.fam = self.fam
-- post-conditions-end

-- impl-start
def implementation_mul (self other : Arr) : Arr := Id.run do
  let a := self.arr
  let b := other.arr
  let mut perm : List Int := a
  if b ≠ [] then
    let bc := completeTo b a.length
    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
  return { arr := perm, fam := self.fam }
-- impl-end

-- proof-start
theorem correct_mul :
    ∀ (self other : Arr),
      problem_spec_mul self other (implementation_mul self other) := by
  intro self other
  unfold problem_spec_mul implementation_mul composeArr
  by_cases h : other.arr = []
  · simp only [Id.run, h, if_pos, ite_not]
    exact ⟨rfl, rfl⟩
  · simp only [Id.run, h, ite_not]
    exact ⟨rfl, rfl⟩
-- proof-end
