# mapping.md — sympy__sympy-13091

## Symbol binding (file:line @ base_commit d1320814eda6549996190618a21eaf212cfd4d1e)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_richEq` / `problem_spec_richEq` / `correct_richEq` | the `==` operator for a symbolic left operand, i.e. the left operand's own `__eq__` together with the operator-level reflected fallback | `sympy/core/basic.py:282-320` (`Basic.__eq__`); `sympy/core/numbers.py:1249-1276` (`Float`), `1718-1734` (`Rational`), `2107-2112` (`Integer`), `3338-3349` (`NumberSymbol`), `2833` (`Infinity`), `3054` (`NegativeInfinity`), `3219-3221` (`NaN`) |
| `implementation_richNe` / `problem_spec_richNe` / `correct_richNe` | the `!=` operator for a symbolic left operand, i.e. that operand's own `__ne__` | `sympy/core/basic.py:322-332`; `sympy/core/numbers.py:1278-1279, 1736-1737, 2114-2115, 3351-3352, 2836, 3057, 3223-3224` |
| `selfEqVerdict` (pure helper) | the verdict computed by the left operand's `__eq__` before the operator resolves it (identity → family → interpret-attempt → kind check → content compare) | basic.py:304-320, numbers.py:1249-1276, 1718-1734, 2107-2112, 3338-3349, 2833, 3054, 3219-3221 |
| `resolveEq` (pure helper) | CPython's `==` operator resolution rule: try the left method, then the reflected right method, then fall back to identity (`is`) which is `False` for distinct objects | language semantics, https://docs.python.org/3/reference/datamodel.html#object.__eq__ |
| `otherVerdict` (input) | the verdict that the OTHER operand's own `__eq__` would return when handed the symbolic object (`NotImplemented`/`True`/`False`) — arbitrary user code, NOT a sympy callee | call-site dependent (`Foo`/`Bar` in the F2P tests) |

**Every left operand whose `__eq__` is one of the eight methods above is IN
scope.** The binding names them individually rather than saying "a symbolic left
operand", because the repo has two structurally different families of `__eq__`
and the model has to carry both (see `identityOnly` below). A left operand whose
type resolves `__eq__` to something else — one of the other 79 classes in the
tree that define their own `__eq__` (measured: `_scan_eq` over the post-patch
tree finds 87 `__eq__` definitions in all) — is a different function and is not
modeled here.

## What the functions do (post-patch, = the modeled behavior)

### `Basic.__eq__(self, other)` (basic.py:282-320) — the classify-then-compare family
```python
from sympy import Pow
if self is other:
    return True
if type(self) is not type(other):
    # issue 6100 a**1.0 == a like a**2.0 == a**2
    if isinstance(self, Pow) and self.exp == 1:
        return self.base == other        # <-- redirects to the OPERATIVE pair
    if isinstance(other, Pow) and other.exp == 1:
        return self == other.base        # <-- redirects to the OPERATIVE pair
    try:
        other = _sympify(other)
    except SympifyError:
        return NotImplemented            # <-- the fix (base_commit: return False)
    if type(self) != type(other):
        return False
return self._hashable_content() == other._hashable_content()
```
`Float`/`Rational`/`Integer`/`NumberSymbol.__eq__` (numbers.py) have the same
shape minus the two `Pow` redirections: `_sympify(other)` is attempted, on
`SympifyError` it returns `NotImplemented` (the fix), otherwise a
same-kind / content comparison decides and a sympifiable non-number is `False`.
`Integer.__eq__` and `Float.__eq__` additionally short-circuit a NATIVE Python
integer / float before sympifying (see the `interpretable` measurement below).

### The identity-only family (numbers.py:2833, 3054, 3219)
```python
class Infinity:          def __eq__(self, other): return other is S.Infinity
class NegativeInfinity:  def __eq__(self, other): return other is S.NegativeInfinity
class NaN:               def __eq__(self, other): return other is S.NaN
```
These three are the whole family. Each is a bare identity test: it never calls
`_sympify`, never returns `NotImplemented`, and — because the class is a
`Singleton`, so `self` IS that singleton — its value is exactly `other is self`.
`patch.diff` leaves all three untouched, which is why the model needs to know
which family the left operand belongs to rather than assuming the first.

### `Basic.__ne__(self, other)` / `Number.__ne__`
```python
return not self == other             # <-- the fix (base_commit: not self.__eq__(other))
```
The identity-only family's `__ne__` is the matching `return other is not
S.<singleton>`, i.e. the negation of its own `__eq__`, so `richNeRef = !richEqRef`
holds for that family too.

## The OPERATIVE PAIR (how the operands are fixed before anything is observed)

basic.py:307-311 does not decide the comparison in those two branches — it
REDIRECTS it to a different pair and re-enters the `==` operator there
(`return self.base == other` / `return self == other.base`). So the pair that the
five observations below describe is the pair the comparison finally lands on:

```python
def operative_pair(a, b):
    """mechanical; a pure function of the two operands"""
    while type(a).__eq__ is Basic.__eq__ and type(a) is not type(b):
        if isinstance(a, Pow) and a.exp == 1:   a = a.base;  continue
        if isinstance(b, Pow) and b.exp == 1:   b = b.base;  continue
        break
    return a, b
