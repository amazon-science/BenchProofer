# refinement.md — mwaskom__seaborn-3187

The operation-by-operation correspondence between `model.py`'s implementation
(the two modeled legend builders and the two deep models `rendered_labels` /
`reading`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses the deep model's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The gold patch touches two independent legend-building sites; both make the
same change — leave the numeric tick formatter the legend renders through in the
mode where it factors no common magnitude out of the labels, and record that
formatter's own label text. The model has one contracted function per site,
giving two independent differential witnesses (`model_prepatch.py`,
`model_prepatch_2.py`).

## A. Site 1 — objects-interface continuous legend (`seaborn/_core/scales.py:377-390`)

Gold hunk (post-patch line numbers in the worktree):
```
 377         if prop.legend:
 378             axis.set_view_interval(vmin, vmax)
 379             locs = axis.major.locator()
 380             locs = locs[(vmin <= locs) & (locs <= vmax)]
 381             labels = axis.major.formatter.format_ticks(locs)   (pre-patch position)
+385             if hasattr(axis.major.formatter, "set_useOffset"):
+386                 axis.major.formatter.set_useOffset(False)
+387             if hasattr(axis.major.formatter, "set_scientific"):
+388                 axis.major.formatter.set_scientific(False)
 389             labels = axis.major.formatter.format_ticks(locs)
 390             new._legend = list(locs), list(labels)
```

| # | model.py impl op (`legend_values_continuous`, lines 236-262) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `locs: List[int]` | `locs`, the clipped tick locations — `scales.py:379-380` (numpy float array) | R | float-array ↔ `List[int]` tick values (mapping.md §2); the exercised locations are integral and the modeled property is exact at them. |
| A2 | `conv0 = fmt.convention`, `lo0 = fmt.view_lo`, `hi0 = fmt.view_hi` (lines 288-290) | nothing — the patch touches neither which formatter object the axis has (`_get_formatter`, `scales.py:623-660`, runs earlier, at `Continuous._setup` time) nor the axis's view interval (`scales.py:378` sets it from the data limits, above the hunk) | I | read-only snapshots of the rendering convention and of the axis range; they exist so the proof can carry "the convention and the range are what they were" across the rendering loop. Their counterpart in the patch is the *absence* of any write to `axis.major.formatter` and of any second `set_view_interval`. |
| A3 | `fmt.residual = False` (line 237) | `scales.py:385-388` — `set_useOffset(False)` and `set_scientific(False)` on `axis.major.formatter`, each guarded by `hasattr` | R + A-reference | one model boolean for the whole family of controls by which a formatter may factor a common magnitude out (§C.2). The `hasattr` guards are no-ops for the `ScalarFormatter` a numeric continuous scale installs (`scales.py:658`) — it has both setters — so on the default convention this reduces to exactly the modeled state change; on a formatter with no such control (`StrMethodFormatter`, `FuncFormatter`) the guards skip and the object is *already* in the modeled `False` state, measured byte-identically in that state (axiom_check.py `check_convention_guard`). |
| A4 | the loop (lines 294-318): `lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi)[i]`, appended in order | `labels = axis.major.formatter.format_ticks(locs)` — `scales.py:389` — then `list(labels)` | A-reference | the rendering is modeled **deeply** by `rendered_labels`, which takes the whole tick set AND the axis range and returns the whole label sequence, because that is how `format_ticks` behaves: it renders through `self.axis`, and on that path `get_view_interval()` is the only thing it reads from it — the very interval `scales.py:378` has just set (mapping.md §3.1; measured set-dependence and range-dependence). The loop reads that sequence in index order, so it emits exactly `format_ticks(locs)`. Crucially the label values are *only* obtainable from this deep model — the impl cannot compute a label for itself. |
| A5 | `Ensures(ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi))` (lines 272-274) with `Ensures(not fmt.residual)` (265), `Ensures(fmt.convention == Old(fmt.convention))` (255) and `Ensures(fmt.view_lo == Old(fmt.view_lo))` / `view_hi` (259-260) | the labels recorded are those the *already-installed* formatter, in the mode the patch leaves it in, renders for *this* tick set | A-consumed (length) + A-reference | this is the clause that says the legend reports the formatter's own text for the right ticks in the right order. `rendered_labels`'s `len` `Ensures` is what discharges `len(Result()) == len(locs)`. Justification for the argument list: the convention is the object's (`scales.py:389` renders through `axis.major.formatter`, not a new formatter), the tick set is `locs` (the same array `scales.py:390` records), the mode is the post-`:385-388` mode, and the range is the one on the axis the formatter is attached to (`:378`) — *not* the span of `locs`, which after the `:380` clip is in general narrower. |
| A6 | `Ensures(Implies(fmt.convention == 0, legend_reads_ticks(...)))` (280-281) and the pointwise form (282-285) | once the residual controls are off, a `ScalarFormatter`'s labels render each tick at full value, so `float(label) == tick` | A-consumed + A-reference | the second `Ensures` of `rendered_labels` (`convention == 0 and not residual ==> reading(...[k]) == ticks[k]`), consumed at `residual == False`. It is unconditional in the range — measured over ranges drawn independently of the ticks, including ranges that do not contain them (axiom_check.py), so no side condition on the range was needed to state it. This is what the F2P test observes: `float(text.get_text()) > 1e7` for `1e8`-scale data. The guard is stated for the full-value convention only, and mapping.md §4 measures that this withholds nothing (for the other conventions the controls are inert and the labels are unreadable regardless). |
| A7 | `Result()` | `new._legend = list(locs), list(labels)` — `scales.py:390` | R | the locations half is the identity on the input (asserted separately by conformance_check.py); `Result()` models the labels half, the part the change is about (mapping.md §2). |

## B. Site 2 — classic relational legend (`seaborn/utils.py:687-714`)

Gold hunk:
```
 692     raw_levels = raw_levels[(raw_levels >= limits[0]) & (raw_levels <= limits[1])]
 694     class dummy_axis:  …
 698     if isinstance(locator, mpl.ticker.LogLocator):
 699         formatter = mpl.ticker.LogFormatter()
 700     else:
 701         formatter = mpl.ticker.ScalarFormatter()
+704         formatter.set_useOffset(False)
+705         formatter.set_scientific(False)
 706     formatter.axis = dummy_axis()
 711     formatter.set_locs(raw_levels)
 712     formatted_levels = [formatter(x) for x in raw_levels]
 714     return raw_levels, formatted_levels
```

| # | model.py impl op (`legend_values_locator`, lines 302-328) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `locs: List[int]` | `raw_levels`, clipped to `limits` — `utils.py:692` | R | the same float-array ↔ `List[int]` refinement as A1. |
| B2 | `conv0 = fmt.convention`, `lo0 = fmt.view_lo`, `hi0 = fmt.view_hi` (lines 366-368) | `utils.py:698-701` — which formatter the site builds is decided by the locator, before and independently of the patch, and never rewritten afterwards; and `utils.py:694-696`, where the axis range this site renders against is the `limits` argument, closed over by the stub axis and never reassigned | I | as A2. This site's axis stub defines `get_view_interval` and *nothing else*, which is the sharpest available statement that the range is the whole of the formatter's environment on the rendering path. |
| B3 | `fmt.residual = False` (line 303) | `utils.py:704-705` — `formatter.set_useOffset(False); formatter.set_scientific(False)` | R + A-reference | as A3, with no `hasattr` guard needed (the object is a freshly-built `ScalarFormatter`, `:701`). The `LogFormatter` branch (`:698-699`) is **in scope** as a non-default convention: it has neither control, so it is already and permanently in the modeled `False` state, and the model claims one-label-per-tick of it but no reading guarantee — both measured (axiom_check.py, kind `log`). |
| B4 | the loop (lines 372-396) | `formatter.set_locs(raw_levels)` then `[formatter(x) for x in raw_levels]` — `utils.py:711-712` | A-reference | the same deep model as A4, through the *other* API: `set_locs` announces the whole tick set and each `formatter(x)` renders one tick in the way chosen for that set. G-AX validates `rendered_labels` against both APIs (`via="format_ticks"` and `via="set_locs"`) and conformance_check.py diffs the model against this site on 100 030 inputs. |
| B5 | postconditions (lines 338-363) | the formatted levels are the formatter's own text for these levels, in order, against the `limits` interval of `:694-696`, and read back to full values on the default convention | A-consumed + A-reference | identical reasoning to A5/A6; the F2P `tests/test_relational.py::TestLinePlotter::test_legend_has_no_offset` checks `float(text.get_text()) > 1e7`, and the P2P `…::test_legend_data` checks the exact texts `['0.20','0.22','0.24','0.26','0.28']` (`tests/test_relational.py:866,877`) — a fact about the *text*, which only the A5-style clause can express (§C.1). |
| B6 | `Result()` | `return raw_levels, formatted_levels` — `utils.py:714` | R | the levels half is the identity; `Result()` models the formatted-levels half. |

## C. No kind-3 (unexpressible-changed-op) steps; the carrier choices

Every step above is R, A-consumed, A-reference, or I. The operation that
genuinely *changed* — leaving the formatter in the mode where it factors nothing
out — is A3/B3, a concrete state change on the modeled formatter object, not
something hidden behind an axiom. The rendering itself is *not* changed by the
patch, and it is modeled as an **A-reference** deep model (`rendered_labels`,
validated == the real matplotlib formatter through both of the APIs the two
sites use); the proofs consume only its two `Ensures`, which is the weakest
sufficient contract (mapping.md §3.1).

### C.1 A label is its TEXT, not its reading

The model's label carrier is an opaque `int` code standing for a label's exact
text, and the ONLY thing the model may learn about it is `reading(label)` — an
uninterpreted function. This is load-bearing, not cosmetic:

* the repo's own legend assertions are on the text (`tests/test_relational.py:866,877`
  expects `'0.20'`, which is `float`-equal to `'0.2'` but not text-equal);
