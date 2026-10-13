import Mathlib
-- imports-end

/-!
Choosing the model key under which each traversed relation's identifier columns
are recorded when planning which columns a query must load.

When a query restricts the fields it loads to a subset reached through related
models, it walks the chain of relations one step at a time. At each step it
reaches a target model and must record, keyed by that model, that the model's
identifier column has to be loaded (otherwise the rows for that model cannot be
assembled).

A model can be either a base model — one that owns its own storage and identifier
column — or an alias model that shares the storage and identifier column of an
underlying base model while remaining a distinct model object. Two alias models of
the same base, and an alias and its base, all share one storage and one identifier
column.

The desired behavior: at every relation step the identifier requirement is keyed
under the *base* model that owns the shared storage — never under an alias.
Keying under an alias would record the requirement against a model object that
does not, by itself, own the identifier column, leaving the load plan unable to
locate that column for the shared storage. For a model that is already a base
model, its base is itself, so keying is unchanged. The recorded keys are produced
one per step, in traversal order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The choice of
-- which model to key each step under is modeled DEEPLY over each step's resolved
-- model (its own identity together with the identity of the base model whose
-- storage it shares), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One resolved relation-step target model, restricted to the observed aspects:
* `ident` — the identity of the model object reached by this step (which may be an
  alias model sharing another model's storage);
* `baseIdent` — the identity of the base model that owns the shared storage and
  identifier column. For a base model (one that owns its own storage) `baseIdent`
  equals `ident`; for an alias model it is the underlying base's identity. -/
structure RelModel where
  ident : Nat
  baseIdent : Nat
deriving DecidableEq, Repr

/-- The base model that owns the storage shared by this step's model: the model
under which the step's identifier requirement must be keyed. Idempotent on base
models (where `baseIdent = ident`). -/
def baseOf (m : RelModel) : Nat :=
  m.baseIdent
-- pure-end

-- post-conditions-start
/-- The produced key list is fully pinned to the traversed steps:

  * it has exactly one key per relation step, in traversal order; and
  * each key is the identity of the base model that owns the step's shared storage
    (`baseIdent`) — never the (possibly alias) resolved model itself.

Every produced key is determined for every step, so no output component is left
free. -/
def problem_spec_relationModelKeys
    (steps : List RelModel) (result : List Nat) : Prop :=
  result.length = steps.length ∧
  ∀ (i : Nat) (m : RelModel), steps[i]? = some m →
    result[i]? = some (baseOf m)
-- post-conditions-end

-- impl-start
def implementation_relationModelKeys
    (steps : List RelModel) : List Nat := Id.run do
  let mut keys : List Nat := []
  for m in steps do
    -- BUGGY (pre-patch): the step's identifier requirement is keyed under the
    -- resolved model AS-IS, not the base model whose storage it shares; for an
    -- alias model this records the key against a model that does not own the
    -- shared identifier column.
    let curModel := m.ident
    keys := keys ++ [curModel]
  return keys
-- impl-end

-- proof-start
theorem correct_relationModelKeys :
    ∀ (steps : List RelModel),
      problem_spec_relationModelKeys steps
        (implementation_relationModelKeys steps) := by
  intro steps
  unfold problem_spec_relationModelKeys implementation_relationModelKeys
  have key : ∀ (ss : List RelModel) (acc : List Nat),
      (Id.run (forIn ss acc (fun m r =>
        (ForInStep.yield (r ++ [baseOf m]) : Id (ForInStep (List Nat))))))
      = acc ++ ss.map baseOf := by
    intro ss
    induction ss with
    | nil => intro acc; simp
    | cons hd tl ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp [List.append_assoc]
  have hbridge : (Id.run do
      let mut keys : List Nat := []
      for m in steps do
        let curModel := baseOf m
        keys := keys ++ [curModel]
      return keys)
      = Id.run (forIn steps [] (fun m r =>
        (ForInStep.yield (r ++ [baseOf m]) : Id (ForInStep (List Nat))))) := rfl
  rw [hbridge, key]
  simp only [List.nil_append]
  refine ⟨by simp, ?_⟩
  intro i m h
  rw [List.getElem?_map, h]
  rfl
-- proof-end
