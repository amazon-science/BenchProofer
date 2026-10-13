# mapping.md — pydata__xarray-3993

Symbol binding, the Lean↔Python type bijection (G-CONF + G-AX use it), callee
provenance, flag deps, and the pinned G-CONF fuzz seed.

## Modeled function
`DataArray.integrate` — `xarray/core/dataarray.py:3483` @ base_commit
`8cc34cb412ba89ebca12fc84f76a9e452628f1bc`.

Only the argument-resolution logic of `DataArray.integrate` changed. Pre-patch its
signature was `integrate(self, dim, datetime_unit=None)` and the body was simply
`ds = self._to_temp_dataset().integrate(dim, datetime_unit); return
self._from_temp_dataset(ds)`. Post-patch the signature becomes
`integrate(self, coord=None, datetime_unit=None, *, dim=None)` and the body adds:
(a) reject when both `dim` and `coord` are supplied; (b) when only `dim` is
supplied, copy it into `coord` and raise a `FutureWarning`; then (c) call the
unchanged downstream integration along the resolved coordinate.

`Dataset.integrate` (`xarray/core/dataset.py:5966`) is touched by the gold patch
ONLY in its docstring / type annotations (`coord: str` → `coord: hashable`, a
one-line summary, an added `See also`). No behavior changes there, so it is NOT
modeled — modeling it would add an unconstrained, behavior-free function.

## Downstream callee (A-reference)
`self._to_temp_dataset().integrate(coord, datetime_unit)` — the actual
trapezoidal integration along the resolved coordinate. This is UNCHANGED by the
fix (the same `Dataset.integrate` numerics run before and after). In Solution.lean
it is the universally-quantified parameter `integrateAlong : Option α → DS`. No
property of it is consumed by the proof (the spec holds for *every* such step), so
it is an **A-reference**, not an `axiom`/`opaque` callee. There is no `axiom
<callee>_prop` and no `opaque` decl in Solution.lean.

Provenance: `xarray/core/dataarray.py` post-patch line
`ds = self._to_temp_dataset().integrate(coord, datetime_unit)` (gold). Flag deps:
none — the resolution does not branch on `datetime_unit`; `datetime_unit` is
threaded straight through to the downstream step and is therefore folded into the
opaque `integrateAlong` (it does not affect WHICH coordinate is selected).

## Type bijection (Lean ↔ Python)
| Lean | Python | note |
|---|---|---|
| `α` | the coordinate selector type (`Hashable`, or a sequence of hashable) | abstract; equality is all that is used |
| `DS` | the integrated `DataArray` result | abstract; produced only by `integrateAlong` |
| `coord : Option α` | the `coord` keyword (`None` when omitted) | `none ↔ coord is None`, `some c ↔ coord == c` |
| `dim : Option α` | the `dim` keyword-only argument (`None` when omitted) | `none ↔ dim is None`, `some d ↔ dim == d` |
| `integrateAlong : Option α → DS` | `self._to_temp_dataset().integrate(·, datetime_unit)` then `_from_temp_dataset` | the unchanged downstream integration; `integrateAlong none` models the (degenerate) call with `coord=None` |
| `Except.error ()` | the `raise ValueError("Cannot pass both 'dim' and 'coord'. …")` path | the rejected call |
| `Except.ok (v, warned)` | normal return; `warned ↔ a FutureWarning was emitted` | `warned = true ↔ the deprecation `warnings.warn(msg, FutureWarning, …)` fired |
| `coord.isSome` / `dim.isSome` | `coord is not None` / `dim is not None` | argument-presence test |

## Argument-resolution truth table (post-patch)
| `coord` | `dim` | outcome | Lean |
|---|---|---|---|
| present | present | `ValueError` | `Except.error ()` |
| absent  | present | integrate along `dim`, emit `FutureWarning` | `Except.ok (integrateAlong dim, true)` |
| present | absent  | integrate along `coord`, no warning | `Except.ok (integrateAlong coord, false)` |
| absent  | absent  | integrate along `coord=None`, no warning | `Except.ok (integrateAlong none, false)` |

The last two rows collapse into the single Lean clause `dim = none → result =
Except.ok (integrateAlong coord, false)` (with `coord` possibly `none`). The three
`problem_spec` antecedents (`coord∧dim`, `dim∧¬coord`, `¬dim`) are mutually
exclusive and exhaustive.

## G-CONF
Pinned fuzz seed: **3993**. `conformance_check.py` builds the R/I Python shadow of
`implementation_integrate` (the resolution table above, with `integrateAlong` left
as the REAL `DataArray._to_temp_dataset().integrate` callee) and differential-tests
it against the patched `DataArray.integrate` over ≥1e5 fuzzed `(coord, dim)`
configurations, comparing both the returned values and whether a `FutureWarning`
was raised. `conf_skip = false` (the impl region has genuine R/I content: the
coordinate selection + error + warning logic). Exit 0 iff zero disagreements.

## G-AX
No consumed callee axiom and no axiomatized A-reference (`integrateAlong` is
universally quantified). `axiom_check.py` is a skip stub (exit 0).
