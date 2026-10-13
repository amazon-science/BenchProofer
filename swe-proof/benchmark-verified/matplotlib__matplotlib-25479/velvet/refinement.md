# refinement.md — matplotlib__matplotlib-25479

Operation-by-operation correspondence between `Solution.lean`'s two impl regions
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** / **A-reference** (none here), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative and faithfulness are audited by **G-EQ**. There are no
A-tagged ops, so G-AX is vacuous (mapping.md §3). Claim: any impl verifying
against this frozen spec, refined per the maps below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The registration site — `ColormapRegistry.register()` (`lib/matplotlib/cm.py:153`)

Gold hunk:
```
  self._cmaps[name] = cmap.copy()
+ # ... the registered name should be the colormap's own name
+ if self._cmaps[name].name != name:
+     self._cmaps[name].name = name
```

| # | Solution.lean impl op (`registeredColormap`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `cmap : Colormap`, `name : String` | `cmap` arg of `register`, the resolved `name` | R | `Colormap` object ↔ the modeled `Colormap` structure (mapping.md §2); `str` ↔ `String`. |
| A2 | `let mut stored := cmap` | `self._cmaps[name] = cmap.copy()` | R + I | `copy()` is a content copy preserving the modeled fields (mapping.md §2); modeled as identity on `name`/`extendStyle`/`lookupTable`. `stored` is the registry's stored value. |
| A3 | `if stored.name ≠ name then stored := { stored with name := name }` | `if self._cmaps[name].name != name: self._cmaps[name].name = name` | I | byte-for-byte the same guarded field assignment: stamp the stored colormap's advertised name with the registration name when they differ. |
| A4 | `return stored`; `ensures out.name = name` ∧ extendStyle/lookupTable preserved | the post-state of `self._cmaps[name]` | R | the stored colormap advertises `name`; its content is unchanged (mapping.md §2). `test_set_cmap_mismatched_name` asserts `cmap_returned.name == "wrong-cmap"`. |

Discriminating content of the change — the stored colormap's `.name` becomes the
registration name even when the object advertised a different name — lives in the
`ensures out.name = name` clause. `Solution_prepatch_1.lean` stores `cmap`
unchanged and **fails** `out.name = name` (G-DIFF) exactly when `cmap.name ≠ name`.

## B. The equality site — `Colormap.__eq__()` (`lib/matplotlib/colors.py:776`)

Gold hunk:
```
- if (not isinstance(other, Colormap) or self.name != other.name or
+ if (not isinstance(other, Colormap) or
          self.colorbar_extend != other.colorbar_extend):
      return False
  ... return np.array_equal(self._lut, other._lut)
```

| # | Solution.lean impl op (`colormapsEqual`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `a b : Colormap` | `self`, `other` | R | `Colormap` ↔ structure (mapping.md §2). |
| B2 | (no node) | `not isinstance(other, Colormap)` guard | R | both F2P operands are `Colormap`; the guard never fires on the tested inputs (mapping.md §2 — object-kind precondition modeled away). |
| B3 | `decide (a.extendStyle = b.extendStyle)` | `self.colorbar_extend != other.colorbar_extend` (negated into the conjunction) | I | the surviving end-style equality; `Bool` ↔ `bool` (mapping.md §2). |
| B4 | `decide (a.lookupTable = b.lookupTable)` | `np.array_equal(self._lut, other._lut)` (incl. the size-mismatch path) | R + I | `np.array_equal` ↔ `=` on `List (List Int)` (mapping.md §2): equal iff equal shape and elements, so different sizes ⇒ `≠`. |
| B5 | result `out`; `ensures out = colormapEqSpec a b` | the boolean `__eq__` returns | I | conjunction of B3 ∧ B4 — name-independent. |

Discriminating content of the change — equality NO LONGER depends on `name` —
lives in `colormapEqSpec` omitting `a.name = b.name`. `Solution_prepatch_2.lean`
re-adds `decide (a.name = b.name)` and **fails** `out = colormapEqSpec a b`
(G-DIFF) exactly when the names differ but the content agrees (the
`cm_copy.name = "Test"; assert cm_copy == cmap` case of `test_colormap_equals`).

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. Both changed operations are spelled out **directly** — a
guarded field assignment (site A) and a field-wise boolean conjunction (site B).
Neither calls a foreign function whose contract the proof must assume: there is
no consumed axiom and no A-reference deep model (mapping.md §3). The
`np.array_equal` on the LUT (B4) is a structural-equality refinement of a
`List (List Int)`, not an axiomatized callee — G-CONF transliterates it directly.

## D. verify(Solution) ⇒ resolved

`registeredColormap` verifies only if its result advertises the registration
name (A4) while preserving content; `colormapsEqual` verifies only if its verdict
is the name-independent field conjunction (B5). Verification runs under
**total correctness** (`loom.semantics.termination "total"`, mapping.md §0), so
a verifying impl must also TERMINATE — a divergent same-spec impl (whose
faithful refinement would hang the F2P tests) does not verify; there is no
vacuous-satisfaction escape. By R (`Colormap` ↔ structure,
`copy` content-identity, `bool` ↔ `Bool`, `np.array_equal` ↔ list `=`) the two
verified methods equal the patched `register` post-state and the patched
`__eq__` on the tested inputs; by G-CONF the R/I transliterations agree with
`patch.diff`'s behaviour on ≥10⁵ inputs. There are no trust points beyond
refinement fidelity (this doc, G-EQ + G-CONF): no axiom soundness obligation
(G-AX vacuous). Therefore a model satisfying this spec, refined by the maps
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE).
