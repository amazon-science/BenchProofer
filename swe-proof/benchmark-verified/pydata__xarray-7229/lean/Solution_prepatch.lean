import Mathlib
-- imports-end

/-!
Three-argument elementwise selection with attribute retention.

A labelled array object carries a *top-level* attribute bag plus two collections
of named *components*: data variables and coordinates. Each component has its own
name and its own attribute bag. (A plain array has no data variables; a container
object has one or more.)

Resolving a name against an object proceeds in stages, and every stage that can
answer yields an attribute bag. Each kind of labelled object RESERVES a
collection of names for its own use, determined by its kind alone. A reserved
name is answered by the object itself, ahead of any like-named component, and
yields whatever bag that answer happens to carry — for most reserved names no bag
at all, and for those whose answer is a view of the whole object, that object's
top-level bag. A name the object does not reserve is sought among its components,
data variables first and then coordinates, and yields that component's own bag. A
name that is neither reserved nor the name of a component yields the empty bag.

`select cond a b keep_attrs` produces a combined object whose data and structure
come from an elementwise three-way selection of `cond`, `a`, and `b`. That
combination routine is itself handed the retention flag, so the attribute bags it
puts on the combined object depend on `keep_attrs` in a way this specification
does not pin down. When `keep_attrs` is false the combined object is returned
verbatim. When `keep_attrs` is true the attributes are rebuilt from the SECOND
argument `a`, component by component:

* the result's top-level attribute bag is taken from `a`'s top-level bag;
* every data-variable component of the result takes the bag that resolving its
  own name against `a` yields;
* every coordinate component of the result likewise takes the bag that resolving
  its own name against `a` yields.

There is one special shape: when the third argument `b` is a container object but
the second argument `a` is not, the result is a container into which `a` is
promoted as a single data variable. In that shape the result's top-level bag is
emptied, only the data variable matching `a`'s own name receives `a`'s top-level
bag (every other data variable keeps whatever bag the combination routine gave
it), and the coordinate components are still rebuilt by resolving their names
against `a` exactly as above.

The essential guarantee, wherever a bag is rebuilt at all, is that the result
component's attributes are the ones that resolving the component's own NAME
against `a` yields — so a coordinate whose name `a` does not reserve takes its
attributes from `a`'s like-named coordinate rather than from `a`'s top-level bag.

NOT EVERY INPUT YIELDS AN OBJECT. Carrying out the rebuild means enumerating the
combined object's components and consulting, for each one, the answer that
resolving its name against `a` gives. On some inputs those consultations cannot
be carried out at all, and the routine completes with NO object rather than with a
combined one. Which inputs those are is not a function of the data this
specification records about `cond`, `a` and `b`: two calls whose recorded
`cond`, `a` and `b` are equal can differ on whether they yield an object, because
the obstruction lives in finer structure of the objects that this record does not
carry. It is therefore taken as a separate observation `produces` OF THE SAME
CALL — `produces` is true exactly when that call yields a combined object — and
the specified outcome is an OPTIONAL object: `none` when `produces` is false, and
otherwise exactly the combined object with attributes retained as described
above. The retention itself is not relaxed anywhere: on every input that yields
an object, the outcome is pinned to one value.
-/

-- axioms-start
/-- An attribute bag: an association list of attribute name/value pairs. -/
abbrev Attrs := List (String × String)

/-- A named component (a data variable or a coordinate) carrying its own
attribute bag. -/
structure Component where
  name : String
  attrs : Attrs
deriving DecidableEq, Repr, Inhabited

/-- A labelled array object: a top-level attribute bag, an optional own name, a
flag marking whether it is a container object, its data-variable and coordinate
components, and the names its own kind RESERVES — the names that resolving
against this object answers itself, ahead of any like-named component, each
paired with the attribute bag that answer carries. -/
structure XObj where
  topAttrs : Attrs
  name : Option String
  isContainer : Bool
  dataVars : List Component
  coords : List Component
  reserved : List (String × Attrs)
deriving DecidableEq, Repr, Inhabited

