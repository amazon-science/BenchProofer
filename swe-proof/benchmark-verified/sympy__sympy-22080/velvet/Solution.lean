import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- The kinds of single sub-expression that can sit directly under a leading
   unary minus in generated source, distinguished only by the printed-form
   class each one falls into:
     * `atomic`     — a bare symbol or number;
     * `power`      — an exponentiation;
     * `funcCall`   — a function-call form `f(...)` (self-delimited);
     * `modOp`      — a remainder operation, printed with an infix
                      remainder operator;
     * `mulCluster` — a product of factors.
   Sub-expressions that print into the same class are one kind. -/
inductive OperandKind where
  | atomic
  | power
  | funcCall
  | modOp
  | mulCluster
  deriving Inhabited, DecidableEq

-- axioms-start
-- (No axiomatized callees. The ordinary recursive printing of the inner factor
--  is unchanged by the behaviour modeled here, so it is consumed as the input
--  `inner` — whatever string the renderer already produces for that factor —
--  rather than re-derived; no property of it is owed a contract. The per-kind
--  wrap ranks are modeled DEEPLY in the `pure` region (`opWeight`); no outside
--  callee is consumed, so there is no contract for G-AX to validate (it skips),
--  and the deep model's fidelity to the desired behaviour is exercised
--  mechanically by conformance_check.py (G-CONF).)
-- axioms-end

-- pure-start
/- An opaque ordinal rank for each operand kind. Only the ORDER of these
   integers matters: the wrap rule below is a single `≤` comparison against
   `negLevel`, so any choice that preserves the kind ordering — `atomic` >
   `funcCall` > `power` > `modOp` > `mulCluster` — yields the same wrap
   decisions. Concrete integers (rather than a `<` relation) keep the
   comparison decidable in the kernel (order-only — see DECISIONS.md
   float-order note). The exact ranks are not meaningful; the per-kind wrap
   table is pinned extensionally by the `needsParen_*` lemmas below. -/
def opWeight : OperandKind → Int
  | .atomic     => 2000
  | .power      => 120
  | .funcCall   => 140
  | .modOp      => 100
  | .mulCluster => 99

/- The threshold rank for a leading unary minus, sitting strictly between the
   ranks of `power` and `modOp`. A factor whose rank does not exceed this
   threshold is wrapped in parentheses, so that the leading minus governs the
   whole factor rather than only its first piece. Like the ranks above, the
   exact value is not meaningful — only that it separates the wrapped kinds
   (`modOp`, `mulCluster`) from the bare ones (`atomic`, `power`, `funcCall`),
   exactly as the `needsParen_*` lemmas record. -/
def negLevel : Int := 110

/- Whether a factor of the given kind must be parenthesized under a leading
   unary minus: exactly when its rank does not exceed the threshold. -/
def needsParen (k : OperandKind) : Bool := decide (opWeight k ≤ negLevel)

/- The printed form of a negated single factor: a leading minus followed by the
   factor's own printed form `inner`, wrapped in parentheses precisely when the
   factor's kind is one that must be wrapped (per `needsParen`). -/
def renderNeg (k : OperandKind) (inner : List Char) : List Char :=
  '-' :: (if needsParen k then ('(' :: inner) ++ [')'] else inner)

@[grind] lemma renderNeg_def (k : OperandKind) (inner : List Char) :
    renderNeg k inner =
      '-' :: (if needsParen k then ('(' :: inner) ++ [')'] else inner) := rfl

/- The remainder operation and a multiplicative cluster are both wrapped. -/
@[grind, simp] lemma needsParen_modOp : needsParen .modOp = true := by decide
@[grind, simp] lemma needsParen_mul   : needsParen .mulCluster = true := by decide
/- An atom, a power, and a function call are not wrapped. -/
@[grind, simp] lemma needsParen_atom  : needsParen .atomic = false := by decide
@[grind, simp] lemma needsParen_pow   : needsParen .power = false := by decide
@[grind, simp] lemma needsParen_func  : needsParen .funcCall = false := by decide
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Print a single factor `inner` that sits directly under a leading unary minus,
   given the factor's kind `k`. The result is the factor's own printed form,
   parenthesized exactly when the factor's kind is one that must be wrapped,
   with the leading minus prepended. Both inputs are read-only (neither is
   `mut`; the print mutates nothing — directive 5); the result is a fresh
   sequence.

   The pinned behaviour: a remainder operation and a product cluster are
   wrapped (so the minus governs the whole factor); an atom, a power, and a
   self-delimited function call are not. -/
method printNegatedFactor (k : OperandKind) (inner : List Char) return (out : List Char)
  ensures out = renderNeg k inner
  ensures k = .modOp     → out = '-' :: (('(' :: inner) ++ [')'])
  ensures k = .mulCluster → out = '-' :: (('(' :: inner) ++ [')'])
  ensures k = .power     → out = '-' :: inner
  ensures k = .atomic    → out = '-' :: inner
  ensures k = .funcCall  → out = '-' :: inner
  do
    -- impl-start
    -- Look up the factor's binding strength and compare it to the unary-minus
    -- threshold; wrap the factor when it binds no more tightly than the
    -- threshold, then prepend the leading minus.
    let wrapped : List Char :=
      if needsParen k then ('(' :: inner) ++ [')'] else inner
    return '-' :: wrapped
    -- impl-end

prove_correct printNegatedFactor by
  loom_solve
