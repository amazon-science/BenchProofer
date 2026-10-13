# mapping.md — matplotlib__matplotlib-20826

## Instance

- Repo `matplotlib/matplotlib`, base_commit `a0d2e399729d36499a1924e5ca5bc067c8396810`.
- Changed file: `lib/matplotlib/axis.py`.
- Changed function: `Axis.clear` (`lib/matplotlib/axis.py:788-816` @ base_commit).
  The gold patch replaces, inside `clear`, the two calls
  ```python
  self._reset_major_tick_kw()
  self._reset_minor_tick_kw()
  ```
  with two in-place assignments that set ONLY the `'gridOn'` entry of each tick
  keyword table:
  ```python
  self._major_tick_kw['gridOn'] = (
          mpl.rcParams['axes.grid'] and
          mpl.rcParams['axes.grid.which'] in ('both', 'major'))
  self._minor_tick_kw['gridOn'] = (
          mpl.rcParams['axes.grid'] and
          mpl.rcParams['axes.grid.which'] in ('both', 'minor'))
  ```
  The two `_reset_*_tick_kw` helpers (`axis.py:776-786`) each begin with
  `self._major/minor_tick_kw.clear()` and then set the `'gridOn'` entry — so the
  pre-patch `clear` wipes EVERY other entry of both tables; the post-patch `clear`
  updates the single `'gridOn'` entry and preserves the rest.

## Symbol binding (Lean ↔ Python @ base_commit)

| Lean symbol | Python counterpart | file:line @ base_commit |
|---|---|---|
| `implementation_clear` / `problem_spec_clear` | the tick-keyword re-initialisation step performed by `Axis.clear` (post-patch): the two `_major/minor_tick_kw['gridOn'] = …` assignments | `Axis.clear` body `axis.py:809-810` (the two lines the patch replaces) |
| `s : TickKwPair` | the pair `(self._major_tick_kw, self._minor_tick_kw)` as it stands at entry to the tick-kw step (already populated, e.g. with the per-side visibility flags written for shared axes) | `axis.py:675`, `axis.py:679` (the dicts) |
| `result : TickKwPair` | the same pair `(self._major_tick_kw, self._minor_tick_kw)` after the step | same |
| `gridKey = "gridOn"` | the dict key `'gridOn'` | `axis.py:778`, `axis.py:809` |
| `gridEnabled : Bool` | `mpl.rcParams['axes.grid']` (a bool) | `axis.py:809` |
| `which : String` | `mpl.rcParams['axes.grid.which']` (one of `'major'`, `'minor'`, `'both'`) | `axis.py:810` |
| `majorGridOn g w` | `g and w in ('both', 'major')` | `axis.py:809` |
| `minorGridOn g w` | `g and w in ('both', 'minor')` | `axis.py:810` |

## Type bijection (G-CONF uses this)

- Python `dict` `self._major_tick_kw` (and `_minor_tick_kw`) ↔ Lean
  `TickKw = String → Option Bool`: a present key `k` with value `v` ↔
  `table k = some v`; an absent key ↔ `table k = none`. The bridge in
  `conformance_check.py` maps a Python dict to its `get(k, None)` view and back.
- **Value-space refinement (R):** a real tick-kw table can hold non-boolean
  values too (sizes, colors, paddings). The modeled value space is `Option Bool`,
  i.e. restricted to the boolean visibility flags — `gridOn`, `tick1On`,
  `tick2On`, `label1On`, `label2On` — which are precisely the entries the bug
  drops and the F2P test (`test_shared_axes_clear`) observes. The frame property
  (every non-`gridOn` entry preserved) holds for ALL keys regardless of value
  type; restricting the fuzzed sentinel entries to booleans does not weaken it,
  and G-CONF additionally fuzzes non-boolean-valued keys to confirm preservation.
- `gridEnabled` ↔ `bool(mpl.rcParams['axes.grid'])`; `which` ↔
  `str(mpl.rcParams['axes.grid.which'])`. `Bool` ↔ Python `bool`,
  `String` ↔ Python `str`.

## Behavioral facts pinned outside Lean (used by G-CONF)

- After the post-patch `Axis.clear`, the tick-kw table `self._major_tick_kw`
  equals its prior contents with key `'gridOn'` overwritten by
  `mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','major')`
  and EVERY other key unchanged; symmetrically `_minor_tick_kw` with `'minor'`.
  No other line of `clear` mutates these dicts (the subsequent `reset_ticks`
  recreates `Tick` objects FROM the kw tables but does not alter them).
- There is no unchanged external callee in the modeled step: the grid flag is a
  concrete boolean expression over the two rcParams, and entry preservation is
  structural. Hence NO consumed `_prop` axiom and NO `opaque` callee — G-AX is a
  principled skip.

## G-CONF fuzz seed

Pinned seed: `2082620210811` (instance number `20826` + gold `created_at` date
`2021-08-11`). The fuzz corpus varies `axes.grid` (bool), `axes.grid.which`
(exactly `'major'`/`'minor'`/`'both'` — the only values matplotlib's rcParam
validator accepts; any other string raises on assignment, so these are the sole
realizable inputs), and the set of pre-existing sentinel entries
injected into each table (boolean visibility flags plus a non-boolean key), then
diffs the real patched `Axis.clear` dict outcome against the R/I shadow.