```
The `type(a).__eq__ is Basic.__eq__` guard is not an extra assumption: the two
redirecting branches exist only in `Basic.__eq__`, so no other left method
redirects. The loop terminates because each step replaces an operand by a proper
subterm of itself.

`otherVerdict` is measured on the operative pair too (`Rop.__eq__(Lop)`), because
the reflected consultation happens inside the re-entered operator, on the pair it
was re-entered with.

## The five observable classes of the operand (abstraction)

Let `(L, R) = operative_pair(self, other)`.

| Lean input | meaning | how it is MEASURED on the real repo |
|---|---|---|
| `sameObj` | `L` and `R` are the same object | `L is R` |
| `identityOnly` | `L`'s kind decides equality by bare object identity — it has no notion of interpreting the operand and can never abstain | a pure function of `type(L)`: resolve `type(L).__eq__` and check that its body, minus docstring, is a single `return <second parameter> is <expr>`. Measured over the whole post-patch tree (87 classes defining `__eq__`): the criterion selects exactly `Infinity` (2833), `NegativeInfinity` (3054), `NaN` (3219) and nothing else. It is a syntactic property of the left operand's TYPE — it never looks at `R` and never consults the comparison's answer |
| `interpretable` | `R` can be coerced into the value's universe at all | `L`'s own coercion: an `Integer` value takes a native Python integer directly (numbers.py:2108 `isinstance(other, integer_types)` — a `bool` IS a Python integer) and a `Float` value takes a native Python float directly (numbers.py:1250); every other operand is `_sympify(R)`, and `interpretable` is false exactly when that raises `SympifyError` |
| `sameKind` | after coercion, `R` is of a kind `L` knows how to compare | structural values (`Basic.__eq__`) and `NumberSymbol`: `type(L) is type(Rs)`; numeric values (`Float`/`Rational`/`Integer`): `isinstance(Rs, Number)`, with the two native fast paths above counting as numbers |
| `contentEq` | the coerced value has content equal to `L`'s | structural: `L._hashable_content() == Rs._hashable_content()`; `Float` lhs — **two distinct arms, in the order the method tests them**: vs a `Float` `Rs`, the RAW mpf tuples are compared with no re-precision, `mpf_eq(L._mpf_, Rs._mpf_)` (numbers.py:1266-1267); vs any other `Number` `Rs`, `Rs` is first re-precised to `L`'s precision, `mpf_eq(L._mpf_, Rs._as_mpf_val(L._prec))` (numbers.py:1268-1275); `Rational`/`Integer` lhs vs `Rational`: `L.p == Rs.p and L.q == Rs.q`; vs `Float`: `mpf_eq(L._as_mpf_val(Rs._prec), Rs._mpf_)` (numbers.py:1733); native-integer fast path: `L.p == Rs`; native-float fast path: `Rs` is coerced with `Float(R)` and then re-precised, `mpf_eq(L._mpf_, Float(R)._as_mpf_val(L._prec))`, `False` if that raises `ValueError` (numbers.py:1250-1257) |

The `Float`-lhs split is load-bearing and is NOT a don't-care: the two arms
disagree exactly when `L` and `Rs` are `Float`s of DIFFERENT precision whose
values agree only after the wider one is rounded to the narrower one's
precision. `Rational(1,10).evalf(15) == Rational(1,10).evalf(30)` is really
`False` (raw tuples `(0,3602879701896397,-55,52)` vs
`(0,4056481920730334084789450257203,-105,102)` differ) although the re-precising
arm would report equal content. A single-precision operand pool cannot see the
difference, because there `_as_mpf_val(L._prec)` is a no-op; the sweep below is
therefore run over a MULTI-PRECISION `Float` pool. Note the two arms are not
interchangeable in the other direction either: the native-float fast path at
1250-1257 really does re-precise, so `Rational('0.1').evalf(10) == 0.1` is
`True` while the raw tuples differ.
| `otherVerdict : Option Bool` | what `R.__eq__(L)` returns | `type(R).__eq__(R, L)`; `NotImplemented ↦ none`, definite `b ↦ some b` |

When `identityOnly` is true the remaining three classifier observations are not
consulted by the spec (the identity-only methods do not compute them); they are
still measured mechanically, and the differential fuzz below covers both
settings of each, so nothing is hidden behind a don't-care.

### Lean ↔ Python type bijection (used by G-CONF / G-AX)
- `Bool` ↔ Python `bool` (the five classifier observables).
- `Option Bool` ↔ Python rich-comparison return: `none ↔ NotImplemented`,
  `some True ↔ True`, `some False ↔ False`. (Lean is total, so a method always
  yields one of these three; Python's third value is the `NotImplemented`
  singleton.)
- `resolveEq lhs rhs : Bool` ↔ the boolean that the `==` operator finally yields
  after reflected dispatch and the identity fallback (`bool(a == b)`).

## WELL-DEFINEDNESS (the abstraction is a total function — measured, not argued)

The observable set must map each real call to ONE tuple and each tuple to ONE
real result. Measured against the base worktree with `patch.diff` applied
(sympy 1.1.2.dev):

- a deterministic sweep of 3450 ordered pairs (46 sympy left operands × 75 right
  operands: sympy expressions, native Python scalars, and foreign classes whose
  reflected `__eq__` covers all three replies) — **0 divergences from the real
  `==`, 0 divergences from the real `!=`, 0 tuples carrying two different real
  results**, over 20 distinct tuples reached;
- a randomized sweep of 20,000 pairs over randomly generated expressions
  (symbols, all 30 numeric singletons and literals, and `Pow`/`Add`/`Mul`/
  `Basic`/applied-function nodes built to depth 3, with `evaluate` toggled so the
  unevaluated unit-exponent powers are actually produced; seed 20260816) — **0
  divergences from the real `==`, 0 from the real `!=`, 0 collisions**, over 23
  distinct tuples reached.

Neither pool above can exercise the `Float`-lhs arm split, and not because it
draws one precision: their only non-default-precision entry is `Float(1.0, 30)`,
`1.0` is binary-exact, and no pair either pool generates carries one inexact
value at two precisions — so the re-precising `_as_mpf_val(L._prec)` cannot
change an answer there. The `contentEq` row is therefore re-measured over a pool
that carries several precisions per value:

- a MULTI-PRECISION pool — 15 decimal values (`0.1`, `0.2`, `0.3`, `0.7`, `1/3`,
  `2/7`, `1/7`, `22/7`, `1/9`, `-0.1`, and the binary-exact `0.5`/`1.0`/`2.0`/
  `0.25`/`0`) × precisions {5, 8, 10, 15, 20, 25, 30, 40, 53, 80}, together with
  the structural, `Rational`/`Integer`, identity-only, `NumberSymbol`, `zoo`,
  native-scalar and foreign-class operands of the pools above: 16,008 ordered
  pairs deterministic + 60,000 randomized (seed 13091) — **0 divergences from the
  real `==`, 0 from the real `!=`, 0 tuples carrying two different real results**,
  19 distinct tuples reached. Under the single re-precising recipe the same pools
  give 147 / 700 divergences, every one a `Float(v,p1)` vs `Float(v,p2)` pair
  with `p1 != p2` and `v` not binary-exact.

The two observables above are exactly what makes that hold. Removing either one
reintroduces a collision, and both collisions are on calls the repo really makes:

| removed | colliding tuple | the two real calls |
|---|---|---|
| operative pair | `sameObj=F, interpretable=T, sameKind=F, contentEq=F, otherVerdict=some true` | `(x**1.0) == x` → real `True` (the redirect makes `x == x` the operative comparison) vs `x == Bar()` where `Bar._sympy_ -> Integer(1)` and `Bar.__eq__ -> True` → real `False` |
| `identityOnly` | `sameObj=F, interpretable=F, sameKind=F, contentEq=F, otherVerdict=some true` | `Basic() == Bar()` (test_basic.py's `Bar`) → real `True` vs `oo == Bar()` / `-oo == Bar()` / `nan == Bar()` → real `False` |

`zoo` (`ComplexInfinity`) is NOT in the identity-only family — it defines no
`__eq__` and resolves to `Basic.__eq__` — so `zoo == Bar()` is `True`, on the
first side of that collision. Measured, not assumed.

## Callee provenance + flag deps
- **No consumed callee axiom; no A-reference.** `_sympify`, `_hashable_content`,
  `mpf_eq`, `Pow.exp`/`Pow.base` are NOT modeled: they only feed the five
  classifier observables and the operative-pair normalization, which are the
  model's inputs. The operand's reflected `__eq__` (`otherVerdict`) is arbitrary
  user code, not a repo callee, so it is a free input — not an axiom.
- No flag dependency.

## Dispatch-priority scope (abstraction boundary)
`resolveEq` consults the left operand's opinion first, then the reflected
opinion. CPython gives the RIGHT operand priority only when its type is a
*subclass* of the left operand's type and overrides the reflected method. The two
gated F2P tests use operands (`Foo`/`Bar`) that are NOT subclasses of the
symbolic types, so left-first resolution is exact for the modeled scope; the
subclass-priority case is out of scope and not modeled.

## G-CONF fuzz seed
Pinned seed: **13091** (also in conformance_check.py and meta.json).
