# refinement.md — django__django-15629

The operation-by-operation correspondence between `model.py`'s implementations
(`reported_reference_parameters`, `references_need_rebuild`, and the deep `emits_collation_clause`
predicate) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

There is **no consumed axiom** in this bundle: both modeled behaviours are
spelled out deeply. The two deep models are **A-reference**s, validated against
the real (gold-patched) Django by `axiom_check.py` (G-AX).

## A. The root cause — `ForeignKey.db_parameters` (`related.py:1182`)

Gold hunk:
```
-        return {"type": self.db_type(connection), "check": self.db_check(connection)}
+        target_db_parameters = self.target_field.db_parameters(connection)
+        return {
+            "type": self.db_type(connection),
+            "check": self.db_check(connection),
+            "collation": target_db_parameters.get("collation"),
+        }
```

| # | model.py impl op (`reported_reference_parameters`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `target_params: Dict[int,int]` | `target_db_parameters = self.target_field.db_parameters(connection)` | R | the referenced column's params dict ↔ `Dict[int,int]` keyed by token constants (mapping.md §2); read-only, fractional permission. |
| A2 | `result[key_type()] = own_type` | `"type": self.db_type(connection)` | R + I | `own_type` ↔ `self.db_type(connection)` (the FK's own type, unchanged callee); dict-write is identical. |
| A3 | `result[key_check()] = own_check` | `"check": self.db_check(connection)` | R + I | `own_check` ↔ `self.db_check(connection)` (unchanged callee); identical write. |
| A4 | `result[key_collation()] = target_params[key_collation()]` | `"collation": target_db_parameters.get("collation")` | R | the new line: the FK reports the referenced column's collation. `target_params[key_collation()]` ↔ `target_db_parameters.get("collation")` under the dict refinement (`get` on a present key ↔ index; `None` ↔ `none_value()`); the `Requires(key_collation() in target_params)` matches that a `CharField`/`TextField` target's params always carry the `"collation"` key (mapping.md §1). |
| A5 | `return result` (a 3-entry dict) | `return {…}` | I | same returned mapping shape. |

The discriminating content — the FK reporting a `"collation"` entry at all —
lives in the postcondition `key_collation() in Result()` plus
`Result()[key_collation()] == target_params[key_collation()]`. `model_prepatch.py`
reproduces the pre-patch impl (omits the collation write) and **fails** on
`key_collation() in Result()` (G-DIFF) — exactly the spec sensing the change.
The whole-dict A-reference (real `ForeignKey.db_parameters` carries the target's
collation) is validated by G-AX over boundary + fuzz collation identities.

## B. The create-time consequence — `_iter_column_sql` COLLATE branch

`base/schema.py:282-283` (unchanged code, newly fed the FK collation):
```python
if collation := field_db_params.get("collation"):
    yield self._collate_sql(collation)
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `emits_collation_clause(params)` = `key_collation() in params and params[key_collation()] != none_value()` | the truthiness test `if field_db_params.get("collation")` | A-reference | the deep predicate mirrors the unchanged emission branch: a COLLATE clause is emitted iff the params declare a non-empty collation. Validated by G-AX reading the real `column_sql` COLLATE token. |
| B2 | `Ensures(emits_collation_clause(Result()) == (key_collation() in target_params and target_params[key_collation()] != none_value()))` in `reported_reference_parameters` | the composition: FK column now emits COLLATE iff target declares one | A-reference + I | ties A4 to B1 — once the FK reports the target's collation (A4), its column emits a COLLATE clause exactly when the target column does. This is what `test_create_fk_models_to_pk_field_db_collation` observes. |

## C. The alter-time consumer — the re-derive trigger

Gold hunks in `base/schema.py` (`drop_foreign_keys`, lines 826-833) and the
mirrored `sqlite3/schema.py:458` guard:
```
-            and old_type != new_type
+            and ((old_type != new_type) or (old_collation != new_collation))
```
(plus the lift of `old_collation`/`new_collation` earlier in the function, and
the `sqlite3` guard `new_field.unique and (old_type != new_type or
old_collation != new_collation)`).

| # | model.py impl op (`references_need_rebuild`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `old_type != new_type` | `old_type != new_type` | R + I | type identities ↔ `int`; `!=` identical. |
| C2 | `or (old_collation != new_collation)` | `or (old_collation != new_collation)` | R + I | the newly added disjunct; collation identities ↔ `int` (`None` ↔ `none_value()`); `!=` identical. |
| C3 | the connection-features / primary-key / unique guards | the surrounding `drop_foreign_keys` conjuncts | (out of scope) | unchanged by the patch; `references_need_rebuild` models ONLY the changed sub-expression (the `(old_type != new_type) or (old_collation != new_collation)` disjunction), not the unchanged guards. |

`model_prepatch_2.py` reverts C2 (`return old_type != new_type`) and **fails**
on the postcondition `Result() == (old_type != new_type or old_collation !=
new_collation)` on the pure-collation-change witness (G-DIFF). This is the
behaviour `test_alter_field_pk_fk_db_collation` exercises: altering a PK's
collation (type unchanged) must re-derive the referencing FK columns. Validated
by G-AX: the gold-patched base-schema source contains the exact disjunction, and
the boolean truth table holds over the full identity grid.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — the FK reporting the target's collation, and the re-derive trigger
gaining the collation disjunct — are modeled **deeply** (spelled out in the impl
regions of `reported_reference_parameters` and `references_need_rebuild`), not hidden behind
an axiom about the function under change. There is no consumed `@ContractOnly`
axiom. The unchanged callees the FK invokes (`db_type`, `db_check`,
`target_field.db_parameters`) appear only as R-refined inputs (`own_type`,
`own_check`, `target_params`), not as consumed axioms; the create-emission
branch `_iter_column_sql` is the unchanged consumer captured structurally as the
A-reference `emits_collation_clause`.

## E. verify(model) ⇒ resolved

`reported_reference_parameters` verifies only if its result reports a `collation` entry equal
to the referenced column's collation (A4, the discriminating clause) and emits a
COLLATE clause exactly when the target does (B2). `references_need_rebuild`
verifies only if it re-derives references on a pure collation change (C2). By R
(dict/collation/type ↔ `Dict[int,int]`/`int`; `get` ↔ index; `None` ↔
`none_value()`) the verified functions equal the gold patch's
`ForeignKey.db_parameters` and `_alter_field` re-derive trigger on the tested
inputs; by G-AX the deep models equal the real (gold-patched) callees over
boundary + fuzz + the full truth table. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
deep models — and the gold patch resolves (G-RESOLVE). The trust point reduces
to refinement fidelity (this document, G-EQ) and deep-model fidelity (G-AX);
there is no axiom-soundness trust point because no axiom is consumed.