* the same tick renders to different texts in different tick sets — `0.2` renders
  `'0.20'` in `{0.20…0.28}` and `'0.2'` alone (axiom_check.py
  `check_text_not_reading`, `check_set_dependence`);
* therefore a model whose observable was the *parsed number* could not
  distinguish a label the formatter rendered from a number written into the
  legend by a private route, and half the guarantee — "the legend reports the
  formatter's own text" — would be unstatable.

Because labels are opaque, the ONLY way an implementation can produce one is to
call `rendered_labels` with the formatter's own convention, the actual tick set,
and the mode it is being left in. That is what makes the sequence-equality clause
(A5) enforce all of: no private route, no per-tick rendering, no other tick set,
no reordering, no dropping.

### C.2 One model boolean for a family of controls

`fmt.residual` abstracts "may this formatter still factor a magnitude common to
the ticks out of them", which the patch realises with two separate controls on a
`ScalarFormatter` (`set_useOffset` and `set_scientific`) and with *nothing* on a
formatter that has no such control. The abstraction is a genuine refinement, not
an under-count: `residual == False` corresponds to "no such control is enabled",
`True` to "at least one is", and conformance_check.py reads the concrete state
back as `get_useOffset() or _scientific` on the real object the patched site
configured (`residual_state`), checking the model's `not fmt.residual`
postcondition against it 5 247 times. Nothing in the spec view reveals how many
concrete controls that is.

