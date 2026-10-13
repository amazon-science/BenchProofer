# mapping.md — django__django-15572

## Instance
- repo: django/django
- base_commit: `0b31e024873681e187b574fe1c4afe5e48aeeecf`
- changed file: `django/template/autoreload.py`
- changed function: `get_template_directories()` (file:10–30 @ base_commit)
- spec_provenance: **cold** (derived from problem_statement + gold patch + repo source only)

## What the function does
`get_template_directories()` iterates the configured template backends and
collects, into a **set**, the normalized absolute directory paths the autoreload
watcher should watch. For each `DjangoTemplates` backend it gathers:

1. the backend's configured dirs (`backend.engine.dirs`), and
2. for each loader exposing `get_dirs`, the loader dirs, **excluding** those that
   are framework-internal (`is_django_path(directory)`).

Each directory string `d` is normalized to an absolute path via
`cwd / to_path(d)` (`Path.cwd()` joined with `to_path(d)`), and the union of all
such paths is returned as a `set`.

## The behavior under spec (the fix)
Normalization turns a falsy/empty directory entry (e.g. the empty string `""`)
into the project-root path, which then incorrectly enters the result set. The
fix adds a truthiness guard at **both** collection sites:
- backend dirs: keep `d` only when `d` is non-empty (`if dir`).
- loader dirs: keep `d` only when `d` is non-empty **and** not framework-internal
  (`if directory and not is_django_path(directory)`).

So a path is in the result iff it is the normalization of a **non-empty**
backend dir, or of a **non-empty, non-framework** loader dir.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
| Python | Lean | notes |
|---|---|---|
| directory entry (`str`) | `String` | a directory configured by the user |
| backend dirs `backend.engine.dirs` (flattened over backends) | `dirs : List String` | R: list models the iteration order of the generator source |
| loader dirs `loader.get_dirs()` (flattened over backends/loaders) | `loaderDirs : List String` | R: flatten the nested `for backend / for loader` iteration |
| normalized path `cwd / to_path(d)` | `resolveDir d : String` | callee passthrough; `resolveDir : String → String` is a parameter (universally quantified — the property holds for ANY normalizer) |
| `is_django_path(directory)` (truthy) | `isFrameworkPath d = true` | callee passthrough; `isFrameworkPath : String → Bool` is a parameter |
| falsy directory `not dir` | `d = ""` | for a directory `str`, falsy ⇔ empty string; the regression's trigger value is `""` |
| result `set()` of paths | `result : List String`, characterized by membership `∈` | a Python set: order/multiplicity irrelevant, so the spec pins set membership via `↔`, which is dedup-insensitive |

## Callee provenance
- `to_path` / `Path.cwd()` / `Path.__truediv__` (the `cwd / to_path(d)` normalizer):
  unchanged std/django path machinery. Modeled as the **parameter**
  `resolveDir : String → String`. Because it is universally quantified, the proof
  consumes **no** property of it (A-reference / passthrough, not A-consumed).
- `is_django_path` (`django/utils/autoreload.py`): unchanged predicate marking
  framework-internal paths. Modeled as the **parameter**
  `isFrameworkPath : String → Bool`. Universally quantified ⇒ no consumed
  property (A-reference / passthrough).

Because both callees are abstract universally-quantified parameters, there is **no
consumed axiom** and nothing for G-AX to validate (axiom_check.py is a skip stub).

## Flag dependencies
None. The fix is unconditional truthiness filtering at both sites.

## Independently-fixed behaviors
The two hunks add the same kind of guard (drop falsy dirs) at two sites. The
modeled function covers both; the prepatch reverts the backend-dir guard (the
behavior the FAIL_TO_PASS test `test_template_dirs_ignore_empty_path` exercises,
via `DIRS=[""]`). The loader-dir guard is reverted in the same prepatch's loop as
well so the spec sees both omissions.

## G-CONF fuzz seed
`seed = 15572` (pinned). Inputs: random `List String` for `dirs` and
`loaderDirs` drawn from a small alphabet including `""`, plus an injected
`isFrameworkPath` predicate and `resolveDir` normalizer.
