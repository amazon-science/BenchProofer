# refinement.md — matplotlib__matplotlib-26466

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `captureCoordA` / `captureCoordB` `do` blocks and the deep `StoredCoord` /
`observe` model) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The modeled change

The gold patch makes three edits in `lib/matplotlib/text.py`:

1. `OffsetFrom.__init__` — `self._ref_coord = ref_coord` becomes
   `x, y = ref_coord; self._ref_coord = x, y` (copy/decompose the input pair).
2. `_AnnotationBase.__init__` — `self.xy = xy` becomes
   `x, y = xy; self.xy = x, y` (same copy/decompose).
3. `OffsetFrom._get_scale` is inlined into `OffsetFrom.__call__`
   (`sc = self._get_scale(renderer)` → `scale = 1 if … else …`).

Edits (1) and (2) are the **behavioural fix** (the bug: a retained reference to
a mutable input array tracked later mutations). Edit (3) is a pure,
behaviour-preserving **refactor** (extract-method inverse): `_get_scale` is
called from exactly one place, returns `1.` for `"pixels"` and
`renderer.points_to_pixels(1.)` otherwise, and the inlined expression computes
the identical value. It changes no observable output and the F2P test does not
exercise a behavioural difference for it. It is therefore **not modeled** (no
`method`), is recorded as a no-op refactor in mapping.md §3.3, and carries no
refinement row. See §C.

## The retention abstraction (deep model of the changed op)

Lean is functional and has no aliasing, so the reference-vs-copy distinction is
invisible at the pure value level. `Solution.lean` models the *observable*
contract directly: a retained coordinate pair is a `StoredCoord`, and `observe`
gives what a reader sees as a function of the source container's **current**
contents `(a, b)`:

```
observe (snapshot x y) a b = (x, y)     -- detached: ignores later (a, b)
observe reference      a b = (a, b)     -- aliased: reflects later (a, b)
```

The postcondition `∀ a b, observe out a b = (coords[0]!, coords[1]!)` is the
directive-5 frame analogue: it pins the retained pair to the capture-time
components for **every** possible later state of the source — which only the
`snapshot` (copy) behaviour satisfies. This is the bug→fix delta.

## A. Site 1 — `OffsetFrom.__init__` (`lib/matplotlib/text.py:1373`, body line 1392)

Gold hunk:
```
- self._ref_coord = ref_coord
+ x, y = ref_coord  # Make copy when ref_coord is an array (and check the shape).
+ self._ref_coord = x, y
```

| # | Solution.lean impl op (`captureCoordA`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `coords : Array Int`, `require coords.size = 2` | `ref_coord` — a `(float, float)` pair / 2-element array | R | a two-component coordinate ↔ `Array Int`, `size = 2` (mapping.md §2). G-CONF bridges component-wise; the order-only copy semantics is integer-faithful (mapping.md §2 note). |
| A2 | `let x := coords[0]!`, `let y := coords[1]!` | `x, y = ref_coord` (tuple unpack) | I | identical concrete op: unpack the two components. |
| A3 | `return StoredCoord.snapshot x y` | `self._ref_coord = x, y` | I + R | storing the unpacked pair is the snapshot (detached) behaviour; `observe` models reading it back after later source mutation. R: the stored attribute pair ↔ `StoredCoord`. |
| A4 | `ensures ∀ a b, observe out a b = (coords[0]!, coords[1]!)` | the *fixed* property: the stored coord no longer tracks later edits of the input array | R + I | the detachment guarantee G-CONF checks by mutating the array post-construction and reading `_ref_coord`. |

`Solution_prepatch_1.lean` reproduces the bug (`return StoredCoord.reference`)
and **fails** `∀ a b, observe out a b = (coords[0]!, coords[1]!)` (G-DIFF) — the
`reference` case yields `(a, b)`, not the capture-time pair.

## B. Site 2 — `_AnnotationBase.__init__` (`lib/matplotlib/text.py:1454`, body line 1459)

Gold hunk:
```
- self.xy = xy
+ x, y = xy  # Make copy when xy is an array (and check the shape).
+ self.xy = x, y
```

| # | Solution.lean impl op (`captureCoordB`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `coords : Array Int`, `require coords.size = 2` | `xy` — a `(float, float)` pair / 2-element array | R | same bijection as A1 (mapping.md §2). |
| B2 | `let x := coords[0]!`, `let y := coords[1]!` | `x, y = xy` | I | identical unpack. |
| B3 | `return StoredCoord.snapshot x y` | `self.xy = x, y` | I + R | snapshot store; `observe` reads it back. |
| B4 | `ensures ∀ a b, observe out a b = (coords[0]!, coords[1]!)` | the fixed detachment property at the second site | R + I | G-CONF mutates the array post-construction and reads `.xy`. |

`Solution_prepatch_2.lean` reproduces the bug at this site and **fails** the
same clause (G-DIFF). Two prepatches because the two sites are fixed and
observed independently (the F2P `test_annotate_and_offsetfrom_copy_input`
exercises BOTH: `OffsetFrom(l, of_xy)` with `of_xy[:] = 1`, and
`annotate(xy=an_xy)` with `an_xy[:] = 2`).

## C. No kind-3 (inexpressible-changed-op) steps; the refactor is not modeled

Every modeled step is R or I. The operation that genuinely *changed* — copying
the input pair into the stored attribute — is modeled **deeply** (the
`StoredCoord` / `observe` abstraction, steps A3/B3), not hidden behind an axiom
about the function under change. There is **no consumed axiom** and **no
A-reference**: nothing here is an unchanged opaque callee; the changed
constructors ARE the modeled functions, and their fidelity is validated by
G-CONF executing the real patched constructors.

Edit (3), the `_get_scale` inline, is a behaviour-preserving refactor. It is
deliberately **omitted** from the model (mapping.md §3.3): it produces the
identical scale value (`1.` for `"pixels"`, `renderer.points_to_pixels(1.)`
otherwise) at the single call site, observes nothing the F2P test discriminates,
and modeling it would only add an unmodeled-renderer dependency without any
bug→fix delta to pin. No refinement row corresponds to it; there is no
"changed inexpressible op" being swept under an axiom.

## D. verify(Solution) ⇒ resolved

`captureCoordA` / `captureCoordB` verify only if their output, observed under
ANY later state of the source container, equals the capture-time pair (A4/B4) —
i.e. only the copy (snapshot) behaviour. By R (two-component coordinate ↔
`Array Int`, attribute-pair ↔ `StoredCoord`) the verified methods equal the
patched `__init__`s on the tested inputs; by G-CONF the R/I transliteration of
both sites agrees with `patch.diff`'s behaviour (mutate-then-read) on ≥10⁵
inputs. There are no A legs. Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement on the modeled sites
(the `_get_scale` refactor being observationally inert) — and the gold patch
resolves (G-RESOLVE). The single residual trust point is the type bijection in
mapping.md §2 (checked falsifiably by G-CONF); there is no axiom trust point.
