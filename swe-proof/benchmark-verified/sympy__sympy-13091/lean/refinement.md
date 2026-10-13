# refinement.md — sympy__sympy-13091

Operation-by-operation correspondence between the impl region of `Solution.lean`
(`implementation_richEq`, `implementation_richNe`) and `patch.diff` (the
POST-PATCH rich-comparison methods). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

The gold patch rewrites the same two idioms in ~30 classes across the codebase.
All edits are instances of exactly two behavior changes; the bundle models the
two changes once each (callee-before-caller: `richEq` then `richNe`).

## `implementation_richEq` ↔ `__eq__` + the `==` operator

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if sameObj then some true` | `if self is other: return True` (Basic) / `if self is other: return True` (NumberSymbol) | R |
| 2 | `else if identityOnly then some false` | `return other is S.Infinity` / `... is S.NegativeInfinity` / `... is S.NaN` (numbers.py:2833, 3054, 3219) — the identity-only family's whole method, reached only when op #1 already observed non-identity, hence `false` | R |
| 3 | `else if !interpretable then none` | `except SympifyError: return NotImplemented` (was `return False`) — **the fix** | R |
| 4 | `else if !sameKind then some false` | `if type(self) != type(other): return False` (Basic) / `return False  # non-(Number)` (numbers) | R |
| 5 | `else some contentEq` | `return self._hashable_content() == other._hashable_content()` (Basic) / mpf / `p,q` compare (numbers). The numeric side is not one comparison but a per-arm cascade, and mapping.md's `contentEq` row carries one measurement per arm: a `Float` lhs compares RAW mpf tuples against a `Float` operand (numbers.py:1266-1267) and re-precises only a non-`Float` `Number` operand (1268-1275) | R |
| 6 | `match selfVerdict with \| some b => return b \| none => match otherVerdict with \| some b => return b \| none => return false` | the `==` OPERATOR resolving the left method's `NotImplemented` by consulting `other.__eq__(self)` and finally `is` (CPython datamodel) | R |

- The operand classification (`_sympify` raising, `type` check, `_hashable_content`
  compare, `mpf_eq`), the left method's family, and the unit-exponent-power
  redirection are collapsed to the five boolean observables `sameObj /
  identityOnly / interpretable / sameKind / contentEq` measured on the OPERATIVE
  pair (mapping.md states each measurement). None of those callees is consumed as
  an axiom; they only produce the model's boolean inputs.
- The fix is op #3: the value's own opinion changes from a definite `false`
  (`some false`) to an ABSTENTION (`none`), which op #6 then resolves via the
  operand's reflected opinion `otherVerdict`. The pre-patch impl
  (`Solution_prepatch_1.lean`) keeps `some false`, so the reflected opinion is
  never consulted — that is the actual asymmetry bug; its carried gold proof
  fails to typecheck (G-DIFF), and it fails specifically on the
  `interpretable = false` goals, i.e. on the clause the patch changed.
- Op #2 is NOT part of the fix and must not be confused with it: it is the
  branch the patch deliberately leaves alone. It sits ABOVE the changed clause so
  that the abstention introduced by op #3 is claimed only for the family that
  really abstains.

## `implementation_richNe` ↔ `__ne__` + the `!=` operator

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 7 | `let eqResult := implementation_richEq …` | `self == other` — the resolved `==` OPERATOR (was `self.__eq__(other)`, the raw self-method) — **the fix** | R |
| 8 | `return !eqResult` | `return not (self == other)` | I |

- The fix is op #7: `not self.__eq__(other)` becomes `not self == other`. The raw
  self-method may return `NotImplemented`, and `not NotImplemented` is `False` in
  Python; routing through the `==` operator first resolves the reflected opinion
  and the identity fallback to a genuine boolean before negation. Modeled as:
  inequality = `!richEqRef …` (negation of the resolved operator) rather than
  negation of the raw `selfEqVerdict` (where `none` would be coerced truthy). The
  pre-patch impl (`Solution_prepatch_2.lean`) negates the raw self verdict
  (`none ↦ true`), reproducing the bug; its carried gold proof fails (G-DIFF) on
  the same `interpretable = false` goals.
- For the identity-only family the real `__ne__` is the matching `return other is
  not S.<singleton>`, which is the negation of that family's own `__eq__`; since
  op #2 makes that family's opinion always definite, `!richEqRef` agrees with it.

## REFINEMENT of the observables (2026-08-16) — why there are five, not three

The observable set has to be a total function: one real call must yield one
tuple, and one tuple must not carry two different real results. The earlier
four-observable version (`sameObj / interpretable / sameKind / contentEq` on the
RAW pair) failed that, measured on the base worktree with `patch.diff` applied:

| measured on | divergences from real `==` | tuples carrying BOTH real results |
|---|---|---|
| earlier 4-observable model, raw pair | **33** / 3450 pairs | **6** |
| current model (5 observables + operative pair) | **0** / 3450 pairs | **0** |

