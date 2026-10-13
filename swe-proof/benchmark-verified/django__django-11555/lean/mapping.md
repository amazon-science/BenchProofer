# mapping.md — django__django-11555

## Instance
- base_commit: `8dd5877f58f84f2b11126afbd0813e24545919ed`
- changed file: `django/db/models/sql/compiler.py`
- changed function: `SQLCompiler.find_ordering_name`
  (file:line @ base_commit — `django/db/models/sql/compiler.py:700` def;
  the patched loop is at lines 722–727).

## What the fix is
Inside `find_ordering_name`, when the resolved field is a relation and the
related model carries a `Meta.ordering`, the method iterates that ordering
specification (`opts.ordering`) and recursively expands each `item` by calling
`self.find_ordering_name(item, …)`. That recursive call ultimately runs
`get_order_dir(item, …)` (`django/db/models/sql/query.py:2212`), whose first
operation is `field[0] == '-'` — it assumes `item` is a *string* field name.

But a model's `Meta.ordering` may contain already-built ordering **expression**
objects (instances of `django.db.models.expressions.OrderBy`, e.g. produced by
`models.F('author').asc(...)`), not just strings. Indexing `OrderBy[0]` raises,
crashing the query (observed during multi-table-inheritance ordering by a
parent pointer field).

The fix adds a per-item dispatch at the top of the loop body: if `item` is an
`OrderBy` instance, append `(item, False)` to `results` and `continue` (skip the
recursive name resolution); otherwise resolve as before.

## Symbol binding (Lean ↔ Python)
| Lean | Python | notes |
|---|---|---|
| `OrderingItem` | element of `opts.ordering` | either a `str` field name or an `OrderBy` expression |
| `OrderingItem.fieldRef name` | a `str` item in `opts.ordering` | the resolvable name (lookup path) |
| `OrderingItem.expression e` | an `OrderBy` item in `opts.ordering` | the `isinstance(item, OrderBy)` branch |
| `OrderExpr` | `django.db.models.expressions.OrderBy` | opaque; only carried, never inspected |
| `(OrderExpr × Bool)` | the `(expr, is_ref)` tuple `results` collects | the `False` second component is the literal `False` in the patch |
| `resolveFieldRef item` | `self.find_ordering_name(item, opts, alias, order, already_seen)` | UNCHANGED callee; expands a name item into directives |
| `implementation_expandOrdering items` | the `results = []; for item in opts.ordering: …; return results` block | the patched loop |
| `items.flatMap expandOrderingItem` | the full in-order expansion of `opts.ordering` | spec carrier |

## Type bijection (G-CONF / G-AX)
- `opts.ordering` (a tuple/list whose elements are `str` or `OrderBy`)  ↔
  `List OrderingItem`. A Python `str` element ↦ `OrderingItem.fieldRef <str>`;
  an `OrderBy` element ↦ `OrderingItem.expression <id>`.
- `results` (a Python `list` of `(OrderBy, bool)` tuples) ↔
  `List (OrderExpr × Bool)`. The patch only ever appends `(item, False)` for the
  expression branch; the `False` is the literal flag.
- The descending direction passed *into* the recursion (`order`) and the
  `already_seen` loop guard are not observed by the modeled per-item dispatch:
  the dispatch decision depends ONLY on whether the item is an `OrderBy`. They
  are part of the unchanged `resolveFieldRef` callee's behavior.

## Callee provenance + flag deps
- `resolveFieldRef` ← `SQLCompiler.find_ordering_name` (the recursive call on a
  string item). UNCHANGED by the patch on the string-item path. It is referenced
  identically in the spec helper `expandOrderingItem` and in the impl, so it is
  an **A-reference** (deep-modeled dispatch; the callee itself is not
  axiomatized) — not a consumed axiom. No flag configuration changes its
  dispatch role here.
- No `_prop` axiom is consumed by the modeled dispatch: the spec is a pure
  structural concatenation (`flatMap`) and the proof discharges by induction on
  the list with `List.forIn_cons` (no callee property needed).

## G-CONF fuzz seed
- pinned seed: `11555`
- fuzz domain: random `opts.ordering` lists mixing `str` field names and
  `OrderBy` expression markers (length 0–12), checking the dispatch (expression
  ⇒ `(item, False)` emitted directly; string ⇒ routed to the resolver) matches
  the patched behavior over ≥10⁵ inputs.
