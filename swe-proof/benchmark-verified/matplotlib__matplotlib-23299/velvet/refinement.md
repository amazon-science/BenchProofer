# refinement.md — matplotlib__matplotlib-23299

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`restoreSnapshot` `do` block, with the deep models `updateDict`/`eraseKey` in the
`pure` region) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement; state the bijection), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom's `ensures`, **A-reference** where
a deep model is validated == the real callee by G-AX), or **I** (identical
concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`). An earlier revision
used partial correctness, which a same-spec DIVERGING impl (a non-terminating
loop before the assignment) vacuously satisfied — the postcondition is only
claimed *if* the method exits; the adversarial G-PANEL-1 audit constructed
exactly that counterexample. Total semantics obliges termination, so the
diverging class is excluded (re-checked: the same attack now fails to verify).
The real restore is a straight-line `del` + `dict.update` in a `finally`
block that always terminates, so total correctness is the faithful reading of
the repo behavior, not an over-tightening. The method body is loop-free, so no
`decreasing` measure is needed.

## A. The restore site — `rc_context()` finally block (`lib/matplotlib/__init__.py:1089-1096`)

Gold hunk (the behavioural change; the docstring line is non-semantic):
```
-    orig = rcParams.copy()
+    orig = dict(rcParams.copy())
+    del orig['backend']
     try:
         ...
     finally:
         dict.update(rcParams, orig)  # Revert to the original rcs.
```

The entry snapshot `orig` is taken of `rcParams`; on exit `dict.update(rcParams,
orig)` reverts every key to its snapshot value. The patch deletes the `backend`
key from the snapshot first, so on exit `backend` keeps whatever value the
context body assigned (it is not in `orig`, so the overlay does not touch it).

| # | Solution.lean impl op (`restoreSnapshot`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `params : List (String × String)` (mut), post-state read as a mapping | the live module dict `rcParams` at restore time | R | `dict[str,str]` ↔ `List (String × String)` with unique keys, read as a key→value mapping (mapping.md §2). G-CONF bridges via Python `dict`. Mutated frame pinned exactly (directive 5). |
| A2 | parameter `saved : List (String × String)` (read-only) | `orig = dict(rcParams.copy())` — the entry snapshot before the `del` | R | same `dict` ↔ assoc-list bijection; `.copy()`/`dict(...)` are identity on content (mapping.md §2). Not `mut`: the snapshot is not written. |
| A3 | `restoreSrc := eraseKey saved "backend"` | `del orig['backend']` | I | concrete drop of one key; dicts have unique keys so `eraseKey` removes exactly the `backend` binding, == `del orig['backend']`. Transliterated by G-CONF; G-AX checks `eraseKey == builtin del`. |
| A4 | `params := updateDict params restoreSrc` | `dict.update(rcParams, orig)` | A-reference + I | the overlay `dict.update` is modeled **deeply** by `updateDict` (saved bindings win, current-only keys kept). The op itself (`:=`, the overlay) is **I** (concrete, transliterated by G-CONF leaving `dict.update` real); the equality of the deep model to the real builtin overlay is the **A-reference** G-AX validates. mapping.md §3.1. |

Discriminating content of the change — the designated key `"backend"` is
EXCLUDED from the overlaid snapshot, so its post-restore value is the CURRENT
value, not the saved one — lives in `eraseKey saved "backend"` (model) ⇔
`del orig['backend']` (real). The pre-patch overlaid the FULL snapshot
(`orig = rcParams.copy()`, no `del`); `Solution_prepatch.lean` reproduces that
(`updateDict params saved`) and **fails** `params = updateDict paramsOld
(eraseKey saved "backend")` (G-DIFF): the unsolved goal is exactly
`updateDict paramsOld saved = updateDict paramsOld (eraseKey saved "backend")`,
which fails whenever `saved` binds `backend` to a value differing from
`params`'s — the F2P scenario.

## B. No consumed axioms

There are no `axiom` declarations and no `:|` stubs. The only callee the restore
defers to — the builtin mapping overlay `dict.update` — is modeled DEEPLY
(`updateDict`, an A-reference validated by G-AX), not consumed as an axiom. The
key-drop `eraseKey` is an ordinary concrete `I` op (also G-AX-checked against the
real `del` for good measure). No dead axiom is shipped.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — excluding
the designated key from the reverted snapshot — is spelled out concretely
(`eraseKey saved "backend"`, step A3, an `I` op) feeding the deeply-modeled
overlay (A4). Nothing is hidden behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`restoreSnapshot` verifies only if its post-state equals `updateDict paramsOld
(eraseKey saved "backend")` (A3 + A4): the snapshot overlaid with `backend`
removed, i.e. `backend` keeps its current value while every other key reverts.
By R (`dict ↔ List (String × String)`, `.copy()`/`dict()` identities) the
verified restore equals the patched finally block `del orig['backend'];
dict.update(rcParams, orig)` on the tested inputs; by G-AX the deep model
`updateDict` equals the real builtin overlay (A-reference) and `eraseKey` equals
the real `del`; by G-CONF the R/I transliteration of the restore agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs (including the F2P scenario: entry
backend `Agg`, body sets `module://aardvark`, restore keeps `module://aardvark`).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). The single trust point is axiom soundness via the A-reference
(G-AX); refinement fidelity is this doc + G-CONF.
