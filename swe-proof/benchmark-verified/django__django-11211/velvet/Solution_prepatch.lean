import Velvet.Std
-- imports-end

/- Total correctness: the real preparation step is a straight-line composition
   of two always-terminating calls (the base preliminary coercion, then the
   normal-form conversion), so a diverging implementation must NOT satisfy
   this spec. Partial correctness would let a non-terminating branch discharge
   its postconditions vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The domain of values a model field may be asked to prepare for use as a
   lookup key. A value arrives in one of several interchangeable shapes that all
   denote the same logical datum: absent, an already-concrete object, a textual
   transcription, or an integer transcription. Modeled as an opaque carrier so
   no claim is made about the field's internal parsing; the bijection to the
   repository value space is in mapping.md (G-AX uses it). -/
inductive Val where
  | absent
  | concrete (canon : List Char)
  | textual  (s : List Char)
  | numeric  (n : Nat)

/- A value is well-formed when it is an accepted representation — the normal-form
   conversion is defined on it (it does not reject it). The F2P input domain (a
   freshly generated identifier and its textual transcription) is well-formed.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom WellFormed : Val → Prop

/- The base field's preliminary value coercion: it performs only generic,
   representation-preserving housekeeping and so returns any already-concrete
   value unchanged. Unchanged callee; weakest sufficient contract = identity on
   this domain (directive 7). G-AX checks it against the real base callee. -/
axiom preCoerce : Val → Val
axiom preCoerce_id : ∀ v : Val, preCoerce v = v

/- The field's normal-form conversion: maps any accepted representation of a
   value to the single canonical representation that datum is stored and compared
   as. Its sole load-bearing property here is that the canonical representation
   is stable — converting an already-canonical value changes nothing — so
   the prepared key is idempotent under further conversion. Unchanged callee;
   pinned only at this weakest sufficient strength (directive 7). G-AX checks it
   against the real conversion over the representation corpus. -/
axiom canonicalize : Val → Val
axiom canonicalize_idem :
    ∀ v : Val, WellFormed v → canonicalize (canonicalize v) = canonicalize v
-- axioms-end

-- pure-start
/- The non-deterministic choices below are well-posed: for any target value `v`
   the set of values equal to `v` is non-empty (`v` itself). This supplies the
   constructive existence witness so each `:|` choice elaborates. It does NOT
   weaken verification: under demonic choice the postcondition must still hold
   for every value the predicate allows — here exactly the named callee result. -/
noncomputable instance findableEqVal (v : Val) (n : Lean.Name) :
    Findable (fun e : Val => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare a field value for use as a relational lookup key.

   The desired behavior: the value is first put through the base field's
   preliminary coercion and then converted to the field's canonical
   representation, so that distinct accepted transcriptions of the same datum
   (for instance a textual transcription and the already-concrete object) yield
   the SAME prepared key. The result is exactly that canonical representation
   (`out = canonicalize value`), and it is itself canonical — a further
   conversion leaves it unchanged (`canonicalize out = out`) — which is what lets
   a key derived from one transcription match a stored value derived from
   another.

   `value` is the read-only input (not `mut`): preparation consumes it and never
   alters it (directive 5). It is required well-formed — an accepted
   representation the conversion does not reject (mapping.md §2). -/
noncomputable section
method preparedValue (value : Val) return (out : Val)
  require WellFormed value
  ensures out = canonicalize value
  ensures canonicalize out = out
  do
    -- impl-start
    -- Pre-image skeleton: the field defines no normal-form step of its own, so
    -- preparation is only the base preliminary coercion — the value is returned
    -- in whatever representation it arrived in, NOT converted to canonical form.
    -- The frozen spec requires the canonical representation, so prove_correct
    -- MUST fail.
    let prepped :| prepped = preCoerce value
    return prepped
    -- impl-end
end

prove_correct preparedValue by
  loom_solve <;> simp_all [preCoerce_id, canonicalize_idem]
