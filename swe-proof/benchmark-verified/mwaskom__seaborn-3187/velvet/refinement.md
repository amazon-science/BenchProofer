# refinement.md — mwaskom__seaborn-3187

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `legendLabels` and `legendEntries` `do` blocks) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (the proof uses the axiom's `ensures`), **A-reference** (a deep
model validated == the real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs would be mechanically refuted by **G-CONF** — but this bundle's impl
region is **all-A-tagged** (the observable is the renderer callee's output
verbatim), so `conf_skip=true` and the A legs + narrative are audited by **G-AX**
and **G-EQ**. Claim: any impl verifying against this frozen spec, refined per the
map below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). All measurements quoted
are from the instance's own container (matplotlib 3.7.2).

## A. Site A — the `objects` legend (`seaborn/_core/scales.py:377-382`)

Gold hunk:
```
             locs = axis.major.locator()
             locs = locs[(vmin <= locs) & (locs <= vmax)]
+            if hasattr(axis.major.formatter, "set_useOffset"):
+                axis.major.formatter.set_useOffset(False)
+            if hasattr(axis.major.formatter, "set_scientific"):
+                axis.major.formatter.set_scientific(False)
             labels = axis.major.formatter.format_ticks(locs)
             new._legend = list(locs), list(labels)
```

