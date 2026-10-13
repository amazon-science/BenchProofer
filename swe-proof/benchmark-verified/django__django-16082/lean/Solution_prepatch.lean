import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature: the only callee the modeled
-- function relies on is the runtime subclass test, which is reproduced concretely
-- as a total Boolean relation over the finite set of numeric field kinds (see the
-- `pure` region). Its agreement with the real subclass predicate is validated
-- executably (G-AX) rather than assumed, so the axioms region stays empty. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The numeric field kinds that participate in arithmetic-type resolution. -/
inductive FieldKind where
  | integerKind
  | floatKind
  | decimalKind
  | autoKind
  deriving DecidableEq, BEq, Repr

/-- The arithmetic operators whose result kind is resolved from the operand
kinds. -/
inductive ArithOp where
  | add
  | sub
  | mul
  | div
  | modOp
  | powOp
  deriving DecidableEq, BEq, Repr

/-- A registered combination row: a left operand kind, a right operand kind, and
the resulting kind. -/
abbrev ComboRow := FieldKind × FieldKind × FieldKind

/-- Operand-kind compatibility: a kind is accepted by a slot of kind `target`
when it is `target` itself, or a specialization of it. The only specialization
among the numeric kinds is that the auto-increment integer kind is a kind of
plain integer. Total and decidable — no runtime callee is assumed. -/
def kindMatches : FieldKind → FieldKind → Bool
  | .autoKind, .integerKind => true
  | a, b => a == b

/-- Rows registered for operations whose operands share the same kind. -/
def sameKindRows : List ComboRow :=
  [(.integerKind, .integerKind, .integerKind),
   (.floatKind,   .floatKind,   .floatKind),
   (.decimalKind, .decimalKind, .decimalKind)]

/-- Rows registered for operations that accept operands of mixed numeric kind,
promoting to the wider kind. -/
def mixedKindRows : List ComboRow :=
  [(.integerKind, .decimalKind, .decimalKind),
   (.decimalKind, .integerKind, .decimalKind),
   (.integerKind, .floatKind,   .floatKind),
   (.floatKind,   .integerKind, .floatKind)]

/-- Operators that support same-kind numeric operands. -/
def sameKindOps : List ArithOp := [.add, .sub, .mul, .div, .modOp, .powOp]

/-- Operators that promote operands of differing numeric kind to the wider kind:
addition, subtraction, multiplication, division, and remainder. Exponentiation is
not among them — a mixed-kind power has no registered promotion. -/
def mixedKindOps : List ArithOp := [.add, .sub, .mul, .div, .modOp]

/-- Scan registered rows in order, returning the result kind of the first row
whose operand slots both accept the given operand kinds. -/
def firstMatch : List ComboRow → FieldKind → FieldKind → Option FieldKind
  | [], _, _ => none
  | (clhs, crhs, combined) :: rest, lhs, rhs =>
      if kindMatches lhs clhs && kindMatches rhs crhs then some combined
      else firstMatch rest lhs rhs

/-- The combination rows registered for a given operator, same-kind rows first,
then mixed-kind rows (the registration order). -/
def combosFor (op : ArithOp) : List ComboRow :=
  (if sameKindOps.contains op then sameKindRows else []) ++
  (if mixedKindOps.contains op then mixedKindRows else [])

/-- The result kind an operator yields for the given operand kinds: the first
registered combination that accepts both operands, or none. -/
def resolveSpec (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind :=
  firstMatch (combosFor op) lhs rhs
-- pure-end

-- post-conditions-start
/-- The resolved result kind is exactly the first registered combination for the
operator whose two operand slots both accept the operand kinds (or none when no
registered combination accepts them). This pins the result for every operator and
operand-kind pair — including mixed numeric kinds under the remainder operator,
which must promote to the wider kind. -/
def problem_spec_resolveCombinedType
    (op : ArithOp) (lhs rhs : FieldKind) (result : Option FieldKind) : Prop :=
  result = resolveSpec op lhs rhs
-- post-conditions-end

-- impl-start
def implementation_resolveCombinedType
    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do
  let mut combinators : List ComboRow := []
  if sameKindOps.contains op then
    combinators := combinators ++ sameKindRows
  -- Pre-patch (buggy): the remainder operator is omitted from the mixed-kind
  -- operators, so a remainder of differing numeric kinds resolves to none.
  if ([ArithOp.add, .sub, .mul, .div] : List ArithOp).contains op then
    combinators := combinators ++ mixedKindRows
  for (clhs, crhs, combined) in combinators do
    if kindMatches lhs clhs && kindMatches rhs crhs then
      return some combined
  return none
-- impl-end

-- proof-start
theorem correct_resolveCombinedType :
    ∀ (op : ArithOp) (lhs rhs : FieldKind),
    problem_spec_resolveCombinedType op lhs rhs
      (implementation_resolveCombinedType op lhs rhs) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
