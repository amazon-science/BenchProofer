# mapping.md — matplotlib__matplotlib-26208

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f0f133943d3e4f1e2e665291fe1c8f658a84cc09`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and the pinned G-CONF fuzz seed.

Repo file under change: `lib/matplotlib/axes/_base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `inheritSharedConvA (source : ConvSetting)` | `Axes.twinx(self)` — `lib/matplotlib/axes/_base.py:4416` (gold-added body line `ax2.xaxis.units = self.xaxis.units`, hunk @ 4441) | first modeled changed function: a companion view sharing the x coordinate must carry over the source x-axis's conversion setting |
| `inheritSharedConvB (source : ConvSetting)` | `Axes.twiny(self)` — `lib/matplotlib/axes/_base.py:4446` (gold-added body line `ax2.yaxis.units = self.yaxis.units`, hunk @ 4470) | second, independent modeled changed function: a companion view sharing the y coordinate must carry over the source y-axis's conversion setting |
| `ConvSetting = Option Int` | the value stored at `Axis.units` (`lib/matplotlib/axis.py:898`, `self.units = None` at construction) | pure spec: an axis's display-conversion setting, absent or present-up-to-identity |
| `isPresent (s : ConvSetting)` | `Axis.units is not None` (the predicate the F2P test asserts: `getattr(ax, axis_name).units is not None`) | pure spec: whether the axis carries a present setting |

The `source` argument of each method is the source axis's `units` value
(`self.xaxis.units` / `self.yaxis.units`); the returned `out` is the companion
axis's `units` value (`ax2.xaxis.units` / `ax2.yaxis.units`) after creation.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `Axis.units` — the per-axis conversion setting, an arbitrary object or `None` | `ConvSetting = Option Int` | `None` ↔ `none`; a present setting object ↔ `some t`, where `t : Int` is a stand-in for the object's identity (`id(obj)`). The ONLY observable the F2P test and the issue exercise are (a) `units is not None` ↔ `isPresent`, and (b) `ax2.<axis>.units is ax1.<axis>.units` ↔ `out = source` (object identity ↔ value equality of the `Int` tag). |
| `units is not None` (F2P assertion) | `isPresent : ConvSetting → Bool` | `s is not None` ↔ `s.isSome` |
| `ax2.<axis>.units is self.<axis>.units` (F2P identity assertion) | `out = source` | object identity in Python ↔ structural equality of the modeled `Option Int` (identity tags compare equal iff the same object) |

Lean is functional and has no aliasing; the gold's `=` (a reference assignment
in Python that makes `ax2.<axis>.units` the *same object* as `self.<axis>.units`)
is modeled as value equality of the identity tag, which is exactly what the F2P
`is` check observes.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

This bundle consumes **no axioms** and declares **no A-reference deep model of
an unchanged callee**. The single operation each changed function adds — copying
the source axis's `units` onto the companion axis's `units` — is the operation
the patch CHANGES, and it is modeled **deeply** as a plain value copy
(`let out := source`). Per SPEC_GUIDE directive 7 / §3, a *changed* op modeled
deeply is the modeled function itself, not a consumed axiom and not an
A-reference of an unchanged callee; its fidelity to the real patched code is the
job of G-CONF (`conformance_check.py`), which executes the REAL patched
`twinx` / `twiny`.

The other statements in `twinx`/`twiny` (`tick_right`, `set_label_position`,
`set_autoscalex_on`, `set_visible(False)`, `_make_twin_axes`, …) are NOT part of
the modeled `units`-carry-over contract — the `ensures` clauses say nothing
about them — so they are not axiomatized and need no G-AX obligation. They are
unchanged by the gold patch.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`26208`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the deep value-copy (`out = source`) to Python and compares against the REAL
patched `twinx`/`twiny`, observing the two F2P-observable facts: the companion
axis carries a present setting exactly when the source does, and the companion's
setting **is** the source's (object identity). There are NO A-tagged callees in
the impl region, so the shadow is pure R/I (`conf_skip = false`).