-- The elementwise three-argument selection that produces the combined object's
-- data and structure (its component names and values) is left opaque here. It
-- takes the retention flag as a FOURTH argument: the flag governs how that
-- routine itself merges the input attribute bags, so both the structure and the
-- attribute bags it yields may differ between the two flag values. Its output is
-- whatever that routine yields; this specification only governs which of the
-- resulting components' attribute bags are subsequently rebuilt, and from where.
-- No property of it is asserted.
opaque select_combine : XObj → XObj → XObj → Bool → XObj
-- axioms-end

-- pure-start
/-- The attribute bag that resolving `nm` against `a` yields: if `a` reserves
that name, the bag its own answer carries; otherwise the bag of the component of
`a` bearing that name (data variables searched before coordinates); otherwise the
empty bag. -/
def lookupAttrs (a : XObj) (nm : String) : Attrs :=
  match a.reserved.find? (fun e => e.1 == nm) with
  | some e => e.2
  | none =>
    match (a.dataVars ++ a.coords).find? (fun c => c.name == nm) with
    | some c => c.attrs
    | none => []

/-- Rebuild every component's attribute bag by resolving its name against `a`. -/
def rebuildFrom (a : XObj) (comps : List Component) : List Component :=
  comps.map (fun c => { c with attrs := lookupAttrs a c.name })

/-- The combined object an input that DOES yield one yields. The data/structure
carrier is the combination `select_combine`; this function pins how each
resulting component's attribute bag is populated. -/
def retainedResult (cond a b : XObj) (keep_attrs : Bool) : XObj :=
  let r := select_combine cond a b keep_attrs
  if !keep_attrs then
    r
  else if b.isContainer && !a.isContainer then
    -- promotion shape: `a` becomes a single data variable in a container result
    let dvs :=
      match a.name with
      | some nm =>
          r.dataVars.map (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c)
      | none => r.dataVars
    { r with topAttrs := []
           , dataVars := dvs
           , coords := rebuildFrom a r.coords }
  else
    { r with topAttrs := a.topAttrs
           , dataVars := rebuildFrom a r.dataVars
           , coords := rebuildFrom a r.coords }

/-- The fully-specified outcome. `produces` is the observation of THIS call that
says whether it yields a combined object at all; when it does, the object is
exactly `retainedResult`. -/
def expectedResult (cond a b : XObj) (keep_attrs : Bool) (produces : Bool) : Option XObj :=
  if produces then some (retainedResult cond a b keep_attrs) else none
-- pure-end

-- post-conditions-start
/-- The outcome is `none` on a call that yields no object (`produces` false).
Otherwise it is exactly the combined object — the combination routine applied to
`cond`, `a`, `b` and the retention flag — with attributes retained from the
second argument component-by-component (the top-level bag from `a`'s own, and
every data variable and every coordinate from what resolving its name against
`a` yields), with the container promotion shape handled as described. When
`keep_attrs` is false the combined object is returned unchanged.

This post-condition is an exact equality to the TOTAL function
`expectedResult`, so it is DETERMINISTIC: for each input — the three objects, the
retention flag, and `produces` — there is exactly one satisfying `result`. -/
def problem_spec_where
    (cond a b : XObj) (keep_attrs produces : Bool) (result : Option XObj) : Prop :=
  result = expectedResult cond a b keep_attrs produces
-- post-conditions-end

-- impl-start
def implementation_where
    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do
  -- Pre-patch bug: attribute retention is funnelled through a single callback
  -- that always yields `a`'s top-level attribute bag, and the combination
  -- routine then stamps that one bag onto EVERY level of the result — top-level,
  -- data variables, and coordinates alike. Coordinate components therefore have
  -- their own attributes overwritten by `a`'s top-level bag instead of being
  -- drawn from `a`'s like-named coordinate.
  let mut result := select_combine cond a b keep_attrs
  if keep_attrs then
    result := { result with topAttrs := a.topAttrs }
    result := { result with
      dataVars := result.dataVars.map (fun c => { c with attrs := a.topAttrs }) }
    result := { result with
      coords := result.coords.map (fun c => { c with attrs := a.topAttrs }) }
  if produces then
    return some result
  else
    return none
-- impl-end

-- proof-start
theorem correct_where :
    ∀ (cond a b : XObj) (keep_attrs produces : Bool),
      problem_spec_where cond a b keep_attrs produces
        (implementation_where cond a b keep_attrs produces) := by
  sorry
-- proof-end
