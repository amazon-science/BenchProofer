# refinement.md — sphinx-doc__sphinx-10449

The operation-by-operation correspondence between `model.py`'s implementation
(the `append_return_type` + `suppress_for_kind` + `has_return_field_in` impl
regions, and the `has_return_field` pure reference) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed** / **A-reference**), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The return-type emit decision — `modify_field_list` (`typehints.py:86`, body 126-130)

Gold hunks (the second + third hunk):
```
-def modify_field_list(node: nodes.field_list, annotations: Dict[str, str]) -> None:
+def modify_field_list(node: nodes.field_list, annotations: Dict[str, str],
+                      suppress_rtype: bool = False) -> None:
 ...
     if 'return' in annotations and 'return' not in arguments:
+        annotation = annotations['return']
+        if annotation == 'None' and suppress_rtype:
+            return
+
         field = nodes.field()
         field += nodes.field_name('', 'rtype')
         field += nodes.field_body('', nodes.paragraph('', annotation))
         node += field
```

| # | model.py impl op (`append_return_type` / `has_return_field_in`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `has_return: bool` | `'return' in annotations` (`typehints.py:126`) | R | boolean abstraction of the `annotations` dict-key membership (mapping.md §2). |
| A2 | `no_return_field = not has_return_field_in(fields)`, with `has_return_field_in(fields) == has_return_field(ToSeq(fields))` (the backward scan for an `rtype`-kind field) | `'return' not in arguments`, where `arguments['return']` is set iff a field's name is `rtype` (the `elif parts[0] == 'rtype'` branch, `typehints.py:107-108`) | R + I | the `arguments` build-up loop is unchanged by the patch; its only relevant output is `'return' in arguments`, modeled deeply as `has_return_field` over the field-kind list (mapping.md §2). Identical control/data flow over the refined carrier. |
| A3 | `if has_return and no_return_field:` … else `return None` | `if 'return' in annotations and 'return' not in arguments:` … (else: no field) | I (under R on A1/A2) | identical concrete guard for entering the emit block. |
| A4 | `suppressed_none = (ToSeq(return_annotation) == seq_none()) and suppress_void_return; if suppressed_none: return None` | `annotation = annotations['return']; if annotation == 'None' and suppress_rtype: return` | I (under R) | **the FIX.** Identical control/data flow: bind the return annotation, and on the conjunction `annotation == 'None' and suppress_rtype` return without appending. `annotation == 'None'` ⇔ `ToSeq(return_annotation) == seq_none()`; the gold's `suppress_rtype` param ↔ model `suppress_void_return` (mapping.md §2). |
| A5 | build `field` = the code points of `return_annotation` (copy loop) and `return field` | `field = nodes.field(); field += field_name('','rtype'); field += field_body('', paragraph('', annotation)); node += field` | R | the appended node is abstracted to its rendered content = the return annotation's code points; the `nodes.*` constructors are unchanged and abstracted (mapping.md §2). The model pins the content to `ToSeq(return_annotation)` (the object's OWN return annotation), matching the gold's `annotation = annotations['return']` binding — NOT the leftover loop variable the pre-patch used. |

The discriminating content of the change — for a container object kind, a
`None` return annotation must NOT yield an `rtype` field — lives in step **A4**
(`suppressed_none` guard). `model_prepatch.py` drops exactly that guard
(appends unconditionally, the pre-patch body) and **fails** the postcondition
```
(Result() is not None) ==
   (has_return and not has_return_field(ToSeq(fields))
    and not (suppress_void_return and ToSeq(return_annotation) == seq_none()))
```
on the class+`None` case — exactly the spec sensing the change (G-DIFF).

## B. The kind dispatch — `merge_typehints` (`typehints.py:61-62`)

Gold hunk (the first hunk):
```
             if app.config.autodoc_typehints_description_target == "all":
-                modify_field_list(field_list, annotations[fullname])
+                if objtype == 'class':
+                    modify_field_list(field_list, annotations[fullname], suppress_rtype=True)
+                else:
+                    modify_field_list(field_list, annotations[fullname])
```

| # | model.py impl op (`suppress_for_kind`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `object_kind: List[int]` | `objtype: str` argument of `merge_typehints` | R | `str` ↔ `List[int]` code points; the gold's `objtype` ↔ model `object_kind` (mapping.md §2). |
| B2 | `return ToSeq(object_kind) == seq_class()` | `objtype == 'class'` selecting `suppress_rtype=True` (else the default `False`) | I (under R) | identical concrete equality test; its boolean result is exactly the `suppress_rtype` value passed to `modify_field_list`. `'class'` ⇔ `seq_class()` (mapping.md §2). |

`suppress_for_kind(object_kind)` computes the very flag `append_return_type`
consumes as `suppress_void_return` (the gold's `suppress_rtype`); together A4+B2
are the whole behavioural change: the container kind ⇒ suppress a `None` return
type. (No separate failing `model_prepatch` is needed for site B in isolation —
the pre-patch passed the default `suppress_rtype=False` for every kind, which is
observationally the same as "no suppression," exactly what site-A's prepatch
already exhibits; the F2P test exercises the `objtype == 'class'` path, where B2
must yield `True` and A4 must then suppress.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — gating the
`rtype` append on `not (suppress_rtype and annotation == 'None')` and threading
the kind-derived `suppress_rtype` flag — is modeled **directly** as ordinary
boolean / sequence logic (steps A4, B2), not hidden behind an axiom. There is
**no opaque callee** on the changed path (mapping.md §3): the `arguments`
build-up and the rendered-content rendering are unchanged repo code abstracted
by R, and the `nodes.*` constructors are not part of the observed decision.
Therefore there is **no A-consumed / A-reference row** and **no `axiom_check.py`**
(G-AX is `n/a`). We never axiomatize the operation under change; it is spelled
out.

## D. verify(model) ⇒ resolved

`append_return_type` verifies only if (A3) it enters the emit block exactly when
there is a return annotation and no existing return-type field, (A4) it
suppresses the field exactly when the kind requests suppression and the
annotation is `None`, and (A5) any appended field's content is the object's own
return annotation; `suppress_for_kind` verifies only if (B2) it requests
suppression exactly for the `'class'` kind. By R (`str` ↔ `List[int]`; the
`field_list`/`arguments` abstraction; the appended node abstracted to its
rendered content) and the I steps, the verified pair equals the gold
`merge_typehints`+`modify_field_list` on the tested inputs: a documented class
whose `__init__` returns `None` no longer emits a class-level `Return type:
None` field, while methods and non-`None` return types still do. There are no
callees to audit (no axioms), so the only trust point is refinement fidelity
(this document, G-EQ); the gold patch resolves (G-RESOLVE). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to the type
refinements of strings to `List[int]` and the field-list node to its observed
properties.
