# refinement.md — django__django-14580

The operation-by-operation correspondence between `model.py`'s implementation
(the `serialize_type` impl region: the table construction, the first-match scan,
and the per-element materialisation of the matched row's text and directive set)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

## A. The distinguished-type serializer — `TypeSerializer.serialize()` (`django/db/migrations/serializer.py:273-287`)

Gold hunk (the one changed line, at `serializer.py:276`):
```
         special_cases = [
-            (models.Model, "models.Model", []),
+            (models.Model, "models.Model", ['from django.db import models']),
             (type(None), 'type(None)', []),
         ]
         for case, string, imports in special_cases:
             if case is self.value:
                 return string, set(imports)
```

The serializer keeps a built-in table of distinguished types, each row pairing a
type with its rendered text and the list of import directives that text needs.
It scans the table and, on the first row whose type is the value being
serialized, returns that row's text together with `set(imports)`. The bug: the
`models.Model` row carried an **empty** directive list, so the surfaced import
set omitted `from django.db import models`; a generated migration referencing
the rendered `models.Model` (e.g. in `bases=(..., models.Model)`) then raised
`NameError: name 'models' is not defined`. The fix puts the namespace-import
directive in that row.

| # | model.py impl op (`serialize_type`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | `value_tag: int`; the `tags[i] == value_tag` test | `self.value` (a `type`); the `case is self.value` reference-identity test (`serializer.py:280`) | R | each distinguished type is an opaque identity; reference-identity on type objects ↔ integer-equality on identity tags (mapping.md §2). Only which distinguished row matches is observable. |
| A2 | `tags`/`texts`/`directives` = three index-aligned columns built inside the function | the `special_cases` list literal of `(case, string, imports)` triples (`serializer.py:275-278`) | R | the list-of-triples ↔ three index-aligned columns (mapping.md §2). Built INSIDE `serialize_type`, exactly as the source builds the literal, so the fixed datum (the row's directive content) lives in the impl where the gold patch edits it. |
| A3 | row 0 carries `directives[0] == base_ref_directive()` (the code points of `from django.db import models`); row 1 carries the empty directive | row 0 `imports == ['from django.db import models']`; row 1 `imports == []` (`serializer.py:276-277`, post-patch) | **I** (under R on the carrier) | the FIX. The base-class-reference row's directive list is the one-element list holding the namespace-import statement (`str` ↔ `List[int]` code points, R); the no-import row's directive list is empty — identical concrete data to the gold table. |
| A4 | `while i < len(tags): if tags[i] == value_tag:` first-match scan | `for case, string, imports in special_cases: if case is self.value:` (`serializer.py:279-280`) | **I** (under R) | identical control flow: a first-match linear scan over the table returning on the first matching row. The `for ... in` over triples ↔ the indexed `while` over the aligned columns. |
| A5 | the matched row's `texts[i]`/`directives[i]` copied element-by-element into `result.text`/`result.imports`; `return result` | `return string, set(imports)` (`serializer.py:281`) | **I** (under R) + **A-reference** | the matched row's text is returned as-is (`str` ↔ `List[int]`, R); the matched row's directive list is materialised into the import **set** — `set(imports)` ↔ the per-element copy of the directive's code points into `result.imports`. `set(imports)`'s "materialise the row's directive list into a directive set" semantics is the **A-reference** validated by axiom_check.py / G-AX (mapping.md §3.1); the proof consumes no axiom for it. |

The unmodelled fall-through (`serializer.py:282-287`: the module-based path for
non-distinguished types) is unchanged by the patch and concerns values that are
NOT in the table; the modeled function's precondition restricts to the
distinguished path (`value_tag` is one of the two table tags), which is exactly
the F2P scenario (serializing `models.Model`). That path carries no behaviour
the F2P/P2P tests of *this* change observe.

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it builds the table with row 0's
directive **empty** (`directives = [other_ref_directive_empty(),
other_ref_directive_empty()]`), exactly as the pre-patch `special_cases` carried
`(models.Model, "models.Model", [])`. With the byte-identical frozen spec it
**fails** verification on the postcondition

```
Ensures(Implies(value_tag == base_ref_tag(),
                ToSeq(Result().text) == base_ref_text()
                and ToSeq(Result().imports) == base_ref_directive()))
```

(`model_prepatch.py:132`, reported as "Postcondition of serialize_type might not
hold … `ToSeq(Result().imports) == base_ref_directive()`"): a result whose
imports come from the empty row-0 directive cannot equal the non-empty
namespace-import directive the spec demands. The companion no-import clause
(row 1 → empty directive set, satisfied both pre- and post-patch) keeps the
model faithful and prevents a wrong impl from "fixing" the wrong row.

That is precisely the behaviour the F2P test observes:
`test_serialize_type_model` asserts
`MigrationWriter.serialize(models.Model) == ("models.Model", {'from django.db import models'})`
(plus a serialize-round-trip equality). The spec is therefore strong enough that
no implementation that surfaces an empty import set for the base-class reference
can verify (the spec sees the bug).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, **I**, or **A-reference**. The operation that genuinely
*changed* — the directive content of the base-class-reference row (step A3) — is
an **I** step (identical concrete table data, only the `str` carrier refined to
`List[int]` code points by R). There is **no consumed axiom**: the table scan
and the directive-set materialisation are pure structural logic, modelled
deeply. The only callee behaviour relied on — that `set(imports)` materialises a
row's directive list into a directive set holding exactly those directives — is
an **A-reference** the deep model is validated against by axiom_check.py (G-AX,
§A5), never an `@ContractOnly` the proof consumes. We never axiomatize the
function under change.

## D. verify(model) ⇒ resolved

`serialize_type` verifies only if serializing the base-class reference yields
its text AND the namespace-import directive (step A3/A5, the postcondition's
discriminating clause) and serializing the no-import reference yields its text
and the empty directive set. By R (type-object identity ↔ integer tags; `str` ↔
`List[int]`; the `special_cases` list-of-triples ↔ the aligned columns; the
`for ... in` first-match scan ↔ the indexed `while`) and the single **I** fix
step, the verified function equals the gold `TypeSerializer.serialize` —
`return string, set(imports)` over the post-patch table — on the tested inputs.
By G-AX the real `TypeSerializer.serialize` returns exactly
`("models.Model", {'from django.db import models'})` for `models.Model` and
`("type(None)", set())` for `type(None)`, and `set(imports)` has the modeled
materialisation semantics (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited primitive — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: axiom soundness (here, the A-reference G-AX
check) and refinement fidelity (this document, G-EQ).
