# refinement.md — django__django-12273

The operation-by-operation correspondence between `model.py`'s implementation
(the `assign_identity` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model is validated == the real callee by
`axiom_check.py` / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The pk setter — `Model._set_pk_val` (`django/db/models/base.py:571`)

Gold hunk:
```
 def _set_pk_val(self, value):
+    for parent_link in self._meta.parents.values():
+        if parent_link and parent_link != self._meta.pk:
+            setattr(self, parent_link.target_field.attname, value)
     return setattr(self, self._meta.pk.attname, value)
```

| # | model.py impl op (`assign_identity`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `store: List[int]` (the attribute slots) | `self` and its `setattr`/`getattr` attribute store | R | attname-indexed `List[int]` ↔ `self.__dict__`; `store[s] = v` ↔ `setattr(self, attname(s), v)` (mapping.md §2). |
| A2 | parameters `target: List[int]`, `active: List[int]` | `self._meta.parents.values()` iterated, with each parent link's `target_field.attname` and the guard `parent_link and parent_link != self._meta.pk` | R + A-reference | the unchanged `_meta` metadata is abstracted to two parallel read-only lists; `target[k]` ↔ slot of `parents.values()[k].target_field.attname`, `active[k]==1` ↔ the guard holding (mapping.md §3.2). Its correspondence to the real `_meta` is validated by G-AX (A-reference), not assumed by an axiom. |
| A3 | `pk_idx: int` | `self._meta.pk.attname` slot | R | the identity slot index (mapping.md §2). |
| A4 | the loop `while k < n: if active[k] == 1: store[target[k]] = value` | `for parent_link in self._meta.parents.values(): if parent_link and parent_link != self._meta.pk: setattr(self, parent_link.target_field.attname, value)` | I (under R for the carriers) | identical control/data flow: iterate the parent links in order, and for each one the guard selects (`active[k]==1`), write `value` to its target slot. This is the changed operation, modeled **deeply** (spelled out), not behind an axiom. |
| A5 | `store[pk_idx] = value` | `return setattr(self, self._meta.pk.attname, value)` | I (under R) | the original identity write, unchanged by the patch. (`return setattr(...)` returns `None`; `assign_identity` returns `None`.) |

The discriminating content of the change — that the assignment **propagates to
every active parent-link target slot**, not only the pk slot — lives in the loop
A4. The pre-patch `_set_pk_val` had only the single A5 write; `model_prepatch.py`
reproduces exactly that (impl is just `store[pk_idx] = value`, no loop) and
**fails** the postcondition

```
Forall(j: 0<=j<len(target) ... Implies(active[j]==1, store[target[j]] == value))
```

i.e. the spec sensing the missing cascade (G-DIFF). This is the single
independently-fixed behavior, so one `model_prepatch.py` suffices.

## B. No consumed axioms; the only callee dependence is an A-reference

The operation calls no library/utility callee that the proof must axiomatize.
The three `_meta` reads (`pk.attname`, `parents.values()`,
`target_field.attname`) are **unchanged structural metadata**; they enter the
model as the read-only inputs `target` / `active` / `pk_idx`, whose fidelity to
the real `_meta` is checked by `axiom_check.py` (G-AX) — an **A-reference**, not
a consumed `@ContractOnly`. There is therefore no `# axioms` content (the region
is present but empty), and no dead axiom.

The guard semantics carried by `active` are themselves part of the A-reference:
G-AX exercises both the present-and-distinct case (single inheritance: own pk +
one distinct active link) and the promoted-pk case (multi inheritance: the
parent link that IS the pk is excluded, one distinct active link remains), so
the `active[k] = parent_link and parent_link != pk` encoding is validated on the
exact two structural shapes the F2P tests use.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — the propagation loop — is modeled **deeply** (A4, the spelled-out
guarded write loop over the slot store), not hidden behind an axiom about the
function under change. There is no consumed axiom.

## D. verify(model) ⇒ resolved

`assign_identity` verifies only if its impl establishes that, after the call,
the pk slot AND every active linked slot hold `value` while every other slot is
unchanged (the three postconditions). By R (attname-indexed `List[int]` ↔
`self.__dict__`; `store[s]=v` ↔ `setattr`) the verified loop+write equals the
gold `for … setattr(target_field.attname, value)` plus `setattr(pk.attname,
value)` on the attributes the operation touches. By G-AX the deep model's
metadata abstraction (`target`/`active`/`pk_idx`) equals the real `_meta`
(A-reference), and the real `_set_pk_val` performs exactly the cascade the model
proves. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited metadata reference — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: the A-reference soundness (G-AX) and refinement fidelity (this
document, G-EQ).
