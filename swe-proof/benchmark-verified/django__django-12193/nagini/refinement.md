# refinement.md — django__django-12193

The operation-by-operation correspondence between `model.py`'s implementation
(the `prepare_attrs` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `CheckboxInput.get_context` (`django/forms/widgets.py:521`)

Gold hunk:
```
     def get_context(self, name, value, attrs):
         if self.check_test(value):
-            if attrs is None:
-                attrs = {}
-            attrs['checked'] = True
+            attrs = {**(attrs or {}), 'checked': True}
         return super().get_context(name, value, attrs)
```

| # | model.py impl op (`prepare_attrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `attrs: Dict[int, bool]` at `Acc(dict_pred(attrs), 1/2)` | the `attrs` argument of `get_context` | R | dict `{str: Any}` ↔ `Dict[int, bool]` (mapping.md §2). The HALF permission is the model's encoding of "read-only": the patched code no longer writes `attrs`, so the spec holds it read-only. |
| A2 | `if counts_as_selected(value):` | `if self.check_test(value):` | R | `check_test` default `boolean_check` ↔ `counts_as_selected` (`not (v is False or v is None or v == '')`), modeled deeply over an `int` value code (mapping.md §2). Same branch condition. |
| A3 | `return mapping_with(attrs, attr_selected(), True)` | `attrs = {**(attrs or {}), 'checked': True}` then handed to `super().get_context` | A-consumed | the new fresh-merge construction `{**(attrs or {}), 'checked': True}` is the unchanged language primitive `{**base, key: value}`, axiomatized as `mapping_with` (mapping.md §3.1). The proof CONSUMES its `Ensures`: `Result() is not attrs` (freshness — the fix), `attr_selected() in Result() and Result()[...] == True`, other keys carried through, no spurious keys. The `attrs or {}` coalescing is the `None → empty` case (mapping.md §2). |
| A4 | (false branch) `return mapping_copy(attrs)` | falls through to `return super().get_context(name, value, attrs)` with `attrs` unchanged | A-consumed + R | when not selected, the patched code passes `attrs` to `super()` unchanged. `super().get_context` reads only `attrs`'s CONTENTS (`build_attrs(self.attrs, attrs)`), never object identity (mapping.md §2), so the model's fresh contents-identical copy `mapping_copy(attrs)` is observationally equivalent and keeps a uniform full-permission return. |
| A5 | `attrs` returned at `Acc(dict_pred(attrs), 1/2)` UNCHANGED (never written) | the caller's `attrs` dict is never mutated in either branch | I | the postcondition `Acc(dict_pred(attrs), 1/2)` (Required AND Ensured) and the absence of any write to `attrs` in the impl ARE the no-mutation guarantee — the exact behaviour the F2P test `test_get_context_does_not_mutate_attrs` observes. |

The discriminating content of the change — the caller's `attrs` mapping is NOT
mutated in place — lives in two places that move together: the read-only HALF
permission `Acc(dict_pred(attrs), 1/2)` on the input, and the freshness clause
`Result() is not attrs` of `mapping_with` (A3). `model_prepatch.py` reproduces
the bug faithfully (`attrs[attr_selected()] = True; return attrs`) and **fails**
verification on the write `attrs[attr_selected()] = True` — "insufficient
permission" — because the read-only input is held at HALF permission. That is
exactly the spec sensing the change (G-DIFF). (Returning the same object would
additionally violate `Result() is not attrs`; the permission failure fires
first.)

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— from an in-place write of the caller's mapping to a fresh-mapping merge — is
captured by (1) the read-only HALF permission on `attrs` (a permission/type
refinement, R+I, that makes any in-place write unprovable) and (2) the freshness
+ contents `Ensures` of the `mapping_with` axiom over the unchanged `{**...}`
language primitive (A-consumed, mapping.md §3.1). There is no axiom about the
function under change; the only consumed axioms cover the unchanged dict-display
primitives the new code composes, and both are validated against the REAL Python
operations by G-AX (axiom_check.py).

## C. verify(model) ⇒ resolved

`prepare_attrs` verifies only if (i) it never writes the caller's mapping (the
read-only HALF permission, A1/A5) and (ii) the prepared mapping is a FRESH
object carrying `attr_selected() == True` exactly when the value counts as
selected, with all other caller attributes preserved (A3, the `mapping_with`
`Ensures`). By R (dict `{str:Any}` ↔ `Dict[int,bool]`; `check_test`/`boolean_check`
↔ `counts_as_selected`; the `super().get_context` contents-only read making the
pass-through copy faithful) the verified function equals the gold
`{**(attrs or {}), 'checked': True}` construction on the tested inputs; by G-AX
the `mapping_with`/`mapping_copy` axioms equal the real Python merge/copy
(A-consumed). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited primitives — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
