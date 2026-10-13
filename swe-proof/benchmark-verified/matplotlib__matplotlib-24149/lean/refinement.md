# refinement.md — operation correspondence (matplotlib__matplotlib-24149)

Maps every op in `implementation_safeRepresentative` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python selection (for each of `x0` and `xconv`) is:
```python
try:
    sel = cbook._safe_first_finite(seq)   # first finite, else StopIteration
except (TypeError, IndexError, KeyError):
    sel = <argument left unchanged>       # the LONE-COORDINATE route
except StopIteration:                     # <-- the FIX
    sel = cbook.safe_first_element(seq)   # first element unconditionally
```
We model the whole three-way selection deeply as `chooseRepresentative`: a lone
coordinate argument stands for itself; a sequence yields its first element that
COUNTS AS FINITE if one exists, else the first element of a non-empty sequence
(`vs.head?`), else nothing.

The per-element ruling is itself modeled deeply and per REGIME, because
`safe_isfinite` is NOT `np.isfinite`. Verbatim at base_commit (`cbook` is
unchanged by the patch):
```python
def safe_isfinite(val):
    if val is None:
        return False                                       # MISSING: never
    try:
        return np.isfinite(val) if np.isscalar(val) else True   # weighed, or
    except TypeError:
        return True                                        # UNWEIGHABLE: always
```
So the ruling has THREE regimes, and `CoordVal` / `CoordVal.countsAsFinite`
carries all three: `.numeric v ↦ v.isFinite`, `.unweighable _ ↦ true`,
`.missing ↦ false`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `arg : CoordArg` (the selection subject) | the coordinate argument `x0` / `xconv` | R | two-shape argument ↔ `CoordArg` bijection (mapping.md); `.sequence` ↔ a 1-D numeric array-like, `.single` ↔ one lone non-iterable coordinate |
| 2 | `.single v => return (some v)` | `_safe_first_finite(x0)` raises `TypeError` on a non-iterable → `except (TypeError, IndexError, KeyError): pass` leaves `x0` bound to the argument itself | A-reference | the unchanged first-finite callee's behavior on a NON-ITERABLE argument, modeled deeply as the identity; validated == the real callee (`TypeError` ⇒ argument unchanged) by G-AX. No finiteness test is applied on this route — measured: a lone `nan` selects `nan`, a lone `datetime` selects that `datetime` |
| 3 | `for v in vs do … if v.isFinite then return (some v)` | `cbook._safe_first_finite(seq)` = `next(v for v in seq if isfinite(v))` | A-reference | the unchanged first-finite callee on a SEQUENCE, modeled deeply (scan to first finite); validated == `_safe_first_finite(_, skip_nonfinite=True)` by G-AX |
| 4 | `CoordVal.countsAsFinite` (three arms) | `cbook.safe_isfinite(v)` | A-reference | the real ruling, per REGIME, NOT bare arithmetic finiteness: weighed by `np.isfinite` for a scalar numpy can weigh, `True` unconditionally for one it cannot (its `TypeError` ⇒ `True`, and the `np.isscalar` guard's `else: return True`), `False` for `None`. Validated == the real closure by G-AX, whose section 1 reads the ruling OFF the helper observably (`[v, finite-sentinel]`) rather than asserting a transcription, and whose sequence lane now fuzzes MIXED-REGIME sequences verbatim instead of coercing them through `np.asarray(dtype=float)` |
| 4b | `CoordVal` (the element domain) | one element of the coordinate argument | R | three-regime element ↔ `CoordVal` bijection (mapping.md): `.numeric` ↔ a scalar numpy can weigh as a quantity, `.unweighable` ↔ anything else present (a `datetime`, a `timedelta`, a `Decimal`, a `str`, a nested sequence, a 0-d array), `.missing` ↔ `None` |
| 5 | falling out of the loop with no `some` (no finite `v`) | the generator is exhausted → `next(...)` raises `StopIteration` → `except StopIteration:` taken | I | the loop-exhaustion path IS the exception branch; structurally identical control flow, and reachable only for an ITERABLE argument, which row 1's `.sequence` constructor is what makes precise |
| 6 | `return vs.head?` | `cbook.safe_first_element(seq)` = `next(iter(seq))` = `seq[0]` on non-empty; nothing when empty | A-reference | the unchanged fall-back callee, modeled deeply as first element; validated == `safe_first_element` (non-empty numeric) by G-AX. Note this op sits inside the `.sequence` arm ONLY, mirroring the call sitting on the `StopIteration` handler ONLY |

No A-consumed rows: the proof discharges `chooseRepresentative` directly; no
UNCHANGED callee property is assumed as an axiom. No changed-inexpressible op.

## Why each element's REGIME is a modeled op and not a modeling convenience
Row 4 is the second correspondence whose PRECISION the model has to express, and
the reason is the same in kind as row 1's. `safe_isfinite` is not a numeric
predicate that happens to be called on numbers; it is a THREE-WAY ruling, and the
two non-arithmetic rulings are the ones the real callers exercise. `bar()` and
`barh()` pass `x0 = x` VERBATIM — only `xconv` is the `np.asarray`'d one — so a
list of `datetime` objects reaches the search un-coerced.

MEASURED (real callees reconstructed from the base worktree at `af39f1e`, `cbook`
unchanged by the patch), correct behavior vs. the bare-arithmetic substitution:

| argument | correct | bare `np.isfinite` |
|---|---|---|
| `[datetime, datetime]` | representative `datetime` | **`TypeError` escapes the search** |
| `[datetime, 2.0]` | representative `datetime` | **`TypeError` escapes** |
| `[timedelta, datetime]` | representative `timedelta` | **`TypeError` escapes** |
| `[Decimal('1.5'), 2.0]` | representative `Decimal('1.5')` | **`TypeError` escapes** |
| `['a', 2.0]` | representative `'a'` | **`TypeError` escapes** |
| `[None, 2.0]` | representative `2.0` | **`TypeError` escapes** |
| `[nan, 2.0]` | representative `2.0` | representative `2.0` (agrees) |
| `[nan]` | representative `nan` | representative `nan` (agrees) |

When the substituted predicate raises, the inner
`except (TypeError, IndexError, KeyError)` swallows it and leaves the argument
bound to the WHOLE LIST; the subsequent `x0 + ddx` on a list then raises, escapes
to the outer `except (ValueError, TypeError, AttributeError)`, and the
coordinate-plus-offset arithmetic is silently discarded. `test_bar_timedelta`
drives `ax.barh([datetime, datetime], …, height=timedelta)` and so drives exactly
the first row.

A `List Float` element carrier has no image of the left column's first six rows,
so an extensional equality over it admits the substitution. `CoordVal` gives each
regime a constructor, which turns the divergence into a value the postcondition
pins: the substitution now has to choose between contradicting the
`.unweighable ↦ counts` clause (rejected — see the `weak-unweighable-skipped`
battery rival) and applying the real three-way ruling, which is the correct
behavior. The converse mis-ruling — counting a `.missing` value — is pinned by the
`weak-missing-counted` rival, so the model pins all three arms and not two.

## Why the argument's shape is a modeled op and not a modeling convenience
Rows 2 and 6 are the two arms whose SEPARATION the model has to express. In the
real code, `safe_first_element` is reachable only from the `StopIteration`
handler, so it never receives a non-iterable argument; it is PARTIAL, and
`next(iter(obj))` raises `TypeError` on a lone coordinate. An implementation that
relocates that call — hoisting it above the `try`, attaching it to the
`TypeError` handler, or narrowing that handler — is denotationally identical on
every sequence and diverges on exactly the lone-coordinate shape, where the
`TypeError` escapes the inner handler, is caught by the outer
`except (ValueError, TypeError, AttributeError)`, and silently discards the
coordinate-plus-offset arithmetic.

MEASURED (real callees reconstructed from the base worktree; `cbook` is unchanged
by the patch), correct behavior vs. the hoisted relocation:

| argument | correct | hoisted |
|---|---|---|
| lone `1.0` | representative `1.0` | **`TypeError` escapes** |
| lone `nan` | representative `nan` | **`TypeError` escapes** |
| lone `datetime(2018,1,1)` | representative `datetime(2018,1,1)` | **`TypeError` escapes** |
| lone 0-d ndarray | representative `array(1.)` | **`TypeError` escapes** |
| `[nan]` | representative `nan` | representative `nan` (agrees) |
| `[nan, 2.0]` | representative `2.0` | representative `2.0` (agrees) |
| `[1.0]` | representative `1.0` | representative `1.0` (agrees) |

A carrier without the argument's shape has no image of the left column's first
four rows, so it cannot see the divergence, and an extensional equality over it
admits the relocation. `CoordArg` gives that regime a constructor, which turns the
divergence into a value the postcondition pins: the relocation now has to choose
between contradicting the lone-value clause (rejected — see the
`weak-single-filtered` battery rival) and guarding itself so that it only ever
runs for a sequence, which is the correct behavior. Two existing regression tests
(`test_bar_timedelta`, `test_broken_barh_timedelta`) drive precisely the
lone-date-coordinate configuration, which is why the relocation regresses the
suite while still passing the F2P.

## Discriminating clause (G-DIFF)
Row 6 is the fix. The prepatch impl omits the non-empty fall-back: on a
non-empty sequence in which nothing counts as finite it `return none` where the
spec (`chooseRepresentative`) requires `vs.head?` = `some vs[0]`. Concretely
`.sequence [.numeric nan] ↦ none` (prepatch) vs `.sequence [.numeric nan] ↦
some (.numeric nan)` (spec), so
the prepatch `correct_safeRepresentative` cannot close against the frozen
`problem_spec_safeRepresentative`. Measured: substituting the prepatch impl while
KEEPING the gold proof body fails with a genuine `Tactic rfl failed` on the
`sequence.none` case, not a tactic accident. That is the G-DIFF signal, and it
mirrors the F2P `test_bar_all_nan` (a single-nan bar that previously crashed).
The lone-value clause is NOT the discriminator — it is identical pre- and
post-patch (measured: `SAME` on every lone-coordinate input) — which is exactly
why adding it strengthens the spec without disturbing the fix's delta. The same
holds of the three-regime ruling (row 4/4b): `safe_isfinite` is a callee the patch
does not touch, so its three rulings are byte-identical pre- and post-patch, and
pinning them strengthens the spec on an axis ORTHOGONAL to the delta rather than
restating it. Measured: substituting the prepatch impl still fails at the
`sequence.none` case on the widened carrier, so the discriminator is unmoved.
