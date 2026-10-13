# refinement.md — matplotlib__matplotlib-20826

Maps every operation in `implementation_clear` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op). Every step is R, A, or I.

The patch edits `Axis.clear` (`lib/matplotlib/axis.py`): it removes the two
`self._reset_*_tick_kw()` calls — each of which did `dict.clear()` then set the
single `'gridOn'` entry — and replaces them with two in-place assignments that
set ONLY `'gridOn'`, leaving every other entry of both tick-keyword tables
intact. The fix is therefore a frame-preserving keyed-map update: recompute one
designated entry, preserve all others.

## Modeled function: `clear` (the tick-keyword re-initialisation step)

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `s : TickKwPair`, `s.major`/`s.minor : String → Option Bool` | the dicts `self._major_tick_kw`, `self._minor_tick_kw` at entry to the step | **R** | a Python `dict` (key→value) viewed as a total `get(k,None)` map; values restricted to the boolean visibility flags the bug drops and the F2P test observes. Bijection in mapping.md. |
| 2 | `majorGridOn gridEnabled which = gridEnabled && (which == "both" \|\| which == "major")` | `mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','major')` | **I** | identical boolean expression; `in ('both','major')` ↔ the two-way `==` disjunction. (Added line of the patch.) |
| 3 | `minorGridOn gridEnabled which = gridEnabled && (which == "both" \|\| which == "minor")` | `… in ('both','minor')` | **I** | as #2 with `'minor'`. (Added line of the patch.) |
| 4 | `major := Function.update s.major gridKey (some (majorGridOn …))` | `self._major_tick_kw['gridOn'] = (…)` | **I** (deep model of the changed op) | **the fixed operation.** The post-patch code mutates the EXISTING dict at key `'gridOn'` only; `Function.update m k v` is exactly "the map equal to `m` everywhere except `k`, where it is `v`". Crucially the base map is `s.major` (the prior contents), NOT a fresh/empty map — this is what the patch changed (it dropped the preceding `.clear()`). |
| 5 | `minor := Function.update s.minor gridKey (some (minorGridOn …))` | `self._minor_tick_kw['gridOn'] = (…)` | **I** | as #4 for the minor table. |
| 6 | `return ⟨major, minor⟩` | the two dicts after the step | **R** | the resulting pair of maps; the rest of `clear` (`reset_ticks`, etc.) reads these tables but does not mutate them, so the step's output is the pair. |

## A-tagging summary

- **No A-consumed axiom and no A-reference callee.** The modeled step calls no
  unchanged external function: the grid flag is concrete boolean logic over the
  two global preferences (rows 2–3, tag I), and entry preservation is the
  structural meaning of `Function.update` (rows 4–5). There is no `opaque` decl
  and no `axiom _prop`. `axiom_check.py` is a principled skip stub (G-AX skips).
- The impl region is all R/I (NOT all-A-tagged): `conf_skip = false`, and
  `conformance_check.py` differential-tests the R/I shadow against the real
  patched `Axis.clear` dict behaviour over ≥1e5 fuzzed inputs (0 disagreements).

## Soundness check (verify ⟹ correct)

- `problem_spec_clear` pins the result COMPLETELY (directive 5 frame): the
  `gridOn` entry of each table equals the freshly computed grid flag, AND every
  other key of each table equals its prior value `s.major k` / `s.minor k`.
  Nothing about the result is left free; the preserved entries are grounded in
  the actual input map (directive 8: no ungrounded oracle — the surviving values
  must be PRODUCED by carrying `s` through, not echoed from a key).
- A wrong impl that re-initialises by emptying the tables first (the pre-fix
  `dict.clear()` behaviour) cannot satisfy this spec: take any `s` with a
  non-`gridOn` entry present, e.g. `s.major "tick2On" = some false`. The spec's
  third conjunct demands `result.major "tick2On" = some false`, but the
  clear-first impl yields `none`. This is the discriminating clause — exactly the
  dropped per-side visibility flag that the F2P test
  `test_shared_axes_clear[png]` detects (shared-axis tick labels that must stay
  hidden after `ax.clear()`).
- `Solution_prepatch.lean` reproduces the pre-fix behaviour (build each table
  from an empty map before setting `gridOn`); it is byte-identical in spec to
  `Solution.lean` and its carried `correct_clear` is unprovable on the frame
  conjuncts (G-DIFF / G-PANEL): for `s` with any non-`gridOn` entry, the third/
  fourth conjuncts are false. One prepatch variant: the fix is a single
  independently-observable behavior (one F2P test).
- patch.diff == gold verbatim (applies at base_commit; resolves the F2P test).
