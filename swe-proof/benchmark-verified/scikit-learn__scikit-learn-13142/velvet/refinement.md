# refinement.md — scikit-learn__scikit-learn-13142

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `finalizeLabels` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized/opaque callee — **A-consumed**
where the proof uses a stated contract, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE); it equals the gold patch
in `instance.json` byte-for-byte.

## A. The label-finalization tail — `BaseMixture.fit_predict` (`sklearn/mixture/base.py:194`, body 257–276)

Gold patch (a code MOVE): the final E-step

```
-        _, log_resp = self._e_step(X)          # line 263, BEFORE _set_parameters
         ...
         self._set_parameters(best_params)      # line 272
+        _, log_resp = self._e_step(X)          # MOVED to AFTER _set_parameters
         return log_resp.argmax(axis=1)
```

| # | Solution.lean impl op (`finalizeLabels`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `transientParams : Params`; `let mut active := transientParams` | the parameter state left in `self` when the `for init` loop ends (the last attempt's params) | R | parameter-set identity ↔ `Params` (mapping.md §2). The `mut active` cell models `self`'s in-force parameter state. |
| A2 | param `storedParams : Params` | `best_params = self._get_parameters()` (line 257) | R | best-scoring attempt's captured parameters ↔ `Params` (mapping.md §2). Read-only free input. |
| A3 | `active := storedParams` | `self._set_parameters(best_params)` (line 272) | I | install the selected best parameter set into the in-force state. Concrete assignment, transliterated directly. |
| A4 | `let out := labelsFor active` | `_, log_resp = self._e_step(X)` then `log_resp.argmax(axis=1)` (post-patch position) | A-reference-free / R | the UNCHANGED label-computing pipeline as a function of the active parameters (X fixed) ↔ free input `labelsFor : Params → Labels`. Because A3 runs first, `active = storedParams`, so `out = labelsFor storedParams`. Carried abstractly — no contract consumed (mapping.md §3); holds for EVERY `labelsFor`. |
| A5 | `return out` | `return log_resp.argmax(axis=1)` | R | label vector ↔ `Labels` (mapping.md §2). |

The discriminating content of the change — the labels must be computed from the
SELECTED best parameter set, not the loop's leftover — lives in the ORDER of A3
before A4. In `Solution.lean` `active := storedParams` precedes `out := labelsFor active`,
so `out = labelsFor storedParams = reportedLabels storedParams labelsFor`. In
`Solution_prepatch.lean` the order is reversed (`out := labelsFor active` while
`active = transientParams`, then `active := storedParams`), so the proof obligation
reduces to `labelsFor transientParams = labelsFor storedParams`, which is **unprovable**
(G-DIFF: the prepatch fails on exactly the `ensures out = reportedLabels …`
clause).

## B. No consumed axioms / no deep-model references

There are no `axiom`s and no A-reference deep models. Every callee the tail
touches (`_e_step`, `argmax`, `_set_parameters`, `_get_parameters`) is UNCHANGED;
the patch reorders them. `_e_step ∘ argmax` is carried as the opaque free input
`labelsFor` with NO behavioural claim, so there is nothing for G-AX to check
(G-AX = skip). `_set_parameters` is the concrete assignment A3 (an **I** op).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — its POSITION
relative to the parameter install — is modeled **directly** by the statement
ordering in the `do` block (A3 before A4), not hidden behind an axiom about the
function under change. There is no consumed axiom about the modeled tail.

## D. G-CONF status

`conf_skip = true`. The R/I ops A3–A5 carry no input-dependent computation whose
shadow could disagree with `patch.diff`: A4's value is the unchanged callee
`labelsFor` applied to whichever parameter set A3 left in force, and the
discriminating observable (best vs leftover parameters) materializes only on a
live fitted mixture with `n_init > 1` — the F2P tests, not a fuzzable
transliteration. `conformance_check.py` is a `status=skip` stub. (Precedent:
astropy__astropy-14096.)

## E. verify(Solution) ⇒ resolved

`finalizeLabels` verifies only if its output equals `reportedLabels storedParams
labelsFor = labelsFor storedParams` (A4 after A3). By R (`Params`/`Labels` bijections,
mapping.md §2) the verified tail returns the labels the unchanged
E-step→argmax pipeline yields with the BEST parameters in force — exactly what
the gold patch computes by moving `_e_step` after `_set_parameters`. The bug the
issue reports (`fit_predict` and `predict` disagree for `n_init > 1`) is exactly
the case where `transientParams ≠ storedParams`: the prepatch returns
`labelsFor transientParams` and fails verification, while the patched code
returns `labelsFor storedParams`, which `predict` (using the stored best params) also
returns — so they agree. The gold patch resolves (G-RESOLVE). Trust points: spec
strength (G-VERIFY/G-DIFF) and refinement fidelity (this doc, G-EQ).
