# refinement.md — matplotlib__matplotlib-26291

The operation-by-operation correspondence between `model.py`'s implementation
(the `call` impl region) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

Gold hunk (`lib/mpl_toolkits/axes_grid1/inset_locator.py`,
`AnchoredLocatorBase.__call__`):
```
     def __call__(self, ax, renderer):
+        if renderer is None:
+            renderer = ax.figure._get_renderer()
         self.axes = ax
         bbox = self.get_window_extent(renderer)
         px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer)
```

The change inserts a guard, BEFORE the measurement, that resolves a usable
drawing context from the host axes when none was supplied — so the subsequent
window-extent + offset measurement is always handed a present renderer instead
of being threaded `None` (which, with no usable fallback on this object, was the
`AttributeError`).

## Operation correspondence

| # | model.py impl op (`call`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| 1 | `eff = renderer` | the `renderer` parameter of `__call__` | R | a renderer object / `None` ↔ `Optional[int]` (mapping.md §2); only present-vs-absent and the threaded renderer's identity are observed. |
| 2 | `if eff is None: eff = axes_context(ax)` | `if renderer is None: renderer = ax.figure._get_renderer()` (the inserted hunk) | A-consumed + I | THE change. The `is None`-guarded reassignment is the identical control flow (I); the right-hand side `ax.figure._get_renderer()` is the unchanged callee `axes_context` (A-consumed — the proof uses its `Ensures(Result() > 0)` to discharge the no-renderer branch's measurement precondition `context > 0` and hence the postcondition `measured_with > 0`). |
| 3 | `measure(self, eff)` | `bbox = self.get_window_extent(renderer)` then `px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer)` (`inset_locator.py:73-74`) | R | the window-extent + offset measurement against the (now resolved) renderer ↔ one `measure(self, eff)` call. The measurement's *occurrence against a present context* `eff` is the load-bearing observable; modeled deeply (the `measurements`/`measured_with` counters), NOT axiomatized. `get_window_extent`/`get_offset` require a usable renderer — modeled by `measure`'s `Requires(context > 0)`; passing the absent context makes them unreachable (the real `AttributeError`). |
| (—) | `self.axes = ax` | `self.axes = ax` (`inset_locator.py:72`) | I (omitted) | a book-keeping assignment the F2P test never observes; orthogonal to the fix and dropped from the model (mapping.md §2). |

## The discriminating clause (G-DIFF)

The whole change is step 2 (the inserted renderer-resolution guard). The spec
senses it through the no-renderer postcondition clauses of `call`:

```
Ensures(self.measurements == 1)
Ensures(self.measured_with > 0)
Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
```

The bug is a *presence* failure: pre-patch threads the absent context into the
measurement on the no-renderer path. The discriminating obligation is "the
measurement is performed against the present context the HOST AXES resolves
even when none was supplied" (`measured_with == axes_context(ax)`), which
subsumes presence (`axes_context` Ensures `Result() > 0`).

The no-renderer clause is pinned to `axes_context(ax)` — not presence-only —
because presence-only was demonstrated too weak: the G-PANEL-1 audit built a
verifying same-spec impl whose faithful patch substitutes a fresh
`RendererAgg(100, 100, 72)` for the resolved renderer. That substitute passes
the thin F2P (`test_inset_axes_tight` only checks the save does not raise) but
measures the window-extent/offset geometry against a context whose dpi/size
need not match the figure's actual renderer, so the computed inset placement
diverges from the gold patch whenever the figure's dpi differs from the
substitute's — behaviourally unequal to gold on the very path under repair.
Pinning to the opaque `axes_context(ax)` states exactly the gold behaviour
("resolve the context from the host axes") without naming the repo callee
(`ax.figure._get_renderer()` appears only here and in mapping.md, never in the
spec view; the axiom stays opaque with only `Ensures(Result() > 0)`).

`model_prepatch.py` (byte-identical spec) omits the resolution: on the
`renderer is None` branch it threads the absent context (the `0` sentinel) into
the measurement — faithfully modeling the pre-patch passing `None` into
`get_window_extent`, whose own-figure fallback is unusable (`self.figure is
None`). It therefore **fails** `measure`'s precondition `context > 0` on that
branch (verifier: `model_prepatch.py:120 — Assertion (context > 0) might not
hold`), which is exactly the F2P observation `test_inset_axes_tight`: the
tight-bbox save path invokes the locator with `renderer=None` and must not raise
(pre-patch: `AttributeError`). The present-renderer branch is unaffected (it
verifies in both), so the single failing prepatch isolates the one fixed
behaviour — the no-renderer path.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— resolving a usable renderer when none was supplied, then measuring against it
— is modeled **deeply** (step 2's control flow + step 3's measurement against a
present context, via the `measurements`/`measured_with` observables and
`measure`'s `Requires(context > 0)`), NOT hidden behind an axiom about the
function under change. The lone consumed axiom (`axes_context`) covers an
**unchanged** callee (`ax.figure._get_renderer()`) the new guard invokes; there
is no A-reference and no dead axiom.

## verify(model) ⇒ resolved

`call` verifies only if it performs the measurement exactly once
(`measurements == 1`) against a PRESENT context (`measured_with > 0`) that is the
supplied renderer when one was supplied (`renderer is not None ⇒ measured_with
== renderer`) and is exactly the host-axes-resolved context when none was
supplied (`renderer is None ⇒ measured_with == axes_context(ax)`). On the
no-renderer branch the only way to discharge that equality is to source the
context from the A-consumed axiom `axes_context(ax)` itself (`axes_context` is
`@Pure`, so the pinned value is well-defined; being opaque, no other expression
— in particular no substitute constant — can be proven equal to it). A wrong
impl cannot satisfy `measure`'s `Requires(context > 0)` while threading the
absent context, so the prepatch fails exactly there; a substitute-source impl
fails the pinned equality instead. By R (renderer object ↔ `Optional[int]`; one
window-extent+offset measurement ↔ one `measure` call) and the A-consumed axiom
(`ax.figure._get_renderer()` always yields a present renderer — G-AX confirms it
on real axes, incl. the inset regression path), the verified callable equals the
gold patch on the tested input: invoked with `renderer=None` by the tight-bbox
save path, it resolves a present renderer and measures against it rather than
raising. The gold patch resolves (G-RESOLVE).
Trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
