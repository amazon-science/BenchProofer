# mapping.md — symbol binding & type bijection (matplotlib__matplotlib-24149)

## Modeled function
- **Lean** `implementation_safeRepresentative : CoordArg → Option CoordVal`
- **Python** the representative-scalar selection performed inside
  `Axes._convert_dx` — `lib/matplotlib/axes/_axes.py:2181-2197 @ af39f1e`
  (post-patch: the `x0 = cbook._safe_first_finite(x0)` block with its
  `except (TypeError, IndexError, KeyError): pass` and its
  `except StopIteration: x0 = cbook.safe_first_element(x0)` handlers, and the
  structurally identical block for `xconv`).

The function under spec is the small selection step that picks ONE scalar
representative to stand for the coordinate argument so that width/offset
arithmetic can be done on a single element rather than the whole vector. The two
patched blocks (`x0` and `xconv`) perform the SAME selection over their
respective input argument; they are one modeled behavior.

## The behavior and its bug
`cbook._safe_first_finite(seq)` returns `next(v for v in seq if safe_isfinite(v))`
— the first element that COUNTS AS FINITE under its own inner ruling, which is
NOT `np.isfinite` (see "The per-element ruling has three regimes" below). When the argument is a sequence containing NO finite
element this `next(...)` raises `StopIteration`. Pre-patch, only `(TypeError,
IndexError, KeyError)` were caught, so `StopIteration` propagated out of
`_convert_dx` and crashed `ax.bar([nan], …)`. The patch adds `except
StopIteration:` which falls back to `cbook.safe_first_element(seq)` =
`_safe_first_finite(seq, skip_nonfinite=False)`, i.e. the FIRST element of the
sequence unconditionally (`next(iter(seq))`). For a non-empty sequence that is
`seq[0]`.

## The argument has TWO shapes, and both are modeled
`_convert_dx`'s `x0` is **not** always a sequence. `bar()` passes `x0 = x`
verbatim, which is whatever the caller supplied, and `broken_barh()` passes
`xr[0]`, a single range start. So the argument inhabits two shapes, and the
patched block routes them differently:

| argument shape | what `_safe_first_finite` does | resulting selection |
|---|---|---|
| a SEQUENCE of coordinates | scans for the first finite element; raises `StopIteration` if none is finite | first finite element; else (non-empty) `seq[0]`; else nothing |
| ONE LONE coordinate (a float, an int, a `np.float64`, a `datetime`, a 0-d array) | `next(iter(obj))` raises **`TypeError`** — the object is not iterable | the `except (TypeError, …): pass` leaves `x0` **bound to the argument itself**, so the lone coordinate is its own representative, unconditionally and with no finiteness test applied |

MEASURED against the real callees reconstructed from the base worktree (the
`cbook` helpers are UNCHANGED by the patch):

```
scalar float 1.0      -> representative 1.0
scalar float nan      -> representative nan       (no finiteness filter applies)
scalar int 3          -> representative 3
np.float64(2.0)       -> representative 2.0
datetime(2018,1,1)    -> representative datetime(2018,1,1)
0-d ndarray           -> representative array(1.)
[nan]                 -> representative nan       (the patch's fall-back)
[nan, 2.0]            -> representative 2.0
[1.0]                 -> representative 1.0
[] / np.array([])     -> nothing (guarded unreachable upstream)
```

The lone-coordinate row is load-bearing, not incidental: it is the ONLY place
the placement of the `safe_first_element` call is observable. Every
mis-placement of that call (hoisting it out of the `try`, attaching it to the
`TypeError` handler, narrowing that handler) agrees with the correct behavior on
EVERY sequence and diverges on EXACTLY the lone-coordinate shape, where it turns
a successful selection into a `TypeError` that escapes to the outer
`except (ValueError, TypeError, AttributeError)` and discards the
coordinate-plus-offset arithmetic. Modeling the argument as a bare `List Float`
left that regime unobservable and admitted such an implementation; `CoordArg`
carries the shape so the divergence becomes a VALUE the postcondition pins.

