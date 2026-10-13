# refinement.md — django__django-9296

The operation-by-operation correspondence between `model.py`'s implementation
(the `paginate_iter` impl region, the deep `mapped` model, and the
`page_lookup` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The traversal site — new `Paginator.__iter__` (`django/core/paginator.py`, inserted at line 37)

Gold hunk (purely additive):
```python
+    def __iter__(self):
+        for page_number in self.page_range:
+            yield self.page(page_number)
```

| # | model.py impl op (`paginate_iter`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `page_numbers: List[int]` | `self.page_range` (`range(1, self.num_pages + 1)`) | R | `range` ↔ its materialized ordered element list `[1..num_pages]` (mapping.md §2). The model abstracts the unchanged `page_range` property to its element list; it does not re-derive the property. |
| A2 | the backward loop `while i > 0: ... result = [page_lookup(x)] + result; i -= 1` building `result` so that `ToSeq(result) == mapped(ToSeq(page_numbers))` | `for page_number in self.page_range: yield self.page(page_number)` | R + I | both produce, in `page_range` order, one item per page number. The gold generator yields front-to-back; the verified loop constructs the same list back-to-front by prepending (`result = [page_lookup(x)] + result`), so the *result order is identical* (`mapped` is front-recursive; the backward loop discharges one unfold per step — the canonical pattern). The control structure (iterate the page-number run once, in order, one item each) is the same; only the construction direction differs, yielding an identical ordered result. |
| A3 | `page_lookup(x)` — the per-page-number value placed at each position | `self.page(page_number)` — the page yielded for each page number | A-consumed | `page_lookup` is the unchanged page-by-number accessor `Paginator.page` (mapping.md §3.2). The proof uses only that it is a pure function of the page number (axiom `Ensures(True)`); G-AX confirms determinism on the real `Paginator.page`. |
| A4 | the result is `mapped(ToSeq(page_numbers))`, i.e. the in-order image of `page_lookup` over the page-number run | the generator's overall output: page(n) for each n in page_range, in order | A-reference | the changed behaviour — *which* pages are produced *in what order* — is modeled **deeply** by the front-recursive `mapped` fold in the `pure` region; there is no `__iter__` axiom the proof consumes. The deep model is validated **== the real traversal** out-of-band: G-AX (axiom_check.py) asserts `list(iter(paginator)) == [paginator.page(n) for n in paginator.page_range]` page-for-page over a broad config sweep incl. the F2P witness (mapping.md §3.1). |

The discriminating content of the change — that walking the collection yields a
non-empty, in-order page traversal at all — lives in the postcondition
`ToSeq(Result()) == mapped(ToSeq(page_numbers))`. Pre-patch the collection has
no traversal (it is not iterable), so the traversal produces nothing;
`model_prepatch.py` reproduces that (the impl returns `[]`) and **fails** this
postcondition for every non-empty page-number run, which is exactly the spec
sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one behaviour that genuinely *changed* — the
addition of an ordered, per-page-number traversal — is modeled **deeply** (the
spelled-out front-recursive map `mapped` consumed in `paginate_iter`, step A4,
an **A-reference**), not hidden behind an axiom about the function under change:
there is no consumed `__iter__` axiom. The only consumed axiom, `page_lookup`
(**A-consumed**, step A3), covers the **unchanged** accessor (`Paginator.page`)
the new code invokes, and claims only the weakest property the proof needs
(purity in the page number). The real `Paginator.page`/`__iter__` appear as the
**A-reference** that G-AX validates the deep model against.

## C. verify(model) ⇒ resolved

`paginate_iter` verifies only if its output equals the exact in-order image
`mapped` of the page-by-number accessor over the page-number run (A4) — i.e. one
item per page number, in `page_range` order, none skipped/repeated/reordered. By
R (range ↔ element list; generator ↔ ordered result list; `Page` ↔ opaque
`page_lookup(n)`) this verified traversal equals
`(self.page(n) for n in self.page_range)` on the tested inputs; by G-AX the deep
model `mapped(page_range)` equals the real `Paginator.__iter__` (A-reference)
page-for-page and `Paginator.page` meets the `page_lookup` axiom it stands in for
(A-consumed). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The F2P test `test_paginator_iteration`
(`Paginator([1,2,3], 2)` ⇒ pages `[1,2]` then `[3]`) is exactly the A4 ordered
image on a two-page run; a verifying impl yields page 1 then page 2 in order,
matching. The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
