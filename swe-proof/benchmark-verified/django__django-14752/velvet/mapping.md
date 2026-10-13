# mapping.md — django__django-14752

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b64db05b9cedd96905d637a2d824cbbf428e40e7`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/contrib/admin/views/autocomplete.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildResults (items : List Item) (serialize : Item → Serialized)` | the results-list construction inside `AutocompleteJsonView.get` — `django/contrib/admin/views/autocomplete.py:27-32` (the `'results': [ … for obj in context['object_list'] ]` comprehension) | the modeled changed construction: build the results list by applying a single per-item serialization to each item of the object list, in order |
| `serializeResult (it : Item)` | the new method `AutocompleteJsonView.serialize_result(self, obj, to_field_name)` — `autocomplete.py` post-patch (returns `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`) | the modeled NEW default per-item serialization (the extracted extension point) |
| `items : List Item` | `context['object_list']` — the page of source objects iterated by the comprehension | the ordered objects to serialize |
| `serialize : Item → Serialized` (free total function) | the per-item serialization actually invoked by `get`: `self.serialize_result(obj, to_field_name)` — late-bound, i.e. the method as resolved on the instance (the default, or a subclass override) | the injected, caller-overridable per-item serialization; abstracted as a free total function (see §3) |
| `it.idText : String` | `str(getattr(obj, to_field_name))` — the chosen identifier rendered as text | observable of one item |
| `it.displayText : String` | `str(obj)` — the object's display text | observable of one item |
| `Serialized` (`List (String × String)`) | the per-item result `dict` (`{'id': …, 'text': …}`, and any extra keys an override adds) | the serialized object |
| `defaultSerialized` *(deep model)* | the default object `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}` (`autocomplete.py` post-patch `serialize_result` body) | pure spec: the default serialization; modeled deeply, NOT an axiom |

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): `get` inlined the result object
`{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}` directly in the
comprehension (`autocomplete.py:29` pre-patch), with NO extraction — so a
subclass could not change the per-item serialization without overriding the
entire `get()` method. The patch moves that object construction into the new
`serialize_result` method and has `get` call `self.serialize_result(obj,
to_field_name)` per item, making the per-item serialization an overridable
extension point.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `context['object_list']`, the ordered page of source objects | `List Item` | a page is modeled by the ordered list of the per-item observables the serialization reads; `len(object_list)` ↔ `items.length`; order is preserved. |
| one source object `obj`, as seen by the default serialization | `Item` (`idText`, `displayText`) | the only renderings the default serialization consults are `str(getattr(obj, to_field_name))` ↔ `idText` and `str(obj)` ↔ `displayText`. The change does not alter how either is computed. |
| the per-item result `dict` | `Serialized = List (String × String)` | an object of string field names to string values, modeled as an ORDERED key/value list so extra fields (an override's customization, e.g. `'posted'`) are representable beyond the two defaults; `dict` key set/values ↔ pairs; insertion order ↔ list order. |
| `self.serialize_result(obj, to_field_name)` invoked per item | `serialize : Item → Serialized` (free total function) | abstracts the per-item serialization actually called. It is LATE-BOUND: `self.serialize_result` resolves to the default or to a subclass override. Modeling it as an arbitrary total function makes the spec quantify over ALL serializers — the very point of the extension. The default serializer corresponds to instantiating `serialize := serializeResult`'s deep model `defaultSerialized`. |
| the default `serialize_result` body | `defaultSerialized` | `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}` ↔ `[("id", it.idText), ("text", it.displayText)]`; the two keys, in order. |

The `'pagination'` part of the response, `process_request`, `has_perm`,
`get_queryset`, and the `JsonResponse` envelope are UNCHANGED by the patch and
OUTSIDE the modeled construction; they are not part of the spec (the change
touches only how the per-item results are built and the new default serializer).

## 3. Callee provenance

No consumed axioms; no deep-model reference to a concrete external callee.

- **`serialize` (the injected per-item serialization).** The change builds the
  results by calling `self.serialize_result(obj, to_field_name)` per item — a
  late-bound method that a subclass may override (that overridability is the
  feature). We do NOT axiomatize it: it is modeled as an arbitrary total
  function `serialize : Item → Serialized`, and the postcondition
  (`out = items.map serialize`) holds for EVERY `serialize`. This is strictly
  weaker than any concrete serializer, so there is no over-claim to check
  (directive 7). It is precisely this universal quantification that pins the
  fixed behavior: the construction must apply WHATEVER serialization is in
  effect to every item, so an override takes effect — which the pre-patch
  inlined-default construction cannot do.

- **`defaultSerialized` (the new default serializer).** This is the new default
  per-item serialization; it is modeled DEEPLY (`defaultSerialized` + the
  `serializeResult` method body), NOT behind an axiom about the function under
  change (directive 7). Its fidelity to the gold patch is audited mechanically
  by G-CONF (`conformance_check.py`).

There is therefore no `axiom_check.py` for this bundle (`meta.json gates.G-AX =
skip`, like django__django-13590 / django__django-11149).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14752`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `buildResults`/`serializeResult` (the deep map model and the
default serializer) to Python and runs them against the gold-patched
`AutocompleteJsonView` construction behaviour: results are built by mapping
`self.serialize_result(obj, to_field_name)` over `object_list`, with the
per-item serialization carried by an in-process serializer (the default, and
several overrides that add extra fields). The whole impl region is R/I (no
A-tagged callee in the computed `out`), so `conf_skip = false`.
