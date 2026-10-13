# mapping.md — django__django-13821

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e64c1d8055a3e476122633da141f16b50f0c4a2d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/backends/sqlite3/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `verifyVersion (info : List Nat) (versionStr : List Char)` | `check_sqlite_version()` — `django/db/backends/sqlite3/base.py:66` | the modeled changed function (the startup version guard) |
| `info : List Nat` *(param)* | `Database.sqlite_version_info` — module global read at `base.py:67` (`from sqlite3 import dbapi2 as Database`; `sqlite3.version_info`, a tuple of ints) | the reported SQLite version tuple |
| `versionStr : List Char` *(param)* | `Database.sqlite_version` — module global read at `base.py:68` (`sqlite3.sqlite_version`, a string) | the reported SQLite version string, echoed in the diagnostic |
| `lexLt` | the tuple `<` operator on `Database.sqlite_version_info` (`base.py:67`) | pure spec: lexicographic strict order on version tuples |
| `requiredVersion = [3, 9, 0]` | the literal `(3, 9, 0)` (`base.py:67`, post-patch) | pure spec: the minimum supported version |
| `errorMessage` | the `%`-interpolated string `'SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version` (`base.py:68-70`, post-patch) | pure spec: the diagnostic surfaced on failure |
| `checkSpec` | the body of `check_sqlite_version` (the `if … raise … else fall-through`) | pure spec: the whole guard outcome |

The pre-patch repo content the change replaces (refinement audit only, not in the
consumer spec view): the threshold `(3, 8, 3)` and the message text `'SQLite
3.8.3 or later is required (found %s).'` (`base.py:67-68` @ base_commit).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `Database.sqlite_version_info` — a tuple of ints, e.g. `(3, 8, 11, 1)` | `List Nat` | `t` (Python int tuple) ↔ `t`-shaped `List Nat`; tuple `<` ↔ `lexLt` (component-wise lexicographic order, prefix ranks below extension); both components are non-negative version numbers |
| `Database.sqlite_version` — a `str`, e.g. `"3.8.11.1"` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; on the ASCII version strings this is total and exact |
| the function's effect: `raise ImproperlyConfigured(msg)` vs. fall-through (`return None`) | `Except (List Char) Unit` | `Except.error m` ↔ raises `ImproperlyConfigured` whose `str(exc)` equals `m` (rendered to `str`); `Except.ok ()` ↔ no raise (returns `None`) |

`check_sqlite_version` takes no Python argument; it reads two module globals.
The spec lifts both to parameters (`info`, `versionStr`) so the guard is a total
function of its observable inputs — G-CONF drives the real function by
monkeypatching exactly these two globals (`conformance_check.py oracle_outcome`).

## 3. Callee provenance (kind-A)

**None.** This bundle has no consumed axioms and no deep-model references. The
function under spec calls no unchanged repo callee whose behaviour the proof
relies on:

* the version comparison is Python tuple `<` — a language primitive, modeled
  deeply by `lexLt` (an I-op, refuted directly by G-CONF), not axiomatized;
* the diagnostic assembly is `%`-string interpolation — a language primitive,
  modeled deeply by `errorMessage`'s `List Char` concatenation (an I-op);
* `ImproperlyConfigured` is a plain exception constructor (the raise/no-raise
  outcome is the `Except` carrier itself), not a callee with a relied-on
  property.

Therefore `axiom_check.py` is absent and **G-AX skips** (`no axioms in bundle`).
All soundness rests on refinement fidelity (refinement.md, audited by G-EQ and
mechanically refuted by G-CONF).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13821`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `lexLt`/`checkSpec`/`errorMessage` (all R/I-tagged ops) to Python
(`tuple(info) < (3, 9, 0)` and the `%`-message) and drives the real patched
`check_sqlite_version` by monkeypatching `Database.sqlite_version_info` and
`Database.sqlite_version`. There are no A-tagged callees to leave as real.
