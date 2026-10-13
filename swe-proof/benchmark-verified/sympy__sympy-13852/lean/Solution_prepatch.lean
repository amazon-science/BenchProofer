import Mathlib
-- imports-end

/-!
Closed-form evaluation of a parametrized special function at a symbolic argument.

The function takes an order parameter `s` and an argument `z`, both symbolic
expressions, and returns either a closed-form value (when the pair falls into a
recognized case) or "no closed form" (the call is left as the unevaluated
function application).

The recognized cases are:

* three distinguished arguments (`z = 1`, `z = -1`, `z = 0`), handled for every
  order `s` and returning, respectively, a companion zeta-type value, the
  negation of an eta-type value, and `0`;
* for the specific order `s = 2`, a finite table of six distinguished arguments,
  each mapping to a transcendental closed form;
* for the orders `s = 0` and `s = -1`, a rational closed form in `z`.

Every other `(s, z)` pair has no closed form and the result is "none".

Modeled as an input→output relation: a pair of symbolic expressions ↦ an optional
symbolic expression. The implementation and the correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract: this behavior is a
-- pure structural dispatch over the symbolic argument, returning closed-form
-- expressions built from the symbolic carrier below. There is therefore no
-- `axiom <callee>_prop` for the proof to consume.

/-- A minimal symbolic-expression carrier: the fragment of the host algebra
needed to state the recognized arguments and their closed-form values. Two
expressions are considered equal iff they are built identically (structural
equality), mirroring the host system's structural comparison of these particular
construction forms. The companions `zeta`/`eta` and the constants `pi`, `imagUnit`
(the imaginary unit), `sqrt5` (the square root of five) are opaque builders. -/
inductive SymExpr where
  | lit : Int → SymExpr
  | pi : SymExpr
  | imagUnit : SymExpr
  | sqrt5 : SymExpr
  | log : SymExpr → SymExpr
  | zeta : SymExpr → SymExpr
  | eta : SymExpr → SymExpr
  | neg : SymExpr → SymExpr
  | add : SymExpr → SymExpr → SymExpr
  | sub : SymExpr → SymExpr → SymExpr
  | mul : SymExpr → SymExpr → SymExpr
  | div : SymExpr → SymExpr → SymExpr
  | powInt : SymExpr → Int → SymExpr
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- One half, `1/2`. -/
def SymExpr.half : SymExpr := .div (.lit 1) (.lit 2)
/-- `(√5 − 1)/2`. -/
def SymExpr.gSub : SymExpr := .div (.sub .sqrt5 (.lit 1)) (.lit 2)
/-- `(√5 + 1)/2`. -/
def SymExpr.gAdd : SymExpr := .div (.add .sqrt5 (.lit 1)) (.lit 2)
/-- `−(√5 − 1)/2`. -/
def SymExpr.zA : SymExpr := .neg SymExpr.gSub
/-- `−(√5 + 1)/2`. -/
def SymExpr.zB : SymExpr := .neg SymExpr.gAdd
/-- `(3 − √5)/2`. -/
def SymExpr.zC : SymExpr := .div (.sub (.lit 3) .sqrt5) (.lit 2)

/-- `π²`. -/
def SymExpr.piSq : SymExpr := .powInt .pi 2

/-- Closed form at the half argument: `π²/12 − log(2)²/2`. -/
def SymExpr.outHalf : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 12)) (.div (.powInt (.log (.lit 2)) 2) (.lit 2))
/-- Closed form at the argument `2`: `π²/4 − I·π·log(2)`. -/
def SymExpr.outTwo : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 4)) (.mul (.mul .imagUnit .pi) (.log (.lit 2)))
/-- Closed form at `−(√5 − 1)/2`: `−π²/15 + log((√5−1)/2)²/2`. -/
def SymExpr.outA : SymExpr :=
  .add (.neg (.div SymExpr.piSq (.lit 15))) (.div (.powInt (.log SymExpr.gSub) 2) (.lit 2))
/-- Closed form at `−(√5 + 1)/2`: `−π²/10 − log((√5+1)/2)²`. -/
def SymExpr.outB : SymExpr :=
  .sub (.neg (.div SymExpr.piSq (.lit 10))) (.powInt (.log SymExpr.gAdd) 2)
/-- Closed form at `(3 − √5)/2`: `π²/15 − log((√5−1)/2)²`. -/
def SymExpr.outC : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 15)) (.powInt (.log SymExpr.gSub) 2)
/-- Closed form at `(√5 − 1)/2`: `π²/10 − log((√5−1)/2)²`. -/
def SymExpr.outD : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 10)) (.powInt (.log SymExpr.gSub) 2)
-- pure-end

-- post-conditions-start
/-- The result is the closed-form value of the order-`s` function at argument `z`,
or `none` when the pair has no closed form. The three distinguished arguments take
priority over the order, matching for every `s`; the order `s = 2` selects from a
finite argument table (no match ⇒ `none`); orders `s = 0` and `s = -1` give a
rational form in `z`; everything else is `none`. Every case pins the result, so no
output is left unconstrained. -/
def problem_spec_polylogEval (s z : SymExpr) (result : Option SymExpr) : Prop :=
  if z = .lit 1 then result = some (.zeta s)
  else if z = .lit (-1) then result = some (.neg (.eta s))
  else if z = .lit 0 then result = some (.lit 0)
  else if s = .lit 2 then
    (if z = SymExpr.half then result = some SymExpr.outHalf
     else if z = .lit 2 then result = some SymExpr.outTwo
     else if z = SymExpr.zA then result = some SymExpr.outA
     else if z = SymExpr.zB then result = some SymExpr.outB
     else if z = SymExpr.zC then result = some SymExpr.outC
     else if z = SymExpr.gSub then result = some SymExpr.outD
     else result = none)
  else if s = .lit 0 then result = some (.div z (.sub (.lit 1) z))
  else if s = .lit (-1) then result = some (.div z (.powInt (.sub (.lit 1) z) 2))
  else result = none
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: only the three distinguished arguments are
-- recognized; for every other `(s, z)` pair the call is left unevaluated
-- (`none`). In particular the order-2 argument table and the rational forms for
-- orders 0 and -1 are absent, so e.g. order 2 at the half argument returns
-- `none` instead of its closed form.
def implementation_polylogEval (s z : SymExpr) : Option SymExpr := Id.run do
  if z = .lit 1 then return some (.zeta s)
  if z = .lit (-1) then return some (.neg (.eta s))
  if z = .lit 0 then return some (.lit 0)
  return none
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl.
-- Discriminating input: `s = 2`, `z = 1/2`. The spec requires `some SymExpr.outHalf`,
-- but the buggy scan returns `none` (it has no order-2 table), so the
-- `s = .lit 2 ∧ z = SymExpr.half` branch of `problem_spec` is unprovable.
theorem correct_polylogEval :
    ∀ (s z : SymExpr),
    problem_spec_polylogEval s z (implementation_polylogEval s z) := by
  sorry
-- proof-end
