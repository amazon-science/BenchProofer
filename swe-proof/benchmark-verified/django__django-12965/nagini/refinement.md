# refinement.md — django__django-12965

The operation-by-operation correspondence between `model.py`'s implementation
(the `references_single_table` impl region, its caller `delete_uses_subquery`,
and the pure `active_tables` helper) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed predicate — `SQLDeleteCompiler.single_alias` (`compiler.py:1408-1410`)

Gold hunk:
```
     @cached_property
     def single_alias(self):
+        # Ensure base table is in aliases.
+        self.query.get_initial_alias()
         return sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1
```

| # | model.py impl op (`references_single_table`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `query: TableRefs` with fields `primary_present`, `extra_active` | `self.query` (a `sql.Query`) with `alias_map` + `alias_refcount` dicts | R | the rich `Query` object reduced to the two aggregate quantities the predicate actually reads (mapping.md §1, §2): whether the base table is accounted for, and how many other tables are active. |
| A2 | `query.primary_present = True` | `self.query.get_initial_alias()` (the added line) | R | the FIX. `get_initial_alias` (`query.py:916-926`) registers/refs the base table so its reference count becomes positive. Its *net effect on the quantity the predicate reads* is exactly "the base table is now accounted for", i.e. `primary_present := True`, while the count of *other* active tables is unchanged. The returned alias string and the precise refcount magnitude are not observed by the predicate, so the assignment is the faithful refinement of the method's relevant effect (mapping.md §2). |
| A3 | `active_tables(query.primary_present, query.extra_active) == 1` | `sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1` | R + I | the boolean-coerced sum over the alias dict ↔ `active_tables = (1 if primary_present else 0) + extra_active` (mapping.md §2); after A2, `primary_present` is `True`, so the value is `1 + extra_active`. The `== 1` comparison is the identical concrete operation (**I**). |
| A4 | `return ... == 1` (a `bool`) | the `cached_property` value | R | identical boolean predicate; `cached_property` is memoization with no effect on the value (mapping.md §2). |

## B. The caller — `SQLDeleteCompiler.as_sql` (`compiler.py:1421-1438`)

`as_sql` is **unchanged** by the gold patch; it is modelled (`delete_uses_subquery`)
as the caller whose observable the F2P test reads, using the predicate
`references_single_table`'s spec (not an axiom — it is under spec, per
SPEC_GUIDE §3 multi-site).

```
def as_sql(self):
    if self.single_alias:
        return self._as_sql(self.query)        # direct single-table DELETE
    innerq = ...; outerq.add_q(Q(pk__in=innerq))
    return self._as_sql(outerq)                # DELETE ... WHERE pk IN (SELECT ...)
```

| # | model.py construct (`delete_uses_subquery`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | `if references_single_table(query): return False` | `if self.single_alias: return self._as_sql(self.query)` | R + I | the direct single-table branch ⇔ "no subquery used" (`Result() is False`); the guard is the same predicate (A). `_as_sql(self.query)` emits `DELETE FROM <table> [WHERE ...]` with no nested SELECT (`compiler.py:1412-1419`). |
| B2 | `return True` | `... outerq.add_q(Q(pk__in=innerq)); return self._as_sql(outerq)` | R + I | the else branch builds the `pk IN (SELECT ...)` subquery ⇔ "a subquery is used" (`Result() is True`). |

The F2P test `test_fast_delete_all` runs `User.objects.all().delete()` and
asserts the captured SQL contains no `SELECT` (and exactly one query). A
whole-table delete has no additional joined tables (`extra_active == 0`), so
post-fix `single_alias` is `True` and `delete_uses_subquery` is `False` — the
direct form, no nested SELECT. The spec clause
`Ensures(Implies(Old(query.extra_active) == 0, Result() is False))` pins exactly
this.

## C. No axioms; no kind-3 (unexpressible-changed-op) steps

Every step above is **R** or **I**. There is **no A row** — the bundle consumes
no `@ContractOnly` axiom and ships none (the `axioms` region is empty). The one
operation that genuinely *changed* — ensuring the base table is accounted for
before the active-table count is read — is modelled **directly** as the impl op
`query.primary_present = True` (A2), an **R**-refinement of `get_initial_alias`'s
net effect on the read quantity, not hidden behind an axiom about the function
under change.

`get_initial_alias` is itself Django code, not an opaque library callee, and its
predicate-relevant effect is fully spelled out by the model; `axiom_check.py`
(G-AX) therefore validates this **refinement claim** — that the real
`get_initial_alias` makes the base table accounted for and leaves the count of
other active tables unchanged, so that for a whole-table delete the real
`single_alias` returns `True` and the real `as_sql` emits no subquery — by
executing the real Django code, rather than checking any axiom `Ensures`.

## D. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it **drops step A2**
(`query.primary_present = True`) exactly as the pre-patch `single_alias` lacked
the `self.query.get_initial_alias()` line. With the byte-identical frozen spec
it **fails** verification on the predicate's postcondition: Nagini reports
`references_single_table:70: Postcondition ... (query.primary_present is True)
might not hold` — and equivalently the predicate clause `Result() == (query.extra_active
== 0)` no longer holds, because for the whole-table case (`primary_present`
entering `False`, `extra_active == 0`) the pre-patch returns
`active_tables(False, 0) == 1` → `0 == 1` → `False`, whereas the spec requires
`True`. That `False` is precisely the wrong subquery decision the issue reports
(`DELETE ... WHERE id IN (SELECT ...)`), so the spec is strong enough that no
implementation omitting the base-table registration can verify (spec sees the
bug). No second `model_prepatch_<k>` is needed: the patch fixes a single
behaviour at a single site.

## E. verify(model) ⇒ resolved

`references_single_table` verifies only if (A2) it ensures the primary table is
accounted for before reading the count and (A3/A4) it returns `active_tables == 1`,
equivalently `extra_active == 0` after A2. `delete_uses_subquery` then verifies
only if it emits the direct form (no subquery, `Result() is False`) exactly when
`extra_active == 0`. By R (the `Query` aliasing dicts ↔ the two aggregate
quantities; `get_initial_alias`'s net effect ↔ `primary_present := True`; the
dict-sum ↔ `active_tables`; the direct/subquery branches ↔ the boolean
discriminator) the verified predicate equals the gold
`self.query.get_initial_alias(); sum(...) == 1` and the unchanged `as_sql`
chooses the direct single-table form for a whole-table delete. G-AX confirms the
refinement claim against the real Django code. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The single trust point here is refinement
fidelity (this document, G-EQ); there is no axiom-soundness trust point because
the bundle consumes no axiom.
