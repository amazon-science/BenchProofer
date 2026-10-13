import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   sub-step that is not pinned here is the attempt to interpret the arbitrary
   right-hand operand as a value of this domain; that interpretation is an
   UNCHANGED callee whose three mutually-exclusive outcomes are the ONLY thing
   the desired behaviour reacts to. It is modeled as a FREE input
   (`InterpretOutcome`, see the method signature): the postconditions hold for
   EVERY value of it, so it is owed no contract — strictly weaker than any
   concrete interpreter (directive 7). The behaviour this bundle pins — how each
   outcome becomes a comparison verdict, and that a failed interpretation never
   escapes as an error — is modeled DEEPLY in the `pure` region. There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The outcome of attempting to interpret the arbitrary right-hand operand as a
   value of this domain, in the three mutually-exclusive shapes the comparison
   reacts to:
     * `uninterpretable` — the operand cannot be interpreted at all (the attempt
                           fails); e.g. it is absent/null, a bare number, or an
                           object of an unrelated type;
     * `sameKind name`   — the operand interprets to a value of THIS same kind,
                           identified solely by the name `name`;
     * `otherKind`       — the operand interprets to a value of a DIFFERENT kind
                           in this domain (one not identified by a bare name).
   These three cases are genuinely different operands and must stay apart. -/
inductive InterpretOutcome where
  | uninterpretable
  | sameKind (name : List Char)
  | otherKind
  deriving DecidableEq, Inhabited

/- The result the comparison must hand back. A comparison NEVER fails outright:
     * `decided b` — a definite boolean verdict `b` for this equality;
     * `deferred`  — no verdict is asserted here; the comparison declines and
                     hands off to the reflected/identity comparison instead
                     (a definite, non-error outcome — the operand is simply not
                     comparable as a value of this domain).
   `deferred` is the well-behaved answer for an operand that could not be
   interpreted: it must be produced INSTEAD of letting the interpretation's
   failure escape to the caller. -/
inductive Verdict where
  | decided (b : Bool)
  | deferred
  deriving DecidableEq, Inhabited

/- A failure shape the desired behaviour must NEVER produce: the comparison let
   the interpretation's failure escape to the caller as an error instead of
   declining gracefully. A correct comparison always yields a `Verdict`
   (`Except.ok`), never this. -/
inductive CmpErr where
  | interpretationEscaped
  deriving DecidableEq, Inhabited

/- The desired comparison result, as a function of this value's own `selfName`
   and the interpretation outcome of the operand:
     * an operand that could not be interpreted yields `deferred` — the
       interpretation's failure is absorbed, never escaping as an error;
     * an operand of THIS same kind compares equal exactly when the two names
       coincide (`decide (selfName = name)`);
     * an operand of a DIFFERENT kind is unequal (`decided false`): a value of
       this kind is never equal to one of another kind.
   Every outcome yields a `Verdict` (`Except.ok`); the result is never an
   escaped error. -/
def compareSpec (selfName : List Char) (o : InterpretOutcome) : Except CmpErr Verdict :=
  match o with
  | .uninterpretable => Except.ok .deferred
  | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
  | .otherKind       => Except.ok (.decided false)

@[grind] lemma compareSpec_uninterpretable (selfName : List Char) :
    compareSpec selfName .uninterpretable = Except.ok .deferred := rfl
@[grind] lemma compareSpec_sameKind (selfName name : List Char) :
    compareSpec selfName (.sameKind name)
      = Except.ok (.decided (decide (selfName = name))) := rfl
@[grind] lemma compareSpec_otherKind (selfName : List Char) :
    compareSpec selfName .otherKind = Except.ok (.decided false) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compare a value of this domain — identified solely by its `selfName` — for
   equality against an arbitrary operand. The operand is first interpreted as a
   value of the domain; `outcome` is that (unchanged) interpretation's result.
   `selfName` and `outcome` are read-only (not `mut`); the comparison builds a
   fresh verdict and mutates neither (directive 5). Desired behaviour:
     * if the operand cannot be interpreted, the comparison must DECLINE
       (`deferred`) rather than let the interpretation's failure escape to the
       caller — comparison must always return a verdict, never fail;
     * if the operand is a value of this same kind, the verdict is whether the
       two names coincide;
     * if the operand is a value of a different kind, the verdict is unequal.
   In particular the result is ALWAYS a verdict (`Except.ok _`), never an
   escaped error. -/
method compareName (selfName : List Char) (outcome : InterpretOutcome)
    return (out : Except CmpErr Verdict)
  ensures out = compareSpec selfName outcome
  ensures ∃ v, out = Except.ok v
  ensures outcome = .uninterpretable → out = Except.ok .deferred
  ensures ∀ name, outcome = .sameKind name →
    out = Except.ok (.decided (decide (selfName = name)))
  ensures outcome = .otherKind → out = Except.ok (.decided false)
  do
    -- impl-start
    -- Dispatch on the interpretation outcome. An operand that could not be
    -- interpreted yields a graceful decline rather than an escaped failure; an
    -- operand of this same kind compares equal iff the names coincide; an
    -- operand of a different kind is unequal.
    let result : Except CmpErr Verdict :=
      match outcome with
      | .uninterpretable => Except.ok .deferred
      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
      | .otherKind       => Except.ok (.decided false)
    return result
    -- impl-end

prove_correct compareName by
  loom_solve
  cases outcome <;> simp_all
