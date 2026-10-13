# mapping.md — matplotlib__matplotlib-23299

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3eadeacc06c9f2ddcdac6ae39819faa9fbee9e39`, states the type
abstraction, and gives the provenance of the modeled operation.

Repo file under change: `lib/matplotlib/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `restore_after_temporary_overrides(params, new_resolved, override_value, other_override)` | the context-manager generator `rc_context(rc=None, fname=None)` — `lib/matplotlib/__init__.py:1057` (snapshot line 1090, restore line 1098) | the modeled changed function: the save→body→restore lifecycle of the temporary-override context manager |
| `key_resolved()` | the distinguished mapping key `'backend'` (`lib/matplotlib/__init__.py`, the key special-cased in `RcParams.__getitem__`/`__setitem__`, lines 644-647, 673-679) | pure spec: the integer token for the one key the restore must not revert |
| `key_other()` | any non-`'backend'` mapping key (e.g. `'interactive'`) | pure spec: a representative ordinary key that the restore DOES revert |

The pre-patch repo expression the change replaces (for the refinement audit,
not referenced from the consumer spec view): `orig = rcParams.copy()`
(`__init__.py:1090`), restored on exit by `dict.update(rcParams, orig)`
(`__init__.py:1098`). The patch makes the snapshot `orig = dict(rcParams.copy())`
and removes the distinguished key from it before the restore runs, so the
`dict.update` on exit carries every key EXCEPT the distinguished one back.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `rcParams` — the live `RcParams` mapping (a `dict` subclass) | `Dict[int, int]` | key string ↔ integer token (`'backend'` ↔ `key_resolved()==0`; an ordinary key ↔ `key_other()==1`); value ↔ integer token (a resolved/explicit value ↔ its integer code; the unresolved auto value ↔ its own distinct code) |
| `orig = dict(rcParams.copy())` snapshot (`__init__.py:1090` post-patch) | a local `Dict[int, int]` copy (`saved` in the impl) | `dict(...)` / `RcParams.copy()` carry key→value pairs faithfully; the model copies the two observed keys |
| `dict.update(rcParams, orig)` restore (`__init__.py:1098`) | per-key assignment `params[k] = saved[k]` over the snapshot's keys | `dict.update` writes each saved key's value into the live mapping; the model restores exactly the keys present in `saved` |
| the body run inside the context (`yield`, plus any `rc_file`/`rcParams.update(rc)`) mutating `rcParams['backend']` to a resolved value | the parameter `new_resolved` written into `params[key_resolved()]` before the restore; `override_value` written into another key the body may also touch; `other_override` the body's write to the ordinary key | the body's only observable effect on the tested behaviour is the post-body value of each key; modeled as the explicit pre-restore values |

The distinguished key's special-cased getter (`RcParams.__getitem__`, lines
673-679: an unresolved auto value triggers `plt.switch_backend`, which is what
re-derives the value and closes the open figures) is the *consequence* that the
F2P guards against, not the operation under change. The behaviour the fix pins,
and that the F2P test observes, is purely the mapping's post-exit state: the
value at the distinguished key after the context exits equals the value set
inside the context, instead of being reverted to the entry value. The model
pins exactly that mapping-state property over `Dict[int,int]`; no
`switch_backend`/figure-registry machinery is modeled (it is downstream of the
mapping state and not exercised by the tested behaviour).

## 3. Callee provenance (kind-A / A-reference — checked by G-AX / axiom_check.py)

This bundle axiomatizes **NO** opaque library callee. The behaviour under
specification — snapshot a mapping, run a body that overrides some keys, then on
exit revert every saved key EXCEPT the distinguished one — is composed entirely
of REAL Python `dict` primitives the gold patch uses: `dict(...)` /
`RcParams.copy()` (snapshot), `del d[k]` (drop the distinguished key from the
snapshot), and `dict.update` (per-key restore). It is therefore modeled
**DEEPLY** (the snapshot, the drop, and the per-key restore are spelled out in
the impl region over a real `Dict[int,int]`). There is no `@ContractOnly` axiom.

### 3.1 `restore_after_temporary_overrides` deep model ↔ the real `dict` primitives (A-reference)

**Operations:** `dict.copy` / `dict(...)` (key→value snapshot), `del orig[k]`
(remove the distinguished key from the snapshot), `dict.update(rcParams, orig)`
(write every snapshot key back into the live mapping). Provenance:
`lib/matplotlib/__init__.py:1089-1098` post-patch; CPython `dict` semantics
(every Python 3.x). G-AX (axiom_check.py) reproduces the gold patch's exact
control flow over a real `dict` — snapshot, drop the distinguished key, run a
body that overrides keys, then `dict.update` the snapshot back — and asserts
every observation matches model.py's frozen postconditions:
  * the distinguished key holds the body-set value on exit (NOT reverted);
  * every other saved key is reverted to its entry value;
  * no key absent from the snapshot is invented by the restore.

It imports nothing repo-specific: `dict` copy/`del`/`update` are Python language
primitives (the very constructs the gold patch composes). Exit 0 iff every
obligation holds.

## 4. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (shadow) against
the REAL patched `matplotlib.rc_context` over the live `rcParams` in the
instance container. Bridge: key token 0 ↔ `'backend'`, token 1 ↔
`'lines.linewidth'`, tokens 2..8 ↔ further float-validated keys (frame clause);
value token n ↔ `'module://_sbu_tok_<n>'` for the distinguished key (accepted
verbatim by its validator) and ↔ `float(n)` for ordinary keys (exact for the
generated range). Post-state is read at the raw-dict level (bypassing the
resolving getter, which is downstream of the modeled mapping state).
≥1e5 Requires-satisfying inputs: enumerated boundary cases + 100000 fuzz
trials. **Pinned fuzz seed: 23299** (the instance number).
