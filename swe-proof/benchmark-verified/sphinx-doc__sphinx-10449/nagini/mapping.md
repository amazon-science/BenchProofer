# mapping.md — sphinx-doc__sphinx-10449

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 36367765fe780f962bba861bf368a765380bbc68`, states the type
abstraction, and records callee provenance.

Repo file under change: `sphinx/ext/autodoc/typehints.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `append_return_type(fields, has_return, return_annotation, suppress_void_return)` | the trailing return-type emit block of `modify_field_list` — `sphinx/ext/autodoc/typehints.py:86` (body `if 'return' in annotations and 'return' not in arguments:` at line 126) | the modeled changed function: decides whether the synthetic return-type field is appended and renders its content (the gold's new `suppress_rtype` param ↔ model `suppress_void_return`) |
| `suppress_for_kind(object_kind)` | the dispatch in `merge_typehints` selecting the `"all"` target — `sphinx/ext/autodoc/typehints.py:61-62` (post-patch `if objtype == 'class': ... suppress_rtype=True`) | the modeled changed dispatch: computes the suppression flag from the documented object kind (the gold's `objtype` arg ↔ model `object_kind`) |
| `has_return_field_in(fields)` | the `arguments` build-up loop of `modify_field_list` — `typehints.py:89-108`, specifically the `elif parts[0] == 'rtype': arguments['return'] = {'type': True}` branch (line 107-108) | helper: whether the existing field list already declares a return type (`'return' in arguments`) |
| `has_return_field(fields)` *(pure spec)* | the predicate `'return' in arguments` over the field list | pure spec: a return-type field already present |
| `is_return_field(code)` *(pure spec)* | a single field whose `field_name` first token is `rtype` (`typehints.py:107`) | pure spec: one field declares a return type |
| `seq_class()` *(pure spec)* | the string literal `'class'` (`typehints.py:61` post-patch, `if objtype == 'class'`) | pure spec: the container object kind name |
| `seq_none()` *(pure spec)* | the string literal `'None'` (`typehints.py` post-patch, `if annotation == 'None'`) | pure spec: the "no value" return-annotation text |
| `opt_seq(x)` *(pure spec)* | n/a (Nagini framing helper for an `Optional` carrier) | pure spec: the code-point sequence of an optionally-produced field |

The pre-patch repo facts the change concerns (for the refinement audit, not
referenced from the consumer spec view): `modify_field_list` had no
`suppress_rtype` parameter (`typehints.py:86`); the emit block appended the
`rtype` field unconditionally (`typehints.py:126-130`); and `merge_typehints`
called `modify_field_list(field_list, annotations[fullname])` with no
kind-dependent dispatch (`typehints.py:62`). A latent transcription detail the
gold also corrects: the pre-patch emit used the loop variable `annotation`
(left over from the `for name, annotation in annotations.items()` loop,
`typehints.py:110`) as the rendered content (`typehints.py:129`); the gold binds
`annotation = annotations['return']` first, so the rendered content is the
object's OWN return annotation — captured by the model's content postcondition
`opt_seq(Result()) == ToSeq(return_annotation)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `objtype: str` (the documented object kind, e.g. `'class'`, `'function'`, `'method'`; model param `object_kind`) | `List[int]` of Unicode code points; compared via `ToSeq` to `seq_class()` | `s == 'class'` ⇔ `ToSeq(object_kind) == seq_class()`; `str` equality ↔ `PSeq` equality |
| `annotations['return']: str` (the return-annotation text, e.g. `'None'`, `'int'`) | `List[int]` of Unicode code points; the relevant predicate is equality to `seq_none()` | `annotation == 'None'` ⇔ `ToSeq(return_annotation) == seq_none()` |
| `'return' in annotations` | the bool parameter `has_return` | direct boolean abstraction of dict-key membership (the `annotations` dict's `return` key) |
| `node: nodes.field_list` (the existing docutils field list) and the derived `arguments: Dict` | `fields: List[int]` of per-field kind codes (1 = a field that already declares a return type, 0 = any other field) + the derived `has_return_field` | `'return' in arguments` ⇔ `has_return_field(ToSeq(fields))`; the only field property the emit decision reads is whether some field is an `rtype` field |
| the appended `nodes.field` carrying `field_name('','rtype')` + `field_body('', paragraph('', annotation))` | `Optional[List[int]]`: `None` = no field appended, a `List[int]` = the appended field's rendered content (its code points) | the only observable facts the F2P test reads are (a) WHETHER the rtype field is appended and (b) its rendered text; both are captured by `Result() is None` vs. the produced content list |

`str` indexing/iteration is banned in Nagini, so all string carriers are
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`. The
docutils `field_list` node is abstracted to the single property the changed code
inspects (`'return' in arguments`) and the single thing it produces (the rtype
field's presence + content).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

**None.** There is no opaque library/utility callee on the changed path. The
entire changed behaviour — the suppression flag computed from `objtype == 'class'`
(`suppress_for_kind`), the `arguments`/`'return'`-presence build-up
(`has_return_field_in`), the emit decision (`'return' in annotations and 'return'
not in arguments`, gated by `not (suppress_rtype and annotation == 'None')`), and
the rendered content (`annotations['return']`) — is ordinary boolean / sequence /
dict-membership logic, all directly expressible in Nagini and modelled deeply
here. The docutils `nodes.field`/`nodes.field_name`/`nodes.field_body`
constructors that physically build the node are unchanged by the patch and are
not part of the decision the F2P test observes; they are abstracted to "a field
with this rendered content was (not) appended" (§2), not axiomatized.

Therefore there are **no `@ContractOnly` axioms**, **no A-reference deep models**
of an external callee, and **no `axiom_check.py`**. G-AX is `n/a`: nothing to
execute against a real callee. The only soundness trust point is refinement
fidelity (refinement.md, G-EQ); correctness is confirmed end-to-end by G-RESOLVE
(the gold patch resolves).
