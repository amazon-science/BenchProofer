# refinement.md — matplotlib__matplotlib-14623

Operation correspondence between `implementation_setLim` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

The fix is the same direction-preservation edit at five call sites
(`set_xlim`, `set_ylim`, `set_xlim3d`, `set_ylim3d`, `set_zlim3d`) plus a
one-line companion change to `LogLocator`'s base `nonsingular` (drop
`increasing=False`). `implementation_setLim` is the single skeleton common to
all five sites; the `nonsingular` companion change is internal to the
`normalizeRange` callee (it only affects the order in which that callee returns
its endpoints, which the post-patch call sites no longer rely on — they capture
direction themselves), so it is covered by leaving `normalizeRange` as the real
callee in G-CONF, not a separately-modeled op.

## `implementation_setLim` ↔ the gold `set_*lim` hunks

The gold patch turns (representative `set_ylim` hunk)

```python
bottom, top = self.yaxis.get_major_locator().nonsingular(bottom, top)   # PRE-PATCH
bottom, top = self.yaxis.limit_range_for_scale(bottom, top)
```

into

```python
swapped = bottom > top                                                  # POST-PATCH
bottom, top = self.yaxis.get_major_locator().nonsingular(bottom, top)
bottom, top = self.yaxis.limit_range_for_scale(bottom, top)
if swapped:
    bottom, top = top, bottom
```

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `let swapped := decide (a > b)` | `swapped = bottom > top` | I | direction flag captured BEFORE normalization (the bug was that this was never captured); `>` on floats ↦ `>` on `Rat` (R: order-only type model) |
| `let n := normalizeRange a b` | `… get_major_locator().nonsingular(bottom, top)` | A-reference | unchanged callee; its result passes through verbatim. The spec consumes NO property of it (exact-equality postcondition). Left as the real callee in G-CONF (validated == real `nonsingular`, linear + log). |
| `let c := clampToDomain n.1 n.2` | `… limit_range_for_scale(bottom, top)` | A-reference | unchanged callee; result passes through verbatim. No consumed property; left as the real callee in G-CONF (validated == real `limit_range_for_scale`, linear + log). |
| `let mut lo := c.1; let mut hi := c.2` | bind normalized endpoints | I | the two committed magnitudes |
| `if swapped then swap lo hi` | `if swapped: bottom, top = top, bottom` | I | the ADDED op — restores the requested direction; this is the fix |
| `return (lo, hi)` | `self.viewLim.intervalx = (left, right)` / committed pair | R | committed view interval ↦ `Rat × Rat`; endpoints ↦ exact `Rat` |

Every row is **I**, **A-reference**, or **R**. The edited op (the conditional
swap) is an **I** concrete op; the postcondition pins the committed pair by
exact equality (`if a > b then (p.2, p.1) else p`), so the two callees carry
NO consumed contract — they are A-reference pass-throughs, validated == the real
callees by the differential G-CONF (not by an axiom; G-AX is a skip stub). The
R/I/A-reference legs are differential-tested by G-CONF against the real patched
`set_ylim` endpoint pipeline. No changed op is inexpressible.
