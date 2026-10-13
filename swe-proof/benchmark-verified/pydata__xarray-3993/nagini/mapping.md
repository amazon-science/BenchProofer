# mapping.md — pydata__xarray-3993

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8cc34cb412ba89ebca12fc84f76a9e452628f1bc`, states the type
abstraction, and records the provenance of the (only) callee the modeled
function delegates to.

Repo files under change: `xarray/core/dataarray.py`, `xarray/core/dataset.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_coordinate(coord, dim)` | `DataArray.integrate(self, …)` — `xarray/core/dataarray.py:3483` (body line 3531) | the modeled changed function: the selector-routing prologue of the integration entry point |
| `Routed.coord` | the coordinate value passed to `self._to_temp_dataset().integrate(coord, datetime_unit)` (post-patch `dataarray.py:3551`) | the coordinate the integration is carried out along |
| `Routed.deprecated` | whether `warnings.warn(msg, FutureWarning, stacklevel=2)` fired (post-patch `dataarray.py:3548`) | the deprecation signal emitted on a legacy-selector-only call |
| `ConflictingSelection` (exception) | the `raise ValueError("Cannot pass both 'dim' and 'coord'. …")` (post-patch `dataarray.py:3537-3539`) | the refusal raised when both selectors are supplied |

The function `select_coordinate` corresponds to the routing PROLOGUE the gold adds
to `DataArray.integrate` before the final delegation
`self._to_temp_dataset().integrate(coord, datetime_unit)`. The downstream
`Dataset.integrate` / `_integrate_one` (the actual trapezoidal numerics) is
UNCHANGED by the gold (its hunk is docstring + type-annotation only — see §3)
and is not observed by this specification.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a coordinate selector (`Hashable`, e.g. the string `"x"`), or the Python default `None` | `Optional[int]`: an `int` identifier when supplied, `None` when not | each distinct selector value ↔ a distinct `int`; "argument not supplied / its default `None`" ↔ `None`. Only `is None` / `is not None` and identity equality of the chosen selector are observed — never the selector's internal structure, so any injective encoding suffices. |
| `raise ValueError("Cannot pass both 'dim' and 'coord'. …")` | `raise ConflictingSelection()` (user-defined) | builtin-exception `Exsures` crashes the Nagini translator; a user-defined class stands in. Only the fact-of-raise on the both-supplied input is observed, which the F2P/repo conflict semantics require. |
| `warnings.warn(msg, FutureWarning, stacklevel=2)` (a side-effecting signal, no value) | the boolean field `Routed.deprecated` set on the returned outcome object | the warning is a pure observable "a `FutureWarning` was emitted on this call"; modeled as a boolean carried out of the routing. `pytest.warns(FutureWarning)` observes exactly this fact (F2P `test_integrate`). |
| `self._to_temp_dataset().integrate(coord, datetime_unit)` then `_from_temp_dataset` (the integration itself) | omitted — identity on the routing outcome | the numerics are unchanged and independent of the routing decision; the F2P test asserts only that the warning fires and that the call still succeeds with `dim` routed into `coord`. Modeled as: the resolved coordinate is carried as `Routed.coord`. |
| `datetime_unit` argument | omitted | passed straight through to the unchanged downstream; not touched by the routing change and not observed by F2P. |
| the call COMPLETES: the honoured call returns its result / the refused call raises (ordinary Python evaluation of a straight-line prologue) | `Requires(MustTerminate(2))` on `select_coordinate` (and measure 1 on the `Routed` constructor it invokes) | the real prologue is loop-free straight-line code, so every call terminates; the obligation pins that an implementation may not DIVERGE instead of answering (without it a non-terminating body satisfies every `Ensures` vacuously — the audit's P1 witness hung the real F2P/P2P suite for 300s and still verified). |

`coord` is the primary selector (new positional/keyword, default `None`); `dim`
is the legacy selector (now keyword-only, default `None`). The model names them
identically (`coord`, `dim`) because the public `problem_statement` already
names both `coord` and `dim` as the two competing argument names (it literally
shows `ds.integrate(coord='x')` and `da.integrate(dim='x')`), so these two
identifiers are public vocabulary, not a leak. The model does NOT name the
patched method/class/module (`integrate`, `DataArray`, `Dataset`, the file
paths) in any spec-view identifier or comment.

## 3. Callee / co-change provenance

### 3.1 No axiomatized callee
The routing decision reads only its two `Optional[int]` selector arguments and
is modeled **deeply** (the spelled-out `if` cascade in the impl region). There
is therefore **no `@ContractOnly` axiom** and **no A-reference deep model** of
any library callee: the only thing the changed prologue does that this
specification observes is its own three-way routing decision and the two signals
it raises. Everything downstream (`_to_temp_dataset`, `Dataset.integrate`,
`_integrate_one`, `numpy.trapz`) is unchanged, independent of the routing, and
unobserved — so nothing is axiomatized. (`axiom_check.py` consequently has no
axiom to fuzz; it instead replays the routing decision table to confirm the deep
model matches the gold control flow exactly — see §3.3.)

### 3.2 The co-changed second site is behaviourally inert
The gold also edits `Dataset.integrate` (`xarray/core/dataset.py:5966`), but
that hunk changes ONLY the function's docstring and adds a return-type
annotation / `Union[Hashable, Sequence[Hashable]]` parameter annotation — its
runtime behaviour (`if not isinstance(coord,(list,tuple)): coord=(coord,); …
_integrate_one`) is unchanged. It introduces no independently-observable
behaviour, so it needs no separate modeled function and no `model_prepatch_<k>`.
(Confirmed by reading both hunks: the only `+`/`-` body lines belong to the
`DataArray.integrate` site.)

### 3.3 Soundness check (G-AX surrogate)
`axiom_check.py` is dependency-free (stdlib only — it cannot import the heavy
xarray/numpy stack inside the gate sandbox). It encodes the gold routing
control flow from `dataarray.py` post-patch as a reference oracle and asserts,
over the full enumeration of `(coord, dim) ∈ {None, present}²` plus fuzzed
identifiers, that the model's three-way decision (`raise` / route-`dim`-and-warn
/ route-`coord`) agrees with the gold prologue on the resolved coordinate, the
deprecation signal, and the refusal — i.e. that the deep routing model is the
gold's prologue. Exit 0 iff sound.
