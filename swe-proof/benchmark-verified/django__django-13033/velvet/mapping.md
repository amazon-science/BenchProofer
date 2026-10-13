# mapping.md — django__django-13033

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e`, states the type
abstraction (the bijection a conformance gate would use to bridge Lean↔Python),
and records callee provenance and flag dependencies.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `orderingExpansionDecision (...)` | the relation-default-ordering guard of `SQLCompiler.find_ordering_name` — `django/db/models/sql/compiler.py:730` (the `if field.is_relation and opts.ordering and … and name != 'pk':` line) | the modeled changed decision |
| `appendRelatedDefaultOrdering` | the boolean value of that `if` condition | pure spec: the guard, with the terminal-segment comparison |
| `terminalSegment segments` | `pieces[-1]` — the last element of `pieces = name.split(LOOKUP_SEP)` (`compiler.py:723`) | pure spec: the terminal lookup segment |
| `segments` | `pieces` (`name.split(LOOKUP_SEP)`, `LOOKUP_SEP == '__'`) | the split lookup path |
| `lookup` | `name` (the lookup name after `get_order_dir` strips the `-` direction, `compiler.py:722`) | the whole joined lookup path |
| `fieldAttr` | `getattr(field, 'attname', None)` (`compiler.py:730`) | the resolved field's stored attribute name (e.g. `editor_id` for FK `editor`) |
| `fieldIsRelation` | `field.is_relation` | whether the resolved field is a relation |
| `modelHasDefaultOrdering` | truthiness of `opts.ordering` | whether the pointed-to model declares a default ordering |

`field`, `fieldAttr`, `segments`/`pieces` and the join state are all produced by
`field, targets, alias, joins, path, opts, transform_function =
self._setup_joins(pieces, opts, alias)` (`compiler.py:726`) — UNCHANGED by the
patch and shared identically by both branches. The patch changes only the third
conjunct of the guard.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| a lookup name `name` (`str`, e.g. `"author__editor_id"`) | `List Char` (`lookup`) | `s` ↔ `s.toList`; equality of names ↔ `List Char` `==` / `!=` |
| `pieces = name.split('__')` (`list[str]`) | `List (List Char)` (`segments`) | each segment `str` ↔ `List Char`; `pieces[-1]` ↔ `segments.getLast!` (`terminalSegment`); precondition `segments ≠ []` mirrors `split` always returning ≥1 element |
| `getattr(field, 'attname', None)` (`str` or `None`) | `Option (List Char)` (`fieldAttr`) | present attr `str` ↔ `some s.toList`; absent (`None`, e.g. non-field) ↔ `none`; `!= name`/`!= pieces[-1]` ↔ `!= some lookup` / `!= some (terminalSegment segments)` |
| `field.is_relation` (`bool`) | `Bool` (`fieldIsRelation`) | identity |
| truthiness of `opts.ordering` (a possibly-empty list) | `Bool` (`modelHasDefaultOrdering`) | non-empty ordering ↔ `true`; empty/absent ↔ `false`. The guard only consumes the truthiness, so the Bool abstraction is exact for this decision. |
| the literal `'pk'` | `"pk".toList` | `name != 'pk'` ↔ `lookup != "pk".toList` |

The decision's Python value is `bool(field.is_relation and opts.ordering and
getattr(field,'attname',None) != pieces[-1] and name != 'pk')`. Python `and`
short-circuits and yields the operands' truthiness; because every operand here
is modeled at `Bool`/equality level, the Lean `&&` chain is observationally
identical to the Python `and` chain for the guard's boolean outcome.

## 3. Callee provenance

No axiomatized callees and no A-reference deep models of outside callees. The
only callee involved, `self._setup_joins` (and beneath it `query.setup_joins`),
is UNCHANGED by the patch and produces the operands `field`, `fieldAttr`,
`segments`, `lookup` that BOTH the pre- and post-patch guard read identically.
It is therefore not part of the modeled decision — it is shared context, not a
contract the proof consumes. The patch's entire behavioral content is the
third conjunct's operand: `pieces[-1]` (terminal segment) vs `name` (whole
joined path).

Flag/config dependencies: none. The guard's branch does not depend on any
runtime flag beyond the resolved field metadata already abstracted in §2.

## 4. G-CONF: skipped (conf_skip = true)

There is no DB-free R/I shadow of this decision. The operands that drive the
discriminating conjunct (`field`, its `attname`, the split `pieces`, and `name`)
are resolved by `_setup_joins` against a live ORM model graph and the query's
join machinery; reproducing the bug-triggering tuple (a self-referential FK
whose `attname` equals the terminal lookup segment, so `attname == pieces[-1]`
while `attname != name`) requires standing up the model classes, their `_meta`,
and a compiled query — i.e. the F2P integration test
`test_order_by_self_referential_fk` itself, not a pure transliteration a gate can
fuzz. Per SPEC_GUIDE §0 / WORKER_PROMPT, `meta.json conf_skip=true` and
`conformance_check.py` is a `status=skip` stub. Soundness of the modeled guard
rests on G-VERIFY (`appendRelatedDefaultOrdering` provably equals the
terminal-segment formulation the impl computes) + G-DIFF (the prepatch's
whole-path comparison fails the postcondition exactly on a multi-segment lookup
ending at the field's stored attribute), the django__django-13315 precedent.
No pinned fuzz seed (no fuzzing performed).
