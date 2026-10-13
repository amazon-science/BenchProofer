# mapping.md — matplotlib__matplotlib-14623

## Modeled function

The fix is the *same* edit applied at five sites (`Axes.set_xlim`,
`Axes.set_ylim`, `Axes3D.set_xlim3d`, `Axes3D.set_ylim3d`,
`Axes3D.set_zlim3d`), plus a one-line companion change in
`LogLocator.nonsingular`. All five sites are the identical
direction-preservation skeleton; one Lean triple `*_setLim` models that single
observable behavior. The `LogLocator.nonsingular` edit is folded into the
normalizer callee's contract (see below), not modeled as a separate function.

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_setLim` / `problem_spec_setLim` / `correct_setLim` | `Axes.set_ylim` endpoint-direction handling (representative of all 5 sites) | `lib/matplotlib/axes/_base.py:3645-3655` @ d65c9ca |
| (same skeleton) | `Axes.set_xlim` | `lib/matplotlib/axes/_base.py:3262-3270` |
| (same skeleton) | `Axes3D.set_xlim3d` / `set_ylim3d` / `set_zlim3d` | `lib/mpl_toolkits/mplot3d/axes3d.py:623-633 / 681-691 / 739-749` |

## Type bijection (used by G-CONF + G-AX)

| Python | Lean | note |
|---|---|---|
| endpoint floats `left`/`bottom`, `right`/`top` | `a b : Rat` | the fix is **order-only** (sign/`>` comparison and swap); exact `Rat` models the order relation soundly. Kernel `Float` order is opaque to tactics (DECISIONS.md / SPEC_GUIDE §2). G-CONF bridges `Rat` ↔ Python `float`/`Fraction` exactly. |
| committed pair `(left, right)` written to `viewLim.intervalx` | `result : Rat × Rat` | the 2-tuple committed to the view interval |
| `swapped = left > right` | `swapped := decide (a > b)` | direction flag captured BEFORE normalization |
| `self.<axis>.get_major_locator().nonsingular(...)` | `normalizeRange : Rat → Rat → Rat × Rat` | unchanged callee (A-consumed). Returns endpoints in increasing order. |
| `self.<axis>.limit_range_for_scale(...)` | `clampToDomain : Rat → Rat → Rat × Rat` | unchanged callee (A-consumed). Order-preserving on already-ordered input. |
| `if swapped: left, right = right, left` | `if swapped then swap lo hi` | the ADDED op — restores requested direction |

## Callee provenance (A-reference pass-throughs — no consumed axioms)

The postcondition pins the committed pair by **exact equality** to the
pass-through values of the two callees (`result = if a > b then (p.2, p.1) else
p`). The proof therefore consumes NO property of either callee; each is an
**A-reference** left as the real repo callee in the differential G-CONF. G-AX is
a skip stub. The construction agent declares only the `opaque` signatures.

- **`normalizeRange`** ↔ `Locator.nonsingular` (`lib/matplotlib/ticker.py:1523`)
  and `LogLocator.nonsingular` (`ticker.py:2378`), both delegating to
  `transforms.nonsingular` (`lib/matplotlib/transforms.py:2791`).
  - Pre-patch the base `Locator.nonsingular` called `transforms.nonsingular(...,
    increasing=False)`, so it preserved a `v0 > v1` order; the companion gold
    edit drops `increasing=False`, making it return endpoints in increasing
    order like every other locator's `nonsingular`. Because the post-patch call
    sites capture the requested direction themselves (the `swapped` flag), this
    internal change to the callee is exercised end-to-end by G-CONF (which runs
    the REAL callee) rather than abstracted into a contract.
- **`clampToDomain`** ↔ `Axis.limit_range_for_scale` (`lib/matplotlib/axis.py:807`)
  → `ScaleBase.limit_range_for_scale` (`scale.py:60`, identity for linear) /
  `LogScale.limit_range_for_scale` (`scale.py:420`, clamps non-positive
  endpoints up to `minpos`). Left as the real callee in G-CONF (linear + log).

## G-CONF fuzz seed

Pinned seed: **20240630** (see `conformance_check.py`, `meta.json
verifier_pins.conf_seed`).
