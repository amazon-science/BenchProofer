# refinement.md — django__django-13406

The operation-by-operation correspondence between `model.py`'s implementation
(the `attach_description` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The attachment site — `QuerySet.query` setter (`django/db/models/query.py:211-213`)

Gold hunk:
```
     @query.setter
     def query(self, value):
+        if value.values_select:
+            self._iterable_class = ValuesIterable
         self._query = value
```

Model impl (`attach_description`):
```python
if value.value_field_count > 0:
    rs.producer_tag = PRODUCES_VALUE_MAPPINGS
rs.description = value
```

| # | model.py impl op (`attach_description`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rs: ResultSet` | `self` (the `QuerySet`) | R | `QuerySet` ↔ `ResultSet`, minimal class with only the two touched fields `producer_tag`/`description` (mapping.md §1-2). |
| A2 | parameter `value: LookupDescription` | `value` (the `sql.Query`) | R | `sql.Query` ↔ `LookupDescription`, minimal class with only the touched read-only field `value_field_count` (mapping.md §1-2). |
| A3 | guard `value.value_field_count > 0` | guard `if value.values_select:` | R + A-reference | `value.values_select` is a tuple; `if <tuple>:` tests non-emptiness, i.e. `bool(values_select) == (len(values_select) > 0)`. The model carries the tuple by its count, so the guard refines to `value_field_count > 0` (mapping.md §2). That `bool(values_select) ⟺ count > 0` and that real `values()`/`values_list()` queries carry a non-empty `values_select` is the **A-reference** G-AX validates against the real Django objects (mapping.md §3); it is not a consumed axiom (no `@ContractOnly`). |
| A4 | `rs.producer_tag = PRODUCES_VALUE_MAPPINGS` (tag 1) | `self._iterable_class = ValuesIterable` | R | the row-producer class object ↔ integer tag; `ValuesIterable` ↔ 1 (`PRODUCES_VALUE_MAPPINGS`). Under the abstraction every value-bearing producer collapses to tag 1 — including `values_list()` flavours, which the patch deliberately reloads to `ValuesIterable` (the documented scope, F2P `test_annotation_values_list`; mapping.md §3). The observable the F2P tests check is "produces value mappings (dicts), not model instances", i.e. tag ≠ 0. |
| A5 | (implicit else) `producer_tag` left at its prior value | (no `else`: `_iterable_class` left at its `__init__` default `ModelIterable`) | I | identical control flow: no assignment on the empty-selection branch. The model's `Old(rs.producer_tag)` preservation ⟺ the real setter not touching `_iterable_class`. |
| A6 | `rs.description = value` | `self._query = value` | R + I | identical assignment of the passed reference; `_query` ↔ `description`, identity preserved (`rs.description is value` ⟺ `self._query is value`). |

## B. The discriminating clause (G-DIFF)

The behavioural content of the change is A3+A4: *a value-bearing query attached
to a freshly-created result set must switch the producer to the value-mapping
producer.* The spec pins this with

```python
Ensures(Implies(value.value_field_count > 0,
                rs.producer_tag == PRODUCES_VALUE_MAPPINGS))
```

`model_prepatch.py` reproduces the pre-patch setter (stores `description` only,
never touches `producer_tag`) and **fails** exactly this postcondition
(`Implies((value.value_field_count > 0), (rs.producer_tag ==
PRODUCES_VALUE_MAPPINGS))` might not hold) — because a freshly-created result
set defaults to the model-instance producer (tag 0). This is precisely the bug
the issue reports (value rows wrongly wrapped as model instances) and the
property the F2P `test_annotation_values` / `test_annotation_values_list` tests
observe (`reloaded.get()` returns a dict, not a model instance). The
empty-selection branch is pinned by the complementary clause
`Implies(value_field_count == 0, producer_tag == Old(producer_tag))`, which the
prepatch satisfies — so the failing clause isolates the exact fixed behaviour.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. There is **no consumed axiom**: the
changed operation — the conditional producer switch — is modeled **deeply**
(spelled out as the conditional attribute update over integer tags) and verified
directly, not hidden behind a `@ContractOnly` about the function under change.
The one opaque correspondence (real tuple-truthiness / real producer classes ↔
the integer tags) is an **A-reference** validated == the real Django setter by
`axiom_check.py` (G-AX, mapping.md §3), not consumed.

## D. verify(model) ⇒ resolved

`attach_description` verifies only if (A3+A4) a value-bearing description forces
the value-mapping producer tag and (A5) an empty-selection description preserves
the prior producer and (A6) the description is stored. By R (the type/tag
bijections of mapping.md §2) and the A-reference (G-AX: `bool(values_select) ⟺
count > 0`; the value-bearing producer is `ValuesIterable` ↔ tag 1; the real
setter preserves `_iterable_class` on the empty branch), the verified attachment
equals the gold setter on the tested inputs. The gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
— here the single A-reference, G-AX — and refinement fidelity (this document,
G-EQ).
