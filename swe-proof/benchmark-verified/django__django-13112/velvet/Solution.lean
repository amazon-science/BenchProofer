import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is the normalization of a
--  model-reference string into its canonical form. It is built entirely from
--  concrete character operations over the input (a case fold of code points and
--  a split on the first dot separator) and is modeled DEEPLY in the `pure`
--  region below. There is no outside callee whose contract is consumed and no
--  A-reference deep model of an outside callee: the per-code-point case fold of
--  an identifier and the dot split are modeled directly, with the Lean↔Python
--  bijection over the ASCII domain (pinned by the `require ∀ c ∈ ref,
--  c.toNat < 128`) recorded in mapping.md §2 and exercised mechanically by
--  conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- Case fold of a code-point sequence: lower every code point. Over the
   identifier alphabet (ASCII letters/digits/underscore — the alphabet of
   application labels and model names, mapping.md §2) this is exactly the
   value-level case fold the reference normalization applies to a model name. -/
def foldCase (s : List Char) : List Char := s.map Char.toLower

/- Whether the reference carries an application qualifier: it contains the dot
   separator that splits an application label from a model name. -/
def isQualified (ref : List Char) : Bool := ref.contains '.'

/- The application-label part: the prefix up to (not including) the first dot. -/
def appPart (ref : List Char) : List Char := ref.takeWhile (· ≠ '.')

/- The model-name part: everything after the first dot. -/
def namePart (ref : List Char) : List Char := (ref.dropWhile (· ≠ '.')).drop 1

/- The normalized model reference. When the reference qualifies a model with an
   application label (a single dot separator), the application label keeps its
   original case and only the model name is case-folded; otherwise the whole
   reference is case-folded. (Front: app label verbatim; back: folded name.) -/
def normalizedRef (ref : List Char) : List Char :=
  if isQualified ref then
    appPart ref ++ ['.'] ++ foldCase (namePart ref)
  else
    foldCase ref
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `ref` is a model reference. A qualified reference carries exactly one dot
   separator (an application label and a model name); the domain therefore
   excludes references with more than one dot. The reference is an ASCII
   code-point sequence (every code point < 128): application labels and model
   names are ASCII identifiers, and on ASCII the per-code-point case fold
   `Char.toLower` coincides exactly with the reference value-level case fold
   (only A–Z fold; no multi-code-point or context-sensitive Unicode folds),
   so the modeled domain is pinned to where that correspondence is exact
   (mapping.md §2–§3). The result is the canonical normalization
   `normalizedRef`. -/
method normalizeRef (ref : List Char) return (out : List Char)
  require (ref.filter (· = '.')).length ≤ 1
  require ∀ c ∈ ref, c.toNat < 128
  ensures out = normalizedRef ref
  do
    -- impl-start
    let result : List Char :=
      if ref.contains '.' then
        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
      else
        ref.map Char.toLower
    return result
    -- impl-end

prove_correct normalizeRef by
  loom_solve
  simp only [normalizedRef, isQualified, appPart, namePart, foldCase]
