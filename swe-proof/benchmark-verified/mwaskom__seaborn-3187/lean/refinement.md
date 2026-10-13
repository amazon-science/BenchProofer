# refinement.md — mwaskom__seaborn-3187

Operation-by-operation correspondence between the two `implementation_*` triples
(Solution.lean impl regions) and `patch.diff` (the gold patch). Tags: **R** type
refinement, **A-consumed** proof uses an axiom, **A-reference** deep model
validated == real callee, **I** identical concrete op.

## Triple 1 — `implementation_continuousLegendLabels` ↔ scales.py site

Post-patch Python (`ContinuousBase._setup`, building `new._legend`,
`seaborn/_core/scales.py` L377–382):
```python
if hasattr(axis.major.formatter, "set_useOffset"):
    axis.major.formatter.set_useOffset(False)
if hasattr(axis.major.formatter, "set_scientific"):
    axis.major.formatter.set_scientific(False)
labels = axis.major.formatter.format_ticks(locs)
```

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match uncompacted r with \| some r' => …` — the capability split | the two `hasattr(...)` guards. MEASURED that both guards agree for every formatter class reachable here, so ONE `compactionCapable` bit refines both | R |
| 2 | `some r' => r' = { r with compacting := false }` | `set_useOffset(False)` then `set_scientific(False)` on that formatter. Both switches off ⇒ the single `compacting := false` bit; MEASURED half-off does not resolve, so the collapse is faithful, not lossy | R |
| 3 | `none => r` (renderer taken exactly as it stands) | the guards falling through: a `LogFormatter` / `LogFormatterSciNotation` is left untouched | R |
| 4 | `render r' ticks` (resp. `render r ticks`) | `axis.major.formatter.format_ticks(locs)` | **A-consumed** — `render` is opaque; the proof uses `render_length` and `render_uncompacted_faithful` |
| 5 | the pair `(writtenFrom, labels)` | `new._legend = list(locs), list(labels)` — plus the formatter itself, which is shared mutable state and outlives the call, so the state the labels were written from is a real observable | R |

## Triple 2 — `implementation_legendEntryLabels` ↔ utils.py site

Post-patch Python (`locator_to_legend_entries`, `else` branch,
`seaborn/utils.py` L699–701 + the label comprehension):
```python
formatter = mpl.ticker.ScalarFormatter()
formatter.set_useOffset(False)
formatter.set_scientific(False)
...
formatter.set_locs(raw_levels)
formatted_levels = [formatter(x) for x in raw_levels]
```

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match uncompacted r with` — same capability split | the `if isinstance(locator, LogLocator)` / `else` split. The `else` arm's `ScalarFormatter` is capable; the `if` arm's `LogFormatter` is not and the gold patch does not touch it | R |
| 2 | `some r' => r' = { r with compacting := false }` | `formatter.set_useOffset(False)`; `formatter.set_scientific(False)` | R |
| 3 | `none => r` | the `LogFormatter` arm, left as built | R |
| 4 | `render r' ticks` | `formatter.set_locs(raw_levels)` then `[formatter(x) for x in raw_levels]`. MEASURED equivalent to `format_ticks` (0 mismatches), which is why ONE `render` stands for both sites' calls | **A-consumed** — same two axioms |
| 5 | the pair | `return raw_levels, formatted_levels` | R |

## Which model expression stands for which real callee

The two impl arms reach two DIFFERENT real callees and the model does not collapse
them: `some r'` ↦ `ScalarFormatter.__call__` on a formatter whose `offset` and
`orderOfMagnitude` the patch has just forced to `0` / `0`; `none` ↦
`LogFormatter.__call__` (or `LogFormatterSciNotation.__call__`), which the patch
leaves alone. `render` is opaque and its argument carries the renderer's whole
state, so one axiomatized symbol legitimately covers both — the model never claims
the two arms write the same text, only that each arm's text is its OWN renderer's.

## The consumed axioms and the callee's steps

`render_uncompacted_faithful` is the read-back leg. `ScalarFormatter.__call__`'s
contract, as STEPS, is:

