# mapping.md — matplotlib__matplotlib-25311

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 430fb1db88843300fb4baae3edc499bbfe073b0c`, states the type
abstraction, and gives the provenance of the deep model (the changed behaviour
is modelled deeply; there is no consumed axiom).

Repo file under change: `lib/matplotlib/offsetbox.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_helper_state(surface, element_id, drag_flag, blit_flag, cid_pick, cid_release)` | `DraggableBase.__init__(self, ref_artist, use_blit=False)` — `lib/matplotlib/offsetbox.py:1503` (body 1504-1515) | the modeled changed function: the helper's set-up, which determines the helper's serialisable state (`__dict__`) and how `canvas` is read |
| `read_surface(surface)` *(deep model — A-reference)* | the `canvas` read accessor: pre-patch the stored attribute `self.canvas` (`offsetbox.py:1508`), post-patch the class-level descriptor `canvas = property(lambda self: self.ref_artist.figure.canvas)` (`offsetbox.py:1516-1517`) | pure spec: reading the helper's canvas yields `ref_artist.figure.canvas` (unchanged by the fix) |
| `contains(s, v)` | membership of an object identity in the helper's `__dict__` values, i.e. in the byte stream a pickle of the helper emits | pure spec: front-recursive sequence membership |
| `Result()` of `build_helper_state` (a `List[int]`) | the object identities held in the helper instance's `__dict__` — the helper's *serialisable* state (what `pickle.dumps` walks, since `DraggableBase` defines no `__getstate__`) | the serialisable state whose membership is constrained |

The pre-patch repo line the fix removes (for the refinement audit, not
referenced from the consumer spec view): `self.canvas = self.ref_artist.figure.canvas`
(`offsetbox.py:1508`). The fix adds the class-level descriptor
`canvas = property(lambda self: self.ref_artist.figure.canvas)`
(`offsetbox.py:1516-1517`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a live Python object held in the helper (`ref_artist`, the figure's `canvas`, the connection ids, the `got_artist`/`_use_blit` flags) | a distinct `int` object identity | each runtime object ↔ a distinct integer (its `id()`); object identity equality ↔ `int` equality. The `Requires(surface != …)` clauses encode that the drawing surface is a *distinct* object from each genuine attribute value (true at runtime: the canvas is not the artist, a flag, or a connection id). |
| the helper instance `__dict__` (its serialisable state; `DraggableBase` defines no `__getstate__`, so `pickle` serialises `vars(self)` verbatim) | `List[int]` of the object identities stored in that state; specification carried by `PSeq[int]` via `ToSeq` | a value `v` is reachable in the serialised state ↔ `contains(ToSeq(Result()), v)`. "the canvas object appears in the pickle stream" ↔ `contains(ToSeq(Result()), surface)`. |
| `self.canvas` read access (attribute pre-patch, `property` getter post-patch) | `read_surface(surface)` returning `surface` | both forms yield `self.ref_artist.figure.canvas`; the value read is identical before and after the fix (only its *storage* changes). |

The `cids` list, the `got_artist` bool and the `_use_blit` bool are abstracted
to single object identities — the model needs only their presence in the
serialisable state (they are genuine retained attributes), not their internal
structure. The blit-supported branch (`use_blit and self.canvas.supports_blit`)
and the two `_connect_picklable` calls are control flow whose *outputs* (the
flag, the two connection ids) are the retained attributes the model carries; the
fix does not change them, so they are represented as opaque retained identities.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `build_helper_state` / `read_surface` / `contains` ↔ real `DraggableBase` (A-reference)
**Subject:** `matplotlib.offsetbox.DraggableBase` set-up and its `canvas`
accessor. The changed behaviour — *the helper no longer stores the canvas as an
instance attribute; it exposes it as a class-level `property`* — is modelled
**deeply**: `build_helper_state` returns the serialisable state (the object
identities placed in `__dict__`) and `read_surface` returns the read value.
There is **no consumed `@ContractOnly` axiom**; the deep model is validated
against the real library out-of-band by `axiom_check.py` (G-AX).

Why a `property` removes the canvas from the serialisable state, and why read
access is unchanged:

* A plain attribute assignment `self.canvas = …` writes a key into the
  instance `__dict__`. Pickling a `DraggableBase` (which has no `__getstate__`)
  serialises `vars(self)` verbatim, so the canvas object is emitted into the
  stream. The draggable helper is reachable from the figure because its
  callbacks were registered with `_connect_picklable`, so a pickle of the
  figure reaches it. (`offsetbox.py:1508,1510-1515`.)
* A `property` is a **class-level data descriptor**; it lives on the class, not
  in any instance `__dict__`. So after the fix the canvas is absent from
  `vars(self)` and from the pickle stream, while `self.canvas` still evaluates
  the getter `lambda self: self.ref_artist.figure.canvas` and returns the same
  object as before. (`offsetbox.py:1516-1517`.)

The same `canvas = property(lambda self: self.<…>.figure.canvas)` idiom is used
elsewhere in matplotlib for the identical picklability reason, e.g.
`lib/matplotlib/lines.py:1583` (`canvas = property(lambda self: self.axes.figure.canvas)`)
— confirming this is the library's established representation of "a derived,
non-serialised canvas handle".

`Figure.__getstate__` independently `state.pop("canvas")` (`lib/matplotlib/figure.py:3159-3177`),
so the *figure's* own canvas does not leak; the only remaining leak path at
`base_commit` is the draggable helper's stored `self.canvas`, which is exactly
what this instance fixes.

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl region against the real
patched `DraggableBase.__init__` in-container (Agg backend), lowering live
objects to `id()` identities per the section-2 bridge: >= 1e5 probes (boundary
artist kinds x blit flags + randomized fuzz over rotating figures/artists),
pinned fuzz seed **25311**.

**Soundness check (G-AX):** `axiom_check.py` exercises the real, unmodified
matplotlib (Agg backend) in the official container. It (a) builds a real
`DraggableBase` over a figure artist and asserts `helper.canvas is fig.canvas`
(read preserved), `"canvas" not in vars(helper)` and no `__dict__` value is the
canvas (surface absent from serialisable state), and every genuine attribute
(`ref_artist`, `got_artist`, `_use_blit`, `cids`) is present; and (b) reproduces
the FAIL_TO_PASS observable end-to-end — pickles a figure with a draggable
legend and asserts no `FigureCanvas` class name appears in
`pickletools.genops(pkl)`. Exit 0 iff sound. It imports only `matplotlib` (the
library the patch changes) and stdlib.