(3450 = 46 in-scope sympy left operands x 75 right operands: sympy expressions,
native Python scalars, and foreign classes whose reflected `__eq__` covers all
three replies. `!=` was checked on the same pool: 0 mismatches. A randomized
sweep of 20,000 pairs over generated expressions, seed 20260816, reproduces
0 / 0 / 0 and reaches 23 distinct tuples.)

The two collisions repaired, each on calls the repo really makes:

1. **unit-exponent power.** `(x**1.0) == x` is really `True`, because
   basic.py:307-311 REDIRECTS to `x == x`; `x == Bar()` with
   `Bar._sympy_ -> Integer(1)`, `Bar.__eq__ -> True` is really `False`. Both had
   the same raw tuple. Repair: observe the OPERATIVE pair — the pair the
   comparison finally lands on after the redirection. This is a syntactic
   normalization of the operands (`a.exp == 1 -> a.base`), not a copy of the
   answer: it is computed from the operands alone and mirrors exactly the two
   `return`s that do the redirecting.
2. **identity-only left operand.** `Basic() == Bar()` is really `True` (the
   left method abstains, the reflected opinion is honoured) while
   `oo == Bar()`, `-oo == Bar()`, `nan == Bar()` are really `False` (their
   `__eq__` is a bare identity test that never abstains). Both had the same
   4-observable tuple. Repair: the new Bool observable `identityOnly`.

`identityOnly` is honest and load-bearing:
- **mechanically computable from the inputs alone.** It is a pure function of
  `type(self)`: resolve `type(self).__eq__`, and check that its body minus
  docstring is a single `return <second parameter> is <expr>`. It never inspects
  the other operand and never consults the comparison's result.
- **not an enumeration of the answer.** Applied to every class in the post-patch
  tree that defines `__eq__` (87 of them, `scan_eq_ast.txt`), the criterion
  selects exactly three: `Infinity` (numbers.py:2833), `NegativeInfinity`
  (3054), `NaN` (3219). It was not fitted to that list; the list is what the
  criterion returns. `ComplexInfinity` (`zoo`) defines no `__eq__` at all and so
  resolves to `Basic.__eq__` — measured `False`, which is why `zoo == Bar()` is
  `True` and sits on the other side of the collision.
- **load-bearing, not decorative.** Deleting it reintroduces collision 2 above,
  and `G-PBT` carries rivals that differ from gold only in the `identityOnly`
  branch and are refuted.
- **not the fix.** The patch does not touch those three methods; the observable
  only records which of the two real families the left operand is in, so the
  changed clause (op #3) is asserted where it actually applies. Both prepatch
  rivals are still rejected, and rejected on the `interpretable = false` goals.

A third measurement precision was needed for zero divergence and is recorded in
mapping.md: `Integer.__eq__` short-circuits a NATIVE Python integer before
sympifying (numbers.py:2108; a `bool` IS a Python integer) and `Float.__eq__` a
native Python float (1250). Without it, `Integer(1) == True` and `S.One == True`
(really `True`) were modeled `False`, because `_sympify(True)` yields `S.true`,
which is not a `Number`.

A fourth precision, likewise recorded in mapping.md: `contentEq` for a `Float`
lhs is measured PER ARM of the real cascade, not by one recipe. Against a `Float`
operand the method compares the raw mpf tuples (numbers.py:1266-1267); only a
non-`Float` `Number` operand is re-precised to the lhs's precision (1268-1275),
as is the native-float fast path (1250-1257). Collapsing the arms into the
re-precising form made `Rational(1,10).evalf(15) == Rational(1,10).evalf(30)`
(really `False`) come out `True`. This is not the patch delta — those two lines
are byte-identical in the base and patched trees, and the input has
`interpretable = True`, so it never reaches the changed clause; it was an
over-strong `contentEq` observable. It is invisible to a single-precision operand
pool, where `_as_mpf_val(L._prec)` is a no-op, which is why the 3450/20,000-pair
sweeps above missed it and why mapping.md now also measures a multi-precision
pool (16,008 + 60,000 pairs, 0 divergences, 0 collisions).

No domain narrowing was applied: the modeled scope is unchanged (every left
operand whose `__eq__` is one of the eight bound methods), and nothing was
excluded to obtain the numbers above.

## Summary
- **Every step is R or I — no A.** The changed ops (#3 abstain, #6 operator
  resolution, #7 operator-level negation) are modeled DEEPLY as total functions
  over the observable inputs; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op. The `axioms` region is empty; **G-AX skips**.
- **No consumed callee.** `otherVerdict` is the operand's own reflected opinion —
  arbitrary external user code (the `Foo`/`Bar` test classes), a free input, not a
  repo callee, so it carries no axiom obligation.
- **G-CONF** mechanically refutes the R/I legs: an in-process replica of the
  post-patch `==`/`!=` operator semantics (left method → reflected method →
  identity), with ONE replica class per real family, is diffed against the impl
  shadow over the whole finite input space (2^5 x 3 = 96 tuples, exhaustive) plus
  ≥1e5 fuzzed `(sameObj, identityOnly, interpretable, sameKind, contentEq,
  otherVerdict)` tuples; zero disagreements.
