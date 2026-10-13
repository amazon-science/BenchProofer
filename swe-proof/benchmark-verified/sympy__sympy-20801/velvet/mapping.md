# mapping.md — sympy__sympy-20801

Symbol binding, the Lean↔Python type bijection (used by G-CONF and — were there
any — G-AX), callee provenance, and the pinned G-CONF fuzz seed. Provenance is
file:line **at `base_commit` `e11d3fed782146eebbffdc9ced0364b223b84b6c`**.

`spec_provenance: cold` — derived from the problem statement, the gold patch, and
the real source at `base_commit` only.

## 1. The modeled function

| Lean symbol | repo symbol | location @ base_commit | carrier |
|---|---|---|---|
| `equalsOperand` | `Float.__eq__(self, other)` | `sympy/core/numbers.py:1383` | `Int × Operand → Bool` (see §2) |

`Float` is `class Float(Number)` (`sympy/core/numbers.py:855`). The method
decides structural equality of a finite-precision floating-point value against a
sympified right-hand operand. The change is confined to this one method; no
other function on the fix list.

## 2. The type bijection (R)

The Python signature is `(self: Float, other) -> bool | NotImplemented`. After
the `_sympify(other)` coercion (which only narrows the success path — the
`SympifyError → NotImplemented` arm is outside the tested behavior and outside
the modeled domain), `other` is a SymPy object dispatched by a ladder of
`isinstance` / `is_*` tests. We model:

* **`self`** by `selfVal : Int` — its mpf mantissa·exponent value reduced to an
  exact integer proxy. The only properties the method reads of `self` are
  `bool(self)` (`Float.__bool__` is `self._mpf_ != fzero`, line 1285 → `selfVal = 0`)
  and `self._mpf_` used in the exact numeric comparison (`self._mpf_ == other._mpf_`,
  line 1400; `mlib.mpf_eq(self._mpf_, ompf)`, line 1410). `selfVal = 0 ↔ self is the
  zero float`. Two distinct mpf values map to distinct `Int`s (the comparison is
  exact — "`Float(.1, 3) != Float(.1, 33)`", line 1398).

* **`other`** by the inductive `Operand`, classifying the dispatch the ladder
  performs:

  | `Operand` ctor | Python operand class / test | branch (lines) | result modeled |
  |---|---|---|---|
  | `logical b`   | `isinstance(other, Boolean)` (`sympy.logic.boolalg.Boolean`, imported line 1384); `b` = `bool(other)` (S.true→true, S.false→false) | 1391–1392 | a float is never equal to a logical constant ⇒ `false` |
  | `numeric m`   | `other.is_NumberSymbol` / `other.is_Float` / `other.is_Rational` / `other.is_Number` — every operand whose equality with `self` is the exact value comparison at `self`'s precision; `m` = `other`'s precision-normalized mpf value (`other._mpf_`, or `other._as_mpf_val(self._prec)`) as the same `Int` proxy | 1393–1410 | `decide (selfVal = m)` (exact mpf equality) |
  | `symbolic t`  | a sympified object that is **not** a `Boolean` and **not** a `Number` (falls past every `is_*` test) | tail (`return False`, line 1411) reached after the zero shortcut | `t` = `bool(other)` (its truthiness); equal only to the zero value when falsy |

  Bijection for G-CONF: a Python operand is bridged to its `Operand` ctor by the
  same `isinstance`/`is_*` predicates the method uses (see `conformance_check.py`
  `classify`). `bool(x)` ↔ the ctor's truth field; `x`'s mpf value ↔ `m`.

`bool(other)` for the numeric branch is `other != 0`; for a logical constant it
is the constant itself; for a symbolic object it is `bool(other)` (defaults to
true for a generic symbol). These truth values are what the pre-image skeleton's
zero shortcut (`return not other`) consults — encoded inline in
`Solution_prepatch.lean`'s impl region (not in the shared spec).

## 3. Callees and provenance

| callee | role | handling |
|---|---|---|
| `_sympify(other)` | coerces `other` to a SymPy object; raises `SympifyError` | **R**: modeled as the classification into `Operand`. The `SympifyError → NotImplemented` arm is outside the modeled (tested) domain. |
| `Float.__bool__` (`numbers.py:1285`) | `self._mpf_ != fzero` | **R**: `selfVal ≠ 0`. The `not self` test is `selfVal = 0`. |
| `isinstance(other, Boolean)` | type test | **R**: `match` on the `logical` ctor. |
| `self._mpf_ == other._mpf_` / `mlib.mpf_eq` / `other._as_mpf_val` (1397–1410) | exact value comparison | **R/I**: `decide (selfVal = m)` (exact integer-proxy equality). These are **unchanged** numeric callees; the change does not touch them. Grounded structurally, so no axiom is consumed. |
| `bool(other)` / `not other` (the zero shortcut) | operand truthiness | **R**: the ctor's truth field; consulted only by the pre-image skeleton. |

No callee is **axiomatized** and no callee is a **deep-model reference**: every
operation is grounded as exact integer arithmetic or a constructor match (all
**R/I**). Therefore `axiom_check.py` is a no-op stub and `meta.json` lists no
axioms — there is nothing for G-AX to validate against a real callee.

## 4. G-CONF fuzz seed

Pinned seed **`20801`**, `N_FUZZ = 100_000`. The shadow builds the R/I
transliteration of `equalsOperand`'s impl region over the real `Float.__eq__`:
it constructs real SymPy operands (zero/nonzero `Float`s, `Integer`/`Rational`/
`Float` numerics, `S.true`/`S.false`, and non-`Number` symbolic objects), bridges
each to its `Operand` ctor (§2), and diffs `shadow(self, other)` against the
patched `self.__eq__(other)` (the G-RESOLVE oracle). Exit 0 iff zero
disagreements.
