# mapping.md — matplotlib__matplotlib-23299

## Symbol binding (file:line @ base_commit 3eadeacc06c9f2ddcdac6ae39819faa9fbee9e39)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_rcContextRestore` / `problem_spec_rcContextRestore` / `correct_rcContextRestore` | the snapshot-and-restore logic of `rc_context` (the `orig = …` capture at entry and the `dict.update(rcParams, orig)` restore at exit) | `lib/matplotlib/__init__.py:1058-1099` (capture at 1090, restore at 1098) |
| `rcRestore` (pure helper) | the net effect of capture+restore on the global settings mapping | `__init__.py:1090,1098` |
| `dictUpdate` (pure helper) | `dict.update(rcParams, orig)` (overwrite cur's entries from upd) | `__init__.py:1098` |
| `assocErase` (pure helper) | `del orig['backend']` (post-patch) — drop one key from the snapshot | `__init__.py` post-patch line |
| `assocSet` (pure helper) | one `cur[k] = v` overwrite inside `dict.update` | builtin dict semantics |

## What the function does (base_commit)

`rc_context` is a context manager that temporarily changes `rcParams`:

```python
@contextlib.contextmanager
def rc_context(rc=None, fname=None):
    orig = rcParams.copy()              # snapshot at entry
    try:
        if fname:
            rc_file(fname)
        if rc:
            rcParams.update(rc)
        yield                           # body runs; may mutate rcParams to `final`
    finally:
        dict.update(rcParams, orig)     # restore: overwrite every key from the snapshot
```

The settings mapping `rcParams` is a dict with a fixed key set that always
includes the `'backend'` key. We model the wrapper's net effect on that mapping:
given the mapping value captured at entry (`orig`) and the mapping value present
when the body finishes (`final`), the restore overwrites every key of the live
mapping with its snapshot value.

The **bug**: the snapshot includes `'backend'`, so the restore reverts the
backend to its entry value even when the body deliberately changed it. The body
runs externally to the modeled function; its only observable to the restore is
the post-body mapping value `final`.

## The fix (gold patch)

```python
    orig = dict(rcParams.copy())
    del orig['backend']                 # exclude backend from the restore snapshot
    ...
    dict.update(rcParams, orig)
```

After the fix, the restore overwrites every key EXCEPT `'backend'`, so the
backend value chosen inside the context survives. This is exactly what the F2P
test `test_no_backend_reset_rccontext` checks.

## Lean ↔ Python type bijection (G-CONF + G-AX use this)

| Python | Lean |
|---|---|
| `rcParams` value (a dict `{str: object}`, fixed keys) | `List (String × String)` association list, unique keys (value rendered as an opaque token; only equality of values matters for the modeled behavior) |
| `orig` (entry snapshot) | `orig : List (String × String)` |
| post-body `rcParams` | `final : List (String × String)` |
| `dict.update(cur, upd)` | `dictUpdate cur upd` (foldl of `assocSet`) |
| `del orig['backend']` | `assocErase orig "backend"` (filter the key out) |
| `cur[k] = v` | `assocSet cur k v` |
| restored `rcParams` | `result : List (String × String)` |

**Domain invariants (real, modeled as theorem preconditions):**
- `'backend'` is always a key of `orig` (rcParams always has it) — so post-patch
  `del orig['backend']` never raises `KeyError`.
- `orig` and `final` share the same key set (a context body changes values, not
  the fixed rcParams key set).

These invariants are carried as hypotheses on `correct_rcContextRestore`; the
postcondition equality `result = rcRestore orig final` holds unconditionally
(they are documented domain bounds, used by G-CONF's fuzz corpus).

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behavior the patch changes —
  which keys are reverted by the restore — is modeled DEEPLY as pure association
  -list operations (`dictUpdate`, `assocErase`, `assocSet`) over the observable
  inputs (`orig`, `final`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op, so there is no callee contract to validate. The `axioms` region is
  empty and **G-AX skips**.
- `rc_file` / `rcParams.update(rc)` run inside the body before `yield`; their net
  effect is subsumed into the post-body mapping value `final` (an input), so they
  are not separately modeled.

## G-CONF fuzz seed

Pinned LCG seed: **23299** (see `conformance_check.py` `SEED`). Corpus: random
dicts over a fixed key pool that always contains `'backend'`; `orig` and `final`
share the key set but differ on random values (including the backend value). The
R/I shadow of `implementation_rcContextRestore` is diffed against an in-process
replica of the POST-PATCH restore. Hand-picked edge: orig backend `'agg'`, final
backend `'module://aardvark'` ⇒ result backend must be `'module://aardvark'`
(the F2P scenario) while all other keys revert to their `orig` value.
