# refinement.md — matplotlib__matplotlib-24637

The operation-by-operation correspondence between `model.py`'s implementation
(the `draw_grouped_output` impl region, plus the deep `grouped_output` /
`id_attribute` / markup-constant model in the `pure` region) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — split into **A-consumed**, where the proof uses an axiom's
`Ensures`, and **A-reference**, where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change — `AnnotationBbox.draw` (`lib/matplotlib/offsetbox.py:1449`)

Gold hunks (two one-line insertions, framing the children draw):
```
  if not self.get_visible() or not self._check_xy(renderer):
      return
+ renderer.open_group(self.__class__.__name__, gid=self.get_gid())
  self.update_positions(renderer)
  ...
  self.offsetbox.draw(renderer)
+ renderer.close_group(self.__class__.__name__)
  self.stale = False
```

| # | model.py impl op (`draw_grouped_output`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `gid: List[int]` (non-empty) | `self.get_gid()` — the artist's group id (a `str`) | R | `str` ↔ `List[int]` of code points (mapping.md §2); `get_gid` is the unchanged accessor returning `self._gid`; the tested case sets a non-empty gid, so `len(gid) > 0`. |
| A2 | parameter `children: List[int]` | the renderer output produced by `self.arrow_patch.draw` / `self.patch.draw` / `self.offsetbox.draw` (`offsetbox.py:1456-1461`, unchanged) | R | the children's emitted markup ↔ an opaque `List[int]` content blob (mapping.md §2); the patch does not change what the children emit, only that a group encloses them. |
| A3 | the three opening loops build `id_attribute(gid)` = `group_open_prefix()` ++ `gid` ++ `attr_end()` = `<g id="` ++ gid ++ `"`, prepended to the result before anything else | `renderer.open_group(self.__class__.__name__, gid=self.get_gid())` inserted **before** the children draw | A-reference | the changed renderer call is modeled **deeply**: the markup constants (`<g id="`, `"`) are spelled out in the `pure` region and emitted by the verified loops; there is NO consumed `open_group` axiom. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) drives the real `RendererSVG.open_group` (→ `XMLWriter.start('g', id=gid)`, the truthy-gid branch) and asserts the emitted bytes begin with `<g id="GID"` (mapping.md §3.1). Note `start` leaves the start tag **unterminated** — the writer picks the terminator later, per A5. |
| A4 | the children loop appends `children` to the result unchanged, after the opening tag | `self.update_positions` + the three child `.draw` calls (unchanged) emit the body content **after** `open_group` | I (children) / R (carrier) | the body content is emitted between the open and close exactly as before; only its position relative to the new framing is what matters. The child draws are byte-for-byte the pre-patch draws (the patch inserts only the two framing lines). |
| A5 | the branch on `len(children)`: the self-closing loop appends `selfclose_end()` = `/>` and returns when no body content was emitted; otherwise the `tag_end()` loop appends `>` before the body and the closing loop appends `group_close()` = `</g>` after it | `renderer.close_group(self.__class__.__name__)` inserted **after** the children draw | A-reference | modeled deeply (the `>`, `/>`, `</g>` constants) and validated == the real `RendererSVG.close_group` (→ `XMLWriter.end('g')`) by G-AX. `end` is where the deferred terminator is chosen (`backend_svg.py:225-231`): if body markup was written it flushes `>` and then writes the end tag `</g>`; if **nothing** was written between start and end it writes `/>` and returns with no end tag. Both forms are reachable for this artist (mapping.md §3.1: an invisible frame plus content that draws nothing), so the impl branches the same way and G-AX samples both sides. |
| A6 | `result` returned (a `List[int]`) | (the renderer's accumulated output stream; `draw` returns `None`, mutating the renderer) | R | the renderer's output stream ↔ the returned `List[int]` (mapping.md §2); the F2P test reads the final SVG buffer and greps it, observing exactly the output content the model returns. |

The discriminating content of the change — the artist's group id reaching the
rendered output, as the id of a group element enclosing the children — lives in
postcondition (1) `ToSeq(Result()) == grouped_output(ToSeq(gid),
ToSeq(children))` and postcondition (2) (the gid-bearing id attribute occurs as a
contiguous run of the output). Clause (1) is form-exact: it demands `>` … `</g>`
on a non-empty body and `/>` with no end tag on an empty one, so it also rejects
a renderer-agnostic model that framed unconditionally. Clause (2) is stated over
`id_attribute` — the `<g id="GID"` run the two forms SHARE — so the "id reached
the output" obligation is carried across the whole admitted domain rather than
only the framed half. The pre-patch `draw` drew the children with **no
surrounding group**, so the output was just the children content and the gid
never appeared; `model_prepatch.py` reproduces that (returns `ToSeq(children)`)
and **fails** postcondition (1) — exactly the spec sensing the change (G-DIFF).
This is precisely what the F2P `test_annotationbbox_gid` observes:
`'<g id="a test for issue 20044">' in buf`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — wrapping the children draw in a gid-bearing group element — is
modeled **deeply** (the spelled-out markup constants `group_open_prefix` /
`attr_end` / `tag_end` / `selfclose_end` / `group_close`, the verified emission
loops, and the `len(children)` branch in `draw_grouped_output`, steps A3/A5), not hidden behind an axiom about the
function under change: there is **no consumed `open_group`/`close_group`
axiom**. The renderer's group primitives appear only as the **A-reference**
that G-AX validates the deep model against. There are no A-consumed axioms in
this bundle (the `axioms` region is empty).

## C. verify(model) ⇒ resolved

`draw_grouped_output` verifies only if its output is the children enclosed in a
group element carrying the gid, terminated in the form the dialect prescribes for
that body (postcondition 1), and only if the gid-bearing id attribute occurs in
the output (postcondition 2). By R (str ↔ List[int]; the renderer output stream ↔
the returned list) the verified output equals the sequence the gold-patched
`AnnotationBbox.draw` produces: `open_group(name, gid=get_gid())` writes
`<g id="GID"`, the children draw writes the body, and `close_group` terminates
the element — `>` … `</g>` when the body carried markup, `/>` alone when it did
not. By G-AX the deep model `grouped_output` / `id_attribute` equals the real
renderer's element writing in BOTH forms (A-reference), and G-CONF confirms the
same against the real patched `draw` including the empty-body class. On the F2P
configuration the body is non-empty (a visible frame patch emits), so the output
carries `<g id="a test for issue 20044">`, the exact string the F2P test asserts
present.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited A-reference — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (here the single A-reference, G-AX) and refinement fidelity (this
document, G-EQ).
