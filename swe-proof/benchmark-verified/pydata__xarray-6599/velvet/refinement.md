# refinement.md — pydata__xarray-6599

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`toNumeric` `do` block, with the deep `epochCount`/`durationCast` models in the
`pure` region) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (modeled callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so a verifying
implementation must TERMINATE and return `toNumericSpec t`. (An earlier
revision used partial correctness, which a same-spec diverging implementation
— an infinite loop with a trivial invariant — would vacuously satisfy; total
semantics excludes that whole class. The real `to_floatable` is a straight-line
kind dispatch over a finite array — `datetime_to_numeric` / `astype(float)` /
pass-through — that always returns, so total correctness is the faithful
semantics.)

## A. The conversion site — `to_floatable()` (`xarray/core/computation.py:1935`)

Gold hunk:
```
-        if x.dtype.kind in "mM":
+        if x.dtype.kind == "M":
+            # datetimes
             return x.copy(data=datetime_to_numeric(x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns"))
+        elif x.dtype.kind == "m":
+            # timedeltas
+            return x.astype(float)
         return x
```

| # | Solution.lean impl op (`toNumeric`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `t : TypedArr` (`kind`, `raw`) | `x: DataArray` arg of `to_floatable` | R | `DataArray` ↔ `TypedArr`: only `x.dtype.kind` and the int carrier `x.data` are observed (mapping.md §2). |
| A2 | `match t.kind with .datetime => …` | `if x.dtype.kind == "M":` | I + R | the datetime branch of the changed dispatch. `kind == "M"` ↔ `.datetime` (R). Concrete branch test (I). |
| A3 | `epochCount t` (= `.ok (raw.map (missing → .nan, else .num))` on datetime, `.error` on duration) | `x.copy(data=datetime_to_numeric(x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns"))` | A-reference | the unchanged epoch-relative callee, modeled deeply; equals the real `datetime_to_numeric` with the pinned offset/unit — incl. NaT → nan (mapping.md §3.1), validated by G-AX. NOT a consumed axiom. |
| A4 | `match … .duration => Except.ok (durationCast t)` | `elif x.dtype.kind == "m": return x.astype(float)` | I + R + A-reference | the **new** duration branch — the heart of the fix. `kind == "m"` ↔ `.duration` (R, I dispatch); `durationCast t` is the deep model of `x.astype(float)` (A-reference, mapping.md §3.2), `== .ok (t.raw.map .num)` (the plain ns counts, NaT count NOT special-cased). |
| A5 | `match … .numeric => Except.ok (t.raw.map .num)` | `return x` (the trailing fall-through) | I + R | an already-numeric array passes through unchanged; `x` returned as-is ↔ `.ok (t.raw.map .num)`. |

Discriminating content of the change — a **duration** (timedelta) array must be
routed to the direct float cast (`durationCast`, yielding `.ok (t.raw.map
.num)`), NOT to the epoch-relative conversion (`epochCount`, which is `.error
.illTypedForDuration` on a duration). The pre-patch code tested
`x.dtype.kind in "mM"`, sending BOTH time kinds through `datetime_to_numeric`;
on a timedelta array `array - offset` raises `_UFuncBinaryResolutionError` (the
issue's traceback) and the polyval result is wrong/unobtainable.
`Solution_prepatch.lean` reproduces that (both time kinds → `epochCount`) and
**fails** `out = toNumericSpec t` on the duration case (G-DIFF), because the spec
demands `.ok (durationCast t)` there while the prepatch produces `.error`.

## B. No second independently-fixed behavior

The patch is a single dispatch change in one nested helper; the datetime branch
(A3) is behaviour-preserving (gold keeps `datetime_to_numeric` for `M`), and the
numeric fall-through (A5) is unchanged. The only newly-correct behavior is the
duration branch (A4). One `Solution_prepatch.lean` suffices.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operations that genuinely *changed* —
the kind dispatch (A2/A4) and the new duration cast (A4) — are modeled
**directly** (the `match` on `t.kind`, the `durationCast` deep model), not hidden
behind an axiom about the function under change. There are **no consumed
axioms**: both `epochCount` and `durationCast` model **unchanged** callees and
are A-references validated by G-AX.

## D. verify(Solution) ⇒ resolved

`toNumeric` verifies only if its output equals `toNumericSpec t`, which routes a
duration to `.ok (durationCast t)` and a datetime to `epochCount t` (A3/A4). By R
(`DataArray ↔ TypedArr`, kind-char ↔ `Kind`, int-carrier ↔ float values with
`NumVal.nan` ↔ the nan a NaT datetime converts to) the verified function equals
the patched `to_floatable` on the tested arrays; by G-AX the deep models
`epochCount`/`durationCast` equal the real `datetime_to_numeric` /
`astype(float)` (A-references, incl. NaT-bearing arrays); by G-CONF the R/I
transliteration of the kind dispatch agrees with `patch.diff`'s behaviour on
≥10⁵ inputs (incl. NaT-bearing). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE,
`test_polyval[timedelta-False]`). Trust points are exactly the two of plan §1.1:
A-reference soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
