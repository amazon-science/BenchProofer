# refinement.md — matplotlib__matplotlib-25311

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`initHandler` `do` block + the `Handler`/`Attr` deep model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

`patch.diff` is the gold patch **verbatim** (applies at base_commit, resolves —
G-RESOLVE).

## A. The constructor — `DraggableBase.__init__` (`lib/matplotlib/offsetbox.py:1503`)

Gold hunks:
```
         self.got_artist = False
-        self.canvas = self.ref_artist.figure.canvas
         self._use_blit = use_blit and self.canvas.supports_blit
         self.cids = [ ... _connect_picklable(...) ... ]
+    # A property, not an attribute, to maintain picklability.
+    canvas = property(lambda self: self.ref_artist.figure.canvas)
```

The change has two coupled halves: (1) DELETE the instance attribute
`self.canvas = self.ref_artist.figure.canvas` from `__init__` (so the live,
non-serializable surface is no longer placed into the instance's persisted
`__dict__`); (2) ADD a class-level `canvas = property(...)` that derives the
surface from `self.ref_artist.figure.canvas` on demand (so every existing
`self.canvas` read — in `__init__` and the drag callbacks — still works, and the
surface stays reachable without being persisted).

| # | Solution.lean impl op (`initHandler`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `attrs := Attr.refHandle :: attrs` | the instance retains `self.ref_artist` (set on entry to `__init__`, line 1504; unchanged) | **I** + R | identical: the reference to the dragged object is retained in the persisted state. `self.ref_artist` ↔ `Attr.refHandle` (mapping.md §2). It is serializable on its own (mapping.md §3) — storing it does not embed the surface. |
| A2 | `attrs := Attr.flag false :: attrs` | `self.got_artist = False` (line 1507, unchanged) | **I** + R | identical: a `False` status flag retained. `False` ↔ `Attr.flag false`. |
| A3 | `attrs := Attr.flag (useBlit && supportsBlit) :: attrs` | `self._use_blit = use_blit and self.canvas.supports_blit` (line 1509, unchanged — note its `self.canvas` read now resolves through the new property) | **I** + R | identical: the effective blit mode bit retained. `use_blit and canvas.supports_blit` ↔ `useBlit && supportsBlit` (mapping.md §2). |
| A4 | `attrs := Attr.registration :: attrs` | `self.cids = [ self.canvas.callbacks._connect_picklable(...) ]` (lines 1510-1516, unchanged; the registrations are picklable by construction) | **I** + R | identical: the (serializable) event registrations retained. `self.cids` ↔ `Attr.registration` (mapping.md §2). |
| A5 | the surface is NOT pushed onto `attrs` (no `Attr.surface ::`) | DELETED line `self.canvas = self.ref_artist.figure.canvas` (was line 1508 pre-patch) | **I** | the CHANGED op, modeled deeply: the surface is no longer placed into the persisted state. The buggy line's effect (`Attr.surface ∈ attrs`) is exactly what is removed. This is the picklability fix; `Solution_prepatch.lean` reproduces the buggy line (pushes `Attr.surface`) and fails the `persistable` clause. |
| A6 | `surfaceFromRef := true` in the returned `Handler` | ADDED `canvas = property(lambda self: self.ref_artist.figure.canvas)` (lines 1516-1517) | **I** + R | the CHANGED op, modeled deeply: the class exposes the surface as a derived accessor over the retained reference, so the surface is obtainable on demand without being persisted. "class defines `canvas` as a derived accessor over `self.ref_artist`" ↔ `surfaceFromRef = true` (mapping.md §2). |

Discriminating content of the change — the surface must NOT appear in the
persisted state, yet must remain reachable — lives in clause `persistable out`
(`Attr.surface ∉ out.attrs`) coupled with `surfaceReachable out`. The pre-patch
constructor stored the surface directly (`self.canvas = ...`), so its persisted
state embedded `Attr.surface`; `Solution_prepatch.lean` reproduces that and
**fails** `persistable out` (G-DIFF: goal reduces to `False`).

