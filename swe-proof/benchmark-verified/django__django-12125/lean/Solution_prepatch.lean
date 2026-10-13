import Mathlib
-- imports-end

/-!
Producing the source-code reference string for a class/type value.

A serializer turns a class value into the pair `(reference, imports)` that
regenerated source can use to name that class again:

  * `reference` — the textual expression that re-denotes the class;
  * `imports`  — the set of import statements that expression needs.

The desired behavior, by the kind of class:

  * the framework's base model class is emitted as the constant literal
    `"models.Model"` with no import;
  * the null/`None` type is emitted as the constant literal `"type(None)"` with no
    import;
  * a class living in the language's built-in namespace is emitted by its
    unqualified leaf name alone, with no import;
  * any other class is emitted as its home module joined (with a dot) to the
    class's FULLY-QUALIFIED in-module path — the path that walks through every
    enclosing scope down to the class — together with the single import of that
    home module.

The last clause is the one that matters for a class declared inside another
class: the reference must spell the complete path through the enclosing
class(es), not merely the leaf name. Using the leaf name alone would denote a
sibling top-level class that does not exist, so the qualified path is required.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two
-- constant special cases, the built-in-namespace test, and the assembly of the
-- reference string from the home module and the class's leaf / fully-qualified
-- names are all modeled structurally over the class descriptor; no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A class/type value, restricted to the attributes the serializer observes.

* `isModelBase` — the value IS the framework's base model class (special case);
* `isNoneType`  — the value IS the null/`None` type (special case);
* `hasModule`   — a home module is observable for the value;
* `module`      — the home module's dotted name (e.g. `"app.models"`);
* `shortName`   — the class's unqualified leaf name (e.g. `"Inner"`);
* `fullName`    — the class's fully-qualified in-module path, threading through
  every enclosing scope (e.g. `"Outer.Inner"`; equal to `shortName` for a class
  declared at module top level). -/
structure TypeRef where
  isModelBase : Bool
  isNoneType : Bool
  hasModule : Bool
  module : String
  shortName : String
  fullName : String

/-- The name of the language's built-in namespace. -/
def builtinsModule : String := "builtins"
-- pure-end

-- post-conditions-start
/-- The serialized `(reference, imports)` for a class value, pinned for every
descriptor. The special cases are tried first (base model class, then null
type); a built-in-namespace class yields its leaf name with no import; any other
class yields `module ++ "." ++ fullName` with the single import of its home
module. A class with no observable home module produces no result (`none`). -/
def problem_spec_serializeType (v : TypeRef)
    (result : Option (String × List String)) : Prop :=
  result =
    (if v.isModelBase then some ("models.Model", [])
     else if v.isNoneType then some ("type(None)", [])
     else if v.hasModule then
       (if v.module = builtinsModule then some (v.shortName, [])
        else some (v.module ++ "." ++ v.fullName, ["import " ++ v.module]))
     else none)
-- post-conditions-end

-- impl-start
def implementation_serializeType (v : TypeRef) :
    Option (String × List String) := Id.run do
  -- The constant special cases, checked in order before anything else.
  if v.isModelBase then
    return some ("models.Model", [])
  if v.isNoneType then
    return some ("type(None)", [])
  -- A class with an observable home module.
  if v.hasModule then
    if v.module = builtinsModule then
      -- Built-in namespace: the leaf name alone, no import.
      return some (v.shortName, [])
    else
      -- Any other module: home module joined to the class's fully-qualified
      -- module, plus the import of that home module.
      return some (v.module ++ "." ++ v.shortName, ["import " ++ v.module])
  return none
-- impl-end

-- proof-start
theorem correct_serializeType :
    ∀ (v : TypeRef),
      problem_spec_serializeType v (implementation_serializeType v) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
