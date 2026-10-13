# mapping.md — django__django-16662

## Symbol binding (file:line @ base_commit 0eb3e9bd754e4c9fac8b616b705178727fc8031e)
Modeled function: the ordering applied to the collected import statements before
they are joined into the import block of a generated migration module,
`MigrationWriter.as_string`, `django/db/migrations/writer.py:176-179` (the
`sorted_imports = sorted(imports, key=...)` line). The gold patch changes the
sort key from the module name alone to the composite key
`(i.split()[0] == "from", i.split()[1])`, so plain `import ...` statements are
grouped ahead of `from ... import ...` statements, each group still ordered by
module name.

Lean modeled function name: `sortImportStatements` (neutral — it names the
*behavior* "order the import statements", not the patched local
`sorted_imports`; see G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `sortImportStatements` (modeled ordering) | `sorted(imports, key=...)`, `writer.py:178` (pre) / `:178-180` (post) |
| input `imports : List String` | `imports` — the `set()` of import-statement strings assembled at `writer.py:139-174` (each `"import X"` or `"from X import Y, Z"`) |
| `firstToken line` | `i.split()[0]` — the leading whitespace token (`"import"` / `"from"`) |
| `moduleName line` | `i.split()[1]` — the second whitespace token (the module name) |
| `isFromStatement line` | `i.split()[0] == "from"` — the boolean group key (post-patch) |
| `importLe a b` | the `<=` induced by `key = (i.split()[0] == "from", i.split()[1])` under Python tuple lexicographic order |
| result `List String` | `sorted_imports` — the ordered list joined by `"\n".join(...)` into `items["imports"]` |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| import-statement string (e.g. `"import datetime"`, `"from django.db import migrations, models"`) | `String` |
| `set[str]` of statements (the assembled `imports`) | `List String` (the membership-collapsed statement set; see note) |
| `i.split()[0]` (leading token) | `firstToken i = (i.splitOn " ").headD ""` |
| `i.split()[1]` (module token) | `moduleName i = (i.splitOn " ").getD 1 ""` |
| `i.split()[0] == "from"` | `isFromStatement i : Bool` |
| key `(i.split()[0] == "from", i.split()[1])` under Python tuple `<` | `importLe : String → String → Bool` (False<True on the group flag, then `String ≤` on the module) |
| `sorted(imports, key=...)` (stable merge sort) | `imports.mergeSort importLe` (Lean `mergeSort` is stable) |
| `sorted_imports : list[str]` | `result : List String` |

### Composite-key vs componentwise note
Python's `sorted` with `key=(g, m)` orders by the tuple **lexicographically**:
first by the group flag `g = (split()[0] == "from")` (False, i.e. plain
`import`, sorts before True, i.e. `from`), then by the module name `m`. Lean's
default `Prod` order is *componentwise*, NOT lexicographic, so the key is
modeled explicitly as `importLe`, a hand-written total preorder that encodes the
same lexicographic comparison: plain-before-from, then `moduleName ≤`. G-CONF
drives the real `key` lambda through Python's `sorted` and compares it list-for-
list against the `importLe` `mergeSort` shadow.

### `split()` vs `splitOn " "` note
Python `str.split()` (no argument) splits on arbitrary whitespace runs and drops
empty leading/trailing fields; the modeled statements are single-space-separated
canonical import lines (as produced by `writer.py`), so `splitOn " "` recovers
the same `[0]` and `[1]` tokens. G-CONF fuzzes only over canonical single-space
import lines (the shape the writer actually assembles), matching this bijection;
this restriction is logged in `conformance_check.py`.

### Set vs list / stability note
`imports` is a Python `set`, so the *input* statement order is unspecified, but
both `sorted(...)` and `mergeSort` are deterministic functions of the multiset of
statements and the key, and both are stable. We model the set as a `List String`
of distinct statements; because the output is fully determined by the key (ties
only among byte-identical statements, which `.only`-style dedup already
collapsed), stability never disagrees. G-CONF feeds the same statement list to
both legs and compares exact list equality.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `str.split()` is modeled deeply
  as `splitOn " "` + indexing (`firstToken`/`moduleName`), an I/R op, not an
  axiom. `sorted` is modeled deeply as `List.mergeSort`. There is no flag
  dependency — the key is a pure function of each statement string.

## G-LEAK
The problem_statement DOES contain the words `import`, `from`, `module`,
`sorted`, `migration` — these are public. It does NOT contain `writer`,
`as_string`, `sorted_imports`, `split`, or the patched file path. The spec view
uses only neutral behavioral vocabulary ("import statement", "module name",
"selective import", "canonical order"). The modeled-function identifier
`sortImportStatements` shares no patched def/class name as a substring (the patch
touches no `def`/`class` line — it edits a statement inside `as_string`). No
narration of the edit is present.

## Pinned G-CONF fuzz seed
`16662`.
