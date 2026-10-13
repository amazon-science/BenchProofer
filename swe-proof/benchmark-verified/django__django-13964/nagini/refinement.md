# refinement.md — django__django-13964

The operation-by-operation correspondence between `model.py`'s implementation
(the `adopt_referenced_key_if_unset` impl region + the deep model
`is_empty_placeholder` / `stored_seq`) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee/datum by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The unset-key adoption branch — `Model._prepare_related_fields_for_save` (`django/db/models/base.py:911`)

Gold hunk (the one change, at `base.py:936`):
```
-                elif getattr(self, field.attname) is None:
+                elif getattr(self, field.attname) in field.empty_values:
                     # Use pk from related object if it has been saved after
                     # an assignment.
                     setattr(self, field.attname, obj.pk)
```

This `elif` branch is reached only after the preceding guard
`if obj.pk is None: … raise ValueError(…)` (`base.py:928-935`) has passed —
i.e. the referenced object `obj` carries a real (non-`None`) stored key. The
bug: the branch fired only when the local foreign-key attribute was exactly
`None`, so a textual foreign key whose attribute had been initialized to the
empty string `''` (the case for a `CharField`/non-numeric primary key assigned
before its key was set) was **not** filled with the referenced key — it stayed
`''`, the silent data loss. The fix widens the emptiness test from `is None` to
`in field.empty_values` (which contains both `None` and `''`).

| # | model.py impl op (`adopt_referenced_key_if_unset`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target: SaveTarget` with field `target.fk : Optional[List[int]]` | the model instance `self`; its local foreign-key value reached via `getattr/setattr(self, field.attname, …)` | R | the persisting object with only its one touched attribute modelled; the dynamically-named FK attribute ↔ `target.fk`; the absent marker `None` ↔ `target.fk is None`, the empty string `''` ↔ `target.fk == []`, a concrete textual key ↔ a non-empty `List[int]` (mapping.md §1, §2). |
| A2 | parameter `related_key: List[int]`, `Requires(len(related_key) > 0)` | `obj.pk` — the referenced object's stored key, known non-`None` because the branch is past the `if obj.pk is None: … raise` guard | R | the saved referenced key ↔ `related_key`; the `obj.pk is not None` guard ↔ `len(related_key) > 0` (a non-empty stored key; mapping.md §1, §2). |
| A3 | `is_empty_placeholder(target.fk)` (the branch condition) | `getattr(self, field.attname) in field.empty_values` | **A-reference** | the changed membership test is modelled **deeply**: `is_empty_placeholder` (the spelled-out `value is None or len(value) == 0`) IS the emptiness decision. There is **no consumed axiom**. Instead the deep model is validated **== the real `field.empty_values` membership** out-of-band: G-AX (axiom_check.py) reads the real `field.empty_values` (= `[None, '', [], (), {}]`, the inherited `Field` default) and asserts membership on every value the attribute can hold (`None`, `''`, a concrete key) equals `is_empty_placeholder` (mapping.md §3.1). The two collapse on the reachable values: `None`→empty, `''`→empty, non-empty key→not empty. |
| A4 | `target.fk = adopted`, where `adopted` is a fresh `List[int]` copy of `related_key` (the loop) | `setattr(self, field.attname, obj.pk)` | **I** (under R on the attribute name and the str↔List[int] carrier) | the FIX body — store the referenced object's stored key into the local foreign-key attribute — is the identical concrete operation, with the dynamic attribute name refined to `target.fk` (R) and `obj.pk` refined to `related_key` (R). The model copies `related_key`'s contents element-by-element into a fresh list rather than aliasing it: a `str` is immutable, so storing the value vs. storing a copy of its contents is observationally identical (`stored_seq(target.fk) == ToSeq(related_key)`); the copy keeps the Nagini predicate permissions disjoint without changing behaviour. |
| A5 | (no node — the branch is not entered) | the `elif` does not fire | I | when `is_empty_placeholder(target.fk)` is False the local attribute is left untouched, exactly as the gold `elif` does not fire for a non-empty value. The faithfulness postcondition `target.fk is Old(target.fk) and stored_seq unchanged` pins this. |

The discriminating content of the change — the **empty string** `''` is now
treated as unset (so the referenced key is adopted), whereas pre-patch only the
absent marker `None` was — lives in `is_empty_placeholder([]) == True` (model)
⇔ `'' in field.empty_values` (real). The pre-patch tested only `is None`;
`model_prepatch.py` reproduces that (`if target.fk is None:`) and **fails** the
postcondition: for an empty-string local key (`Old(target.fk) == []`, an empty
placeholder) it leaves `target.fk == []`, so `len(target.fk) > 0` is violated
(and clause (1) `stored_seq(target.fk) == ToSeq(related_key)` fails) — which is
exactly the spec sensing the change (G-DIFF).

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: its branch condition is
`target.fk is None` (the absent marker only), exactly the pre-patch
`getattr(self, field.attname) is None`. With the byte-identical frozen spec it
**fails** verification on the postcondition `Ensures(len(target.fk) > 0)`
(`model_prepatch.py:94` — `Assertion (len(target.fk) > 0) might not hold`),
because for the empty-string case (`Old(target.fk) == []`) the pre-patch branch
does not fire and the attribute stays the empty sequence. That is precisely the
behaviour the F2P test
`test_save_fk_after_parent_with_non_numeric_pk_set_on_child` observes: a child
with a textual-PK foreign key, parent saved after assignment, must end with
`child.parent_id == parent.name` (here `'jeff'`), not `''`.

The faithfulness clause (2) — a present, non-empty key preserved untouched
(`target.fk is Old(target.fk) and stored_seq unchanged`) — keeps the spec
honest about the unchanged behaviour the PASS_TO_PASS tests observe
(`test_save_nullable_fk_after_parent_with_to_field`, where the local key is
already `'jeff'` and must be left as-is), so a wrong impl cannot satisfy the
spec by clobbering a deliberate value. The `Requires(len(related_key) > 0)`
keeps the spec faithful to the branch's reachability (it runs only once the
referenced key is known).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — widening the emptiness test from `is None` to `in field.empty_values`
— is modelled **deeply** (the spelled-out `is_empty_placeholder` predicate,
step A3, an **A-reference**), not hidden behind an axiom about the function under
change. There is **no consumed `@ContractOnly` axiom** (the `axioms` region is
empty); `field.empty_values` is a fixed known constant, not an opaque callee,
and its membership is validated `== is_empty_placeholder` by G-AX (A-reference).
The fix body itself (step A4) is an **I** step (the same `setattr(…obj.pk)`
store, with the attribute name and the key carrier refined by R).

## D. verify(model) ⇒ resolved

`adopt_referenced_key_if_unset` verifies only if (A3/A4) it stores the
referenced key into the local attribute whenever that attribute holds an empty
placeholder — **including the empty string** — and (A5/clause 2) leaves a
non-empty key untouched. By R (the in-memory object and its dynamically-named FK
attribute ↔ `SaveTarget.fk`; `obj.pk` ↔ `related_key`; `str` ↔ `List[int]`) and
the single **I** fix step, the verified branch equals the gold
`elif getattr(self, field.attname) in field.empty_values:
setattr(self, field.attname, obj.pk)` on the tested inputs. By G-AX the real
`field.empty_values` membership equals the deep model `is_empty_placeholder` it
stands in for (A-reference), and the real changed method adopts the textual key
end-to-end. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited A-reference — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
