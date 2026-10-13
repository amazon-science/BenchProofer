# mapping.md — matplotlib__matplotlib-13989

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = <see meta.json>`, states the type abstraction (the bijection
G-CONF uses to bridge Lean↔Python), and gives the provenance of each modeled
callee.

Repo file under change: `lib/matplotlib/axes/_axes.py` (method `Axes.hist`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildHistOptionsM (boundsOpt) (density) (accumulate)` | the assembly of the local `hist_kwargs` mapping inside `Axes.hist` — `lib/matplotlib/axes/_axes.py:6654` (init), `:6685` (bounds entry), `:6688–6689` (density entry) | the modeled operation: building the per-histogram keyword-option mapping passed to `np.histogram` |
| `HistOptions` (structure) | the `hist_kwargs` dict as it stands when it reaches the histogram call (`:6698` `np.histogram(..., **hist_kwargs)`), reduced to the two entries this assembly decides | the option mapping carrier |
| `HistOptions.boundsOpt : Option (Float × Float)` | the `'range'` entry of `hist_kwargs` (`hist_kwargs['range'] = bin_range`, `:6685`); `bin_range` is the `(xmin, xmax)` 2-tuple | presence + identity of the explicit lower/upper data-bounds entry |
| `HistOptions.densityOpt : Option Bool` | the `'density'` entry of `hist_kwargs` (set at `:6689`) | presence + value of the normalize-to-a-density entry |
| `density : Bool` | the local `density` bool at `:6688` (`density = bool(density) or bool(normed)`) | whether this computation normalizes to a density |
| `accumulate : Bool` | the local `stacked` bool at `:6688` (the `if density and not stacked:` guard) | whether the histograms are accumulated on top of each other |
| `buildHistOptions` (pure) | the post-patch assembly logic of lines `:6654`–`:6689` | pure deep model of the option-mapping assembly |

The selection, in source order at base_commit (the **pre-image** still
*replaces* the whole mapping at line 6689 — the bug):

```python
        hist_kwargs = dict()                       # :6654   (densityOpt = none, boundsOpt = none)
        ...
        if not input_empty and len(x) > 1:
            ...                                    # multi-dataset path (not modeled — see §2)
        else:
            hist_kwargs['range'] = bin_range       # :6685   (boundsOpt := some bounds)

        density = bool(density) or bool(normed)    # :6688
        if density and not stacked:
            hist_kwargs = dict(density=density)     # :6689   PRE-IMAGE (BUG): REPLACES the dict,
                                                    #         discarding any 'range' entry set at :6685
        # POST-IMAGE (fix):  hist_kwargs['density'] = density   # ADDS the entry, keeps 'range'
        ...
        m, bins = np.histogram(x[i], bins, weights=w[i], **hist_kwargs)   # :6698
```

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean domain
and the Python repo. A wrong entry surfaces as spurious G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `hist_kwargs` dict reaching `np.histogram` (`:6698`), reduced to its `'range'`/`'density'` entries | `HistOptions` | `'range' in d` ↔ `boundsOpt = some _`; `d['range']` ↔ the `(lo, hi)` payload; `'density' in d` ↔ `densityOpt = some _`; `d['density']` ↔ the payload bool. The two entries are the only ones this assembly writes, so they are the only fields modeled. |
| `bin_range`, a `(xmin, xmax)` float 2-tuple (`:6685`) | `Option (Float × Float)` | a present `'range'` entry ↔ `some (lo, hi)`; absent ↔ `none`. The numeric values are carried **opaquely** (this assembly never inspects them); only presence + identity matter. `some` ↔ key-present, payload preserved verbatim. |
| local `density` bool (`:6688`) | `Bool` | `True ↔ true`, `False ↔ false` |
| local `stacked` bool (the `not stacked` guard, `:6688`) | `Bool` (`accumulate`) | `True ↔ true`, `False ↔ false` |

**Scope (modeled vs out-of-scope branches).** The F2P test
`test_hist_range_and_density` is a single dataset (`plt.hist(np.random.rand(10),
…)`) → `len(x) == 1`, so it takes the `else` branch at `:6685` that sets the
`'range'` entry, with `stacked == False` and `density == True`. That is exactly
the `boundsOpt = some _, density = true, accumulate = false` modeled case. The
multi-dataset branch (`len(x) > 1`, `:6680`) routes the range through
`histogram_bin_edges` instead of via `hist_kwargs` and is not the bug site; it
is collapsed into the input (a caller that did NOT set the `'range'` entry is
modeled by `boundsOpt = none`) and is not separately modeled. The
`stacked and density` stacked-normalization at `:6705` is downstream of the
mapping assembly and unchanged.

## 3. Callee provenance (no axioms)

None. The modeled operation is the **pure assembly** of the option mapping — a
dict construction and a single conditional key write — modeled deeply as
`buildHistOptions`. The downstream consumer `np.histogram(..., **hist_kwargs)`
(`:6698`) is **unchanged** by the patch: its documented contract (when a
`range=(lo, hi)` keyword is supplied, the returned bin edges span exactly
`[lo, hi]`) is the same before and after, so the fix's whole effect is to STOP
discarding that keyword. `np.histogram` is therefore not modeled and owed no
contract here — it is the real correctness oracle exercised by G-RESOLVE (the
F2P test asserts `bins[0] == 0` and `bins[-1] == 1`). There is no A-consumed
axiom and no A-reference deep model of an outside callee — `meta.json axioms =
[]`, `deep_model_references = []`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **13989**. The R/I shadow
is the modeled assembly `buildHistOptions` transliterated to Python over a real
`dict` (the `hist_kwargs` carrier); the oracle is the **patched** assembly block,
transliterated verbatim from the post-image of `Axes.hist` (lines 6654–6689) —
`hist_kwargs = dict(); … ; hist_kwargs['range'] = bin_range; … ; if density and
not stacked: hist_kwargs['density'] = density`. Both are exercised over the full
finite control space (presence/absence of the bounds entry × `density` ×
`stacked`) plus seeded fuzz of the opaque bounds payload. See the
`conformance_check.py` docstring for why the real `Axes.hist` is not driven
end-to-end in-container (it needs a live Figure/Axes + a backend merely to read
back which keyword survives into `np.histogram`).
