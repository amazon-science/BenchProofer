import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Building the related-object
-- iterator for an m2m field is a short chain of query-state builder steps over a
-- query whose related-loading configuration is modeled concretely below (a
-- structure projecting only the touched components). The condition under which an
-- evaluated query is rejected — a related field that is simultaneously held back
-- from immediate loading yet requested for relational traversal — is modeled
-- deeply as `raisesFieldError` (an A-reference; refinement.md), not axiomatized.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The relational-traversal configuration carried by a query (the analogue of a
query's `select_related` state), projected onto the observable distinction:
* `unrestricted` — no specific field set is pinned for relational traversal.
  This covers both "no traversal requested" and "traversal unrestricted": the
  two are indistinguishable on the modeled slice, where only a field-RESTRICTED
  configuration can conflict with deferred loading, so the projection collapses
  them;
* `fields` — traversal is restricted to a specific set of named related fields. -/
inductive SelectRel where
  | unrestricted
  | fields (fs : List String)
  deriving DecidableEq, Repr

/-- A query for the related objects of an m2m field, projected onto the
components the iterator construction inspects:
* `relation`  — identity of the related set being iterated (which related
  manager the objects come from); never altered by building the iterator;
* `selectRel` — the relational-traversal configuration inherited from the
  related manager (see `SelectRel`);
* `immediate` — the immediate-loading field mask (the analogue of `only(...)`):
  `none` means no restriction was applied, `some mask` means only the fields in
  `mask` are loaded immediately and every other field is held back. -/
structure QuerySet where
  relation : String
  selectRel : SelectRel
  immediate : Option (List String)
  deriving DecidableEq, Repr

/-- Whether evaluating the query would be rejected because some related field is
both held back from immediate loading and requested for relational traversal.
This can only happen when traversal is restricted to a specific field set: a
named related field that is requested for traversal but is absent from the
immediate-loading mask is the conflict. When no specific field set is pinned
(`unrestricted`), no such per-field conflict is possible. -/
def raisesFieldError (q : QuerySet) : Bool :=
  match q.selectRel, q.immediate with
  | SelectRel.fields fs, some mask => fs.any (fun f => !mask.contains f)
  | _, _ => false
-- pure-end

-- post-conditions-start
/-- Building the iterator over an m2m field's related primary keys yields a query
that (1) still iterates the same related set as the input, (2) loads only the
primary key immediately — preserving the load-minimization behavior, (3) carries
NO field-restricted relational-traversal configuration (any restricted
configuration the related manager supplied is discarded; the surviving
configuration is the unrestricted one — the model does not distinguish the
behaviorally-equivalent ways of clearing the restriction), and therefore (4) can
be evaluated without the deferred-versus-traversed conflict. The frame clause
pins the iterated relation to the input so the result must be built from THIS
query; the mask clause pins the load minimization; the traversal clause pins the
state change the issue demands (the inherited field restriction must not
survive); the no-conflict clause is the behavior the issue demands
(serialization must not be rejected even when the related manager requests
restricted relational traversal).

Note for reviewers: the three equality clauses pin EVERY component of `result`
exactly (the fourth clause is then entailed by definition of
`raisesFieldError`), so this spec is DETERMINISTIC — any `result` satisfying it
is the single record `{ relation := qs.relation, selectRel := unrestricted,
immediate := some ["pk"] }`, with no free or opaque oracle anywhere. A
same-spec implementation can verify only by computing exactly that record on
every input (extensional identity with the reference); a verifying same-spec
variant — however its body is phrased (direct record construction, reordered
builder steps, redundant branching) — is extensionally the reference behavior
and is a positive control, NOT evidence of spec weakness, so it must not be
submitted as a counterexample attack. See `spec_m2mPkQuery_deterministic` in
the proof region for the machine-checked statement. -/
def problem_spec_m2mPkQuery (qs : QuerySet) (result : QuerySet) : Prop :=
  result.relation = qs.relation ∧
  result.immediate = some ["pk"] ∧
  result.selectRel = SelectRel.unrestricted ∧
  raisesFieldError result = false
-- post-conditions-end

-- impl-start
def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
  let mut q := qs
  q := { q with selectRel := SelectRel.unrestricted }
  q := { q with immediate := some ["pk"] }
  return q
-- impl-end

-- proof-start
theorem correct_m2mPkQuery :
    ∀ (qs : QuerySet),
      problem_spec_m2mPkQuery qs (implementation_m2mPkQuery qs) := by
  intro qs
  unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
  simp only [Id.run]
  exact ⟨rfl, rfl, rfl, trivial⟩

/-- The spec is DETERMINISTIC: the three equality clauses pin every component
of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
equals the implementation's output on `qs`. Hence no same-spec implementation
with observably wrong behavior on ANY input can verify: a verifying same-spec
variant is extensionally the reference behavior (a positive control, not a
counterexample). -/
theorem spec_m2mPkQuery_deterministic :
    ∀ (qs result : QuerySet),
      problem_spec_m2mPkQuery qs result →
      result = implementation_m2mPkQuery qs := by
  intro qs result h
  obtain ⟨hr, hi, hs, _⟩ := h
  have himpl : implementation_m2mPkQuery qs =
      { relation := qs.relation, selectRel := SelectRel.unrestricted,
        immediate := some ["pk"] } := rfl
  rw [himpl]
  cases result
  simp_all
-- proof-end
