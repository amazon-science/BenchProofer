# refinement.md — matplotlib__matplotlib-24637

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `groupedRender` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (a deep model validated == a real callee
by G-AX), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The composite-render command stream — `AnnotationBbox.draw` (`lib/matplotlib/offsetbox.py:1449`)

Gold hunks:
```
         if not self.get_visible() or not self._check_xy(renderer):
             return
+        renderer.open_group(self.__class__.__name__, gid=self.get_gid())
         self.update_positions(renderer)
         ...
         self.offsetbox.draw(renderer)
+        renderer.close_group(self.__class__.__name__)
         self.stale = False
```

The patch wraps the composite's existing drawing body (the child renderings)
between a `renderer.open_group(..., gid=self.get_gid())` call and a matching
`renderer.close_group(...)` call. The grouping element carries the artist's own
identifier, so the back end (e.g. SVG) emits `<g id="{gid}"> … </g>` around the
whole composite and the identifier reaches the output.

| # | Solution.lean impl op (`groupedRender`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `trace := [RenderCmd.beginGroup gid]` (the stream opens with `beginGroup gid`; `out.head? = some (beginGroup gid)`) | `+ renderer.open_group(self.__class__.__name__, gid=self.get_gid())` inserted before the body | R + I | identical op under the command↔call refinement (mapping.md §2): the first command handed to the back end is a group-open carrying exactly `self.get_gid()`. `gid : Option String` ↔ the `gid=` argument; the constant label `self.__class__.__name__` is abstracted (does not affect the tested behaviour). |
| A2 | `trace := trace ++ children` (the children's stream, verbatim and in order; `out.tail` begins with `children`) | the unchanged body: `update_positions`, `arrow_patch.draw` (if any), `patch.draw`, `offsetbox.draw` | R + I | the children's command stream is unchanged by the patch — neither added to, removed, nor reordered — so it is reproduced verbatim. Modeled as the opaque `children : List RenderCmd` carried through unchanged (mapping.md §2,§3). |
| A3 | `trace := trace ++ [RenderCmd.endGroup]` (the stream ends with the matching close; `out.getLast? = some endGroup`) | `+ renderer.close_group(self.__class__.__name__)` inserted after the body | R + I | identical op: the last command is the matching group-close, so the open/close bracket the entire body as one enclosing unit. |

The discriminating content of the change — the composite's stream is now
*enclosed* by a grouping element carrying the artist's own identifier — lives in
`out.head? = some (RenderCmd.beginGroup gid)` together with
`out.getLast? = some RenderCmd.endGroup` and the full
`out = beginGroup gid :: (children ++ [endGroup])`. The pre-patch code emits only
the children (`children`, no enclosing group); `Solution_prepatch.lean`
reproduces that (`trace := [] ++ children`) and **fails** the postconditions —
verified: it leaves `([] ++ children).head? = some (RenderCmd.beginGroup gid)`,
`([] ++ children).getLast? = some RenderCmd.endGroup`,
`([] ++ children).tail = children ++ [RenderCmd.endGroup]`,
`([] ++ children).length = children.length + 2`, and the full-equality goal all
unsolved (G-DIFF). The F2P test (`test_annotationbbox_gid`) sets a non-`None`
identifier and asserts `<g id="a test for issue 20044">` appears in the SVG —
i.e. it observes exactly `out.head? = some (beginGroup (some "…"))`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operations that genuinely *changed* — the two
inserted grouping commands — are modeled **directly and concretely**
(`beginGroup gid` at the head, `endGroup` at the tail), not hidden behind any
axiom. There are no axioms in this bundle: the change inserts two command
emissions around the composite's existing body, so there is no unchanged callee
whose *contract* is consumed and no deep model to validate against a real callee.
`renderer.open_group`/`close_group` are unchanged command sinks (their effect IS
the modeled `beginGroup`/`endGroup` command, mapping.md §3); the child
renderings are unchanged and carried through verbatim as `children`. There is no
A-consumed and no A-reference row, and **no `axiom_check.py`** (nothing for G-AX
to run).

## C. verify(model) ⇒ resolved

`groupedRender` verifies only if its output opens with `beginGroup gid` (A1,
`out.head? = some (beginGroup gid)`), ends with the matching `endGroup` (A3,
`out.getLast? = some endGroup`), and carries the children through unchanged and
in order between them (A2, `out.tail = children ++ [endGroup]`, equivalently the
full `out = beginGroup gid :: (children ++ [endGroup])`). Both `gid` and
`children` are read-only — neither is a `mut` parameter; `gid` is reproduced
exactly in the opening command and `children` exactly in the interior
(directive 5: a wrong impl cannot satisfy the postconditions while inventing a
different identifier, dropping the enclosing group, or altering/reordering the
children, because each is pinned structurally). The result is grounded in the
inputs (`out = beginGroup gid :: (children ++ [endGroup])`), not in an ungrounded
oracle (directive 8): there is no answer-key to echo. By R (back-end command ↔
call, `Option String` gid ↔ the `gid=` argument, `List RenderCmd` ↔ the ordered
stream) the verified stream equals the post-patch command stream of
`AnnotationBbox.draw`, which the SVG back end turns into `<g id="{gid}"> … </g>`
around the composite. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this document, G-EQ;
mechanically re-checked by G-CONF, which drives the REAL gold-patched
`AnnotationBbox.draw` against a recording renderer over F2P + boundary + fuzzed
identifiers, 0 disagreements); there is no axiom-soundness trust point because
there are no axioms.
