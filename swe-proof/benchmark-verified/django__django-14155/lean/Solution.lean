import Mathlib
-- imports-end

/-!
Rendering a human-readable representation string for a resolved URL match.

A resolved match bundles a view together with the data describing how it was
reached: the positional arguments, the keyword arguments, the match's own name,
the chain of application names, the chain of namespaces, and the route pattern.
The representation is a single line of the form

    ResolverMatch(func=…, args=…, kwargs=…, url_name=…, app_names=…,
                  namespaces=…, route=…)

Two things govern how the individual slots are rendered.

* The view slot. A view may be given either directly or as a *partial
  application* — a callable obtained by binding some arguments of another
  callable up front. For a partial application the slot shows the callable's own
  detailed representation (which exposes the underlying callable together with
  the pre-bound arguments). For any other view the slot shows the dotted
  module-import path of the view.

* The remaining six slots. Each is rendered with its *representation* form — the
  unambiguous form in which, for example, a textual value appears delimited by
  quotes — rather than its plain display form. For values whose two forms differ
  (such as text), this is observable in the output.

Each value below is therefore supplied with both of its renderings (plain `s`
and representation `r`); the view is supplied with a flag marking whether it is a
partial application, its dotted path, and its own detailed representation. The
behavior is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every rendering consumed
-- here (each value's plain and representation forms, and the view's path and
-- detailed representation) is supplied as an input; the assembly of the output
-- line from those renderings is spelled out concretely below.
-- axioms-end

-- pure-start
/-- A value together with its two textual renderings: `s` is the plain display
form and `r` is the representation form (e.g. text delimited by quotes). For many
values the two coincide; for text they differ. -/
structure Rendered where
  s : String
  r : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for the representation line of a resolved match.

Inputs:
* `funcIsPartial` — whether the view is a partial application;
* `funcPath`      — the view's dotted import path;
* `funcRepr`      — the view's own detailed representation;
* `args kwargs urlName appNames namespaces route` — the remaining values, each
                    carrying both its plain (`s`) and representation (`r`) form.

The view slot shows `funcRepr` when the view is a partial application and
`funcPath` otherwise; each remaining slot shows its representation form. -/
def problem_spec_resolverMatchRepr
    (funcIsPartial : Bool) (funcPath funcRepr : String)
    (args kwargs urlName appNames namespaces route : Rendered)
    (result : String) : Prop :=
  result =
    "ResolverMatch(func=" ++ (if funcIsPartial then funcRepr else funcPath) ++
    ", args=" ++ args.r ++
    ", kwargs=" ++ kwargs.r ++
    ", url_name=" ++ urlName.r ++
    ", app_names=" ++ appNames.r ++
    ", namespaces=" ++ namespaces.r ++
    ", route=" ++ route.r ++ ")"
-- post-conditions-end

-- impl-start
def implementation_resolverMatchRepr
    (funcIsPartial : Bool) (funcPath funcRepr : String)
    (args kwargs urlName appNames namespaces route : Rendered)
    : String := Id.run do
  -- Choose the view slot: a partial application shows its own detailed
  -- representation; any other view shows its dotted import path.
  let mut func := funcPath
  if funcIsPartial then
    func := funcRepr
  -- Assemble the line, rendering each remaining value in its representation form.
  return "ResolverMatch(func=" ++ func ++
    ", args=" ++ args.r ++
    ", kwargs=" ++ kwargs.r ++
    ", url_name=" ++ urlName.r ++
    ", app_names=" ++ appNames.r ++
    ", namespaces=" ++ namespaces.r ++
    ", route=" ++ route.r ++ ")"
-- impl-end

-- proof-start
theorem correct_resolverMatchRepr :
    ∀ (funcIsPartial : Bool) (funcPath funcRepr : String)
      (args kwargs urlName appNames namespaces route : Rendered),
      problem_spec_resolverMatchRepr funcIsPartial funcPath funcRepr
        args kwargs urlName appNames namespaces route
        (implementation_resolverMatchRepr funcIsPartial funcPath funcRepr
          args kwargs urlName appNames namespaces route) := by
  intro funcIsPartial funcPath funcRepr args kwargs urlName appNames namespaces route
  unfold problem_spec_resolverMatchRepr implementation_resolverMatchRepr
  cases funcIsPartial <;> rfl
-- proof-end
