import Mathlib
-- imports-end

/-!
The effective antialiasing flag of a text artist.

A text artist exposes a per-object antialiasing setting, in the same spirit as
other drawable artists. The value is a boolean that is later consulted by the
drawing stage. It is resolved from three sources, in increasing priority:

* a global default boolean (the configured fallback used when nothing more
  specific is given);
* an optional value supplied when the artist is created (when omitted, the
  global default stands);
* an optional value supplied afterwards by an explicit assignment on the artist
  (when never assigned, the previously-resolved value stands).

The getter returns exactly this resolved boolean, and it is this same boolean
that the drawing stage hands to the graphics context. The desired rule is:

  * with no per-object choice ever made, the resolved value equals the global
    default;
  * a value supplied at creation overrides the global default;
  * a later explicit assignment overrides whatever was in effect before it,
    regardless of how that earlier value arose.

The resolution is independent of the global default once a per-object value is
in effect.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The global
-- default boolean is supplied as an input (`rcDefault`); the resolution is
-- modeled structurally over that default together with the two optional
-- per-object choices, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The resolved antialiasing boolean. `rcDefault` is the global fallback,
`ctorArg` the optional value supplied at creation (`none` = omitted), and
`laterSet` the optional value supplied by a later explicit assignment
(`none` = never assigned). A later assignment wins over a creation-time value,
which in turn wins over the global default. -/
def resolveAntialiased (rcDefault : Bool) (ctorArg : Option Bool)
    (laterSet : Option Bool) : Bool :=
  laterSet.getD (ctorArg.getD rcDefault)
-- pure-end

-- post-conditions-start
/-- The reported antialiasing boolean is exactly the value selected by the
resolution rule: a later explicit assignment if present, otherwise a
creation-time value if present, otherwise the global default. -/
def problem_spec_textAntialiased
    (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool)
    (result : Bool) : Prop :=
  result = resolveAntialiased rcDefault ctorArg laterSet
-- post-conditions-end

-- impl-start
/-- Pre-patch skeleton: there is no per-object antialiasing state, so the value
reported is always the global default — the optional per-object choices are
ignored. -/
def implementation_textAntialiased
    (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
  Id.run do
    let mut acc := rcDefault
    return acc
-- impl-end

-- proof-start
theorem correct_textAntialiased :
    ∀ (rcDefault : Bool) (ctorArg laterSet : Option Bool),
      problem_spec_textAntialiased rcDefault ctorArg laterSet
        (implementation_textAntialiased rcDefault ctorArg laterSet) := by
  intro rcDefault ctorArg laterSet
  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased
  cases ctorArg <;> cases laterSet <;> rfl
-- proof-end
