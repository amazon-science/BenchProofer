# mapping.md — mwaskom__seaborn-3187

## Symbol binding (file:line @ base_commit 22cdfb0c)

Two independently-fixed legend-label-producing sites; one CLEVER triple each.

### Triple 1 — `implementation_continuousLegendLabels`
- **Python site:** `ContinuousBase._setup`, building `new._legend`, in
  `seaborn/_core/scales.py` L377–382 @ base_commit. Post-patch (gold) inserts,
  before `format_ticks`:
  ```python
  if hasattr(axis.major.formatter, "set_useOffset"):
      axis.major.formatter.set_useOffset(False)
  if hasattr(axis.major.formatter, "set_scientific"):
      axis.major.formatter.set_scientific(False)
  labels = axis.major.formatter.format_ticks(locs)
  ```
  `axis.major.formatter` here is a matplotlib tick formatter attached to the
  scale's `PseudoAxis` during `_setup`. For a linear `Continuous` scale it is a
  `ScalarFormatter` (exposes both `set_useOffset` and `set_scientific`); for a log
  scale it is a `LogFormatter` / `LogFormatterSciNotation` (exposes neither).
- **Lean binding:** `implementation_continuousLegendLabels` /
  `problem_spec_continuousLegendLabels` / `correct_continuousLegendLabels` in
  `Solution.lean`.

### Triple 2 — `implementation_legendEntryLabels`
- **Python site:** `locator_to_legend_entries`, in `seaborn/utils.py` L687–710 @
  base_commit; the `else` branch building the `ScalarFormatter` (L699–701).
  Post-patch (gold) inserts, right after `formatter = ScalarFormatter()`:
  ```python
  formatter.set_useOffset(False)
  formatter.set_scientific(False)
  ```
  then `formatter.set_locs(raw_levels)` and `[formatter(x) for x in raw_levels]`
  produce the labels. The `if isinstance(locator, LogLocator)` arm builds a
  `LogFormatter` instead and the gold patch does NOT touch it.
- **Lean binding:** `implementation_legendEntryLabels` /
  `problem_spec_legendEntryLabels` / `correct_legendEntryLabels` in
  `Solution.lean`.

## Lean ↔ Python type bridge (used by G-AX + G-CONF)

The Lean carrier is a `TickRenderer` — the tick formatter a legend builder MEETS,
together with the axis view interval it reads — plus the OPAQUE `render` /
`labelValue`. `render` and `labelValue` are axioms, not computed here; the two
consumed facts about them are validated executably by `axiom_check.py` (G-AX).

| Lean | Python | note |
|---|---|---|
| `ticks : List Int` | the tick positions to be labelled (`locs` in scales.py; `raw_levels` in utils.py) | order preserved; modelled as `Int` because the round trip is only exact on integers, and MEASURED the real locators at these sites produce integer-valued "nice" levels |
| `r : TickRenderer` | a tick formatter instance together with the view interval its axis reports | the renderer arrives already built and is shared mutable state |
| `r.compactionCapable : Bool` | `hasattr(formatter, "set_useOffset")` | MEASURED to agree with `hasattr(formatter, "set_scientific")` for every formatter class reachable at these sites: `ScalarFormatter` exposes both, `LogFormatter` / `LogFormatterSciNotation` neither. So it is one intrinsic bit of the class, not a setting |
| `r.compacting : Bool` | whether the two compaction behaviours are enabled (`set_useOffset(v)`, `set_scientific(v)`) | the only component a legend builder may change; MEASURED that half-off does not resolve, so the single bit faithfully means BOTH off |
| `r.numeralStyle : Bool` | `not (formatter._useMathText or formatter._useLocale or formatter._usetex)` for a capable formatter; `False` for a non-capable one | whether the renderer spells a label as a BARE NUMERAL. Settled from a constructor argument or an rcParam BEFORE the renderer reaches either site, and NOT touched by `set_useOffset` / `set_scientific`, so no legend builder can change it |
| `r.convention : Nat` | the remainder of what governs the text: the formatter CLASS plus the axis view interval | encoded as an index into `axiom_check.py`'s `CONVENTIONS`; MEASURED load-bearing, the text varies with the view interval alone |
| `render r ticks` | `formatter.set_locs([float(t) for t in ticks])` then `[formatter(float(t)) for t in ticks]` | MEASURED equivalent to `formatter.format_ticks(locs)` — the call the scales.py site makes — with 0 mismatches; opaque in Lean |
| `labelValue s` | `float(s.strip().replace(U+2212, '-'))` | the quantity a reader recovers from one label read back on its own; raises for text that denotes no quantity. Opaque in Lean |
| `result : TickRenderer × List String` | (the formatter state the labels were written from, the label text list the legend keeps) | the renderer half is a real observable: the formatter is shared and outlives the call |

## Why `numeralStyle` is part of the state, and why the read-back claim is guarded by it

`ScalarFormatter.__call__` ends in
`_format_maybe_minus_and_locale(self.format, xp)`, and `_set_format` appends a
`$\mathdefault{...}$` wrapper whenever `self._usetex or self._useMathText`; the
locale arm routes the text through `locale.format_string(..., grouping=True)`.
So a capable renderer with compaction FULLY off — the gold patch's own two calls
applied, `offset == 0` and `orderOfMagnitude == 0` — still writes text that does
not read back as a number when any of those three is set. MEASURED on the pinned
matplotlib 3.7.2 with `patch.diff` applied, ticks `[0, 200000, …, 1000000]`:

| configuration | labels | read back? |
|---|---|---|
| bare numerals | `['0','200000',…,'1000000']` | yes, all |
| `useMathText` | `['$\mathdefault{0}$', …]` | no, none parse |
| `useLocale` (grouping locale) | `['0','200,000',…,'1,000,000']` | no, all but `0` |

Both dressed configurations are reachable through the public API at these very
sites — `Continuous().label(formatter=ScalarFormatter(useMathText=True))` at the
scales.py site, and `mpl.rcParams['axes.formatter.use_mathtext'] = True` /
`axes.formatter.use_locale` at both (the utils.py site's bare `ScalarFormatter()`
picks the rcParams up on construction). Neither is something the legend builder
can undo. So the read-back guarantee is claimed exactly where the renderer
delivers it: capable, not compacting, spelling bare numerals, and within 2^53.
`axiom_check.py` obligation 7 measures BOTH directions of that guard — every
dressed mode must be observed to break somewhere, and none may hold everywhere.

## Magnitude guard

Tick positions reach the renderer through an IEEE-754 double channel, which stops
distinguishing consecutive integers past 2^53, so a tick above that is snapped to
a neighbour before any text is written (MEASURED: `2^53 + 1` renders as
`9007199254740992`). Hence the `t.natAbs ≤ 9007199254740992` guard on the
read-back claim. `axiom_check.py` obligation 4 measures that the guard is not
needlessly narrow.

## Callee provenance

`render` and `labelValue` are AXIOMATIZED opaque callees; `render_length` and
`render_uncompacted_faithful` are the two CONSUMED contracts, and both correctness
proofs depend on them (`#print axioms`). Their executable validation against the
real matplotlib formatter is `axiom_check.py` → **G-AX** (strict mode).

## G-CONF fuzz seed
Pinned seed: **3187** (also in conformance_check.py and meta.json).
