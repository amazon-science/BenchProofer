# mapping.md — django__django-15987

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7e6b537f5b92be152779fc492bb908d27fe7c52a`, states the type
abstraction, and gives the provenance of the A-reference the deep model is
validated against.

Repo file under change: `django/core/management/commands/loaddata.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `default_dir_is_listed(value_matches, is_path_object)` | the duplicate-detection membership test inside the `fixture_dirs` cached property — `django/core/management/commands/loaddata.py:370` (`if app_dir in fixture_dirs:`), within `fixture_dirs` defined at line 355 | the modeled changed decision (is the application's default fixtures directory already present in the configured directory collection?) |
| `value_matches[k]` | `str(d_k) == app_dir`, where `d_k` is the k-th entry of `settings.FIXTURE_DIRS` and `app_dir = os.path.join(app_config.path, "fixtures")` (line 369) | per-entry fact: entry k's path STRING equals the default directory's path string |
| `is_path_object[k]` | `isinstance(d_k, pathlib.PurePath)` — whether the k-th `FIXTURE_DIRS` entry is a path object vs. a plain `str` | per-entry fact: entry is a rich path object (raw `==` against a `str` is always `False`) |
| `any_match(eqs)` | the membership `app_dir in [...]` reduced to a disjunction over the entries | pure spec: whether some entry's path string equals the default one's |
| Result `True` | the branch is taken ⇒ `raise ImproperlyConfigured("... is a default fixture directory ... cannot be listed in settings.FIXTURE_DIRS.")` (lines 371-375) | the default directory is detected as already configured |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view): `app_dir in fixture_dirs` (line 370) —
a raw membership test of the `str` `app_dir` against the raw `FIXTURE_DIRS`
entries. The post-patch expression is `app_dir in [str(d) for d in fixture_dirs]`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `settings.FIXTURE_DIRS`, a list of directory entries each a `str` or a `pathlib.Path` | two parallel `List[bool]` `value_matches` / `is_path_object`, one slot per entry (same index, same length — pinned by the `len == len` Requires/Invariant) | entry `d_k` ↦ `(value_matches[k] = (str(d_k) == app_dir), is_path_object[k] = isinstance(d_k, PurePath))` |
| `app_dir` — the default fixtures directory path `str` (`os.path.join(app_config.path, "fixtures")`) | not a parameter: its only observable role is as the comparison target, fully captured by `value_matches[k]` (= "entry k's path string equals it") | — |
| `app_dir in [str(d) for d in fixture_dirs]` (post-patch membership over the str-coerced entries) | `any_match(ToSeq(value_matches))` | a disjunction of the per-entry value matches; `str(d)==app_dir` ↔ `value_matches[k]` (R2 below) |
| `app_dir in fixture_dirs` (pre-patch raw membership) | the prepatch loop's `value_matches[k] and not is_path_object[k]` | a plain-`str` entry raw-equals `app_dir` iff its value matches; a `PurePath` is never raw-`==` a `str`, so a path entry never raw-matches (R2) |
| taking the `True` branch / raising `ImproperlyConfigured` | `Result() == True` | the F2P assertion only observes whether the error is raised (`assertRaisesMessage`); the message text is unchanged by the patch |

Why `app_dir`/the entry strings are abstracted to per-entry booleans rather than
modeled as deep `List[int]` code-point sequences: the tested behaviour depends
only on *path-string equality* between each entry and the default directory
(membership), never on the concrete characters. The discriminating fact is
purely `str` vs. path-object under that equality — captured exactly by the two
booleans. (Cf. the django-11141 pattern: an irrelevant input — here the
path-object-ness — is pinned out of the postcondition RHS.)

## 3. A-reference (checked by G-AX / axiom_check.py) — no consumed axioms

There is **no `@ContractOnly` axiom** the proof consumes: `default_dir_is_listed`
is modeled deeply over the two booleans and the front-recursive fold `any_match`.
The one thing requiring out-of-band validation is the **faithfulness of the
per-entry abstraction** against the real Python path machinery — an A-reference.

### 3.1 `value_matches` / `is_path_object` ↔ `str` / `pathlib.PurePath` (A-reference)
**Callees:** `os.path.join`, `str(d)` for `d` a `str` or `pathlib.Path`, and the
`PurePath.__eq__` semantics. CPython:
- `str(pathlib.Path(p))` returns the path's string form; for any path `p`,
  `str(Path(cur) / "fixtures") == os.path.join(cur, "fixtures")` (the test's
  `Path(_cur_dir) / "fixtures"` equals the app's default `app_dir`).
- `pathlib.PurePath.__eq__` returns `NotImplemented` against a non-`PurePath`,
  so `Path(x) == "x"` is `False` for every `x` — a path object is never the
  identical value as the equivalent string. (CPython `Lib/pathlib.py`,
  `PurePath.__eq__`; docs https://docs.python.org/3/library/pathlib.html.)

Hence:
- **post-patch** `app_dir in [str(d) for d in fixture_dirs]` is exactly
  `∃k. str(d_k) == app_dir` = `any_match(value_matches)` (R1/R3);
- **pre-patch** `app_dir in fixture_dirs` is exactly
  `∃k. (d_k == app_dir)` = `∃k. value_matches[k] ∧ ¬is_path_object[k]`
  (a str entry raw-matches iff its value matches; a path entry never does) — the
  prepatch loop (R2/R3).

**Soundness check (G-AX):** `axiom_check.py` builds real configurations (the
explicit F2P scenario `FIXTURE_DIRS=[Path(_cur_dir) / "fixtures"]`, 9 boundary
cases over str/Path × match/no-match, and 20 000 randomized fuzz configs),
reduces each entry to `(value_matches, is_path_object)` with the REAL
`str()`/`isinstance` machinery, and asserts the modelled `any_match` equals the
real `app_dir in [str(d) for d in fixture_dirs]` AND the modelled prepatch loop
equals the real `app_dir in fixture_dirs`, plus that any string-equal `Path`
satisfies the str comparison but fails the raw one. stdlib-only
(`os.path`, `pathlib`); exit 0 iff sound.
