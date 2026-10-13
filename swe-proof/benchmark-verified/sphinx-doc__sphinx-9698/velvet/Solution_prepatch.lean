import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The index-entry label is built entirely from the
--  inputs — a pure per-character string computation modeled in full below.
--  Nothing is delegated to an unchanged callee, so there is no `axiom` and no
--  A-reference. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Which kind of member an index entry is being produced for. A documented
   member can be presented as a class-level member, an instance attribute
   exposed through a getter, a class-shared member, or a plain bound member.
   These four are mutually exclusive here: the kind is the single category the
   member is finally classified under (the caller resolves any overlap by a
   settled precedence before this point — see mapping.md §1). -/
inductive MethodKind where
  | classMethod
  | propertyKind
  | staticMethod
  | instanceMethod
  deriving DecidableEq, Inhabited

/- Split a dotted qualified name at its LAST separator '.', mirroring a
   right-anchored single split. `none` when the name carries no separator at all
   (a bare, unqualified name); otherwise `some (owner, member)` where `member` is
   the trailing component after the final '.' and `owner` is everything before
   it. Front-recursive so each step exposes one leading character: if the tail
   already contains a separator the split lives there and the head joins the
   owner; only when the tail has none does a head '.' become the final
   separator. -/
def rsplitDot : List Char → Option (List Char × List Char)
  | []      => none
  | c :: cs =>
    match rsplitDot cs with
    | some (owner, member) => some (c :: owner, member)
    | none                 => if c = '.' then some ([], cs) else none

/- The qualified owner actually shown in the label: when a module name is present
   and module names are configured to be shown, the owner is prefixed with that
   module name and a separator; otherwise the owner stands alone. -/
def shownOwner (modname owner : List Char) (addModuleNames : Bool) : List Char :=
  if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner

/- The index-entry label for a documented member.

   When the name is qualified (it has an owner and a trailing member component),
   the label names the member and parenthesizes the owner with a category word.
   For a class-level, class-shared, or plain bound member the member is shown as
   a CALL — its name followed by an empty call marker `()`. For a member exposed
   as an attribute through a getter, the member is shown WITHOUT that call marker
   — it is read as a value, not invoked — so only its bare name precedes the
   parenthesized category. This is the one behaviour the issue turns on: that
   attribute-style category, and only it, drops the call marker.

   When the name is unqualified (no owner component), the label is the name shown
   as a call, optionally annotated with the module it lives in. -/
def indexText
    (name modname : List Char) (addModuleNames : Bool) (kind : MethodKind) : List Char :=
  match rsplitDot name with
  | some (owner, member) =>
      let shown := shownOwner modname owner addModuleNames
      match kind with
      | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
      | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
      | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
      | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
  | none =>
      if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
      else name ++ "()".toList

/- Single-step unfold so `loom_solve` can discharge the postcondition by reducing
   the impl expression to the spec. -/
@[grind] lemma indexText_def
    (name modname : List Char) (addModuleNames : Bool) (kind : MethodKind) :
    indexText name modname addModuleNames kind =
      (match rsplitDot name with
       | some (owner, member) =>
           let shown := shownOwner modname owner addModuleNames
           match kind with
           | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
           | .propertyKind   => member ++ " (".toList   ++ shown ++ " property)".toList
           | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
           | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
       | none =>
           if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
           else name ++ "()".toList) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the index-entry label for a documented member.

   `name` is the member's qualified name; `modname` is the module it belongs to
   (empty when none applies); `addModuleNames` says whether the module name is
   shown as a prefix; `kind` is the resolved category of the member. All four are
   read-only — none is declared `mut` — and none is altered (directive 5).

   Desired behaviour: a qualified member is labelled by its trailing component and
   its parenthesized owner-plus-category. A member exposed as an attribute through
   a getter is read as a value, so its label carries NO empty call marker `()`
   after the name; every other category is invoked and so keeps that marker. An
   unqualified name is labelled as a call, optionally annotated with its module.
   The result is the fresh label string. -/
method indexEntryText
    (name : List Char) (modname : List Char) (addModuleNames : Bool) (kind : MethodKind)
    return (out : List Char)
  ensures out = indexText name modname addModuleNames kind
  do
    -- impl-start
    let out : List Char :=
      match rsplitDot name with
      | some (owner, member) =>
          -- Prefix the owner with the module name when one is present and module
          -- names are configured to be shown.
          let shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner
          match kind with
          | .classMethod    => member ++ "() (".toList ++ shown ++ " class method)".toList
          -- Pre-image skeleton: the attribute-style member is ALSO emitted with
          -- the empty call marker `()`, exactly like the invoked categories. The
          -- frozen spec demands no marker for this category, so prove_correct
          -- MUST fail (G-DIFF).
          | .propertyKind   => member ++ "() (".toList  ++ shown ++ " property)".toList
          | .staticMethod   => member ++ "() (".toList ++ shown ++ " static method)".toList
          | .instanceMethod => member ++ "() (".toList ++ shown ++ " method)".toList
      | none =>
          if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList
          else name ++ "()".toList
    return out
    -- impl-end

prove_correct indexEntryText by
  loom_solve
  simp_all [indexText, shownOwner]
