import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the value selection is computed entirely from the
--  three candidate inputs, modeled deeply; nothing is delegated to an
--  unchanged callee.)
-- axioms-end

-- pure-start
/- Resolve a single configuration value from a precedence-ordered set of
   sources. A configuration may supply the value under a *preferred* key or,
   for backward compatibility, under a *secondary* key; if neither key is
   present a constructed *base* value is used. The preferred source wins over
   the secondary source, which in turn wins over the base value. Presence is
   key-presence, not value-truthiness: a source that is present but empty still
   takes precedence over the sources below it (modeled with `Option`: `some v`
   = key present with value `v`, `none` = key absent). -/
def resolveWithPrecedence
    (preferredOpt secondaryOpt : Option String) (baseValue : String) : String :=
  preferredOpt.getD (secondaryOpt.getD baseValue)

/- Single-step unfold so `loom_solve` can discharge the postcondition. -/
@[grind] lemma resolveWithPrecedence_def
    (p s : Option String) (b : String) :
    resolveWithPrecedence p s b = p.getD (s.getD b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Selection of an effective configuration value from three candidate sources:
   a preferred override (`preferredOpt`), a secondary override kept for
   backward compatibility (`secondaryOpt`), and a base value always available
   (`baseValue`). The result is the value of the highest-precedence source that
   is present — preferred, then secondary, then base. All three inputs are
   read-only (none declared `mut`); the selection only reads them (directive
   5). The two override sources are modeled as `Option String` (a key that may
   be absent); the base value as `String` (always present). -/
method selectOverride
    (preferredOpt : Option String) (secondaryOpt : Option String) (baseValue : String)
    return (out : String)
  ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
  do
    -- impl-start
    let viaSecondary := secondaryOpt.getD baseValue
    let out := preferredOpt.getD viaSecondary
    return out
    -- impl-end

prove_correct selectOverride by
  loom_solve
