import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. Every
   unchanged sub-computation is modeled as a FREE INPUT, owed no contract because
   the behaviour holds for every value it could take (directive 7): the equality
   of all the OTHER observable fields (`otherEqual`), the base rendering a
   constraint already produces (`base`), the standard value formatter's rendering
   of a single code value (`shown`), the pre-existing serialized bindings
   (`base`), and the validity verdict of an instance against a constraint
   (`isValid`). The one piece of behaviour this bundle pins — how an optional
   error code is surfaced in each observable projection of a constraint — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A violation error code: a short machine string, or absent (`none`). -/
abbrev ErrCode := Option (List Char)

/- The error code a constraint effectively records: the supplied code when one
   is given, and absent otherwise (the absent default). -/
def recordedCode (supplied : ErrCode) : ErrCode := supplied

/- The serialized keyword bindings of a constraint: the bindings already present
   gain an explicit error-code entry exactly when an error code is set, bound to
   the standard key. The pre-existing bindings (`base`) pass through unchanged. -/
def withCodeKwarg (base : List (String × List Char)) (code : ErrCode) :
    List (String × List Char) :=
  match code with
  | none   => base
  | some c => base ++ [("violation_error_code", c)]

/- Whether two constraints are equal: they agree on all other observable fields
   (`otherEqual`) AND carry the same error code. -/
def constraintEq (otherEqual : Bool) (codeA codeB : ErrCode) : Bool :=
  otherEqual && (codeA == codeB)

/- The textual form of a constraint: the base rendering (`base`) extended with an
   error-code fragment exactly when an error code is set. `shown` is the rendering
   of the code value produced by the standard value formatter (an unchanged
   formatting step), appended after the key fragment. -/
def renderedWithCode (base : List Char) (code : ErrCode) (shown : List Char) :
    List Char :=
  match code with
  | none   => base
  | some _ => base ++ " violation_error_code=".toList ++ shown

/- The outcome of checking one instance against a constraint, on the branch that
   reports a violation through the constraint's own message: acceptance
   (`isValid`) carries nothing; a violation carries the constraint's error code,
   so a caller observes that exact code on the reported error. -/
def checkResult (isValid : Bool) (code : ErrCode) : Except ErrCode Unit :=
  if isValid then Except.ok () else Except.error code
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record the error code carried by a constraint from the optionally-supplied
   value. `supplied` is read-only (directive 5). Desired behaviour: the recorded
   code is the supplied one when present and absent otherwise. -/
method recordErrorCode (supplied : ErrCode) return (out : ErrCode)
  ensures out = recordedCode supplied
  do
    -- impl-start
    let mut out : ErrCode := none
    if supplied ≠ none then
      out := supplied
    return out
    -- impl-end

prove_correct recordErrorCode by
  loom_solve <;> simp_all [recordedCode]

/- Produce the serialized keyword bindings of a constraint. `base` (the bindings
   already present) and `code` are read-only (directive 5). Desired behaviour: an
   explicit error-code binding is added exactly when an error code is set; the
   pre-existing bindings are preserved unchanged. -/
method serializeWithCode (base : List (String × List Char)) (code : ErrCode)
    return (out : List (String × List Char))
  ensures out = withCodeKwarg base code
  do
    -- impl-start
    let out := match code with
      | none   => base
      | some c => base ++ [("violation_error_code", c)]
    return out
    -- impl-end

prove_correct serializeWithCode by
  loom_solve <;> simp_all [withCodeKwarg]

/- Decide whether two constraints are equal. `otherEqual` (whether all other
   observable fields agree) and the two codes are read-only (directive 5).
   Desired behaviour: equality holds exactly when the other fields agree AND the
   error codes coincide, so two constraints differing only in error code are
   distinguished. -/
method constraintsEqual (otherEqual : Bool) (codeA : ErrCode) (codeB : ErrCode) return (out : Bool)
  ensures out = constraintEq otherEqual codeA codeB
  do
    -- impl-start
    let out := otherEqual && (codeA == codeB)
    return out
    -- impl-end

prove_correct constraintsEqual by
  loom_solve <;> simp_all [constraintEq]

/- Produce the textual form of a constraint. `base` (the base rendering), `code`,
   and `shown` (the value formatter's rendering of the code) are read-only
   (directive 5). Desired behaviour: the error-code fragment is appended exactly
   when an error code is set, leaving the base rendering otherwise untouched. -/
method renderConstraint (base : List Char) (code : ErrCode) (shown : List Char)
    return (out : List Char)
  ensures out = renderedWithCode base code shown
  do
    -- impl-start
    -- Pre-image skeleton: the textual form is the base rendering only; no
    -- error-code fragment is ever appended.
    let out := base
    return out
    -- impl-end

prove_correct renderConstraint by
  loom_solve <;> simp_all [renderedWithCode]

/- Check one instance against a constraint on the branch that reports a violation
   through the constraint's own message. `isValid` (the instance's validity
   verdict) and `code` are read-only (directive 5). Desired behaviour: a valid
   instance is accepted with no report; a violation is reported carrying the
   constraint's error code, so the reported error exposes that exact code. -/
method validateWithCode (isValid : Bool) (code : ErrCode) return (out : Except ErrCode Unit)
  ensures out = checkResult isValid code
  ensures isValid = false → out = Except.error code
  ensures isValid = true → out = Except.ok ()
  do
    -- impl-start
    let out : Except ErrCode Unit :=
      if isValid then Except.ok () else Except.error code
    return out
    -- impl-end

prove_correct validateWithCode by
  loom_solve <;> simp_all [checkResult]
