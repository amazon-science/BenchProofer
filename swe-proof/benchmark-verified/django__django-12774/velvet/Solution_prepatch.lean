import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged sub-observations the decision consults are modeled as FREE inputs
   (see the method signature): whether the requested key is *individually*
   declared as a unique key (`fieldUnique : Bool`), and the collection of
   uniqueness guarantees in force (`constraints`). The decision's postcondition
   holds for EVERY value of both, so neither is owed a contract — each is
   strictly weaker than any concrete callee (directive 7). The behaviour this
   bundle pins — which requested keys are admissible — is modeled DEEPLY in the
   `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The single outcome the decision distinguishes from acceptance: the requested
   key is rejected as not being a guaranteed-unique key. Acceptance carries
   nothing (`Except.ok ()`). -/
inductive ValidationErr where
  | fieldNotUnique
  deriving DecidableEq

/- The keys covered by ONE uniqueness guarantee. A guarantee that spans exactly
   one column contributes that sole column's name; a guarantee spanning several
   columns (or none) contributes nothing — a multi-column guarantee does not by
   itself make any single one of its columns a unique key. -/
def soleColumn (guarantee : List String) : List String :=
  if guarantee.length = 1 then [guarantee[0]!] else []

/- The keys covered by SOME single-column uniqueness guarantee: the
   per-guarantee expansion of the list of guarantees, concatenated. Written
   front-recursively so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def singleColumnKeys : List (List String) → List String
  | []      => []
  | g :: gs => soleColumn g ++ singleColumnKeys gs

@[grind] lemma singleColumnKeys_nil : singleColumnKeys [] = [] := rfl
@[grind] lemma singleColumnKeys_cons (g : List String) (gs : List (List String)) :
    singleColumnKeys (g :: gs) = soleColumn g ++ singleColumnKeys gs := rfl

/- The desired validation decision for a requested lookup key. The key is
   rejected exactly when ALL of: it is not the primary-key alias, it is not
   individually declared unique, AND it is not covered by any single-column
   uniqueness guarantee. Otherwise it is admissible. The primary-key alias and
   an individually-unique key are always admissible; a key that is the sole
   column of a uniqueness guarantee is ALSO admissible (it is guaranteed unique
   across all rows just the same). -/
def lookupFieldDecision (fieldName : String) (fieldUnique : Bool)
    (constraints : List (List String)) : Except ValidationErr Unit :=
  if (fieldName != "pk") && (!fieldUnique) &&
      (!(singleColumnKeys constraints).contains fieldName) then
    Except.error ValidationErr.fieldNotUnique
  else
    Except.ok ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a requested lookup key is admissible for retrieving records
   keyed by that field. All inputs are read-only (none is `mut`):
     * `fieldName`   — the requested key name; the primary-key alias is `"pk"`;
     * `fieldUnique` — whether that key is individually declared unique;
     * `constraints` — the uniqueness guarantees in force, each given as the
                       list of column names it spans.

   Desired behaviour: the key is admissible unless it is neither the primary-key
   alias, nor individually unique, nor the sole column of a uniqueness
   guarantee — in which case it is rejected. A key that is guaranteed unique
   solely by a single-column uniqueness guarantee MUST be accepted, exactly like
   an individually-unique key. The decision fully determines whether the
   retrieval proceeds or is refused. -/
method validateLookupField (fieldName : String) (fieldUnique : Bool)
    (constraints : List (List String)) return (out : Except ValidationErr Unit)
  ensures out = lookupFieldDecision fieldName fieldUnique constraints
  do
    -- impl-start
    -- PRE-PATCH SKELETON (buggy): the decision consults only whether the key is
    -- the primary-key alias or individually unique; it ignores the uniqueness
    -- guarantees entirely, so a key that is the sole column of a guarantee is
    -- wrongly rejected.
    if (fieldName != "pk") && (!fieldUnique) then
      return Except.error ValidationErr.fieldNotUnique
    else
      return Except.ok ()
    -- impl-end

/- The backward-fold step: dropping one fewer guarantee exposes the guarantee at
   `i-1` on the front, so `singleColumnKeys` peels one `soleColumn`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma singleColumnKeys_drop_step (constraints : List (List String)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ constraints.length) :
    singleColumnKeys (constraints.drop (i - 1))
      = soleColumn constraints[i - 1]! ++ singleColumnKeys (constraints.drop i) := by
  have hlt : i - 1 < constraints.length := by omega
  have hcons : constraints.drop (i - 1) = constraints[i - 1]! :: constraints.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, singleColumnKeys_cons]

prove_correct validateLookupField by
  loom_solve
  all_goals simp_all [lookupFieldDecision]
