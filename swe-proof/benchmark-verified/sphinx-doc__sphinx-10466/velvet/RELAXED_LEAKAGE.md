# RELAXED_LEAKAGE — sphinx-doc__sphinx-10466 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

## The mismatch

The gold fix to `Catalog.__iter__` (`sphinx/builders/gettext.py:58`) replaces

```
positions = [(source, line) for source, line, uuid in self.metadata[message]]
```

with

```
positions = sorted(set((source, line) for source, line, uuid
                       in self.metadata[message]))
```

Two facets:

- **(a) Deduplication — fully public.** The problem_statement is titled
  "Message.locations duplicate unnecessary", states the expected behavior
  ("there are NO duplications of other locations"), and the reporter's own
  proposed fix is `self.locations = list(set(locations))`. Token scan of
  problem_statement: `duplicat` ×3, `set(` ×1. This facet does NOT leak.
- **(b) The ASCENDING SORT — gold/test_patch-only.** Token scan of
  problem_statement for `sort` / `sorted` / `order` / `ascend` / `descend`
  = 0 hits. The publicly proposed fix `list(set(...))` performs NO sort.
  The `sorted(...)` lives only in the gold diff and the hidden test_patch,
  whose F2P test (`test_Catalog_duplicated_message`) asserts the EXACT
  ascending list
  `[('/path/to/filename', 1), ('/path/to/filename', 2), ('/path/to/yetanother', 1)]`.
  hints_text mentions "sort" 8× but only in unrelated contexts (PO
  comment-line sorting `comment_list.sort()`, `dump_po(sort_output=...)`
  message-output ordering, a general `format_output` idea) — never the
  `positions` line in `Catalog.__iter__`; and hints_text is excluded from
  the leakage baseline anyway.

The leaking token is the spec view's `orderedPositions` model and docstring:
"The published positions of a message: the DISTINCT (source, line) pairs
among its entries, **listed in ascending order**. ... the sort puts the
survivors in a **canonical ascending order**", realized by
`def orderedPositions (entries) := ((entries.map toPos).dedup).mergeSort posLe`
with `posLe` "order by source first (code-point lexicographic), then by line
index".

## Why the leak is unavoidable

Faithfulness forces the sort facet into the spec:

- The F2P test pins a SPECIFIC ascending order of the deduplicated
  `(source, line)` pairs. A patch implementing only the publicly proposed
  `list(set(...))` is hash-order-dependent (set iteration order is not
  guaranteed across runs/versions) and does NOT resolve the F2P test.
- Hence any spec that is faithful to the post-gold behavior — one that
  rejects the prepatch bug AND rejects unstable non-sorting
  implementations (G-EQ attack `dedup-but-no-sort` must fail) — MUST pin
  the ascending order of the output.
- A spec derivable from problem_statement alone could pin only the
  deduplication, admitting every permutation of the survivors — which the
  G-EQ panel demonstrated is a spec-too-weak defect (the dedup-no-sort
  attack would verify). Faithful + non-leaking is provably impossible here.

This is the same faithful-must-leak shape as the dispositioned
sphinx-doc__sphinx-9673 instance (plural `:returns:` synonym): the
discriminator exists only in gold + hidden tests, and the spec cannot be
both faithful and silent about it.

## Core soundness is intact (per the recorded P2 audit)

- G-VERIFY: Solution.lean verifies (2.8 s), proof closes without sorry.
- G-DIFF: `Solution_prepatch.lean` (raw projection, no dedup/sort) fails
  for the right reason.
- G-EQ: SOUND / TIGHT — 7 spec-too-weak attacks (incl. dedup-no-sort,
  sort-no-dedup, descending, wrong-key) all rejected; positive control
  verifies.
- G-PANEL-2 (faithfulness): FAITHFUL — model matches real
  `sorted(set(...))` on 500k adversarial fuzz inputs, 0 divergences;
  `posLe` is a genuine total order matching Python default tuple compare
  including non-BMP.
- G-CONF: 0 / 100006 disagreements (seed 10466). G-AX: sound/vacuous
  (dedup + total-order-sort deep models validated against stdlib on
  6 boundary + 20000 fuzz lists). G-RESOLVE: resolved.

Only the secondary no-leakage property is relaxed, for this one documented
facet (the ascending sort of the published positions).
