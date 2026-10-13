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
    if !resolvesToReference attr.kind then
      wrapped := true
    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
  return whenStatements
-- impl-end

-- proof-start
/-- Loop body lemma (Route B): the cleaned `forIn` over `objs`, generalized over
the accumulator `init`, accumulates one branch per record (in order), wrapping a
literal exactly when the value does not resolve to a reference. -/
private theorem bulkUpdateBranches_forIn
    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
    (Id.run (forIn objs init fun obj r =>
      if (!resolvesToReference obj.2.kind) = true then
        pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
      else
        pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))))
    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  induction objs generalizing init with
  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (!resolvesToReference a.2.kind) = true
    · rw [if_pos h]
      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]
    · rw [if_neg h]
      simp only [Bool.not_eq_true] at h
      simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append, h]

/-- The implementation equals the obvious `List.map`: bridge the desugared loop
body (`do pure PUnit.unit; …; pure (ForInStep.yield …)`) to the cleaned body of
`bulkUpdateBranches_forIn` (definitionally equal), then apply the lemma. -/
private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
    implementation_bulkUpdateBranches objs
      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  unfold implementation_bulkUpdateBranches
  have h2 : (Id.run do
      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
            if (!resolvesToReference obj.2.kind) = true then do
              pure PUnit.unit
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
            else do
              pure PUnit.unit
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)]))
      pure r)
      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
          if (!resolvesToReference obj.2.kind) = true then
            pure (ForInStep.yield (r ++ [(⟨obj.1, true, obj.2.ident⟩ : CaseBranch)]))
          else
            pure (ForInStep.yield (r ++ [(⟨obj.1, false, obj.2.ident⟩ : CaseBranch)])))) := rfl
  rw [h2, bulkUpdateBranches_forIn]
  simp

theorem correct_bulkUpdateBranches :
    ∀ (objs : List (Nat × AttrValue)),
      problem_spec_bulkUpdateBranches objs
        (implementation_bulkUpdateBranches objs) := by
  intro objs
  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
  refine ⟨by simp, ?_⟩
  intro i pk attr hi
  rw [List.getElem?_map, hi]
  rfl
-- proof-end
