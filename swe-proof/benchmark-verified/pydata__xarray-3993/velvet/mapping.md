# mapping.md — pydata__xarray-3993

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8cc34cb412ba89ebca12fc84f76a9e452628f1bc`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance. `spec_provenance: cold`.

Repo file under change (behavioral): `xarray/core/dataarray.py`. The companion
`xarray/core/dataset.py` hunk in the gold patch is **docstring / type-annotation
only** (it renames a parameter in the signature's type hints and rewrites prose);
it changes no runtime behaviour and is not modeled (see §3.2).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `integrateDispatch (primary : Selector) (legacy : Selector)` | the argument-resolution head of `DataArray.integrate` — `xarray/core/dataarray.py:3483` (the signature) through the call to `self._to_temp_dataset().integrate(...)` at body line 3537 | the modeled changed function: how the public entry point resolves its two selector arguments into a single forwarded coordinate (+ the advisory/rejection decisions) |
| `primary : Selector` | the primary coordinate-selector argument (post-patch the leading one) | a selector that may be supplied or left at its absent default; `none ↔` left absent / supplied as the absent sentinel, `some k ↔` supplied with name tag `k` |
| `legacy : Selector` | the legacy coordinate-selector argument (kept, keyword-only post-patch) | same carrier as `primary` |
| `Dispatch` (struct: `forwarded`, `advisory`) | the resolved `(coord, warn?)` pair the head computes before calling the integrator | `forwarded ↔` the single coordinate value handed to `self._to_temp_dataset().integrate(coord, ...)`; `advisory ↔` whether a deprecation `FutureWarning` is emitted |
| `DispatchErr.bothSupplied` | the `ValueError("Cannot pass both ...")` raised when both selectors are supplied | the rejection of a contradictory call |
| `resolve` | the two-`if` resolution head + the forwarding call (the pure decision the method implements) | pure spec the method's `ensures` pins |

The pre-patch repo shape the change replaces (refinement audit only, not named
in the consumer spec view): `DataArray.integrate(self, dim, datetime_unit=None)`
took a single **required positional** selector, forwarded it verbatim, and
emitted no advisory and rejected nothing.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a selector argument (`coord` / `dim`) | `Selector = Option Nat` | argument left absent **or** supplied as `None` ↔ `none`; argument supplied with coordinate name `s` ↔ `some (id s)`, `id` any injective name tag. The dispatch only asks "was this selector supplied (non-`None`)?" and forwards its value verbatim, so a `Nat` tag is a faithful, total carrier. **`None` and "absent" collapse to `none`** because the real head's tests are exactly `coord is not None` / `dim is not None`. |
| the resolved forwarded coordinate | `Dispatch.forwarded : Nat` | the single value handed to `self._to_temp_dataset().integrate(coord, datetime_unit)`; G-CONF forwards the chosen name to the SAME real integrator on both sides, so only the *choice* is under test |
| the deprecation `FutureWarning` | `Dispatch.advisory : Bool` | `true ↔` exactly one `FutureWarning` is emitted by the call; `false ↔` none is |
| both selectors supplied (each non-`None`) | `Except.error .bothSupplied` | the real `ValueError("Cannot pass both 'dim' and 'coord'. ...")` |
| neither selector supplied (both `None`) | `Except.ok none` | no coordinate is forwarded; downstream this refines to forwarding `None` to the unchanged integrator, which then raises `ValueError("Coordinate None does not exist.")` — both sides observe an error (refinement.md §A row 4) |
| `datetime_unit`, the array data, dims, attrs | dropped | unchanged by this patch and never inspected by the resolution head; the integration result is observed only as a signature that *distinguishes which coordinate was forwarded* (G-CONF), so richer structure is observationally irrelevant and not modeled (avoids over-claiming) |

## 3. Callee provenance

### 3.1 No axioms, no deep-model references (G-AX skip)
This bundle has **no consumed axioms and no A-reference deep models**, so it ships
**no `axiom_check.py`** (meta.json `gates.G-AX.status = "skip"`). Rationale: the
only downstream callee the head reaches — the trapezoidal integrator
`self._to_temp_dataset().integrate(coord, datetime_unit)` (i.e.
`Dataset.integrate` → `_integrate_one`) — is **unchanged** by this patch, and the
change never alters *what* the integrator computes, only *which coordinate value
is forwarded to it* and *whether an advisory/rejection precedes it*. The
integrator's behaviour is observed only **through** the forwarded selector, which
is the input carrier (SPEC_GUIDE §0.8: ground the postcondition in the inputs).
There is therefore nothing to axiomatize and no callee equivalence to validate.
G-CONF forwards the chosen coordinate to the real integrator on **both** the
shadow and the oracle, so the integrator cancels out and only the dispatch
decision is differentially tested.

### 3.2 The `Dataset.integrate` hunk is non-behavioral
The gold patch's second file hunk (`xarray/core/dataset.py:5963`) changes only
`Dataset.integrate`'s **signature type annotations and docstring** (it adds
`Union[Hashable, Sequence[Hashable]]` / `-> "Dataset"` hints and rewrites prose);
the runtime body is byte-identical. No F2P/PASS_TO_PASS behaviour depends on it,
so it is carried verbatim in `patch.diff` (for G-RESOLVE) but is **not modeled**
and contributes no separate prepatch (a docstring change is unobservable to the
spec and cannot produce a discriminating failing prepatch).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`3993`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates `resolve`
(the whole impl region is R/I — no A-tagged callee) and bridges I/O via the §2
bijection, forwarding the resolved coordinate to the real (unchanged) integrator
on both sides. It diffs the shadow against `patch.diff`'s patched
`DataArray.integrate` behaviour — projected onto (error?, forwarded-signature,
advisory-raised?) — over ≥10⁵ fuzzed `(coord, dim)` selector pairs spanning
absent / `None` / named, including the F2P scenario `da.integrate(dim="x")`.
