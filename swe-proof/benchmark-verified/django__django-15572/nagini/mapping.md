# mapping.md — django__django-15572

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0b31e024873681e187b574fe1c4afe5e48aeeecf`, states the type
abstraction, and gives the provenance of the one axiomatized callee.

Repo file under change: `django/template/autoreload.py`. The changed function is
`get_template_directories()` (`django/template/autoreload.py:10-30`), which
builds a `set` of normalized watched directories. The function contains two
collection sites; the gold patch adds a truthiness guard to each.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collect_direct_locations(entries)` | the first collection site — `items.update(cwd / to_path(dir) for dir in backend.engine.dirs)` (`django/template/autoreload.py:20`) | modeled changed site #1: the directly-declared directory entries |
| `collect_provider_locations(entries)` | the second collection site — `items.update(cwd / to_path(directory) for directory in loader.get_dirs() if not is_django_path(directory))` (`django/template/autoreload.py:25-29`) | modeled changed site #2: the auxiliary loader's directory entries |
| `beneath_framework(entry)` *(axiom — A-consumed, structural)* | `is_django_path` — `django/utils/autoreload.py:54-56` | unchanged callee: `Path(django.__file__).parent in Path(path).parents`; deterministic Boolean predicate the second site filters on |
| `is_present(entry)` | the truthiness test the gold adds: `if dir` / `if directory and ...` (`autoreload.py:20,28`) | pure spec: a raw entry carries a location iff it is non-empty |
| `join_base(entry)` | `cwd / to_path(entry)` (`autoreload.py:20,26`), with `cwd = Path.cwd()` (line 14) and `to_path` (`django/utils/_os.py:56-62`) | pure spec: the normalized watched location for one entry |
| `selected_direct` / `selected_provider` | the two generator-expression-into-`set.update` comprehensions | pure spec: the filtered-then-mapped subsequence emitted by each site |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a configured directory entry: a `str` (`""`, `"templates"`, an absolute path, …) or a `Path` | `int` token | the only property the change observes is the entry's **truthiness**. The reserved token `0` ↔ the empty entry `""` (the only falsy value Django's DIRS / loader dirs produce; `Path` instances and non-empty `str` are always truthy). Every other token `d ≠ 0` ↔ a distinct present entry. |
| `cwd / to_path(dir)` — the normalized `Path` for an entry | `join_base(entry)` (an `int` location token) | `to_path("")` is `Path(".")`, and `cwd / Path(".") == cwd` (the base location): the **empty** entry collapses onto the base. Model: `join_base(0) == 0` (the reserved base/cwd location token), `join_base(d) == d ≠ 0` for present entries (carries its own location token). This is the exact behavioural fact the F2P test turns on. **Scope note:** the relevant universal is the *empty-entry* collapse `cwd / to_path("") == cwd`. The converse — "*every* present (truthy) entry joins to a location distinct from the base" — is NOT a universal we assert: truthy dot-paths (`"."`, `"./."`, `Path(".")`) also normalize onto `cwd`. On the configured/tested entries the F2P/P2P tests exercise (`""`, `templates_extra`, absolute/relative strings, `Path(...)` — none a bare dot), a present entry does carry a distinct location, which is all the refinement needs; we do not claim it of arbitrary truthy strings. |
| the accumulating `set` `items`, `set.update(<genexpr>)` | a `List[int]` accumulated in order, with `ToSeq` carried as a `PSeq[int]` | a `set` is order- and duplicate-insensitive; the gold change adds/removes *which entries contribute a location*, never the set machinery. Modeling the collection as the ordered filtered-then-mapped subsequence is a sound refinement of "the set of contributed locations": two impls agree on the emitted subsequence ⇒ agree on the resulting set. The F2P assertion `get_template_directories() == set()` is exactly "the emitted subsequence is empty". |
| `for dir in backend.engine.dirs` / `for directory in loader.get_dirs()` | iteration over the `entries: List[int]` parameter | identity over the entry list. |

`str` indexing/iteration is banned in Nagini; but no character-level operation
is performed on an entry here — the change inspects only truthiness — so an
integer token (truthy ⇔ `≠ 0`) is the faithful, minimal carrier rather than
`List[int]` of code points.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `beneath_framework` ↔ `is_django_path` (A-consumed, structural only)
**Callee:** `django.utils.autoreload.is_django_path(path)`
(`django/utils/autoreload.py:54-56`):

```python
def is_django_path(path):
    """Return True if the given file path is nested under Django."""
    return Path(django.__file__).parent in Path(path).parents
```

This callee is **unchanged** by the gold patch (the gold only inserts the
`directory and` truthiness guard *before* the pre-existing
`not is_django_path(directory)` filter at the second site). The proof consumes
no value constraint on it — `beneath_framework` is declared `@Pure @ContractOnly`
with **no `Ensures`**, so the only property used is that it is a *deterministic
Boolean function of its entry* (which `@Pure` supplies). The second site's
filter is therefore `is_present(entry) and not beneath_framework(entry)`,
mirroring `directory and not is_django_path(directory)`.

**Soundness check (G-AX):** `axiom_check.py` executes the real `is_django_path`
on many inputs and asserts (a) it returns a `bool`, and (b) it is deterministic
(same input → same output across calls) — the entirety of the contract the
proof relies on. Because the axiom carries no value `Ensures`, no stronger
obligation exists to violate; the check confirms the only relied-on property.

### 3.2 The empty-entry collapse — `join_base(0) == 0` (deep model, validated)
The decisive behavioural fact — that joining the **empty** entry onto the base
yields the base location itself — is modeled DEEPLY by `join_base` /
`is_present` (not behind an axiom). `axiom_check.py` validates it against the
real `pathlib` + `to_path` composition: `Path.cwd() / to_path("") == Path.cwd()`
(the empty entry collapses to the base). This is the property the F2P test
`test_template_dirs_ignore_empty_path` (`DIRS: [""]` ⇒ result `set()`) observes.
Docs: https://docs.python.org/3/library/pathlib.html (`PurePath` joining;
`Path(".")` and `p / Path(".") == p`).

**Scope of the present-entry side (NOT a universal).** The complementary fact
used by the refinement is that, **on the configured/tested entries**
(`templates_extra`, absolute/relative path strings, `Path(...)` instances — the
F2P/P2P inputs), a present entry joins to a location distinct from the base, so
modelling a present token as a distinct non-zero location is faithful there.
This is *not* asserted as a universal over arbitrary truthy strings: a present
entry's truthiness (`bool(entry)`) is NOT equivalent to "joins to a distinct
location" — truthy dot-paths (`"."`, `"./."`, `Path(".")`) also normalize onto
`cwd` (`cwd / Path(".") == cwd`). No tested input is a bare dot, and the
soundness chain (verify ⟹ resolved) depends only on the empty-entry collapse
above plus distinctness on the tested entries; it does not depend on, and we do
not publish, the false universal "every truthy entry joins to a distinct
location". `axiom_check.py` therefore validates the empty-entry collapse as the
load-bearing universal, and present-entry distinctness only on the
configured/tested entries (plus the explicit dot-path family, documented there
as the boundary where truthiness and distinctness diverge).
