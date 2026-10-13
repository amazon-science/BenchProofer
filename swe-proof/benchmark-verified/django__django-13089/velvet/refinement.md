# refinement.md — django__django-13089

Correspondence between `Solution.lean`'s `cullStep` impl and `patch.diff` (the
gold patch guards the cull-boundary read with a None check). `patch.diff` is the
gold verbatim (applies at `base_commit = 27c0904…`, resolves — G-RESOLVE).

## A. The guarded cull-boundary step — `DatabaseCache._cull`

Gold hunk (post-patch):
```python
last_cache_key = cursor.fetchone()
if last_cache_key:
    cursor.execute(
        'DELETE FROM %s WHERE cache_key < %%s' % table,
        [last_cache_key[0]],
    )
```
Pre-patch (buggy):
```python
cursor.execute("DELETE FROM %s "
               "WHERE cache_key < %%s" % table,
               [cursor.fetchone()[0]])
```

| # | Solution.lean impl op (`cullStep`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fetched : Option (List Int)` | `last_cache_key = cursor.fetchone()` | R | DB row tuple ↔ `some [cols…]`; `None` ↔ `none` (mapping.md §2). The lookup result is taken as the modeled input. |
| A2 | `let lastKey := fetched` | binding `last_cache_key` | I | identical concrete bind of the lookup result. |
| A3 | `if lastKey.isSome then … else …` | `if last_cache_key:` | I | identical control-flow guard. Python truthiness of a present (non-empty, `require row ≠ []`) row ↔ `isSome`; `None`/absent ↔ falsy ↔ `¬ isSome` (mapping.md §2). |
| A4 | present branch: `return some ((lastKey.getD []).head!)` | `cursor.execute('DELETE … WHERE cache_key < %s', [last_cache_key[0]])` | R | the DELETE is observed through the boundary key it targets: `last_cache_key[0]` ↔ `row.head!`; "delete issued with key k" ↔ `out = some k` (mapping.md §2). |
| A5 | absent branch: `return none` | (no `cursor.execute` — the `if` body is skipped) | R | "no delete issued / no row read" ↔ `out = none`. Crucially the absent row is NEVER subscripted. |

Every step is R or I. No A (axiom) steps — there is no consumed axiom and no
A-reference deep model of an external callee; the modeled behavior is entirely
the None-guard control flow between two abstracted DB operations. No kind-3
(changed inexpressible) steps.

### A-tagging of the two DB operations
* `cursor.fetchone()` — its result is the modeled INPUT boundary (A1, R), not a
  consumed contract. Not axiomatized.
* `cursor.execute('DELETE …')` — observed only via the boundary key it would use
  (A4, R). Its row-level side effect on the backend is abstracted to that key;
  it is not deep-modeled as an A-reference because the only property the fix
  changes is *whether and with what key* it runs — captured exactly by `out`.

This is why there is no `axiom_check.py` (no axioms / A-references to validate)
and why G-CONF is skipped (no DB-free R/I shadow of live cursor ops — mapping.md
§4): the deeply-modeled content is control flow, and its two endpoints are not
executable without a live DB. Soundness rests on G-VERIFY + G-DIFF.

## B. verify(Solution) ⇒ resolved

`cullStep` verifies only if both `ensures` hold:
* `fetched = none → out = none` — on an absent lookup, NO boundary is produced
  and NO row is subscripted (A5). This is precisely the behavior the issue and
  the F2P test `test_cull_delete_when_store_empty` demand: with an empty store
  (`_max_entries = -1` forces a cull, the culling SELECT returns no row), `_cull`
  must not crash with `'NoneType' object is not subscriptable`.
* `∀ row, fetched = some row → out = some row.head!` — on a present row, the
  delete is parameterised by the first column (A4), preserving the pre-existing
  passing behavior (`test_cull`, `test_zero_cull`).

By the R bijection (mapping.md §2) the verified result corresponds to the patched
`_cull`: guard present ⇒ delete with `last_cache_key[0]`; guard absent ⇒ skip.
The prepatch impl (`return some ((fetched.getD []).head!)`) reads the first
column UNCONDITIONALLY — exactly the gold pre-patch `[cursor.fetchone()[0]]`. It
fails the `fetched = none → out = none` clause (G-DIFF), which is the observable
of the 'NoneType is not subscriptable' bug. No trust points beyond the type
bijection: there are no axioms.
