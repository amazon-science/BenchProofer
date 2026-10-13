# refinement.md — django__django-13410

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `acquireLock` and `releaseLock` `do` blocks) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The acquire site — `lock(f, flags)` (`django/core/files/locks.py:109`)

Gold hunk:
```
- ret = fcntl.flock(_fd(f), flags)
- return ret == 0
+ try:
+     fcntl.flock(_fd(f), flags)
+     return True
+ except BlockingIOError:
+     return False
```

| # | Solution.lean impl op (`acquireLock`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `outcome : LockOutcome` | the outcome of `fcntl.flock(_fd(f), flags)` (normal return vs `BlockingIOError`) | R | `LockOutcome.succeeded` ↔ the `try` body completing past `fcntl.flock(...)`; `LockOutcome.contended` ↔ the `except BlockingIOError` path (mapping.md §2). G-CONF realizes both against the real primitive. |
| A2 | `if outcome = succeeded then return true` | the `try`-body `return True` (reached iff `fcntl.flock` returned, i.e. did not raise) | I | concrete boolean, transliterated by G-CONF. Pins the changed behaviour: success is now `True`, decoupled from the primitive's no-value (`None`) result that the pre-patch `ret == 0` test mishandled. |
| A3 | `else return false` | the `except BlockingIOError: return False` path | I | concrete boolean; a non-blocking contended acquisition reports `False`. |

Discriminating content of the change — success is reported `true`, not the
`None == 0 ⇒ False` of the pre-patch — lives in `acquiredOk succeeded = true`
(model) ⇔ the `try`-body `return True` (real). `Solution_prepatch_lock.lean`
reproduces the pre-patch `return ret == 0` semantics (always `false` because the
primitive's normal result is never the integer `0`) and **fails**
`out = acquiredOk outcome` on the `succeeded` case (G-DIFF). This is exactly the
behaviour the F2P `test_exclusive_lock`/`test_shared_lock` assertions
`assertIs(locks.lock(...), True/False)` require.

## B. The release site — `unlock(f)` (`django/core/files/locks.py:113`)

Gold hunk:
```
- ret = fcntl.flock(_fd(f), fcntl.LOCK_UN)
- return ret == 0
+ fcntl.flock(_fd(f), fcntl.LOCK_UN)
+ return True
```

| # | Solution.lean impl op (`releaseLock`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `return true` | the gold body: call `fcntl.flock(_fd(f), LOCK_UN)`, then unconditionally `return True` | I | `LOCK_UN` on a held descriptor completes normally; the gold `unlock` no longer guards on the (non-zero-comparable, i.e. `None`) result and always reports `True`. The constant-`true` spec mirrors this. |

The release path has no non-blocking contended outcome (unlocking never
contends), so `releaseLock` takes no `LockOutcome` and is the constant `true`.
`Solution_prepatch_unlock.lean` reproduces the pre-patch `return ret == 0`
(always `false`, `None != 0`) and **fails** `out = true` (G-DIFF). This matches
the F2P assertions `assertIs(locks.unlock(...), True)`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — how the wrapper
turns the primitive's outcome into a boolean — is modeled **directly** in the
`pure` region (`acquiredOk`, and the constant `true` for release) over an
R-refined `LockOutcome`. There is **no axiom** about the function under change
and **no axiom** about the unchanged callee `fcntl.flock`: its outcome ↔
`LockOutcome` correspondence is an R-refinement validated by G-CONF against the
real primitive, not a consumed contract. Hence no A rows and G-AX = skip
(mapping.md §3).

## D. verify(Solution) ⇒ resolved

`acquireLock` verifies only if its output equals `acquiredOk outcome` — `true`
on `succeeded`, `false` on `contended` (A2/A3) — and `releaseLock` only if it is
constantly `true` (B1). By R (`LockOutcome` ↔ the real `fcntl.flock` outcome) the
verified wrappers equal the gold `lock`/`unlock` on every realizable outcome; by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour over real
`fcntl.flock` contention on the pinned fuzz inputs. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust (G-AX = skip).
