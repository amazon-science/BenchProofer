# refinement.md — django__django-14752

Maps every operation in `implementation_get` to its `patch.diff` counterpart in
`AutocompleteJsonView.get` (django/contrib/admin/views/autocomplete.py:12-33).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** op left as the real repo callee in G-CONF (not axiomatized),
**I** identical concrete op.

## Patch (post-patch `get`, results-assembly portion)
```python
context = self.get_context_data()
return JsonResponse({
    'results': [
        self.serialize_result(obj, to_field_name)
        for obj in context['object_list']
    ],
    'pagination': {'more': context['page_obj'].has_next()},
})

def serialize_result(self, obj, to_field_name):
    return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
```

The fix extracts the inline per-item entry expression — pre-patch the list
comprehension built `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`
directly — into a dedicated method `serialize_result(obj, to_field_name)` that
`get` now CALLS per object. Because the call is dispatched on `self`, a subclass
can override `serialize_result` and thereby change every entry. The default-class
method's body is the verbatim pre-patch inline expression, so default output is
byte-identical; the change is observable only through an override.

## Modeling decision
The observable behavior of `get` is the response payload
`{'results': [...], 'pagination': {'more': <bool>}}`. The `results` list is the
per-item rendering applied to each selected object, in order; `more` is the
page-has-next flag. The fix changes WHICH rendering produces each entry: the
dispatched, overridable `serialize_result` rather than a hardwired inline
expression. So the model:

- takes `objects : List Obj` (the selected `object_list`), `fieldKey : String`
  (`to_field_name`), and `hasMore : Bool` (`page_obj.has_next()`);
- applies an arbitrary `render : Obj → String → E` (the dispatched per-item
  rendering — the unchanged-bodied but now-overridable `serialize_result`) to
  each object, in order, to build `results`;
- copies `hasMore` into the response verbatim.

`Obj` and `E` are abstract carriers: `get` never inspects a selected object
except through the per-item rendering, and never inspects an entry at all.
Universally quantifying `render` makes the spec hold for EVERY rendering, so the
only thing it pins is that `results` is `render` applied per object in order and
`more` is the input flag — which is exactly the fixed behavior (the results list
is now produced BY the dispatched extension point).

The impl carries a second parameter `_defaultRender : Obj → String → E`
modeling the pre-patch hardwired inline expression. Post-patch routes the loop
through `render` (the dispatched method); the pre-patch bug (Solution_prepatch)
routes it through `_defaultRender`, ignoring the dispatched rendering — which is
exactly why a caller-chosen override had no effect pre-patch.

## Operation correspondence
| # | Lean op (`implementation_get`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut results := []` | start of the `'results'` list comprehension | I | empty accumulator. |
| 2 | `for o in objects do results := results ++ [render o fieldKey]` | `[ self.serialize_result(obj, to_field_name) for obj in context['object_list'] ]` | R / A-reference | the per-object loop is `R` (Python list comprehension ↔ Lean `for`/accumulate, order-preserving); `render o fieldKey` is the A-reference — the dispatched `self.serialize_result(obj, to_field_name)`, left as the REAL callee in G-CONF (NOT axiomatized). |
| 3 | `return { results := results, more := hasMore }` | `return JsonResponse({'results': [...], 'pagination': {'more': context['page_obj'].has_next()}})` | R / I | assemble the payload: `results` is op #2's accumulator (`I` framing), `more` is `page_obj.has_next()` copied verbatim (`R`: the JsonResponse dict ↔ `Resp` structure bijection per mapping.md). |

## R/I legs ⇒ G-CONF
The per-object loop (op #2, R: order-preserving accumulation) and the payload
framing (op #3) are the R/I content. The `render` piece of op #2 is an
A-reference: G-CONF leaves it as the REAL post-patch `serialize_result` (it does
NOT substitute an axiom model), which isolates and tests the R/I loop + framing
legs. `conf_skip = false`: the impl region has genuine R/I content (the
per-object loop and payload framing), so `conformance_check.py`
differential-tests the shadow (loop + framing, with the real `serialize_result`
as the per-item step) against the patched `get`'s results-assembly over ≥10^5
fuzzed inputs.

## No A-consumed row
The proof consumes no property of `render` / `_defaultRender` (both universally
quantified), so `meta.json axioms = []`. The per-item rendering is recorded as an
A-reference solely to document the G-CONF binding to the real `serialize_result`
callee; there is no `opaque`/`axiom` declaration in `Solution.lean` and
`axiom_check.py` is a skip stub.

## F2P alignment
`test_serialize_result` defines a subclass overriding `serialize_result` to add a
`'posted'` field, issues a request, and asserts the response `results` carry the
extra field for every object. Pre-patch, `get` hardwired the inline entry and
never dispatched through an overridable method, so a subclass override had no
effect — the response carried only `id`/`text`. The discriminating clause
`problem_spec_get` pins (`results = objects.map render`, i.e. each entry is
produced BY the dispatched rendering); the prepatch impl (builds `results` from
the fixed `_defaultRender`, ignoring `render`) cannot satisfy it for arbitrary
`render`. `patch.diff` (gold verbatim) makes the harness resolve.
