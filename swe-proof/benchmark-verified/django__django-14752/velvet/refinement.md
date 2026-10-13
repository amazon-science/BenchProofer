# refinement.md — django__django-14752

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildResults` and `serializeResult` `do` blocks plus the deep
`defaultSerialized` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no axioms** (A) in this
bundle. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The results-construction site — `AutocompleteJsonView.get`

Gold hunk (`django/contrib/admin/views/autocomplete.py:27-32`):
```
 return JsonResponse({
     'results': [
-        {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
+        self.serialize_result(obj, to_field_name)
         for obj in context['object_list']
     ],
     'pagination': {'more': context['page_obj'].has_next()},
 })
```

| # | Solution.lean impl op (`buildResults`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `items : List Item` | `context['object_list']` (the page of objects) | R | the ordered page ↔ its ordered per-item observables (mapping.md §2). G-CONF bridges via `observe`. |
| A2 | parameter `serialize : Item → Serialized` (free total function) | `self.serialize_result(obj, to_field_name)` — the late-bound per-item serialization | R | the per-item serialization the comprehension invokes. Late-bound (default or subclass override); modeled as an arbitrary total serializer so the spec quantifies over ALL of them — strictly weaker than any concrete serializer, no contract owed (directive 7, mapping.md §3). G-CONF instantiates `serialize` with the default and several overrides. |
| A3 | `let results := items.map serialize; return results` | `[ self.serialize_result(obj, to_field_name) for obj in context['object_list'] ]` | I | order-preserving element-wise application of the in-effect serialization; the list comprehension's map ↔ `List.map` (count and order identical, G-CONF-checked). |

Discriminating content of the change — the construction must apply WHICHEVER
per-item serialization is in effect (so a subclass override takes effect for
every item), rather than an inlined fixed object — lives in `out = items.map
serialize` for the FREE `serialize` (model) ⇔ the replacement of the inlined
`{'id': …, 'text': …}` by `self.serialize_result(obj, to_field_name)` (real).
The pre-patch inlined the fixed default object unconditionally;
`Solution_prepatch.lean` reproduces that (`items.map defaultSerialized`,
ignoring `serialize`) and **fails** the postcondition `out = items.map
serialize`, leaving the goal `List.map defaultSerialized items = List.map
serialize items` (G-DIFF) — exactly the override the F2P `test_serialize_result`
exercises (a subclass `serialize_result` adding a `'posted'` field must appear
in every result).

## B. The default-serializer site — `AutocompleteJsonView.serialize_result`

Gold hunk (`autocomplete.py`, new method post-patch):
```
+    def serialize_result(self, obj, to_field_name):
+        return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
```

| # | Solution.lean impl op (`serializeResult`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `it : Item` (`idText`, `displayText`) | `(obj, to_field_name)` | R | one object ↔ its two read renderings: `str(getattr(obj, to_field_name))` ↔ `idText`, `str(obj)` ↔ `displayText` (mapping.md §2). |
| B2 | `return [("id", it.idText), ("text", it.displayText)]`; `ensures out = defaultSerialized it` | `return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}` | I | the default object, modeled deeply: exactly the `id` and `text` fields, in that order. The ordered key/value list ↔ the `dict` (mapping.md §2). G-CONF refutes any divergence. |

The default serializer's content is what the PASS_TO_PASS tests observe (the
unchanged `{'id': …, 'text': …}` default response shape); B2 pins it exactly so
no weaker default verifies. `serializeResult` is the value `buildResults`'s
`serialize` defaults to — connecting site A's universal quantification to the
concrete default (mapping.md §3).

There is no separate failing prepatch for site B: the default object is
byte-identical pre- and post-patch (the patch only MOVES it into a method). A
prepatch must keep the spec byte-identical (G-DIFF); the observable fix is the
construction's dispatch through the overridable serializer, which site A's
prepatch already exercises.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed construction is expressed concretely (A3, a
`List.map` over a free serializer); the new default serializer is expressed
concretely (B2). The overridability — the actual feature — is captured by the
universal quantification over `serialize` (the spec holds for EVERY serializer,
so the construction cannot hardcode one). Nothing inexpressible is hidden.

## D. verify(Solution) ⇒ resolved

`buildResults` verifies only if its output equals `items.map serialize` for the
FREE `serialize` — i.e. it must apply whatever per-item serialization is in
effect to every item, in order (A3), so an override takes effect.
`serializeResult` verifies only if it equals `defaultSerialized` — the exact
`{id, text}` default (B2). By R (`object_list ↔ List Item`,
`self.serialize_result ↔ serialize`, the `dict ↔ Serialized` bijection,
mapping.md §2) the verified construction equals the gold patch's
`[self.serialize_result(obj, to_field_name) for obj in context['object_list']]`
with the default `serialize_result` returning `{id, text}`; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs across the
default serializer and several field-adding overrides. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom trust point.
