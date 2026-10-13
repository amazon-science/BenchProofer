# mapping.md — matplotlib__matplotlib-23299

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3eadeacc06c9f2ddcdac6ae39819faa9fbee9e39`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `lib/matplotlib/__init__.py` (function `rc_context`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `restoreSnapshot (params, saved)` | the `finally:` restore block of `rc_context` — `lib/matplotlib/__init__.py:1095-1096` (the `orig = rcParams.copy()` setup at line 1089) | the modeled changed behavior: revert the rcParams mapping to its entry snapshot on context exit, EXCEPT the designated key |
| `updateDict (current, saved)` *(deep model — A-reference)* | `dict.update(rcParams, orig)` — Python builtin `dict.update`, called at `lib/matplotlib/__init__.py:1096` | pure spec: overlay a saved mapping onto the current one (saved bindings win); deep model of the unchanged builtin overlay, validated `updateDict == dict.update` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `eraseKey (d, name)` | `del orig['backend']` — Python builtin `del` on a dict — `lib/matplotlib/__init__.py:1090` (post-patch) | pure spec: drop one key from a mapping; the concrete `I` op the patch adds |
| `lookupKey` | (helper) membership test used by `updateDict`'s filter | pure spec: first-binding lookup in the assoc-list carrier |
| `"backend"` (the designated key) | the literal `'backend'` rcParam key | the one key excluded from the reverted snapshot |

The pre-patch repo behavior the change fixes (refinement audit only, not in the
consumer spec view): `orig = rcParams.copy()` (line 1089) snapshots the FULL
mapping including `backend`, so the `finally` overlay reverts `backend` too —
clobbering any backend assigned inside the context (the bug: `get_backend()`
resolves the backend during the context, mutating `rcParams['backend']`, which
the restore then wiped, dropping the live figures).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `rcParams` / `orig` — a `dict[str, str]` (an `RcParams`/`dict` of setting name → value) | `List (String × String)` with unique keys, read as a key→value mapping | `d` (Python dict) ↔ assoc list of its items; key membership ↔ `lookupKey … |>.isSome`; observable equality is mapping equality (key→value), order is NOT observable |
| `dict.copy()` / `dict(...)` wrapper (`__init__.py:1089`) | identity (omitted) | `.copy()`/`dict(...)` produce a content-equal mapping; identity on the assoc-list carrier under mapping equality |
| a setting key/value (`'backend'`, `'module://aardvark'`, …) | Lean `String` | exact string identity |

Only the `backend` key's restore behavior is observed by the F2P test
(`test_no_backend_reset_rccontext`): it sets `rcParams['backend'] =
'module://aardvark'` inside `rc_context()` and asserts it survives the exit.
Other keys' revert-to-snapshot behavior is the unchanged, P2P-preserved
semantics. The mapping carrier is `List (String × String)` because the operation
is a whole-mapping overlay keyed by string.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `updateDict` deep model ↔ `dict.update` (A-reference)
**Callee:** Python builtin `dict.update(current, saved)`. The overlay operation
is modeled **deeply** by `updateDict` in the `pure` region; there is **no
`update` axiom** the proof consumes. Semantics of the real builtin: for every
key in `saved`, `current[key]` becomes `saved[key]`; keys only in `current` are
untouched; result order is irrelevant under dict semantics. `updateDict current
saved = saved ++ current.filter (key not in saved)` encodes exactly that as a
key→value mapping (saved bindings win). Docs:
https://docs.python.org/3/library/stdtypes.html#dict.update.

### 3.2 `eraseKey` ↔ `del d[k]` (I op, G-AX-checked)
**Callee:** Python builtin `del`. `eraseKey d name` drops every binding for
`name`; since dicts have unique keys this equals `del d[name]` (a no-op if
absent). Concrete `I` op; checked equal to the real `del` by G-AX for defense in
depth.

**Soundness check (G-AX):** `axiom_check.py` runs the real `dict.update` and
`del` on boundary inputs (empty mappings, disjoint/overlapping keys, the
`backend`-only case, the F2P scenario) plus 30 000 randomized fuzz cases,
asserting (a) `updateDict == real dict.update` as a mapping (A-reference) and
(b) `eraseKey == real del`, and (c) the end-to-end patched restore keeps the
designated `backend` key at its current value. Imports only Python builtins.
Exit 0 iff sound. No flag dependency.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`23299`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `eraseKey` (I op) to a Python comprehension and leaves
`updateDict`'s overlay as the real builtin `dict.update` (A-reference → run real
callee, not the axiom model). The oracle is the patched `rc_context` finally
block (`del orig['backend']; dict.update(rcParams, orig)`).
