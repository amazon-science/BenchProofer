# mapping.md — mwaskom__seaborn-3187

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 22cdfb0c93f8ec78492d87edb810f10cb7f57a31`, states the type
abstraction, and gives the provenance of the two deep models (the real
matplotlib tick formatters the legend code renders through).

Repo files under change: `seaborn/_core/scales.py`, `seaborn/utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line, post-change) | role |
|---|---|---|
| `legend_values_continuous(fmt, locs)` | the legend branch of `ContinuousBase._setup` — `seaborn/_core/scales.py:377-390` (`if prop.legend: axis.set_view_interval(...); locs = axis.major.locator(); locs = locs[(vmin <= locs) & (locs <= vmax)]; …; labels = axis.major.formatter.format_ticks(locs); new._legend = list(locs), list(labels)`) | modeled changed function, site 1: builds `(locs, labels)` for an objects-interface continuous legend, rendering through the formatter already installed on the axis |
| `legend_values_locator(fmt, locs)` | `locator_to_legend_entries` — `seaborn/utils.py:687-714` (`formatter = mpl.ticker.ScalarFormatter(); … formatter.axis = dummy_axis(); formatter.set_locs(raw_levels); formatted_levels = [formatter(x) for x in raw_levels]`) | modeled changed function, site 2: builds `(levels, formatted_levels)` for the classic relational legend |
| `TickFormatter(convention, residual, view_lo, view_hi)` | the tick formatter object itself: `axis.major.formatter` (site 1, chosen by `Continuous._get_formatter`, `seaborn/_core/scales.py:623-660`) / the local `formatter` (site 2, `seaborn/utils.py:698-706`) | shared mutable state that arrives already built and outlives the call |
| `TickFormatter.convention` | which formatter object it IS — the rendering convention it was constructed with (`ScalarFormatter()` at `scales.py:658` / `utils.py:701`; `EngFormatter` at `scales.py:655`; `StrMethodFormatter` / `FuncFormatter` at `scales.py:640,642`; `LogFormatterSciNotation` at `scales.py:646`; `LogFormatter` at `utils.py:699`) | immutable-by-the-builder attribute; `0` is the convention that writes each tick's own value in full |
| `TickFormatter.view_lo` / `TickFormatter.view_hi` | the numeric range currently in view on the axis the formatter is attached to: `axis.set_view_interval(vmin, vmax)` at `seaborn/_core/scales.py:378` (site 1) / the `limits` argument the site's stub axis hands back, `seaborn/utils.py:694-696` (`class dummy_axis: def get_view_interval(self): return limits`) (site 2) | an input the formatter reads on the rendering path; arrives set and is not the builder's to change |
| `TickFormatter.residual` | whether any control by which the formatter may factor a magnitude common to the ticks out of them is still enabled (`get_useOffset()` / `_scientific` on a `ScalarFormatter`-derived formatter; nothing at all on a formatter with no such control) | the one mutable mode the builder is answerable for |
| `rendered_labels(convention, ticks, residual, view_lo, view_hi)` *(deep model — A-consumed)* | the label sequence that formatter renders for that whole tick set: `axis.major.formatter.format_ticks(locs)` (site 1, `scales.py:389`) / `formatter.set_locs(raw_levels); [formatter(x) for x in raw_levels]` (site 2, `utils.py:711-712`) | the callee the legend's text comes from; §3.1 |
| `reading(label)` *(deep model — A-reference)* | the number a reader recovers from a label's text: `float(text)` after normalising the Unicode minus and digit-grouping spaces | pure spec; §3.2 |
| `legend_reads_ticks(labels, ticks)` | the whole-legend property: every label reads back to the full value of the tick it labels | pure spec helper |