## B. No A (axiom) steps; no kind-3

There are no consumed axioms and no A-reference deep models: the change touches
no algorithmic callee whose contract the proof must borrow. The single structural
fact relied on — a stored reference handle is serializable while the live surface
is not — is encoded in the type model (`Attr.refHandle ≠ Attr.surface`,
mapping.md §3), an environment property of the **unchanged** figure-pickling
machinery (`Figure.__getstate__` drops the canvas), not a contract this proof
consumes. So `axioms = []` and there is no G-AX obligation.

The changed ops (A5 delete-attribute, A6 add-property) are modeled **deeply** as
the construction of `out.attrs` and `out.surfaceFromRef` — both **I** under the
type bijection. No operation is a *changed op Velvet cannot express*: the whole
change is structural and is captured exactly by membership/absence in `out.attrs`
plus the `surfaceFromRef` bit. No kind-3 steps.

## C. verify(Solution) ⇒ resolved; prepatch fails

`initHandler` verifies only if BOTH `persistable out` (the surface is absent from
the persisted state — A5) and `surfaceReachable out` (the surface is obtainable
from the retained reference — A6, grounded by `Attr.refHandle ∈ out.attrs`) hold,
plus the full persisted working inventory is present: the retained reference
(A1), the cleared drag-status bit `Attr.flag false` (A2), the effective mode bit
(A3), and the event registrations `Attr.registration` (A4), and no OTHER
boolean status bit is retained (`flagsExact out (useBlit && supportsBlit)` —
the status-bit inventory is closed: every retained `Attr.flag b` has
`b = false ∨ b = useBlit && supportsBlit`, matching the real constructor which
sets exactly two boolean attributes, mapping.md §4). By R (mapping.md §2)
the verified handler equals: an instance whose `__dict__` carries `ref_artist`,
`got_artist = False`, `_use_blit`, and the callback ids but NOT the canvas, with
the class exposing `canvas` as a derived property — exactly the gold post-patch
object. A stripped constructor omitting the registrations or the cleared status
bit does not verify (the inventory clauses reject it), and neither does one
that adds or substitutes a status bit the real constructor does not set
(`flagsExact` rejects it: e.g. an unconditional `Attr.flag true`, or a
disjunction in place of the conjunction, fails on the inputs where the extra
bit differs from both pinned bits).

The F2P test `test_complete[png]` asserts
`"FigureCanvasAgg" not in [arg for op,arg,pos in pickletools.genops(pkl)]` after
pickling a figure containing a `draggable=True` legend — i.e. no rendering
surface appears in the serialized stream: the `persistable` clause. It then calls
`loaded.canvas.draw()`, which requires the surface to remain reachable through
the unpickled object: the `surfaceReachable` clause. The PASS_TO_PASS pickle
suite requires the rest of the persisted state to be intact (A1-A4). All are
pinned by the spec.

The prepatch retains the surface directly (`Attr.surface :: attrs`) and provides
no derived accessor (`surfaceFromRef := false`): it satisfies `surfaceReachable`
(via the directly retained surface) but violates `persistable`, so `prove_correct`
fails on exactly the discriminating clause:
```
case «ensures_4: persistable out»
useBlit supportsBlit : Bool
⊢ False          -- unprovable: the surface is in the persisted state
```
This is the precise bug the issue describes ("Unable to pickle figure with
draggable legend … cannot pickle 'FigureCanvasQTAgg' object"). G-DIFF passes.

G-CONF is `conf_skip=true`: the impl region constructs an abstract object-state
model whose only observable (a surface reference appearing / not appearing in a
real pickle stream) materializes solely inside the F2P integration test
(build a figure + draggable legend, pickle it), not as a DB-free, input-dependent
R/I shadow fuzzable over ≥10⁵ inputs (mapping.md §5). No axioms ⇒ no G-AX.
Soundness is carried by G-VERIFY + G-DIFF + G-RESOLVE — the
`django__django-11179` state-construction precedent.
