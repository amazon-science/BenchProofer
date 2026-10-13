# mapping.md — matplotlib__matplotlib-26208

`spec_provenance: cold` — derived only from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`f0f133943d3e4f1e2e665291fe1c8f658a84cc09`).

Repo file under change: `lib/matplotlib/axes/_base.py`.

## 1. Symbol binding

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_stepA` / `problem_spec_stepA` / `correct_stepA` | `Axes.twinx(self)` — gold-added body line `ax2.xaxis.units = self.xaxis.units` | `lib/matplotlib/axes/_base.py:4416` (hunk @ 4441) |
| `implementation_stepB` / `problem_spec_stepB` / `correct_stepB` | `Axes.twiny(self)` — gold-added body line `ax2.yaxis.units = self.yaxis.units` | `lib/matplotlib/axes/_base.py:4446` (hunk @ 4470) |
| `Slot = Option Nat` | the value stored at `Axis.units` (`lib/matplotlib/axis.py:898`, `self.units = None` at construction) | pure spec: a coordinate's interpretation/conversion setting, absent or present-up-to-identity |
| `isPresent (s : Slot)` | `Axis.units is not None` (the predicate the F2P test asserts) | pure spec: whether the shared coordinate carries a present setting |

Both modeled functions create a *secondary frame* that re-uses ONE coordinate of
the source frame (`twinx` re-uses the x coordinate; `twiny` re-uses the y
coordinate). The gold patch adds, at the very end of each function (just before
`return ax2`):

```
twinx:  ax2.xaxis.units = self.xaxis.units   # _base.py @ +4444
twiny:  ax2.yaxis.units = self.yaxis.units   # _base.py @ +4474
```

i.e. the newly-created secondary frame's *shared* coordinate inherits the source
coordinate's interpretation/conversion setting.

Each modeled function takes `source` — the source coordinate's `units` value
(`self.xaxis.units` / `self.yaxis.units`) — and returns `out` — the secondary
frame's copy of that shared coordinate's `units` value (`ax2.xaxis.units` /
`ax2.yaxis.units`) after construction. Only the shared coordinate is observed at
each site; the secondary frame's OTHER (independent, freshly created) coordinate
is not touched by the gold edit and is not part of this contract.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `Axis.units` — the per-coordinate conversion setting, an arbitrary object or `None` | `Slot = Option Nat` | `None` ↔ `none`; a present setting object ↔ `some t`, where `t : Nat` is a stand-in for the object's identity (`id(obj)`). The ONLY observables the F2P test and the issue exercise are (a) `units is not None` ↔ `isPresent`, and (b) `ax2.<axis>.units is ax1.<axis>.units` ↔ `out = source`. |
| `units is not None` (F2P assertion) | `isPresent : Slot → Bool` | `s is not None` ↔ `s.isSome` |
| `ax2.<axis>.units is self.<axis>.units` (F2P identity assertion) | `out = source` | object identity in Python ↔ structural equality of the modeled `Option Nat` (identity tags compare equal iff the same object) |

Lean is functional and has no aliasing; the gold's `=` (a reference assignment in
Python that makes `ax2.<axis>.units` the *same object* as `self.<axis>.units`) is
modeled as value equality of the identity tag, which is exactly what the F2P `is`
check observes.

## 3. Callee provenance / flag deps

- `_make_twin_axes(sharex=self)` / `(sharey=self)` and the orientation/visibility
  calls (`tick_right`, `set_label_position`, `set_offset_position`,
  `set_autoscalex_on`, `tick_left`, `set_visible`, `patch.set_visible`, …) do NOT
  read or write `.units`. They are unchanged context with no effect on the modeled
  observable; the secondary frame's shared coordinate starts at the fresh (absent)
  default until the gold edit copies the source's setting onto it. NOT axiomatized
  (no `_prop`).
- The changed op is a plain attribute assignment (`ax2.<axis>.units =
  self.<axis>.units`); it calls no repo helper, so there is no consumed callee
  axiom and no A-reference. The setting is modeled DEEPLY as plain `Option Nat`
  data; its carry-over (`out = source`) is an R/I op validated by G-CONF.
- The two sites are modeled and exercised independently because the F2P test is
  parametrised over `twin ∈ {x, y}` and asserts each coordinate on its own.
- No flag dependency.

## 4. Pinned G-CONF fuzz seed

`26208` (also in `meta.json verifier_pins.conf_seed` and `conformance_check.py`).
`conformance_check.py` seeds its `random.Random` with `26208`; the R/I shadow
transliterates the deep value-copy (`out = source`) and compares against the
POST-PATCH oracle (`ax2.<axis>.units = self.<axis>.units`), observing the two
F2P-observable facts: the shared coordinate carries a present setting exactly when
the source does, and it **is** the source's (object identity). There are NO
A-tagged callees in the impl region, so the shadow is pure R/I (`conf_skip = false`).
