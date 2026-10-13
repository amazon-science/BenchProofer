import Mathlib
-- imports-end

/-!
Building the index-entry label for a documented class member.

When a member of a class is documented, a single index entry is registered for
it. The text of that entry is assembled from:

  * the member's fully-qualified dotted name (e.g. `Class.member`), from which the
    leading class part and the trailing member part are separated at the final
    dot;
  * the enclosing module name, which may be empty;
  * a flag selecting whether the module name is prepended to the class part;
  * and the *kind* of member it is — an ordinary method, a class method, a static
    method, or a value-like attribute exposed without a call.

The label distinguishes the kinds with a parenthesised qualifier naming the
class. For the call-like kinds (ordinary method, class method, static method) the
member name is shown with an empty argument list appended, reflecting that the
member is invoked. For the value-like kind, the member is referred to by its bare
name, with no argument list, because it is accessed rather than called.

When the dotted name has no separating dot, the class part cannot be formed, and
the label falls back to naming the member alone (with an empty argument list),
optionally qualified by the module it lives in.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dotted-name
-- separation, the optional module-name qualification, and the assembly of the
-- label are all modeled directly as string operations over the inputs; there is
-- no opaque callee whose contract the proof must assume.
-- axioms-end

-- pure-start
/-- Separate a dotted name at its FINAL dot, as a right split into two parts.
Returns `none` when the name contains no dot (no class part can be formed);
otherwise `some (before, after)` where `after` is the trailing segment and
`before` is everything preceding the final dot, rejoined with dots. -/
def rsplitLastDot (s : String) : Option (String × String) :=
  match (s.splitOn ".").reverse with
  | []        => none
  | [_]       => none
  | last :: rest => some (String.intercalate "." rest.reverse, last)
-- pure-end

-- post-conditions-start
/-- The index-entry label is fully pinned to the inputs in every case:

  * when the name has no separating dot, the label is the bare member name with an
    empty argument list, qualified by the module name when one is present;
  * when the name splits, the class part is the trailing-class component,
    optionally prefixed by the module name, and the label is one of four
    determined shapes selected by the member kind — the call-like kinds carry an empty
    argument list after the member name, the value-like kind does not.

Every branch determines the result, so no output component is left free. -/
def problem_spec_getIndexText (name modname : String)
    (isClassmethod isProperty isStaticmethod addModuleNames : Bool)
    (result : String) : Prop :=
  match rsplitLastDot name with
  | none =>
      (modname ≠ "" → result = name ++ "() (in module " ++ modname ++ ")") ∧
      (modname = "" → result = name ++ "()")
  | some (clsname0, methname) =>
      let clsname :=
        if addModuleNames && modname != "" then modname ++ "." ++ clsname0 else clsname0
      (isClassmethod = true →
          result = methname ++ "() (" ++ clsname ++ " class method)") ∧
      (isClassmethod = false → isProperty = true →
          result = methname ++ " (" ++ clsname ++ " property)") ∧
      (isClassmethod = false → isProperty = false → isStaticmethod = true →
          result = methname ++ "() (" ++ clsname ++ " static method)") ∧
      (isClassmethod = false → isProperty = false → isStaticmethod = false →
          result = methname ++ "() (" ++ clsname ++ " method)")
-- post-conditions-end

-- impl-start
def implementation_getIndexText (name modname : String)
    (isClassmethod isProperty isStaticmethod addModuleNames : Bool) : String := Id.run do
  match rsplitLastDot name with
  | none =>
    if modname != "" then
      return name ++ "() (in module " ++ modname ++ ")"
    else
      return name ++ "()"
  | some (clsname0, methname) =>
    let mut clsname := clsname0
    if addModuleNames && modname != "" then
      clsname := modname ++ "." ++ clsname0
    if isClassmethod then
      return methname ++ "() (" ++ clsname ++ " class method)"
    else if isProperty then
      return methname ++ "() (" ++ clsname ++ " property)"
    else if isStaticmethod then
      return methname ++ "() (" ++ clsname ++ " static method)"
    else
      return methname ++ "() (" ++ clsname ++ " method)"
-- impl-end

-- proof-start
theorem correct_getIndexText :
    ∀ (name modname : String)
      (isClassmethod isProperty isStaticmethod addModuleNames : Bool),
      problem_spec_getIndexText name modname
        isClassmethod isProperty isStaticmethod addModuleNames
        (implementation_getIndexText name modname
          isClassmethod isProperty isStaticmethod addModuleNames) := by
  sorry
-- proof-end
