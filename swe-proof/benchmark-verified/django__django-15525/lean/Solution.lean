import Mathlib
-- imports-end

-- axioms-start
/-- A data-store alias (e.g. the store an operation targets). -/
abbrev Store := String

/-- Opaque carrier for the descriptive field data of a record (everything other
than its identifier). It is the data a record's identifying key is derived
from. -/
abbrev Payload := List String

/-- An identifying tuple-key for a record. -/
abbrev Key := List String

/-- A freshly assembled, not-yet-stored record: its descriptive `payload`,
together with the store alias against which any of its related-record lookups
are resolved. -/
structure Record where
  payload : Payload
  store   : Store
deriving Repr

/-- The data of a record being processed: an optional already-known identifier
plus the descriptive `payload`. -/
structure Data where
  id      : Option Int
  payload : Payload
deriving Repr, DecidableEq

/-- How assembling a record can fail. -/
inductive Failure where
  /-- A key derivation did not hand back a key. Either the model offers no such
  step at all — not every model has an identifying key to derive, and on one that
  does not there is nothing to run — or the step could not resolve on the record
  it was handed: deriving a key follows that record's references to other records
  against the store alias the record carries, and they need not resolve there.
  Both are the same observation, so both are this one value: no key came back. -/
  | keyDerivationUnavailable : Failure
deriving Repr, DecidableEq

/-- Look up an existing record by its identifying key in the given store and
return its stored identifier, or `none` when no such record exists there.
(Unchanged callee — opaque signature only.) -/
opaque lookupByKey : Store → Key → Option Int

/-- Coerce a looked-up raw identifier into the field's identifier type.
(Unchanged callee — opaque signature only.) -/
opaque coerceId : Int → Int
-- axioms-end

-- pure-start
/-- The alias used by default for a record whose target store has not been
established. -/
def defaultStore : Store := "default"

/-- The key-derivation step the model being processed offers, as this operation
receives it: handed an assembled record, it yields that record's identifying
key. It is a PARTIAL step — see `derivationAvailability` — and it reads the
record it is handed, so both WHETHER it yields a key and WHICH key it yields
depend on the `store` alias carried by that record as well as on the descriptive
payload (the key may follow references to other records, and those references
are resolved against that alias — so under another alias they may not resolve at
all). (Unchanged callee — signature only.)

Because this carrier is pure and total, an application of the step whose value is
DISCARDED (`let _ := derive r`) is erased: it denotes nothing, and an
implementation carrying one is the very same function — up to `rfl` — as the
implementation without it. Running the step is modelled ONLY by BINDING it
(`←`), which is also the only way "no key came back" is observable at all. So a
candidate whose intended transcription runs the step at a point where a failure
to yield a key would escape must BIND it at that point; a candidate that
evaluates it and drops the value has modelled a program that never ran it. -/
abbrev KeyDerivation := Record → Except Failure Key

/-- What the operation may assume about the derivation step it is handed.

The step is available exactly on a model that supports identifying keys
(`hasKey`) — and, where it is, only ON THE RECORD ASSEMBLED FOR THE TARGET
STORE, i.e. the record whose references to other records resolve in the very
store the key is being derived for. Nothing at all is assumed about the step on
any OTHER record: run on a record still carrying some other store alias, a
derivation that follows a reference to a record living in `store` has nothing to
find there and yields no key. On a model that supports no identifying keys there
is no step to run in the first place, so it yields no key on ANY record.

So the derivation step is defined only under `hasKey` AND only on the record
assembled for `store`; both are definedness conditions for running it, not
merely conditions on whether running it is useful. -/
def derivationAvailability
    (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) : Prop :=
  (hasKey = true →
      ∃ key : Key, derive { payload := data.payload, store := store } = Except.ok key) ∧
  (hasKey = false → ∀ r : Record,
      derive r = Except.error Failure.keyDerivationUnavailable)
-- pure-end

-- post-conditions-start
/-- Specification of assembling a record for processing.

* (C0) Assembling a record always yields a record: it never comes back with no
  key derived. Since the derivation step is only defined where the model
  supports identifying keys and only on the record assembled for the target
  store, this pins both WHERE that step may be run and WHAT it may be run on —
  an implementation that runs it anywhere else has no key to show and cannot
  produce a record at all.
* (C1) The descriptive payload is never altered (frame).
* (C2) When the record has no identifier yet and the model supports identifying
  keys, the identifier is resolved from the key the derivation step yields for
  the record **assembled on the target store `store`**, looked up in that same
  store; if found, the result's id is the coerced stored id, otherwise the id is
  left as it was.
* (C3) In every other case the identifier is left unchanged (frame). -/
def problem_spec_resolveRecord
    (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation)
    (result : Except Failure Data) : Prop :=
  (∃ res : Data, result = Except.ok res) ∧
  ( ∀ res : Data, result = Except.ok res →
      res.payload = data.payload ∧
      ( (data.id = none ∧ hasKey = true) →
          ∀ key : Key,
            derive { payload := data.payload, store := store } = Except.ok key →
            res.id =
              (match lookupByKey store key with
               | some raw => some (coerceId raw)
               | none     => data.id) ) ∧
      ( ¬ (data.id = none ∧ hasKey = true) → res.id = data.id ) )
-- post-conditions-end

-- impl-start
def implementation_resolveRecord
    (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
    Except Failure Data := do
  if data.id = none ∧ hasKey = true then
    -- assemble the record; establish its target store before deriving the key
    let mut obj : Record := { payload := data.payload, store := defaultStore }
    obj := { obj with store := store }
    let key ← derive obj
    match lookupByKey store key with
    | some raw => return { data with id := some (coerceId raw) }
    | none     => return data
  return data
-- impl-end

-- proof-start
theorem correct_resolveRecord :
    ∀ (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation),
      derivationAvailability data store hasKey derive →
      problem_spec_resolveRecord data store hasKey derive
        (implementation_resolveRecord data store hasKey derive) := by
  intro data store hasKey derive havail
  unfold problem_spec_resolveRecord implementation_resolveRecord
  by_cases h : (data.id = none ∧ hasKey = true)
  · rw [if_pos h]
    obtain ⟨key, hk⟩ := havail.1 h.2
    simp only [hk, bind, Except.bind]
    cases hl : lookupByKey store key with
    | none =>
      refine ⟨⟨data, rfl⟩, ?_⟩
      intro res hres
      simp only [pure, Except.pure, Except.ok.injEq] at hres
      subst hres
      refine ⟨rfl, ?_, ?_⟩
      · intro _ key₁ hkey
        simp only [Except.ok.injEq] at hkey
        subst hkey
        rw [hl]
      · intro hc; exact absurd h hc
    | some raw =>
      refine ⟨⟨{ id := some (coerceId raw), payload := data.payload }, rfl⟩, ?_⟩
      intro res hres
      simp only [pure, Except.pure, Except.ok.injEq] at hres
      subst hres
      refine ⟨rfl, ?_, ?_⟩
      · intro _ key₁ hkey
        simp only [Except.ok.injEq] at hkey
        subst hkey
        rw [hl]
      · intro hc; exact absurd h hc
  · rw [if_neg h]
    simp only [bind, Except.bind, pure, Except.pure, Except.ok.injEq]
    refine ⟨⟨data, rfl⟩, ?_⟩
    intro res hres
    subst hres
    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
-- proof-end
