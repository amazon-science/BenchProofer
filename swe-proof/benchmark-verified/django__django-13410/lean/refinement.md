# refinement.md — django__django-13410

Maps every operation in `implementation_acquire` / `implementation_release` to
its `patch.diff` counterpart (the rewritten posix `lock`/`unlock` in
`django/core/files/locks.py`). Tags: **R** type-refinement, **A-consumed** proof
uses a callee axiom, **A-reference** deep-modeled used callee validated == real
callee, **I** identical concrete op.

## Patch (the two rewritten helpers)
```python
def lock(f, flags):
    try:
        fcntl.flock(_fd(f), flags)
        return True
    except BlockingIOError:
        return False

def unlock(f):
    fcntl.flock(_fd(f), fcntl.LOCK_UN)
    return True
```

## Operation correspondence — `implementation_acquire` ↔ `lock`
| # | Lean op (`implementation_acquire`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `try (… ) catch e => match e with …` | `try: … except BlockingIOError: …` | R | the two-channel result of the primitive is refined from "returns `None` / raises `OSError`" to `outcome : Except FlockErr Unit`; the `try/except` becomes an `Except` `try/catch` that matches on the signal. |
| 2 | `let _ ← outcome` | `fcntl.flock(_fd(f), flags)` | R | the primitive call is abstracted as consuming the `outcome` channel: `.ok ()` ↦ completed (binds, discards the unit), `.error …` ↦ raised (short-circuits to the catch). `_fd(f)`/`flags` are inputs to the abstracted call, not modeled. |
| 3 | `return true` | `return True` | I | success branch reports `True`. |
| 4 | `\| .wouldBlock => return false` | `except BlockingIOError: return False` | I | only the not-granted-right-now signal is turned into the `False` status. |
| 5 | `\| .other c => throw (.other c)` | (no matching `except`) any other `OSError` propagates | R | the faithful skeleton of "catch ONLY BlockingIOError": every other signal is re-raised / propagated, not converted to a status. |

## Operation correspondence — `implementation_release` ↔ `unlock`
| # | Lean op (`implementation_release`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let _ ← outcome` | `fcntl.flock(_fd(f), fcntl.LOCK_UN)` | R | same abstraction of the primitive call; `unlock` has no `except`, so an `.error` channel propagates through the `Except` bind unchanged (faithful: release does no error handling). |
| 2 | `return true` | `return True` | I | release always reports `True` (on the completed channel). |

Every op is **R** (the `Except`-channel refinement of the primitive's two-channel
result) or **I** (the literal `True`/`False` returns). There is **no A-consumed**
row (no opaque-axiom contract is consumed — the proofs close with zero axioms)
and **no A-reference** (the primitive is not deep-modeled; it is abstracted as the
input `outcome`). `meta.json axioms = []`, `deep_model_references = []`,
`conf_skip = false` — the impl is pure R/I, so G-CONF mechanically
differential-tests `implementation_acquire`/`release` against the real patched
`locks.lock`/`unlock` (driving a substituted `flock` for each `outcome` channel).

## conf_skip
`false`. The impl region is R/I data logic (turning the primitive's result
channel into a boolean status), which has a faithful Python shadow that does NOT
re-implement the abstracted callee. `conformance_check.py` builds that shadow and
diffs it against the real patched `lock`/`unlock`.

## Prepatch(es) = the real bug
Pre-patch, both helpers compute `ret = fcntl.flock(...); return ret == 0`. The
primitive returns `None` on success (never `0`) and raises on failure, so
`ret == 0` is always `False` — both helpers always report failure.

- **`Solution_prepatch_1.lean`** (acquire): `implementation_acquire` is the
  buggy skeleton `let _ ← outcome; return false` — i.e. the result channel is
  consumed but the status is the always-`False` `ret == 0`. It cannot satisfy
  `problem_spec_acquire` on the `.ok ()` channel, where the spec demands
  `.ok true`. The carried gold proof (`cases outcome <;> rfl`) fails to
  typecheck against it (G-DIFF; `lean_verify` exit 1). This is exactly
  FAIL_TO_PASS `test_exclusive_lock`/`test_shared_lock`, which assert
  `locks.lock(f, LOCK_EX) is True`.
- **`Solution_prepatch_2.lean`** (release): `implementation_release` is the buggy
  `let _ ← outcome; return false`; cannot satisfy `problem_spec_release` on the
  `.ok ()` channel (spec demands `.ok true`). Carried gold proof fails to
  typecheck. This is the `assertIs(locks.unlock(f1), True)` assertions of the
  same F2P tests.

Each prepatch isolates one independently-observable fixed behavior (the other
helper carries the gold impl), so each fails G-VERIFY on its own clause.
