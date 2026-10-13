import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee. The
   behaviour under spec is the construction of a textual reference to one member
   of an enumeration, together with the single import that reference needs. It
   is built entirely from concrete string operations over the inputs (the
   defining module name, the enumeration type name, and the member's symbolic
   name) and is modeled DEEPLY in the `pure` region below. The decision of WHICH
   value-rendering routine handles a given value, and the surrounding
   import-collection bookkeeping, are unchanged control flow reached identically
   and are not modeled here — only the reference/import construction is. See
   mapping.md §3 and refinement.md §C. -/
-- axioms-end

-- pure-start
/- A member's symbolic name, rendered as a single quoted token: the name
   surrounded by apostrophes (the name `GOOD` renders as `'GOOD'`). This is the
   member's exact canonical textual representation ONLY on the identifier
   domain (letters, digits, underscore — never a quote, backslash, or other
   special character); the operation below REQUIRES that domain of its
   `memberName` input, so the spec never asserts this rendering outside it. -/
def quotedName (name : List Char) : List Char := ['\''] ++ name ++ ['\'']

/- The identifier alphabet for a member's symbolic name: ASCII letters, ASCII
   digits, and the underscore. On names drawn from this alphabet the canonical
   textual rendering of the name is exactly `quotedName` (single quotes, no
   escaping). -/
def isIdentChar (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_'

/- The textual reference to one member of an enumeration: the qualified
   enumeration type — its defining `module` and type `className`, joined by a
   dot — followed by the member's quoted symbolic name in SUBSCRIPT form, e.g.

       module.Class['NAME']

   Built only from the module name, the type name, and the member's symbolic
   name; the member's stored payload plays no part in the reference. Keying the
   reference on the stable symbolic name (rather than the stored payload) is the
   point: the reference stays valid even when the payload is a value that may be
   rendered differently elsewhere or over time. -/
def memberReference (module className memberName : List Char) : List Char :=
  module ++ ['.'] ++ className ++ ['['] ++ quotedName memberName ++ [']']

/- The set of imports the reference needs: exactly the import of the
   enumeration's own defining module, and nothing else. The reference names no
   symbol from the member's payload, so it pulls in no payload imports. -/
def referenceImports (module : List Char) : List (List Char) :=
  ["import ".toList ++ module]

@[grind] lemma memberReference_def (module className memberName : List Char) :
    memberReference module className memberName
      = module ++ ['.'] ++ className ++ ['['] ++ quotedName memberName ++ [']'] := rfl

@[grind] lemma referenceImports_def (module : List Char) :
    referenceImports module = ["import ".toList ++ module] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the source-code reference for one member of an enumeration, used when
   that member is emitted into generated source. The reference identifies the
   member by its qualified type and its stable symbolic name.

   Inputs: `module` and `className` name the enumeration's defining module and
   type; `memberName` is the member's symbolic name; `payloadText` and
   `payloadImports` describe the member's stored payload as it would be rendered
   on its own. `payloadText` and `payloadImports` are read-only and MUST NOT
   reach the result: the reference and its imports are pinned to the module,
   type, and symbolic name alone (directive 5 — the payload is a supplied value
   that must not leak into the output). Any implementation that lets the payload
   determine the reference text or the import set fails to verify.

   Domain: the member's symbolic name is REQUIRED to be drawn from the
   identifier alphabet (letters, digits, underscore). Members declared in an
   enumeration's class body always satisfy this — their names are attribute
   names — and on this alphabet the quoted rendering `quotedName` is exactly
   the name's canonical textual representation (single quotes, no escaping).
   The spec makes no claim for names outside this alphabet (e.g. names carrying
   a quote or a backslash, constructible only through the functional
   enumeration API), whose canonical rendering may switch quote style or insert
   escapes.

   Desired behaviour: the reference renders the member by its symbolic name in
   subscript form (`module.Class['NAME']`), and the only import it requires is
   the import of the enumeration's defining module. -/
method referenceEnumMember
    (module : List Char) (className : List Char) (memberName : List Char)
    (payloadText : List Char) (payloadImports : List (List Char))
    return (out : (List Char) × (List (List Char)))
  require ∀ c ∈ memberName, isIdentChar c
  ensures out.1 = memberReference module className memberName
  ensures out.2 = referenceImports module
  ensures out = (memberReference module className memberName, referenceImports module)
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: the reference is keyed on the member's stored
    -- PAYLOAD as rendered on its own (call form `module.Class(payloadText)`), and
    -- the payload's own imports are merged in. The frozen spec pins the result to
    -- the symbolic-name subscript form with only the module import, so
    -- prove_correct MUST fail.
    let refString : List Char :=
      module ++ ['.'] ++ className ++ ['('] ++ payloadText ++ [')']
    let imports : List (List Char) := ("import ".toList ++ module) :: payloadImports
    return (refString, imports)
    -- impl-end

prove_correct referenceEnumMember by
  loom_solve
  all_goals simp_all [memberReference, quotedName, referenceImports]
