import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one unchanged callee this slice relies on — the
-- expression compiler that turns a single bound name into an evaluable form —
-- is modeled DEEPLY in the `pure` region (`compileName`) and validated == the
-- real callee by G-AX (an A-reference, mapping.md §3). The acceptance test
-- `matcher` is taken as a FREE INPUT, so the spec makes no behavioural claim
-- about it and holds for every value.
-- axioms-end

-- pure-start
/- The outcome of turning a single bound name into an evaluable form can fail:
   the compiler refuses names whose spelling coincides with one of the literal
   constants of the language, because such a spelling cannot denote a bound
   name. -/
inductive CompileErr where
  | reservedConstant
  deriving DecidableEq

/- The three name spellings the compiler treats as literal constants rather
   than bound names. A name with one of these exact spellings cannot be
   compiled as a bound-name reference. -/
def isReservedName (name : List Char) : Bool :=
  name = "True".toList || name = "False".toList || name = "None".toList

/- Deep model of the unchanged compiler callee (A-reference, mapping.md §3.1):
   compiling a bound-name reference succeeds for every spelling EXCEPT the
   reserved-constant spellings, for which it fails. Validated `compileName` ==
   the real compiler by axiom_check.py (G-AX); NOT consumed as an axiom. -/
def compileName (name : List Char) : Except CompileErr Unit :=
  if isReservedName name then Except.error .reservedConstant else Except.ok ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Evaluate a bare match-expression identifier against a matcher.

   A bare identifier is compiled into an evaluable form and then looked up
   through the matcher; the value of the expression is whether the matcher
   accepts that identifier. The desired behaviour is that EVERY admissible
   identifier evaluates successfully to the matcher's verdict on that exact
   identifier — including identifiers whose spelling coincides with a language
   literal constant (e.g. the three reserved-constant spellings), which must be
   evaluable just like any other identifier and must be matched on the
   identifier the user wrote, unchanged.

   `ident` and `matcher` are read-only (directive 5). -/
method evalBareIdent (ident : List Char) (matcher : List Char → Bool)
    return (out : Except CompileErr Bool)
  ensures out = Except.ok (matcher ident)
  do
    -- impl-start
    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
    -- is a character that can never begin a bound name the user could write),
    -- then look the original identifier up through the matcher.
    let identPrefix : List Char := ['$']
    let name : List Char := identPrefix ++ ident
    let compiled : Except CompileErr Unit := compileName name
    let key : List Char := name.drop identPrefix.length
    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
    return out
    -- impl-end

prove_correct evalBareIdent by
  loom_solve
  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
  have hok : compileName (['$'] ++ ident) = Except.ok () := by
    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
    unfold compileName; rw [h]; rfl
  rw [hok, hkey]; rfl
