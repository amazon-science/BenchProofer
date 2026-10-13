# refinement.md — matplotlib__matplotlib-23299

Operation-by-operation correspondence between `implementation_restoreSettings`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH snapshot+restore
logic of `rc_context`). Tags: **R** type refinement, **A-consumed** proof uses an
axiom, **A-reference** deep model validated == real callee, **I** identical
concrete op.

The modeled function captures the wrapper's net effect on the global settings
mapping. Its observables are `orig` (the entry snapshot, `rcParams.copy()`) and
`final` (the post-body mapping, what `rcParams` holds when the body finishes).
The body itself (`rc_file` / `rcParams.update(rc)` / `yield`) runs outside the
modeled function; its only output to the restore is `final`.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut snapshot := orig` | `orig = dict(rcParams.copy())` (entry snapshot) | R |
| 2 | `snapshot := assocErase snapshot "backend"` | `del orig['backend']` (the FIX: drop the backend key from the snapshot) | R |
| 3 | `return dictUpdate final snapshot` | `dict.update(rcParams, orig)` in the `finally` block — overlay each snapshot entry onto the current mapping | R |

Notes:

- **Every step is R — no A.** The behavior the patch changes (which keys the
  restore reverts) is modeled DEEPLY as pure association-list operations
  (`dictUpdate`, `assocErase`, `assocSet`); SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op. The `axioms` region is empty; **G-AX skips**.
- **R, not I.** Each op is a refinement: the Python `dict` global `rcParams` and
  its `copy()`/`del`/`dict.update` operations are refined onto the
  `List (String × String)` carrier per mapping.md's bijection
  (`dict.update` ↔ `dictUpdate`, `del d[k]` ↔ `assocErase`, `d[k]=v` ↔
  `assocSet`). The body's net effect is refined into the single input `final`.
- **The fix itself** is step 2 (`assocErase snapshot "backend"`). The pre-patch
  impl (`Solution_prepatch.lean`) omits that erase, so it overlays the full
  snapshot — including `"backend"` — onto `final`, reverting the body's backend
  choice. That is the actual bug: the figure-clearing cascade in the issue is
  triggered because `get_backend()` re-resolves the backend after the context
  reverted it to the auto-sentinel. The discriminating clause is the `"backend"`
  entry of the result: fixed ⇒ keeps `final`'s value; buggy ⇒ reverts to
  `orig`'s value. The carried gold proof on the prepatch fails to typecheck
  against the buggy impl (G-DIFF).
- **`del orig['backend']` never raises** in practice: `rcParams` always carries
  the `'backend'` key, so the key is present in `orig`. `assocErase` is total
  regardless (it filters), so the Lean model is faithful whether or not the key
  is present; mapping.md records the domain invariant.
- **G-CONF** mechanically refutes the R legs: a faithful in-process replica of
  the POST-PATCH restore (`dict.update(final, orig - {'backend'})`) is diffed
  against the impl shadow over ≥1e5 fuzzed `(orig, final)` mapping pairs. No A
  legs.
