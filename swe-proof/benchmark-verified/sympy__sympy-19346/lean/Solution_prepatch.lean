import Mathlib
-- imports-end

/-!
Canonical textual representation of a mapping and of an unordered collection.

A symbolic-expression toolkit exposes a *canonical representation* function that
turns a value into a string from which the value can be reconstructed. The
representation is built structurally: containers are rendered by delimiting their
contents and rendering **each contained element with the very same canonical
representation function** (the recursive renderer), so that nested structure is
reproduced faithfully all the way down.

This file pins that canonical representation for two container shapes.

* A **mapping** — an ordered list of key/value entries — is rendered as the
  entries, in order, each written as the canonical representation of the key,
  then `": "`, then the canonical representation of the value; the entries are
  separated by `", "`; the whole is wrapped in braces `{ … }`. The empty mapping
  renders as `"{}"`.

* An **unordered collection** — taken in its iteration order — is rendered, when
  non-empty, as the canonical representation of each element, separated by `", "`
  and wrapped in braces `{ … }`. The empty collection has the dedicated rendering
  `"set()"`.

In both cases the contained elements must be rendered through the recursive
canonical renderer (`elemRepr` below), not through any other textual conversion;
that is exactly what makes a nested value reconstructible.
-/

-- axioms-start
/-- A single symbolic-expression value (key, value, or collection element). Its
internal structure is irrelevant here; only its canonical rendering matters. -/
opaque SymExpr : Type

/-- The canonical recursive renderer applied to one element: the same
representation function the toolkit uses everywhere, which is what allows a
rendered container to be parsed back. Declared as an opaque carrier (the
recursion lives inside it); the proof consumes no property of it. -/
opaque elemRepr : SymExpr → String

/-- An alternative, NON-canonical textual conversion of one element (an element's
own plain textual form, which does not recurse through the canonical renderer).
Declared so the contrasting behaviour can be expressed; the canonical spec never
references it. -/
opaque nativeRepr : SymExpr → String
-- axioms-end

-- pure-start
/-- The rendering of one key/value entry of a mapping: the canonical
representation of the key, `": "`, then the canonical representation of the
value. -/
def entryText (p : SymExpr × SymExpr) : String :=
  elemRepr p.1 ++ ": " ++ elemRepr p.2
-- pure-end

-- post-conditions-start
/-- Canonical rendering of a mapping given as an ordered list of key/value
entries: each entry rendered (key `": "` value, both via the canonical renderer),
the entries joined by `", "`, wrapped in braces. The empty mapping yields `"{}"`.
Every entry is pinned to the canonical renderer, so no element may be rendered by
any other conversion. -/
def problem_spec_dictRepr
    (entries : List (SymExpr × SymExpr)) (result : String) : Prop :=
  result = "{" ++ String.intercalate ", " (entries.map entryText) ++ "}"
-- post-conditions-end

-- impl-start
/-- PRE-PATCH (buggy) skeleton. With no dedicated rendering for a mapping, the
toolkit fell through to its generic fallback, which renders each contained
element with the element's own plain textual conversion (`nativeRepr`) instead of
the canonical recursive renderer (`elemRepr`). Nested structure is therefore lost
and the rendered string can no longer be reconstructed. -/
def implementation_dictRepr
    (entries : List (SymExpr × SymExpr)) : String := Id.run do
  let sep := ", "
  let mut parts : List String := []
  for p in entries do
    parts := parts ++ [nativeRepr p.1 ++ ": " ++ nativeRepr p.2]
  return "{" ++ String.intercalate sep parts ++ "}"
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- pre-patch implementation it cannot close: the spec pins every entry to the
-- canonical recursive renderer (`elemRepr`) while this impl emits the element's
-- own plain textual conversion (`nativeRepr`); the two carriers are distinct, so
-- the discriminating clause is false.
theorem correct_dictRepr :
    ∀ (entries : List (SymExpr × SymExpr)),
      problem_spec_dictRepr entries (implementation_dictRepr entries) := by
  unfold problem_spec_dictRepr implementation_dictRepr entryText
  simp [Id.run]
-- proof-end

-- post-conditions-start
/-- Canonical rendering of an unordered collection taken in iteration order: when
empty it is the dedicated literal `"set()"`; otherwise each element is rendered by
the canonical renderer, joined by `", "`, and wrapped in braces. Each element is
pinned to the canonical renderer. -/
def problem_spec_setRepr
    (elems : List SymExpr) (result : String) : Prop :=
  result =
    (if elems.isEmpty then "set()"
     else "{" ++ String.intercalate ", " (elems.map elemRepr) ++ "}")
-- post-conditions-end

-- impl-start
/-- PRE-PATCH (buggy) skeleton. With no dedicated rendering for an unordered
collection, the toolkit fell through to its generic fallback: each element was
rendered with the element's own plain textual conversion (`nativeRepr`) rather
than the canonical recursive renderer (`elemRepr`), and the empty collection was
NOT given its dedicated literal. -/
def implementation_setRepr
    (elems : List SymExpr) : String := Id.run do
  let mut parts : List String := []
  for e in elems do
    parts := parts ++ [nativeRepr e]
  return "{" ++ String.intercalate ", " parts ++ "}"
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- pre-patch implementation it cannot close: the spec demands the dedicated empty
-- literal and pins every element to the canonical recursive renderer (`elemRepr`),
-- while this impl omits the empty case and emits `nativeRepr`.
theorem correct_setRepr :
    ∀ (elems : List SymExpr),
      problem_spec_setRepr elems (implementation_setRepr elems) := by
  unfold problem_spec_setRepr implementation_setRepr
  simp [Id.run]
-- proof-end
