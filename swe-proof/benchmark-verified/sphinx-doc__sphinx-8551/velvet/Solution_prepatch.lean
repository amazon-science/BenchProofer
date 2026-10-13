import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under spec is a pure data-flow that builds a
   cross-reference descriptor from its inputs: the documentation scope in effect
   (the current module name and current class name, each possibly unset) is
   recorded onto the descriptor alongside the resolution target. Every observable
   is computed from the inputs; nothing is borrowed from an oracle. There is no
   module-level `axiom` and no `:|` callee stub (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The documentation scope in effect at the point a cross-reference is built: the
   name of the current module and the name of the current class, each `none` when
   unset. These are the read-only inputs whose faithful propagation is the
   behaviour at issue. -/
abbrev ScopeName := Option (List Char)

/- A cross-reference descriptor for an inline type specifier. It records the
   resolution domain, the reference kind, the resolution target, a flag asking
   resolution to prefer the most specific match, and — the behaviour at issue —
   the documentation scope (current module / current class) under which the
   reference was written. A descriptor that fails to record the scope forces a
   later resolution step to search every (sub)module, producing the spurious
   ambiguity the issue reports. -/
structure CrossRef where
  domain         : List Char
  kind           : List Char
  target         : List Char
  preferSpecific : Bool
  scopeModule    : ScopeName
  scopeClass     : ScopeName
  deriving DecidableEq, Repr

/- Normalize a resolution target written with an explicit leading marker: a
   leading `.` or `~` selects an alternate display/lookup mode and is stripped
   from the stored target. Any other target is stored verbatim. (Unchanged
   behaviour, modeled concretely.) -/
def normalizeTarget (target : List Char) : List Char :=
  match target with
  | c :: rest => if c = '.' ∨ c = '~' then rest else target
  | []        => target

/- Normalize the reference kind against the target: `None` is not a type, so a
   class-kind reference whose (raw) target is exactly `None` is built as an
   object-kind reference instead. Any other kind/target combination keeps the
   kind verbatim. (Unchanged pre-existing behaviour of the concrete inline-type
   reference builders, inside the modeled boundary; modeled concretely.) -/
def normalizeKind (kind target : List Char) : List Char :=
  if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
    ['o','b','j']
  else kind

/- The cross-reference descriptor for an inline type specifier, modeled deeply.
   The kind and target are normalized and the prefer-specific flag is set (all
   unchanged behaviour); crucially, the descriptor carries the current
   documentation scope so a same-scope target can be preferred during
   resolution. Pinned by the method `ensures`; validated against the real
   reference builder by G-CONF. -/
def scopedRef (curModule curClass : ScopeName) (domain kind target : List Char) :
    CrossRef :=
  { domain         := domain
    kind           := normalizeKind kind target
    target         := normalizeTarget target
    preferSpecific := true
    scopeModule    := curModule
    scopeClass     := curClass }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the cross-reference descriptor for an inline type specifier written
   inside a documentation entry. Desired behaviour: the descriptor must record
   the documentation scope in effect where it was written — the current module
   and the current class — so that an unqualified target resolves against the
   current scope (and its parent scopes) rather than matching the same short name
   in every (sub)module. Failing to record the scope is exactly the defect that
   yields false "more than one target" ambiguity for an unqualified name.

   `curModule`, `curClass`, `domain`, `kind`, `target` are read-only: the
   method builds and returns a fresh descriptor and never mutates its inputs.

   The kind is required non-empty: every caller inside the modeled slice
   supplies a concrete reference kind, and a kindless request takes a plain
   display-only rendering path that builds no cross-reference descriptor at
   all — that path is outside the modeled behaviour (mapping.md §1). -/
method buildCrossRef (curModule : ScopeName) (curClass : ScopeName) (domain : List Char)
    (kind : List Char) (target : List Char)
    return (out : CrossRef)
  require kind ≠ []
  ensures out = scopedRef curModule curClass domain kind target
  ensures out.scopeModule = curModule
  ensures out.scopeClass = curClass
  ensures out.preferSpecific = true
  ensures out.kind = normalizeKind kind target
  ensures out.target = normalizeTarget target
  do
    -- impl-start
    -- `None` is not a type: a class-kind reference to the literal target `None`
    -- is built as an object-kind reference instead (unchanged behaviour)
    let kindAdj :=
      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
        ['o','b','j']
      else kind
    -- the base reference built for this target, carrying the raw target
    let base : CrossRef :=
      { domain := domain, kind := kindAdj, target := target,
        preferSpecific := false, scopeModule := none, scopeClass := none }
    -- ask resolution to prefer the most specific match
    let withSpec := { base with preferSpecific := true }
    -- (the documentation scope is NOT recorded onto the reference here, so a
    -- later resolution step searches every (sub)module for the target)
    let withScope := withSpec
    -- normalize an explicit-prefix target (leading scope/short-name marker)
    let result :=
      match target with
      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
                     else withScope
      | []        => withScope
    return result
    -- impl-end

prove_correct buildCrossRef by
  loom_solve <;>
    (simp only [scopedRef, normalizeKind, normalizeTarget]
     cases target with
      | nil => simp
      | cons c rest => by_cases h : c = '.' ∨ c = '~' <;> simp [h])
