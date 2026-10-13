# mapping.md — django__django-12965

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 437196da9a386bd4cc62b0ce3f2de4aba468613d`, states the type
abstraction, and records the (absence of) axiom provenance.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `references_single_table(query)` | `SQLDeleteCompiler.single_alias` — `django/db/models/sql/compiler.py:1408-1410` (the `@cached_property`) | the modeled changed function: the "exactly one active table" predicate (spec-view name avoids echoing the repo symbol) |
| `delete_uses_subquery(query)` | `SQLDeleteCompiler.as_sql` — `django/db/models/sql/compiler.py:1421-1438` (the caller, deciding direct vs. subquery form) | the unchanged caller whose observable (subquery used / not) the F2P test reads; under spec, uses `single_alias` |
| `TableRefs.primary_present` | "the base table alias is present in `self.query.alias_map` with `self.query.alias_refcount[base] > 0`" (`query.py:146-152,755,916-926`) | whether the primary table is currently accounted for |
| `TableRefs.extra_active` | "the number of *additional* (non-base) aliases `t` in `self.query.alias_map` with `self.query.alias_refcount[t] > 0`" | count of additional joined tables currently active |
| `active_tables(primary_present, extra_active)` | `sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map)` — `compiler.py:1410` | pure spec: total number of active tables |
| `query.primary_present = True` (in `references_single_table` impl) | `self.query.get_initial_alias()` — `compiler.py:1409` (added line) ↔ `Query.get_initial_alias` `query.py:916-926` | the FIX: ensure the base table alias is registered with a positive reference count before the count is read |

The pre-patch repo state the change repairs (for the refinement audit, not
referenced from the consumer spec view): `single_alias` read
`sum(... for t in self.query.alias_map) == 1` **without** first calling
`get_initial_alias()`. For a whole-table removal (`Model.objects.all().delete()`)
the delete query's `alias_map`/`alias_refcount` carry no base-table entry at the
moment `single_alias` is read, so the sum is `0`, the predicate is `False`, and
`as_sql` wrongly takes the subquery branch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.query` (a `sql.Query`) with `alias_map: dict` + `alias_refcount: dict` | a minimal `TableRefs` object carrying only the two touched aggregate quantities | the only quantities `single_alias`/`as_sql` read out of the dicts are (a) whether the base table is active and (b) how many other tables are active |
| `self.query.alias_refcount[base] > 0` (base table accounted for) | `query.primary_present: bool` | `True` ⇔ base alias present with positive refcount |
| `len([t for t in alias_map if alias_refcount[t] > 0 and t != base])` | `query.extra_active: int (>= 0)` | the count of *additional* active tables (joins); `0` for a whole-table delete |
| `sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map)` | `active_tables(primary_present, extra_active) = (1 if primary_present else 0) + extra_active` | the boolean-coerced sum over the dict ↔ (base contributes 1 when active) + (extra active count) |
| `Query.get_initial_alias()` (refs/joins the base table) | `query.primary_present = True` | the method's *net effect on the read quantity* is to make the base table accounted for (refcount becomes positive); the alias string it returns and the refcount magnitude are not observed by `single_alias` |
| `self.single_alias` (`cached_property` bool) | `references_single_table(query) -> bool` | identical boolean predicate |
| `SQLDeleteCompiler.as_sql` returning `_as_sql(self.query)` (direct) vs. `_as_sql(outerq)` with `Q(pk__in=innerq)` (subquery) | `delete_uses_subquery(query) -> bool` | `False` ⇔ the direct single-table form (`_as_sql(self.query)`); `True` ⇔ the subquery form. The F2P test reads exactly this discriminator: "the produced SQL contains no nested SELECT". |

`Query.get_initial_alias` (`query.py:916-926`): when `alias_map` already has
entries it `ref_alias(base)` (increments base refcount, still > 0); when
`alias_map` is empty it `join(BaseTable(...))` which registers the base alias
with refcount 1 (`query.py:755,981`). In both cases its net effect on the
predicate-relevant quantity is: the base table ends accounted for
(`primary_present = True`), and the count of *other* active tables is
unchanged. That is exactly what the impl op `query.primary_present = True`
captures, leaving `query.extra_active` fixed.

## 3. Callee provenance (kind-A)

**None.** This bundle consumes no `@ContractOnly` axioms. The changed operation
— "ensure the base table is accounted for, then count the active tables" — is
pure table-reference bookkeeping over the query's alias state, modelled
*directly* (`active_tables` spelled out; the registration modelled as
`primary_present = True`). There is no unchanged opaque library callee whose
behaviour the proof depends on, so there is nothing for G-AX to execute against;
`axiom_check.py` documents this and validates the *refinement* claim (the net
effect of `get_initial_alias` on the predicate-relevant quantities) against the
real Django code instead. See `axiom_check.py` and refinement.md §C.