| # | Solution.lean impl op (`legendLabels`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `ticks : List Float` (no restriction on the carrier) | the clipped `locs` array fed to the formatter (IEEE-754 doubles) | R | tick list ↔ `List Float`, identity on doubles, non-finite values included (mapping.md §2). The model constrains no arithmetic on ticks — only which list is handed to the renderer — so the CARRIER needs no restriction. The renderer's DOMAIN is restricted, and explicitly (A1e). An earlier revision used `List Int` bounded by `2^53`; G-EQ refuted it with a materialized rival that verified and did not resolve, because the F2P legend of `tests/test_relational.py::TestRelationalPlotter::test_legend_has_no_offset` draws non-integral levels. |
| A1b | binder `modesAvailable : Bool`, dispatched on by the impl's `if` | the two `hasattr(axis.major.formatter, ...)` guards at scales.py:381-384 | R | site A does not construct its formatter; `Continuous._get_formatter` (scales.py:622-658) installs one of FIVE kinds and only `ScalarFormatter` carries the setters, so both guards are true together or false together (measured exhaustively over all 16 `Formatter` subclasses in `matplotlib.ticker` + `matplotlib.dates`: 1 has both, 15 have neither, 0 have one — mapping.md §3.3). `true` ↔ both setters present; `false` ↔ the site is a no-op. Both outcomes are modeled; neither is assumed away (mapping.md §1.2). |
| A1c | binder `cfg : RendererConfig` | `axis.major.formatter` as installed — the formatter object with its own presentation settings, attached to the axis at its view interval | R | opaque handle (mapping.md §2). Because `cfg` carries the renderer's OWN settings, the modes-available clause is a statement about the very renderer installed, not about a generic plain `ScalarFormatter`: measured at the real patched site, a `ScalarFormatter(useMathText=True)` install yields legend labels `['$\mathdefault{100000000}$', …]` and `renderTicks cfg false false ticks` is byte-identical to them (mapping.md §1.2(i)). |
| A1d | binder `ownLabels : List String` under `require ownLabels.length = ticks.length` | `axis.major.formatter.format_ticks(locs)` for the installed formatter, unconfigured | R | the labels the installed formatter yields on its own; the `require` is `Formatter.format_ticks`'s own one-label-per-tick guarantee (measured on the 9 instantiated non-`ScalarFormatter` renderers, 0 violations). |
| A1e | `require modesAvailable = true → renders cfg false false ticks` | the *scope* of this row's correspondence: those `(installation, locs)` at which `format_ticks(locs)` on the configured renderer returns labels rather than raising | R | the renderer is PARTIAL, so a model that claimed a label list for every argument would be a model of a different function. `renders` is exactly "this installation with these switches returns for this tick list", made operational (return vs. raise) and measured in `axiom_check.py`; it is on the `modesAvailable = true` arm only, because the other arm calls this renderer at all. It excludes nothing the site can reach — all 1173 ordinary configuration/tick/switch observations and all 793 `(installation, tick list)` pairs the two sites produce are inside it, 0 exclusions — and where it fails, the raise propagates out of THIS site (`Continuous(norm=(-max, max)).tick(at=[0.0])._setup(…)` → `OverflowError`, measured at `base_commit`), so no legend exists there for A4/A5 to describe. Not idle: at interval `(-9e307, 9e307)` with ticks `[0.0]` and both switches off the renderer returns nothing, where `(-8e307, 8e307)` returns `['0']` (mapping.md §3.4). |
| A2 | `offsetMode := false` (on the `modesAvailable` arm) | `set_useOffset(False)` (under its `hasattr` guard) | I | disabling the additive shared-term mode. The guard is modeled by A1b rather than assumed away, so this leg stands only where the setter really exists. |
| A3 | `scaleMode := false` (on the `modesAvailable` arm) | `set_scientific(False)` (under its `hasattr` guard) | I | disabling the multiplicative `10^k` shared-term mode; same guard reasoning. |
| A3b | `else` arm: `return ownLabels` | both guards false ⇒ neither setter is called ⇒ `format_ticks(locs)` on the untouched formatter | I | the patched and pre-patch sites are byte-identical here (measured on all 9 instantiated non-`ScalarFormatter` renderers, driven through the site's own guarded sequence), which is what the `modesAvailable = false → labels = ownLabels` clause pins. |
| A4 | `labels :| labels = renderTicks cfg offsetMode scaleMode ticks` | `labels = axis.major.formatter.format_ticks(locs)` | A-consumed | the rendering is the unchanged matplotlib callee (mapping.md §3.1). The proof consumes `renderTicks_length` for the count clause and `sharedTerm_none` for the shared-term clause — the latter fires only at `false false`, which is what A2/A3 establish. The spec pins the call itself as well (`∃ offsetMode scaleMode, labels = renderTicks cfg offsetMode scaleMode ticks`): the site renders EXACTLY the clipped `locs` it holds, with the renderer it holds, and passes the result straight through, so an impl may not render a different tick list, use another renderer handle, nor post-process what comes back. That conjunct is load-bearing, not decoration — a rival rendering `locs` PADDED with a distant extra position and returning the prefix keeps both switches off (so it hoists nothing and both F2P tests still pass) yet changes the labels ordinary data prints; measured, `[0.20,…,0.28]` renders as `['0.20',…,'0.28']` alone and as `['0','0','0','0','0']` padded with `2^53`, and the materialized patch for that shape was measured to FAIL (both F2P pass, `tests/test_relational.py::TestLinePlotter::test_legend_data` regresses). |
| A5 | `ensures … sharedTerm cfg offsetMode scaleMode ticks = ""` (the second conjunct, on the same arm) | the *purpose* of the two `set_*(False)` calls: no offset / scientific term is hoisted out of the legend's labels | A-consumed | `sharedTerm` is `Formatter.get_offset()` — the term matplotlib draws separately from the labels, which a legend has nowhere to draw (mapping.md §3.1). Measured `""` for all 16 renderer configurations × 18 boundary tick lists with both switches off (every one of which is in the domain — A1e), and non-empty on 96 hoisting combinations, 32 of them with BOTH switches on and in the domain there, which is what `sharedTerm_hoists` states. This is the clause that discriminates the patch, and it is stated on the separately-reported term rather than on any label's numeric read-back because read-back is FALSE of the real site for marked-up renderers (measured: 6 of the 48 configuration/tick combinations G-AX drives print labels no numeric parse accepts, while still hoisting nothing) — mapping.md §1.2(ii). |
| A6 | result `labels` returned | `new._legend = list(locs), list(labels)` | R | the labels become the legend text; the F2P tests read each drawn label and reject abbreviations. `list(locs)` (the levels) is unchanged by the patch and orthogonal to the observed labels. |

Discriminating content: with both switches off, `sharedTerm_none` gives
`sharedTerm cfg offsetMode scaleMode ticks = ""` — nothing is hoisted out of any
label, which is what the F2P assertions detect. The pre-patch left both modes at
their default (enabled); `Solution_prepatch.lean`'s `legendLabels` renders with
`renderTicks cfg true true ticks` and **fails** the shared-term `ensures`
(G-DIFF), because no axiom lets a `true true` rendering be reproduced by a
setting that hoists nothing. It fails the count clause as well, and for a second
reason worth stating: the arm is handed the renderer's domain at `false false`
only (A1e), so a rendering at `true true` is a call this model does not describe
and its label count is not derivable either.

## B. Site B — the classic legend (`seaborn/utils.py:687-710`)

Gold hunk:
```
     if isinstance(locator, mpl.ticker.LogLocator):
         formatter = mpl.ticker.LogFormatter()
     else:
         formatter = mpl.ticker.ScalarFormatter()
+        formatter.set_useOffset(False)
+        formatter.set_scientific(False)
     formatter.axis = dummy_axis()
```

| # | Solution.lean impl op (`legendEntries`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `isLog : Bool` | `isinstance(locator, mpl.ticker.LogLocator)` | R | the branch selector; `True` ↔ the `LogLocator` case (mapping.md §1). Read-only (not `mut`). |
| B1b | parameter `ticks : List Float`, `cfg : RendererConfig` | `raw_levels`, and the renderer this arm constructs over `dummy_axis()` | R | as A1/A1c. Site B's `cfg` is the installation both arms share: the freshly constructed formatter with its default presentation settings, attached to the local `dummy_axis()` whose `get_view_interval()` returns the `limits` argument — the span of the DATA the legend describes, not of the tick list. Which renderer KIND is constructed on that installation is the branch, which is why one handle feeds two callees (`renderTicks`, `renderLog`). |
| B2 | `then` branch: `labels :| labels = renderLog cfg ticks` | `formatter = mpl.ticker.LogFormatter()` … `formatter.axis = dummy_axis()` … `set_locs(raw_levels)` … `[formatter(x) for x in raw_levels]` | A-consumed | the log renderer is unchanged by the gold hunk (no setters added — `LogFormatter` lacks them, mapping.md §3.2/§3.3). Modeled by `renderLog`; the clause `isLog = true → labels = renderLog cfg ticks` pins the log path's observable to be exactly this callee's output on this installation, and the proof consumes `renderLog_length` for the length clause. The handle is load-bearing here and not decoration: `LogFormatter.__call__` reads `self.axis.get_view_interval()` and abbreviates to a power-of-ten form once `vmax - vmin` exceeds `1e5`, so the same ticks print different labels on different installs (measured: `[1, 100, 10000]` → `['1','100','10000']` at limits `(1, 1e5)` and `['1','100','1e4']` at `(1, 1.5e5)`; 6 of the 75 tick lists the site produces on a 1206-point limit grid are ambiguous this way). An earlier revision of this spec wrote this clause as `labels = renderLog ticks`; that is a claim about a function of the ticks alone, which this callee is not — the gold code returns `['1','100','1e4']` on the second install while the clause demanded one fixed list for both — and G-PANEL-2 refuted it as unfaithful. `renderLog(cfg, ticks)` now reproduces the real site's log labels on all 1173 (interval, tick list) pairs of that grid, 0 disagreements, where the ticks-only model disagrees on 63 (mapping.md §3.2). |
| B1c | `require isLog = true → rendersLog cfg ticks` and `require isLog = false → renders cfg false false ticks` | the scope of B2 and of B5 respectively: those `(installation, raw_levels)` at which the renderer THAT arm constructs returns labels rather than raising | R | as A1e, one per arm because the two renderers are two different partial functions with two genuinely different domains — measured, at interval `(-max, max)` the log renderer returns `['1','100','1e4']` for `[1,100,10000]` where a `ScalarFormatter` with both switches off returns nothing (mapping.md §3.4). Each arm is handed only the domain of the renderer it calls, at the setting it uses, so neither `require` licenses the other arm's call. Where either fails the raise propagates out of THIS site too (`locator_to_legend_entries(FixedLocator([0.0]), (-max, max), float)` → `OverflowError`, measured at `base_commit`), so there is no legend to describe; and neither excludes any `(limits, raw_levels)` pair the site produces on its own grid. |
| B3 | `else` branch: `offsetMode := false` | `formatter.set_useOffset(False)` | I | as A2, and no `hasattr` guard is needed here (nor modeled): this arm CONSTRUCTS a fresh `ScalarFormatter`, which always carries both setters. Site B is genuinely two-way (`LogFormatter` vs fresh `ScalarFormatter`) where site A is five-way, which is why only `legendLabels` carries a `modesAvailable` binder. |
| B4 | `else` branch: `scaleMode := false` | `formatter.set_scientific(False)` | I | as A3. |
| B5 | `else` branch: `labels :| labels = renderTicks cfg offsetMode scaleMode ticks` | `[formatter(x) for x in raw_levels]` with the `ScalarFormatter` | A-consumed | same callee/axioms as A4/A5; consumes `renderTicks_length` + `sharedTerm_none`, and is likewise pinned as a CALL on exactly `raw_levels` with exactly this renderer handle by the linear path's `∃ offsetMode scaleMode, labels = renderTicks cfg offsetMode scaleMode ticks ∧ sharedTerm … = ""`. Site B calls `set_locs(raw_levels)` then `[formatter(x) for x in raw_levels]` rather than `format_ticks`, but `Formatter.format_ticks` IS `set_locs(values)` followed by `[self(value, i) for i, value in enumerate(values)]` (matplotlib 3.7.2 source) and `ScalarFormatter.__call__` ignores the index argument, so the two are the same call sequence. Measured through the real site rather than only read off the source: a replica built the way this arm builds its formatter reproduces `locator_to_legend_entries`'s own labels on 173 installs across the limit grid with the switches untouched, and `renderTicks cfg om sm ticks` equals that same `set_locs`-then-call sequence driven after setting them on 692 configuration/switch combinations, 0 disagreements (G-AX). Both sites' linear arms therefore legitimately share `renderTicks`. |

Discriminating content: the linear branch's shared-term clause holds only with
both switches off. The prepatch's `legendEntries` else-branch renders with
`renderTicks cfg true true` and **fails** that clause (G-DIFF). The log branch is
pinned to the log renderer's own labels for the installation it was given
(`isLog = true → labels = renderLog cfg ticks`), matching the gold code exactly
(it touches nothing on the `LogFormatter` path, so the legend shows that
renderer's output unchanged); an impl that substituted a different renderer on
the log path, or handed it a different tick list, fails this clause
(`weak-alt-path-substitutes-renderer`, `weak-alt-path-permutes-argument`,
`weak-selector-ignored`).

This is an **independently-fixed behavior** from site A (a different function,
different F2P test — `tests/test_relational.py::...::test_legend_has_no_offset`);
`Solution_prepatch.lean` injects the bug at BOTH sites and fails, so a single
prepatch witnesses both (G-DIFF requires ≥1 failing prepatch per
independently-observable fixed behavior; both clauses are present and both fail).

## C. No kind-3 (inexpressible-changed-op) steps; G-CONF skipped

Every step is R, A, or I. The operation the patch *changes* is the formatter's
**configuration** (turning the two shared-term modes off), modeled concretely by
the impl-local constants `offsetMode = scaleMode = false` (steps A2/A3, B3/B4 —
all **I**); it is NOT hidden behind an axiom about the function under change. The
*rendering itself* is an UNCHANGED matplotlib callee, correctly an **A-consumed**
axiom (`renderTicks`/`sharedTerm`/`renderLog`), never axiomatizing the function
under spec.

Because the computed observable (`labels`) is the A-tagged callee's output
verbatim and the impl's only R/I content is the configuration constants + the
`modesAvailable` and `isLog` branches (no input-dependent transformation of label
contents), `meta.json conf_skip=true` and `conformance_check.py` is a
`status=skip` stub (SPEC_GUIDE §4). The discriminating fact — both switches off ⇒
nothing hoisted, a switch on ⇒ something can be — is a property of the real
renderer, validated by **G-AX**, not a transliterable R/I shadow.

## D. verify(Solution) ⇒ resolved

`legendLabels` / `legendEntries` verify only if, on the arm where the renderer's
two switches exist, the labels are that renderer's own output for exactly the
site's tick list under a setting that hoists NOTHING out of them
(`∃ offsetMode scaleMode, labels = renderTicks cfg offsetMode scaleMode ticks ∧
sharedTerm cfg offsetMode scaleMode ticks = ""`). The only axiom supplying an
empty shared term is `sharedTerm_none`, which holds at `false false` — i.e. only
where both modes are disabled, exactly the gold edit (A2/A3, B3/B4). On the other
arms the spec pins the untouched behaviour instead: `modesAvailable = false →
labels = ownLabels` (site A's no-op arm) and `isLog = true → labels = renderLog
cfg ticks` (site B's log arm), so the ONLY verifying behaviour there is the code
the gold patch leaves in place. Both of those pinning clauses name the
INSTALLATION as well as the ticks, because neither untouched renderer's text is a
function of the ticks alone (mapping.md §1.2 for site A's, §3.2 for the log one) —
a pin that dropped it would be over-strong on the real code rather than
protective.

The obligations are stated on the renderers' modeled DOMAIN (A1e, B1c), so the
implication "verify ⇒ resolved" needs that domain to cover what the tests run.
It does, measured: every `(installation, tick list, switch setting)` the two sites
produce on their own grids is inside it (1173 ordinary observations and 793 site
pairs, 0 exclusions), the F2P and P2P levels among them; and outside it the sites
produce no legend at all rather than a differently-labelled one, so there is no
input on which a verifying impl could be silently unlike the gold code
(mapping.md §3.4).

By R (tick ↔ `Float` identically, label ↔ `String`, `cfg` ↔ the installed
formatter, `sharedTerm` ↔ `Formatter.get_offset()`), the verified labels equal the
gold patch's `format_ticks(locs)` output with `get_offset() == ""`. That is what
the F2P tests assert: they build `1e8`-offset data and reject any label that is
not the tick's own value, and matplotlib produces such a label exactly when it
has hoisted the shared `1e8` (or the shared `10^8` factor) out into the
separately-drawn term — measured, both switches on gives labels `['0','20','40',
'60','80']` with `get_offset() == '+1e8'`, and both switches off gives
`['100000000',…,'100000080']` with `get_offset() == ''`. G-AX establishes the
axioms of the real callees over 16 renderer configurations × 18 boundary tick
lists × 4 switch settings plus 6000 fuzzed lists, and over a second grid and fuzz
straddling the domain boundary — 34 824 in-domain observations, 0 violations —
witnesses the hoisting case 96 times so the clause is not idle, checks that the
modeled domain is deterministic, inhabited, not idle and covers both sites, and
fails on its negative controls. The obligation is also faithful where a read-back one would not be:
6 of the 48 configuration/tick combinations print marked-up labels no numeric
parse accepts while hoisting nothing, and the shared-term clause is true of them
(measured end-to-end at the real patched site for a `useMathText` install —
mapping.md §1.2).

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). Trust points are exactly axiom soundness (G-AX) and refinement
fidelity (this doc, G-EQ); there is no R/I shadow (conf_skip).
