import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Building the code reference for a type value is a
--  pure straight-line dispatch over a handful of facts read off the value; it
--  calls nothing it does not itself compute. The selected name is modeled
--  DEEPLY in the `pure` region, so there is no consumed axiom and no A-reference
--  deep model of an outside callee. Nothing here is axiomatized.)
-- axioms-end

-- pure-start
/- The facts a type value exposes that the reference computation reacts to.
   Only these are observable to the computation (mapping.md §2):
     * `isSentinelBase` — the value is the framework's base model type, which has
                          one canonical spelling;
     * `isNoneType`     — the value is the type of the absent value, also with one
                          canonical spelling;
     * `isBuiltin`      — the value lives in the language's built-in namespace, so
                          it needs no module prefix and no import;
     * `module`         — the dotted name of the module the value lives in;
     * `qualified`      — the value's location WITHIN its module, INCLUDING every
                          enclosing scope it is nested in (so a value defined
                          inside another is spelled enclosing-then-inner);
     * `bare`           — the value's own name, WITHOUT any enclosing scope. -/
structure TypeValue where
  isSentinelBase : Bool
  isNoneType : Bool
  isBuiltin : Bool
  module : List Char
  qualified : List Char
  bare : List Char
deriving Inhabited, DecidableEq

/- A rendered code reference: the source-text expression that names the value,
   together with the import line needed to make that expression resolve
   (`none` when no import is needed). -/
structure Rendered where
  expr : List Char
  imp : Option (List Char)
deriving Inhabited, DecidableEq

/- The reference for a type value, spelled out. In priority order:
     * the base model type renders to its one canonical spelling, no import;
     * the absent-value type renders to its one canonical spelling, no import;
     * a built-in renders to its own bare name, no module prefix, no import;
     * anything else renders to its module followed by its FULL within-module
       location — the location that includes every enclosing scope, so a value
       nested inside another resolves to the enclosing-then-inner path — and
       carries an import of its module. -/
def renderRef (t : TypeValue) : Rendered :=
  if t.isSentinelBase then
    { expr := "models.Model".toList, imp := none }
  else if t.isNoneType then
    { expr := "type(None)".toList, imp := none }
  else if t.isBuiltin then
    { expr := t.bare, imp := none }
  else
    { expr := t.module ++ ['.'] ++ t.qualified,
      imp := some ("import ".toList ++ t.module) }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the code reference (expression + needed import) for a type value.

   The value is read-only (not `mut`): the computation inspects it and builds a
   fresh reference, mutating nothing (directive 5). The result is pinned exactly:
   the two sentinel types and the built-in case have set spellings with no
   import; every other value is named by its module plus its FULL within-module
   location and imports that module. Crucially, that location is the one that
   includes every enclosing scope (`qualified`) — so a value nested inside another
   resolves to the enclosing-then-inner path, not to a same-named top-level value
   (`bare`). -/
method typeReference (t : TypeValue) return (out : Rendered)
  ensures out = renderRef t
  -- General (non-sentinel, non-builtin) values: named by module + FULL location,
  -- including any enclosing scope; the import is that module.
  ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ ¬ t.isBuiltin) →
            out = { expr := t.module ++ ['.'] ++ t.qualified,
                    imp := some ("import ".toList ++ t.module) }
  -- Built-ins: bare name, no import.
  ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ t.isBuiltin) →
            out = { expr := t.bare, imp := none }
  do
    -- impl-start
    -- Pre-image skeleton: the general branch names a value by its module joined
    -- to the value's own name only (`bare`), dropping any enclosing scope. For a
    -- value nested inside another this resolves to the wrong (top-level) path.
    -- The frozen spec requires the FULL within-module location (`qualified`), so
    -- prove_correct MUST fail.
    if t.isSentinelBase then
      return { expr := "models.Model".toList, imp := none }
    else
      if t.isNoneType then
        return { expr := "type(None)".toList, imp := none }
      else
        if t.isBuiltin then
          return { expr := t.bare, imp := none }
        else
          return { expr := t.module ++ ['.'] ++ t.bare,
                   imp := some ("import ".toList ++ t.module) }
    -- impl-end

prove_correct typeReference by
  loom_solve <;> simp_all [renderRef]
