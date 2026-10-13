import Mathlib
-- imports-end

/-!
Validating a reference from one record to another stored record.

A record may hold a reference (a "foreign key") to a target record of another
kind, identified by a key value. Validation must confirm that the reference is
sound: that some stored target record actually carries that key value (and meets
any standing choice constraint attached to the reference).

The target kind exposes two views of its stored records:

  * a DEFAULT presentation view, which a target kind may narrow with a standing
    filter so that some genuinely-stored records are not presented (for example,
    records flagged as retired); and
  * the UNDERLYING stored collection, which contains every stored record
    irrespective of any such presentation filter.

The desired behavior is that a reference is sound exactly when the UNDERLYING
stored collection contains a record with the referenced key value that also
satisfies the choice constraint — i.e. soundness depends only on whether the
target record genuinely exists and is eligible, never on whether the target
kind's default presentation happens to hide it. Two references need no existence
check at all: a reference that merely links a record to its parent record, and a
reference whose value is absent (null); both are sound outright.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled here — selecting the underlying stored collection rather than the
-- narrowed default presentation, and checking key-and-eligibility membership
-- over it — is modeled structurally over the per-record observables the stored
-- collection already exposes, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A stored target record, paired with the observables the existence check
consults.
* `key` — the record's value for the referenced field (the reference matches a
  record iff this equals the referenced value);
* `defaultVisible` — whether the record survives the target kind's default
  presentation filter (`false` ⇒ genuinely stored but hidden from the default
  presentation view);
* `limitOk` — whether the record satisfies the standing choice constraint
  attached to the reference. -/
structure Row where
  key : Nat
  defaultVisible : Bool
  limitOk : Bool

/-- A reference value `v` is matched by some eligible record in the given
collection: a record whose `key` equals `v` and which satisfies the choice
constraint. -/
def existsValid (v : Nat) (rows : List Row) : Bool :=
  rows.any (fun r => r.key == v && r.limitOk)
-- pure-end

-- post-conditions-start
/-- The soundness verdict is fully pinned by the inputs. A parent-link reference,
or an absent (null) value, is sound outright. Otherwise the reference is sound
exactly when the UNDERLYING stored collection (`rows` in full, independent of
each record's `defaultVisible` presentation flag) contains an eligible record
matching the referenced value. The entire result is determined; no component is
left free. -/
def problem_spec_validateReference
    (parentLink : Bool) (value : Option Nat) (rows : List Row)
    (result : Bool) : Prop :=
  result =
    (if parentLink then true
     else match value with
          | none => true
          | some v => existsValid v rows)
-- post-conditions-end

-- impl-start
def implementation_validateReference
    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=
  Id.run do
    if parentLink then
      return true
    match value with
    | none => return true
    | some v =>
      -- Existence check over the DEFAULT presentation view: records hidden by
      -- the target kind's default presentation filter are dropped before the
      -- key/eligibility match, so a genuinely-stored-but-hidden record is not
      -- seen.
      let mut qs := rows.filter (fun r => r.defaultVisible)
      qs := qs.filter (fun r => r.key == v)
      qs := qs.filter (fun r => r.limitOk)
      return !qs.isEmpty
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: on a collection whose only record matching the referenced
-- value is hidden from the default presentation view (`defaultVisible = false`)
-- but is genuinely stored and eligible, this impl drops it and reports the
-- reference unsound, whereas the spec — which scans the underlying stored
-- collection — reports it sound.
theorem correct_validateReference :
    ∀ (parentLink : Bool) (value : Option Nat) (rows : List Row),
      problem_spec_validateReference parentLink value rows
        (implementation_validateReference parentLink value rows) := by
  sorry
-- proof-end
