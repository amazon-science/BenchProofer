# refinement.md — sphinx-doc__sphinx-8459

The operation-by-operation correspondence between `model.py`'s implementation
(the `record_annotations` impl region and the deep `resolve` / `expand` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses a
`@ContractOnly` axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The recording site — `record_typehints` (`sphinx/ext/autodoc/typehints.py:23`)

Gold hunk (body line 30):
```
- sig = inspect.signature(obj)
+ sig = inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)
```
followed (unchanged) by the recording loop:
```
for param in sig.parameters.values():
    if param.annotation is not param.empty:
        annotation[param.name] = typing.stringify(param.annotation)
if sig.return_annotation is not sig.empty:
    annotation['return'] = typing.stringify(sig.return_annotation)
```

| # | model.py impl op (`record_annotations`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | the two parameter slots `(name0,raw0,has0)`, `(name1,raw1,has1)` and the return slot `(ret_raw,ret_has)` | iterating `sig.parameters.values()` and the return annotation | R | a `str` parameter name ↔ `int` name token; a `str` annotation source / its `stringify` rendering ↔ `int` annotation token; `param.annotation is not param.empty` ↔ the `has*` flag (mapping.md §2). The real loop records each parameter independently, so a fixed handful of named slots is the faithful skeleton of the per-parameter recording; the tested callable `sum(x, y) -> ...` has exactly two parameters and a return. |
| A2 | `aliases: Dict[int, int]` parameter | `app.config.autodoc_type_aliases` threaded into the signature call | R | the user-configured alias `Dict[str,str]` ↔ `Dict[int,int]` (source token → resolved token); membership/lookup is the only operation (mapping.md §2). This is the value the patch newly passes. |
| A3 | `annotation[name_i] = resolve(raw_i, aliases)` for each annotated slot; `annotation[KEY_RETURN()] = resolve(ret_raw, aliases)` for the return | `annotation[param.name] = typing.stringify(param.annotation)` where `param.annotation` came from `inspect.signature(obj, type_aliases=...)` → `get_type_hints(subject, None, type_aliases)` | A-reference | the changed behaviour — the annotation is resolved **through the configured alias map** — is modelled **deeply**: `resolve` (with `expand`) in the `pure` region IS that resolution (alias's target when the map governs the source, else the underlying expansion). There is no consumed `get_type_hints` axiom — the proof never depends on one. Instead the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real resolver `typing.get_type_hints(obj, None, type_aliases)` (the function sphinx delegates to) with and without the alias map and asserts the alias branch preserves the configured name while the no-alias branch expands to a *different* form (mapping.md §3.1). `stringify` is the identity on the carrier (a token already denotes the rendered string; mapping.md §3.2), so the recorded token equals `resolve(raw, aliases)`. |
| A4 | `if has_i: annotation[name_i] = ...` / `if not has_i: name_i absent` | `if param.annotation is not param.empty:` guard | I | the annotation-present guard is the identical concrete control flow: an annotated slot is recorded, an unannotated slot is skipped. |
| A5 | the reserved return slot `KEY_RETURN()` | the literal dict key `'return'` | R | a distinguished name token ↔ the reserved `'return'` key; pinned distinct from every parameter name by the precondition (mapping.md §1). |
| A6 | `annotation = {}` built and returned (a `Dict[int,int]`) | `annotations.setdefault(name, OrderedDict())` populated in place | R | the per-object recorded mapping ↔ `Dict[int,int]`; the F2P rendering observes *which resolved annotation is recorded under each name*, which `OrderedDict` vs `dict` does not change (insertion order is not observed by the asserted output) (mapping.md §2). |

The discriminating content of the change — the annotation is resolved
**through the configured alias map** rather than with no aliases — lives in
`resolve(raw_i, aliases)` (model, the alias branch when `raw_i in aliases`) ⇔
`inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)` (real).
The pre-patch `inspect.signature(obj)` defaults `type_aliases={}`, resolving
every source with no aliases (`expand`); `model_prepatch.py` reproduces that
(records `expand(raw_i)` regardless of the alias map) and **fails** the
postcondition clause (1) `Result()[name0] == resolve(raw0, aliases)`, which is
exactly the spec sensing the change (G-DIFF). In the F2P configuration
`aliases = {myint → myint}`: the gold records `myint` (`resolve(myint, aliases)
== myint`), the pre-patch records `int` (`expand(myint) == int ≠ myint`) — the
observed `Dict[str, Any]`/`int`-instead-of-the-alias bug.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the annotation resolution now consulting the configured alias map —
is modelled **deeply** (the spelled-out two-branch `resolve`/`expand` consumed
in `record_annotations`, step A3, an **A-reference**), not hidden behind an
axiom about the function under change. There is **no consumed axiom**: the only
callee the change relies on (`get_type_hints` via `inspect.signature`) is the
**A-reference** that G-AX validates the deep model against.

## C. verify(model) ⇒ resolved

`record_annotations` verifies only if each recorded annotation equals the
alias-resolved token `resolve(raw, aliases)` (A3) — i.e. the alias is preserved
when the configured map governs the source. By R (str ↔ int tokens, `stringify`
identity, the per-object mapping ↔ `Dict[int,int]`) the verified recorder equals
the gold `record_typehints` on the tested callable; by G-AX the deep model
`resolve`/`expand` equals the real `get_type_hints` resolver (A-reference) under
the alias map sphinx supplies. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited
A-reference callee — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: axiom/deep-model soundness (G-AX) and
refinement fidelity (this document, G-EQ).
