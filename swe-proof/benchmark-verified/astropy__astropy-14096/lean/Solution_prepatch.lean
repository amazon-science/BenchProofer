import Mathlib
-- imports-end

/-!
Resolving a named attribute on a rich coordinate object through its
fallback attribute-resolution hook.

The object first tries a number of domain-specific resolution branches for the
requested name (frame aliases, frame attributes, delegation to an embedded
frame, interpretation of the name as a transform target). Evaluating whichever
branch applies has one of two outcomes, and the hook surfaces it unchanged: the
branch yields a value, or evaluating it fails and the failure it raises escapes
the hook verbatim. Interpreting a name as a transform target is the branch that
makes the second outcome reachable — the transform can be unavailable for the
data actually carried, and the failure it reports is not in general an
attribute-lookup failure at all.

When none of those branches applies, the outcome is **precisely** the object's
ordinary attribute-access result for that same name — its value if the ordinary
protocol produces one, or otherwise the very failure the ordinary protocol
raises, propagated verbatim. The fallback hook does not substitute or
re-synthesize a failure of its own; in particular it does not replace a genuine
attribute-access failure with one it manufactures from the originally requested
name. Whatever name the ordinary lookup reports in its failure is the name the
hook reports.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Unchanged dependency callees the resolver uses, declared as opaque signatures
-- (the proof needs no property axiom about either — the contract is stated
-- directly over them and discharged by case analysis):
--
-- * `handledCase self attr` : the combined outcome of the domain-specific
--   resolution branches — `some r` when one of them applies, `r` being that
--   branch's own outcome (a value, or the failure evaluating it raises), and
--   `none` when none of them applies.
-- * `ordinaryLookup self attr` : the object's ordinary attribute-access result
--   for the name — a value, or the genuine failure the access protocol raises.

/-- A failure observed at the attribute-access boundary.

* `missing` — the attribute name the failure reports as missing; the empty
  string for failures that report no attribute name at all.
* `kind` — the class of failure observed. An attribute-lookup failure is only
  one of the possibilities: interpreting a name as a transform target can fail
  instead with a conversion, unit or type failure, and a value the ordinary
  protocol computes on demand can fail in the same open-ended way. It defaults
  to the attribute-lookup class, which is the only class the manufactured
  no-such-attribute report can carry. -/
structure AttrError where
  missing : String
  kind : String := "AttributeError"
deriving DecidableEq, Repr, Inhabited

/-- The object whose attribute is being resolved. -/
opaque CoordObj : Type

/-- A resolved attribute value. -/
opaque AttrValue : Type

/-- Combined outcome of the domain-specific resolution branches: `some r` when one
of them applies to the requested name — `r` being that branch's own outcome, the
value it resolves to (`Except.ok`) or the failure evaluating it raises
(`Except.error`) — and `none` when none of them applies and control falls through
to the fallback. -/
opaque handledCase : CoordObj → String → Option (Except AttrError AttrValue)

/-- The object's ordinary attribute-access result for the requested name: a value,
or the genuine failure the access protocol raises (whose reported missing name need
not equal the requested name — e.g. when accessing the name runs user code that
itself accesses some other, genuinely-missing name). -/
opaque ordinaryLookup : CoordObj → String → Except AttrError AttrValue
-- axioms-end

-- pure-start
-- (no additional pure helpers required)
-- pure-end

-- post-conditions-start
/-- The fallback attribute resolver's contract:

* if a domain-specific branch applies (`handledCase = some r`), the result is
  that branch's own outcome `r`, surfaced unchanged — the value it resolved, or
  the failure evaluating it raised, neither of them replaced by anything else;
* otherwise the result is *exactly* the object's ordinary attribute-access
  outcome for the name — value or failure, propagated verbatim with no
  substitution. -/
def problem_spec_resolveAttr (self : CoordObj) (attr : String)
    (result : Except AttrError AttrValue) : Prop :=
  (∀ r, handledCase self attr = some r → result = r) ∧
  (handledCase self attr = none → result = ordinaryLookup self attr)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the domain-specific resolution branches are
-- unchanged — whichever applies still surfaces its own outcome, value or raised
-- failure alike — but when NONE of them applies, instead of consulting the
-- object's ordinary attribute-access protocol the hook FABRICATES an
-- attribute-lookup failure keyed to the originally requested name. This discards
-- the genuine failure the ordinary protocol would raise (which may report a
-- different, genuinely-missing name), so on the `none` branch the result is
-- always `Except.error { missing := attr }` regardless of the real outcome.
def implementation_resolveAttr (self : CoordObj) (attr : String) :
    Except AttrError AttrValue := Id.run do
  if let some r := handledCase self attr then
    return r
  return Except.error { missing := attr }
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl. On the
-- `none` branch the spec demands `result = ordinaryLookup self attr`, but the
-- buggy impl returns the fabricated `Except.error { missing := attr }`, which is
-- not in general equal to the ordinary-lookup outcome — the discriminating clause.
theorem correct_resolveAttr :
    ∀ (self : CoordObj) (attr : String),
      problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
  intro self attr
  unfold problem_spec_resolveAttr implementation_resolveAttr
  cases h : handledCase self attr with
  | none =>
    refine ⟨?_, ?_⟩
    · intro r hr; exact Option.noConfusion hr
    · intro _; rfl
  | some r =>
    refine ⟨?_, ?_⟩
    · intro r' hr'; exact Option.some_inj.mp hr'
    · intro hc; exact Option.noConfusion hc
-- proof-end
