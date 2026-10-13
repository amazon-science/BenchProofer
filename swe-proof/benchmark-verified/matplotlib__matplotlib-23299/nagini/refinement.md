# refinement.md — matplotlib__matplotlib-23299

The operation-by-operation correspondence between `model.py`'s implementation
(the `restore_after_temporary_overrides` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee/primitive by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested input, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The save→restore site — `rc_context()` (`lib/matplotlib/__init__.py:1057`)

Gold hunk (the behavioural change; a docstring line is also added):
```
-    orig = rcParams.copy()
+    orig = dict(rcParams.copy())
+    del orig['backend']
     try:
         ...                       # body: yield (+ rc_file / rcParams.update(rc))
     finally:
         dict.update(rcParams, orig)   # revert the snapshot
```

The function is a `@contextlib.contextmanager` generator: the code before
`yield` runs on context entry, the `finally` after `yield` runs on exit. The
model collapses this lifecycle into one straight-line function whose pre-`yield`
snapshot, body-override, and post-`yield` revert are spelled out in order; the
body's only observable effect on the tested behaviour is the value each key
holds when the revert begins, modeled by the explicit `new_resolved` /
`other_override` parameters.

| # | model.py impl op (`restore_after_temporary_overrides`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `params: Dict[int, int]` | the module-global `rcParams` (an `RcParams`, a `dict` subclass) | R | `RcParams` ↔ `Dict[int,int]`: string key ↔ integer token, value ↔ integer token (mapping.md §2). The observed behaviour is mapping state only. |
| A2 | `key_resolved() == 0` | the key `'backend'` (`__init__.py`, special-cased in `RcParams.__getitem__`/`__setitem__`) | R | the distinguished key the revert must not touch, as an integer token (mapping.md §1). |
| A3 | `key_other() == 1` | any non-`'backend'` key (e.g. `'interactive'`) | R | a representative ordinary key the revert DOES touch (mapping.md §1). |
| A4 | `saved = {}; saved[key_other()] = params[key_other()]` — a snapshot that records the to-be-reverted keys and EXCLUDES the distinguished key | `orig = dict(rcParams.copy())` **then** `del orig['backend']` — a snapshot of every key with the distinguished key removed | R + A-reference | the gold's `copy()` + `del orig['backend']` produces a dict whose key set is "all keys except `'backend'`"; the model realises the SAME net snapshot data flow by recording into `saved` only the keys the revert is meant to touch (the ordinary key), never the distinguished key. `del` on a `Dict` is outside the Nagini fragment, so the equivalent "snapshot-minus-distinguished-key" is constructed directly; the equivalence of the two constructions (snapshot-then-delete vs. snapshot-excluding) is validated == the real `dict` primitives by axiom_check.py (G-AX). |
| A5 | `params[key_resolved()] = new_resolved; params[key_other()] = other_override` | the body run at `yield` (and `rc_file(fname)` / `rcParams.update(rc)`) overriding entries | R | the body's writes to the two observed keys; modeled as their post-body values (mapping.md §2). `__setitem__`/`dict.update` write key→value, refined to `Dict[int,int]` assignment. |
| A6 | `if key_other() in saved: params[key_other()] = saved[key_other()]` — revert exactly the snapshot's keys | `dict.update(rcParams, orig)` in the `finally` | R + A-reference | `dict.update(rcParams, orig)` writes each key of `orig` back into `rcParams`; since `orig` excludes the distinguished key (A4), only the ordinary keys are reverted. The model reverts exactly the keys present in `saved` (the ordinary key), leaving the distinguished key untouched — the identical net effect. Validated == the real `dict.update` over the post-`del` snapshot by axiom_check.py (G-AX). The gold's `dict.update(rcParams, orig)` reverts EVERY non-`backend` key (`orig` is the full snapshot minus `'backend'`), not merely the one observed ordinary key. The spec pins this full-revert behaviour **in-spec** via post-condition clause (4) — a forward `Forall(k: k in params and k != key_resolved() ⟹ params[k] == Old(params[k]))` — so it is a verifier obligation, not refinement prose. Under the map (`key_other()` ↔ any non-`backend` key, e.g. `'text.usetex'`), this closes the scope-loss hole: an impl that corrupts/drops any third pre-existing non-distinguished key (and would fail P2P `test_rcparams_reset_after_fail`) cannot verify. |

The discriminating content of the change — the distinguished key being EXCLUDED
from the snapshot, so the exit-time revert leaves it holding the body-set value
rather than overwriting it with the stale entry value — lives in A4 (the
snapshot omits `key_resolved()`) and is observed by the postcondition
`params[key_resolved()] == new_resolved` (survive). The pre-patch keeps the
distinguished key in the snapshot and reverts it; `model_prepatch.py` reproduces
that (`saved[key_resolved()] = params[key_resolved()]` plus reverting it) and
**fails** the postcondition `params[key_resolved()] == new_resolved`, which is
exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — building the restore snapshot WITHOUT the distinguished key — is
modeled **deeply** (the snapshot construction, the omission of the distinguished
key, and the per-key revert are spelled out in the impl region over a real
`Dict[int,int]`), not hidden behind an axiom about the function under change.
There is **no consumed `@ContractOnly` axiom**: the only callees are CPython
`dict` primitives (`copy`/`del`/`update`), which are the **A-reference** that
G-AX (`axiom_check.py`) validates the deep model against by reproducing the gold
patch's exact control flow over a real `dict`.

The `del` keyword on a `Dict` is outside the Nagini 1.2.0 fragment, so the
gold's `orig = dict(rcParams.copy()); del orig['backend']` (snapshot-then-delete)
is realised as the behaviourally-identical "snapshot that excludes the
distinguished key" (A4) — same net snapshot, same net revert, validated by G-AX.
This is a type/fragment refinement (R), not a changed-operation hand-wave: the
*data flow* (the snapshot the revert consumes excludes `'backend'`) is identical.

## B2. Termination is an explicit obligation

Nagini checks partial correctness by default, so a diverging implementation
would satisfy every post-state clause vacuously. The contract therefore
carries `Requires(MustTerminate(2))`: any implementation that fails to
complete (e.g. spins in a loop after establishing the post-state) fails the
obligation-leak check and cannot verify. The modeled restore is bounded,
loop-free work, so the gold-faithful impl discharges the obligation trivially.

## C. verify(model) ⇒ resolved

`restore_after_temporary_overrides` verifies only if, after the snapshot-build /
body-override / revert sequence, the distinguished key holds the body-set value
(A4+A6 ⇒ survive postcondition) AND every ordinary key is reverted to its entry
value (revert postcondition) AND no spurious key appears AND every
non-distinguished pre-existing key is reverted to its entry value (the frame /
full-revert postcondition clause (4) — which subsumes the single observed-key
revert and additionally forbids corrupting or dropping any other pre-existing
non-`backend` key, the exact scope-loss the gold's full-snapshot revert
prevents and that P2P `test_rcparams_reset_after_fail` exercises). By R (`RcParams` ↔
`Dict[int,int]`, string keys ↔ tokens, the generator lifecycle ↔ straight-line
snapshot/body/revert) the verified function equals the gold patch's
`orig = dict(rcParams.copy()); del orig['backend']; …; dict.update(rcParams,
orig)` on the tested mapping state; by G-AX the deep model equals the real
`dict` primitives (the A-reference). The F2P test `test_no_backend_reset_rccontext`
sets `rcParams['backend']` inside `rc_context()` and asserts it is unchanged
after exit — exactly the survive postcondition. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited primitives — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
