# RELAXED_LEAKAGE — matplotlib__matplotlib-23299 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). This bundle's own recorded
P2 leakage audit (`verdict.md`, sub-review 3) reached exactly this
disposition — "VERDICT: RELAXED … This is a known, documented RELAXED
instance, not a fresh avoidable leak … a faithful PS-only non-leaking spec is
provably impossible" — and flagged the missing in-bundle recording as the
defect to correct; this file plus the meta flag IS that prescribed
correction. The same instance is already dispositioned identically in the
sibling `nagini/` bundle (`nagini/RELAXED_LEAKAGE.md`, project decision
2026-06-14).

## The mismatch

The gold fix (`lib/matplotlib/__init__.py`, `rc_context`) EXCLUDES the
distinguished `'backend'` key from the snapshot that the context manager
reverts on exit:

```python
-    orig = rcParams.copy()
+    orig = dict(rcParams.copy())
+    del orig['backend']
     try:
         ...
     finally:
         dict.update(rcParams, orig)   # Revert to the original rcs.
```

Effect: a backend value assigned/resolved inside the context SURVIVES the
exit-time revert instead of being overwritten with the stale entry value. The
sole F2P test (`test_no_backend_reset_rccontext`) sets
`rcParams['backend'] = 'module://aardvark'` inside `rc_context()` and asserts
it is unchanged after exit. The discriminator is therefore the
survive-vs-revert treatment of the `backend` key on context exit.

The dispositioned leaking facet in this bundle's spec view (frozen spec
region of `Solution.lean`): the postcondition
`ensures params = updateDict paramsOld (eraseKey saved "backend")` — naming
the literal key `"backend"` and the exact operation "drop `backend` from the
entry snapshot before overlaying it back" — together with the docstring's
statement that the restored mapping keeps the CURRENT value for the
designated key `"backend"` and the saved value for every other recorded key.
Under the mapping.md bijection (`eraseKey` = `del`, `updateDict` =
`dict.update`, `.copy()`/`dict()` = content identity) a reader of the spec
view alone can reconstruct the gold edit. That reconstruction is the
dispositioned facet.

## Why the leak is unavoidable

The discriminating vocabulary — the `rc_context` snapshot/revert mechanism
and the exclusion of the `backend` key from the reverted snapshot — is
**absent from the solver-visible `problem_statement`**:

- The `problem_statement` frames the ENTIRE defect as a downstream SYMPTOM:
  "`get_backend()` clears figures from `Gcf.figs` if they were created under
  `rc_context`", with a `Gcf.figs`-before/after reproduction. It never names
  the `backend` *rcParam*, the `rcParams` snapshot/restore mechanism, or that
  the fix is to exclude a key from the reverted snapshot.
- Token scan of `problem_statement`: `revert`, `restore`, `preserve`,
  `survive`, `snapshot`, `reset`, `copy`, `del`, `re-resolve`, `sentinel` —
  all absent. Its `backend` tokens are the symptom surface (`get_backend()`,
  "Matplotlib Backend: QtAgg"), not the rcParams-key/restore-exclusion layer.
- The actual diagnosis (backend auto-sentinel stashed by `rc_context`, set
  back on the way out, `get_backend()` re-resolving it) lives ONLY in
  `hints_text` — excluded from the leakage baseline — and the
  survive-vs-revert behavior is pinned only by the hidden `test_patch`.
- A `problem_statement`-only solver sees a `Gcf.figs`/`get_backend` symptom
  and would reach for the figure-manager / backend-resolution path, never for
  the `rc_context` snapshot exclusion the gold actually edits.

A faithful spec (one whose prepatch fails G-DIFF and which no wrong impl
satisfies) MUST pin the survive-vs-revert discriminator: drop
`eraseKey saved "backend"` from the postcondition and
`Solution_prepatch.lean` (full-snapshot overlay, `updateDict params saved`)
would verify, so G-DIFF could not fire. A spec derivable from the
`problem_statement` alone could model only the `Gcf.figs` symptom, not the
`rcParams` restore the gold changes. Faithful + non-leaking is provably
impossible here — the definition of a `problem_statement ↔ gold` mismatch.

## Core soundness is intact (per the recorded audits of THIS bundle)

- **G-VERIFY: pass** — `Solution.lean` verifies (exit 0), no sorry, under
  TOTAL correctness semantics (termination obliged; the diverging-impl class
  the earlier G-PANEL-1 audit exploited under partial semantics is excluded).
- **G-DIFF: pass** — `Solution_prepatch.lean` (full-snapshot overlay, the real
  pre-patch behavior) genuinely fails on the discriminating goal
  `updateDict paramsOld saved = updateDict paramsOld (eraseKey saved "backend")`
  — exactly the F2P case. `same_spec(Solution, prepatch) = True`.
- **G-EQ: SOUND / TIGHT** — exact-equality postcondition over concrete pure
  `def`s; 7+ wrong impls (incl. the prepatch bug) verify-rejected; positive
  control verifies.
- **G-PANEL-2: FAITHFUL** — spec prediction == real post-gold `rc_context`
  post-exit `rcParams` on every scenario incl. the F2P case; independent
  200k-input differential probe, 0 mismatches on the reachable domain.
- **G-AX: pass** — `updateDict` == real builtin `dict.update` overlay and
  `eraseKey` == real `del` on 8 boundary + 30000 fuzz cases (plus an
  independent 200k A-reference fuzz, 0 mismatches).
- **G-CONF: pass** — R/I shadow agrees with the patched finally block on
  100005 inputs (seed 23299), 0 disagreements.
- **G-RESOLVE: resolved** — `patch.diff` is the gold patch verbatim.

Only the secondary no-leakage property is relaxed, for this one documented
facet (the `backend` key excluded from the reverted snapshot so its
context-body value survives). The verify ⟹ correct contract is unaffected.
