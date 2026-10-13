# refinement.md — sphinx-doc__sphinx-7440

The operation-by-operation correspondence between `model.py`'s implementation
(the `register_term_name` impl region and the deep `casefold` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, proof uses the axiom's
`Ensures`, and **A-reference**, a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The registration site — `make_glossary_term` (`sphinx/domains/std.py:308`)

Gold hunk 1:
```
- std.note_object('term', termtext.lower(), node_id, location=term)
+ std.note_object('term', termtext, node_id, location=term)
```

| # | model.py impl op (`register_term_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `termtext: List[int]` | the `termtext` value (`term.astext()`) used as the `note_object` name argument | R | `str` ↔ `List[int]` code points (mapping.md §2); `termtext = term.astext()` is the rendered term text. |
| A2 | the result is `termtext` copied **verbatim** (the forward loop appends each `termtext[i]` unchanged; postcondition `ToSeq(Result()) == ToSeq(termtext)`, plus `len` and element-wise equality) | the second argument of `note_object` is `termtext` (no `.lower()`) | I + R | the post-patch code passes the term text itself as the key; the model computes the identity copy. The verbatim equality is the same concrete operation under the `str`↔`List[int]` refinement. The registered key is what `note_object` stores and `get_objects` re-emits unchanged (mapping.md §1), which the F2P test reads back. |
| A3 | the contrast operation the result must NOT equal — `casefold(ToSeq(termtext))` (the deep `@Pure` ASCII fold) | the **removed** `.lower()` call (`termtext.lower()`) | A-reference | the changed operation is the *removal* of a case fold. The fold is modelled **deeply** (`casefold`/`fold_cp` in the `pure` region); there is no consumed axiom. G-AX validates `casefold == ASCII str.lower()` and that the identity result differs from `casefold` exactly on upper-case input — so the verbatim postcondition genuinely senses the removed `.lower()`. The pre-patch skeleton (`model_prepatch.py`) computes `casefold` and FAILS the postcondition. |

The discriminating content of the change — the key keeps the author's original
case (`TERM2`, not `term2`) — lives in the postcondition
`ToSeq(Result()) == ToSeq(termtext)` (model) ⇔ dropping `.lower()` (real). The
pre-patch lower-cased the key; `model_prepatch.py` reproduces that (the backward
loop emitting `c+32` for ASCII 'A'..'Z') and **fails** the postcondition
`ToSeq(Result()) == ToSeq(termtext)` on any upper-case input, which is exactly
the spec sensing the change (G-DIFF).

## B. The lookup-consistency site — `XRefRole(lowercase=True)` → `XRefRole()`

Gold hunk 2 (`sphinx/domains/std.py:568`):
```
- 'term':    XRefRole(lowercase=True, innernodeclass=nodes.inline,
+ 'term':    XRefRole(innernodeclass=nodes.inline,
                      warn_dangling=True),
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (none — the read side of the same case-preservation property) | dropping `lowercase=True` from the `'term'` role | R/consistency | `lowercase=True` lower-cases a `:term:` reference's lookup *target* (`sphinx/roles.py:146-147`). Once keys are stored with original case (hunk A), references must look them up with original case; this hunk is the read-side counterpart of the same single behaviour "term keys are case-preserving". |

Why no separate failing `model_prepatch_<k>` for site B: the F2P test
`test_glossary` exercises only the **write** path (registration → `objects` →
`get_objects` and the index entry); it contains no `:term:` cross-reference, so
hunk 2 has no independently-observable behaviour in the F2P/P2P set. It is the
consistent read-side of the *same* case-preservation property that hunk A
implements; there is no second independently-fixed behaviour to give a distinct
differential witness. Site A's prepatch already exercises the case fold that
both hunks remove. (mapping.md §3.2.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The operation that genuinely changed —
the *removal* of the term-text case fold — is modelled **deeply** (the identity
copy in `register_term_name` plus the spelled-out `casefold` fold it is
differentiated against, an **A-reference**), not hidden behind an axiom about
the function under change. There is no consumed axiom: `casefold` is validated
== the real `str.lower()` (ASCII domain) by G-AX, and the registration's
verbatim postcondition is discharged by the deep identity copy, grounded
element-wise in the actual input carrier (`termtext`) — not by any oracle.

## D. verify(model) ⇒ resolved

`register_term_name` verifies only if its output equals the term text verbatim,
character for character (A2) — i.e. only if it applies **no** case fold. By R
(`str` ↔ `List[int]`, `term.astext()` rendering, `note_object`/`get_objects`
storing and re-emitting the key unchanged) the verified key equals the
`termtext` argument the post-patch code passes to `note_object` on the tested
inputs; by G-AX the deep model `casefold` equals the real `str.lower()`
(A-reference) on the ASCII term-text domain, so the verbatim postcondition's
divergence from `casefold` faithfully captures the removed `.lower()`. The
read-side hunk B is the consistent counterpart of the same property (R). Hence a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the one audited A-reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