So the post-patch selection is:
- (lone coordinate) that coordinate itself, unconditionally;
- (sequence) first finite element, if any exists; else
- (sequence) first element of the sequence, when non-empty; else
- (empty sequence) nothing — the surrounding `xconv.size == 0` guard means an
  empty sequence never reaches this selection with a representative, modeled as
  `none`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| the coordinate argument `x0` / `xconv` | `CoordArg` | two shapes, per the table above |
| a 1-D array-like of coordinate values (`list`, `tuple`, `ndarray`) | `CoordArg.sequence (vs : List CoordVal)` | per-element scan; total/sound indexing. Elements need NOT be numbers: `bar()`/`barh()` pass `x0 = x` verbatim (only `xconv` is `np.asarray`'d), so a list of `datetime`s reaches the scan un-coerced |
| one lone non-iterable coordinate | `CoordArg.single (v : CoordVal)` | the `TypeError`→`pass` route; the value stands for itself. A non-numeric lone coordinate (a `datetime`) takes the SAME route and is carried by the same `CoordArg` constructor, with its own `CoordVal` regime (`.unweighable`) — the regime is retained rather than abstracted away, because the search over a SEQUENCE does consult it |
| a scalar coordinate the ruling weighs | `CoordVal.numeric (v : Float)` | one IEEE-754 double |
| one element of the coordinate argument | `CoordVal` | three regimes, per "The per-element ruling has three regimes" below: `.numeric (v : Float)` ↔ a scalar `np.isfinite` can weigh; `.unweighable (tag : Nat)` ↔ any other value that is PRESENT (a `datetime`, `date`, `timedelta`, `Decimal`, `str`, nested sequence, 0-d/n-d array); `.missing` ↔ `None`. The `tag` distinguishes distinct unweighable values without modeling their internals, which the selection never inspects |
| `cbook.safe_isfinite(v)` | `CoordVal.countsAsFinite v : Bool` | the real three-way ruling: `.numeric v ↦ v.isFinite` (IEEE-754 finiteness ⇔ not NaN and not ±inf, and `np.isfinite` agrees on such scalars); `.unweighable _ ↦ true` (numpy cannot make heads or tails of it, so the helper assumes finite — both via the `np.isscalar` guard's `else` and via its `except TypeError`); `.missing ↦ false` (`val is None` is the helper's FIRST test). Modeled as a Bool predicate (kernel `Float` ORDER is opaque, but `isFinite` is a decidable Bool flag — DECISIONS.md float rule satisfied) |
| selected representative (one coordinate value) | `Option CoordVal` | `some v` when a representative is selected; `none` only for the empty sequence |
| `StopIteration` raised by `next(generator)` | `find?` returning `none` on a `.sequence` (nothing counts as finite) | the exception path IS the fall-back branch |
| `TypeError` raised by `next(iter(obj))` on a non-iterable | the `.single` constructor's arm | the exception path IS the identity route; `x0` is left unchanged |

## The per-element ruling has three regimes
`safe_isfinite` is a closure inside the unchanged `_safe_first_finite`. Verbatim at
`af39f1e`:

```python
def safe_isfinite(val):
    if val is None:
        return False                                          # MISSING
    try:
        return np.isfinite(val) if np.isscalar(val) else True  # weighed | not
    except TypeError:
        return True                                           # UNWEIGHABLE
```

So it is NOT `np.isfinite`. It agrees with `np.isfinite` on exactly the scalars
numpy can weigh, and departs from it in two directions: it COUNTS a value numpy
cannot weigh (rather than erroring or skipping), and it REFUSES `None` (which
`np.isfinite` errors on). MEASURED against this callee reconstructed from the base
worktree:

```
1.0                  counts        np.isfinite  True   (agree)
nan / ±inf           does NOT      np.isfinite  False  (agree)
None                 does NOT      np.isfinite  TypeError
datetime(2018,1,1)   COUNTS        np.isfinite  TypeError
date / timedelta     COUNTS        np.isfinite  TypeError
Decimal('1.5')       COUNTS        np.isfinite  TypeError
'abc'                COUNTS        np.isfinite  TypeError
np.asarray(nan)      COUNTS        np.isfinite  False
[1, 2] (nested)      COUNTS        np.isfinite  ValueError
```

That difference is REACHABLE as a sequence, so it is modeled rather than argued
away. Instrumentation of the real callers: `bar()`/`barh()` pass `x0 = x`
VERBATIM — only `xconv` is the `np.asarray(self.convert_xunits(x))` one — so
`ax.barh([datetime, datetime], …, height=timedelta)` delivers a LIST of
`datetime` objects straight into the scan un-coerced. `test_bar_timedelta` drives
precisely that. Modeling the ruling as bare `Float.isFinite` over a `List Float`
left the whole non-numeric element regime unobservable and admitted an
implementation that substitutes `np.isfinite` for it; `CoordVal` carries the
regime so the divergence becomes a VALUE the postcondition pins.

An earlier revision of this section claimed the F2P path feeds a numeric array so
"every element is a plain float". That premise is FALSE for the modeled block —
it holds of `xconv`, not of `x0` — and is corrected above. G-AX's sequence lane
consequently no longer coerces through `np.asarray(obj, dtype=float)` (which made
mixed-regime sequences literally unconstructible in the fuzzer), and its per-value
lane reads each ruling OFF the real helper observably.

## Callee provenance
- `_safe_first_finite` (skip_nonfinite=True) — UNCHANGED callee; on a sequence
  its observable effect ("first element that counts as finite under its own inner
  three-way ruling, else raise StopIteration") is modeled DEEPLY by
  `vs.find? (·.countsAsFinite)` over `CoordVal`, and on a lone non-iterable
  coordinate its observable effect ("raise TypeError", which the enclosing
  handler turns into "leave the argument as its own representative") is modeled
  DEEPLY by the `.single` arm. **A-reference**, validated by G-AX. Not
  axiomatized.
- `safe_first_element` = `_safe_first_finite(_, skip_nonfinite=False)` —
  UNCHANGED callee newly invoked by the patch; on a non-empty numeric sequence it
  is `next(iter(seq))` = `seq[0]`, modeled DEEPLY by `vs.head?`. It is invoked
  ONLY on the exhausted-search branch, which is why it never sees a lone
  coordinate; that call-site restriction is what the `.single` arm makes
  observable. **A-reference**, validated by G-AX. Not axiomatized.
- The CHANGED operation is the control-flow selection (add the StopIteration
  fall-back), modeled deeply as `chooseRepresentative`; nothing here is the thing
  under spec being axiomatized.

## Flag dependency
`safe_first_element` calls `_safe_first_finite` with `skip_nonfinite=False`; on a
plain (non-`np.flatiter`, non-`Iterator`) numeric sequence both reduce to
`next(iter(obj))`. G-AX exercises plain list/array/tuple sequences and lone
scalar coordinates — the configurations the F2P and P2P paths use. Generators
(`RuntimeError`) and `np.flatiter` (unfiltered `obj[0]`) are OUT of the declared
domain: `_convert_dx` opens with `assert type(xconv) is np.ndarray`, and
`np.asarray(arr.flat)` materialises to a plain ndarray.

## G-CONF fuzz seed
Pinned seed: **24149**. ≥10^5 fuzzed inputs across BOTH argument shapes — an
alphabet that oversamples non-finite sentinels (`nan`, `+inf`, `-inf`) and
ordinary finite floats for the sequence shape, PLUS mixed-REGIME sequences drawn
from an alphabet that also carries unweighable values (`datetime`, `date`,
`timedelta`, `Decimal`, `str`, 0-d array) and `None`, plus lone-coordinate cases
(finite, non-finite, integral, non-numeric) — and all-non-counting and empty
boundary cases.
