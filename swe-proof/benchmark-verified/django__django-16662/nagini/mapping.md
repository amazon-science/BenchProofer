# mapping.md — django__django-16662

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0eb3e9bd754e4c9fac8b616b705178727fc8031e`, states the type
abstraction, and gives the provenance of the comparison the model is validated
against (G-AX / axiom_check.py).

Repo file under change: `django/db/migrations/writer.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `arrange_lines(flags, modules)` | the import-ordering step inside `MigrationWriter.as_string` — `django/db/migrations/writer.py:176-179` (the `sorted_imports = sorted(imports, key=...)` call) | the modeled changed behaviour: arrange the import lines into output order |
| `compkey(is_from, module)` | the sort **key** `lambda i: (i.split()[0] == "from", i.split()[1])` — `django/db/migrations/writer.py:178` (post-patch) | pure spec: the per-line ordering key, the pair (group flag, module token), linearised to one integer |
| `flags[k]` | `i.split()[0] == "from"` for line `i` (1 if the line begins with `from`, else 0) | group flag of line k |
| `modules[k]` | `i.split()[1]` for line `i` (the module-name sort token: the word after `import` in `import X` or after `from` in `from Y import ...`) | order-preserving integer code of line k's module name |

`as_string` builds the set `imports` of fully-formed import-statement strings
(e.g. `"import datetime"`, `"import time"`, `"from django.db import migrations,
models"`), then orders them with `sorted(imports, key=...)` and joins them with
newlines (`writer.py:179`). The only thing the patch changes is the sort key
(`writer.py:178`); everything before and after (building the set, the join, the
template fill) is unchanged and observationally irrelevant to the tested
ordering. The modeled function captures exactly that sort.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an import-statement `str` `i` | the pair `(flags[k], modules[k])` of two ints | each line is reduced to the two whitespace-split tokens the key reads: `i.split()[0] == "from"` ↔ `flags[k] ∈ {0,1}`; `i.split()[1]` (the module token) ↔ `modules[k]`, an integer code. The full string is the carrier of these two attributes; the rest of the string never participates in the ordering decision. |
| the module-name token `str` `i.split()[1]` | `modules[k]: int`, an **order-preserving** code | `module_a < module_b` (Python `str` `<`, the secondary key's comparison) ↔ `code(module_a) < code(module_b)`. Any injective code respecting the lexicographic order of the distinct module tokens present is a valid witness; bounded `0 ≤ code < 1e9` so the linearisation below is order-preserving. (Standard `str`→order-code abstraction; Nagini bans `str` indexing.) |
| the tuple key `(i.split()[0]=="from", i.split()[1])` | `compkey(flags[k], modules[k]) = flags[k]*1e9 + modules[k]` | tuple `<` (lexicographic, group flag primary) ↔ integer `<` on `compkey`. Order-preserving because `0 ≤ module < 1e9`: the flag term dominates, so flag-0 lines key strictly below flag-1 lines, and within a flag the module code decides — exactly Python's tuple comparison on `(bool, str)`. |
| `sorted(imports, key=k)` (a stable comparison sort producing the ascending-by-key permutation) | `arrange_lines` — a comparison arrangement pinned by the postcondition to be a **sorted rearrangement** (`ToMS` preserved + ascending) | same operation (kind I): produce the permutation of the inputs that is ascending in the key. Stability is unobservable here because the keys of distinct import lines are distinct (distinct `(group, module)` pairs — `imports` is a set and the two attributes determine the line), so the sorted permutation is unique and any correct sort yields it. |

### Modeled-domain choice (three lines)

The modeled domain is fixed at **three** import lines. This is the minimal
configuration that exhibits the discriminating behaviour — a from-import line
whose module token sorts before a plain-import line's module token (the F2P
configuration: `import datetime`, `import time`, `from django.db import
migrations, models`, where `django.db` < `time` lexicographically yet the
from-line must follow both plain imports). A general-`N` verified comparison
sort with a maintained pairwise-ordering invariant does not converge within the
verifier's hard 300s wall in Nagini 1.2.0 (the cross-region two-variable
sortedness invariant is a Z3 wall, measured: two 290s timeouts); per the project's
operational rule the modeled domain is shrunk to the configuration that
witnesses the change. On three lines the sort is unrolled into straight-line
comparisons and the spec is FULLY tight (sorted + multiset-preserving — no
gaps), so no wrong arrangement of the three lines verifies (G-EQ).

## 3. The ordering reference (A-reference — checked by G-AX / axiom_check.py)

There is **no `@ContractOnly` axiom**. The changed decision — the ordering key —
is modeled deeply (`compkey`); the sort itself is the standard library
`sorted`, the unchanged comparison engine. The one fact the refinement leans on
that lives outside the verified text is the **order-preservation of the
linearisation**: that ascending integer order on `compkey(f, m)` agrees with
ascending order on the real pair key `(is_from, module)` = `(i.split()[0]=="from",
i.split()[1])`. This is an **A-reference**: validated equal to the real callee
out-of-band by `axiom_check.py` (G-AX), not consumed as an axiom.

**Real callee:** CPython `sorted(iterable, key=...)` with the gold key
`lambda i: (i.split()[0] == "from", i.split()[1])`
(`django/db/migrations/writer.py:178`, post-patch). `sorted` is stable and orders
by Python's tuple comparison on `(bool, str)`, which is lexicographic with the
bool (group flag) dominating — `False (0)` before `True (1)`. Docs:
https://docs.python.org/3/library/functions.html#sorted ;
tuple ordering: https://docs.python.org/3/reference/expressions.html#comparisons .

**Soundness check (G-AX):** `axiom_check.py` (stdlib-only) asserts, on boundary
pairs over the two group flags and many module tokens plus randomized fuzz:
(a) `compkey(f, m) < compkey(f', m')` **iff** the real tuple key
`(bool(f), name_m) < (bool(f'), name_m')`, with `m`/`name_m` ranging over an
order-preserving code/name correspondence — i.e. the linearisation is exactly
the tuple order; and (b) running the **real** `sorted` with the **real gold key**
on assembled import-line strings produces the grouped order the model's
ascending-`compkey` arrangement encodes (all plain imports before all
from-imports, module-ordered within each group), and in particular reproduces
the F2P observation `import datetime`, `import time`, `from django.db import
migrations, models`. It also confirms the **pre-fix** key
`lambda i: i.split()[1]` produces the rejected interleaved order on that same
configuration. Exit 0 iff sound. It imports only `random` and `sys` (no repo
code; the gold key is a one-line lambda reproduced verbatim).
