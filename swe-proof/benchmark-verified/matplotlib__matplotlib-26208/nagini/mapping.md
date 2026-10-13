# mapping.md — matplotlib__matplotlib-26208

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f0f133943d3e4f1e2e665291fe1c8f658a84cc09`, states the type
abstraction, and gives the provenance of the one deep-model reference (there are
no consumed `@ContractOnly` axioms).

Repo file under change: `lib/matplotlib/axes/_base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_companion_sharing_horizontal(source_horizontal)` | `_AxesBase.twinx(self)` — `lib/matplotlib/axes/_base.py:4416` (changed hunk at body line 4444) | modeled changed function: the companion-frame builder sharing the horizontal (x) direction |
| `build_companion_sharing_vertical(source_vertical)` | `_AxesBase.twiny(self)` — `lib/matplotlib/axes/_base.py:4446` (changed hunk at body line 4474) | modeled changed function: the companion-frame builder sharing the vertical (y) direction |
| `CoordinateAxis` (field `descriptor`) | `matplotlib.axis.Axis` (its `self.units` field, set to `None` in `Axis.__init__`, `lib/matplotlib/axis.py:898`) | minimal carrier of the single touched field: the axis' unit descriptor reference |
| `UnitDescriptor` | the object stored in `Axis.units` (e.g. a `matplotlib.category.UnitData`, produced by the unit machinery from categorical/unit-bearing data) | opaque unit descriptor; only its object identity is observable |
| `Result()` of each builder | the new companion Axes' shared-direction axis: `ax2.xaxis` (`twinx`) / `ax2.yaxis` (`twiny`) | the freshly-built companion axis whose descriptor must be propagated |
| `source_horizontal` / `source_vertical` | `self.xaxis` (`twinx`) / `self.yaxis` (`twiny`) | the source frame's shared-direction axis, read-only |

The gold hunks (verbatim, `lib/matplotlib/axes/_base.py`):

```
# in twinx(), after ax2.patch.set_visible(False):
+        ax2.xaxis.units = self.xaxis.units

# in twiny(), after ax2.patch.set_visible(False):
+        ax2.yaxis.units = self.yaxis.units
```

A freshly constructed companion Axes is built by `self._make_twin_axes(...)`
(`_base.py:4396`), which calls `self.figure.add_subplot/add_axes`; the new Axes
constructs brand-new `Axis` objects, each with `self.units = None`
(`axis.py:898`). Hence the companion axis starts with no descriptor — modeled by
`CoordinateAxis.__init__` ensuring `self.descriptor is None`. The fix copies the
source axis' descriptor onto it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `matplotlib.axis.Axis` | `CoordinateAxis` with the single field `descriptor` | `axis.units` ↔ `coordinate_axis.descriptor`; the many other `Axis` fields are untouched by the patch and irrelevant to the observed behaviour, so they are omitted (minimal class, SPEC_GUIDE §2 rich-object rule) |
| `Axis.units` value (a `UnitData`/converter-supplied object, or `None`) | `Optional[UnitDescriptor]` | identity-only: `units is None` ↔ `descriptor is None`; `a.units is b.units` ↔ `a.descriptor is b.descriptor` |
| the new companion `Axes` and its shared `Axis` produced by `_make_twin_axes` | `Result()` (a fresh `CoordinateAxis`, `descriptor is None` on construction) | the patch's `ax2.xaxis` / `ax2.yaxis` is a brand-new axis (units=None) before the copy; modeled by constructing a fresh `CoordinateAxis` |
| `self.xaxis` / `self.yaxis` (read, not mutated by the hunk) | `source_horizontal` / `source_vertical` at `Acc(.descriptor, 1/2)` (read-only) | the patch only READS `self.<axis>.units`; directive 5 fractional permission |

The companion-frame builder's many unchanged operations (tick placement,
label/offset positioning, autoscale-setting inheritance, axis-visibility and
patch-visibility toggles) do not touch the unit descriptor and are not part of
the fixed behaviour, so they are not modeled — the skeleton models the changed
hunk (the descriptor propagation) faithfully and omits the unchanged siblings
(refinement.md §A row H0).

## 3. Callee provenance

### 3.1 No consumed axioms
The modelled change is a pure object-field propagation (read one reference,
construct a fresh object, write the reference). There is **no `@ContractOnly`
axiom** the proof consumes — the `axioms` region is empty. Nothing opaque is
relied upon: object construction, field read, field write, and reference
identity (`is`) are all directly expressible in Nagini.

### 3.2 `Result().descriptor is source.descriptor` deep model ↔ real `twinx`/`twiny` (A-reference)
The single deep-model claim — *after the companion frame is built, its
shared-direction axis references the SAME descriptor object as the source axis,
and is therefore non-None* — is the observable behaviour of the real
`twinx`/`twiny`. It is modeled **deeply** (the `companion.descriptor =
source.descriptor` assignment + the fresh-axis `None` start), not behind an
axiom, and validated **== the real callee** out-of-band by `axiom_check.py`
(G-AX): in-container it drives a real `Axes` to acquire a unit descriptor from
categorical data, builds the companion via the real `twinx`/`twiny`, and observes
the identity regime on `ax2.<axis>.units` vs `ax1.<axis>.units`.

**Soundness / discrimination check (G-AX):** `axiom_check.py` runs the real
matplotlib builders on the F2P scenario (`ax1.plot(['0','1'], ['a','b'])`) and
three further categorical scenarios for each direction (8 real builds total),
observing the modeled identity invariant on the real `Axis.units` objects. It
imports only `matplotlib` (the very module whose `twinx`/`twiny` the patch
edits) and `sys`. Per the panel refinement (DEFECT-2) it is a **discrimination
check that is self-validating against the image as shipped**: it does NOT assert
the post-fix invariant unconditionally (which spuriously failed against the
`base_commit` pre-patch tree). Instead it classifies each build as `patched`
(`twin.units is source.units` and not None — the deep-model postcondition holds)
or `prepatch` (`twin.<axis>.units is None` while `source.units is not None` — the
bug), exits 0 reporting the observed regime, and exits 1 only if a site is
neither (which would make the deep model unsound) or regimes are mixed across
sites. Verified locally: post-fix matplotlib reports `patched` on all 8 builds
(twin.units **is** source.units); the omit-the-copy pre-patch builder leaves
`twin.<axis>.units is None` (`prepatch`), breaking both `is not None` and
`is source.units` — exactly the bug the F2P test (`test_twin_units[x]`,
`test_twin_units[y]`) observes. Provenance: gold hunks at `_base.py:4444,4474`;
`Axis.units` default `None` at `axis.py:898`.
