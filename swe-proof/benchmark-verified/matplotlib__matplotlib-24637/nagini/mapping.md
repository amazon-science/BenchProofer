# mapping.md — matplotlib__matplotlib-24637

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a9ba9d5d3fe9d5ac15fbdb06127f97d381148dd0`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `lib/matplotlib/offsetbox.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `draw_grouped_output(gid, children)` | `AnnotationBbox.draw(self, renderer)` — `lib/matplotlib/offsetbox.py:1449` | the modeled changed function: the container artist's draw method |
| `gid` parameter | `self.get_gid()` — `lib/matplotlib/artist.py:618` (returns `self._gid`, the group id set by `set_gid`) | the group id of the artist, fed to the renderer |
| `children` parameter | the renderer output produced by drawing the artist's children (`self.arrow_patch.draw`, `self.patch.draw`, `self.offsetbox.draw`) — `offsetbox.py:1456-1461` | the body content the child artists emit into the renderer |
| `group_open_prefix()` / `attr_end()` / `tag_end()` / `selfclose_end()` / `group_close()` | `RendererSVG.open_group(s, gid)` / `RendererSVG.close_group(s)` — `lib/matplotlib/backends/backend_svg.py:663-673`, via `XMLWriter.start`/`.end` — `backend_svg.py:155/208` | the markup the SVG renderer writes for a grouping element carrying a gid, in BOTH tag-termination forms |
| `Result()` | the renderer output sequence after `draw` returns | the rendered SVG content for this artist |

The pre-patch repo shape (for the refinement audit, not referenced from the
consumer spec view): `AnnotationBbox.draw` drew its children directly into the
renderer with NO surrounding grouping element, so the artist's group id never
entered the rendered output.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the renderer's accumulating SVG byte/character stream | `List[int]` of code points (specification over `PSeq[int]` via `ToSeq`); banned `str` indexing ⇒ `List[int]` | `out[k]` ↔ the k-th emitted code point; list `+`/`PSeq` `+` ↔ stream concatenation; `len` ↔ stream length |
| `self.get_gid()` — a `str` group id | `gid: List[int]` of its code points | `gid[k]` ↔ `ord(get_gid()[k])`; the tested case has a non-empty gid (the test calls `ab.set_gid("a test for issue 20044")`), so `gid` is required non-empty. `xml_safe(ToSeq(gid))` additionally requires the gid to hold none of `"` `&` `<` `>`: on that domain `_quote_escape_attrib`/`_escape_cdata` are the identity and the id attribute carries the code points verbatim, so the bridge is an equality. Off that domain the renderer escapes (`a&b` ⇒ `<g id="a&amp;b">`) or switches quotes (`a"b` ⇒ `<g id='a"b'>`), which the code-point carrier does not model — hence the restriction is ENCODED as a precondition rather than left in prose |
| the SVG group start tag's id attribute `<g id="…"` for a truthy gid | `id_attribute(gid)` = `group_open_prefix()` (the `<g id="` code points) ++ `gid` ++ `attr_end()` (the `"` code point) | the renderer writes `start('g', id=gid)` ⇒ literally `<g id="GID"`; the gid is interpolated verbatim into the id attribute (`backend_svg.py:665-666`, `XMLWriter.start` at `:155`). This run is common to BOTH termination forms, which is why the spec's clause (2) is stated over it |
| the start-tag terminator when body content follows, `>` | `tag_end()` ⇒ `opening_tag(gid)` = `id_attribute(gid) ++ tag_end()` = `<g id="GID">` | `XMLWriter.__flush` writes `">\n"` when the tag is open and data follows (`backend_svg.py:145-149`) |
| the start-tag terminator when NO body content is emitted, `/>` (and NO end tag) | `selfclose_end()` ⇒ `self_closing_tag(gid)` = `id_attribute(gid) ++ selfclose_end()` = `<g id="GID"/>` | `XMLWriter.end`: `if self.__data: self.__flush(indent); elif self.__open: self.__open = 0; self.__write("/>\n"); return` (`backend_svg.py:225-231`). With nothing written between `start('g')` and `end('g')` the element is self-closed and **no `</g>` is emitted at all** |
| the SVG group end tag `</g>`, emitted only in the framed form | `group_close()` (the `</g>` code points) | `close_group` ⇒ `writer.end('g')` ⇒ `</g>` when data was written (`backend_svg.py:232-234`) |
| drawing the three children (arrow_patch, patch, offsetbox) into the renderer | the opaque `children` content sequence | the children's own emitted markup; abstracted to one content blob — `draw` does not change what each child emits, only whether a gid-bearing group surrounds them |
| `renderer is not None` guard / `get_visible()` / `_check_xy()` early return | omitted (out of tested scope) | the F2P test draws a visible, in-bounds annotation; the early-return guards are unchanged by the patch and do not affect the gid behaviour. mapping note §3. |
| whether the child draws emitted any markup at all | `len(children) == 0` vs `> 0`, the branch in `grouped_output` | the renderer, not the artist, picks the termination form, and it picks on exactly this condition. The empty case is REACHABLE: `frameon=False` builds `self.patch` with `visible=frameon` and `Patch.draw` returns immediately when not visible (`patches.py`), an empty `DrawingArea` iterates no children, and `TextArea('')` hits `Text.draw`'s `if self.get_text() == '': return` — so nothing is written between the group open and close. Verified end-to-end against the real patched `draw` through `savefig`: that configuration yields `<g id="GID"/>` and the F2P-style grep for `<g id="GID">` FAILS on it. Both sides are therefore modeled and both are sampled by G-AX and G-CONF |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`. The five
literal markups (`<g id="`, `"`, `>`, `/>`, `</g>`) are modeled as fixed
code-point sequences whose CONTENT is not what the test discriminates on — the
test (`backend_svg.py::test_annotationbbox_gid`) greps for `<g id="<gid>">`,
i.e. the group start tag carrying the gid — so the load-bearing fact is that the
`gid` code points appear as the group's id, BEFORE the children content and
matched by the element's termination. The exact bytes of the markup constants are
fixed by the unchanged `RendererSVG.open_group`/`close_group` and the
`XMLWriter` beneath them (see §3).

