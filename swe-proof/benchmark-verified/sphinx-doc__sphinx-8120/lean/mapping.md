# mapping.md — sphinx-doc__sphinx-8120

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 795747bdb6b8fb7d717d5bbfc2c3316869e66a73
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
A message-catalog search path is assembled as an ordered list of locations: the
system default location first, then the bundled (built-in) defaults location,
then the caller-supplied locations. A downstream catalog loader walks this list
**in order**, and earlier locations take precedence over later ones (the first
catalog found is primary; later ones are merged in only as fallbacks). Because
the bundled defaults were placed *before* the caller-supplied locations, a
caller who supplied their own catalog could never override the bundled entries —
the bundled translation always won.

The gold patch rebuilds the search list so the caller-supplied locations come
*before* the bundled defaults location (the system default stays first):

```
# before (buggy):  [None, <bundled>] + list(<user dirs>)
# after  (fixed):  [None] + list(<user dirs>) + [<bundled>]
```

The relative order of caller-supplied locations vs. the bundled defaults is the
entire observable behavioral change. The order-walking precedence rule lives in
the *unchanged* downstream loader and is not modeled (no callee axiom needed —
see "Callee provenance").

## Two-file patch; only ONE behavioral site
| file | function (@ base_commit) | nature |
|---|---|---|
| sphinx/application.py | `Sphinx._init_i18n` — `sphinx/application.py:296` | **modeled site**: the search-list assembly that changes |
| sphinx/locale/__init__.py | `init` signature — `sphinx/locale/__init__.py:109` | **non-behavioral**: widens the parameter type annotation `List[str]` → `List[Optional[str]]` only. The list already contained `None` (the system-default sentinel) at base_commit; the annotation merely documents that. No runtime behavior changes, so it is not separately modeled. |

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_catalogSearchPath` | the `locale_dirs = …` assembly inside `Sphinx._init_i18n` (sphinx/application.py:296, post-patch lines 296–298) |
| `problem_spec_catalogSearchPath` | the post-condition that assembly must satisfy |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `userDirs : List String` | `list(repo.locale_dirs)` (list of str) | the caller-supplied catalog directories, in their given order |
| `packageLocale : String` | `path.join(package_dir, 'locale')` (str) | the single bundled-defaults directory path |
| `result : List (Option String)` | `locale_dirs` (list whose entries are `str` or `None`) | the assembled search path passed to the loader |
| `none` | `None` | the system-default location sentinel (kept first in both versions) |
| `some s` | the `str` `s` | a concrete directory path |

`String` ↔ Python `str` is the identity bijection (byte-for-byte). `Option
String` ↔ `Optional[str]`: `none ↔ None`, `some s ↔ s`. Lean `List` order ↔
Python `list` order (positional, identity).

## Callee provenance / flag deps
- No unchanged repo callee is consumed. `repo.locale_dirs` and
  `path.join(package_dir, 'locale')` are read as plain data (mapped to the inputs
  above). The only operation performed by the modeled fragment is list
  construction (literal `[None]`, list concatenation `+=`), modeled directly as
  Lean list construction / `++` (an **I**/**R** op — see refinement.md). The
  downstream `locale.init` order-precedence loop is unchanged and not invoked by
  the modeled fragment, so there is no `opaque` callee and no `axiom`. The
  `axioms` region is empty and `axiom_check.py` is a skip stub.
- No flag dependency: the assembly is unconditional (this branch runs whenever a
  language is configured). G-CONF fuzzes `userDirs` length ∈ {0, 1, …, k} and
  arbitrary directory strings, including the empty-`userDirs` case (where the
  bug is invisible) and non-empty cases (where it manifests).

## G-CONF fuzz seed
- pinned seed: `8120`
- ≥10^5 fuzzed `(userDirs, packageLocale)` tuples; `userDirs` drawn with lengths
  0–6 and random path-like strings, `packageLocale` a random path-like string.
