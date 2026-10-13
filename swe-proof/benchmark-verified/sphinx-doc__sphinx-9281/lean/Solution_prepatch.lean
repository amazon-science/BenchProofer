import Mathlib
-- imports-end

/-!
Rendering a value to the human-readable string used to display it in generated
documentation (for example, to show a parameter's default value in a signature).

Values come in several kinds. Some container kinds — mappings, sets, frozen
sets — have a dedicated rendering of their own, which is assembled from the
displays of the values they contain; every other kind of value has a
general-purpose rendering. What is pinned here is the display of a **plain
enumeration member**: an enumeration member that is not itself a value of one
of those container kinds. Such a member has a class name and a member name, and
its desired display is its qualified name, written `Class.Member`. (An
enumeration member that is ALSO a value of one of those container kinds is
displayed by that container kind's own rendering instead — it is not given the
dedicated treatment.)

So the result is determined kind-by-kind:

  * for a plain enumeration member with class name `C` and member name `M`, the
    display is exactly the text `C` followed by `.` followed by `M`;
  * for a value of any other kind — including a value of one of the container
    kinds, whether or not it is also an enumeration member — the display is the
    one the display routine gives that value.
-/

-- axioms-start
/-- The display the routine gives a value that is NOT given the dedicated
plain-enumeration-member treatment: the dedicated container renderings — each
assembled from the displays of the values that container holds, whatever those
displays are — together with the general-purpose rendering. Only its result
enters the behaviour modeled here, and the modeled behaviour assumes no
property of it, so it is declared as an opaque carrier with no asserted
property. (It is defined on every kind of value, including plain enumeration
members: for such a member it is the general-purpose rendering — the display
that member receives when the dedicated treatment described in the spec is not
applied to it.) -/
opaque legacyDescription : PyValue → String
-- axioms-end

-- pure-start
/-- A value to be displayed, modeled at the granularity the top-level rendering
decision distinguishes: either a **plain enumeration member** (an enumeration
member that is not itself a value of one of the container kinds that have their
own rendering; it carries its class name and member name) or **any other kind
of value** (an opaque identity tag standing for a distinct value:
non-enumeration values, and also enumeration members that are themselves
containers of one of those kinds and so are displayed by that container
rendering). -/
inductive PyValue where
  | enumMember (className : String) (memberName : String)
  | other (tag : Nat)
deriving Repr
-- pure-end

-- post-conditions-start
/-- The display string, pinned for every kind of value.

A plain enumeration member is displayed as its qualified name — its class
name, a dot, then its member name. A value of any other kind is displayed
exactly as the display routine renders that value. -/
def problem_spec_describeValue (obj : PyValue) (result : String) : Prop :=
  match obj with
  | .enumMember className memberName => result = className ++ "." ++ memberName
  | .other _ => result = legacyDescription obj
-- post-conditions-end

-- impl-start
def implementation_describeValue (obj : PyValue) : String := Id.run do
  -- Pre-patch behaviour: a value of any kind is handed straight to the
  -- existing display routine; plain enumeration members receive no dedicated
  -- treatment and so are rendered like any other value.
  return legacyDescription obj
-- impl-end

-- proof-start
theorem correct_describeValue :
    ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
  intro obj
  unfold problem_spec_describeValue implementation_describeValue
  cases obj <;> rfl
-- proof-end
