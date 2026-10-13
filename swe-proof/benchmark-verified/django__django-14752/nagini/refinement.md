# refinement.md — django__django-14752

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_results` and `default_record_entry` impl regions, the
`record_entry` late-bound axiom, and the `lookup_text`/`display` axioms) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`/opacity, and **A-reference**, where a deep model is validated
== the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The results-builder site — `get()` (`autocomplete.py:27-33`)

Gold hunk:
```
         return JsonResponse({
             'results': [
-                {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
+                self.serialize_result(obj, to_field_name)
                 for obj in context['object_list']
             ],
             'pagination': {'more': context['page_obj'].has_next()},
         })
```

| # | model.py impl op (`build_results`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | `recs: List[Record]`, iterated by index `0..len-1` | `context['object_list']`, iterated in order by the comprehension | R | the queryset ↔ `List[Record]`; iteration order ↔ list index order (mapping.md §2). |
| A2 | `result.append(record_entry(view, recs[i], to_field_name))` per record | `self.serialize_result(obj, to_field_name)` per `obj` in the comprehension | **A-consumed** | the FIX. The builder defers each entry to the responder's OWN, late-bound conversion step. `record_entry(view, rec, tf)` is the opaque axiom standing for the dynamically-dispatched `self.serialize_result(obj, tf)` (mapping.md §3.1). The proof consumes its opacity: the postcondition `Result()[k] is record_entry(view, recs[k], tf)` is dischargeable ONLY by actually calling the step, never by inlining a fixed entry — which is exactly "the result is bound to the (overridable) conversion step, not to a fixed entry shape." G-AX confirms the real dispatch honours an override. |
| A3 | `result` returned (a `List[Entry]`), `len(result) == len(recs)`, aligned by index | the comprehension's list value placed under `'results'` in the `JsonResponse` dict | R | the result list ↔ the `'results'` list; `len`/order preserved. The surrounding `JsonResponse({...,'pagination':...})` wrapper and the `'pagination'` entry are unchanged by the patch and carry no behaviour the F2P test of this change observes (outside modelled scope; mapping.md §1). |

## B. The default conversion site — `serialize_result()` (new method)

Gold hunk (the added method):
```
+    def serialize_result(self, obj, to_field_name):
+        """..."""
+        return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
```

| # | model.py impl op (`default_record_entry`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| B1 | `Entry(lookup_text(rec, tf), display(rec))` | `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}` | **I** (under R on the carrier) + **A-consumed** | identical concrete construction: the entry's identifier field is `str(getattr(obj, tf))` (`lookup_text`, A-consumed) and its display field is `str(obj)` (`display`, A-consumed); the dict ↔ `Entry` carrier is R (mapping.md §2). `lookup_text`/`display` axiomatize the unchanged Python builtins `getattr`/`str` (mapping.md §3.3). This is the body extracted verbatim from the pre-patch inline entry. |

The **relationship** between the two sites — that for the BASE responder the
late-bound step (A2) equals the default body (B1) — is the **A-reference**:
`default_record_entry` is the deep model of the default `serialize_result`,
validated `== the real default entry` by axiom_check.py (G-AX, mapping.md §3.2),
NOT consumed by the proof. The builder (A2) never consumes the default's
contents; it consumes only the opacity/dispatch of the late-bound step. This is
what makes the refactoring's extension point real: a non-base responder's entries
need not equal the default.

## C. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it reverts step **A2** — instead
of deferring to the responder's late-bound conversion step, the builder INLINES
the default entry (`result.append(Entry(lookup_text(recs[i], tf), display(recs[i])))`),
exactly as the pre-patch `get` constructed `{'id': str(getattr(obj, tf)),
'text': str(obj)}` inline. With the byte-identical frozen spec it **fails**
verification on the loop invariant
`Result()[k] is record_entry(view, recs[k], to_field_name)`
(`model_prepatch.py:183`): a freshly-constructed default `Entry` is not the
opaque dispatched value, and cannot be proved equal to it (the late-bound step
is opaque). That is precisely the behaviour the F2P test observes:
`test_serialize_result` subclasses `AutocompleteJsonView`, overrides
`serialize_result` to add a `'posted'` key, and asserts every result entry
carries it. The pre-patch inline builder IGNORES the override (the bug); the
post-patch builder defers to it. The spec is therefore strong enough that no
implementation that fixes the entry contents itself — rather than deferring to
the responder's replaceable conversion step — can verify (the spec sees the bug).

Only ONE `model_prepatch.py` is needed: the only independently-observable fixed
behaviour is the deferral/dispatch (site A). Site B (the default body) is not an
independently-observable bug — pre-patch the method did not exist and its body
WAS the inline entry; the same `default_record_entry` therefore verifies in
both model.py and model_prepatch.py (its spec is byte-identical and its impl
unchanged). The default body's agreement with the live step is audited by G-AX
(A-reference, §B), not by a second failing skeleton.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
deferring per-record conversion to a late-bound, overridable step instead of
inlining a fixed entry — is the **A-consumed** step A2, an axiom about an
*unchanged-in-this-function* callee the new code now CALLS (the dynamically
dispatched `self.serialize_result`), not about the function under change itself.
The default body it factors out is modelled **deeply** (`default_record_entry`,
step B1) and validated against the real default by G-AX (the **A-reference**);
there is no axiom about the function under change. We never axiomatize the
function under spec.

## E. verify(model) ⇒ resolved

`build_results` verifies only if (A2) every entry is exactly the value the
responder's OWN late-bound conversion step produces for the corresponding
record, in order, and `default_record_entry` verifies only if (B1) the
default entry exposes `id == str(getattr(obj, tf))` and `text == str(obj)`. By R
(queryset ↔ `List[Record]`, result dict ↔ `Entry`, `str` ↔ `PSeq[int]`,
attribute name ↔ `int` token) and the I/A steps, the verified builder equals the
gold `get` comprehension `[self.serialize_result(obj, to_field_name) for obj in
context['object_list']]` and the verified default equals the gold
`serialize_result` body, on the tested inputs. By G-AX the real dispatch honours
an overriding responder (A-consumed, §3.1) and the real default entry equals the
deep model (A-reference, §3.2). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and audited callees —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
