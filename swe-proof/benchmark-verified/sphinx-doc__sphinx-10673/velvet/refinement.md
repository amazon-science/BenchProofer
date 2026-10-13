# refinement.md — sphinx-doc__sphinx-10673

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `selectToctreeEntries` `do` block and the `retainedEntries`/`targetExists`
pure model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative + grounding are audited by **G-EQ** / **G-AX**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## 0. What the F2P test observes (scoping)

`tests/test_environment_toctree.py::test_toctree_index` builds the doc set and
asserts on `app.env.tocs['index']`: the second toctree node must carry

```
entries=[(None, 'genindex'), (None, 'modindex'), (None, 'search')]
```

i.e. the three auto-generated reference targets are **retained** as toctree
entries instead of being dropped with a "nonexisting document" warning. Those
entries are produced solely by `TocTree.parse_content`
(`sphinx/directives/other.py`) appending to `toctree['entries']`. The modeled
function is therefore `parse_content`'s per-entry validity decision; the other
two gold hunks are not observed by this test (§C).

## A. The validity decision — `TocTree.parse_content` (`sphinx/directives/other.py`)

Gold hunk (the discriminating change):
```
+        generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())
         ...
-        all_docnames = self.env.found_docs.copy()
+        all_docnames = self.env.found_docs.copy() | generated_docnames
         ...
-                elif docname not in self.env.found_docs:
+                elif docname not in self.env.found_docs | generated_docnames:
```
The pre-patch validity test was `docname in self.env.found_docs`; the post-patch
test is `docname in self.env.found_docs | generated_docnames`. An entry naming
an auto-generated target now passes and is appended to `toctree['entries']`.

| # | Solution.lean impl op (`selectToctreeEntries`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `requested : List String` | the directive `content` lines, each a plain entry (`ref == docname == entry`) | R | each content line ↔ a docname string; `str` ↔ `String`, ordered list ↔ `List String` (mapping.md §2). The F2P entries are simple, suffixless, top-level names, so suffix-stripping + `docname_join` are observationally identity (mapping.md §2). |
| A2 | parameter `sourceDocs : List String` | `self.env.found_docs` (a `set[str]`) | R | the documents that have a backing source file; `set` membership ↔ `List.contains` (mapping.md §2). Order is irrelevant — only membership is observed. |
| A3 | parameter `autoTargets : List String` | `generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())` | R | the reference targets the project provides automatically; key set ↔ `List String` membership. **Grounded** (not consumed): G-AX (`axiom_check.py`) pins this key set is exactly `{genindex, modindex, search}` in the real repo. mapping.md §3. |
| A4 | `targetExists sourceDocs autoTargets e = sourceDocs.contains e \|\| autoTargets.contains e` | `docname in self.env.found_docs \| generated_docnames` | I | identical concrete predicate: set-union membership ↔ disjunction of `.contains` (De Morgan: `x ∈ A ∪ B ↔ x∈A ∨ x∈B`). G-CONF transliterates both sides. |
| A5 | the backward `while` fold keeping `e` iff `targetExists …` (= `retainedEntries`) | the `for entry in self.content` loop appending `(title, docname)` to `toctree['entries']` exactly on the `else` (valid) branch | I | the retained sequence is the request-order filter by A4; the gold's drop-on-warning branch ↔ the model's `[]` contribution. The order-preserving filter is concrete (transliterated by G-CONF). |
| A6 | `out` returned (`List String`) | `toctree['entries']` entry names read by `app.env.tocs['index']` | R | the test compares entry **names** (the `(None, docname)` pairs' docnames); titles are `None` for plain entries (mapping.md §2). |

Discriminating content of the change — an entry that is **only** an auto target
(in `autoTargets`, not in `sourceDocs`) must be **kept** — lives in
`targetExists`'s `|| autoTargets.contains e` disjunct (model) ⇔ the
`| generated_docnames` union (real). `Solution_prepatch.lean` reproduces the
pre-patch test (membership in `sourceDocs` only) and **fails** the loop-body
obligation `out = retainedEntries …` (G-DIFF), because for an entry in
`autoTargets \ sourceDocs` the buggy contribution `[]` ≠ the spec's `[e]`.

## B. No consumed axioms, no deep-model references

`autoTargets` is a free input, so there is no callee whose contract the proof
assumes — the `axioms` region is empty and `deep_model_references` is `[]`.
G-AX's role here is purely to **ground** the R-binding A3 (that the real
`generated_docnames` set is `{genindex, modindex, search}`), so the conformance
oracle and the F2P scenario are driven with the true set. There is no A-consumed
or A-reference row.

## C. Other gold hunks — out of modeled scope, test-neutral

The gold patch also edits two further sites:

1. `sphinx/environment/adapters/toctree.py::TocTree.resolve` —
   `_entries_from_toctree` gains an `elif ref in generated_docnames:` branch that
   *renders* a generated entry as a link node. This affects the **resolved**
   output tree (`get_toctree_for` / HTML), not `env.tocs['index']`, which the
   F2P test reads. It is the downstream rendering of the entries A1–A6 retain.
2. `sphinx/environment/collectors/toctree.py::assign_figure_numbers` — skips
   generated docnames while walking for figure numbers (`if subdocname in
   generated_docnames: continue`). A guard that only matters when `numfig` is on
   and a figure sits under such an entry; test-neutral here.

Also unmodeled: the glob branch's added `if docname in generated_docnames:
continue` (don't pull generated targets into a `*`-glob). The F2P scenario uses
no glob entry.

These are genuine R/I-or-identity refinements of *unobserved* behaviour; none is
a kind-3 (inexpressible-changed-op). The single behaviour the F2P test demands —
auto targets become valid toctree entries — is modeled directly and deeply by
A1–A6. There is no consumed axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`selectToctreeEntries` verifies only if its output equals the request-order
filter keeping exactly the entries that are in `sourceDocs ∪ autoTargets` (A4/A5)
— in particular it MUST keep an entry that is only an auto target (the
`ensures … autoTargets.contains e → e ∈ out` clause). By R (A1–A3, A6:
`str ↔ String`, set ↔ membership, names-only comparison) the verified filter
equals the patched `parse_content`'s appended `toctree['entries']` on the tested
inputs; by G-AX the autoTargets carrier is grounded to the real
`generated_docnames` set; by G-CONF the R/I transliteration agrees with
`patch.diff`'s acceptance behaviour on ≥10⁵ inputs. Therefore a model satisfying
this spec, refined by the map above, produces the gold patch's observed entries —
and the gold patch resolves (G-RESOLVE). Trust points are exactly: the R-binding
grounding (G-AX A3) and refinement fidelity (this doc, G-EQ + G-CONF).
