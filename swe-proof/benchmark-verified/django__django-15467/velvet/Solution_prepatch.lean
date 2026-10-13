import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees in the modeled slice. The decision modeled here is a
--  closed function of its inputs: a flag saying whether the related field allows
--  an empty selection, and a caller-provided override that is either absent or
--  carries an explicit value. The only outside-provided value is the module's standard
--  fallback placeholder label; it is modeled DEEPLY as the literal placeholder
--  string `defaultLabel` (`pure` region) and validated against the real
--  localization callee that produces it by axiom_check.py (G-AX) — an
--  A-reference, not a consumed axiom. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The fallback placeholder shown for the empty selection when the related field
   allows one and the caller offered no placeholder of its own. Modeled as the
   literal placeholder text the module's standard localization helper returns for
   this position (a deep model — an A-reference validated == the real helper by
   axiom_check.py / G-AX, mapping.md §3.1). A present-with-value option carrier
   `some s` means a placeholder string `s` is shown for the empty selection;
   `none` means no empty selection is offered. -/
@[grind] def defaultLabel : Option String := some "None"

/- The placeholder resolved for the empty selection.

   `allowsBlank` says the related field allows an empty selection. `override`
   models what the caller already provided for the placeholder, with
   key-presence semantics: `none` = the caller provided nothing (the key is
   absent), `some v` = the caller provided the value `v` (possibly `v = none`,
   i.e. an explicit "no placeholder").

   Desired behaviour: when an empty selection is allowed, a caller-provided
   placeholder is kept as-is and ONLY when the caller provided nothing does the
   standard fallback placeholder apply; when no empty selection is allowed, no
   placeholder is shown regardless of what the caller offered. `Option.getD`
   captures the keep-caller-value-else-fallback choice exactly (it mirrors the
   "lookup with default" the resolution performs). -/
@[grind] def resolvedLabel (allowsBlank : Bool) (override : Option (Option String)) :
    Option String :=
  if allowsBlank then override.getD defaultLabel else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolving the placeholder for the empty selection of a single-choice related
   field rendered as mutually-exclusive options.

   `allowsBlank` reports whether the related field allows an empty selection.
   `override` is the placeholder the caller already supplied, carried with
   key-presence semantics (`none` = nothing supplied; `some v` = supplied the
   value `v`, where `v = none` is an explicit "no placeholder"). The result is
   the placeholder ultimately shown for the empty selection.

   Desired behaviour: a caller-supplied placeholder takes precedence and is
   preserved whenever an empty selection is allowed; the standard fallback
   placeholder applies only when an empty selection is allowed and the caller
   supplied nothing; and when no empty selection is allowed, no placeholder is
   shown at all.

   Both inputs are read-only (neither `mut`): the routine inspects the flag and
   the caller's override and produces the resolved placeholder, mutating neither
   (directive 5). The resolution is pinned exactly by `resolvedLabel`. -/
method emptyLabelFor (allowsBlank : Bool) (override : Option (Option String))
    return (out : Option String)
  ensures out = resolvedLabel allowsBlank override
  do
    -- impl-start
    -- Pre-image skeleton: when an empty selection is allowed this always
    -- installs the standard fallback placeholder, discarding any placeholder the
    -- caller supplied. The frozen spec requires the caller's override to be kept
    -- (resolvedLabel uses `override.getD defaultLabel`), so prove_correct MUST
    -- fail whenever the caller supplied a value.
    if allowsBlank then
      let e : Option String := defaultLabel
      return e
    else
      return none
    -- impl-end

prove_correct emptyLabelFor by
  loom_solve
