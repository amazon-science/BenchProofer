import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The field-restriction map this operation builds is
--  keyed by a model identity normalized to its CANONICAL form before use. That
--  normalization is modeled DEEPLY as a per-entity map over the
--  input carrier (`canonOf`/`keysOf` below); the carrier is the relation-chain
--  itself, not an outside contract. There is no `axiom` declaration and no
--  A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One model encountered while walking a relation chain, carrying only the two
   identities the operation observes: `ident`, the model exactly as reached
   through the relation (which may be an alternate/derived view of an underlying
   model), and `canon`, that model's canonical underlying identity. For a plain
   model the two coincide (`ident = canon`); for a derived view they differ, and
   only the canonical identity is the stable key the downstream consumer indexes
   by. -/
structure Entity where
  ident : Int
  canon : Int
deriving Inhabited, DecidableEq

/- The key an entity contributes to the field-restriction map: its CANONICAL
   identity. Selecting `canon` (not the surface `ident`) is what makes a derived
   view and its underlying model collapse to one key — the single behavioral
   change this operation requires. -/
def canonOf (e : Entity) : Int :=
  e.canon

/- The sequence of map keys for a whole relation chain: the canonical identity
   of every entity, in order. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern). Because each entity contributes
   its canonical identity, an entity reached as a derived view keys the same as
   its underlying model — exactly what a consumer indexing by the canonical
   identity demands. -/
def keysOf : List Entity → List Int
  | []      => []
  | e :: es => canonOf e :: keysOf es

@[grind] lemma keysOf_nil : keysOf [] = [] := rfl
@[grind] lemma keysOf_cons (e : Entity) (es : List Entity) :
    keysOf (e :: es) = canonOf e :: keysOf es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveKeys (entities : List Entity) return (out : List Int)
  ensures out = keysOf entities
  do
    -- impl-start
    let mut keys : List Int := []
    let mut i := entities.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entities.length
      invariant keys = keysOf (entities.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entities[i - 1]!
      keys := canonOf e :: keys
      i := i - 1
    return keys
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entity at
   `i-1` on the front, so `keysOf` peels one canonical key. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keysOf_drop_step (entities : List Entity) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entities.length) :
    keysOf (entities.drop (i - 1))
      = canonOf entities[i - 1]! :: keysOf (entities.drop i) := by
  have hlt : i - 1 < entities.length := by omega
  have hcons : entities.drop (i - 1) = entities[i - 1]! :: entities.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keysOf_cons]

prove_correct resolveKeys by
  loom_solve
  rw [keysOf_drop_step entities i (by omega) (by omega)]
  simp_all
