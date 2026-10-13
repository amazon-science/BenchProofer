# refinement.md — pytest-dev__pytest-10356

The operation-by-operation correspondence between `model.py`'s implementation
(the `unpacked_tokens` impl region + the deep `concat_chain` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/abstracted callee — **A-consumed** where the proof uses an
axiom's `Ensures`, **A-reference** where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The mark-collection site — `get_unpacked_marks` (`src/_pytest/mark/structures.py:358`)

Gold hunk (class branch added; non-class branch unchanged in behaviour):
```
- def get_unpacked_marks(obj: object) -> Iterable[Mark]:
-     mark_list = getattr(obj, "pytestmark", [])
-     if not isinstance(mark_list, list):
-         mark_list = [mark_list]
-     return normalize_mark_list(mark_list)
+ def get_unpacked_marks(obj, *, consider_mro: bool = True) -> List[Mark]:
+     if isinstance(obj, type):
+         if not consider_mro:
+             mark_lists = [obj.__dict__.get("pytestmark", [])]
+         else:
+             mark_lists = [x.__dict__.get("pytestmark", []) for x in obj.__mro__]
+         mark_list = []
+         for item in mark_lists:
+             if isinstance(item, list): mark_list.extend(item)
+             else: mark_list.append(item)
+     else:
+         ...  # unchanged single-attribute path for non-classes
+     return list(normalize_mark_list(mark_list))
```

| # | model.py impl op (`unpacked_tokens`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `chain: PSeq[PSeq[int]]` | `obj` is a class (the `isinstance(obj, type)` branch); the chain is `[x.__dict__.get("pytestmark", []) for x in obj.__mro__]` | R | a class ↔ its MRO own-mark lists; each own list ↔ `PSeq[int]` of token ids (mapping.md §2). The model covers the class branch — the behaviour the F2P test exercises. |
| A2 | parameter `consider_chain: bool` | keyword-only `consider_mro: bool = True` | R/I | same boolean flag, renamed to a non-leaking identifier; same two branches. |
| A3 | `if not consider_chain: return chain[0]` | `if not consider_mro: mark_lists = [obj.__dict__.get("pytestmark", [])]` → concatenated → normalised | R | the `consider_mro=False` branch reads a single-element `mark_lists` whose only element is the class's own dict list; concatenation of a one-element chain is that element, so `Result() == chain[0]` (mapping.md §2, `normalize_mark_list` = identity on the name sequence). |
| A4 | `result = PSeq().take(0)`; backward loop `result = chain[i-1] + result`; `Result() == concat_chain(chain)` | `mark_lists = [...for x in obj.__mro__]`; `for item in mark_lists: mark_list.extend(item)` | A-reference | the changed collection is modeled **deeply**: `concat_chain` (the spelled-out front-recursive fold in the `pure` region) and the verified backward loop ARE the MRO-ordered concatenation. There is no consumed concatenation axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `get_unpacked_marks` on F2P + boundary + ~4000 fuzz hierarchies and asserts the name sequence `== concat_chain(chain)`. The `list.extend` over the MRO own-lists IS that concatenation (mapping.md §3.1). |
| A5 | `result` returned (a `PSeq[int]`) | `list(normalize_mark_list(mark_list))` | R | `normalize_mark_list` is order/length-preserving on `Mark` items (the F2P marks are proper `Mark`s), hence the identity on the token-identifier sequence (mapping.md §2); the F2P test compares the ordered mark list. |

The discriminating content of the change — collecting along the FULL MRO so a
class with two independently-decorated ancestors keeps BOTH ancestors' marks
(`["c","a","b"]`), not just one — lives in `Result() == concat_chain(chain)`
(model, the `consider_chain=True` clause) ⇔ the
`[x.__dict__.get("pytestmark", []) for x in obj.__mro__]` concatenation (real).
The pre-patch read one MRO-resolved attribute (`getattr(obj, "pytestmark", [])`)
and lost the other ancestors' marks; `model_prepatch.py` reproduces that
(`return chain[0]`, the single-source result) and **fails** the postcondition
`Implies(consider_chain, Result() == concat_chain(chain))` — exactly the spec
sensing the change (G-DIFF).

## B. The store site — `store_mark` (`structures.py:383`)

Gold hunk:
```
- obj.pytestmark = [*get_unpacked_marks(obj), mark]
+ obj.pytestmark = [*get_unpacked_marks(obj, consider_mro=False), mark]
```

This is the call-site change that makes each class's OWN `__dict__["pytestmark"]`
hold exactly the class's directly-applied marks (so the MRO walk in `A` does not
double-count ancestor marks). It is not modeled as a separate function: its sole
behavioural role is to establish the `chain[k]` = own-marks abstraction (mapping.md
§1). Its correctness is audited by **G-AX**, where every class in axiom_check.py
is constructed through the real decorator path that calls `store_mark` — so the
real `chain` per-member own-lists are produced exactly as the patch produces them,
and the deep-model equality `get_unpacked_marks(C) == concat_chain(chain)` would
break if `store_mark` did not pass `consider_mro=False`. No separate failing
`model_prepatch_<k>` is needed: site A's prepatch already exercises the
multiple-inheritance mark-loss that this call-site change is part of fixing, and a
prepatch must keep the spec byte-identical (G-DIFF's `same_spec`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — collecting marks along the whole MRO — is modeled **deeply** (the
spelled-out front-recursive fold `concat_chain` consumed in `unpacked_tokens`,
step A4, an **A-reference**), not hidden behind an axiom about the function under
change. There is **no consumed `@ContractOnly` axiom**: `normalize_mark_list`
(the only unchanged callee touched) is the identity on the token-identifier
sequence under the refinement (mapping.md §2), so it needs no axiom; the changed
collection's `get_unpacked_marks` appears only as the **A-reference** G-AX
validates the deep model against.

## D. verify(model) ⇒ resolved

`unpacked_tokens` verifies only if its output, when the full chain is considered,
equals the exact MRO-ordered concatenation `concat_chain(chain)` (A4) and, when
not, equals `chain[0]` (A3). By R (class ↔ MRO own-lists; `normalize_mark_list`
identity on names) the verified collector equals
`list(normalize_mark_list([...for x in obj.__mro__]))` on the tested class inputs;
by G-AX the deep model `concat_chain` equals the real `get_unpacked_marks`
(A-reference) on the F2P shape and ~4000 fuzz hierarchies. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep model — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: deep-model/axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
