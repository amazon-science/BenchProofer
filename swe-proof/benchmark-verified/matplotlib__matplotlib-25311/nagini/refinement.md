# refinement.md — matplotlib__matplotlib-25311

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_helper_state` impl region and the deep `read_surface` / `contains`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `Ensures`, **A-reference** where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change — `DraggableBase.__init__` + the `canvas` accessor (`lib/matplotlib/offsetbox.py`)

Gold hunks:
```
  def __init__(self, ref_artist, use_blit=False):
      self.ref_artist = ref_artist
      if not ref_artist.pickable():
          ref_artist.set_picker(True)
      self.got_artist = False
-     self.canvas = self.ref_artist.figure.canvas
      self._use_blit = use_blit and self.canvas.supports_blit
      self.cids = [ … _connect_picklable(…) … ]

+ # A property, not an attribute, to maintain picklability.
+ canvas = property(lambda self: self.ref_artist.figure.canvas)
```

The fix has two coupled parts: (i) **delete** the instance attribute assignment
`self.canvas = self.ref_artist.figure.canvas`, so the canvas is no longer placed
in the instance `__dict__` (the serialisable state); (ii) **add** a class-level
`property` so `self.canvas` still reads `self.ref_artist.figure.canvas` on demand.

| # | model.py impl op (`build_helper_state`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `surface, element_id, drag_flag, blit_flag, cid_pick, cid_release: int` | the live objects the helper touches: `self.ref_artist.figure.canvas`, `ref_artist`, `self.got_artist`, `self._use_blit`, the two `cids` from `_connect_picklable` | R | each runtime object ↔ a distinct integer object identity (`id()`); identity equality ↔ `int` equality (mapping.md §2). The `Requires(surface != …)` clauses encode that the canvas is a distinct object from each genuine attribute (true at runtime). |
| A2 | `read_surface(surface) == surface` (postcondition 1) and the `read_surface` getter returning `surface` | the `canvas` read accessor: post-patch `property(lambda self: self.ref_artist.figure.canvas)` (pre-patch the stored `self.canvas`) | A-reference | the *read* of `.canvas` is modelled deeply by `read_surface`: reading yields `ref_artist.figure.canvas`. The fix does not change the value read (only its storage); G-AX asserts `helper.canvas is fig.canvas` on the real library. |
| A3 | `state = [element_id, drag_flag, blit_flag, cid_pick, cid_release]` — the canvas is **omitted** from the serialisable state | deleting `self.canvas = …` so `canvas` is absent from `__dict__`, and exposing it via a class-level `property` (which lives on the class, never in any instance `__dict__`) | A-reference | the changed behaviour is modelled **deeply**: the serialisable state is exactly the genuine retained attributes, with the canvas absent. G-AX validates this against the real `DraggableBase`: `"canvas" not in vars(helper)`, no `__dict__` value is the canvas, and the genuine attributes remain. There is no consumed axiom. |
| A4 | postcondition `not contains(ToSeq(Result()), surface)` | the picklability property the fix establishes: a pickle of the figure (which reaches the helper through its `_connect_picklable` callbacks) emits no reference to the canvas | A-reference + I | `contains` is the deep membership model (mapping.md §2); the clause says the canvas identity is absent from the serialisable state. This is exactly the FAIL_TO_PASS assertion (`"FigureCanvasAgg" not in pickletools.genops(pkl)`); G-AX reproduces it end-to-end. |
| A5 | postconditions `contains(ToSeq(Result()), x)` for `x ∈ {element_id, drag_flag, blit_flag, cid_pick, cid_release}` | the genuine attributes the fix LEAVES in `__dict__` (`ref_artist`, `got_artist`, `_use_blit`, `cids`) | A-reference + I | pins that the fix removes *only* the canvas, not the real helper state — so the model is the genuine instance, not a vacuously-empty one. G-AX asserts each genuine attribute is present in `vars(helper)`. |

The discriminating content of the change — *the canvas is no longer part of the
helper's serialisable state* — lives in postcondition A4
(`not contains(ToSeq(Result()), surface)`). The pre-patch stored
`self.canvas` as an attribute; `model_prepatch.py` reproduces that (the canvas
identity appended to the serialisable `state`) and **fails** that exact
postcondition (model_prepatch.py:79), which is precisely the spec sensing the change
(G-DIFF). Read access (A2) and the retained attributes (A5) hold in BOTH the
patched and pre-patched skeletons — they are the faithfulness guards that stop a
"drop everything" cheat from satisfying A4 vacuously.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely
*changed* — moving the canvas from an instance attribute (in `__dict__`, hence
serialised) to a class-level `property` (not serialised) — is modelled
**deeply**: `build_helper_state` spells out the serialisable state with the
canvas omitted, and `read_surface` spells out the unchanged read. There is **no
consumed `@ContractOnly` axiom** the proof depends on; the changed `DraggableBase`
behaviour is the A-reference that G-AX validates the deep model against (it is
the function under change, so per directive 7 it is never axiomatized).

## C. verify(model) ⇒ resolved

`build_helper_state` verifies only if (A4) the canvas identity is absent from the
serialisable state AND (A2) read access still yields the canvas AND (A5) the
genuine attributes are retained. By R (live object ↔ int identity; `__dict__`
membership ↔ `contains`; the read accessor ↔ `read_surface`), a verifying model
is behaviourally the gold patch: it removes the stored `self.canvas` (A3/A4),
keeps `self.canvas` reading `ref_artist.figure.canvas` (A2), and leaves the
other attributes (A5). G-AX confirms the deep model equals the real
`DraggableBase` (read preserved, canvas absent from `__dict__`, attributes
retained) and reproduces the FAIL_TO_PASS observable (no `FigureCanvas` in the
figure's pickle stream). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited deep model —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: deep-model soundness (G-AX) and refinement fidelity (this document,
G-EQ).
