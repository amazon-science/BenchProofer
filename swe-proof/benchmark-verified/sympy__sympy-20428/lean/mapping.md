# mapping.md — sympy__sympy-20428

## Symbol binding (file:line @ base_commit c0e85160406f9bf2bcaa2992138587668a1cd0bc)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_nonzero` / `problem_spec_nonzero` / `correct_nonzero` | `ExpressionDomain.Expression.__bool__` — the truthiness (nonzero) test of an `EX` (symbolic-expression) domain element | `sympy/polys/domains/expressiondomain.py:122-123` @ base_commit |
| `ExprVal.isMathZero` | `f.ex.is_zero` — the symbolic value's *determined* mathematical-zero flag (the `Basic.is_zero` assumptions query) | post-patch RHS, `expressiondomain.py:123` |
| `ExprVal.isLiteralZero` | the truth of `f.ex == 0` — i.e. `f.ex != 0` is *false*; the value is *syntactically* the additive identity | pre-patch RHS, `expressiondomain.py:123` (`return f.ex != 0`) |

The modeled function is `Expression.__bool__`. It is invoked everywhere SymPy
asks "is this `EX` coefficient nonzero?" — most relevantly when DMP polynomial
representations are *stripped* of leading zero coefficients. A coefficient that
reports truthy is kept; one that reports falsy is stripped. The issue's
`clear_denoms()` on a constant poly produced a coefficient whose value is
mathematically `0` but written as a large nested-radical combination; under the
pre-patch syntactic test it reported truthy, so the leading zero was NOT
stripped, leaving the inconsistent `DMP([EX(0)], EX, None)` instead of
`DMP([], EX, None)`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| an `EX` element `f` wrapping a SymPy expression `f.ex` | `e : ExprVal` | the element is abstracted by exactly its two zero-observations below |
| `f.ex == 0` (structural/syntactic equality to the `Integer(0)` atom) is `True` | `e.isLiteralZero = true` | `bool(f.ex == 0)` ↦ `isLiteralZero` |
| `f.ex.is_zero` is `True` (assumptions system *determines* the value vanishes) | `e.isMathZero = true` | `f.ex.is_zero is True` ↦ `isMathZero = true`; `is_zero` being `False` **or `None`** ↦ `isMathZero = false` |
| return value of `__bool__(f)` (Python truthiness, a `bool`) | `result : Bool` | `True` ↦ `true`, `False` ↦ `false` |

### Modeling notes (the subtlety)

- `Basic.is_zero` is **three-valued**: `True`, `False`, or `None` (undetermined).
  The post-patch code computes `not f.ex.is_zero`. In Python `not None is True`,
  so an *undetermined* value reports **truthy** (nonzero) — conservative and
  correct (do not strip a coefficient you cannot prove is zero). The Lean model
  collapses this onto a single Boolean `isMathZero` that is `true` **iff
  `f.ex.is_zero is True`**; both `False` and `None` map to `isMathZero = false`,
  so `!isMathZero` faithfully reproduces `not f.ex.is_zero` across all three
  cases. G-CONF fuzzes all three (`True`/`False`/`None`).
- Soundness invariant relating the two flags: if a value is *syntactically* `0`
  then it is certainly mathematically `0` — `f.ex == 0 ⇒ f.ex.is_zero is True`.
  This invariant (`isLiteralZero = true → isMathZero = true`) is what makes the
  pre-patch syntactic test a *strict weakening* of the correct semantic test (it
  can only over-report nonzero), and the gap the issue exploits is exactly an
  input where it is slack (`isLiteralZero = false`, `isMathZero = true`). It is
  NOT a binder on `correct_nonzero` (the post-patch spec/impl agree
  unconditionally, so the theorem is unconditional); it is a semantic property
  of the real domain, asserted by `conformance_check.py` as a sanity invariant
  over every fuzzed expression (a literal-zero input must also be math-zero).

## Callee provenance + flag dependencies

- **No callee axiom is consumed.** The operation the patch changes is the
  zero-test itself; it is modeled DEEPLY by the two input flags
  (`isLiteralZero` for the pre-patch surface test, `isMathZero` for the
  post-patch semantic test). `Basic.is_zero` is the SymPy assumptions query that
  *defines* `isMathZero`; it is not an unchanged helper the proof needs a
  contract about — it is the observable bridged by `mapping.md` and validated by
  G-CONF (A-reference). Per §0.7 we do NOT axiomatize the operation the patch
  changes.
- No configuration flags gate the modeled function (`__bool__` takes no args).

## G-CONF fuzz seed

`SEED = 20240626` (pinned in `conformance_check.py`).
