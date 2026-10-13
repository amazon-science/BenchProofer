import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is consumed as an axiom for this bundle. The behavior
   under specification is a pure decision over the model's declared metadata:
   whether the login identity field is guaranteed unique, decided from the
   field's own uniqueness flag together with the model's declared uniqueness
   constraints. The set of "total" (always-applicable) uniqueness constraints
   is modeled DEEPLY below (`totalUnique`) rather than borrowed from an oracle;
   its agreement with the real metadata accessor is validated executably by
   axiom_check.py (G-AX, an A-reference — mapping.md §3). Every observable is
   computed from the inputs; there is no consumed axiom. -/
-- axioms-end

-- pure-start
/- One declared constraint on a model, reduced to the three attributes that
   decide whether it guarantees a field is unique for every row:
   * `fields`      — the ordered field names the constraint ranges over;
   * `isUnique`    — whether it is a uniqueness constraint (vs. e.g. a check
                     constraint), which alone can guarantee distinct values;
   * `conditional` — whether it only applies to a subset of rows (a partial /
                     conditioned constraint), in which case it does NOT
                     guarantee uniqueness across all rows. -/
structure Constraint where
  fields : List String
  isUnique : Bool
  conditional : Bool
deriving DecidableEq, Inhabited, Repr

/- The verdict the identity-field uniqueness check produces:
   * `ok`      — the field is guaranteed unique, nothing reported;
   * `error`   — not guaranteed unique and only the default backend is in use
                 (uniqueness is mandatory there);
   * `warning` — not guaranteed unique but a custom backend may tolerate it. -/
inductive Verdict where
  | ok
  | error
  | warning
deriving DecidableEq, Inhabited, Repr

/- The field tuples of the constraints that guarantee uniqueness for ALL rows:
   exactly the uniqueness constraints that are unconditional. Front-recursive so
   each membership query reduces directly. This is the deep model of the
   model-metadata accessor for total (unconditional) uniqueness constraints;
   validated == the real accessor by axiom_check.py (A-reference). -/
def totalUnique : List Constraint → List (List String)
  | []      => []
  | c :: cs => if c.isUnique && !c.conditional then c.fields :: totalUnique cs
               else totalUnique cs

/- Whether some total uniqueness constraint ranges over EXACTLY the single
   identity field `uf` — i.e. that one field is, on its own, guaranteed unique
   for every row by a declared constraint. -/
def coversField (cs : List Constraint) (uf : String) : Bool :=
  (totalUnique cs).any (fun fs => fs == [uf])

@[grind] lemma totalUnique_nil : totalUnique [] = [] := rfl
@[grind] lemma totalUnique_cons (c : Constraint) (cs : List Constraint) :
    totalUnique (c :: cs)
      = (if c.isUnique && !c.conditional then c.fields :: totalUnique cs
         else totalUnique cs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide what to report about the uniqueness of a model's login identity field
   `usernameField`. The field is acceptable when either its own column is
   declared unique (`fieldUnique`) OR a declared constraint guarantees that the
   single field is unique for every row (`coversField`). Only when NEITHER holds
   is anything reported, and then the severity depends on whether only the
   default authentication backend is configured (`defaultBackendOnly`): the
   default backend requires uniqueness (an error), while a custom backend might
   tolerate non-unique identities (a warning).

   `fieldUnique`, `constraints`, `usernameField` and `defaultBackendOnly` are
   read-only inputs; the method computes and returns a verdict and mutates
   nothing it is given. -/
method usernameUniquenessVerdict
    (fieldUnique : Bool) (constraints : List Constraint)
    (usernameField : String) (defaultBackendOnly : Bool)
    return (out : Verdict)
  ensures out =
    (if !fieldUnique && !coversField constraints usernameField then
       (if defaultBackendOnly then Verdict.error else Verdict.warning)
     else Verdict.ok)
  do
    -- impl-start
    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
    let out : Verdict :=
      if !fieldUnique && !covered then
        (if defaultBackendOnly then Verdict.error else Verdict.warning)
      else Verdict.ok
    return out
    -- impl-end

prove_correct usernameUniquenessVerdict by
  loom_solve
  simp_all [coversField]