1. `set_locs` → `_compute_offset` (consults `_useOffset` / `_offset_threshold`),
   `_set_order_of_magnitude` (consults `_scientific` / `_powerlimits`), `_set_format`.
2. `xp = (x - self.offset) / 10 ** self.orderOfMagnitude`.
3. `_format_maybe_minus_and_locale(self.format, xp)` → `locale.format_string(...,
   grouping=True)` when `_useLocale`, else `%`-formatting; then `fix_minus`
   (U+2212 when `axes.unicode_minus`).
4. `self.format` itself, from `_set_format`, is wrapped in
   `r'$\mathdefault{%s}$'` when `_usetex or _useMathText`.

The gold patch's two calls neutralize step 1's two consulted tables only —
`offset == 0` and `orderOfMagnitude == 0`, so step 2 is the identity. Steps 3 and 4
are governed by state the patch does not touch and no legend builder can reach.
The axiom therefore has a leg for each: `compacting = false` for step 1/2,
`numeralStyle = true` for steps 3/4, and `t.natAbs ≤ 2^53` for the double channel
the tick travels through before step 2. Dropping the `numeralStyle` leg makes the
axiom FALSE of the real formatter at states it really reaches — MEASURED:
`useMathText=True` with the patch applied and `offset == orderOfMagnitude == 0`
writes `$\mathdefault{200000}$`, which reads back to no quantity at all. Details
and the reachability of that state through the public API: mapping.md.

`render_length` is the arity leg: one label per tick in every mode, MEASURED to
hold for every formatter class and every mode probed.

## The fix, isolated

- Triple 1 (scales.py): pre-patch omits the two guarded calls, so the labels are
  written from the renderer with the compacting mode still ON. The spec's first
  clause `∀ r', uncompacted r = some r' → writtenFrom = r'` demands `compacting =
  false` there, so the prepatch impl `(r, render r ticks)` contradicts it at any
  capable renderer standing in that mode. `Solution_prepatch.lean` ships exactly
  that buggy impl → its `correct_continuousLegendLabels` is unclosable (G-DIFF);
  MEASURED as a genuine contradiction, not merely tactic-weak, by an explicit
  `¬ problem_spec_…` refutation.
- Triple 2 (utils.py): likewise; `Solution_prepatch_2.lean` ships the buggy second
  impl → its `correct_legendEntryLabels` is unclosable. One prepatch variant per
  independently-tested behavior (F2P has one test per site).
- The single `compacting` bit is load-bearing, not a convenience: MEASURED a rival
  that turns only ONE of the two switches off resolves 0/2 F2P.

## Out of scope (unchanged, not modeled)

The tick *locator* that picks `locs` / `raw_levels`, `axis.set_view_interval`, the
`(vmin <= locs) & (locs <= vmax)` clip, `np.broadcast`, string→glyph rendering, the
legend artist construction, and the exact text of the `LogFormatter` arm. The patch
touches none of them; the only behavioral change is the compaction state the labels
are written from, which these two triples isolate. Whatever of the above still
governs the text is carried opaquely in `convention`, so the model never claims
determinacy the real renderer lacks.

## Mechanized checks

- **G-AX** (`axiom_check.py`, strict) validates the two consumed axioms against the
  real pinned matplotlib: it sweeps formatter kinds × text modes × compaction modes
  × view intervals × boundary and fuzzed tick sets, asserts 0 in-domain read-back
  violations, and additionally proves each guard TIGHT — obligation 4 for the 2^53
  bound, obligation 7 for `numeralStyle` (every dressed mode must be observed to
  break somewhere, and none may hold everywhere).
- **G-CONF** drives the REAL post-patch `seaborn.utils.locator_to_legend_entries`
  (triple 2's exact site, a pure callable needing no figure) over a discrete edge
  matrix plus ≥1e5 fuzzed large-offset tick sets, parses each produced label back,
  and diffs against the impl shadow. The pre-patch negative control (compaction
  left on) is shown to disagree, proving the test discriminates the bug.
