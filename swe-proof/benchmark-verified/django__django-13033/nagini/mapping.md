# mapping.md — django__django-13033

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e`, states the type
abstraction, and documents the one structural fact about the standard string
`split` that the precondition encodes (validated by `axiom_check.py`).

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `ordering_mode(name, path_segments, relation_own_column, points_to_relation, has_default_ordering)` | the related-default-ordering decision inside `SQLCompiler.find_ordering_name` — `django/db/models/sql/compiler.py:715` (the guarding `if` at line 730) | the modeled changed decision predicate |
| `name` | `name` — the lookup string after `get_order_dir` strips the direction prefix (`compiler.py:722`) | full joined lookup path string |
| `path_segments` | `pieces = name.split(LOOKUP_SEP)` (`compiler.py:724`; `LOOKUP_SEP == '__'`, `django/db/models/constants.py:6`) | the lookup path split into its name segments |
| `path_terminal(path_segments)` (= `path_segments[-1]`) | `pieces[-1]` — the post-patch comparison operand (`compiler.py:730`) | final segment of the lookup path |
| `relation_own_column` | `getattr(field, 'attname', None)` (`compiler.py:730`) | the resolved relation field's attribute name (e.g. `root_id`) |
| `points_to_relation` | `field.is_relation` (`compiler.py:730`) | whether the resolved final field is a relation |
| `has_default_ordering` | `bool(opts.ordering)` — truthiness of the related model's `Meta.ordering` (`compiler.py:730`) | whether the related model declares a default ordering |
| `PK()` (= `'pk'`) | the string literal `'pk'` in `name != 'pk'` (`compiler.py:730`) | primary-key shortcut token |
| `Result()` (`mode` ∈ {0,1}) | which branch `find_ordering_name` takes: `1` = the related-model-default-ordering expansion branch (`compiler.py:731-747`); `0` = the direct-target branch (`compiler.py:748-749`) | observable decision outcome |

The pre-patch operand the change replaces (for the refinement audit, not
referenced from the consumer spec view): `getattr(field, 'attname', None) != name`
(`compiler.py:730`), i.e. comparing the attribute name against the WHOLE joined
path string instead of against the final segment `pieces[-1]`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (a name / segment / attname) | `PSeq[int]` of Unicode code points | `s[k]` ↔ `ord(s[k])`; `len`, `==`/`!=` mirror `str` length/equality |
| `name.split(LOOKUP_SEP)` → `list[str]` | `path_segments: PSeq[PSeq[int]]` (sequence of segment sequences) | `path_segments[i]` ↔ the i-th segment; `pieces[-1]` ↔ `path_terminal(path_segments) = path_segments[len-1]` |
| `field.is_relation` (`bool`) | `points_to_relation: bool` | identity |
| `bool(opts.ordering)` (truthiness of a possibly-empty tuple) | `has_default_ordering: bool` | identity (the predicate uses only the truthiness) |
| `getattr(field, 'attname', None)` (`str` or `None`) | `relation_own_column: PSeq[int]` | when `field` has no `attname` (`None`), the `!=` comparison is always true; modeled by a `relation_own_column` value distinct from every segment, so the abstraction is exact for the predicate's outcome |
| which `return` branch is taken | `Result() ∈ {0,1}` | `1` ↔ default-ordering-expansion branch; `0` ↔ direct-target branch |

`str` indexing/iteration is banned in Nagini, so segments are `PSeq[int]` and
the path is `PSeq[PSeq[int]]`.

## 3. The one structural fact (split invariant) — checked by axiom_check.py

The precondition

  `Implies(len(path_segments) > 1, name != path_terminal(path_segments))`

is NOT an axiom about a callee the proof consumes; it is the exact semantic
invariant of `name.split(LOOKUP_SEP)` (`compiler.py:724`): if splitting a string
on `'__'` yields more than one part, the original string contained the separator
`'__'` and therefore is strictly longer than — and unequal to — its final part
alone. (`pieces` is exactly `name.split('__')`, so `'__'.join(pieces) == name`.)

`axiom_check.py` validates this invariant against the real CPython
`str.split('__')` on boundary inputs (no separator, leading/trailing/repeated
separators, empty segments, the issue's `record__root_id` reproducer) plus
randomized fuzz: for every generated `name`, with `pieces = name.split('__')`,
it asserts `len(pieces) <= 1 or name != pieces[-1]`. stdlib-only; exit 0 iff the
invariant holds on every observation. There are no `@ContractOnly` axioms in
this bundle (the changed predicate is modeled deeply; no library callee is
consumed inside an `Ensures`).
