import Mathlib
-- imports-end

/-!
Computing the displayed type labels for a documented callable.

A documented callable contributes, to the generated documentation, a table that
maps each of its parameters (and, separately, its return value) to the *type
label* shown for it. The inputs to this computation are:

  * the callable's parameter list, in declaration order, each parameter carrying
    its declared type *name* when it has one (a parameter with no declared type
    is documented without a type label and contributes no entry);
  * the declared type *name* of the return value, when present;
  * the user-configured *type-alias* table — a list of `name → replacement`
    pairs — which lets a project display a chosen label in place of a type's
    default rendering;
  * the default renderer, which turns a declared type name into the label shown
    when no alias applies.

The desired table:

  * is built in declaration order — one entry per parameter that carries a
    declared type name, keyed by the parameter's own name — followed by a single
    return entry (under the reserved key `"return"`) when the return value
    carries a declared type name;
  * shows, for every entry, the alias-aware label of that entry's declared type
    name: if the name occurs as a key in the type-alias table, its configured
    replacement is shown; otherwise the default renderer's label is shown.

The configured type aliases must therefore be honoured for parameter labels and
for the return label alike.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The default rendering of a
-- declared type name is taken as a free input `render : String → String`,
-- universally quantified in the theorem; the spec is required to hold for every
-- such renderer. The alias-aware label rule — consulting the configured alias
-- table before falling back to the default renderer — is modeled directly below
-- (`renderName`), so it is an A-reference, not a consumed axiom.
-- axioms-end

-- pure-start
/-- Look up `nm` in the alias table, returning the configured replacement label
for the first matching key, or `none` when `nm` is not aliased. -/
def lookupAlias (aliases : List (String × String)) (nm : String) : Option String :=
  (aliases.find? (fun p => p.1 == nm)).map (·.2)

/-- The alias-aware label of a declared type name: its configured replacement if
the name is aliased, otherwise the default renderer's label. -/
def renderName (render : String → String) (aliases : List (String × String))
    (nm : String) : String :=
  match lookupAlias aliases nm with
  | some target => target
  | none => render nm

/-- The parameter entries, in declaration order: one `(parameter name, label)`
pair per parameter that carries a declared type name; parameters with no
declared type name contribute nothing. Front-recursive over the parameter list. -/
def paramEntries (render : String → String) (aliases : List (String × String)) :
    List (String × Option String) → List (String × String)
  | [] => []
  | (_name, none) :: rest => paramEntries render aliases rest
  | (name, some nm) :: rest =>
      (name, renderName render aliases nm) :: paramEntries render aliases rest

/-- The return entry, under the reserved key `"return"`, present only when the
return value carries a declared type name. -/
def returnEntry (render : String → String) (aliases : List (String × String))
    (ret : Option String) : List (String × String) :=
  match ret with
  | none => []
  | some nm => [("return", renderName render aliases nm)]
-- pure-end

-- post-conditions-start
/-- `result` is the displayed type-label table for a documented callable, given
the default renderer `render`, the configured alias table `aliases`, the
parameters `params` (each `(name, optional declared type name)`, in order), and
the optional return type name `ret`.

The table is the ordered parameter entries followed by the return entry; every
label is alias-aware. The whole result is pinned to the inputs: order, which
keys are present, and each label are all determined. -/
def problem_spec_aliasedLabels (render : String → String)
    (aliases : List (String × String)) (params : List (String × Option String))
    (ret : Option String) (result : List (String × String)) : Prop :=
  result = paramEntries render aliases params ++ returnEntry render aliases ret
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the configured alias table is NOT consulted when
-- building the labels — every entry uses the default renderer directly. So an
-- annotation whose name has a configured alias is shown with its default label
-- instead of the configured replacement, for both parameter and return entries.
def implementation_aliasedLabels (render : String → String)
    (aliases : List (String × String)) (params : List (String × Option String))
    (ret : Option String) : List (String × String) := Id.run do
  let mut annotation : List (String × String) := []
  for (name, ann) in params do
    if let some nm := ann then
      annotation := annotation ++ [(name, render nm)]
  if let some nm := ret then
    annotation := annotation ++ [("return", render nm)]
  return annotation
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (when
-- an alias applies, `render nm ≠ renderName render aliases nm`, contradicting
-- the `result = paramEntries … ++ returnEntry …` clause), so verification fails.
theorem correct_aliasedLabels :
    ∀ (render : String → String) (aliases : List (String × String))
      (params : List (String × Option String)) (ret : Option String),
      problem_spec_aliasedLabels render aliases params ret
        (implementation_aliasedLabels render aliases params ret) := by
  sorry
-- proof-end
