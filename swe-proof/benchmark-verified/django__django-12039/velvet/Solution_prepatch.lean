import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees. The per-column rendering is spelled out directly as
   `columnText` below. The column-name token is taken as an input carrier
   (mapping.md §2), so the name-quoting helper is not represented as an axiom. -/
-- axioms-end

-- pure-start
/- The textual form of one indexed column reference. A column is rendered as
   its name token, optionally followed by a trailing qualifier. A qualifier is
   appended only when one is supplied for this position (`idx` is within the
   supplied list) AND that qualifier is non-empty; in that case exactly one
   space separates the name from the qualifier. An absent qualifier (`idx`
   beyond the supplied list) or an empty qualifier contributes nothing — not
   even a separating space. -/
def columnText (name : List Char) (suffixes : List (List Char)) (idx : Nat) :
    List Char :=
  if idx < suffixes.length then
    if suffixes[idx]! = [] then name
    else name ++ ' ' :: suffixes[idx]!
  else name
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method renderColumn (name : List Char) (suffixes : List (List Char)) (idx : Nat)
    return (out : List Char)
  ensures out = columnText name suffixes idx
  do
    -- impl-start
    -- Pre-image skeleton: when a qualifier is supplied for this position it is
    -- appended by bare concatenation, with no separating space and no
    -- empty-qualifier guard. The frozen spec requires a single separating
    -- space before any non-empty qualifier, so prove_correct MUST fail on the
    -- supplied-non-empty-qualifier case.
    let mut col := name
    if idx < suffixes.length then
      col := name ++ suffixes[idx]!
    return col
    -- impl-end

prove_correct renderColumn by
  loom_solve <;> simp_all [columnText]
