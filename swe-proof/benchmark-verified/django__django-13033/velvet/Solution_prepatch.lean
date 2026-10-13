import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a pure boolean function
--  of the resolved field metadata and the lookup path; the machinery that
--  resolves that metadata is unchanged and shared by both branches, so it is
--  not consumed as an outside contract. There is no `axiom` declaration and no
--  A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- A relation lookup is written as a path of segments joined by a separator
   (e.g. `a__b__c` is the three segments `a`, `b`, `c`). The *terminal segment*
   is the last one — the concrete attribute actually named at the end of the
   path. -/
def terminalSegment (segments : List (List Char)) : List Char :=
  segments.getLast!

/- Whether to append a related model's own default ordering for an ordering
   lookup. The default ordering of the pointed-to model is appended only when

     * the resolved field is a relation, AND
     * that model declares a default ordering, AND
     * the field's stored attribute name is NOT the attribute named by the
       TERMINAL segment of the lookup path (when the path ends at the field's
       own stored attribute, the column is ordered directly rather than
       expanding the related model's default ordering), AND
     * the lookup is not the primary-key shortcut `pk`.

   The terminal-segment comparison is what distinguishes a lookup that ends at
   a relation's stored attribute (order directly by that column) from one that
   ends at the relation itself (expand the related model's default ordering). -/
def appendRelatedDefaultOrdering
    (fieldIsRelation modelHasDefaultOrdering : Bool)
    (fieldAttr : Option (List Char))
    (segments : List (List Char)) (lookup : List Char) : Bool :=
  fieldIsRelation && modelHasDefaultOrdering &&
    (fieldAttr != some (terminalSegment segments)) &&
    (lookup != "pk".toList)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method orderingExpansionDecision (fieldIsRelation : Bool) (modelHasDefaultOrdering : Bool) (fieldAttr : Option (List Char)) (segments : List (List Char)) (lookup : List Char) return (out : Bool)
  require segments ≠ []
  ensures out =
    appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering
      fieldAttr segments lookup
  do
    -- impl-start
    -- Pre-image skeleton: the stored attribute name is compared against the
    -- WHOLE joined lookup path rather than its terminal segment. For any
    -- multi-segment path that ends at the field's own stored attribute this
    -- comparison can never be equal, so the expansion is forced even though
    -- the lookup names that very attribute. The frozen spec requires the
    -- terminal-segment comparison (appendRelatedDefaultOrdering), so
    -- prove_correct MUST fail.
    let endsAtStoredAttr := fieldAttr != some lookup
    let notPkShortcut := lookup != "pk".toList
    return fieldIsRelation && modelHasDefaultOrdering &&
      endsAtStoredAttr && notPkShortcut
    -- impl-end

prove_correct orderingExpansionDecision by
  loom_solve
  simp [appendRelatedDefaultOrdering]
