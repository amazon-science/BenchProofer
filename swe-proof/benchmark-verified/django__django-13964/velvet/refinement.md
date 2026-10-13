# refinement.md — django__django-13964

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`fillEmptyKeyRefs` `do` block, with the deep models `resolvedKey`/`resolvedKeys`/
`isEmpty`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee/notion by G-AX), or **I** (identical concrete op). EVERY step is R, A, or
I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reconciliation site — `_prepare_related_fields_for_save` (`django/db/models/base.py:911`)

Gold hunk (`base.py:936`):
```
-                elif getattr(self, field.attname) is None:
+                elif getattr(self, field.attname) in field.empty_values:
                     # Use pk from related object if it has been saved after
                     # an assignment.
                     setattr(self, field.attname, obj.pk)
```

The function loops `for field in self._meta.concrete_fields`, and for each cached
relation whose related object is present and carries a key (`obj.pk is not None`),
reaches the edited `elif`. `refs` models exactly that filtered sequence of
references; per reference the model computes `resolvedKey stored targetKey`.

| # | Solution.lean impl op (`fillEmptyKeyRefs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `refs : List KeyRef` | the cached FK references reaching the `elif` (the filtered `for field` loop) | R | the loop over `self._meta.concrete_fields`, restricted to relation fields whose related object is cached/present/has-a-key, ↔ `List KeyRef` in concrete-field order (mapping.md §2). The two prior UNCHANGED cases (`if not obj: continue`; the `obj.pk is None` `raise`) are the filter; the precondition `r.targetKey ≠ pyNone` records that survivors carry a key. |
| A2 | `r.stored : PyVal` | `getattr(self, field.attname)` | R | the locally-stored FK value, mapped by the `PyVal` bijection (`None↔pyNone`, `''↔pyStr []`, `[]/()/{}↔pyColl 0`, `int↔pyInt`; mapping.md §2). |
| A3 | `r.targetKey : PyVal` | `obj.pk` (where `obj = getattr(self, field.name)`) | R | the related object's primary key, mapped by the same bijection. |
| A4 | `isEmpty r.stored` | `getattr(self, field.attname) in field.empty_values` | A-reference | the changed condition is modeled **deeply**: `isEmpty` (pure region) IS the structural recognizer of `x in field.empty_values` (`field.empty_values == [None,'',[],(),{}]`). No consumed `emptyValues` axiom; the equality of this deep model to the real membership test is the **A-reference** G-AX validates (mapping.md §3.1). |
| A5 | `resolvedKey r.stored r.targetKey = if isEmpty r.stored then r.targetKey else r.stored` | `if … in field.empty_values: setattr(self, field.attname, obj.pk)` else leave `field.attname` as is | I (over A4's decision) | the adopt-or-keep is a concrete conditional transliterated by G-CONF: empty stored key ⇒ the post-state attname is `obj.pk`; otherwise the attname is unchanged. |
| A6 | the backward `while` fold building `result = resolvedKeys refs` | the `for field` loop applying the `elif` to each reference | I | concrete iteration; the fold computes, in order, the resolved stored key per reference. G-CONF transliterates it. |
| A7 | `out : List PyVal` returned | the post-state FK attname values after the loop (`setattr` side effects) | R | the modeled function returns the resolved stored keys as a value (functional model); the real side-effecting `setattr` writes those same keys back to `self`. The F2P test observes the post-state `child.parent_id`, which equals `out`'s entry for that reference (mapping.md §2). |

Discriminating content of the change — an **empty-but-present** stored key (the
empty string of a non-numeric primary key, `pyStr []`) must trigger adoption of
the related object's key, where `is None` did not — lives in
`isEmpty (pyStr []) = true` (model) ⇔ `'' in field.empty_values == True` (real).
The pre-patch condition `getattr(self, field.attname) is None` fires only on
`pyNone`; `Solution_prepatch.lean` reproduces that (`if r.stored = pyNone`) and
**fails** `out = resolvedKeys refs` exactly at a `stored` that is empty but not
`pyNone` (G-DIFF; the unsolved goal is `(if stored = pyNone …) = resolvedKey
stored …`).

## B. No A-consumed axioms

The routine consults no outside contract. Both observables of the changed branch
— "is the stored key empty" (A4) and "adopt the related key when so" (A5) — are
spelled out in the `pure`/`impl` regions and validated as A-references by G-AX
(mapping.md §3.1). There is no dead `axiom` the proof never uses.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — widening
the trigger from "absent" to "empty" — is modeled **deeply** (`isEmpty` plus the
`resolvedKey` decision, an A-reference + I), not hidden behind an axiom about the
function under change.

## D. verify(Solution) ⇒ resolved

`fillEmptyKeyRefs` verifies only if its output equals `resolvedKeys refs` — i.e.
each reference's resolved key is `obj.pk` exactly when the stored key is empty
(`isEmpty`, including the empty string), else the stored key unchanged (A5, A7).
By R (`PyVal` bijection, concrete-field-order list, post-state = returned value)
the verified routine equals the patched `_prepare_related_fields_for_save` on the
tested references; by G-AX the deep model `isEmpty` equals the real
`x in field.empty_values` (A-reference) and the end-to-end empty⇒adopt decision
matches the patched routine; by G-CONF the R/I transliteration of the fold agrees
with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited A-reference — and the gold patch resolves (G-RESOLVE). The single trust
point (plan §1.1) is refinement fidelity (this doc + G-CONF) plus the A-reference
soundness (G-AX); there is no consumed axiom.
