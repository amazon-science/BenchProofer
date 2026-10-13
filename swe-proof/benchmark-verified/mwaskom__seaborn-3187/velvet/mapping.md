# mapping.md — mwaskom__seaborn-3187

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 22cdfb0c93f8ec78492d87edb810f10cb7f57a31`, states the type
abstraction (the bijection G-AX uses to bridge Lean↔Python), and gives the
provenance of each axiom.

Repo files under change:
* `seaborn/_core/scales.py` — the legend branch of `ContinuousBase._setup` (the
  `objects` interface).
* `seaborn/utils.py` — `locator_to_legend_entries` (the classic / function-level
  interface, e.g. `relplot`/`scatterplot`).

Both sites build a *brief numeric legend*: a short list of tick positions is
turned into printed labels by a matplotlib tick **formatter**, and those labels
become the legend's text. The two F2P tests
(`tests/_core/test_plot.py::TestLegend::test_legend_has_no_offset`,
`tests/test_relational.py::TestRelationalPlotter::test_legend_has_no_offset`)
construct data offset by `1e8` and assert every legend label parses back to a
number `> 1e7` — i.e. no label may be an abbreviation from which a shared term
has been hoisted out, because a legend has nowhere to display that term.

All measurements quoted below were taken in the instance's own container
(`swebench/sweb.eval.x86_64.mwaskom_1776_seaborn-3187`), i.e. against
**matplotlib 3.7.2** — the version the oracle pins for seaborn 0.12 — and not
against a host matplotlib.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `legendLabels (modesAvailable, cfg, ownLabels, ticks)` | the legend branch of `ContinuousBase._setup` — `seaborn/_core/scales.py:377-382` (`if prop.legend: … labels = axis.major.formatter.format_ticks(locs)`) | modeled changed function, site A (objects interface) |
| `legendEntries (isLog, cfg, ticks)` | `locator_to_legend_entries(locator, limits, dtype)` — `seaborn/utils.py:687-710` | modeled changed function, site B (classic interface) |
| `RendererConfig` *(opaque type — A-consumed)* | the tick formatter **as installed**: the `Formatter` object itself, carrying its own presentation settings (`useMathText`, `usetex`, an explicitly supplied `useOffset` value, a format string, a unit, …) together with the axis view interval it is attached to | the renderer handle; nothing in the spec inspects it |
| `renderTicks cfg offsetMode scaleMode ticks` *(axiom — A-consumed)* | that installed formatter with its two shared-term display switches set to `offsetMode` / `scaleMode`, rendering the tick list (`format_ticks(locs)` at site A, `set_locs(raw_levels)` + `[formatter(x) for x in raw_levels]` at site B) | unchanged matplotlib callee that prints tick labels |
| `sharedTerm cfg offsetMode scaleMode ticks` *(axiom — A-consumed)* | `Formatter.get_offset()` for the same installed formatter and switch setting after `set_locs(ticks)` — matplotlib's *separately drawn* hoisted term (the axis's offset/scale text), which the legend has no place to draw | the term hoisted out of the labels; `""` iff nothing was hoisted |
| `renderLog cfg ticks` *(axiom — A-consumed)* | `matplotlib.ticker.LogFormatter` **as installed** (the `isinstance(locator, mpl.ticker.LogLocator)` branch of `locator_to_legend_entries`, `utils.py:698-699`, attached to `dummy_axis()` and driven by `set_locs(raw_levels)` + `[formatter(x) for x in raw_levels]`) | unchanged matplotlib callee for log-spaced ticks. It takes the SAME handle as `renderTicks`, and must: `LogFormatter.__call__` reads `self.axis.get_view_interval()` and abbreviates a label to a power-of-ten form once that interval is wide enough, so the label text is a function of (installation, ticks) and NOT of the ticks alone — measured, the ticks `[1, 100, 10000]` print `['1','100','10000']` on an install spanning `1 … 1e5` and `['1','100','1e4']` on one spanning `1 … 1.5e5` (§3.2) |
| `offsetMode` / `scaleMode` (impl-local Bool constants) | the formatter's two shared-term display modes, set by `set_useOffset(...)` / `set_scientific(...)` | `offsetMode ↔ useOffset`, `scaleMode ↔ scientific` |
| `modesAvailable : Bool` (site A binder) | whether the formatter installed by `Continuous._get_formatter` (scales.py:622-658) HAS the two setters, i.e. the truth value of `hasattr(axis.major.formatter, "set_useOffset")` / `..."set_scientific"` at scales.py:381-384 | `true` ↔ a formatter carrying both setters; `false` ↔ one carrying neither. MEASURED exhaustively over all 16 `Formatter` subclasses matplotlib exposes in `matplotlib.ticker` + `matplotlib.dates` (the two modules a seaborn scale draws its formatters from): `ScalarFormatter` has both, the other 15 have neither, none has one, so the two `hasattr` guards never disagree and ONE Bool is a faithful model of both rather than an approximation (§3.3). |
| `ownLabels : List String` (site A binder) | `axis.major.formatter.format_ticks(locs)` for the installed formatter in the configuration the site leaves it in when neither setter exists | the labels that formatter produces on its own. MEASURED: on each of the 9 instantiated non-`ScalarFormatter` renderers reachable at this site, driving the site's own guarded sequence leaves the output byte-identical to this — exactly what the `modesAvailable = false → labels = ownLabels` clause states. The `require ownLabels.length = ticks.length` is `Formatter.format_ticks`'s own one-label-per-tick guarantee (measured on the same 9, 0 violations). |

The pre-patch behavior the change removes (refinement audit only, not in the
consumer spec view): at both sites the formatter was used in its **default**
configuration, i.e. `useOffset` and `scientific` left enabled, so a
`ScalarFormatter` could hoist a common additive offset or a common `10^k` factor
out of the printed labels and report it separately, where the legend loses it.

### 1.1 Provenance of the observable (what `∃ offsetMode scaleMode, labels = renderTicks cfg …` binds)

Both methods pin their observable to be the renderer callee applied to EXACTLY
the tick list the site holds:

* site A, `modesAvailable = true` arm: `labels = axis.major.formatter.format_ticks(locs)`
  — one call, on the clipped `locs` the site already computed, with the result
  assigned straight to `labels` (scales.py:382, then
  `new._legend = list(locs), list(labels)`);
* site B, linear arm: `[formatter(x) for x in raw_levels]` after
  `formatter.set_locs(raw_levels)` — again exactly the site's own level list
  (utils.py:707-710).

Neither site renders a different list, and neither post-processes what comes
back. The Lean clause states that as `∃ (offsetMode scaleMode : Bool), labels =
renderTicks cfg offsetMode scaleMode ticks`: the two mode Bools are existential
because *which* switch setting was used is not itself visible in the legend text
(what is visible is that nothing was hoisted, which the conjoined `sharedTerm …
= ""` pins), whereas the *renderer handle*, the *tick list rendered* and the
*pass-through of the result* are.

**Why this clause is load-bearing, not decorative.** `ScalarFormatter` derives
its shared display decisions — the hoisted term, and the digit count
`_set_format` chooses — from the WHOLE list it is handed relative to its view
interval, so rendering a PADDED tick list and returning a prefix is a different
function from rendering the list itself. Measured with both switches off:

| ticks | rendered alone | padded with `2^53`, prefix kept | padded with `0.0`, prefix kept |
|---|---|---|---|
| `[0.20, 0.22, 0.24, 0.26, 0.28]` | `['0.20','0.22','0.24','0.26','0.28']` | `['0','0','0','0','0']` | byte-identical |
| `[1e8, 1e8+2, 1e8+4, 1e8+6]` | `['100000000','100000002','100000004','100000006']` | byte-identical | byte-identical |

The first row's middle column is the divergence the clause must exclude: the
padded rendering keeps both switches off, so it hoists nothing and the F2P
threshold assertions still pass, yet the legend text a regression test pins
(`tests/test_relational.py::TestLinePlotter::test_legend_data` expects
`['0.20','0.22','0.24','0.26','0.28']`) changes. A materialized rival of that
shape was measured: FAIL_TO_PASS 2/2 pass, that PASS_TO_PASS test regresses. The
other columns are the honest caveat — the divergence needs a sentinel far from
the levels, and integral levels of the F2P scale are insensitive to it — so the
provenance cannot be derived from any property of the label *text*; it has to be
stated as its own conjunct, and it is (the `properties.py` rivals
`weak-labels-pads-the-tick-argument` / `weak-entries-pads-the-tick-argument` are
rejected by exactly this conjunct).

### 1.2 The two branches site A really selects between

`if prop.legend:` (scales.py:377) opens the region this spec models; INSIDE it,
scales.py:381-384 is itself a conditional, and the model represents both of its
outcomes rather than assuming one:

```python
if hasattr(axis.major.formatter, "set_useOffset"):     # <- modesAvailable
    axis.major.formatter.set_useOffset(False)