The behaviour the change installs, at both sites: the formatter the legend
renders through is put into the mode in which it factors nothing out, so the
labels the legend records carry each tick's own value rather than a small
residual with the common magnitude parked in a separate string the legend never
keeps (`new._legend = list(locs), list(labels)` at `scales.py:390`;
`return raw_levels, formatted_levels` at `utils.py:714`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | correspondence |
|---|---|---|
| tick locations — a numpy float array (`axis.major.locator()` clipped to the view interval, `scales.py:379-380`; `raw_levels` clipped to `limits`, `utils.py:688-692`) | `List[int]` of tick values | `locs[k]` ↔ `int(locs[k])`. The exercised locations are integral (`np.add(xy["x"], 1e8)`, `long_df["z"] + 1e8`, and the `[0.20…0.28]` grid scaled), and the modeled property — *is the recorded text the formatter's own text, and does it read back to the tick's full value* — is exact at integral values. Domain `|loc| <= 2**53`, where int ↔ IEEE double is exact (conformance_check.py `MAX_EXACT`). |
| a legend label — the per-tick **string** the legend records | an opaque `int` code standing for that exact TEXT | injective by construction: two labels are equal in the model exactly when their texts are identical. The identity coding is what conformance_check.py uses (`label_comparison: "exact text"`). **This is the load-bearing carrier choice**: the model is deliberately NOT allowed to see a label as the number it reads back to, because `float('0.20') == float('0.2')` while the repo's own legend assertion is on the text (`tests/test_relational.py:866,877` expects `['0.20','0.22','0.24','0.26','0.28']`). A model whose observable was the parsed number cannot distinguish a label the formatter rendered from a number written in directly. |
| which formatter object the legend renders through | `fmt.convention`, an opaque `int` | `0` ↔ the convention that writes each tick's own value in full — the formatter a numeric legend gets when nothing else has been asked (`ScalarFormatter()`, `scales.py:658` / `utils.py:701`, reached whenever `Continuous.label` was given no `formatter=`/`like=`/`base=`/`unit=`, `scales.py:631-658`). Any other value ↔ a formatter that re-expresses ticks in a unit or at a precision of its own (`EngFormatter`, `StrMethodFormatter`, `FuncFormatter`, `LogFormatterSciNotation`, `LogFormatter`). The model never writes this field and only ever tests `== 0`, so the codes for the other conventions are arbitrary and distinct. |
| the axis range the formatter renders against — a float pair (`(vmin, vmax)` at `scales.py:378`; `limits` at `utils.py:694-696`) | `fmt.view_lo` / `fmt.view_hi`, two `int`s | `view_lo ↔ int(vmin)`, `view_hi ↔ int(vmax)`, same exactness domain as the tick carrier. It is a SEPARATE input from the tick set, not a function of it: a legend's ticks are chosen inside its variable's range and are normally narrower (both sites then clip the ticks to the range — `scales.py:380`, `utils.py:692`). Modeled as formatter state rather than a parameter because the formatter reaches it on its own, through the axis it is attached to (`self.axis.get_view_interval()`); on the rendering path that call is the ONLY channel a matplotlib formatter has to its environment, so this pair completes the input list. |
| whether the formatter may still factor a magnitude out | `fmt.residual: bool` | `True` ↔ at least one such control is enabled; `False` ↔ none is. On a `ScalarFormatter`-derived formatter this reads as `get_useOffset() or _scientific` (conformance_check.py `residual_state`); a formatter with no such control is already, and permanently, in the `False` state — measured, not assumed (axiom_check.py's guard check: every non-default convention renders byte-identically with those controls disabled and left alone). ONE model boolean for the whole family: refinement.md §C. |
| `new._legend = list(locs), list(labels)` / `return raw_levels, formatted_levels` | `Result()` (the label sequence) | the locations half is the identity on the input — asserted separately by conformance_check.py; `Result()` models the labels half, the part the change is about. |

`float` is modeled as `int` because the change is **not** about floating-point
precision: it is about which string the legend records. At the exercised integral
tick values the text/reading distinction is exact, so no interpreted-float
encoding is needed (refinement.md §D; meta `float_encoding: null`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `rendered_labels` ↔ the real formatter's rendering (A-consumed)

**Callee:** `matplotlib.ticker.Formatter` subclasses, through the two APIs the two
sites use — `format_ticks(locs)` (site 1, `scales.py:389`) and
`set_locs(raw_levels)` + `formatter(x)` (site 2, `utils.py:711-712`).

The signature takes the WHOLE tick set and returns the WHOLE label sequence
because that is how the callee behaves: a formatter picks ONE way of writing all
the ticks it is given and renders each of them that way. Measured: tick `1e8`
renders `'0'` in the set `{1e8, 1e8+1}` and `'1'` in `{0, 1e8, 1e8+1}`; tick
`0.2` renders `'0.20'` in `{0.2 … 0.28}` and `'0.2'` alone (axiom_check.py
`check_set_dependence`, `check_text_not_reading`). So a per-tick signature would
be unfaithful, and a model that rendered ticks one at a time could not reproduce
the repo's labels.

The signature also takes the AXIS RANGE, because the tick set is not the callee's
only input. A `matplotlib` formatter renders through the axis it is attached to,
and on the rendering path (`format_ticks` / `set_locs` / `__call__`) what every
kind reads from that axis is `self.axis.get_view_interval()` — which is exactly
what each site sets up: `axis.set_view_interval(vmin, vmax)` at `scales.py:378`,
and the stub axis of `utils.py:694-696` whose *only* method returns `limits`.
The `Log*` kinds additionally attempt `self.axis.get_transform()` (guarded by
`try/AttributeError` in `LogFormatter.set_locs`), but at neither modeled site
does the attached axis provide one: seaborn's `PseudoAxis` (`scales.py:791-877`,
methods `set_/get_view_interval`, `set_/get_data_interval`, `get_tick_space`,
the four `set_major_/minor_` setters, `set_units`, `update_units`,
`convert_units`) defines no `get_transform`, and site 2's stub axis defines
`get_view_interval` and nothing else, so that branch is inert here — 48 real site-1 renderings
across `trans` ∈ {None, log, symlog, symlog(1), symlog(10)} × 4 log-formatter
kinds produce 0 sequence mismatches against the transform-less deep model
(G-PANEL-2 differential). So (convention, tick set, mode, range) is the complete
input list at these two sites, and holding the range at the tick set's own span
— the degenerate choice a careless driver makes — would model a callee that does
not exist.
Measured range-dependence with the tick set held FIXED and only the range moved:
the SI-unit, both log and the default conventions all change their label text
(axiom_check.py `check_range_dependence`, measured
`['eng', 'log', 'logsci', 'scalar']`). Since the model pins the whole label
sequence, a rendering taken against any other interval — the tick span included —
is a different sequence and cannot discharge the postcondition.

The axiom states only the two properties the proofs consume — the weakest
sufficient contract:

1. `len(rendered_labels(c, ticks, r)) == len(ticks)` — one label per tick, for
   every convention and every mode.
2. `c == 0 and not r ==> reading(rendered_labels(c, ticks, r)[k]) == ticks[k]` —
   the full-value convention, with residual rendering disabled, factors nothing
   out, so each of its labels reads back to its tick's full value.

Nothing else about a label is knowable: with residual rendering enabled the
readings are UNCONSTRAINED (which is exactly the information a legend loses), and
two conventions, two modes or two tick sets need not render alike. That is what
makes the arrived-in behaviour unprovable (G-DIFF, two twins) and what makes
every wrong-argument rival in properties.py unprovable too.

**Declared domain.** Neither deep model declares a `Requires`, so the declared
domain is universal, and the model reaches the callee only at
`(any convention, any List[int] tick sequence, residual=False, the range it
arrived with)` — the loop invariants pin the mode, the convention and both range
bounds. The real callee's own domain is disclosed in `model.py`'s
`rendered_labels` docstring and pinned two-sidedly by axiom_check.py
`check_callee_domain`: **only** a convention that chooses its unit from the WIDTH
of the axis range can lack a label sequence for a range of no width, every
convention that does render one renders exactly one label per tick, and on a
range of positive width every convention renders (an empty tick set included).
The declared set is a BOUND and the actual restriction is measured, because it is
matplotlib-version-dependent: on mpl 3.10.9 `EngFormatter` takes
`math.log(vmax - vmin, 1000)` in `set_locs` and so raises `ValueError: math
domain error` on a zero-width range (measured set `['eng']`), while in the
instance's own environment — the one G-AX and G-CONF run in — nothing raises.
Where it does happen the real legend site produces no legend either, which is why
conformance_check.py compares the whole outcome including failure and counts the
agreements rather than skipping the input.

**Soundness check (G-AX).** axiom_check.py runs 7 real formatter kinds
(`ScalarFormatter`, `EngFormatter`, two `StrMethodFormatter`s, `FuncFormatter`,
`LogFormatterSciNotation`, `LogFormatter`) over 10 boundary tick sets + 4000 fuzz
sets, each against SEVEN axis ranges drawn independently of the ticks (the
diagonal, 2×, 1000×, zero-anchored, upward-only, an unrelated `(0,1)` and
`(-1e9,1e9)`), through both APIs, and asserts: one label per tick everywhere; the
full-value convention with the controls disabled reads back to full ticks on
every one of those ranges; with them enabled it demonstrably does not (so the
hypothesis is load-bearing); the text carries strictly more than its reading and
depends on the whole set; at least one convention's text MOVES when only the
range moves (so the range argument is load-bearing, not decorative — §4); some
non-default conventions are unreadable even with every control disabled (so no
reading guarantee is available there); and the default convention is one the
controls move. Imports only `matplotlib`/`numpy`/stdlib.

### 3.2 `reading` ↔ reading a label back as a number (A-reference)

**Callee:** none in the repo — this is the *reader's* operation, i.e. what the
repo's own tests do to a legend label (`float(text.get_text())`). Modeled as a
deliberately UNINTERPRETED `@Pure @ContractOnly` function: the ONLY thing the
model may learn about a label's text. Its concrete meaning is `float(text)` after
normalising `ScalarFormatter`'s Unicode minus (U+2212) and digit-grouping spaces,
and it is validated in that form by axiom_check.py, but the model consumes no
axiom about it directly — only the one guarded statement inside
`rendered_labels`. Keeping it uninterpreted is what stops the spec from being
satisfiable by any value the implementation can compute for itself.

## 4. The convention partition, and why the reading guarantee is guarded

`Continuous.label` (`seaborn/_core/scales.py:502-507`) lets the caller supply the
formatter, and `_get_formatter` (`:623-660`) honours it: `formatter=` is returned
as-is (`:631-632`), `like=` becomes a `StrMethodFormatter`/`FuncFormatter`,
`base=` a `LogFormatterSciNotation`, `unit=` an `EngFormatter`, and otherwise a
plain `ScalarFormatter`. Site 2 similarly picks a `LogFormatter` for a log
locator (`seaborn/utils.py:698-699`) and a `ScalarFormatter` otherwise.

So the formatter a legend renders through is genuinely open, and only ONE of
those conventions can produce labels that read back to full tick values at all.
Measured (axiom_check.py `check_convention_guard`,
`check_default_convention_is_the_moved_one`):

* both `StrMethodFormatter`s and `FuncFormatter` have no such control at all,
  and `LogFormatter` / `LogFormatterSciNotation` / `EngFormatter` do not consult
  the ones they inherit for the decision the guard is about. What matters for the
  guard is the surviving one-sided fact, measured directly: on the `1e8`-scale
  F2P shape these conventions render `['100 Mg', …]` / `['1e+08', …]` /
  `['10^{8}', …]`, which do **not** read back to their ticks even with every
  residual control disabled — so on them there is no reading guarantee to
  withhold.
* `ScalarFormatter` is a kind those controls DO move: on a large tick set its
  labels differ with them disabled vs left alone.
* The count of non-default conventions whose text moves with those controls is
  REPORTED rather than asserted to be zero (`check_convention_guard` returns
  `(unreadable, moved)`). An earlier version of this document claimed all of them
  were byte-identical either way; in mpl 3.10.9 that is measurably false for the
  `Log*` kinds on some ranges, and the guard does not need it — it needs only
  that those conventions' labels are unreadable regardless, which is what is
  asserted.

Hence the guarded shape of the reading clause,
`Implies(fmt.convention == 0, legend_reads_ticks(...))`: it withholds nothing
that is available, and for the other conventions there is no residual-mode
behaviour for such a clause to be about. The guard is in the POSTCONDITION, not a
precondition — every convention is admitted, and
`Ensures(fmt.convention == Old(fmt.convention))` stops an implementation
falsifying the guard instead of delivering the guarantee (properties.py
`convention-rewrite` is the rival that measures this).

Because the model's postconditions hold for it, the site-2 log branch
(`utils.py:698-699`, a `LogFormatter` with no residual control) is IN scope as a
non-default convention: `not fmt.residual` is true of it on arrival and stays
true, one label per tick holds, and no reading guarantee is claimed of it.

## 5. G-CONF (differential conformance — conformance_check.py)

**Pinned seed: `3187`** (module constant `SEED`).

**Shadow.** The `# impl-start`/`# impl-end` regions of BOTH modeled functions,
copied verbatim with only the contract calls removed (`Invariant`, `Assert`, the
`# invariants-start/-end` markers) — the model IS Python, so nothing is
transliterated; the dead-looking `conv0` / `old_seq` bindings are kept because
they are in the region. `TickFormatter` and `legend_reads_ticks` are the pure
region, copied the same way; `PSeq`/`ToSeq` are a thin immutable-sequence shim.
`rendered_labels` and `reading` are `@ContractOnly` (no body), so the shadow
CALLS the real callees §3 binds them to. The model's `ticks`, `residual`, `view_lo` and
`view_hi` arguments are passed straight through — the driver supplies only which
real formatter kind the opaque `convention` code denotes and which API the site
under test renders through, neither of which is model state, so the abstraction
is not inverted. The bridge attaches the formatter to an axis whose
`get_view_interval()` returns exactly the model's `(view_lo, view_hi)`, and the
driver hands the oracle that very same interval. Both axioms are therefore *exercised* on every input rather than
assumed.

**Oracle.** Both repo sites of §1, CALLED live in the gold-patched container
(neither needs a figure):

* site 1 — the legend branch of `ContinuousBase._setup`, driven as
  `Continuous().tick(at=locs).label(formatter=f)._setup(pd.Series([view_lo,
  view_hi]), Color())` and read off `scale._legend`. The data series is what
  fixes `vmin`/`vmax`, hence the `axis.set_view_interval(vmin, vmax)` of
  `scales.py:378` — so the axis range is driven from the CASE, independently of
  the tick set. Passing the formatter IN
  (`scales.py:502-507` → `:631-632`) does two things: it makes all four
  conventions drivable at site 1, and it leaves the driver holding the same
  object the patched code configured, so the STATE half of the postcondition
  (`not fmt.residual`, `fmt.convention == Old(fmt.convention)`) is observed on
  the real object rather than inferred.
* site 2 — `seaborn.utils.locator_to_legend_entries`, called directly with
  `FixedLocator(locs)`, `limits=(view_lo, view_hi)` — the same independently
  drawn range, which this site hands to its formatter through the stub axis of
  `utils.py:694-696` — and `float`. This site builds its own
  formatter, so only the default convention is reachable and the object is not
  observable; the state half is checked at site 1 only, and the JSON records
  that (`state_half_observed_at`).

**Bridge (§2 inverted).** model → repo: `List[int]` tick locations become
`[float(v) for v in locs]` fed to a `FixedLocator`; `view_lo`/`view_hi` become
the axis range the site is set up with; the opaque `convention` code becomes a
real formatter kind. repo → model: each label is its own opaque code —
the EXACT text, compared byte for byte — and the `list(locs)` half of each site's
return value is separately asserted to be the identity on the input. Every
generated input satisfies the model's `Requires` (`Acc(list_pred(locs), 1/2)` —
any `List[int]`, the empty list included; `Acc(fmt.convention)`,
`Acc(fmt.residual)`, `Acc(fmt.view_lo)`, `Acc(fmt.view_hi)` — any formatter in
any state, on an axis of any range).

**Inputs.** 30 boundary cases (empty / singleton / duplicates / unsorted / the
exact F2P tick shape `[1e8+1 … 1e8+4]` / magnitude regimes 1 … 2**53 / negative
and zero-spanning / 12-element long lists), each at FOUR axis ranges (the
diagonal plus 1×/10×/1000× the tick span wider on each side), + 100 000 seeded
fuzz draws each with an independently drawn range from the same ladder. The range
always contains the tick set, because both sites clip their ticks to it
(`scales.py:380`, `utils.py:692`), so a range excluding a tick could not be
presented with that tick surviving; `wider_than_ticks_checks` in the JSON counts
the cases whose range is strictly wider than the ticks. Every
input is diffed against site 2; the boundary cases and every 20th fuzz draw also
against site 1 under the default convention; the boundary cases and every 2000th
draw against site 1 under each of the other three. Recorded run (in the
instance's own environment): **105 750 checks (100 120 site-2 + 5 630 site-1),
0 disagreements**, 5 630 formatter-state checks, 105 240 reading checks, 1 320
bridge-purity checks, 74 315 of the checks on a range strictly WIDER than the
ticks (`wider_than_ticks_checks`), `axis_range_driven_independently: true`,
`boundary_range_factors: [0, 1, 10, 1000]`, `raise_agreements: 0` (nothing in
that environment reaches the §3.1 restriction; the whole-outcome comparison is
what makes the driver robust to an environment where something does — 9
agreements on mpl 3.10.9), `label_comparison: "exact text"`,
`conventions_driven: {0: scalar, 1: eng, 2: strmethod_3g, 3: log}`.

**Non-vacuity.** The pre-state skeletons (`model_prepatch.py`,
`model_prepatch_2.py`) are this same impl with the rendering mode left as it
arrived. The driver evaluates that variant on every large-magnitude case (capped
at 20 000 evaluations, reported in the JSON, never silently applied) and requires
at least one to DISAGREE with the patched oracle; a run where none did is
reported as `fail`. Recorded run: 20 000/20 000 controls disagree.

**Verdict (gate-recorded).** `G-CONF=pass`, exit 0, `shadow_provenance: "direct"`.
