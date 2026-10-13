# refinement.md — django__django-15127

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `refreshCachedTable` `do` block, plus the deep `recomputeTable` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (modeled callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The receiver — `update_level_tags(setting, **kwargs)` (`apps.py`, added)

Gold hunk:
```
+def update_level_tags(setting, **kwargs):
+    if setting == 'MESSAGE_TAGS':
+        base.LEVEL_TAGS = get_level_tags()
```

| # | Solution.lean impl op (`refreshCachedTable`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `cached : List (Int × String)` *(mut)* | the module global `base.LEVEL_TAGS` (read/written by the receiver) | R | `dict[int,str]` ↔ `List (Int × String)` as a key→value mapping (mapping.md §2). The cached table is the only mutated state. |
| A2 | param `changedKey : String` | the `setting` argument | R | `str` ↔ `String`, identity on content (mapping.md §2). |
| A3 | param `watchedKey : String`, compared `changedKey = watchedKey` | the literal guard `setting == 'MESSAGE_TAGS'` | R + I | the equality test is the identical concrete op; `watchedKey` abstracts the literal `'MESSAGE_TAGS'` (mapping.md §1) so the spec view names no patched symbol. The `if` control flow is **I**. |
| A4 | `cached := recomputeTable base overrides` (the `then` branch) | `base.LEVEL_TAGS = get_level_tags()` | A-reference + I | the recompute is modeled **deeply**: `recomputeTable`/`lookupEntry` (pure region) ARE the dict-merge `{**DEFAULT_TAGS, **MESSAGE_TAGS}` (overrides win). The assignment (`:=`) is **I**; the equality of the deep model to the real `get_level_tags()` is the **A-reference** G-AX validates (mapping.md §3.1). No consumed axiom. |
| A5 | `else cached` (the implicit `else`: `cached` unchanged) — pinned by `ensures changedKey ≠ watchedKey → cached = cachedOld` | the absence of an `else` branch in the receiver (`base.LEVEL_TAGS` untouched for any other setting) | I | **directive-5 mut-frame.** The `mut` param `cached` is conceptually unchanged on the non-matching branch, so the post-state is pinned exactly (`cached = cachedOld`). The real receiver mutates nothing when `setting != 'MESSAGE_TAGS'`; the frame clause is the Lean analogue. |

Discriminating content of the change — **the table is recomputed when (and the
frame is held unless) the watched key changes** — lives in the two `ensures`
clauses. The pre-patch repo had **no receiver at all** (and no
`setting_changed.connect`), so under `@override_settings(MESSAGE_TAGS=…)` the
cached `LEVEL_TAGS` kept its import-time value and `Message.level_tag` returned
the stale/empty tag. `Solution_prepatch.lean` reproduces that as the no-op
skeleton (`cached := cached`) and **fails** the first `ensures`
(`changedKey = watchedKey → cached = recomputeTable base overrides`) — G-DIFF.

## B. The registration — `MessagesConfig.ready` (`apps.py`, added)

Gold hunk:
```
+    def ready(self):
+        setting_changed.connect(update_level_tags)
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no impl node) | `setting_changed.connect(update_level_tags)` in `ready` | A-reference (plumbing) | pure registration on Django's unchanged `setting_changed` signal. It has no computation of its own; its only observable effect is that the receiver (modeled in §A) actually runs on each setting change. That premise is what makes §A's `ensures` observable, and it is exercised end-to-end by the F2P test under G-RESOLVE (if the receiver were never connected, the F2P assertion `base.LEVEL_TAGS == message_tags` would still fail). No consumed axiom; no separately modeled function. |

No separate failing prepatch for site B: connect/dispatch is unchanged
machinery, and a prepatch must keep the spec byte-identical (G-DIFF). The
behavior the registration enables is the recompute in §A, whose prepatch
(no-op) already fails on the discriminating clause.

## B2. Termination semantics (spec-strengthening, audit repair)

The bundle uses `loom.semantics.termination "total"` (`TotalCorrectness`), not
`"partial"`. A prior audit (G-EQ / G-PANEL-1) exhibited a same-spec
counterexample under partial correctness: a diverging implementation (a
non-terminating loop in place of the straight-line conditional) verified
vacuously, because partial correctness constrains only terminating executions —
and its translated patch hangs the test suite, so it does not resolve
(verify⇏correct). The real receiver `update_level_tags` is straight-line code
(one guard, one assignment) that always terminates, so total correctness is the
faithful semantics: it rejects every diverging impl (a loop without a
`decreasing` measure is unprovable under total semantics) while the verified
impl here is loop-free and unaffected. The `set_option`/`open` lines are part
of the frozen spec view shared byte-identical by both twins.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — adding a
conditional recompute of the cached table on the watched setting change — is
modeled **directly** (the `if`/assignment skeleton, A4/A5, both **I** up to the
A-reference recompute), not hidden behind an axiom about the function under
change: there is **no consumed axiom**. The only A legs are **A-references** —
the deep model `recomputeTable` of the unchanged callee `get_level_tags`
(G-AX-validated) and the unchanged signal-dispatch plumbing (G-RESOLVE-exercised).

## D. verify(Solution) ⇒ resolved

`refreshCachedTable` verifies only if (A4) it recomputes the table to the exact
default-overlaid-by-override merge when the watched key changes, AND (A5) it
leaves the table exactly unchanged otherwise (the mut-frame). By R
(`dict ↔ List (Int×String)` as a mapping, `str ↔ String` identities) the
verified handler equals the gold receiver `update_level_tags`; by G-AX the deep
model `recomputeTable` equals the real `get_level_tags()` (A-reference); by
G-CONF the R/I transliteration of the conditional + frame agrees with
`patch.diff`'s observable effect on `base.LEVEL_TAGS` over ≥10⁵ inputs; and by
G-RESOLVE the gold patch (receiver + registration) makes the F2P test pass.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves.
Trust points are exactly the two of plan §1.1: axiom soundness (G-AX, here the
A-reference deep model) and refinement fidelity (this doc, G-EQ + G-CONF).
