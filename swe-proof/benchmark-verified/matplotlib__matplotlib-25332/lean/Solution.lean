import Mathlib
-- imports-end

/-!
Serializing a reference-backed grouping container so it round-trips.

A grouping container records a partition of objects into disjoint sets. To allow
the grouped objects to be garbage-collected, the container does not hold the
objects directly; it holds *references* to them. The partition is stored as a
table mapping each member's reference to the list of references that make up its
group.

References of this kind are an in-memory bookkeeping device: they cannot be
turned into a self-contained, transferable value, so a naive attempt to
serialize a container that holds them does not produce a value at all — it fails.

The desired behavior, modeled here, is twofold:

  * `serialize` — producing the transferable form of the container. It must
    SUCCEED (rather than fail), and the value it produces must record, for every
    entry of the table, the referent of the key together with the referents of
    each member of its group — i.e. the partition with every reference replaced
    by the object it points at.

  * `deserialize` — reconstructing the container from a transferable form. It
    rebuilds the table by replacing every recorded referent (key and members
    alike) with a fresh reference to it, so the original partition is restored.

Taken together these pin the round-trip: serializing then deserializing yields
the same partition the container started with.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. A reference and
-- the act of following it / creating it are modeled directly as the `Ref`
-- structure below (its identity token `val`, `Ref.mk`), not as an axiomatized
-- repo callee. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A reference to a grouped object, modeled by the object's identity token.
Following the reference is `Ref.val`; creating one is `Ref.mk`. Two references
are equal exactly when they point at the same object. -/
structure Ref where
  val : Int
deriving DecidableEq, Repr

/-- The transferable form of the partition table: for each entry, the referent
of the key paired with the referents of its group's members. (Every reference is
replaced by the object it points at.) -/
def toStrong (m : List (Ref × List Ref)) : List (Int × List Int) :=
  m.map (fun kv => (kv.1.val, kv.2.map (fun r => r.val)))

/-- Reconstructing the partition table from its transferable form: every recorded
referent (key and members alike) is wrapped in a fresh reference to it. -/
def toWeak (s : List (Int × List Int)) : List (Ref × List Ref) :=
  s.map (fun kv => (Ref.mk kv.1, kv.2.map (fun n => Ref.mk n)))
-- pure-end

-- post-conditions-start
/-- Serialization succeeds and produces exactly the transferable form of the
partition table: an `ok` value whose content records, for every entry, the
referent of the key together with the referents of each member of its group.
The whole result is pinned to the input table, so no component is left free. -/
def problem_spec_serialize (m : List (Ref × List Ref))
    (result : Except String (List (Int × List Int))) : Prop :=
  result = Except.ok (toStrong m)
-- post-conditions-end

-- impl-start
def implementation_serialize (m : List (Ref × List Ref)) :
    Except String (List (Int × List Int)) := Id.run do
  let mut acc : List (Int × List Int) := []
  for kv in m do
    let key := kv.1
    let members := kv.2
    let mut derefMembers : List Int := []
    for v in members do
      derefMembers := derefMembers ++ [v.val]
    acc := acc ++ [(key.val, derefMembers)]
  return Except.ok acc
-- impl-end

-- proof-start
/-- `forIn` over a list, where the body yields the accumulator with `f x`
appended, computes `init ++ xs.map f`. The workhorse for both round-trip loops
(inner and outer), generalized over the accumulator. -/
theorem forIn_app_pure {α β : Type} (xs : List α) (init : List β) (f : α → β) :
    (forIn xs init (fun x r => pure (ForInStep.yield (r ++ [f x]))) : Id (List β))
    = pure (init ++ xs.map f) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, ih]
    simp [List.append_assoc]

theorem correct_serialize :
    ∀ (m : List (Ref × List Ref)),
      problem_spec_serialize m (implementation_serialize m) := by
  intro m
  unfold problem_spec_serialize implementation_serialize toStrong
  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
  rfl
-- proof-end

-- post-conditions-start
/-- Deserialization reconstructs the partition table from its transferable form:
every recorded referent (key and members alike) is wrapped in a fresh reference
to it. The whole result is pinned to the input, so no component is left free. -/
def problem_spec_deserialize (s : List (Int × List Int))
    (result : List (Ref × List Ref)) : Prop :=
  result = toWeak s
-- post-conditions-end

-- impl-start
def implementation_deserialize (s : List (Int × List Int)) :
    List (Ref × List Ref) := Id.run do
  let mut acc : List (Ref × List Ref) := []
  for kv in s do
    let members := kv.2
    let mut wrapMembers : List Ref := []
    for v in members do
      wrapMembers := wrapMembers ++ [Ref.mk v]
    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]
  return acc
-- impl-end

-- proof-start
theorem correct_deserialize :
    ∀ (s : List (Int × List Int)),
      problem_spec_deserialize s (implementation_deserialize s) := by
  intro s
  unfold problem_spec_deserialize implementation_deserialize toWeak
  simp only [Id.run, bind, forIn_app_pure, List.nil_append]
  rfl
-- proof-end
