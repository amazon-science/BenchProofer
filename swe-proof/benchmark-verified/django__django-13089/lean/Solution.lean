import Mathlib
-- imports-end

/-!
Trimming a size-bounded key/value store back under its capacity.

A persistent store keeps records, each identified by a distinct `key` string and
carrying an `expires` instant. A maintenance pass reduces the store when it has
grown past its configured capacity. The pass works in well-defined stages:

  * if the maintenance frequency is configured as zero, the whole store is
    emptied;
  * otherwise every already-expired record (one whose `expires` instant lies
    strictly before the reference instant `now`) is dropped first;
  * the surviving count is then compared against the capacity. If it is within
    capacity nothing further happens. If it exceeds capacity, a culling boundary
    is chosen and every record whose key sorts strictly below that boundary is
    dropped.

The culling boundary is located by ordering the surviving keys ascending and
taking the one at offset `survivors / frequency`. When that offset addresses an
actual key, that key is the boundary and the lower keys are dropped. When the
offset lies at or beyond the number of survivors, the ordering yields no such
key; in that situation the store is left exactly as it is.

The maintenance pass always completes and reports the resulting set of surviving
records (`some …`); it never aborts.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification as an opaque
-- contract. The capacity, frequency and reference instant enter as plain data;
-- each record's key and expiry enter as plain data. The only nontrivial step is
-- locating the culling boundary, which is the offset-indexed element of the
-- ascending ordering of the surviving keys — modeled directly (sort + index),
-- not axiomatized. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A store record: a distinct key string and an expiry instant. -/
structure Entry where
  key : String
  expires : Int
deriving DecidableEq, Repr, Inhabited

/-- The records that have not yet expired at reference instant `now`: those whose
expiry instant is at or after `now` (the strictly-earlier ones are dropped). -/
def keepUnexpired (now : Int) (entries : List Entry) : List Entry :=
  entries.filter (fun e => decide (now ≤ e.expires))

/-- The culling boundary: the key at position `offset` in the ascending ordering
of the keys of `xs`, or `none` when `offset` is at or beyond the number of
records (the ordering has no such position). -/
def cullBoundary (xs : List Entry) (offset : Nat) : Option String :=
  ((xs.map (·.key)).mergeSort (· ≤ ·))[offset]?

/-- The records kept when culling below `k`: those whose key does not sort
strictly below `k` (the strictly-lower keys are dropped). -/
def keepAboveKey (k : String) (xs : List Entry) : List Entry :=
  xs.filter (fun e => !decide (e.key < k))
-- pure-end

-- post-conditions-start
/-- The maintenance pass result is pinned for every configuration:

  * zero frequency empties the store (`some []`);
  * otherwise, against `remaining` (the survivors after dropping expired
    records): when the survivor count is within capacity the store is exactly
    `remaining`; when it exceeds capacity the store is `remaining` with its
    lowest keys culled below the chosen boundary, or exactly `remaining` when the
    boundary offset addresses no key.

The result is always `some …`: the pass completes for every input. No output
component is left free. -/
def problem_spec_cull
    (frequency : Nat) (capacity now : Int) (entries : List Entry)
    (result : Option (List Entry)) : Prop :=
  let remaining := keepUnexpired now entries
  (frequency = 0 → result = some []) ∧
  (frequency ≠ 0 →
    ((remaining.length : Int) ≤ capacity → result = some remaining) ∧
    ((remaining.length : Int) > capacity →
      result = some (match cullBoundary remaining (remaining.length / frequency) with
                     | some k => keepAboveKey k remaining
                     | none   => remaining)))
-- post-conditions-end

-- impl-start
def implementation_cull
    (frequency : Nat) (capacity now : Int) (entries : List Entry) :
    Option (List Entry) := Id.run do
  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
-- impl-end

-- proof-start
theorem correct_cull :
    ∀ (frequency : Nat) (capacity now : Int) (entries : List Entry),
      problem_spec_cull frequency capacity now entries
        (implementation_cull frequency capacity now entries) := by
  intro frequency capacity now entries
  unfold problem_spec_cull implementation_cull
  simp only [Id.run]
  refine ⟨fun h0 => by simp only [h0, if_true]; rfl, ?_⟩
  intro hne
  simp only [hne, if_false]
  refine ⟨?_, ?_⟩
  · intro hle
    have hgt : ¬ (↑(keepUnexpired now entries).length > capacity) := by
      simp only [not_lt]; exact hle
    simp only [hgt, if_false]
    rfl
  · intro hgt
    simp only [hgt, if_true]
    cases h : cullBoundary (keepUnexpired now entries)
        ((keepUnexpired now entries).length / frequency) with
    | none => rfl
    | some k => rfl
-- proof-end
