# mapping.md — django__django-14752

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b64db05b9cedd96905d637a2d824cbbf428e40e7`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/contrib/admin/views/autocomplete.py`
(`class AutocompleteJsonView(BaseListView)`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_results(view, recs, to_field_name)` | the results list-comprehension inside `AutocompleteJsonView.get` — `autocomplete.py:27-31` (the `'results': [ ... for obj in context['object_list']]` value) | modeled changed function (hunk 1): builds the results list, deferring each entry to the responder's conversion step |
| `default_record_entry(view, rec, to_field_name)` | `AutocompleteJsonView.serialize_result` — the NEW method added post-patch (`autocomplete.py`, body `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`) | modeled changed function (hunk 2): the default conversion step's body |
| `record_entry(view, rec, to_field_name)` *(axiom — A-consumed)* | `self.serialize_result(obj, to_field_name)` — the late-bound (dynamically-dispatched) method call introduced into `get` at `autocomplete.py:29` post-patch | the responder's OWN, replaceable conversion step (the extension point); opaque per-(responder, record) entry producer |
| `lookup_text(rec, to_field_name)` *(axiom — A-consumed)* | `str(getattr(obj, to_field_name))` — Python builtins `getattr` + `str` (`autocomplete.py:29` pre-patch, `serialize_result` body post-patch) | unchanged extraction of the textual form of the designated lookup attribute |
| `display(rec)` *(axiom — A-consumed)* | `str(obj)` — Python builtin `str` / the model's `__str__` (`autocomplete.py:29` pre-patch, `serialize_result` body post-patch) | unchanged extraction of the textual form of the record |
| `View` | the `AutocompleteJsonView` instance `self` (and its subclasses) | the responder; its dynamic type selects the late-bound conversion step |
| `Record` | a matched model object `obj` from `context['object_list']` | a matched record; carries the two textual values the default conversion reads |
| `Entry` | one result dict `{'id': ..., 'text': ...}` (extensible with further keys) | one entry of the results list |

The pre-patch shape the change refactors (for the refinement audit, not
referenced from the consumer spec view): `get` constructed each entry inline as
`{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`
(`autocomplete.py:29`), with NO `serialize_result` method on the class.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `AutocompleteJsonView` (sub)instance `self` | `View` (bare identity object) | the responder's identity/dynamic type ↔ the receiver argument `view`; which conversion step is late-bound is a function of `view` (the `serialize_result(view, …)` argument). |
| a matched model object `obj` | `Record` with fields `id_text`, `display_text` | `str(getattr(obj, to_field_name))` ↔ `rec.id_text`; `str(obj)` ↔ `rec.display_text`. The two unchanged str-coercions are surfaced as the axioms `lookup_text`/`display` returning these fields. |
| the result dict `{'id': s1, 'text': s2, …}` | `Entry` with fields `id_val`, `text_val` | `dict['id']` ↔ `Entry.id_val`; `dict['text']` ↔ `Entry.text_val`; extra keys an override may add are outside the two observed fields (carried opaquely by the `record_entry` axiom's result). |
| `str` value (`id`, `text`) | `PSeq[int]` of Unicode code points | `s[k]` ↔ `ord`; `len` ↔ `len`; concat ↔ `+`. (`str` indexing is banned in Nagini.) |
| `to_field_name` (a `str` attribute name) | `int` token | an opaque identifier of the designated lookup attribute; only its identity matters (it is passed through unchanged from `get` into the conversion step). |
| `context['object_list']` (a queryset, iterated in order) | `List[Record]` | iteration order ↔ list index order; `len` ↔ `len`. |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `record_entry` axiom ↔ the late-bound method (A-consumed)
**Callee:** `self.serialize_result(obj, to_field_name)` — the method introduced
into `get` post-patch (`autocomplete.py:29`). It is **dynamically dispatched**
on the responder `self`: the base `AutocompleteJsonView` provides the default
body, and a subclass may override it (the documented extension point — the
problem statement's `CustomAutocompleteJsonView.serialize_result`). The axiom
encodes only what the builder's proof needs: that the entry for record `recs[k]`
is *whatever this responder's conversion step produces* — an opaque
`Entry`-valued function of `(view, rec, to_field_name)`. It pins NO entry
contents (`Ensures(True)`); that opacity is exactly the extension point and is
what makes the builder's postcondition dischargeable ONLY by actually calling
the step (not by inlining a fixed entry). The fractional `Requires` on the
record's two text fields is the weakest permission the call needs (the step
reads, never mutates, the record).

**Soundness check (G-AX):** `axiom_check.py` executes the REAL post-patch method
bodies (quoted verbatim from `patch.diff`) and asserts the builder defers to the
late-bound step: an overriding responder's extra field appears in EVERY entry,
in order, and the base responder yields the default entries. (A-consumed: the
builder's postcondition `Result()[k] is record_entry(view, recs[k], tf)`
consumes this opacity/dispatch property.)

### 3.2 `default_record_entry` deep model ↔ the default method body (A-reference)
**Callee:** the new `AutocompleteJsonView.serialize_result` body
`return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`. The default
conversion step is modeled **deeply** as `default_record_entry` (the
`Entry(lookup_text(rec, tf), display(rec))` construction), NOT consumed as an
axiom. G-AX validates the deep model equals the real default entry: for the base
responder, the entry is exactly `{'id': str(getattr(obj, tf)), 'text': str(obj)}`
with exactly the `id`/`text` keys.

### 3.3 `lookup_text` / `display` axioms ↔ Python builtins (A-consumed)
**Callees:** `str(getattr(obj, to_field_name))` and `str(obj)` — pure, unchanged
Python builtins, identical pre- and post-patch (they appear verbatim both in the
pre-patch inline entry and in the post-patch `serialize_result` body). The axioms
encode only that each is a deterministic textual function of the record; for the
modelled `Record` they return the stored `id_text` / `display_text`. These are
the weakest contracts `default_record_entry` needs, and they are the
A-reference link for §3.2 (validated by `axiom_check.py`'s
`check_default_reference`, which runs the real `getattr`/`str` chain).
