# mapping.md — django__django-13410

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 580a4341cb0b4cbfc215a70afc004875a7e815f4`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/core/files/locks.py` (the POSIX `import fcntl`
branch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `acquireLock (outcome : LockOutcome)` | `lock(f, flags)` — `django/core/files/locks.py:109` (POSIX/fcntl branch) | the modeled changed function: report, as a definite boolean, whether the lock was acquired |
| `releaseLock` | `unlock(f)` — `django/core/files/locks.py:113` (POSIX/fcntl branch) | the modeled changed function: report, as a definite boolean, whether the lock was released |
| `LockOutcome` (`succeeded` / `contended`) | the observable outcome of the call `fcntl.flock(_fd(f), …)` — CPython stdlib `fcntl` module | R-refinement of the underlying OS lock primitive's outcome (mapping.md §2) |
| `acquiredOk (outcome)` | the per-outcome decision the post-patch body computes | pure spec: success indicator from the primitive's outcome |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): `ret = fcntl.flock(_fd(f), flags); return ret == 0`
(and the analogous `unlock` line) — `lock` lines 109-110, `unlock` lines
113-114.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the outcome of `fcntl.flock(_fd(f), flags)` | `LockOutcome` | **`succeeded`** ↔ the call returns normally (CPython `fcntl.flock` yields `None` on success — it never yields the integer `0`). **`contended`** ↔ a non-blocking request (`flags & LOCK_NB`) finds the resource already held, so the call raises `BlockingIOError` (a subclass of `OSError`, errno `EWOULDBLOCK`/`EAGAIN`). |
| the file/file-descriptor argument `f` and the `flags` argument | (omitted) | not observable in the result beyond which `LockOutcome` the call produces; `_fd(f)` is the unchanged descriptor accessor. The function does not mutate `f` (directive 5): the model takes only the outcome and returns a `Bool`, carrying no mutable frame. |
| the returned success indicator (`bool`) | `Bool` | `True` ↔ `true`, `False` ↔ `false`; Python `assertIs(..., True/False)` (the F2P tests) requires a definite `bool`, which both `acquireLock`/`releaseLock` return. |

The blocking primitive's third behaviour — a *blocking* request on a held
resource — never returns (it waits), so it is not an observable outcome of a
returning call and is intentionally absent from `LockOutcome`. The problem
statement scopes the fix to callers using `LOCK_NB`, exactly the returning
contended path modeled by `contended`.

`releaseLock` takes no `LockOutcome`: releasing a held lock with `LOCK_UN`
completes normally (the gold `unlock` no longer guards it and unconditionally
returns `True`), so its result is the constant `true`.

## 3. Callee provenance

There are **no axioms** and **no deep-model references** in this bundle. The one
callee involved, `fcntl.flock`, is **unchanged** by the patch; the change is
purely in how the POSIX `lock`/`unlock` wrappers translate that callee's outcome
into a boolean. The outcome ↔ `LockOutcome` correspondence (§2) is an
R-refinement, validated end-to-end by G-CONF (`conformance_check.py`), which
drives the *real* patched `lock`/`unlock` over *real* `fcntl.flock` contention
realized with real file descriptors (the same mechanism the F2P tests use).
Consequently G-AX is `skip` (no `axiom_check.py`): there is no axiom or deep
model whose `ensures` could be over-claimed.

### 3.1 `fcntl.flock` outcome facts (the soundness crux, validated by G-CONF)
CPython `fcntl.flock(fd, op)`:
* returns `None` on success — **not** the integer `0`. Hence the pre-patch
  `return ret == 0` is `None == 0`, i.e. always `False`, even on success.
* raises `OSError` (specifically `BlockingIOError`) when `op & LOCK_NB` and the
  resource is already held by a conflicting lock.
Docs: https://docs.python.org/3/library/fcntl.html#fcntl.flock . G-CONF realizes
both outcomes against the real primitive (two independent open file descriptions
of the same file; flock conflicts across them on Linux).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13410`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`acquiredOk`/`releaseLock` to Python and realizes each `LockOutcome` as a real
`fcntl.flock` outcome (lock held / free, blocking / non-blocking) before running
the patched real `lock`/`unlock`.
