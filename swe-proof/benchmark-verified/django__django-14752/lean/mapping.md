# mapping.md — django__django-14752

## Symbol binding (file:line @ base_commit b64db05b9c)
- Modeled function: `AutocompleteJsonView.get`
  — `django/contrib/admin/views/autocomplete.py:12-33` @ base_commit.
  The observable output is the `JsonResponse` content dict
  `{'results': [...], 'pagination': {'more': <bool>}}` (lines 27-33).
- New callee introduced by the patch: `AutocompleteJsonView.serialize_result`
  — `django/contrib/admin/views/autocomplete.py` (added after `get`, lines 35-40
  post-patch). Its body is the inline per-item dict expression that the pre-patch
  `get` computed at line 29:
  `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`.
- Callees used but UNCHANGED (not modeled, not axiomatized — they are subsumed
  into the abstract per-item rendering function / the pagination flag):
  `process_request`, `has_perm`, `get_queryset`, `get_context_data`,
  `context['page_obj'].has_next()`, `JsonResponse`.

## What the fix changes
Pre-patch `get` hardcodes the per-object result entry inline inside the
`'results'` list comprehension (line 29). Post-patch `get` instead calls
`self.serialize_result(obj, to_field_name)` per object (a dispatched, hence
subclass-overridable, method), whose default implementation is the SAME inline
dict. Default-class output is therefore byte-identical; the change is observable
only when a subclass provides a different per-item rendering — which is exactly
what FAIL_TO_PASS `test_serialize_result` exercises (it overrides
`serialize_result` to add a `posted` field and asserts the response carries it).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)
| Python | Lean |
|---|---|
| `context['object_list']` (queryset, iterated) | `objects : List Obj` (`Obj` abstract — only ever consumed by the per-item rendering) |
| `to_field_name : str` | `fieldKey : String` |
| `context['page_obj'].has_next() : bool` | `hasMore : Bool` |
| the dispatched `self.serialize_result(obj, to_field_name)` (per-item entry) | `render : Obj → String → E` (`E` abstract — the entry dict type) |
| the pre-patch hardwired inline entry `{'id': str(getattr(obj,tf)),'text':str(obj)}` | `defaultRender : Obj → String → E` |
| `{'results': [...], 'pagination': {'more': b}}` | `Resp E := { results : List E, more : Bool }` |
| `[ render(obj, tf) for obj in object_list ]` | `objects.map (fun o => render o fieldKey)` |

`render` and `defaultRender` are both UNIVERSALLY QUANTIFIED (like
`jsonBody`/`escapeId` in django-15103): the spec then holds for every rendering
function and pins only that `results` is the per-item rendering applied to each
object in order, and `more` equals the supplied has-next flag. Post-patch routes
the loop through `render` (the dispatched method); pre-patch routes it through
`defaultRender` (the hardwired inline entry), ignoring `render`.

## Callee provenance / flag deps
- `serialize_result` (A-reference): its post-patch body is the verbatim
  pre-patch inline expression — behavior-preserving for the base class. No flag
  dependence. G-CONF binds `render` to the REAL post-patch `serialize_result`
  and `defaultRender` to the REAL pre-patch inline expression and asserts they
  agree on the default class (the refactor preserves default output).
- No consumed callee axiom: the proof needs no property of `render` /
  `defaultRender` (both universally quantified) ⇒ `axioms = []`, `axiom_check.py`
  is a skip stub.

## G-CONF fuzz seed
Pinned seed: `14752`. (`conformance_check.py` uses `random.seed(14752)`.)
