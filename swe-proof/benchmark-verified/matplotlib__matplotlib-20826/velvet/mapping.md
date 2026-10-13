# mapping.md — matplotlib__matplotlib-20826

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a0d2e399729d36499a1924e5ca5bc067c8396810`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee/flag provenance.

Repo file under change: `lib/matplotlib/axis.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resetAxisTickKeywords` | the tick-keyword reset performed inside `Axis.clear` — `lib/matplotlib/axis.py:788` (the changed hunk, body lines 806–818) | the modeled changed behaviour: re-derive the distinguished entry of each tick-keyword settings map while preserving the rest |
| `majorKw : String → Bool` | `self._major_tick_kw` (`dict`, initialised `axis.py:675`) | the major-tick keyword settings map |
| `minorKw : String → Bool` | `self._minor_tick_kw` (`dict`, initialised `axis.py:676`) | the minor-tick keyword settings map |
| `key : String` | the literal setting name `'gridOn'` (the one entry the reset recomputes — `axis.py:808,811` post-patch) | the distinguished entry recomputed on reset |
| `majorVal : Bool` | `mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','major')` (`axis.py:807-809` post-patch) | the recomputed value of the distinguished entry for the major map |
| `minorVal : Bool` | `mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','minor')` (`axis.py:810-812` post-patch) | the recomputed value of the distinguished entry for the minor map |

The pre-patch repo construct the change removes (refinement audit only, not in
the consumer spec view): the two helpers `_reset_major_tick_kw`
(`axis.py:776-780`) and `_reset_minor_tick_kw` (`axis.py:782-786`), each of which
does `self._{major,minor}_tick_kw.clear()` and then writes only `gridOn`. The
old `clear()` (`axis.py:809-810`) called both helpers; the `.clear()` discarded
every other entry of the two maps — the visibility flags (`tick1On`, `tick2On`,
`label1On`, `label2On`, …) that linked/shared axes had previously turned off.
The fix writes `gridOn` **in place**, so the rest of each map survives.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self._major_tick_kw` / `self._minor_tick_kw` (`dict[str, bool]` over the on/off tick-keyword flags) | `String → Bool` (a total settings map) | a `dict` `d` ↔ the total map `m` with `m s = d[s]` for keys present in `d`; the frame quantifier `∀ k ≠ key, m k = mOld k` ↔ "every dict entry other than `'gridOn'` is preserved (same presence and value) and no new entry is introduced". The tick-keyword values this bug concerns are booleans (`gridOn`, `tick1On`, `tick2On`, `label1On`, `label2On`); G-CONF fuzzes exactly that boolean key domain. |
| the setting name `'gridOn'` | `key : String` | identity on the string literal |
| `mpl.rcParams['axes.grid'] and ... in ('both', 'major')` | `majorVal : Bool` | the recomputed flag is supplied to the model as an input boolean; its `rcParams` computation is transliterated I-tag in the G-CONF shadow (§4) and read from the same `rcParams` the oracle reads |
| `mpl.rcParams['axes.grid'] and ... in ('both', 'minor')` | `minorVal : Bool` | as above, for the minor map |

`majorKw`/`minorKw` are declared `mut` and are genuinely mutated; `key`,
`majorVal`, `minorVal` are read-only and are NOT `mut` (directive-5 discipline).
The post-state of each mutated map is pinned exactly: one entry equals the
recomputed value, every other entry equals its old value (the frame).

## 3. Callees and axioms

**None.** The modeled operation is a pure data-structure update: write one entry
of each settings map, preserve the rest. There is no unchanged repository callee
whose contract the proof must assume, so this bundle declares **no `axiom` and no
A-reference deep model**, and ships **no `axiom_check.py`** — G-AX skips (gates.py
`gate_ax`: skip when `axiom_check.py` is absent). The value written (`majorVal`/
`minorVal`) is a config lookup, modeled as a method input (an R/I leg checked by
G-CONF), not a callee contract.

The frame property the proof relies on — `Function.update f k v` agrees with `f`
off `k` and equals `v` at `k` — is Mathlib library knowledge
(`Function.update_of_ne`, `Function.update_self`), not a repository assumption.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`20826`**. The R/I shadow
it builds is `Function.update` on `key = 'gridOn'` for each map (a Python dict
copy with `'gridOn'` overwritten); the oracle is the patched `Axis.clear`
behaviour observed by pre-populating `axis._major_tick_kw`/`_minor_tick_kw`,
calling `axis.clear()`, and reading the resulting dicts. Both sides read the same
`mpl.rcParams` so the recomputed `gridOn` is compared, not assumed. The oracle
(`clear()`) is memoised on the finite `(major-map, minor-map, axes.grid,
axes.grid.which)` input domain so ≥10⁵ fuzzed inputs are processed without 10⁵
figure mutations.
