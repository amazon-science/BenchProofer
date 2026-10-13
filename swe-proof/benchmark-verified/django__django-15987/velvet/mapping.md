# mapping.md — django__django-15987

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7e6b537f5b92be152779fc492bb908d27fe7c52a`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of every callee. There are **no axioms** in this bundle: the changed
operation is modeled directly, and the only callee involved is a pure,
language-level string coercion modeled as an R-refinement (no consumed axiom,
no deep-model A-reference).

Repo file under change: `django/core/management/commands/loaddata.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `detectCollision (target : List Char) (entries : List Entry)` | the membership test of the per-app default-directory duplicate check, `Command.fixture_dirs` — `django/core/management/commands/loaddata.py:370` (`if app_dir in fixture_dirs:`, body of the loop opened at line 367) | the modeled changed function: does the candidate location coincide with any configured entry? |
| `target : List Char` | `app_dir` — `os.path.join(app_config.path, "fixtures")` (`loaddata.py:369`), a `str` | the per-app default fixtures directory being checked |
| `entries : List Entry` | `fixture_dirs` = `settings.FIXTURE_DIRS` (`loaddata.py:365`), a sequence whose elements are arbitrary path-likes (`str` OR `pathlib.Path`) | the configured collection searched for a collision |
| `Entry.text` | `str(d)` for an element `d` of `fixture_dirs` — the entry's canonical textual rendering | the value membership must compare on |
| `Entry.wrapped` | whether the element is a structured path object (`Path`) rather than a bare `str` | bookkeeping for the bijection; the fixed behaviour ignores it |
| `matchesText` | the post-patch membership expression `app_dir in [str(d) for d in fixture_dirs]` (`loaddata.py:370` post-patch) | pure spec: text-only membership |

There are no additional change sites: the gold patch edits exactly one line.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `app_dir` (a `str`) | `target : List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; equality of strings ↔ `List Char` `==` |
| an element `d` of `fixture_dirs` (a `str` or `pathlib.Path`) | an `Entry` value | `d ↦ Entry.mk (str(d)).toList (isinstance(d, Path))`. The model field `text` is the entry's **canonical textual rendering** `str(d)`; `wrapped` flags whether `d` is a structured object. |
| `str(d)` coercion (the per-element op the fix adds) | projection `Entry.text` (R) | `str` of a `str` is the identity; `str` of a `Path` is its canonical POSIX/OS path string. Both are captured by carrying `text = str(d)` in the bijection — so the coercion is observationally a projection to `text`, an R-refinement, **not an axiom**. |
| `x in seq` membership (`==` over the elements) | `matchesText target entries` (a disjunction of `Entry.text == target`) | Python `in` uses `==`; `str == str` is value equality; the model compares `text` values. |

The discriminating fact the issue is about: `str == Path` is **always `False`**
in Python (a `str` never `==` a `Path`, even when `str(path) == thestr`). So the
PRE-patch `app_dir in fixture_dirs` compares the `str` `app_dir` against raw
elements and never matches a `Path` element — a duplicate held as a `Path` goes
undetected. The model encodes this as: the buggy skeleton matches only entries
with `wrapped = false`, whereas the frozen spec `matchesText` matches on `text`
regardless of `wrapped`. `str(d)` normalizes both forms to the same `text`, so
the fixed membership is text-only — exactly `matchesText`.

Lean `String`/`List Char` is total and sound; the carrier for `target`/`text` is
`List Char` because the comparison is value-level string equality.

## 3. Callee provenance

**No consumed axioms; no deep-model A-references.** The single callee the patch
introduces is `str(d)`, the language-level string coercion. It is **not**
axiomatized: it is folded into the R-refinement above (each `Entry` carries its
already-coerced `text = str(d)`), and its observable effect — projecting any
path-like element to its canonical string — is validated mechanically by G-CONF
(`conformance_check.py` builds entries as both raw `str` and real `pathlib.Path`
values and compares the text-only shadow against `app_dir in [str(d) for d in
fixture_dirs]`). Hence `axiom_check.py` is intentionally absent and G-AX skips
(`no axiom_check.py (no axioms in bundle)`), exactly as for a pure-R/I bundle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15987`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`matchesText`/`detectCollision` (text-only membership) to Python; the oracle is
the patched hunk `app_dir in [str(d) for d in fixture_dirs]` exercised over
collections that mix plain-`str` and real `pathlib.Path` entries (the entry type
the issue concerns), with `app_dir` produced via `os.path.join` as in the repo.
