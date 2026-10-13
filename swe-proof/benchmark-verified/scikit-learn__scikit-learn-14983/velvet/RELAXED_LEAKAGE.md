# RELAXED_LEAKAGE — scikit-learn__scikit-learn-14983 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition was prescribed by the bundle's own accepted P2 audit
(`verdict.md`, defect D1 and sub-review 3, verdict **RELAXED**): the audit
ACCEPTED the bundle, established the leak is semantic, genuine, and
unavoidable, and flagged that the relaxed disposition had not yet been
recorded. This file records it.

## The mismatch

The public `problem_statement` is a pure symptom report: `repr(RepeatedKFold())`
prints an object address (`<sklearn.model_selection._split.RepeatedKFold
object at 0x...>`) instead of
`RepeatedKFold(n_splits=5, n_repeats=10, random_state=None)`. Token scan of
`problem_statement`: none of {cvargs, fallback, secondary, store, attribute,
getattr, param, dict, stored} appears. It says nothing about WHERE the
displayed parameter values live on the object.

The gold fix (`patch.diff`, two hunks in `sklearn/model_selection/_split.py`):

1. add `__repr__` to `_RepeatedSplits` delegating to `_build_repr(self)`;
2. in `_build_repr`'s value loop, after `value = getattr(self, key, None)`:

```
+                if value is None and hasattr(self, 'cvargs'):
+                    value = self.cvargs.get(key, None)
```

The tested discriminator — the F2P test `test_repeated_cv_repr` pins
`RepeatedKFold(n_splits=2, n_repeats=6)` rendering
`(n_repeats=6, n_splits=2, random_state=None)`, which requires `n_splits=2`
to be sourced from the SECONDARY store `self.cvargs` because it is absent
from the instance `__dict__` — exists only in the gold diff, the hidden
test_patch, and `hints_text` (where the "params are stored in `self.cvargs`,
`getattr` returns None" diagnosis lives). `hints_text` is excluded from the
public leakage baseline.

The leaking line is the spec view's `resolveOne` docstring
(`Solution.lean` lines 16–18):

> "When the primary source yields no value and a secondary parameter store is
> present (`hasFallback`), the value is taken from that store `fallback`
> instead."

together with the `resolveOne` body's discriminating `none`-branch
(`if hasFallback then fallback.lookup key else none`) and the frozen
postcondition `out = resolveAll attrs fallback hasFallback keys`. The leak is
purely semantic — the spec view names no repo symbol (`cvargs`, `_build_repr`,
`RepeatedKFold`, `sklearn`) and quotes no diff line — so the mechanical
G-LEAK lexical screen passes; only the mechanism is disclosed.

## Why the leak is unavoidable

Faithfulness forces the fallback facet into the spec:

- The pre-patch `_build_repr` resolves values from the object's own attribute
  table ONLY (`getattr(self, key, None)`). `Solution_prepatch.lean` reproduces
  exactly that (`attrs.lookup k`) and must FAIL the frozen spec (G-DIFF) on
  precisely the keys that live only in the fallback store — that failing goal,
  `attrs.lookup k = resolveOne attrs fallback hasFallback k`, IS the
  secondary-store fallback.
- Hence any spec faithful to the post-gold behavior — one that rejects the
  prepatch bug and pins the F2P-observed values for store-only parameters —
  MUST express that a value missing from the primary source is taken from a
  secondary parameter store.
- A spec derivable from the `problem_statement` alone could pin only "repr
  shows the constructor parameters" without saying where the values come
  from; the attrs-only prepatch resolution would satisfy it (rendering
  `n_splits=None`), i.e. it admits the actual bug — a spec-too-weak defect.
  Faithful + non-leaking is provably impossible here.

This is the same faithful-must-leak shape as the dispositioned
sphinx-doc__sphinx-10466 (ascending sort of positions) and
sphinx-doc__sphinx-9673 (plural `:returns:` synonym) instances: the
discriminator exists only in gold + hidden tests + hints, and the spec cannot
be both faithful and silent about it.

## Core soundness is intact (per the recorded P2 audit, verdict.md)

- G-VERIFY: Solution.lean verifies (2.7 s), proof closes without sorry.
- G-DIFF: `Solution_prepatch.lean` (attrs-only resolution) fails for the
  right reason — unsolved goal
  `attrs.lookup k = resolveOne attrs fallback hasFallback k`.
- G-EQ: SOUND / TIGHT — 7 same-spec wrong impls (incl. ignore-fallback,
  always-fallback, fallback-priority, empty, off-by-one, fallback-only) all
  rejected by the discriminating clause; two positive controls verify.
- G-PANEL-2 (faithfulness): FAITHFUL — resolveOne/resolveAll match the real
  patched `getattr` + `cvargs.get` composition; independent end-to-end drive
  of patched RepeatedKFold/RepeatedStratifiedKFold reproduces the F2P repr.
- G-AX: deep model == real patched value resolution on 12 boundary + 20000
  fuzz object states (exit 0). G-CONF: 0 / 100012 disagreements (seed 14983),
  e2e leg ok on 4 real RepeatedCV objects. G-MUT: killed 14/14.
  G-RESOLVE: resolved.

Only the secondary no-leakage property is relaxed, for this one documented
facet (the secondary-parameter-store fallback in the displayed-value
resolution).