if hasattr(axis.major.formatter, "set_scientific"):
    axis.major.formatter.set_scientific(False)
labels = axis.major.formatter.format_ticks(locs)
```

Site A does not construct its formatter. `Continuous._get_formatter`
(scales.py:622-658) installs one of FIVE kinds — a caller-supplied `Formatter`
(`formatter=`), a `StrMethodFormatter`/`FuncFormatter` (`like=`), a
`LogFormatterSciNotation` (`base=` / log or symlog trans), an `EngFormatter`
(`unit=`), or a plain `ScalarFormatter` — and a `Temporal` scale installs date
formatters. `modesAvailable` is the guard's own truth value, so:

* `modesAvailable = true` → the setters exist and are called, and the clause
  states what the site then computes: the installed renderer's own output for
  exactly these ticks, under a switch setting that hoists nothing;
* `modesAvailable = false` → neither setter exists, nothing is configured, and
  the clause pins the output to the renderer's unconfigured labels
  (`labels = ownLabels`).

Two consequences are worth stating explicitly, because the spec is only
faithful with them.

**(i) `cfg` carries the renderer's OWN presentation settings, so the true-branch
clause is true of renderers whose labels are not plain decimals.** A
`ScalarFormatter` constructed with `useMathText=True` (or under `usetex`) HAS
both setters, so it takes the `modesAvailable = true` branch, yet its labels are
marked-up rather than plain (`float(label)` raises on every one of them). Because
`renderTicks` is bound to *the formatter as installed* and not to a generic plain
`ScalarFormatter`, the clause is a statement about that very renderer. Measured
end-to-end at the real patched site (labels read straight out of
`scale._legend`; ticks `[1e8, 1e8+20, …, 1e8+80]`):

| installed `cfg` | site A's labels | `renderTicks cfg false false ticks` | `sharedTerm cfg false false ticks` |
|---|---|---|---|
| `ScalarFormatter(useMathText=True)` | `['$\mathdefault{100000000}$', …, '$\mathdefault{100000080}$']` | byte-identical | `''` |
| `ScalarFormatter()` | `['100000000', …, '100000080']` | byte-identical | `''` |
| `ScalarFormatter(useOffset=1e8, useMathText=True)` | `['$\mathdefault{100000000}$', …]` | byte-identical | `''` |
| `StrMethodFormatter("{x:.3f}")` (neither setter) | `['100000000.000', …]` | — (`modesAvailable = false`; `= ownLabels`, measured equal) | — |

and with a switch ON the same handles do hoist, and report it separately:
`renderTicks cfg true true` gives `['$\mathdefault{0}$','$\mathdefault{20}$',…]`
with `sharedTerm = '$\mathdefault{+10^{8}}$'` (mathtext) and `['0','20',…]` with
`sharedTerm = '+1e8'` (plain). So each clause is TRUE of the real site for every
one of these installs, and non-trivially so.

**(ii) The observable is the hoisted term, not the label's numeric value.** No
clause reads a label back to a number. Read-back is not a property of the site:
the marked-up rows above print labels no numeric parse accepts (measured: 6 of
the 48 configuration/tick combinations G-AX drives print such labels), so a
read-back obligation stated over the `modesAvailable = true` branch would be
FALSE of the real code even though every label there is correct. What is
uniformly true — and is all a legend needs — is that nothing was hoisted out:
`sharedTerm cfg offsetMode scaleMode ticks = ""`. That is `get_offset()`, the
term matplotlib draws *outside* the labels, which a legend has nowhere to draw;
it is empty exactly when each label stands on its own.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| a tick position: the IEEE-754 double the locator emits and the formatter receives | `Float` | identity — Lean `Float` *is* the IEEE-754 double, non-finite values included. The CARRIER is unrestricted: the model constrains no arithmetic on ticks, only which list is handed to the renderer, so every position the real site can hold is representable. What *is* restricted is the renderer's DOMAIN, and the restriction is explicit rather than implied by the carrier: see `renders` / `rendersLog` below and §3.4. |
| the list of tick positions `locs` / `raw_levels` | `List Float` | Python list ↔ `List`; `len` ↔ `.length`; positional index ↔ `[i]!` |
| a printed label `text.get_text()` (a `str`) | `String` | identity; label text is compared only for equality with the renderer's own output, never parsed |
| `axis.major.formatter` / `formatter` as installed, plus the view interval it is attached to | `cfg : RendererConfig` | opaque handle; two installs are the same `cfg` iff they render identically for every switch setting and tick list (G-AX rebuilds each configuration and asserts byte-identical labels, so the handle is well defined) |
| that formatter with the two display modes set, rendering the tick list | `renderTicks cfg offsetMode scaleMode ticks` | — |
| `formatter.get_offset()` — the separately drawn hoisted term | `sharedTerm cfg offsetMode scaleMode ticks` | identity on strings; `""` ↔ nothing hoisted |
| a `LogFormatter` **attached to the same axis** rendering `locs` | `renderLog cfg ticks` | the log-axis formatter of that installation applied to the tick list. `cfg` is the same handle `renderTicks` takes because at site B both arms attach their formatter to the SAME `dummy_axis()`; the two arms differ only in which renderer kind is constructed on it, which is what two distinct opaque functions over one handle expresses |
| that same formatter **returning** labels for that tick list rather than failing outright | `renders cfg offsetMode scaleMode ticks` | the modeled DOMAIN of `renderTicks`/`sharedTerm`: it holds exactly when `format_ticks(locs)` on that installation, with the two switches set as given, returns instead of raising. `axiom_check.py` makes it operational (return vs. raise) and asserts the three facts about that renderer only inside it (§3.4) |
| the `LogFormatter` of that installation **returning** labels for that tick list | `rendersLog cfg ticks` | the modeled domain of `renderLog`, the same way; it is a different set from the one above, measured (§3.4) |
| `formatter.set_useOffset(False)` (patch) | `offsetMode := false` | disabling the additive shared-term mode |
| `formatter.set_scientific(False)` (patch) | `scaleMode := false` | disabling the multiplicative `10^k` shared-term mode |

There is no numeric carrier below `Float` and no restriction on it. An earlier
revision of this spec modeled ticks as `List Int` bounded by `2^53`; that carrier
was not faithful to the site (the F2P legend of
`tests/test_relational.py::TestRelationalPlotter::test_legend_has_no_offset`
draws non-integral levels), and G-EQ refuted it with a materialized rival that
verified and did not resolve. `Float` is the carrier the callee actually
receives, so the model now covers the same inputs the site does.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `renderTicks` / `sharedTerm` ↔ the installed formatter (A-consumed)

**Callee:** the tick formatter as installed, rendering a list of tick locations
against a view interval (both sites attach the formatter to an axis — the real
axis at site A, seaborn's own `dummy_axis` at site B — and call
`format_ticks(locs)` / `formatter(x)` per element). A `ScalarFormatter` exposes
two *shared-term abbreviation* modes:

* `set_useOffset(b)` — when on, a common **additive** offset shared by all ticks
  is factored out of the labels (`axes.formatter.useoffset` /
  `offset_threshold` rcParams);
* `set_scientific(b)` — when on, a common **multiplicative** `10^k` factor is
  factored out of the labels.

Whatever is factored out is not silently dropped: matplotlib reports it
separately, via `Formatter.get_offset()`, for the axis to draw next to the ticks.
A legend has no such place, so a hoisted term is simply lost there. The patch
turns BOTH modes off at both sites, which is encoded as `renderTicks cfg false
false …`. The axioms the proof consumes are the **weakest** the legend
correctness needs, and none of them constrains label text:

* `renderTicks_length` — one label per tick, for any switch setting and any
  installed renderer, **wherever that renderer returns labels at all**
  (`renders cfg offsetMode scaleMode ticks →`; §3.4).
* `sharedTerm_none` — with BOTH switches off, `get_offset()` is `""`: nothing
  was hoisted, so each label stands on its own. This is the fact the F2P tests
  are really asserting, and unlike a read-back it is true of every renderer
  configuration, including ones whose labels are marked-up (§1.2(ii)). Stated
  on `renders cfg false false ticks`, for the same reason.
* `sharedTerm_hoists` — some configuration and tick list are in the domain with
  both switches on and DO hoist a term out there, so the `= ""` clause is a real
  constraint rather than an identity. (One conjunction, so the witness carries
  both halves.)
* `renderLog_length` (§3.2), on `rendersLog cfg ticks`.
* `renders_nonvacuous` — some installation and NON-EMPTY tick list lie in both
  domains at once, so neither guard is empty and no guarded fact (and no
  obligation that consumes one) is vacuous.

**Measured (G-AX, `axiom_check.py`, exit 0).** Over 16 renderer
configurations × 18 boundary tick lists × 4 switch settings, plus 6000 fuzzed
float tick lists, plus a second grid and a second fuzz that straddle the domain
boundary (§3.4): `renderTicks_length` and `sharedTerm_none` hold with 0
violations on all 34 824 in-domain observations. The 16 configurations include
the plain install, `useMathText`,
`usetex`, an explicit `useOffset` value, tight and huge view intervals, and
negative/mixed-magnitude ranges; each one is rebuilt and asserted to produce
byte-identical labels, which is what makes `RendererConfig` a well-defined
handle. `sharedTerm_hoists` is witnessed 32 times in the domain with both
switches on (e.g. plain install reports `'+1e8'` separately while printing
`'0'`), with 64 further hoisting observations at one-switch settings. Non-vacuity of
the *specification* is measured too: where the tests look, both-off labels stand
for their own ticks (42 configuration/tick combinations) while every hoisting
setting misreads (102 combinations), and 6 combinations print typeset labels that
no numeric reading parses at all — which is precisely why the obligation is
stated on the separately-reported term rather than on the label text.

Negative control (fails, as it must): asserting `sharedTerm_none` for a
*hoisting* setting reports `sharedTerm_none unsound: cfg=plain
ticks=[100000000.0, …] reported '1e8' separately with both switches off`, so the
check is sensitive to the switch it is about.

### 3.2 `renderLog` ↔ `LogFormatter` as installed (A-consumed)

**Callee:** `matplotlib.ticker.LogFormatter`, used by `locator_to_legend_entries`
when `isinstance(locator, mpl.ticker.LogLocator)` (`utils.py:698-699`). It has no
`set_useOffset`/`set_scientific` modes (confirmed by the exhaustive partition in
§3.3), so nothing is disabled on that path and the log labels are emitted
unchanged. The spec pins that unchanged behavior exactly: on the log path the
legend's labels ARE this renderer's output for THIS installation
(`legendEntries`'s `isLog = true → labels = renderLog cfg ticks`), and it emits
one label per tick (`renderLog_length`). A log-spaced label is not a plain
decimal, so nothing about its text is constrained.

**Why `renderLog` takes the handle — the observable is not a function of the
ticks.** This is the one place where the tick list does *not* determine the label
text, so it is worth spelling out from the callee's own source. Site B's own axis
is the local class

```python
    class dummy_axis:
        def get_view_interval(self):
            return limits