**Why the model branches.** The writer defers a start tag's terminator until it
knows whether content followed, so a gid-bearing group element has TWO real
forms — `<g id="GID">` ++ body ++ `</g>` when the children emitted markup, and
`<g id="GID"/>` with no end tag when they emitted none. A model asserting the
framed form unconditionally would be UNFAITHFUL on the empty-body class (it would
predict `>` … `</g>` where the callee writes `/>`), and that class is reachable
for this artist (§2 last row). `grouped_output` therefore branches on
`len(children)`, and clause (2) of the postcondition is stated over
`id_attribute(gid)` — the `<g id="GID"` run COMMON to both forms — so that "the
gid reached the output" is asserted across the whole admitted domain rather than
only on the framed half. The form-specific structure stays pinned by clause (1),
which is a full equality.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `RendererSVG.open_group` / `close_group` (A-reference)
**Callee:** `RendererSVG.open_group(self, s, gid=None)` and
`RendererSVG.close_group(self, s)` — `lib/matplotlib/backends/backend_svg.py:663`:

```python
def open_group(self, s, gid=None):
    if gid:
        self.writer.start('g', id=gid)          # -> <g id="GID"   (terminator deferred)
    else:
        self._groupd[s] = self._groupd.get(s, 0) + 1
        self.writer.start('g', id="%s_%d" % (s, self._groupd[s]))

def close_group(self, s):
    self.writer.end('g')                         # -> '</g>'  OR  '/>' (see below)
```

