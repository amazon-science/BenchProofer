# refinement.md — django__django-13033

Maps every operation in `implementation_orderingExpandsRelation` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `orderingExpandsRelation` (`SQLCompiler.find_ordering_name` guard)

Post-patch repo code (`patch.diff`), the relevant guard of `find_ordering_name`:
```python
if (
    field.is_relation and
    opts.ordering and
    getattr(field, 'attname', None) != pieces[-1] and
    name != 'pk'
):
    # … recurse into opts.ordering, append related model's default ordering …
    return results
targets, alias, _ = self.query.trim_joins(targets, joins, path)
return [(OrderBy(transform_function(t, alias), descending=descending), False) for t in targets]
```
where `pieces = name.split(LOOKUP_SEP)` (`LOOKUP_SEP = '__'`) and `name` is the
direction-stripped lookup path from `get_order_dir`.

Lean impl (`implementation_orderingExpandsRelation`): a boolean dispatch over the
same four conjuncts, returning whether the default-ordering-expansion branch is
entered.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `fieldIsRelation relatedHasOrdering : Bool`, `fieldAttr : Option String`, `path : String` | `field.is_relation`, `bool(opts.ordering)`, `getattr(field,'attname',None)`, and the lookup `name` — the already-resolved observations the guard reads (mapping.md bijection) | **R** | the join/field resolution (`_setup_joins`) is unchanged by the patch and runs identically on both sides; its outputs are read as the decision's free inputs. `field.attname or None` ↔ `Option String`; `opts.ordering` truthiness ↔ `Bool`. |
| 2 | `lastSegment path = (path.splitOn "__").getLastD ""` | `pieces[-1]` where `pieces = name.split('__')` (`compiler.py:724,732`) | **I** (the changed op, deeply modeled) | **the fixed operation.** The patch replaces `name` with `pieces[-1]` in the third conjunct. `name.split('__')[-1]` ↔ `(path.splitOn "__").getLastD ""`; `String.splitOn` on a non-empty separator always returns a non-empty list, so the final segment is total (mapping.md split note). The prepatch impl compares against the WHOLE `path` (pre-patch `name`). |
| 3 | `fieldAttr != some (lastSegment path)` | `getattr(field,'attname',None) != pieces[-1]` | **I** | identical inequality; `None != s` ↔ `none ≠ some s` (always true); `"a" != "a"` ↔ `some "a" ≠ some "a"` (false). |
| 4 | `fieldIsRelation && relatedHasOrdering && (fieldAttr != some (lastSegment path)) && (path != "pk")` then `return true` | `if field.is_relation and opts.ordering and getattr(field,'attname',None) != pieces[-1] and name != 'pk':` (enters expansion branch) | **I** | identical four-way conjunction with identical short-circuit semantics; `name != 'pk'` ↔ `path != "pk"`. |
| 5 | `return false` | fall through past the `if` to `trim_joins` + the direct `OrderBy` on the resolved targets (`compiler.py:748-749`) | **R** | the guard being false means "no default-ordering expansion; order by the column directly." Modeled as `result = false`; the concrete direct-column `OrderBy` construction is not part of the modeled boolean decision (unchanged by the patch). |
| 6 | `Id.run do … return …` (`Bool`) | whether control enters the `if` body | **R** | the entire modeled outcome is the boolean "expansion branch entered?"; the recursion's contents and the direct branch are downstream of the decision and unchanged by the patch. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `find_ordering_name` guard decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_orderingExpandsRelation` pins the result as an `iff` against the
  exact four-conjunct condition (directive 5 — frame: the boolean output is fully
  determined for every input; directive 8 — every conjunct is grounded in the
  inputs `fieldIsRelation`/`relatedHasOrdering`/`fieldAttr`/`path`, no ungrounded
  oracle). A verifying impl must return `true` exactly on the modeled condition.
- The discriminating clause is `fieldAttr ≠ some (lastSegment path)`. For the F2P
  case — a self-referential FK ordered by its stored column, `path =
  "record__root_id"`, `fieldAttr = some "root_id"`, `fieldIsRelation = true`,
  `relatedHasOrdering = true` — the spec demands `result = false` (no expansion:
  `lastSegment "record__root_id" = "root_id" = fieldAttr`). The prepatch impl
  compares `fieldAttr` against the WHOLE `path` (`"record__root_id" ≠ "root_id"`
  ⇒ guard true ⇒ `result = true`), disagreeing with the spec. Hence the carried
  gold proof's `hc`-case rewrite (which assumes the impl guard matches the spec's
  `lastSegment` condition) fails to elaborate against the prepatch impl
  (G-DIFF/G-PANEL).
- This is exactly what `test_order_by_self_referential_fk` exercises:
  `order_by('author__editor')` (relation, no trailing `_id`) keeps the related
  default ordering (`result = true`), while `order_by('author__editor_id')`
  (trailing segment = the FK's stored attribute) orders by the column directly
  (`result = false`) — pre-patch both wrongly expanded.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  guard decision, exhaustively over the modeled abstraction (is_relation ×
  has_ordering × attname ∈ {None, matching/non-matching segment} × multi-segment
  paths × the `pk` shortcut) plus ≥1e5 fuzzed points (0 disagreements).
