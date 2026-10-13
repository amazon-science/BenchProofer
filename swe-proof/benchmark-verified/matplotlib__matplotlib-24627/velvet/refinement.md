# refinement.md — matplotlib__matplotlib-24627

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `clearAxes` `do` block and the deep `deparent` / `deparentAll` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The modeled change

The gold patch makes one edit in `lib/matplotlib/axes/_base.py`, inside the
per-axes clear routine:

```python
- self._children = []
+ old_children, self._children = self._children, []
+ for chld in old_children:
+     chld.axes = chld.figure = None
```

Pre-patch, clearing the axes discarded the axes' own reference to its children
(rebinding the collection to empty) but left each former child's `.axes` and
`.figure` attributes still pointing at the now-cleared axes/figure. The fix
deparents every formerly-attached child: it unsets BOTH links on each one.

## The deparenting abstraction (deep model of the changed op)

Lean is functional and has no aliasing or in-place attribute mutation, so the
"clear empties the collection but the artists keep their back-links" bug is
modeled at the *observable* level: an `Artist` is viewed through `hasAxes` /
`hasFigure` (whether `.axes` / `.figure` is set), and the result of clearing is
the same artists with both links unset:

```
deparent a            = { hasAxes := false, hasFigure := false }   -- both links unset
deparentAll []        = []
deparentAll (a :: as) = deparent a :: deparentAll as               -- every former child
```

The postcondition `out = deparentAll children` pins every returned artist to the
deparented state — `.axes` and `.figure` both unset — which only the fix
satisfies. This is the bug→fix delta the F2P test observes.

## A. The clear site — `_AxesBase.__clear` (`lib/matplotlib/axes/_base.py:1271`, body line 1311)

| # | Solution.lean impl op (`clearAxes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `children : List Artist` | `old_children` = `self._children` (the artists attached before the clear) | R | the attached-artist sequence ↔ `List Artist` (mapping.md §2). G-CONF bridges element-wise; the modeled observable per artist is the boolean set/unset status of its two links. |
| A2 | `result := []`; the backward `while` rebuilds it | `old_children, self._children = self._children, []` — snapshot the old children, empty the live collection | I + R | snapshotting the former children and starting an empty result is the rebind; order preserved. The emptied `self._children` collection is not itself observed by the spec (the contract is on the former children's links, mapping.md §2). |
| A3 | loop body `result := deparent a :: result` (over each `a := children[i-1]!`) | `for chld in old_children: chld.axes = chld.figure = None` | I | identical concrete op: visit each former child and unset both its links. The backward index walk reproduces the forward `for` order in the result (proven via `deparentAll_drop_step`). |
| A4 | `ensures out = deparentAll children` | the *fixed* property: every formerly-attached artist ends with `.axes is None` and `.figure is None` | R + I | the deparenting guarantee G-CONF checks by attaching real artists, clearing, and reading each one's `.axes`/`.figure`. R: per-artist link state ↔ `hasAxes`/`hasFigure`. |

`Solution_prepatch.lean` reproduces the bug — the loop returns each artist
**unchanged** (`result := a :: result`, no `deparent`) — and **fails**
`out = deparentAll children` (G-DIFF): a still-attached artist has
`hasAxes = true`/`hasFigure = true`, not the deparented `false`/`false`. The
residual goal is exactly `ensures_1: result_1 = deparentAll children`.

## B. No kind-3 (inexpressible-changed-op) steps; surrounding statements not modeled

Every modeled step is R or I. The operation that genuinely *changed* — unsetting
both links on each former child — is modeled **deeply** (the `deparent` /
`deparentAll` fold, steps A3/A4), not hidden behind an axiom about the function
under change. There is **no consumed axiom** and **no A-reference**: nothing here
is an unchanged opaque callee; the clear routine IS the modeled function, and its
fidelity is validated by G-CONF executing the real patched `clear()`.

The other statements in `__clear` (resetting `_mouseover_set`, `child_axes`, the
`None` sentinels, regridding, …) are untouched by the patch, observe nothing the
F2P test discriminates, and carry no bug→fix delta. They are deliberately omitted
from the model (mapping.md §3.2). No refinement row corresponds to them; there is
no "changed inexpressible op" being swept under an axiom.

## C. verify(Solution) ⇒ resolved

`clearAxes` verifies only if its output, observed per artist, equals the
fully-deparented sequence (A4) — i.e. every formerly-attached artist has both
its `.axes` and `.figure` links unset, which only the fix produces. By R
(attached-artist sequence ↔ `List Artist`, per-artist link state ↔
`hasAxes`/`hasFigure`) the verified method equals the patched `__clear` on the
tested inputs; by G-CONF the R/I transliteration of the deparenting loop agrees
with `patch.diff`'s behaviour (attach-then-clear-then-read) on ≥10⁵ inputs. There
are no A legs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement on the modeled site (the surrounding
clear statements being observationally inert for the contract) — and the gold
patch resolves (G-RESOLVE). The single residual trust point is the type bijection
in mapping.md §2 (checked falsifiably by G-CONF); there is no axiom trust point.
