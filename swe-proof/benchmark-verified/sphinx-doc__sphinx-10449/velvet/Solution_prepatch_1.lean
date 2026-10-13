import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled functions decide a single observable:
--  whether a "return type" entry is appended to a documented object's
--  description, and with what text. The entry-building constructors are pure
--  data assembly, modeled directly as the produced entry text (an
--  `Option (List Char)`: `some t` = an entry carrying text `t` is appended,
--  `none` = no entry is appended) — an I/R transliteration validated against
--  the real implementation by conformance_check.py (G-CONF). The inputs are the
--  observations the decision reads: whether a return annotation exists for the
--  object, whether the description already declares a return type, the return
--  annotation's rendered text, and the object's kind. Every observable is a
--  closed function of these inputs — nothing is borrowed from an oracle, and
--  there is no unchanged library callee whose contract the proof must
--  axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether an object of the given kind must NOT advertise a "None" return type.
   A documented value/function/method that returns `None` legitimately shows a
   `None` return type; a documented *class* must not — a class has no return
   value of its own, so listing `None` as its return type is spurious. The kind
   is the object's descriptor label (`"class"`, `"function"`, `"method"`, …);
   only the class kind triggers the omission. -/
@[grind] def isClassKind (kind : List Char) : Bool := kind == "class".toList

/- The "return type" entry appended to an object's description, as the text it
   carries (`some text`) or its absence (`none`).

   An entry is appended only when the object actually has a return annotation
   (`hasReturnAnno`) AND the description does not already declare a return type
   (`returnInArgs` is false) — declaring it twice would duplicate it. When both
   hold, the entry normally carries the rendered return annotation
   (`returnAnnotation`). The sole exception: when `omitNoneReturnType` is set and
   the annotation is exactly `None`, no entry is appended at all — a `None`
   return type is suppressed for objects that must not advertise one. -/
@[grind] def returnTypeEntry (hasReturnAnno returnInArgs : Bool)
    (returnAnnotation : List Char) (omitNoneReturnType : Bool) : Option (List Char) :=
  if hasReturnAnno && !returnInArgs then
    (if (returnAnnotation == "None".toList) && omitNoneReturnType then none
     else some returnAnnotation)
  else
    none

/- The "return type" entry appended for an object of a given kind. The kind
   decides whether a `None` return type is suppressed: a class kind suppresses
   it, every other kind keeps it. Otherwise the entry is exactly the one
   `returnTypeEntry` describes. -/
@[grind] def returnTypeEntryForKind (kind : List Char) (hasReturnAnno returnInArgs : Bool)
    (returnAnnotation : List Char) : Option (List Char) :=
  returnTypeEntry hasReturnAnno returnInArgs returnAnnotation (isClassKind kind)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Append the "return type" entry to a documented object's description.

   `hasReturnAnno` says the object carries a return annotation; `returnInArgs`
   says the description already declares a return type (so a fresh entry would
   duplicate it); `returnAnnotation` is the rendered annotation text; and
   `omitNoneReturnType` requests that a `None` return type be omitted rather than
   shown. The result is the entry that gets appended — `some text` for an entry
   carrying `text`, or `none` when nothing is appended. A fresh result is built
   and no input is mutated (directive 5). -/
method emitReturnTypeEntry (hasReturnAnno : Bool) (returnInArgs : Bool)
    (returnAnnotation : List Char) (omitNoneReturnType : Bool)
    return (out : Option (List Char))
  ensures out = returnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNoneReturnType
  do
    -- impl-start
    -- Pre-image skeleton: the entry builder is unconditional — whenever the
    -- object has a return annotation not already declared, the entry carrying
    -- that annotation is appended, with no suppression path. The frozen spec
    -- requires the suppression branch (omit a `None` entry when requested), so
    -- prove_correct MUST fail.
    if hasReturnAnno && !returnInArgs then
      return (some returnAnnotation)
    else
      return none
    -- impl-end

prove_correct emitReturnTypeEntry by
  loom_solve

/- Append the "return type" entry for an object of a given `kind`. The kind
   alone selects the policy: for a class, a `None` return type is omitted (a
   class advertising `None` as its return type is spurious); for every other
   kind the entry is produced exactly as for any documented object. The
   remaining inputs and the result are as in `emitReturnTypeEntry`.

   `kind` and the other inputs are read-only (not `mut`): the routine selects the
   policy and delegates, mutating no input (directive 5). The produced entry is
   pinned for both regimes, so no result component is left free. -/
method emitReturnTypeForKind (kind : List Char) (hasReturnAnno : Bool) (returnInArgs : Bool)
    (returnAnnotation : List Char)
    return (out : Option (List Char))
  ensures out = returnTypeEntryForKind kind hasReturnAnno returnInArgs returnAnnotation
  ensures (kind = "class".toList ∧ hasReturnAnno = true ∧ returnInArgs = false
           ∧ returnAnnotation = "None".toList) → out = none
  ensures (kind ≠ "class".toList ∧ hasReturnAnno = true ∧ returnInArgs = false)
           → out = some returnAnnotation
  do
    -- impl-start
    if isClassKind kind then
      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true
      return r
    else
      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false
      return r
    -- impl-end

prove_correct emitReturnTypeForKind by
  loom_solve
