import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The equality VERDICT a value produces for an operand,
--  and the binary comparison-operator dispatch that resolves two verdicts into a
--  decision, are modeled DEEPLY in the `pure` region below. The reflected
--  comparison the OTHER operand would produce is taken as a FREE INPUT
--  (`reflectedV`) — the spec makes no claim about a foreign object's own logic —
--  so there is no outside callee to axiomatize and no A-reference deep model.)
-- axioms-end

-- pure-start
/- The outcome a value reports when asked to compare itself to an operand. A
   comparison can decide the operand is equal, decide it is unequal, or report
   that it cannot make sense of the operand and the decision must be DELEGATED to
   the operand's own (reflected) comparison:
     * `isTrue`     — decided equal;
     * `isFalse`    — decided unequal;
     * `undecided`  — cannot interpret the operand; defer to its reflected logic. -/
inductive Verdict where
  | isTrue
  | isFalse
  | undecided
  deriving Inhabited, DecidableEq

/- How an operand presents to a value's equality test, reduced to the only
   distinctions the comparison reacts to:
     * `foreign`         — the operand cannot be interpreted in this value's
                           domain (its conversion is rejected);
     * `matchingEqual`   — the operand is interpretable and is the same thing;
     * `matchingUnequal` — the operand is interpretable but differs (different
                           kind, or interpretable yet not equal). -/
inductive Operand where
  | foreign
  | matchingEqual
  | matchingUnequal
  deriving Inhabited, DecidableEq

/- The equality verdict a value reports for an operand, modeled deeply. The
   desired behaviour:
     * an operand it cannot interpret yields `undecided` — the value declines to
       decide so the comparison can be delegated to the operand's reflected
       logic, keeping the relation symmetric;
     * an interpretable, equal operand yields `isTrue`;
     * an interpretable but differing operand yields `isFalse`. -/
def eqResult : Operand → Verdict
  | .foreign         => .undecided
  | .matchingEqual   => .isTrue
  | .matchingUnequal => .isFalse

/- The binary equality OPERATOR's dispatch — the unchanged language mechanism
   that resolves a comparison into a final yes/no. It consults the left value's
   verdict first; if that value declined to decide (`undecided`), it consults the
   operand's reflected verdict; if BOTH decline, the operands are distinct things,
   so the result is `false` (the identity fallback). The operator always returns a
   decided boolean. -/
def resolveEq (selfV reflectedV : Verdict) : Bool :=
  match selfV with
  | .isTrue     => true
  | .isFalse    => false
  | .undecided  =>
      match reflectedV with
      | .isTrue    => true
      | .isFalse   => false
      | .undecided => false

/- Inequality is the negation of the equality OPERATOR's resolved decision — NOT
   the negation of the value's raw verdict (negating an `undecided` report
   directly would silently treat "I cannot decide" as "equal" and break the
   relation). Routing through `resolveEq` means delegation is honoured before the
   negation. -/
def neResult (selfV reflectedV : Verdict) : Bool := ! resolveEq selfV reflectedV
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A value's own equality verdict for an operand. `operand` is read-only (not
   `mut`); the test computes a verdict and mutates nothing (directive 5). The
   load-bearing clause is the first conditional: an uninterpretable operand must
   be reported `undecided`, never `isFalse`, so the comparison can be delegated. -/
method directEquality (operand : Operand) return (out : Verdict)
  ensures out = eqResult operand
  ensures operand = .foreign → out = .undecided
  ensures operand = .matchingEqual → out = .isTrue
  ensures operand = .matchingUnequal → out = .isFalse
  do
    -- impl-start
    -- Pre-image skeleton: an operand it cannot interpret is decided UNEQUAL
    -- (`isFalse`) outright rather than declining (`undecided`). The frozen spec
    -- requires `operand = .foreign → out = .undecided`, so prove_correct MUST
    -- fail: deciding a foreign operand unequal precludes delegation and breaks
    -- the symmetric relation.
    let result : Verdict :=
      match operand with
      | .foreign         => .isFalse
      | .matchingEqual   => .isTrue
      | .matchingUnequal => .isFalse
    return result
    -- impl-end

prove_correct directEquality by
  loom_solve
  cases operand <;> simp_all [eqResult]

/- The equality comparison as the operator resolves it: it consults this value's
   own verdict (`directEquality`), and on `undecided` defers to the operand's
   reflected verdict, falling back to inequality when both decline.
   `reflectedV` is the operand's own comparison outcome — a free input.
   The discriminating clauses pin the delegation: a foreign operand that DOES
   recognise this value (reflected `isTrue`) compares EQUAL — reachable only
   because `directEquality` declined rather than deciding `isFalse`. -/
method equalityCompare (operand : Operand) (reflectedV : Verdict) return (out : Bool)
  ensures out = resolveEq (eqResult operand) reflectedV
  ensures (operand = .foreign ∧ reflectedV = .isTrue) → out = true
  ensures (operand = .foreign ∧ reflectedV = .isFalse) → out = false
  ensures (operand = .foreign ∧ reflectedV = .undecided) → out = false
  ensures (operand = .matchingEqual) → out = true
  do
    -- impl-start
    -- Consult this value's own verdict, then let the operator dispatch resolve it
    -- against the operand's reflected verdict (delegating on `undecided`).
    let selfV ← directEquality operand
    let r := resolveEq selfV reflectedV
    return r
    -- impl-end

prove_correct equalityCompare by
  loom_solve <;>
    (cases operand <;> cases reflectedV <;> simp_all [eqResult, resolveEq])

/- The inequality comparison. It negates the equality OPERATOR's resolved
   decision (`equalityCompare` → `resolveEq`), not this value's raw verdict, so a
   delegated comparison is resolved before negation. The discriminating clause:
   a foreign operand whose reflected logic also declines (`undecided`) is UNEQUAL
   (`true`) — whereas negating the raw `undecided` verdict directly would wrongly
   yield `false`. -/
method inequalityCompare (operand : Operand) (reflectedV : Verdict) return (out : Bool)
  ensures out = neResult (eqResult operand) reflectedV
  ensures (operand = .foreign ∧ reflectedV = .undecided) → out = true
  ensures (operand = .foreign ∧ reflectedV = .isTrue) → out = false
  ensures (operand = .matchingEqual) → out = false
  do
    -- impl-start
    -- Negate the operator-resolved equality decision (which delegates on an
    -- `undecided` verdict) rather than the raw verdict.
    let selfV ← directEquality operand
    let eq := resolveEq selfV reflectedV
    return !eq
    -- impl-end

prove_correct inequalityCompare by
  loom_solve <;>
    (cases operand <;> cases reflectedV <;> simp_all [eqResult, resolveEq, neResult])
