import Mathlib
-- imports-end

/-!
Deciding how each per-row value is carried into a batched conditional update.

When a batch of records is written in a single conditional update, the update is
assembled one branch per record: for each record the new value of the target
field is read and placed into a `WHEN <this record> THEN <value>` branch, keyed
by the record's identity.

A field value can be one of two behavioral kinds:

  * a plain stored value (a string, a number, …) — it must be carried as a
    literal, i.e. wrapped so the backend stores it verbatim;
  * a value that resolves to a database reference — for example a value that
    names another column to read from, or a value that is itself a computed
    query node. Such a value must be carried through unwrapped, so the backend
    resolves it (e.g. to the named column) rather than storing its textual form.

The desired behavior: a value is wrapped as a literal exactly when it does NOT
resolve to a database reference; any value that resolves to a reference — whether
it is a full computed query node or merely names another column — is passed
through unchanged. Each produced branch keeps the record's identity unchanged and
carries the same underlying value it was given.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The wrapping
-- decision is modeled DEEPLY over the value's behavioral kind, and the literal
-- wrapping is modeled as a flag on the produced branch (the underlying value is
-- preserved either way), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The behavioral kind of a per-record field value, as it bears on how the value
must be carried into the update:
* `plainValue` — an ordinary stored value (string/number/…); does NOT resolve to a
  database reference, so it must be wrapped as a literal;
* `directExpression` — a value that is itself a computed query node; resolves to a
  database reference, carried through unwrapped;
* `fieldReference` — a value that names another column to resolve against;
  resolves to a database reference, carried through unwrapped. -/
inductive ValueKind
  | plainValue
  | directExpression
  | fieldReference
deriving DecidableEq, Repr

/-- A per-record field value, restricted to the observed aspects: an opaque
identity of the underlying value (only equality / pass-through is observed) and
its behavioral kind. -/
structure AttrValue where
  ident : Nat
  kind : ValueKind
deriving DecidableEq, Repr

/-- Whether a value resolves to a database reference: true for everything except a
plain stored value. A value that resolves to a reference is carried through
unwrapped; only a plain stored value is wrapped as a literal. -/
def resolvesToReference (k : ValueKind) : Bool :=
  k != ValueKind.plainValue

/-- One produced conditional branch:
* `pk` — the record identity the branch is keyed on (carried through unchanged);
* `wrapped` — whether the carried value was wrapped as a literal;
* `valueIdent` — the identity of the underlying value (preserved whether or not it
  was wrapped). -/
structure CaseBranch where
  pk : Nat
  wrapped : Bool
  valueIdent : Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The produced branch list is fully pinned to the input batch:

  * it has exactly one branch per record, in record order;
  * each branch keeps its record's identity (`pk`) unchanged;
  * each branch carries the same underlying value identity it was given; and
  * a branch's value is wrapped as a literal exactly when the value does NOT
    resolve to a database reference (i.e. only for a plain stored value); every
    value that resolves to a reference is carried through unwrapped.

Both the wrapped flag and the carried identity are determined for every record,
so no output component is left free. -/
def problem_spec_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) (result : List CaseBranch) : Prop :=
  result.length = objs.length ∧
  ∀ (i : Nat) (pk : Nat) (attr : AttrValue), objs[i]? = some (pk, attr) →
    result[i]? = some (⟨pk, !resolvesToReference attr.kind, attr.ident⟩ : CaseBranch)
-- post-conditions-end

-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
  let mut whenStatements : List CaseBranch := []
  for obj in objs do
    let pk := obj.1
    let attr := obj.2
    let mut wrapped := false
    -- BUGGY (pre-patch): only a direct computed query node is treated as
    -- resolvable; a value that merely names another column is wrongly wrapped.
    if attr.kind != ValueKind.directExpression then
      wrapped := true
    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
  return whenStatements
-- impl-end

-- proof-start
theorem correct_bulkUpdateBranches :
    ∀ (objs : List (Nat × AttrValue)),
      problem_spec_bulkUpdateBranches objs
        (implementation_bulkUpdateBranches objs) := by
  intro objs
  unfold problem_spec_bulkUpdateBranches implementation_bulkUpdateBranches
  have key : ∀ (os : List (Nat × AttrValue)) (acc : List CaseBranch),
      (Id.run (forIn os acc (fun obj r =>
        (if (!resolvesToReference obj.2.kind) = true then
            ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)])
          else ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]) : Id (ForInStep (List CaseBranch))))))
      = acc ++ os.map (fun obj => (⟨obj.1, !resolvesToReference obj.2.kind, obj.2.ident⟩ : CaseBranch)) := by
    intro os
    induction os with
    | nil => intro acc; rw [List.map_nil, List.append_nil]; rfl
    | cons hd tl ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : (!resolvesToReference hd.2.kind) = true
      · simp only [h, if_true, ih]
        simp only [Bool.not_eq_true'] at h
        simp [h, List.append_assoc]
      · have hf : (!resolvesToReference hd.2.kind) = false := by simpa using h
        simp only [hf, Bool.false_eq_true, if_false, ih]
        simp only [Bool.not_eq_false] at hf
        simp [hf, List.append_assoc]
  have hbridge : (Id.run do
      let mut whenStatements : List CaseBranch := []
      for obj in objs do
        let pk := obj.1
        let attr := obj.2
        let mut wrapped := false
        if !resolvesToReference attr.kind then
          wrapped := true
        whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
      return whenStatements)
      = Id.run (forIn objs [] (fun obj r =>
        (if (!resolvesToReference obj.2.kind) = true then
            ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)])
          else ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]) : Id (ForInStep (List CaseBranch))))) := rfl
  rw [hbridge, key]
  simp only [List.nil_append]
  refine ⟨by simp, ?_⟩
  intro i pk attr h
  rw [List.getElem?_map, h]
  rfl
-- proof-end
