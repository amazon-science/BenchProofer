# mapping.md — django__django-13033

## Symbol binding (file:line @ base_commit a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e)

Modeled function: the default-ordering-expansion decision inside
`SQLCompiler.find_ordering_name(self, name, opts, alias=None,
default_order='ASC', already_seen=None)`,
`django/db/models/sql/compiler.py:715-749` (the guard at line 730 that decides
whether the related model's `Meta.ordering` is appended).

The gold patch changes the guard so that the resolved field's own stored
attribute is compared against the lookup path's FINAL SEGMENT (`pieces[-1]`)
rather than against the WHOLE lookup `name`. When the ordering directly
designates a relation's stored column via a multi-segment lookup (e.g.
`record__root_id`), the final segment (`root_id`) equals the field's attribute,
so post-patch the guard is skipped and the column is ordered directly; pre-patch
the whole path (`record__root_id`) differs from the bare attribute (`root_id`),
so the guard wrongly fired and expanded the related model's default ordering.

Lean modeled function name: `orderingExpandsRelation` (names the *behavior* —
"does ordering by this related-field lookup expand into the relation's default
ordering" — at the abstract level).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `fieldIsRelation : Bool` | `field.is_relation` (`compiler.py:730`); `field` is the field resolved by `_setup_joins(pieces, opts, alias)` (`compiler.py:725`) |
| `relatedHasOrdering : Bool` | truthiness of `opts.ordering` (`compiler.py:730`) — whether the resolved model's `Meta.ordering` is non-empty |
| `fieldAttr : Option String` | `getattr(field, 'attname', None)` (`compiler.py:730`) — the field's stored attribute name, `None` when the field has no `attname` ↔ `none` |
| `path : String` | `name` (`compiler.py:730`), the lookup path AFTER `get_order_dir` strips the direction prefix (`compiler.py:722`) — e.g. `"record__root_id"` |
| `lastSegment path` | `pieces[-1]` (`compiler.py:732` post-patch), where `pieces = name.split(LOOKUP_SEP)` (`compiler.py:724`, `LOOKUP_SEP = '__'`, `django/db/models/constants.py:6`) |
| `path != "pk"` | `name != 'pk'` (`compiler.py:730`) — the primary-key shortcut exclusion |
| `result : Bool` | whether control enters the `if` body (`compiler.py:731-747`) that recurses into `opts.ordering` and appends the related model's default ordering; `false` = fall through to the direct-column branch (`compiler.py:748-749`) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `field.is_relation : bool` | `fieldIsRelation : Bool` |
| `bool(opts.ordering)` (non-empty ordering tuple) | `relatedHasOrdering : Bool` |
| `getattr(field, 'attname', None)` (`str` or `None`) | `fieldAttr : Option String` |
| `name : str` (direction-stripped lookup path) | `path : String` |
| `name.split('__')[-1]` | `(path.splitOn "__").getLastD ""` (`lastSegment path`) |
| `getattr(field,'attname',None) != pieces[-1]` | `fieldAttr != some (lastSegment path)` |
| `name != 'pk'` | `path != "pk"` |
| enters default-ordering-expansion branch | `result = true` |

### `name` vs `pieces[-1]` modeling note
`get_order_dir(name, default_order)` (`compiler.py:722`) strips a leading `'-'`
direction prefix and returns the bare lookup string; that bare string is `name`
as seen at line 730, and `pieces = name.split('__')` (line 724). So `pieces[-1]`
is exactly the final `'__'`-separated segment of `name`. The Lean model takes
`path` to be that direction-stripped lookup and computes `lastSegment path` by
`splitOn "__"`. `String.splitOn` on a non-empty separator always returns a
non-empty list, so `getLastD ""` yields the final segment for every input
(`""` only for the empty path, which the optimizer never produces). The
`get_order_dir` direction-stripping is upstream of the modeled guard and equally
present pre- and post-patch, so it is part of the resolution that yields the free
input `path`, not part of the decision.

### attname / `None` bijection
`getattr(field, 'attname', None)` is `None` for fields without a stored attribute
(e.g. reverse relations) and a `str` (e.g. `"root_id"`, `"author_id"`) for a
concrete FK/column field. Modeled `Option String`: `None ↔ none`, `"s" ↔ some s`.
The comparison `!= pieces[-1]` is string inequality; `None != pieces[-1]` is
always `True` in Python (a `None` attname never equals any segment string),
matching `none ≠ some _` in Lean.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The decision reads four
  already-resolved observations (`field.is_relation`, `opts.ordering`,
  `field.attname`, the lookup `name`) and computes `name.split('__')[-1]`
  directly. `field`/`opts`/`joins`/`targets` are produced by `_setup_joins` /
  `setup_joins`, which the patch does NOT change and which run identically on
  both sides of the guard; they are read as the free inputs of the modeled
  boolean decision. The only computation the guard itself performs — the split
  and the equality/inequality tests — is modeled deeply (`String.splitOn`,
  `Option`/`String` (in)equality). So no `opaque`/`axiom` callee contract is
  required ⇒ `axioms = []`, `deep_model_references = []`, `axiom_check.py` is a
  skip stub (G-AX skips).
- No flag dependency: the guard fires purely on the four observations above;
  `default_order`/`descending` affect only the recursion's sort direction, not
  whether the branch is entered.

## G-LEAK
The solver-visible `problem_statement` publicly discusses `order_by`, the
`Meta.ordering` default ordering, foreign keys, the `_id` relation column, and
the lookup syntax (`record__root_id`, `record__root`, `record__root__id`). The
gold diff's only changed symbol is the guard inside `find_ordering_name`. The
spec view names no patched file path, reproduces no gold-diff line, includes no
diff marker, and narrates no bug→fix mechanism; the docstring states the abstract
desired expansion behavior only. (`find_ordering_name`, `pieces`, `attname`,
`is_relation` appear NOWHERE in the spec view — neither in identifiers nor
comments.)

## Pinned G-CONF fuzz seed
`13033`.
