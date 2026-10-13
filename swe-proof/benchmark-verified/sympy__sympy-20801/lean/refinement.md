# refinement.md — sympy__sympy-20801

Operation-by-operation correspondence between `implementation_floatEq`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `Float.__eq__`
equality dispatch). Tags: **R** type refinement, **A-consumed** proof uses an
axiom, **A-reference** deep model validated == real callee, **I** identical
concrete op.

The modeled domain starts AFTER the operand has been successfully sympified
(the `try: other = _sympify(other) except SympifyError: return NotImplemented`
guard is a precondition, not a modeled branch).

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if inp.otherIsBoolean then return false` | `if isinstance(other, Boolean): return False` | R |
| 2 | `if inp.otherIsNumberSymbol then (if inp.otherIsIrrational then return false; return inp.numberSymbolEq)` | `if other.is_NumberSymbol: if other.is_irrational: return False; return other.__eq__(self)` | R |
| 3 | `if inp.otherIsFloat then return inp.mpfEq` | `if other.is_Float: return self._mpf_ == other._mpf_` | R |
| 4 | `if inp.otherIsRational then return inp.rationalEq` | `if other.is_Rational: return other.__eq__(self)` | R |
| 5 | `if inp.otherIsNumber then return inp.numberMpfEq` | `if other.is_Number: ompf = other._as_mpf_val(self._prec); return bool(mlib.mpf_eq(self._mpf_, ompf))` | R |
| 6 | `if inp.selfIsZero then return inp.otherIsFalsy` | `if not self: return not other` (the RELOCATED clause, now after the dispatch) | R |
| 7 | `return false` | `return False    # Float != non-Number` | R |
| — | (no leading op — the relocated clause is NOT at the top) | the DELETED top-of-function `if not self: return not other` | I (relocation: the zero-operand clause now runs after ops 1–5 instead of before them) |

Notes:

- **Every step is R or I — no A.** The dispatch is modeled DEEPLY over the
  operand's observable kind-flags; SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed decision. The `axioms` region is empty; **G-AX skips**.
- The R tag on ops 1–7 is the *carried-observation* refinement: the boolean
  outcome of each UNCHANGED upstream sub-decision — the operand's own equality
  for a rational `NumberSymbol` (`numberSymbolEq`) and for a `Rational`
  (`rationalEq`), the exact mpf-tuple equality for a float (`mpfEq`), the
  shared-precision numeric equality (`numberMpfEq`), and the falsiness of the
  operand (`otherIsFalsy`) — is a field of `EqInput` rather than re-derived.
  These are orthogonal to the dispatch-ordering fix and unchanged by the patch;
  the bijection is the field↔Python-expression map in mapping.md. None of them
  leaves an output component free: `result` is fully pinned to `floatEqResult
  inp` (directive 5 frame: the lone output is the returned boolean).
- The **fix itself** is op-"—": the gold patch DELETES the top-of-function
  `if not self: return not other` and RE-INSERTS the identical clause just
  before the terminal `return False`. Its effect is captured by op 6 sitting
  AFTER ops 1–5 in the impl, exactly mirroring the relocated lines. The
  pre-patch impl (`Solution_prepatch.lean`) re-introduces it as a LEADING
  `if inp.selfIsZero then return inp.otherIsFalsy`, behaviourally identical to
  the base-commit top-of-function clause.
- The discriminating inputs (where prepatch ≠ post-patch) are exactly those with
  `selfIsZero = true` AND at least one of the kind-flags true with a delegated
  result differing from `otherIsFalsy` — chiefly `selfIsZero ∧ otherIsBoolean`
  (post-patch `false`, prepatch `otherIsFalsy`, which is `true` for `S.false`).
  This is precisely the `S(0.0) == S.false` regression in `test_zero_not_false`.
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against the post-patch dispatch over ≥1e5 fuzzed inputs.
