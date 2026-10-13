# mapping.md — django__django-15572

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0b31e024873681e187b574fe1c4afe5e48aeeecf`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each opaque callee.

Repo file under change: `django/template/autoreload.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collectConfiguredDirs (entries : List (List Char))` | the first `items.update(...)` generator over `backend.engine.dirs` — `django/template/autoreload.py:20` | modeled changed site #1: the directly-configured template directories collection |
| `collectLoaderDirs (entries : List (List Char))` | the second `items.update(...)` generator over `loader.get_dirs()` — `django/template/autoreload.py:25-29` | modeled changed site #2: the loader-supplied template directories collection |
| `keepConfigured (entry)` | the `if dir` guard added at `autoreload.py:20` (post-patch) | pure spec: admissibility of a configured entry (non-empty) |
| `keepLoader (entry)` | the `if directory and not is_django_path(directory)` guard at `autoreload.py:28` (post-patch) | pure spec: admissibility of a loader entry (non-empty AND not framework-owned) |
| `collectConfigured` / `collectLoader` (folds) | the two generator expressions as a whole | pure spec: per-entry filtered expansion |
| `normalizePath` *(opaque — A-consumed, free)* | `cwd / to_path(dir)` — `Path.cwd()` (`autoreload.py:14`) combined with `to_path` (`django/utils/_os.py:56`) | unchanged per-entry normaliser; OPAQUE free function, no asserted contract |
| `isFrameworkOwned` *(opaque — A-consumed, free)* | `is_django_path(directory)` — `django/utils/autoreload.py:54` | unchanged ownership predicate; OPAQUE free function, no asserted contract |

The patch changes ONLY the two `if` guards (adds `if dir` to site #1; adds
`directory and` to site #2's existing `not is_django_path(...)` guard). The
normaliser `cwd / to_path(...)` and the predicate `is_django_path(...)` are
UNCHANGED by the patch and are therefore left opaque.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a directory entry — a `str` (or `Path`) in `engine.dirs` / `get_dirs()` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; the empty `str` `""` ↔ `[]`. A `Path` entry maps to its string form; the only property the patch observes is emptiness/truthiness. |
| Python truthiness of a directory entry `dir` (`if dir`) | `entry ≠ []` (`keepConfigured`) | for a `str`/`Path` entry the only falsy value reachable here is the empty string `""` ↔ `[]`; every non-empty entry is truthy. `decide (entry ≠ [])` ↔ `bool(dir)`. |
| `is_django_path(directory)` → `bool` | `isFrameworkOwned entry : Bool` (opaque) | a free boolean function of the entry; the patch does not change it, so nothing is asserted about its value (G-CONF runs the same stand-in on both sides). |
| `cwd / to_path(dir)` → `Path` | `normalizePath entry : List Char` (opaque) | a free per-entry function; the patch does not change it. The collection's `set` semantics observe these normalised values; order/dedup is set-level and not part of the modeled R/I content. |
| `items` accumulation into a `set()` | `List (List Char)` (in entry order) | the model accumulates a list in input order; the repo dedups into a set. Dedup/order is not part of the patched behaviour (the patch only changes membership via the filter), so the list model faithfully captures the R/I content — which entries survive to be normalised. |

Lean `List Char` indexing is total and sound; the carrier is `List (List Char)`
because each site iterates over a list of directory entries, each a character
sequence whose only patched-observable property is emptiness.

## 3. Callee provenance (opaque free functions — no G-AX obligation)

Both callees the modeled sites defer to are UNCHANGED by the patch and are
modeled as OPAQUE free functions with **no asserted `ensures`**:

### 3.1 `normalizePath` ↔ `cwd / to_path(dir)` (opaque, A-consumed)
**Callee:** `Path.cwd() / to_path(entry)` (`to_path` at `django/utils/_os.py:56`
wraps a value in `pathlib.Path`; `cwd` from `autoreload.py:14`). The patch does
not touch this normalisation; it is consumed as an opaque term applied to each
retained entry. Nothing is claimed about its return value, so there is nothing
for G-AX to validate.

### 3.2 `isFrameworkOwned` ↔ `is_django_path(directory)` (opaque, A-consumed)
**Callee:** `is_django_path(path)` (`django/utils/autoreload.py:54`): returns
`True` if `path` is nested under Django's own package directory. The patch does
not change it — it only ANDs the new emptiness test in front of the existing
`not is_django_path(...)`. Modeled as an opaque free boolean; no asserted
contract, so no G-AX obligation.

**Why no consumed `_prop` axioms / no A-reference deep model:** the only
behaviour the patch CHANGES is the emptiness filter, which is modeled DEEPLY
(`keepConfigured`/`keepLoader` and the folds `collectConfigured`/`collectLoader`,
spelled out in the `pure` region). The two callees are left opaque precisely
because they are unchanged and the spec asserts nothing about them; an opaque
callee with no `ensures` cannot mask a wrong impl (the spec still forces the
emptiness-filter structure regardless of their values). Hence **G-AX is a skip**
(no `axiom_check.py`), exactly as for django__django-12276.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15572`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`keepConfigured`/`keepLoader` and the folds to Python; the A-tagged callees
(`normalizePath`, `isFrameworkOwned`) are run as the SAME deterministic
stand-in on both the shadow and the oracle (the patched generator expressions),
so they cancel and the differential test isolates the emptiness/ownership
filter — the only R/I content.
