# mapping.md — django__django-13410

## Symbol binding (file:line @ base_commit 580a4341cb0b4cbfc215a70afc004875a7e815f4)
Modeled file: `django/core/files/locks.py`. The gold patch rewrites the two
posix (`fcntl`-backed) advisory-lock helpers in the `else:` branch that runs when
`fcntl` is importable (`:108-115` pre-patch):

```python
def lock(f, flags):
    ret = fcntl.flock(_fd(f), flags)
    return ret == 0

def unlock(f):
    ret = fcntl.flock(_fd(f), fcntl.LOCK_UN)
    return ret == 0
```

Pre-patch bug: `fcntl.flock` returns `None` on success and *raises* `OSError`
(`BlockingIOError` for a non-blocking miss) on failure — it never returns `0`.
So `ret == 0` is `None == 0` → always `False`. Both helpers therefore always
report failure, and a non-blocking caller can never tell it acquired the lock.

Gold fix (`:109-118` post-patch):

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

Two independently-observable fixed behaviors → two modeled functions and two
prepatches:
- `acquire` ↔ `locks.lock` (`Solution_prepatch_1.lean`)
- `release` ↔ `locks.unlock` (`Solution_prepatch_2.lean`)

Lean modeled-function names are NEUTRAL: `acquire`/`release` name the *behavior*
("obtain / give up an advisory lock"), sharing no substring with the patched
symbols `lock`/`unlock`/`flock` (and `lock`/`unlock` are not even in the
solver-visible problem statement beyond the module name; see G-LEAK below).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `acquire` (modeled fn) | `locks.lock(f, flags)`, `locks.py:109-115` (post-patch `:109-114`) |
| `release` (modeled fn) | `locks.unlock(f)`, `locks.py:113-115` (post-patch `:116-118`) |
| `outcome : Outcome` | the result channel of `fcntl.flock(_fd(f), …)` |
| `Outcome = Except FlockErr Unit` | `flock`'s two channels (returns `None` / raises `OSError`) |
| `.ok ()` | `flock` returned (completed; its `None` value is discarded) |
| `.error .wouldBlock` | `flock` raised `BlockingIOError` (non-blocking request not granted) |
| `.error (.other c)` | `flock` raised some OTHER `OSError` (errno `c`) — not the not-granted signal |
| result `.ok true` | the helper returned `True` |
| result `.ok false` | the helper returned `False` |
| result `.error (.other c)` | an out-of-band signal propagated out of the helper (unhandled) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `fcntl.flock(...)` returns `None` (operation completed) | `outcome = .ok ()` |
| `fcntl.flock(...)` raises `BlockingIOError` | `outcome = .error .wouldBlock` |
| `fcntl.flock(...)` raises any other `OSError` (errno `c`) | `outcome = .error (.other c)` |
| `lock`: `try: flock(...); return True; except BlockingIOError: return False` (other `OSError` propagates) | `implementation_acquire`: `try (let _ ← outcome; return true) catch e => match e with .wouldBlock => return false | .other c => throw (.other c)` |
| `unlock`: `flock(..., LOCK_UN); return True` (no `except`) | `implementation_release`: `let _ ← outcome; return true` |
| returned `True` / `False` | `.ok true` / `.ok false` |
| an `OSError` propagating out of the helper | `.error (.other c)` propagated by the `Except` bind |

### flock result-channel modeling note
CPython's `fcntl.flock` (see the Python docs) returns `None` on success and
raises `OSError` to signal failure; a non-blocking (`LOCK_NB`) request that
cannot be granted raises `BlockingIOError` (an `OSError` subclass). The gold
`lock` catches EXACTLY `BlockingIOError` and maps it to `False`; **any other
`OSError` propagates** — this is why the error model distinguishes
`.wouldBlock` (handled → `False`) from `.other c` (propagated). A spec that
collapsed all failures to one channel would let a wrong impl that swallows e.g.
`EBADF` still verify; the two-constructor `FlockErr` closes that hole.
`unlock` (releasing, via `LOCK_UN`) does not block, so in practice it never
raises and always returns `True`; its `Except` model propagates ANY error
channel unchanged (the helper has no `except`), the faithful skeleton of "no
error handling on release." (Python promotes errno EAGAIN/EWOULDBLOCK/
EINPROGRESS/EALREADY `OSError`s to `BlockingIOError`; G-CONF's `.other` errnos
exclude those so they land on the genuinely-propagated channel.)

The `outcome` argument abstracts ONLY the primitive's result channel — the
boolean-status logic that the patch changes is modeled R/I (not axiomatized).

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The lower-level primitive
  `fcntl.flock` is the *changed-path* dependency, but its INTERNAL behavior is
  not modeled at all — it is abstracted as the `outcome` argument. The patch
  changes only how `outcome` is turned into a boolean, which is pure R/I logic
  modeled directly. So `meta.json axioms = []` and `deep_model_references = []`.
- `_fd(f)` (unchanged helper) extracts a file descriptor; it does not affect the
  result-channel→bool mapping and is not modeled (it feeds the abstracted
  primitive call).
- Flag dependency: `lock` is called with `LOCK_EX`/`LOCK_SH`, optionally
  `| LOCK_NB`. Only a non-blocking (`LOCK_NB`) request can raise
  `BlockingIOError`; a blocking request waits and completes (`outcome = .ok ()`).
  G-CONF drives both `outcome` channels for `lock`.

## G-LEAK
The solver-visible `problem_statement` discusses the posix file-locking helpers,
non-blocking locks, and that `flock` returns `None`/raises `OSError`. The spec
view (Solution.lean minus impl+proof) describes the abstract behavior — turning a
lower-level primitive's two-channel result into a boolean status — without
naming the patched symbols (`lock`, `unlock`, `flock`, `fcntl`) or the patched
file path, and without narrating the bug→fix mechanism (no "always returns
False", no "ret == 0", no diff lines). The modeled-function identifiers
`acquire`/`release` share no substring with the patched defs `lock`/`unlock`.

## Pinned G-CONF fuzz seed
`13410`.
