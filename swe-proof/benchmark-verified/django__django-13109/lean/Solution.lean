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
      let mut qs := rows
      qs := qs.filter (fun r => r.key == v)
      qs := qs.filter (fun r => r.limitOk)
      return !qs.isEmpty
-- impl-end

-- proof-start
theorem correct_validateReference :
    ∀ (parentLink : Bool) (value : Option Nat) (rows : List Row),
      problem_spec_validateReference parentLink value rows
        (implementation_validateReference parentLink value rows) := by
  have helper : ∀ (l : List Row) (p : Row → Bool),
      (!(l.filter p).isEmpty) = l.any p := by
    intro l p
    induction l with
    | nil => rfl
    | cons a as ih =>
      simp only [List.filter_cons, List.any_cons]
      by_cases h : p a = true
      · simp [h]
      · simp only [Bool.not_eq_true] at h
        simp [h, ih]
  intro parentLink value rows
  unfold problem_spec_validateReference implementation_validateReference existsValid
  simp only [Id.run, bind, pure]
  cases parentLink <;> simp only [Bool.false_eq_true, if_false, if_true]
  cases value with
  | none => rfl
  | some v =>
    show (!(List.filter (fun r => r.limitOk) (List.filter (fun r => r.key == v) rows)).isEmpty)
        = rows.any (fun r => r.key == v && r.limitOk)
    rw [List.filter_filter, helper]
    have hp : (fun r : Row => r.limitOk && r.key == v)
        = (fun r : Row => r.key == v && r.limitOk) := by
      funext r; rw [Bool.and_comm]
    rw [hp]
-- proof-end
