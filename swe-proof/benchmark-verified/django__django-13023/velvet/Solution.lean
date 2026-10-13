import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged sub-steps the operation delegates to — the null/float fast paths
   and the attempt to interpret an arbitrary input as a fixed-precision decimal —
   are modeled as FREE inputs of the method (`isNone`, `isFloat`, `floatRes`,
   `conv`; see the signature). The postconditions hold for EVERY value of those,
   so they are owed no contract: they are strictly weaker than any concrete
   implementation of the delegated steps (directive 7). The behaviour this bundle
   actually pins — how the OUTCOME of a failed interpretation is reported — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque carrier for a successfully produced fixed-precision decimal value.
   Nothing about its internal content is constrained: the operation under
   specification never inspects it, it only decides whether to surface it or to
   report a failure. -/
structure DecimalVal where
  payload : Int
  deriving DecidableEq, Inhabited

/- The kinds of failure the interpretation step can report. An interpretation
   attempt either succeeds with a value or fails reporting one of these. The
   first three are the recoverable ways an arbitrary object can fail to be read
   as a fixed-precision decimal — an invalid numeric operation, an unsupported
   operand type, or an out-of-domain value; `other` stands for any failure
   outside that recoverable family. -/
inductive ExcKind where
  | invalidOperation
  | typeError
  | valueError
  | other
  deriving DecidableEq, Inhabited

/- The outcome of attempting to interpret the input as a decimal: either a
   produced value, or a reported failure of some kind. This is the (free,
   unconstrained) result of the unchanged interpretation step. -/
inductive ConvResult where
  | converted (d : DecimalVal)
  | raised (e : ExcKind)
  deriving DecidableEq, Inhabited

/- The observable outcome of the whole operation:
   * `ret d`         — a fixed-precision decimal value is returned;
   * `retNone`       — the null fast-path returns the input unchanged;
   * `validationError` — the field's invalid-value error is reported;
   * `propagated e`  — a raw failure of kind `e` escapes the operation uncaught. -/
inductive PyResult where
  | ret (d : DecimalVal)
  | retNone
  | validationError
  | propagated (e : ExcKind)
  deriving DecidableEq, Inhabited

/- Which failure kinds are recoverable, i.e. must be normalised to the field's
   invalid-value error instead of being allowed to escape. Every way an arbitrary
   object can fail to be read as a fixed-precision decimal is recoverable; only a
   failure outside that family (`other`) is left to propagate. This is the heart
   of the desired behaviour: NO recoverable interpretation failure may surface as
   a raw exception to the caller. -/
def isRecoverable : ExcKind → Bool
  | .invalidOperation => true
  | .typeError        => true
  | .valueError       => true
  | .other            => false

/- The deep model of the operation's outcome from the (free) observations of its
   delegated steps. Null and float inputs take their fast paths; otherwise the
   interpretation attempt's outcome decides: a produced value is returned, a
   recoverable failure becomes the field's invalid-value error, and any other
   failure propagates. -/
def toDecimalResult (isNone isFloat : Bool) (floatRes : DecimalVal)
    (conv : ConvResult) : PyResult :=
  if isNone then PyResult.retNone
  else
    if isFloat then PyResult.ret floatRes
    else
      match conv with
      | ConvResult.converted d => PyResult.ret d
      | ConvResult.raised e =>
          if isRecoverable e then PyResult.validationError
          else PyResult.propagated e

@[grind] lemma isRecoverable_invalidOperation :
    isRecoverable ExcKind.invalidOperation = true := rfl
@[grind] lemma isRecoverable_typeError :
    isRecoverable ExcKind.typeError = true := rfl
@[grind] lemma isRecoverable_valueError :
    isRecoverable ExcKind.valueError = true := rfl
@[grind] lemma isRecoverable_other :
    isRecoverable ExcKind.other = false := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Interpret an arbitrary input as a fixed-precision decimal value. The delegated
   steps are read-only abstractions: `isNone` / `isFloat` flag the two fast paths,
   `floatRes` is the value the float fast path produces, and `conv` is the outcome
   of attempting to read a non-null, non-float input as a decimal — it either
   yields a value or reports a failure of some kind. Desired behaviour: a null
   input is returned unchanged; a float yields its converted value; for any other
   input the interpretation attempt's outcome decides — a produced value is
   returned, EVERY recoverable failure to interpret the input is reported as the
   field's invalid-value error (never escaping as a raw exception), and only a
   failure outside the recoverable family propagates. -/
method toDecimal (isNone : Bool) (isFloat : Bool) (floatRes : DecimalVal) (conv : ConvResult)
    return (out : PyResult)
  ensures out = toDecimalResult isNone isFloat floatRes conv
  ensures isNone = true → out = PyResult.retNone
  ensures (isNone = false ∧ isFloat = true) → out = PyResult.ret floatRes
  ensures ∀ d, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.converted d) →
    out = PyResult.ret d
  ensures ∀ e, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.raised e ∧
    isRecoverable e = true) → out = PyResult.validationError
  ensures ∀ e, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.raised e ∧
    isRecoverable e = false) → out = PyResult.propagated e
  do
    -- impl-start
    -- Null and float inputs take their unchanged fast paths. For any other input
    -- the interpretation attempt's outcome decides: a produced value is returned;
    -- a reported failure that is one of the recoverable interpretation failures
    -- becomes the field's invalid-value error; any other failure propagates.
    let result : PyResult :=
      if isNone then PyResult.retNone
      else
        if isFloat then PyResult.ret floatRes
        else
          match conv with
          | ConvResult.converted d => PyResult.ret d
          | ConvResult.raised e =>
              if isRecoverable e then PyResult.validationError
              else PyResult.propagated e
    return result
    -- impl-end

prove_correct toDecimal by
  loom_solve
  simp_all [toDecimalResult, isRecoverable]
