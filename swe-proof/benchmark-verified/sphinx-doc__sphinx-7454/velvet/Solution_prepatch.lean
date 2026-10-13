import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Building a single cross-reference for a name in a
--  type annotation is a pure computation over the name text; the node
--  constructor and the surrounding annotation parser are collapsed into the
--  input name and the result record, and are owed no contract. There is no
--  `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- How a name appearing in a type annotation is to be resolved into a
   documentation link:
     * `classRef` — resolved as a class, the kind used for ordinary type names
                    such as `int`, `List`, or a user-defined class;
     * `valueRef` — resolved as a plain value/object, used for a name that
                    denotes a value rather than a class. -/
inductive RefKind where
  | classRef
  | valueRef
  deriving Inhabited, DecidableEq

/- A resolved cross-reference, reduced to the fields that determine how it links:
   the resolution kind, the documentation domain it resolves in, the target name
   it points at, and the text shown to the reader. -/
structure TypeReference where
  kind   : RefKind
  domain : List Char
  target : List Char
  label  : List Char
  deriving Inhabited, DecidableEq

/- The resolution kind a name should get: the literal name of the singleton
   value `None` denotes a value, so it is resolved as a plain value reference (so
   that it links to that value's documentation); every other name is treated as
   a class reference. -/
def desiredKind (name : List Char) : RefKind :=
  if name = "None".toList then .valueRef else .classRef
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the cross-reference for one name occurring in a type annotation. `name`
   is read-only (not `mut`): the reference is freshly constructed and the input
   name is echoed verbatim into both the target and the shown label (directive 5
   — the input frame is stated exactly in the postconditions). The domain is
   always the Python domain. The resolution kind is the only thing that varies
   with the name: the `None` singleton resolves as a value reference, every other
   name as a class reference, so that `None` links the same way other type names
   do. -/
method referenceForName (name : List Char) return (out : TypeReference)
  ensures out.domain = "py".toList
  ensures out.target = name
  ensures out.label = name
  ensures out.kind = desiredKind name
  ensures name = "None".toList → out.kind = .valueRef
  ensures name ≠ "None".toList → out.kind = .classRef
  ensures out.kind = .valueRef ↔ name = "None".toList
  do
    -- impl-start
    -- Pre-image skeleton: every name, including the `None` singleton, was given
    -- the same class reference kind — there was no special case distinguishing a
    -- value name from a class name. The frozen spec requires the `None` name to
    -- resolve as a value reference, so prove_correct MUST fail.
    let kind : RefKind := .classRef
    let result : TypeReference :=
      { kind   := kind,
        domain := "py".toList,
        target := name,
        label  := name }
    return result
    -- impl-end

prove_correct referenceForName by
  loom_solve
  simp_all [desiredKind]