```

so the interval the renderer reads is `limits` — the span of the **data** the
legend describes, which `locator_to_legend_entries` was called with — and not the
span of the tick list it is handed. `LogFormatter.__call__` reads
`vmin, vmax = self.axis.get_view_interval()` and passes `d = vmax - vmin` down to
`_pprint_val`, whose format ladder switches at `d = 1e5` (`'%1.1f'` at or below
it, `'%1.1e'` above). `LogFormatter.set_locs` likewise ignores its `locs`
argument and derives `self._sublabels` from the same interval. So the same ticks
legitimately print two different label lists on two installations, and the model
must carry the installation to say which one it means.

Measured in the instance's own container (matplotlib 3.7.2, base_commit
22cdfb0c), through the site's own entry point:

| data limits | ticks the locator chose | labels the site prints |
|---|---|---|
| `(1.0, 1e5)` | `[1.0, 100.0, 10000.0]` | `['1', '100', '10000']` |
| `(1.0, 1.5e5)` | `[1.0, 100.0, 10000.0]` | `['1', '100', '1e4']` |
| `(1.0, 1e6)` | `[1.0, 100.0, 10000.0, 1e6]` | `['1', '100', '1e4', '1e+06']` |
| `(0.5, 2e5)` | `[10.0, 1000.0, 100000.0]` | `['10', '1000', '1e+05']` |

The first two rows are the same tick list and different labels. The same two rows
appear identically with `patch.diff` applied (the change touches only the
`ScalarFormatter` arm), so this is a property of the callee, not a delta of the
change. End-to-end through the public API the drawn legend agrees:
`sns.scatterplot(..., hue=np.geomspace(1, hi, 40), hue_norm=LogNorm(),
legend='brief')` draws `['1', '100', '10000']` at `hi = 1e5` and
`['1', '100', '1e4']` at `hi = 1.5e5`.

**Breadth, and what G-AX now checks.** Over a grid of 1206 data-limit pairs, 1173
of which yield a non-empty tick list, the site produces 75 distinct tick lists and
**6** of them print more than one label list — e.g. `[1e4, 1e5]` prints both
`['1e4','1e+05']` and `['10000','1e+05']`. So the interval-dependence is a broad
feature of the callee, not one fragile point. `axiom_check.py` therefore validates
the log renderer in the widened form, in a chain of two measurements:

1. `renderLog(cfg, ticks)` — the `LogFormatter` of installation `cfg`, driven by
   the site's own `set_locs`-then-call sequence — reproduces the labels the real
   `locator_to_legend_entries` prints, byte-for-byte, on all 1173
   (interval, tick list) pairs the site itself produced: **0 disagreements**;
2. the ticks-only model kept as the negative control (interval taken to be the
   ticks' own span, which is what an earlier revision of this spec used)
   disagrees with the site on **63** of the same 1173 pairs — so the handle
   argument is justified by a measured divergence, not by caution. The handle is
   additionally witnessed non-idle 10 times directly, by rendering one tick list
   on two installations differing only in the interval, and `renderLog` is
   re-derived twice per configuration to confirm it is a function of
   (handle, ticks).

`renderLog_length` is checked over 7 explicit log installations × 3 log tick
lists plus the 6000-case fuzz, 0 violations.

The same two-step chain is run for site B's numeric arm, which pins the
`set_locs` + per-element sequence the site uses to the `format_ticks` the axioms
are stated over: a replica built the way the site builds its `ScalarFormatter`
(fresh instance, `dummy_axis()` at the data limits) reproduces the site's own
labels on 173 installs with the two switches untouched, and `renderTicks cfg om
sm ticks` equals that same sequence driven after setting them, on 692
configuration/switch combinations.

Site B needs no `hasattr` guard at all: its else-arm constructs a FRESH
`ScalarFormatter`, which always carries both setters, and its log arm is a
`LogFormatter` the change never touches. The guards exist at site A for the
different reason given in §1.2 — site A uses whichever formatter was installed.

### 3.3 The non-`ScalarFormatter` branch is measured, not assumed (G-AX)

`modesAvailable = false → labels = ownLabels` is a claim about every OTHER
renderer a continuous scale can install, so `axiom_check.py` asks the site's two
questions of those renderers directly instead of reasoning about them. It does so
at two levels.

**Exhaustively, over every subclass.** `hasattr` on a bound method is decided by
the class, so no instantiation is needed and no awkward-to-construct subclass can
be missed. Enumerating every `Formatter` subclass matplotlib exposes in the two
modules a seaborn scale draws its formatters from — `matplotlib.ticker` and
`matplotlib.dates` — gives 16 subclasses (matplotlib 3.7.2), and the check
asserts:

1. `hasattr(f, "set_useOffset") == hasattr(f, "set_scientific")` for ALL 16 — the
   two guards at scales.py:381-384 never disagree, so ONE Bool models the pair
   faithfully rather than approximately;
2. exactly one of them, `ScalarFormatter`, answers yes — so the remaining 15 all
   reach the site with both questions answered no, and the
   `modesAvailable = false` arm is a real case covering many renderers, not an
   empty one.

Claim 2 is about this matplotlib, and is re-measured rather than reasoned from
the class names. The near-miss is `EngFormatter`, which reads like a numeric
formatter and in some matplotlib releases derives from `ScalarFormatter` — where
it would inherit both setters and move to the other arm. Under the version this
instance pins its bases are `(Formatter, TickHelper, object)` and
`hasattr(EngFormatter, "set_useOffset")` is `False`, measured; `axiom_check.py`
asserts both facts, so a matplotlib that changed this would fail G-AX here rather
than quietly invalidate the partition. What the modelling actually needs is claim
1 (the two guards never disagree), which is asserted for all 16 subclasses either
way.

**Concretely, over nine instantiated renderers.** For each renderer reachable
from `Continuous._get_formatter`'s non-`ScalarFormatter` arms (plus the
`Temporal` scale's date formatters) — `LogFormatter`, `LogFormatterSciNotation`
(`base=` / log-symlog trans), `EngFormatter` (`unit=`), `StrMethodFormatter` and
`FuncFormatter` (`like=`), `PercentFormatter` and `FixedFormatter`
(caller-supplied `formatter=`), `ConciseDateFormatter` and `AutoDateFormatter`
(`Temporal`) — it attaches the renderer to an axis the way seaborn does and
asserts, measured:

3. `len(f.format_ticks(ticks)) == len(ticks)` — the `require ownLabels.length =
   ticks.length` really is `Formatter.format_ticks`'s own guarantee, not a
   precondition invented for the proof;
4. running the site's own guarded sequence over the renderer leaves its labels
   byte-identical to its unconfigured `format_ticks(locs)` output — i.e.
   `labels = ownLabels`, the `modesAvailable = false` clause verbatim;
5. each of them hoists nothing FOR THE TICK LIST IT IS DRIVEN WITH
   (`get_offset()` is `""`), so the labels checked in 4 each stand on their own.

   Scoped to the tick list deliberately: "these renderers never hoist anything"
   would be FALSE, and it is not what the `modesAvailable = false` arm claims.
   Measured at `base_commit` (matplotlib 3.7.2), `ConciseDateFormatter` reports a
   term separately as soon as the span narrows — `'1973-Jan'` over four years,
   `'1970-Jan'` over a month, `'1970-Jan-02'` over a day or an hour — and only
   the quarter-span fixture above leaves it empty. That does not touch the
   modelling, because the arm's obligation is 4 (`labels = ownLabels`) and 4 is
   span-independent: `axiom_check.py`'s `check_date_spans` drives the two date
   renderers over five spans from an hour to four years (ten (span, renderer)
   settings), neither guard question ever answers yes, so the site runs neither
   setter, and `labels = ownLabels` holds on all ten — including the four where
   the separately reported term is non-empty. The specification says nothing
   about that term on this arm, which is the honest thing to say: a date legend
   really can lose its offset string, but the site cannot influence that, so a
   clause about it would constrain the renderer rather than the routine.

Negative controls (both fail, as they must): smuggling a bare `ScalarFormatter`
onto the instantiated list breaks assertion 2 (`ScalarFormatter_CONTROL
unexpectedly exposes the shared-term mode setters; the modesAvailable == False
case would not cover it`), and introducing a `Formatter` subclass with only
`set_useOffset` breaks assertion 1 (`modesAvailable unfaithful: … answers
set_useOffset=True but set_scientific=False, so one Bool cannot model the two
guards`). The check therefore genuinely distinguishes the two branches rather
than passing on anything put in front of it.

**Soundness check (G-AX):** `axiom_check.py` imports only `matplotlib` (the
library the gold patch touches) + stdlib, builds the real formatters over a
`dummy_axis` exactly as seaborn does, and asserts every obligation above. Exit 0
iff sound; it also asserts non-vacuity.

### 3.4 The renderers are PARTIAL, and the model's domain is explicit (`renders`, `rendersLog`)

Both axiomatized callees are partial functions of `(installation, switches,
ticks)`. For some arguments they return no labels at all — they raise, and the
raise leaves the modeled region entirely. The model states that domain instead of
assuming it away: `renders cfg offsetMode scaleMode ticks` and `rendersLog cfg
ticks` are opaque predicates, all four facts about the renderers are stated only
inside them, `renders_nonvacuous` says they are inhabited, and each obligation is
handed the domain of the renderer ITS arm calls, at the setting that arm uses:

* `legendLabels`: `require modesAvailable = true → renders cfg false false ticks`
  (D2). The other arm calls no renderer, so it carries no domain requirement.
* `legendEntries`: `require isLog = true → rendersLog cfg ticks` (D3) and
  `require isLog = false → renders cfg false false ticks` (D4) — two separate
  facts, because the two renderers' domains are two different sets (measured
  below).

An earlier revision of this spec stated the three renderer facts with no domain
guard at all, i.e. as claims about every `(cfg, switches, ticks)`. The
measurements below refute that reading, which is why the guards are here.

**Where the numeric renderer stops returning.** A `ScalarFormatter` that has
fewer than two tick positions of its own to measure falls back on the interval it
is attached to, and takes the base-ten magnitude of that interval's span; if the
span is not finite, that magnitude does not exist and the renderer raises
`OverflowError: cannot convert float infinity to integer` (matplotlib 3.7.2,
`ticker.py:796`, inside `ScalarFormatter._set_format`). Measured, with both
switches off:

| installation interval | ticks | result |
|---|---|---|
| `(-8e307, 8e307)` | `[0.0]` | `(['0'], '')` — in the domain |
| `(-9e307, 9e307)` | `[0.0]` | raises — outside |
| `(-1e308, 1e308)` | `[0.0]` | raises |
| `(-max, max)` | `[0.0]` | raises |
| `(-1e9, 1e9)` | `[0.0]` | `(['0'], '')` |

Bisecting the symmetric case gives the boundary exactly: the largest half-width
that still returns is `8.988465674311579e+307`, i.e. `max_double / 2` — a span of
exactly `max_double`. One step above it the span overflows to infinity and the
renderer stops returning. The exclusion is attributable to the SPAN and not to
the shape of the configuration, which is what the `(-9e307, 9e307)` /
`(-8e307, 8e307)` pair pins: the two installs differ in nothing else.

**The domain depends on the switches too**, which is why `renders` takes them and
why a guard stated at one setting cannot be reused at another. At interval
`(-max, max)` with ticks `[1e300]`: both switches off → raises; multiplicative
switch on → `(['1'], '1e300')`. Likewise at ticks `[-max, max]`: `off/off` and
`on/off` raise, `off/on` and `on/on` return (`['−1.798', '1.798']`, separately
reporting `'1e308'`). Turning the multiplicative mode on is what makes the
magnitude finite again — so the very setting the specification requires
(`false false`, the only one that hoists nothing) is the narrower domain.

**The tick list alone can leave the domain**, at an ordinary interval: `[inf]`
raises `OverflowError`, `[nan]` raises `ValueError`, `[0.0, inf]` raises, and
`[1e308, -1e308]` raises because the ticks' own range overflows. Lean's `Float`
includes these values, so an unguarded fact would have been claiming something
about them.

**The log renderer's domain is a different set** — genuinely wider here, which is
why there are two predicates. At interval `(-max, max)` the log renderer returns
`['1', '100', '1e4']` for `[1, 100, 10000]` and `['1e+300']` for `[1e300]`, where
the numeric renderer with both switches off returns nothing; it does refuse a
non-finite position, like the other one.

**The excluded region is outside the modeled region, not mis-described by it.**
This is what makes a domain restriction honest rather than an escape hatch: where
the domain fails, the raise propagates out of BOTH modeled sites, so there is no
legend there at all for a clause to be about. Measured at `base_commit` (the
commit G-AX runs at):

* site B — `locator_to_legend_entries(FixedLocator([0.0]), (-max, max), float)`
  → `OverflowError`; the same at `(-9e307, 9e307)` and `(-1e308, 1e308)`; at
  `(-1e9, 1e9)` it returns `([0.0], ['0'])`.
* site A — `Continuous(norm=(-max, max)).tick(at=[0.0])._setup(…)` →
  `OverflowError`; at `norm=(-1e9, 1e9)` it returns `([0.0], ['0'])`.

**And the domain costs the specification nothing where the instance lives.**
`axiom_check.py` asserts, rather than merely counts, that the ORDINARY region is
entirely inside the domain: every one of the 16 renderer configurations crossed
with every one of the 18 tick lists the site really produces — the F2P levels
(`1e8 + 20k`, `1e8 + 2.5k`) and the P2P levels among them — at all four switch
settings — 1 173 observations, with 0 exclusions; and every `(installation, tick
list)` pair either
site produced over its own data-limit grid (793 of them) is in the domain too. A
matplotlib that narrowed the domain into that region would fail G-AX here.

**Measured (G-AX, `axiom_check.py`, exit 0 at `base_commit`).** `renders` held on
34 824 of 38 652 observations and failed on 3 828; `rendersLog` held on 8 633 of
9 309 and failed on 676. Every guarded fact was asserted on every in-domain
observation with 0 violations, and every refusal was reproduced on a second call
with the same exception type, so "returns" really is a function of the arguments
and the predicate is well defined. Non-idleness is checked separately over a grid
that reaches the end of the double range (494 excluded observations there),
together with the boundary pair, the switch-dependence witness and the
log-is-wider witness above. `renders_nonvacuous` is witnessed by the installation
spanning `1 … 1e5` with ticks `[1, 100, 10000]`, which is in both domains at once
(numeric `['1', '100', '10000']`, log `['1', '100', '10000']`).

Why the earlier check did not see it: its magnitudes topped out at `1e12` and its
widest interval was `(-1e9, 1e9)`, so every observation it made was on the
comfortable side of a boundary that sits at `1e308`. The grid now straddles it
deliberately, and a second fuzz (3 000 draws with spans in `1e295 … 1e308` and
tick magnitudes up to and including non-finite ones) keeps both sides populated.

## 4. G-CONF — conf_skip=true (no R/I shadow)

The computed observable at both sites (`labels`) is produced ENTIRELY by the
A-tagged renderer callee. The impl region's only R/I content is the two
configuration constants (`offsetMode = scaleMode = false`), the `modesAvailable`
guard and the `isLog` renderer selection — none is an input-dependent
transformation of the label contents to differentially fuzz. The discriminating
fact (both switches off ⇒ nothing is hoisted; a switch on ⇒ something can be) is
a property of the real matplotlib renderer, validated by G-AX, not a
transliterable R/I shadow. Hence `meta.json conf_skip=true` and
`conformance_check.py` is a `status=skip` stub (SPEC_GUIDE §4). No fuzz seed is
pinned (no fuzzing runs).
