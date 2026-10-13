# refinement.md — matplotlib__matplotlib-26466

Operation-by-operation correspondence between the two `implementation_*` impls
(Solution.lean impl regions, plus the `StoredCoord` / `observe` retention model in
the `pure` region) and `patch.diff` (the POST-PATCH copy-on-store sites). Tags:
**R** type refinement, **A-consumed** proof uses an axiom, **A-reference** deep
model validated == real callee, **I** identical concrete op.

## The retention abstraction (deep model of the changed op)

Lean is functional and has no aliasing, so the reference-vs-copy distinction is
invisible at the pure value level. `Solution.lean` models the *observable*
contract directly. A retained coordinate is a `StoredCoord` (`snapshot x y` —
detached — or `reference` — bound to the source), and `observe out later` gives
what a reader sees as a function of the source container's CURRENT contents
`later`:

```
observe (snapshot x y) later = (x, y)     -- detached: ignores later
observe reference      later = later      -- aliased: reflects later
```

The postcondition `∀ later, observe out later = initial` pins the retained pair to
the construction-time components for EVERY possible later state of the source —
which only the `snapshot` (copy) behaviour satisfies. This is the bug→fix delta,
modeled deeply rather than asserted away.

## `implementation_freezeOffsetOrigin` ↔ `OffsetFrom.__init__`

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let x := initial.1` | `x, y = ref_coord` — read first component out of the source at construction time | I |
| 2 | `let y := initial.2` | `x, y = ref_coord` — read second component out of the source at construction time | I |
| 3 | `return StoredCoord.snapshot x y` | `self._ref_coord = x, y` — store the two read components as a fresh (detached) tuple | I + R |
| 4 | postcondition `∀ later, observe out later = initial` | the property the patch achieves: the stored coord no longer tracks later edits of the source array | R |

## `implementation_freezeAnchorPoint` ↔ `_AnnotationBase.__init__`

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let x := initial.1` | `x, y = xy` — read first component out of the source at construction time | I |
| 2 | `let y := initial.2` | `x, y = xy` — read second component out of the source at construction time | I |
| 3 | `return StoredCoord.snapshot x y` | `self.xy = x, y` — store the two read components as a fresh (detached) tuple | I + R |
| 4 | postcondition `∀ later, observe out later = initial` | same detachment property at the second site | R |

## Notes
- **Every step is R or I — no A.** The capture is modeled DEEPLY via the
  `StoredCoord` / `observe` retention; nothing is axiomatized. The `axioms`
  region is empty; **G-AX skips**.
- The R tag is the type refinement `Rat × Rat` ↔ a numpy 2D coordinate
  `(float, float)`, and the stored-attribute pair ↔ `StoredCoord`: the components
  are only read and stored verbatim, never computed on, so exact rationals are a
  faithful stand-in (mapping.md).
- The soundness-critical fact: the base_commit by-reference store
  (`self._ref_coord = ref_coord` / `self.xy = xy`) is `StoredCoord.reference`,
  whose `observe` reflects the source's later value; the patched store is
  `StoredCoord.snapshot`, whose `observe` ignores it. The universally-quantified
  `later` in the postcondition makes the aliasing observable in an immutable
  setting, and only the `snapshot` retention closes the proof.
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  each impl (returns a `StoredCoord`, observed under `later`) is diffed against a
  faithful replica of the post-patch capture driven through a real in-place
  mutation of a mutable `list`, over ≥1e5 fuzzed `(initial, later)` inputs, with
  the `reference` retention as the negative control.
- **G-DIFF**: two independently-fixed behaviours (the two stores), so two
  prepatch files. `Solution_prepatch_1.lean` reintroduces the `OffsetFrom` site
  behaviour (`return StoredCoord.reference`); `Solution_prepatch_2.lean` does the
  same at the `_AnnotationBase` site. Each carries the gold proof body, which
  fails to close against the `reference` impl (residual goal `later = initial`,
  not provable for arbitrary `later`).
