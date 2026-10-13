# refinement.md — pydata__xarray-6599

The operation-by-operation correspondence between `model.py`'s implementation
(the `to_floatable` impl region, the deep `magnitude_read` model, and the live
`elapsed_since` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`/`Requires`, and **A-reference**,
where a deep model is validated == the real operation by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The conversion-dispatch site — `to_floatable` (`computation.py:1935`)

Gold hunk:
```
- if x.dtype.kind in "mM":
+ if x.dtype.kind == "M":
+     # datetimes
      return x.copy(data=datetime_to_numeric(x.data,
                    offset=np.datetime64("1970-01-01"), datetime_unit="ns"))
+ elif x.dtype.kind == "m":
+     # timedeltas
+     return x.astype(float)
  return x
```

| # | model.py impl op (`to_floatable`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `kind: int` ∈ {`OTHER`,`TIME_POINT`,`TIME_SPAN`} | `x.dtype.kind` ∈ {numeric, `"M"`, `"m"`} | R | dtype-kind code ↔ int tag: `"M"` ↔ `TIME_POINT`, `"m"` ↔ `TIME_SPAN`, else `OTHER` (mapping.md §2). |
| A2 | parameter `values: List[int]`, spec over `ToSeq(values)` | `x.data` / `x` (the variable's numpy array of magnitudes) | R | numpy array ↔ `List[int]` of base-resolution magnitudes (mapping.md §2). |
| A3 | branch `if kind == TIME_POINT:` → return `elapsed_since(kind, ToSeq(values), reference)` materialized into a list | `if x.dtype.kind == "M":` → `x.copy(data=datetime_to_numeric(x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns"))` | A-consumed + R | the timestamp branch calls the **unchanged** callee `datetime_to_numeric`; modeled by the `elapsed_since` axiom (the per-element subtraction of the reference instant, on its NaT-free domain — `Requires(well_defined_magnitudes(values))`, mapping.md §3.1). The proof consumes its `Ensures`. `x.copy(data=...)` is the identity on value content (R, mapping.md §2). G-AX checks `elapsed_since` == real `datetime_to_numeric` (reference 0) on the NaT-free domain, and that the callee deviates (nan) on the excluded `-2**63` sentinel so the domain exclusion is necessary. |
| A4 | branch `elif kind == TIME_SPAN:` → return `magnitude_read(ToSeq(values))` (== `ToSeq(values)`) | `elif x.dtype.kind == "m":` → `x.astype(float)` | A-reference | the duration branch's `astype(float)` is the **new/changed operation**, modeled **deeply** by the `@Pure` `magnitude_read` (the identity on ns magnitudes), NOT behind a consumed axiom. The deep model is validated **== the real op** out-of-band: G-AX runs `timedelta64[ns].astype(float)` and asserts it equals the raw magnitudes (mapping.md §3.2). |
| A5 | branch `else:` → return `values` unchanged | `return x` (the trailing passthrough) | I | already-numeric values pass through; literal identity on the value content. |

## B. The decisive behavioural change (what the spec senses — G-DIFF)

The pre-patch single guard `if x.dtype.kind in "mM":` routed **both** timestamps
and durations into `datetime_to_numeric(..., offset=np.datetime64("1970-01-01"),
...)`. The patch splits this: only `"M"` keeps the measurement, and `"m"` gets
its own `astype(float)`.

In the model, `elapsed_since` (the unchanged callee = the measurement) carries
`Requires(kind == TIME_POINT)` — it is defined only for timestamps, because in
reality `datetime_to_numeric` with a `datetime64` offset performs
`timedelta64 - datetime64`, which raises `UFuncTypeError` for a duration
(mapping.md §3.1; reproduced in the issue thread). `model_prepatch.py`
reproduces the bug exactly: its branch `if kind == TIME_POINT or kind ==
TIME_SPAN:` routes a `TIME_SPAN` input into `elapsed_since(kind, ...)`, whose
precondition `kind == TIME_POINT` then **might not hold** — verification fails
on precisely that clause. That is the spec sensing the change: a duration must
NOT be sent through the timestamp measurement.

The value side is pinned too: the post-state requires, for a `TIME_SPAN` input,
`ToSeq(Result()) == ToSeq(values)` (the magnitude read), so a fixed impl that
routes durations away from the measurement but returns wrong values would also
fail.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed/was added*
— the duration branch's `astype(float)` — is modeled **deeply** (the spelled-out
identity `magnitude_read` consumed in `to_floatable`, step A4, an
**A-reference**), not hidden behind an axiom about the changed operation. The
only consumed axiom, `elapsed_since` (**A-consumed**, step A3), covers the
**unchanged** callee `datetime_to_numeric` the timestamp branch invokes — and its
soundness-critical content is its **precondition** (`Requires(kind ==
TIME_POINT)`: the measurement is undefined for durations), which is the very
fact the bug violates. The duration `astype(float)` appears only as the
**A-reference** that G-AX validates the deep model against.

## D. Float-as-int soundness (R justification for §2)

The conversion's output is `float64`, modeled as `int`. This is sound here
because the behaviour under test is precision-independent: the F2P magnitudes
(`1000, 2000, 3000` ns) and the P2P datetime magnitudes (`0, 1e9, 2e9` ns) are
exact integers whose float images are integer-valued, and the bug is a
*type-applicability* error (duration sent through an instant-only measurement),
not a rounding difference. No tested input distinguishes the buggy from the
fixed behaviour by precision; the discriminator is which branch runs and whether
the measurement is applicable. (SPEC_GUIDE §2: int-scaled float is permitted
when refinement.md shows precision-independence — shown here.)

The same exact-integer band underlies the `elapsed_since` axiom's domain. For
the int model to be precise, `|magnitude| < 2**53` (above that `astype(float)`
loses precision; this is the panel's MINOR 1, bounded and not test-reachable —
the tested magnitudes are tiny). And the not-a-value sentinel `-2**63` is
*excluded* from the timestamp measurement's domain by
`Requires(well_defined_magnitudes(values))` (mapping.md §3.1): there the real
`datetime_to_numeric` returns `nan`, not the per-element subtraction, so the
axiom would over-claim without the exclusion (the panel G-AX defect). The
duration branch's `astype(float)` does NOT special-case `-2**63`, so the
`magnitude_read` deep model (A4) stays the identity on the full int64 range —
the exclusion is needed only for the timestamp path, hence the caller guards it
by `Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values)))`.

## E. verify(model) ⇒ resolved

`to_floatable` verifies only if (A3) timestamps go through the measurement
`elapsed_since` (whose precondition forbids feeding it a duration), (A4)
durations return their raw magnitudes via the deep model `magnitude_read`, and
(A5) other values pass through. By R (dtype-kind ↔ tag, numpy array ↔
`List[int]`, `copy`/float-as-int identities) the verified helper equals the gold
`to_floatable` on the tested inputs; by G-AX the axiom `elapsed_since` is sound
== real `datetime_to_numeric` **on its (NaT-free) domain** (the `-2**63` sentinel,
where the callee returns `nan`, is excluded by
`Requires(well_defined_magnitudes(values))` — confirmed necessary by
`check_sentinel_excluded`) and its precondition is honest (the callee raises
on durations), and the deep model `magnitude_read` == real `astype(float)`.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
