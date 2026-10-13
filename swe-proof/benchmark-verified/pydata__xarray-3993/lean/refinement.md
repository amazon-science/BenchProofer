# refinement.md — pydata__xarray-3993

Maps every operation in `implementation_integrate` to its `patch.diff` counterpart
in `DataArray.integrate` (`xarray/core/dataarray.py:3483`). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference** op left
as the real repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch `DataArray.integrate`, resolution branch)
```python
def integrate(self, coord=None, datetime_unit=None, *, dim=None):
    if dim is not None and coord is not None:
        raise ValueError(
            "Cannot pass both 'dim' and 'coord'. Please pass only 'coord' instead."
        )
    if dim is not None and coord is None:
        coord = dim
        msg = (... "dim ... replaced with coord ..." ...)
        warnings.warn(msg, FutureWarning, stacklevel=2)
    ds = self._to_temp_dataset().integrate(coord, datetime_unit)
    return self._from_temp_dataset(ds)
```

The behavioral content of the fix is entirely the argument resolution: reject the
contradictory pair, alias a sole `dim` into `coord` while raising a deprecation
notice, then call the UNCHANGED downstream integration along the resolved
coordinate.

## Modeling decision
The observable behavior is: (i) whether the call is rejected; (ii) which
coordinate the integration runs along; (iii) whether a deprecation notice is
raised. The downstream numeric integration
(`self._to_temp_dataset().integrate(coord, datetime_unit)` then
`_from_temp_dataset`) is identical pre- and post-patch — the fix never touches it.
So it is modeled as an arbitrary `integrateAlong : Option α → DS`, universally
quantified, and the spec pins only that the CORRECTLY-RESOLVED coordinate reaches
it, plus the error / warning logic. `datetime_unit` does not affect coordinate
selection, so it is folded into `integrateAlong` (it would only change the
downstream value, never the resolution).

## Operation correspondence
| # | Lean op (`implementation_integrate`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if dim.isSome && coord.isSome then return Except.error ()` | `if dim is not None and coord is not None: raise ValueError(...)` | R | `Option.isSome ↔ "is not None"`; the rejected call ↔ `Except.error ()`. |
| 2 | `let mut effective := coord` | `coord` is the default integration target | R | `coord : Option α ↔ the coord keyword`. |
| 3 | `let mut warned := false` | no warning by default | I | warning flag initialised off. |
| 4 | `if dim.isSome && coord.isNone then effective := dim; warned := true` | `if dim is not None and coord is None: coord = dim; warnings.warn(msg, FutureWarning, …)` | R | alias the sole `dim` into the effective coordinate AND record the deprecation notice (`warned = true ↔ a FutureWarning fired`). This is the fixed token. |
| 5 | `integrateAlong effective` | `ds = self._to_temp_dataset().integrate(coord, datetime_unit); return self._from_temp_dataset(ds)` | A-reference | the UNCHANGED downstream integration along the resolved coordinate; left abstract (universally quantified) in spec/proof and bound to the REAL callee in G-CONF. No property consumed ⇒ NOT A-consumed and NOT deep-modeled. |
| 6 | `return Except.ok (integrateAlong effective, warned)` | normal return of the integrated array (with the warning having been emitted or not) | I | package the integrated value with the notice flag. |

## R/I legs ⇒ G-CONF
Ops 1, 2, 4 (resolution + error + warning, R) and 3, 6 (flag init + return, I) are
the R/I content. Op 5 is the A-reference: G-CONF leaves it as the REAL
`DataArray._to_temp_dataset().integrate` callee (it does NOT substitute an axiom
model), which is exactly how the R/I resolution legs are isolated and tested.
`conf_skip = false`: the impl region has genuine R/I content (the resolution is the
fixed behavior), so `conformance_check.py` differential-tests the shadow
(resolution + warning detection, with the real downstream `integrate` as the value
step) against the patched `DataArray.integrate` over ≥1e5 fuzzed inputs.

## No A-consumed row
The proof consumes no property of `integrateAlong` (it is universally quantified),
so `meta.json axioms = []`. Op 5 is recorded as an A-reference solely to document
the G-CONF binding to the real callee; there is no `opaque`/`axiom` declaration in
`Solution.lean` and `axiom_check.py` is a skip stub.

## F2P alignment
`test_integrate[True]` / `test_integrate[False]` add
`with pytest.warns(FutureWarning): da.integrate(dim="x")` — i.e. the sole-`dim`
call must integrate along `x` AND raise a `FutureWarning`. The discriminating
clause `problem_spec_integrate` pins (`dim` present, `coord` absent ⇒
`integrateAlong dim` AND `warned = true`). The prepatch impl (the real bug:
`integrate` had only a `dim` arg, always integrating along it with NO warning and
NO both-supplied rejection) cannot satisfy this clause — it returns `warned =
false` and cannot discharge the `dim`-only or both-supplied antecedents — so its
carried gold proof fails to typecheck (G-DIFF). `patch.diff` (gold verbatim) makes
the harness resolve.
