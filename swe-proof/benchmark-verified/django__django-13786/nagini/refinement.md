# refinement.md — django__django-13786

The operation-by-operation correspondence between `model.py`'s implementation
(the `reduced_create_options` impl region, composing the `merge_options` and
`without_key` axioms with the deep clearing logic) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses the axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed site — the `AlterModelOptions` branch of `CreateModel.reduce`

Gold hunk (`django/db/migrations/operations/models.py`, the
`isinstance(operation, AlterModelOptions)` branch):
```
+            options = {**self.options, **operation.options}
+            for key in operation.ALTER_OPTION_KEYS:
+                if key not in operation.options:
+                    options.pop(key, None)
             return [
                 CreateModel(
                     self.name,
                     fields=self.fields,
-                    options={**self.options, **operation.options},
+                    options=options,
                     ...
```

| # | model.py impl op (`reduced_create_options`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | params `self_options`, `operation_options` : `Dict[int, int]` | `self.options`, `operation.options` : `dict` (str→value) | R | option-name `str` ↔ `int` token, option value ↔ `int` token; only membership + per-key value are observed (mapping.md §2). |
| 2 | `options = merge_options(self_options, operation_options)` | `options = {**self.options, **operation.options}` | A-consumed | `merge_options` is the weakest contract on the dict-display merge the proof needs (fresh dict, `b` wins on overlap, union of keys). Validated against the real `{**a, **b}` by G-AX (mapping.md §3.1). The proof consumes its `Ensures` to establish clause (1) and the no-foreign-key clause. |
| 3 | `if key_managed_a() not in operation_options: options = without_key(options, key_managed_a())` and the same for `key_managed_b()` | `for key in operation.ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key, None)` | I (control logic) + A-consumed (the pop) | the NEW control logic — clear each managed name the alter step does not provide — is modelled DEEPLY (spelled out as guarded clearing branches over the representative managed names). The membership guard `key not in operation.options` ↔ `key_managed_X() not in operation_options` is the identical concrete test (I). The per-key removal primitive `options.pop(key, None)` is the A-consumed `without_key` axiom (mapping.md §3.2). The model iterates the modeled managed family `{key_managed_a, key_managed_b}` = `is_managed_option`; the gold iterates `ALTER_OPTION_KEYS` — the same managed family under R (mapping.md §2). |
| 4 | `return options` (the fresh result mapping) | `options=options` field of the new `CreateModel(...)` | R | the computed options mapping becomes the collapsed `CreateModel`'s `options`; the surrounding `CreateModel(self.name, fields=self.fields, …, bases=self.bases, managers=self.managers)` construction is UNCHANGED by the patch (the only edited field is `options`), so it is outside the modeled behaviour. The optimizer test (`assertOptimizesTo`) compares the resulting operations, whose `options` compare by `==` on the mapping content the model pins. |

The discriminating content of the change lives in step 3 — the clearing of a
managed name the alter step omits. The pre-patch code (`model_prepatch.py`)
keeps only step 2 (the bare merge) and **fails** the postcondition
`Implies(key_managed_a() not in operation_options, key_managed_a() not in Result())`
(clause (2)), which is exactly the spec sensing the change (G-DIFF). This is the
behaviour the F2P test observes: `CreateModel(options={'verbose_name': …})` +
`AlterModelOptions(options={})` must optimize to `CreateModel()` with NO options
(verbose_name cleared), not `CreateModel(options={'verbose_name': …})`.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — the loop that clears managed options the alter step does not provide
— is modelled **deeply** (the guarded clearing branches in the impl, step 3),
NOT hidden behind an axiom about the function under change. The two consumed
axioms (`merge_options`, `without_key`) cover **unchanged** language primitives
the new code composes (the dict merge and `dict.pop`), each the weakest contract
the proof needs and each G-AX-checked against the real primitive. There is no
A-reference (no deep model is checked == a real callee; the deep part is the
control logic, validated by the composition check in axiom_check.py and by
G-RESOLVE on the gold).

## verify(model) ⇒ resolved

`reduced_create_options` verifies only if (1) every name the alter step provides
wins with the alter step's value, (2) every managed name the alter step omits is
absent from the result (the bug → fix delta), (3) a non-managed name the alter
step omits keeps the creation step's value, and no foreign name appears. By R
(str-keyed dict ↔ `Dict[int,int]`, the unchanged `CreateModel` construction) the
verified options mapping equals the gold patch's `options` on the tested inputs;
by G-AX the consumed axioms equal the real `{**a, **b}` / `dict.pop`, and their
composition equals the gold reduce-options computation. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