`AnnotationBbox.draw` (post-patch) calls `renderer.open_group(self.__class__.__name__,
gid=self.get_gid())` before drawing its children and
`renderer.close_group(self.__class__.__name__)` after. When `get_gid()` is a
non-empty string (`if gid:` truthy — exactly the F2P case), `start` writes
`<g id="GID"` and interpolates the gid verbatim into the id attribute.

**The terminator is chosen by the writer, not the artist.** `XMLWriter` leaves
the start tag open (`self.__open = 1`) and decides how to close it later
(`backend_svg.py:127-234`):

```python
def __flush(self, indent=True):          # called when data / a nested tag follows
    if self.__open:
        self.__write(">\n" if indent else ">")

def end(self, tag=None, indent=True):
    ...
    if self.__data:      self.__flush(indent)     # framed form -> falls through to '</g>'
    elif self.__open:    self.__open = 0; self.__write("/>\n"); return   # SELF-CLOSING
    ...
    self.__write("</%s>\n" % tag)
```

So the element has two forms, and BOTH are real for this artist:

| children emitted | real output | model |
|---|---|---|
| some markup | `<g id="GID">` ++ body ++ `</g>` | `opening_tag(gid) ++ children ++ group_close()` |
| nothing at all | `<g id="GID"/>` (no end tag) | `self_closing_tag(gid)` |

**The empty case is reachable, not hypothetical.** `frameon=False` constructs
`self.patch` as `FancyBboxPatch(..., visible=frameon)` and `Patch.draw` returns
at once when not visible; an empty `DrawingArea` iterates no children;
`TextArea('')` hits `Text.draw`'s `if self.get_text() == '': return`;
`_bbox_artist` is a no-op with `DEBUG=False`. With no arrow, ZERO markup is
written between the group open and close. Driven end-to-end through the real
patched `AnnotationBbox.draw` + `savefig` in the instance image:

```
empty DrawingArea, frameon=False -> '<g id="a test for issue 20044"/>'  F2P-grep FAILS
TextArea(''),       frameon=False -> '<g id="a test for issue 20044"/>'  F2P-grep FAILS
empty DrawingArea, frameon=True  -> '<g id="a test for issue 20044">'   F2P-grep passes
DrawingArea+Circle, frameon=False -> '<g id="a test for issue 20044">'   F2P-grep passes
```

The markup is modeled DEEPLY (spelled-out fixed code-point sequences in the
`pure` region: `group_open_prefix` = `<g id="`, `attr_end` = `"`, `tag_end` = `>`,
`selfclose_end` = `/>`, `group_close` = `</g>`); there is **no consumed
`open_group` axiom**. The deep model is validated == the real SVG output
out-of-band by `axiom_check.py` (G-AX): it runs the real `XMLWriter.start('g',
id=gid)` / `.end('g')` over both body classes and asserts the emitted bytes equal
`grouped_output(gid, body)` — including 789 empty-body cases that exercise the
self-closing branch — and that `id_attribute(gid)` opens the output in every case.

**Flag dependencies (both ENCODED as preconditions, not asserted in prose):**
1. The gid path is taken iff `gid` is truthy (`if gid:`); `Requires(len(gid) > 0)`
   pins exactly that branch. With an empty gid the renderer falls back to the
   label-counter id (`"%s_%d"`); that branch is outside the tested scope.
2. The id attribute carries the gid verbatim only for gids free of `"` `&` `<`
   `>`; `Requires(xml_safe(ToSeq(gid)))` pins that domain. Confirmed against
   base_commit `_quote_escape_attrib`: `a"b` ⇒ `<g id='a"b'>` (quote switch),
   `a&b` ⇒ `<g id="a&amp;b">`, `a<b` ⇒ `<g id="a&lt;b">`. Escaping/quote-switching
   is unchanged by the patch and out of the code-point carrier's scope.

### 3.2 No consumed axioms
There are no `@ContractOnly` axioms in this bundle (the `axioms` region is
empty). The only callee the changed code invokes — the SVG renderer's element
writing — is modeled deeply and validated by G-AX as an **A-reference**, not
consumed. See `refinement.md`.
