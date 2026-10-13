# refinement.md — sphinx-doc__sphinx-10673

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_toctree_entries` impl region and the deep `mem`/`known`/`kept`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`, all
three hunks, and is the real correctness oracle, G-RESOLVE).

## A. The classification site — `TocTree.parse_content` (`sphinx/directives/other.py:79`)

This is the FAIL_TO_PASS-discriminating site. The gold widens the universe a
listed target is checked against, from the discovered source documents alone to
their union with the always-provided reference pages.

Gold hunks (`other.py`):
```
+ generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())
  ...
- all_docnames = self.env.found_docs.copy()
+ all_docnames = self.env.found_docs.copy() | generated_docnames
  ...
-                elif docname not in self.env.found_docs:
+                elif docname not in self.env.found_docs | generated_docnames:
```
(The glob branch also gains a `if docname in generated_docnames: continue`
guard so generated pages are not pulled in by `*` globs; the F2P test uses a
**non-glob** toctree, so the load-bearing change is the membership test above.)

| # | model.py impl op (`select_toctree_entries`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `entries`, `found`, `generated : List[int]` | the iterated target names, `self.env.found_docs`, and `generated_docnames` | R | document name `str` ↔ `int` id; `set`/`frozenset` ↔ `List[int]` with membership = `mem` (mapping.md §2). |
| A2 | `x = entries[i - 1]` (each listed target, in order) | the per-`entry` body of the `for entry in self.content` loop, after suffix-strip + `docname_join` (`other.py:104-118`) | R | the normalization producing each `docname` is identity on the F2P targets `genindex`/`modindex`/`search` (no suffix, no path join); modeled as reading the target id (mapping.md §2). |
| A3 | branch on `known(x, ToSeq(found), ToSeq(generated))` = `mem(x, found) or mem(x, gen)` | `docname not in self.env.found_docs | generated_docnames` (the negation selects the warn/drop branch; its complement is "retain") | A-reference | the changed membership operation is modeled **deeply**: `known` (= `mem ∨ mem`) is the set-union membership the patch performs. There is no consumed axiom; the deep model is validated **== the real set-union/membership** by G-AX (axiom_check.py asserts `kept == [e for e in entries if e in set(found)|set(generated)]`). Python set union `A | B` membership IS `x ∈ A ∨ x ∈ B` (mapping.md §3.2). |
| A4 | retain: `result = [x] + result` when known; else drop (output is the order-preserving `kept(entries, found, generated)`) | append `(title, docname)` to `toctree['entries']` in the non-warning branch; emit a warning and append nothing in the `docname not in …` branch | R + I | retaining iff known ↔ appending iff in the union; the model tracks the `docname` ids and their order (the F2P assertion), `title` (`None` for these targets) omitted (mapping.md §2). The backward loop builds the same order-preserving list `kept`. |

The discriminating content of the change — a target naming a generated
reference page (`genindex`/`modindex`/`search`), present in `generated` but
absent from `found`, must be **retained** — lives in `known(x, found, gen)`
returning `True` via the `mem(x, gen)` disjunct (model) ⇔ `docname in
self.env.found_docs | generated_docnames` being `True` via the
`generated_docnames` operand (real). The pre-patch checked `found` alone;
`model_prepatch.py` reproduces that (`if mem(x, ToSeq(found)):`) and **fails**
the postcondition `ToSeq(Result()) == kept(ToSeq(entries), …)` — specifically
the `else`-branch unfold `kept(cons) == kept(cons.drop(1))`, which requires
`not known(x)` but a generated-only target has `known(x) == True`. This is
exactly the spec sensing the change (G-DIFF).

## B. The two non-F2P-observable hunks (callee/render sites)

The gold also touches two further functions; both are shipped verbatim in
`patch.diff` (G-RESOLVE) but are **not independently observable** from the
FAIL_TO_PASS assertion (which inspects only `env.tocs['index']`, populated by
`parse_content`):

- `sphinx/environment/adapters/toctree.py::TocTree.resolve` /
  `_entries_from_toctree` — adds an `elif ref in generated_docnames:` branch
  that renders a reference node for a generated page during toctree
  *resolution* (HTML/XML writing), so the resolved tree links the page instead
  of warning. This runs after `env.tocs` is built and does not change the entry
  lists the F2P test asserts.
- `sphinx/environment/collectors/toctree.py::assign_figure_numbers` /
  `_walk_doctree` — adds `if subdocname in generated_docnames: continue` so the
  figure-numbering walk skips generated pages. This is numbering bookkeeping,
  not an `env.tocs` entry list.

Both are pure additive guards keyed on the same `generated_docnames` set as
site A; their correctness is carried by G-RESOLVE (the gold patch resolves with
all three hunks). They are not modeled as separate functions and get no
separate failing `model_prepatch_<k>`, because there is no independent F2P
behaviour to discriminate — the FAIL_TO_PASS observes site A only. (Per
SPEC_GUIDE §3 we model the F2P-observable site faithfully and deeply rather than
collapse all three into one function; sites B are sound-by-inclusion via the
verbatim gold and G-RESOLVE.) See mapping.md §3.3.

## C. No kind-3 (unexpressible-changed-op) steps

Every step in §A is R, A-reference, or I. The one operation that genuinely
*changed* — the membership universe of the target classification — is modeled
**deeply** (`known` = `mem(·,found) ∨ mem(·,gen)`, the spelled-out set-union
membership over `PSeq[int]`, an **A-reference**), not hidden behind an axiom
about the function under change. There is **no consumed `@ContractOnly`
axiom** (A-consumed) in this bundle: Python set union/membership are language
primitives modeled directly, so the only trust point is the A-reference, which
G-AX validates.

## D. verify(model) ⇒ resolved

`select_toctree_entries` verifies only if its output equals the exact
order-preserving retention `kept(entries, found, generated)` with the head
decision being `known(x, found, gen)` (membership in EITHER family, A3). By R
(name `str` ↔ `int` id, `set` ↔ membership fold) the verified function equals
the patched `parse_content` classification on the tested targets; by G-AX the
deep model `kept` equals the real set-union membership the patch performs
(A-reference). The two additional gold hunks (§B) are non-F2P-observable
additive guards carried by the verbatim gold patch and G-RESOLVE. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited A-reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ); there is no
consumed axiom.
