# refinement.md — django__django-14089

The operation-by-operation correspondence between `model.py`'s implementation
(the `reverse_order` impl region and the deep `rev` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The backward-enumeration site — new `OrderedSet.__reversed__`

Gold hunk (`django/utils/datastructures.py`, inserted after `__iter__`):
```
+    def __reversed__(self):
+        return reversed(self.dict)
```

| # | model.py impl op (`reverse_order`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elements: List[int]` | the receiver `self`, whose ordered contents are `self.dict`'s keys in insertion order | R | `OrderedSet`'s ordered contents ↔ `List[int]` of distinct element keys in insertion order (mapping.md §1, §2). `self.dict = dict.fromkeys(iterable or ())` and `__iter__` returns `iter(self.dict)`, so the forward enumeration is exactly `elements`. |
| A2 | the result is `rev(ToSeq(elements))`, the reversal of the forward enumeration, computed by the backward loop that appends each element from the end | `reversed(self.dict)` (materialized) | A-reference | the changed operation — providing a backward enumeration — is modeled **deeply**: `rev` (the spelled-out front-recursive reversal in the `pure` region) and the verified loop in `reverse_order` ARE the reversal. There is no consumed `reversed` axiom — the proof never depends on one. Instead the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) builds `dict.fromkeys(items)` and asserts `list(reversed(d)) == rev(list(d))`. Because `self.dict` keeps insertion order with distinct keys, `reversed(self.dict)` yields the keys in reverse insertion order — exactly the element-wise reversal of `iter(self.dict)` (mapping.md §3.1). The model loop and the real callee compute the same sequence. |
| A3 | `Result()` is a freshly-built `List[int]` (full permission), the input `elements` is returned read-only (`Acc(list_pred(elements), 1/2)` required AND ensured) | `reversed(self.dict)` returns a fresh iterator and does not mutate `self.dict` | R + I | the new method only reads `self.dict`; the verified read-only permission discipline (directive 5) mirrors that. G-AX confirms materializing `reversed(d)` leaves `list(iter(d))` unchanged. |

The discriminating content of the change — the backward enumeration is the
**reversal** of the forward enumeration, not a copy of it — lives in
`ToSeq(Result()) == rev(ToSeq(elements))` (model) ⇔ the new `reversed(self.dict)`
(real). Before the patch there was no `__reversed__` (and `OrderedSet` exposes
no `__getitem__`/sequence protocol), so `reversed(OrderedSet(...))` could not
produce a reverse-ordered traversal; `model_prepatch.py` reproduces the
faithful pre-patch skeleton (the traversal hands back the elements in forward
order) and **fails** the postcondition `ToSeq(Result()) == rev(ToSeq(elements))`,
which is exactly the spec sensing the change (G-DIFF). Its failing clause is the
reversal postcondition (witnessed by Nagini at `model_prepatch.py:58`).

## B. The iterator-ness obligation

The F2P test also asserts `isinstance(reversed(OrderedSet([1,2,3])),
collections.abc.Iterator)`. `reversed(self.dict)` returns a
`dict_reversekeyiterator`, which IS a `collections.abc.Iterator` — a guaranteed
property of the builtin `reversed`. This is not a sequence-value property Nagini
expresses over `List[int]` (the model materializes the traversal as a list whose
*order* is pinned), so it is discharged by the A-reference check: axiom_check.py
asserts `isinstance(reversed(d), collections.abc.Iterator)` on every input. This
is an A-reference obligation on the same real callee as A2, not a separate
consumed axiom, and not a kind-3 step (the *value* the iterator yields is
modeled deeply by `rev`; only the wrapper type is checked out-of-band).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding a backward enumeration equal to the reversal of the forward
one — is modeled **deeply** (the spelled-out reversal `rev` consumed in
`reverse_order`, step A2, an **A-reference**), not hidden behind an axiom about
the function under change: there is **no consumed `reversed` axiom** and the
model's `axioms` region is empty. The builtin `reversed(dict)` appears only as
the **A-reference** that G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`reverse_order` verifies only if its output equals the exact reversal of the
forward enumeration (A2) — a wrong impl that preserves the order, drops, or
duplicates elements fails the postcondition. By R (`OrderedSet` contents ↔
`List[int]`; `self.dict` insertion order ↔ `elements`) the verified reversal
equals `reversed(self.dict)` materialized on the tested inputs; by G-AX the
deep model `rev` equals the real `reversed(dict)` (A-reference) and `reversed(d)`
is a `collections.abc.Iterator` (the F2P type obligation). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
The trust point is exactly the one of PLAN §1.1 that applies here: axiom/
deep-model soundness (G-AX); refinement fidelity is this document (G-EQ).
