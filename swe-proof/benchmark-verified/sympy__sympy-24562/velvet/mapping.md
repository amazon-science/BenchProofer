# mapping.md — sympy__sympy-24562

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b1cb676cf92dd1a48365b731979833375b188bf2`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled piece.

Repo file under change: `sympy/core/numbers.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `denominatorProduct (pDen : Nat) (qDigits : List Nat)` | the denominator-accumulation block of `Rational.__new__` — `sympy/core/numbers.py:1626-1641` (the assignments that build the combined denominator from the two normalised operands) | the modeled changed function |
| `digitsValue (ds : List Nat)` | the integer value of a decimal-string operand, as obtained by parsing it (`int(q)` / `fractions.Fraction`) — `sympy/core/numbers.py:1640` post-patch (`Q *= int(q)`) | pure spec: the numeric value of a non-negative integer written in positional decimal notation |

The denominator-accumulation block at base_commit (the bug):

```python
        q = 1
        gcd = 1
        ...
        if not isinstance(p, SYMPY_INTS):
            p = Rational(p)
            q *= p.q          # line 1630 — q is still the RAW q operand here
            p = p.p
        else:
            p = int(p)
        if not isinstance(q, SYMPY_INTS):
            q = Rational(q)
            p *= q.q
            q = q.p
        else:
            q = int(q)        # line 1640
```

The fix (gold) introduces a fresh integer accumulator `Q`, so the raw `q`
operand is only ever *parsed*, never arithmetically scaled:

```python
        Q = 1
        ...
            Q *= p.q          # was: q *= p.q
        ...
            Q *= q.p          # was: q = q.p
        else:
            Q *= int(q)       # was: q = int(q)
        q = Q
```

## 2. The bug, precisely

When the second operand `q` is supplied as a **string** (e.g. `Rational('0.5',
'100')`), it is *not* a `SYMPY_INTS`, so at base_commit the first branch runs
`q *= p.q`. Here `q` is still the raw `str` `'100'` and `p.q` is the integer
denominator of the first operand (`2`, from `Rational('0.5') = 1/2`). Python's
`str * int` **repeats** the string: `'100' * 2 == '100100'`, which is then
reparsed to the integer `100100`. So `Rational('0.5','100')` yields `1/100100`
instead of the correct `1/200`. The fix accumulates the factor into a fresh
*integer* `Q` (`Q *= p.q` ⇒ `1 * 2 = 2`) and multiplies by the parsed value of
the operand (`Q *= int('100') = 200`), so the denominator is the arithmetic
**product** `pDen * value(q) = 2 * 100 = 200`.

This is a type-confusion bug: scaling a still-textual operand *repeats* its
digit sequence, whereas the correct denominator is the *value-product*.

## 3. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the denominator factor `p.q` contributed by the first operand (a positive `int`) | `pDen : Nat` | `pDen` ↔ the Python `int p.q`; both ≥ 1 (a normalised denominator is positive). The unchanged callee that produces it (`Rational(p).q`) is consulted before this step. |
| the second operand `q`, a non-negative integer presented in decimal notation (the `str` case the bug hits) | `qDigits : List Nat` | the decimal digit string `d₀d₁…dₙ` (most significant first) ↔ `[d₀, d₁, …, dₙ]` with each `dᵢ < 10`. `digitsValue qDigits` ↔ `int("".join(map(str, qDigits)))`. |
| the combined denominator the block produces | `out : Nat` | `out` ↔ the integer the patched block assigns to `q` (`Q`). |

Why `List Nat` (decimal digits), not just `Nat`: the bug is **non-homomorphic**
in the value domain (string repeat ≠ integer multiply), so an `Int`-only model
could not exhibit it. The carrier must expose the *digit sequence* so that
"repeat the operand" (`(List.replicate pDen qDigits).flatten`, the prepatch) is
distinguishable from "multiply its value" (`pDen * digitsValue qDigits`, the
spec). On every non-degenerate input these differ (`'100'*2 = 100100 ≠ 200`).

## 4. Callee provenance (kind-A)

None. There is **no consumed axiom** and **no A-reference deep model**. The two
inputs (`pDen`, `qDigits`) are read-only abstractions of values produced by
UNCHANGED parsing/normalisation callees (`Rational(p).q`, `int(q)` /
`fractions.Fraction`) that run *before* the changed block; they are not
re-derived or pinned here. The operation under specification — assembling the
combined denominator — is modeled **deeply** as the `do` block. So G-AX has
nothing to validate (`meta.json gates.G-AX.status = "skip"`, no `axiom_check.py`).

## 5. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24562`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`digitsValue` and the impl region's value-product (R/I-tagged ops) to Python and
compares against `patch.diff`'s behaviour (the patched denominator block) over
≥10⁵ fuzzed `(pDen, qDigits)` inputs, bridged via the §3 bijection. The impl
region is entirely R/I (no A-tagged callee), so G-CONF runs for real
(`conf_skip = false`).