### C.3 The `float → int` carrier

Sound here because the change is **not** about floating-point precision: it is
about which string the legend records. The F2P tests assert an
order-of-magnitude fact (`float(text) > 1e7`) and the P2P test an exact text; at
the integral tick values in play, `reading(label) == tick` mirrors
`float(label) == tick` with no rounding, and G-AX confirms exact equality on
integral ranges through `1e9`. Hence `--float-encoding` is not needed
(meta `float_encoding: null`).

### C.4 The one disclosed callee-domain restriction

A convention that chooses its unit from the WIDTH of the axis range
(matplotlib's `EngFormatter`, whose `set_locs` evaluates
`math.floor(math.log(vmax - vmin, 1000)) * 3`) may have no label sequence for a
range of no width — on mpl 3.10.9 it raises `ValueError: math domain error`. The
model does not narrow its input domain to hide this: `rendered_labels`'s docstring
discloses it, axiom_check.py `check_callee_domain` pins it two-sidedly (only a
width-reading convention may be restricted; every convention that renders renders
one label per tick; on a range of positive width every convention renders, an
empty tick set included), and conformance_check.py compares the model's
refinement and the real site by TOTAL outcome (value or exception type) rather
than skipping the input. The restriction is
version-dependent and therefore measured rather than asserted: in the instance's
own environment the measured set is empty and `raise_agreements` is 0 — no input
is skipped and no failure is silently excused either way.

