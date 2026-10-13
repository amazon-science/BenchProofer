import Mathlib
-- imports-end

/-!
Deciding whether a documented private / special / init member of a class,
exception, or module should be *included* in generated API documentation.

A member is described by its declaring kind (`what`: "module", "class",
"exception", "method", …), its `name` (e.g. `__init__`, `__repr__`,
`_helper`), and the member object itself. The member object carries:

* whether it has a docstring,
* its qualified name (`Owner.member`), from which the owning class's short
  name is taken as everything before the final dot,
* a table mapping class short-names visible in the object's defining scope to
  those classes (each class knows the attribute names it directly declares),
* and, when the object is a wrapper produced by decoration, a link to the
  object it wraps. Following these links to the end yields the *underlying*
  object — the original, undecorated member, whose defining scope is the one
  that actually declares the owning class.

Three independent toggles control inclusion: one each for init members,
other special (`__dunder__`) members, and private (`_name`) members.

A member is included exactly when it has a docstring, is not the weak-reference
slot, belongs to a documentable kind, is genuinely owned by the resolved class
(or sits directly in a module), and its category toggle is on. The owning class
must be resolved from the underlying object's defining scope, so that a
*decorated* member — whose wrapper is defined in a different scope — is still
recognized as owned by its class. "Included" is reported as `some false`
("do not skip"); every other case defers with `none`. The implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No dependency callee requires a consumed contract. Resolving an object to the
-- underlying object it wraps is modeled DEEPLY here (`coreObject`, following the
-- wrapper links to the end), so it is validated against the real operation
-- rather than axiomatized.
-- axioms-end

-- pure-start
/-- A class, modeled by the attribute names it directly declares (its
`__dict__` keys). -/
structure ClsInfo where
  attrs : List String
deriving Repr

/-- A member object. `inner` links a decoration wrapper to the object it wraps
(`none` once the underlying object is reached). `globalsMap` maps class
short-names visible in this object's defining scope to those classes. -/
inductive PyObj where
  | node (qualname : String) (hasDoc : Bool)
         (globalsMap : List (String × ClsInfo)) (inner : Option PyObj)

namespace PyObj

def qualname : PyObj → String
  | node q _ _ _ => q
def hasDoc : PyObj → Bool
  | node _ d _ _ => d
def globalsMap : PyObj → List (String × ClsInfo)
  | node _ _ g _ => g
def inner : PyObj → Option PyObj
  | node _ _ _ i => i

/-- The underlying object: follow the wrapper links to the end. -/
def coreObject : PyObj → PyObj
  | node q d g none => node q d g none
  | node _ _ _ (some o) => coreObject o

end PyObj

/-- The three inclusion toggles. -/
structure IncludeFlags where
  incInit : Bool
  incSpecial : Bool
  incPrivate : Bool

/-- The owning class's short-name: everything before the final dot of the
qualified name, but only when that prefix is itself a single dotless segment
(`Owner.member`). `none` otherwise (no dot, or a nested `A.B.member`). -/
def clsPathSingle (qualname : String) : Option String :=
  match qualname.splitOn "." with
  | [c, _] => some c
  | _ => none

def isInitName (name : String) : Bool := name == "__init__"

def isSpecialName (name : String) : Bool :=
  !(isInitName name) && name.startsWith "__" && name.endsWith "__"

def isPrivateName (name : String) : Bool :=
  !(isInitName name) && !(isSpecialName name) && name.startsWith "_"

/-- The resolved class (from the underlying object's scope) genuinely owns the
member: the class exists in scope and `name` is one of its directly-declared
attributes. Only meaningful for class / exception members. -/
def clsIsOwner (what name : String) (obj : PyObj) : Bool :=
  if what == "class" || what == "exception" then
    match clsPathSingle obj.qualname with
    | some cp =>
      match (obj.coreObject.globalsMap).lookup cp with
      | some cls => cls.attrs.contains name
      | none => false
    | none => false
  else
    false

/-- The full inclusion predicate over the inputs. -/
def shouldInclude (cfg : IncludeFlags) (what name : String) (obj : PyObj) : Bool :=
  name != "__weakref__" && obj.hasDoc &&
  (what == "module" || what == "class" || what == "exception") &&
  (what == "module" || clsIsOwner what name obj) &&
  ((isSpecialName name && cfg.incSpecial) ||
   (isPrivateName name && cfg.incPrivate) ||
   (isInitName name && cfg.incInit))
-- pure-end

-- post-conditions-start
/-- The result is `some false` ("do not skip — include it") exactly when the
member should be included, and `none` (defer) otherwise. In particular the
result is never `some true`. -/
def problem_spec_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) (result : Option Bool) : Prop :=
  (shouldInclude cfg what name obj = true  → result = some false) ∧
  (shouldInclude cfg what name obj = false → result = none)
-- post-conditions-end

-- impl-start
def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) : Option Bool := Id.run do
  let hasDoc := obj.hasDoc
  let isMember := what == "module" || what == "class" || what == "exception"
  if name != "__weakref__" && hasDoc && isMember then
    let mut clsOwner := false
    if what == "class" || what == "exception" then
      match clsPathSingle obj.qualname with
      | some clsPath =>
        -- resolve the owning class via the UNDERLYING object's scope
        match (obj.coreObject.globalsMap).lookup clsPath with
        | some cls => clsOwner := cls.attrs.contains name
        | none => clsOwner := false
      | none => clsOwner := false
    if what == "module" || clsOwner then
      let isInit := name == "__init__"
      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
      let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
         (isInit && cfg.incInit) then
        return some false
  return none
-- impl-end


-- proof-start
-- The boolean value the implementation computes into its local `clsOwner`
-- at the point of the `if what == "module" || clsOwner` test: mirrors the
-- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
-- neither "class" nor "exception" (the inner `if` is skipped).
def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
  if what == "class" || what == "exception" then
    match clsPathSingle obj.qualname with
    | some clsPath =>
      match (obj.coreObject.globalsMap).lookup clsPath with
      | some cls => cls.attrs.contains name
      | none => false
    | none => false
  else
    false

-- OwnershipBridge: the impl's locally-computed ownership boolean equals the
-- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
theorem clsOwner_eq (what name : String) (obj : PyObj) :
    ImplClsOwner what name obj = clsIsOwner what name obj := rfl

-- Directions: the two implications of `problem_spec_memberInclusion`, proved
-- directly by matching the impl's control-flow branches to `shouldInclude`'s
-- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
    shouldInclude cfg what name obj = true →
      implementation_memberInclusion cfg what name obj = some false := by
  intro h
  unfold shouldInclude at h
  unfold implementation_memberInclusion
  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
    isSpecialName, isPrivateName, isInitName] at h
  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
  grind

theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
    shouldInclude cfg what name obj = false →
      implementation_memberInclusion cfg what name obj = none := by
  intro h
  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
  simp only [implementation_memberInclusion, Id.run, bind, pure]
  repeat' split
  all_goals (first | rfl | (exfalso; grind))

theorem correct_memberInclusion :
    ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
      problem_spec_memberInclusion cfg what name obj
        (implementation_memberInclusion cfg what name obj) := by
  intro cfg what name obj
  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩

-- proof-end
