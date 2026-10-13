# refinement.md — matplotlib__matplotlib-23314

The operation-by-operation correspondence between `model.py`'s implementation
(the `render` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change — `Axes3D.draw` gains a visibility guard

Gold hunk (`lib/mpl_toolkits/mplot3d/axes3d.py`, in `draw`):
```
     def draw(self, renderer):
+        if not self.get_visible():
+            return
         self._unstale_viewLim()
         # draw the background patch
         ...
```

| # | model.py impl op (`render`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `self: Container` parameter | the `Axes3D` instance `self` | R | `Axes3D` ↔ `Container` carrying only the two read fields (mapping.md §2). |
| 2 | `sink: Sink` parameter | the `renderer` argument | R | the rendering backend ↔ `Sink` whose `work` tally is the cumulative draw effect (mapping.md §2). |
| 3 | `not self.visible` | `not self.get_visible()` | I + A-reference | identical boolean negation; `self.visible` is the boolean field read modeling the unchanged accessor `get_visible()` (mapping.md §1/§3). The accessor faithfulness (`get_visible() == stored flag`) is the **A-reference** validated by axiom_check.py (a), not a consumed axiom — it is a direct field read. |
| 4 | `if not self.visible: return` | `if not self.get_visible(): return` | I | the new guard — identical control flow: when not visible, return immediately, performing no further work. This is the entire content of the gold hunk. |
| 5 | `sink.work = sink.work + self.content` (the post-guard body) | `self._unstale_viewLim(); self.patch.draw(renderer); … ; super().draw(renderer)` (the whole rest of `draw`, lines 390-444) | R / A-reference | the unchanged render body is abstracted as delivering `self.content` units of work to the sink. The patch does not touch this body; it is modeled as the opaque non-negative quantity `content` rather than spelled out. Its only relevant property — that a visible pass delivers the body's work and an invisible pass delivers none — is what clauses (1)/(2) pin. Validated against the real render behavior by axiom_check.py (b) (**A-reference**). |

The discriminating content of the change — *no rendering work when not visible*
— lives in the guard (step 4) and is sensed by the postcondition
`Implies(not self.visible, sink.work == Old(sink.work))`. The pre-patch `draw`
has no guard and unconditionally runs the body; `model_prepatch.py` reproduces
that (drops step 4, keeping only the body of step 5) and **fails** exactly that
postcondition (when `content > 0`, an invisible container would still deliver
`content` work). That is the spec sensing the change (G-DIFF), and it mirrors
the F2P test `test_invisible_axes[png]`, which draws an invisible 3D axes and
asserts the output equals an empty reference figure (nothing drawn).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. There is **no consumed `@ContractOnly`
axiom**: the only callee the new code invokes is `get_visible()`, modeled
directly as the boolean field read `self.visible` (step 3, kind I — fully
expressible). The unchanged render body is abstracted as the opaque quantity
`content` (step 5, kind R), with its visible/invisible work behavior validated
against the real callee out-of-band by G-AX (an A-reference), never hidden
behind a consumed axiom. No operation that genuinely changed is left
inexpressible.

## verify(model) ⇒ resolved

`render` verifies only if, when `not self.visible`, the sink is left exactly as
on entry (clause 1, the new guard), and when visible the sink receives the
full `content` (clause 2, the unchanged body). By R (Axes3D↔Container,
renderer↔Sink, body↔content) and I (the boolean guard / early return), the
verified `render` IS the gold-patched `Axes3D.draw`: an invisible 3D axes draws
nothing (matching the empty reference figure of `test_invisible_axes`), a
visible one draws fully (preserving every P2P rendering test). The accessor and
the body's draw/no-draw behavior are confirmed against the real matplotlib code
by axiom_check.py (G-AX). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and audited behavioral
references — and the gold patch resolves (G-RESOLVE).
