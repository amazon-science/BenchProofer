# refinement.md — django__django-15104

The operation-by-operation correspondence between `model.py`'s implementation
(the `reduce_to_relation_agnostic` impl region and the two deep-model removal
primitives) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed**, the proof uses the
axiom's `Ensures`; **A-reference**, a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim: any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The relation-agnostic reduction — `only_relation_agnostic_fields`

Gold hunk (`django/db/migrations/autodetector.py:99`):
```
         for name, field in sorted(fields.items()):
             deconstruction = self.deep_deconstruct(field)
             if field.remote_field and field.remote_field.model:
-                del deconstruction[2]['to']
+                deconstruction[2].pop('to', None)
             fields_def.append(deconstruction)
         return fields_def
```

| # | model.py impl op (`reduce_to_relation_agnostic`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | the surrounding per-field loop is not modeled; a single field's body is the contracted function | `for name, field in sorted(fields.items()): … fields_def.append(deconstruction)` | I | the loop is unchanged by the patch — identical iteration; the entire fix lives in the per-field body. The body is independent per field, so modeling one invocation is faithful (mapping.md §2). |
| A2 | param `kwargs: Dict[int, int]` (read-only, fractional permission) | `deconstruction[2]` (the kwargs `dict` of `self.deep_deconstruct(field)`) | R | string-keyed kwargs `dict` ↔ `Dict[int, int]`; only key membership + per-key value identity are observed (mapping.md §2). `'to'` ↔ `TO()`. The detector edits in place; the model returns the *equal* mapping — observationally identical for the value comparison (mapping.md §2). |
| A3 | param `is_relation: bool` | the guard `field.remote_field and field.remote_field.model` | R | the relation guard's truth value (mapping.md §2). |
| A4 | `if is_relation:` | `if field.remote_field and field.remote_field.model:` | I | identical control flow: the removal happens iff the relation guard holds. |
| A5 | `return pop_default(kwargs, TO())` | `deconstruction[2].pop('to', None)` | A-reference | the **changed** removal is modeled **deeply** by `pop_default` — keyword removal applicable to any mapping: no precondition on `k`, result has `TO()`/`'to'` absent and every other entry preserved/none introduced. There is no opaque consumed axiom about the function under change. The deep model is validated **== the real `dict.pop(k, None)`** out-of-band by G-AX (axiom_check.py runs the real primitive on boundary+fuzz mappings incl. the absent-key case). The real `pop(..., None)` IS that removal (mapping.md §3.1). |
| A6 | `return kwargs` (non-relation: input returned unchanged) | `fields_def.append(deconstruction)` with no removal | I | when the guard is false neither model nor patch alters the mapping; the postcondition pins this (`not is_relation` ⇒ every key, incl. `'to'`, survives with its value). |
| A7 | `Requires(MustTerminate(2))` on the contracted function; `Requires(MustTerminate(1))` on both removal primitives | the per-field body is straight-line code that always completes and appends its deconstruction | R | total-correctness obligation: the real body always ANSWERS. Nagini verifies partial correctness by default, so without the obligation a diverging or self-recursive impl would satisfy every `Ensures` vacuously (a G-PANEL-1 counterexample). The primitives' strictly smaller measure (1 < 2) admits the bounded `dict` primitive steps while forbidding a self-call of the contracted routine. |

## B. What discriminates the fix (G-DIFF) — the pre-patch `del`

`model_prepatch.py` is byte-identical in every spec region (docstring, axioms,
pure, pre/post-conditions, invariants) and differs only in the impl op A5:
```
- return pop_default(kwargs, TO())     # model.py (post-patch: applicable to any mapping)
+ return del_present(kwargs, TO())     # model_prepatch.py (pre-patch: applicable only when 'to' present)
```
`del_present` is the **deep model of the pre-patch `del deconstruction[2]['to']`**
(A-reference, mapping.md §3.2): it carries `Requires(k in d)` because real
`del d[k]` is *undefined* (raises `KeyError`) on an absent key. The contracted
function permits, and its postcondition must hold for, an input where
`is_relation` is true but `'to'` (`TO()`) is absent — exactly the reported bug
input (a relation field whose deconstruction omits `'to'`). The prepatch cannot
discharge `del_present`'s `TO() in kwargs` precondition for that input and
**fails verification** (`model_prepatch.py:126: precondition … (k in d) might
not hold`). The post-patch `pop_default`, applicable to any mapping, discharges
the same postcondition. This is the spec sensing the change: a removal undefined
on an absent key (crashes) → one applicable everywhere (a no-op when absent).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the keyword removal — is modeled **deeply**: `pop_default`
(post-patch) and `del_present` (pre-patch) are spelled-out contracts for the two
real `dict` primitives, each validated == its real primitive by G-AX
(A-reference), not hidden behind a single opaque axiom about the function under
change. There is **no A-consumed axiom** in this bundle (no unchanged opaque
library callee is invoked): both removal primitives are A-reference deep models
of the changed line's two forms.

## D. verify(model) ⇒ resolved

`reduce_to_relation_agnostic` verifies only if, for **every** input mapping
(including a relation field whose kwargs omit `TO()`/`'to'`), the result drops
`TO()` while preserving every other entry, AND a non-relation field's mapping is
returned unchanged — and the relation case requires the broadly-applicable
removal `pop_default` (A5); the narrowly-applicable `del_present` (the bug) does
not verify (§B). By R (string-keyed dict ↔ `Dict[int,int]`; relation guard ↔ `is_relation`;
single-field body ↔ loop body, I) the verified operation equals the gold patch's
`deconstruction[2].pop('to', None)` under the relation guard on the tested
inputs; by G-AX the deep model `pop_default` equals the real `dict.pop(k, None)`
(A-reference) and `del_present` equals the real `del d[k]` (A-reference, raising
on the absent key). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited primitive — and
the gold patch resolves (G-RESOLVE). The trust points are exactly those of PLAN
§1.1: A-reference soundness (G-AX) and refinement fidelity (this document,
G-EQ).
