# refinement.md — matplotlib__matplotlib-13989

The operation-by-operation correspondence between `model.py`'s implementation
(the `assemble_binning_options` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, the proof uses the axiom's `Ensures`, and **A-reference**, a
deep model validated == the real operation by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The kwargs-assembly site — `Axes.hist` (`lib/matplotlib/axes/_axes.py`)

Gold hunk (the single changed line, lines 6688-6689 @ base_commit):
```
  density = bool(density) or bool(normed)
  if density and not stacked:
-     hist_kwargs = dict(density=density)
+     hist_kwargs['density'] = density
```

| # | model.py impl op (`assemble_binning_options`) | patch.diff / surrounding op | tag | justification |
|---|---|---|---|---|
| A1 | `hist_kwargs = {}` | `hist_kwargs = dict()` (line 6654) | R | empty `dict` ↔ empty `Dict[int, int]`; `dict()` ↔ `{}` (mapping.md §2). |
| A2 | `if not multi_precomputed: hist_kwargs[KEY_RANGE()] = range_value` | the `else` arm `hist_kwargs['range'] = bin_range` (line 6685), taken when `not (not input_empty and len(x) > 1)` | R | the string key `'range'` ↔ `KEY_RANGE()`; the `(xmin,xmax)` value ↔ the opaque `range_value` (only its preservation is observed); the branch condition `not input_empty and len(x) > 1` ↔ the `multi_precomputed` bool (mapping.md §2). The multi-dataset arm records no range (folds it into precomputed bins), matching `multi_precomputed ⟹ KEY_RANGE() not in Result()`. |
| A3 | `if density and not stacked: hist_kwargs[KEY_DENSITY()] = 1` | gold `hist_kwargs['density'] = density` (line 6689) | R + I | the guard `density and not stacked` is **I** (identical bool control flow); `'density'` ↔ `KEY_DENSITY()` and the truthy flag value ↔ `1` are **R** (mapping.md §2). This is the IN-PLACE write the gold introduces: it adds the density entry WITHOUT discarding the range entry recorded at A2. |
| A4 | `return hist_kwargs` | the `hist_kwargs` local as forwarded to `np.histogram(..., **hist_kwargs)` (line 6698) | R | returning the assembled mapping ↔ forwarding it as keyword options; the observable downstream is which keys reach `np.histogram` (mapping.md §3.1). |

The whole assembly (A1-A4) is the **A-reference**: the changed operation is
modelled **deeply** (spelled out), and the deep model is validated **== the real
`Axes.hist` kwargs assembly + the real `numpy.histogram` observable** out-of-band
by G-AX (`axiom_check.py`), NOT consumed as an axiom. There is no `@ContractOnly`
the proof depends on.

## B. The discriminator and the prepatch

The discriminating content of the change lives in clause
`Implies(not multi_precomputed, KEY_RANGE() in Result() and
Result()[KEY_RANGE()] == range_value)` — *a recorded range survives the
recording of the density flag*.

`model_prepatch.py` reproduces the base_commit bug `hist_kwargs =
dict(density=density)` faithfully: in the `density and not stacked` branch it
**rebinds** the local to a freshly-created one-key mapping (`fresh = {}; fresh[
KEY_DENSITY()] = 1; hist_kwargs = fresh`), dropping the range entry recorded in
A2. It therefore **fails** that postcondition — exactly the spec sensing the
change (G-DIFF). The gold's in-place write keeps the range, so `model.py`
verifies.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or part of the single deep **A-reference**. The
operation that genuinely changed — whether the density branch rebinds the
options mapping (dropping `'range'`) or writes into it in place (keeping
`'range'`) — is modelled **deeply** (the two guarded writes and the rebind-vs-
write distinction are spelled out in the impl regions of the two twins), not
hidden behind an axiom about the function under change. There is **no consumed
axiom** (no A-consumed rows): the downstream histogram computation is observed
only through the public `numpy.histogram` behaviour in G-AX, not relied upon as
a frozen contract inside the proof.

## D. verify(model) ⇒ resolved

`assemble_binning_options` verifies only if the forwarded options mapping keeps the
range entry whenever the single-pass branch recorded it (A2 + the survival
clause) AND adds the density entry exactly in the `density and not stacked` case
(A3). By R (string-key ↔ int-token, `(xmin,xmax)` ↔ `range_value`, truthy flag ↔
`1`) the verified assembly equals the gold `Axes.hist` assembly on the tested
inputs; by G-AX the deep model equals the real `Axes.hist` kwargs assembly and
the real `numpy.histogram` honours the preserved range (`bins[0]==0`,
`bins[-1]==1` for the F2P call), while the dropped-range prepatch does not.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).
