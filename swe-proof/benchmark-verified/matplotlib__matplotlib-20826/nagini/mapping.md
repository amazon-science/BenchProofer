# mapping.md — matplotlib__matplotlib-20826

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a0d2e399729d36499a1924e5ca5bc067c8396810`, states the type
abstraction, and gives the provenance of the one axiom.

Repo file under change: `lib/matplotlib/axis.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reinit_tick_kw_major(tick_kw, flag_enabled, selection_covers)` | the major tick-keyword re-initialisation performed by `Axis.clear` — `lib/matplotlib/axis.py:788` (the lines that handled `self._major_tick_kw`, body lines 809) | modeled changed site (major) |
| `reinit_tick_kw_minor(tick_kw, flag_enabled, selection_covers)` | the minor tick-keyword re-initialisation performed by `Axis.clear` — `lib/matplotlib/axis.py:788` (body line 810) | modeled changed site (minor) |
| `tick_kw` parameter | `self._major_tick_kw` / `self._minor_tick_kw` — the per-axis tick-keyword dicts (`lib/matplotlib/axis.py:675-676`, set as `dict()`; consumed by `Axis._get_tick`, e.g. `lib/matplotlib/axis.py:2045-2050`, `XTick(self.axes, 0, major=major, **tick_kw)`) | the mutated mapping |
| `refreshed_key()` (de-narrated; was the grid identity) | the dict key `'gridOn'` | the one designated entry that is refreshed |
| `flag_enabled` (de-narrated) | `mpl.rcParams['axes.grid']` | the first ambient config flag ("grids globally enabled") |
| `selection_covers` (de-narrated) | `mpl.rcParams['axes.grid.which'] in ('both', 'major')` (major site) / `in ('both', 'minor')` (minor site) | "the configured which-selection covers this tick class" |

(Audit-doc note: this mapping deliberately names the gold mechanism — `gridOn` /
`axes.grid` — to establish the refinement provenance; that is the auditor's job
and is NOT consumer-visible. The model.py spec view is de-narrated and names none
of it; see meta.json `gates.G-LEAK`. The model identifiers `refreshed_key` /
`flag_enabled` / `selection_covers` are the renamed-for-leakage tokens.)
| `dict_carry_over(d)` *(axiom — A-reference)* | Python mapping-copy primitive (`dict(d)` / `d.copy()`); models the "carry over the existing tick-keyword settings" effect that the fixed in-place update preserves | unchanged dict operation, validated == real primitive by axiom_check.py (G-AX) |

The pre-patch repo symbols whose CALLS the change removes (audit only, not
referenced from the consumer spec view): `Axis._reset_major_tick_kw`
(`axis.py:776-780`) and `Axis._reset_minor_tick_kw` (`axis.py:782-786`), each of
which does `self._<which>_tick_kw.clear()` then sets only `gridOn`. The gold
patch stops `Axis.clear` from calling those two reset helpers and instead sets
`self._major_tick_kw['gridOn'] = …` / `self._minor_tick_kw['gridOn'] = …`
**in place**, leaving every other previously-stored key untouched. (The helpers
themselves are unchanged; only `clear`'s use of them changes — `set_tick_params`
still calls them on an explicit `reset=True`, where wiping IS intended.)

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self._major_tick_kw` / `self._minor_tick_kw` : `dict` from str setting-name to value | `Dict[int, bool]` from a setting-name TOKEN to its on/off value | each observed setting name (`'gridOn'`, `'tick1On'`, `'label1On'`, `'tick2On'`, `'label2On'`, …) ↔ a distinct `int` token; the refreshed designated name ↔ `refreshed_key() == 0`; the only values the bug concerns are booleans (visibility on/off), so `bool` is the faithful value carrier. `k in d` ↔ key membership; `d[k]` ↔ value lookup. |
| the gold in-place statement `self._major_tick_kw['gridOn'] = (...)` mutating the SAME dict, leaving other keys | a function RETURNING a fresh `Dict[int, bool]` whose content is the input's other keys preserved plus the updated grid key | the resulting *state* of the mapping is observationally identical whether produced by in-place mutation of the same object or by a fresh equal mapping (the consumer `_get_tick` reads `**tick_kw` by content, never by identity). Modelling re-initialisation as a state-producing function keeps the operation translatable (Nagini 1.2.0 supports neither `dict.clear()` nor key deletion) while pinning the same content guarantee. |
| `mpl.rcParams['axes.grid']` (bool) | `flag_enabled: bool` | identity |
| `mpl.rcParams['axes.grid.which'] in ('both','major'/'minor')` (bool) | `selection_covers: bool` | identity (the str-membership test is evaluated outside the modelled site; its boolean outcome is the input) |

`str` indexing/iteration is banned in Nagini, so dict keys are `int` tokens; the
`which`-membership test result is supplied as the `bool` input `selection_covers`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `dict_carry_over` ↔ Python mapping-copy primitive (A-reference)
**Callee:** the language-level mapping carry-over `dict(d)` / `d.copy()` /
`{**d}` — a fresh dict with exactly the same key/value content as `d`: every key
preserved with its value, none introduced, `d` unchanged. This is the standard,
documented behaviour of `dict` construction from a mapping
(https://docs.python.org/3/library/stdtypes.html#dict). The model uses it to
realise the "the existing tick-keyword settings are carried over (only the grid
key is updated)" effect that the FIXED `Axis.clear` achieves by an in-place
assignment that does NOT clear the dict. It is an **A-reference**: a deep model
of an unchanged primitive, validated equal to the real primitive by
`axiom_check.py`, NOT relied on as opaque behaviour.

The axiom is the **weakest** contract the proof needs: it states only the exact
key/value equivalence (both directions) and freshness — nothing about ordering,
identity of values, or any richer dict behaviour.

**Soundness check (G-AX):** `axiom_check.py` runs the real `dict(d)` on boundary
inputs (empty, grid-only, the side-hiding visibility flags shared axes store —
e.g. `{label1On: False, tick1On: False}` — mixtures, and grid already set both
ways) plus 20 000 randomised fuzz mappings, asserting both directions of the
key/value equivalence and freshness. It additionally validates the END-TO-END
modelled re-initialisation (the designated key set to `flag_enabled and selection_covers`, every
other key preserved, no spurious key) against a faithful Python reference of the
fixed operation over the same boundary + fuzz, and confirms the buggy
empty-then-set behaviour differs whenever a non-grid key exists. Exit 0 iff
sound. It imports only the standard library; nothing repo-specific.
