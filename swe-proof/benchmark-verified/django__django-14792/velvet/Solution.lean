import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no axioms: this operation reads two already-available labels off its input
--  and selects between them; there is no unchanged callee to axiomatize.)
-- axioms-end

-- pure-start
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the public label for a region descriptor.

   A descriptor offers two labels: a short label that may be absent (`none`)
   or empty, and a full label that is always present. The desired result is
   the short label whenever it carries content, and the full label otherwise.

   `shortLabel`/`fullLabel` are read-only inputs (no `mut`): the result is a
   pure selection between them. -/
method resolveZoneLabel (shortLabel : Option (List Char)) (fullLabel : List Char)
    return (out : List Char)
  ensures (∀ s, shortLabel = some s → s ≠ [] → out = s)
  ensures (shortLabel = none → out = fullLabel)
  ensures (∀ s, shortLabel = some s → s = [] → out = fullLabel)
  do
    -- impl-start
    match shortLabel with
    | none => return fullLabel
    | some s =>
      let out := if s ≠ [] then s else fullLabel
      return out
    -- impl-end

prove_correct resolveZoneLabel by
  loom_solve