### C.5 The axis range is an input, and it is pinned

The label sequence is a function of the tick set AND of the axis range the
formatter reads, so the model carries the range as two fields of the formatter
(`view_lo`, `view_hi`) and passes them to `rendered_labels`. Three consequences,
all of which strengthen the spec rather than relax it:

* the sequence clause (A5/B5) now says the labels are those the formatter renders
  *against the range it is attached to*. Rendering against any other interval —
  most temptingly the span of the tick set, which is what a collapsed
  range==ticks diagonal makes look right — is a different application of the
  callee and cannot discharge it (properties.py `interval-from-ticks`,
  `other-interval`);
* both bounds are pinned across the call (`Ensures(fmt.view_lo ==
  Old(fmt.view_lo))`, likewise `view_hi`), so an implementation cannot rewrite the
  range and then render honestly against the range it chose (properties.py
  `interval-rewrite`). The patch writes no view interval inside either hunk: at
  site 1 `:378` sets it above the change, at site 2 the stub axis closes over
  `limits` and never reassigns it;
* nothing in the reading guarantee is conditioned on the range. Measured over
  8 240 renders on ranges drawn independently of the ticks (including ranges that
  exclude them), the full-value convention with the residual controls disabled had
  zero reading violations, so the guarantee needed no new precondition.

The two fields are readable but not writable-in-effect (any write must be undone
by the return), which is why adding them cannot serve as an escape hatch for a
weaker implementation.

## D. verify(model) ⇒ resolved

Each `legend_values_*` verifies only if, at return, (i) the label sequence is
`rendered_labels(fmt.convention, ToSeq(locs), fmt.residual, fmt.view_lo,
fmt.view_hi)` — the formatter's own labels, for this tick set, against the range
of the axis it is attached to, in order (A5/B5); (ii) `fmt.residual` is `False`,
i.e. the formatter is left factoring nothing out (A3/B3), and the convention and
both range bounds are what they were on entry (A2/C.5); and (iii) on the
full-value convention every label reads back to its tick's full value
(A6). (iii) is derivable *only* from (i) + (ii) via the consumed `Ensures` of
`rendered_labels`, so an implementation cannot have one without the other: label
text that the formatter did not render is unobtainable (C.1), and a rendering
taken before the mode was settled is a different `rendered_labels` application.

By R (float-array ↔ `List[int]`; the locations/levels halves are identities) the
verified builders equal the gold-patched `new._legend = list(locs), list(labels)`
(`scales.py:390`) and `return raw_levels, formatted_levels` (`utils.py:714`) on
the tested inputs; by G-AX the deep model equals the real formatter through both
site APIs (A-reference); by G-CONF the model's own impl and the two live patched
sites agree on 105 300 inputs, compared as whole outcomes (C.4).

The pre-patch skeletons render in the mode the formatter arrived in. There
`fmt.residual` is not known to be `False`, so postcondition (ii) fails outright,
and (iii) is unprovable because the readings of `rendered_labels(0, ticks, True,
lo, hi)` are unconstrained — exactly the spec sensing the bug at each site (G-DIFF, two
witnesses). The 20 000/20 000 disagreeing pre-patch controls in
conformance_check.py show that this is a real behavioural difference and not an
artefact of the proof.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The trust points are the two of PLAN §1.1: axiom soundness (G-AX)
and refinement fidelity (this document, G-EQ).
