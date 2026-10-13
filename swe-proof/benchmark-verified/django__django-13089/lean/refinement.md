# refinement.md — django__django-13089

Maps every operation in `implementation_cull` to its `patch.diff` counterpart in
`BaseDatabaseCache._cull` (`django/core/cache/backends/db.py`, the `else` arm).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch `_cull` else arm)
```python
def _cull(self, db, cursor, now):
    if self._cull_frequency == 0:
        self.clear()
    else:
        connection = connections[db]
        table = connection.ops.quote_name(self._table)
        cursor.execute("DELETE FROM %s WHERE expires < %%s" % table,
                       [connection.ops.adapt_datetimefield_value(now)])
        cursor.execute("SELECT COUNT(*) FROM %s" % table)
        num = cursor.fetchone()[0]
        if num > self._max_entries:
            cull_num = num // self._cull_frequency
            cursor.execute(
                connection.ops.cache_key_culling_sql() % table,
                [cull_num])
            last_cache_key = cursor.fetchone()          # <-- gold fix
            if last_cache_key:                          # <-- gold fix
                cursor.execute(
                    'DELETE FROM %s WHERE cache_key < %%s' % table,
                    [last_cache_key[0]],
                )
```
The modeled value is the SET OF ROWS REMAINING in the cache table after the
pass.

## Operation correspondence
| # | Lean op (`implementation_cull`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if frequency = 0 then return some []` | `if self._cull_frequency == 0: self.clear()` | R | `self.clear()` empties the table ↔ the surviving set is `[]`; `self._cull_frequency : int (≥0)` ↔ `frequency : Nat`. |
| 2 | `let remaining := keepUnexpired now entries` | `cursor.execute("DELETE FROM %s WHERE expires < %%s", [now])` | R | dropping rows with `expires < now` ↔ keeping rows with `now ≤ expires`. `datetime` compared by `<` only ↔ `Int` order-surrogate (mapping.md). |
| 3 | `if (remaining.length : Int) > capacity then` | `cursor.execute("SELECT COUNT(*)"); num = cursor.fetchone()[0]; if num > self._max_entries:` | R | `num` (count of survivors) ↔ `remaining.length`; `self._max_entries : int` (may be negative) ↔ `capacity : Int`; `num > _max_entries` ↔ `remaining.length > capacity`. |
| 4 | `let cullNum := remaining.length / frequency` | `cull_num = num // self._cull_frequency` | I | `Nat` floor division ↔ Python `//` on non-negative ints. |
| 5 | `cullBoundary remaining cullNum` | `cursor.execute(cache_key_culling_sql() % table, [cull_num]); cursor.fetchone()` | R/I | `cache_key_culling_sql() = "... ORDER BY cache_key LIMIT 1 OFFSET %s"` returns the offset-th ascending `cache_key`, or NO ROW when `cull_num >= count` ↔ `((remaining.map key).mergeSort (·≤·))[cullNum]?`. The ordering SELECT is modeled deeply (sort + indexed access), not axiomatized. `some k` ↔ a fetched row; `none` ↔ empty fetch. |
| 6a | `\| some k => return some (keepAboveKey k remaining)` | `if last_cache_key: cursor.execute('DELETE FROM %s WHERE cache_key < %%s', [last_cache_key[0]])` | R | boundary fetched ⇒ delete rows with `cache_key < k` ↔ keep rows with `¬ key < k`. THE GOLD FIX'S `if last_cache_key:` guard is exactly this `some` branch. |
| 6b | `\| none => return some remaining` | (the implicit else of `if last_cache_key:`: NO delete performed) | R | empty boundary fetch ⇒ the patch performs no delete ⇒ the survivor set is unchanged. THIS is the behavior the fix introduces (pre-patch this path crashed). |
| 7 | `return some remaining` | the table contents after the pass (the within-capacity path) | I | within capacity ⇒ only the expiry delete happened ⇒ return survivors. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — `cache_key_culling_sql` / `COUNT(*)` enter as deeply
modeled ops or as `remaining.length`). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the final delete was unconditional:
```python
cursor.execute("DELETE FROM %s WHERE cache_key < %%s" % table,
               [cursor.fetchone()[0]])
```
When the boundary fetch returns no row (`cull_num >= count` — e.g. an empty or
near-empty store whose `_max_entries` has been forced below the survivor count),
`cursor.fetchone()` is `None` and `None[0]` raises *"'NoneType' object is not
subscriptable"*. The prepatch impl models exactly this: in op 6b it returns
`none` (the abort) instead of `some remaining`. It therefore cannot satisfy
`problem_spec_cull` on the discriminating clause
(`remaining.length > capacity → result = some (match cullBoundary … with | none
=> remaining …)`) whenever the boundary offset addresses no key — precisely the
case the FAIL_TO_PASS test `test_cull_delete_when_store_empty` exercises (a store
with `_max_entries = -1` so the very first `set()` forces `_cull` to delete on an
empty/one-row store, and the key must survive without a crash). The carried gold
proof fails to typecheck against the buggy `none` branch (G-DIFF).

`patch.diff == gold` verbatim.
