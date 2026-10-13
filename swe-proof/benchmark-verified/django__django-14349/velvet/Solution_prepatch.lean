import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The three ways the pre-existing structural validation of a candidate string
   can come out. It usually either accepts the string or refuses it with the
   designated validation failure, but on some degenerate strings it aborts with
   an unrelated error instead (neither an acceptance nor the designated
   refusal); that abort propagates out of the validator unchanged. -/
inductive BaselineOutcome where
  | accepts   -- the structural validation accepts the string
  | rejects   -- it refuses the string with the designated validation failure
  | crashes   -- it aborts with an unrelated error that propagates unchanged
  deriving DecidableEq

/- The pre-existing structural validation of a candidate string, abstracted as a
   pure, deterministic function of the string's code points onto the three
   outcomes above. It is left uninterpreted here because this artifact
   constrains only whether the additional code-point screen is applied *before*
   it — the structural validation itself is unchanged. Provenance + executable
   soundness check (determinism + totality onto the three outcomes over the
   value domain): mapping.md / axiom_check.py (G-AX). -/
axiom baselineOutcome : List Char → BaselineOutcome
-- axioms-end

-- pure-start
/- The three control code points that must never occur inside a valid string:
   horizontal tab (U+0009), carriage return (U+000D), and line feed (U+000A). -/
def isForbidden (c : Char) : Bool :=
  c = '\t' || c = '\r' || c = '\n'

/- Whether any code point of the sequence is one of the forbidden control
   characters. Front-recursive scan over the code points; equivalently, the
   sequence and the forbidden set have a non-empty common member. -/
def containsForbidden : List Char → Bool
  | []      => false
  | c :: cs => isForbidden c || containsForbidden cs

@[grind] lemma containsForbidden_nil : containsForbidden [] = false := rfl
@[grind] lemma containsForbidden_cons (c : Char) (cs : List Char) :
    containsForbidden (c :: cs) = (isForbidden c || containsForbidden cs) := rfl

/- The observable outcome of one validation call: a normal return (the string
   is accepted), the designated validation failure (the string is refused), or
   an abort by an unrelated error escaping the call. -/
inductive CallOutcome where
  | accepted  -- the call returns normally
  | rejected  -- the call raises the designated validation failure
  | crashed   -- an unrelated error escapes the call
  deriving DecidableEq

/- How the unchanged structural validation's outcome surfaces when it is the
   one that decides the call: acceptance returns, refusal raises the designated
   validation failure, and an abort escapes unchanged. -/
def liftBaseline : BaselineOutcome → CallOutcome
  | BaselineOutcome.accepts => CallOutcome.accepted
  | BaselineOutcome.rejects => CallOutcome.rejected
  | BaselineOutcome.crashes => CallOutcome.crashed

@[grind] lemma liftBaseline_accepts :
    liftBaseline BaselineOutcome.accepts = CallOutcome.accepted := rfl
@[grind] lemma liftBaseline_rejects :
    liftBaseline BaselineOutcome.rejects = CallOutcome.rejected := rfl
@[grind] lemma liftBaseline_crashes :
    liftBaseline BaselineOutcome.crashes = CallOutcome.crashed := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A string that carries a forbidden control character is refused with the
   designated validation failure OUTRIGHT — before, and independently of, the
   pre-existing structural validation, whose own three-way outcome the call
   otherwise surfaces unchanged (acceptance, the designated refusal, or an
   unrelated abort). The pre-existing validation's outcome on `value` enters as
   `baselineVerdict` (required equal to the opaque `baselineOutcome value`,
   i.e. it is that unchanged validation's deterministic answer). Crucially the
   forbidden-character screen is decided *without consulting* `baselineVerdict`,
   so a string carrying a forbidden character is always refused — even when the
   structural validation alone would have accepted it, and even when it would
   have aborted. -/
method validateUrl (value : List Char) (baselineVerdict : BaselineOutcome) return (outcome : CallOutcome)
  require baselineVerdict = baselineOutcome value
  ensures outcome = (if containsForbidden value then CallOutcome.rejected
                     else liftBaseline (baselineOutcome value))
  do
    -- impl-start
    -- Pre-image skeleton: no code-point screen is applied; the call's outcome
    -- is the structural validation's outcome alone. The frozen spec refuses
    -- any string carrying a forbidden character BEFORE that validation runs,
    -- so prove_correct MUST fail on inputs that carry a forbidden character
    -- yet the structural validation alone would not refuse.
    return liftBaseline baselineVerdict
    -- impl-end

prove_correct validateUrl by
  loom_solve
