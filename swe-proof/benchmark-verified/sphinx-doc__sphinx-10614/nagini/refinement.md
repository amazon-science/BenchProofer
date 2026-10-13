# refinement.md — sphinx-doc__sphinx-10614

The operation-by-operation correspondence between `model.py`'s implementation
(the three implemented functions and the deep models in the `pure` region) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`Ensures`, **A-reference** where a deep model is validated == the real
operation by `axiom_check.py` / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There are **no consumed `@ContractOnly` axioms** (the `axioms` region is
empty): every changed operation is modelled deeply as plain sequence
arithmetic. The only A-references are the three deep models, each checked
== its real Python string operation by `axiom_check.py`.

## Gold hunk (`sphinx/ext/inheritance_diagram.py`, `html_visit_inheritance_diagram`)

```
   for child in pending_xrefs:
       if child.get('refuri') is not None:
-          if graphviz_output_format == 'SVG':
-              urls[child['reftitle']] = "../" + child.get('refuri')
+          # Construct the name from the URI if the reference is external via intersphinx
+          if not child.get('internal', True):
+              refname = child['refuri'].rsplit('#', 1)[-1]
           else:
-              urls[child['reftitle']] = child.get('refuri')
+              refname = child['reftitle']
+
+          urls[refname] = child.get('refuri')
       elif child.get('refid') is not None:
           if graphviz_output_format == 'SVG':
-              urls[child['reftitle']] = '../' + current_filename + '#' + child.get('refid')
+              urls[child['reftitle']] = current_filename + '#' + child.get('refid')
           else:
               urls[child['reftitle']] = '#' + child.get('refid')
```

Post-patch line numbers used below: `:409` the image-format read
(`graphviz_output_format = …upper()`), `:410` `current_filename`, `:417` the
external refname, `:421` the `refuri` link value, `:423-424` the vector `refid`
link value, `:425-426` the raster `refid` link value.

## 0. The image format is a modelled input, not a context

`vector_format` ↔ `graphviz_output_format == 'SVG'` (`:409`), tag **R** (a `str`
comparison ↔ a `bool`; `axiom_check.py` covers both values, and
`conformance_check.py` drives the real function with `'svg'`, `'SVG'`, `'Svg'`,
`'png'`, `'PNG'`, `'pdf'` so the `.upper()` bridge is exercised).

This parameter exists because the gold change is not confined to the vector
arm. In the `refuri` case it deletes the format branch, so `:421` fixes the
link value for BOTH formats; in the `refid` case it edits the vector arm and
leaves the raster arm standing at `:425-426`. Both values of the observable are
reachable (`graphviz_output_format` defaults to `'png'`) and both are tested —
F2P `test_inheritance_diagram_svg_html` for the vector format, P2P
`test_inheritance_diagram_png_html` for the raster one. A spec that pinned only
the vector values would therefore under-determine the change: see §F.

## A. Behaviour 1 — the destination-URI link (`url_for_destination`)

Models the `refuri` branch value. Gold change: the pre-patch SVG case
`"../" + child.get('refuri')` and the pre-patch non-SVG case
`child.get('refuri')` collapse into the single format-independent
`urls[refname] = child.get('refuri')` (`:421`) — i.e. the link is the
destination URI itself, with no `"../"` prefix, in either format.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `dest_uri: List[int]` | the `str` `child.get('refuri')` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | param `vector_format: bool`, unused by the value | `:421` is not inside any `if graphviz_output_format` test | R + I | the gold statement's value does not depend on the format, so the model's value does not either; the parameter is present so the postcondition QUANTIFIES over the format instead of leaving one arm unstated. |
| A3 | copy loop building `result` with `ToSeq(result) == ToSeq(dest_uri)` | `child.get('refuri')` as the assigned value | A-reference | the changed value expression is modelled deeply (the identity on the URI); G-AX checks `url_for_destination(dest_uri, vec) == dest_uri` against `:421` for both `vec` values. |
| A4 | `Ensures(has_scheme(dest_uri) == has_scheme(Result()))` | (semantic consequence: an absolute URL keeps its scheme) | A-reference + I | scheme-membership is preserved because the value is the identity; G-AX checks `has_scheme(s) == ('://' in s)`. |

Pre-patch (the bug): the SVG arm prepended `"../"`. `model_prepatch.py`
reproduces that faithfully — `'../'` on the vector arm only, the raster arm
already correct — and **fails** the postcondition
`ToSeq(Result()) == ToSeq(dest_uri)`, the spec sensing the change (G-DIFF). The
discriminating tested content: an absolute URL such as
`https://example.org/foo.html#…` must begin with its scheme, never with `../`.

## B. Behaviour 2 — the self-document anchor link (`url_for_self_doc_anchor`)

Models the `refid` branch value — the one value that IS format-dependent. Gold
change: `'../' + current_filename + '#' + refid` → `current_filename + '#' +
refid` on the vector arm (`:423-424`); the raster arm `'#' + refid`
(`:425-426`) is what the vector arm must NOT be confused with.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `current_doc_name, anchor_id: List[int]` | the `str`s `current_filename` (`:410`), `child.get('refid')` | R | `str` ↔ `List[int]` (mapping.md §2). |
| B2 | `Implies(vector_format, ToSeq(Result()) == ToSeq(current_doc_name) + PSeq(35) + ToSeq(anchor_id))`, built by the `cf ++ '#' ++ aid` concatenation (`35 == '#'`) | `:423-424` `urls[child['reftitle']] = current_filename + '#' + child.get('refid')` under `if graphviz_output_format == 'SVG'` | A-reference | the changed concatenation is modelled deeply; G-AX checks `url_for_self_doc_anchor(cf, aid, True) == cf + '#' + aid`. |
| B3 | `Implies(vector_format, Result().take(len(current_doc_name)) == current_doc_name)` | (the vector link begins with the current document name, not `../`) | I | structural consequence of the concatenation; discriminates the `../` prefix. |
| B4 | `Implies(not vector_format, ToSeq(Result()) == PSeq(35) + ToSeq(anchor_id))`, built by the raster arm's early return | `:425-426` `urls[child['reftitle']] = '#' + child.get('refid')` | A-reference | the `else` arm the change leaves standing; G-AX checks `url_for_self_doc_anchor(cf, aid, False) == '#' + aid` and that it differs from the vector value whenever `cf` is non-empty. Pinning it is what stops a rival from prefixing the raster anchor with the document name (or anything else). |

Pre-patch: the SVG arm prepended `'../'`. `model_prepatch_2.py` reproduces that
(`'../'` on the vector arm only; its raster arm is the correct `'#' ++ aid`) and
**fails** `Implies(vector_format, ToSeq(Result()) == ToSeq(current_doc_name) +
PSeq(35) + ToSeq(anchor_id))` (G-DIFF).

## C. Behaviour 3 — the external-reference key (`trailing_name_for_destination`)

Models the new `refname = child['refuri'].rsplit('#', 1)[-1]` (`:417`) for
external (`internal=False`) references. (For internal references the key stays
`child['reftitle']` — unchanged, tag **I**, not modelled.) `:417` is likewise
outside any format test, which is why this function has no `vector_format`
parameter: identification is the same operation in both formats, and adding a
parameter the value cannot depend on would only invite a vacuous branch.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | param `dest_uri: List[int]` | the `str` `child['refuri']` | R | `str` ↔ `List[int]` (mapping.md §2). |
| C2 | backward scan for the last `#`, return `dest_uri.drop(start)` with `ToSeq(Result()) == after_last_hash(ToSeq(dest_uri))` | `:417` `child['refuri'].rsplit('#', 1)[-1]` | A-reference | `after_last_hash` is the deep model of `rsplit('#', 1)[-1]` (the trailing component after the final `#`); G-AX checks `trailing_name_for_destination(dest_uri) == after_last_hash(dest_uri) == dest_uri.rsplit('#', 1)[-1]`. |

Pre-patch: the external key was not derived from the URI (the old code keyed by
`child['reftitle']` and never stripped the URI to its trailing name).
`model_prepatch_3.py` reproduces the no-extraction behaviour (it returns the
whole `dest_uri`) and **fails** `ToSeq(Result()) == after_last_hash(ToSeq(dest_uri))`
whenever the URI carries a `#` anchor (G-DIFF).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operations that genuinely
*changed* — dropping the `"../"` prefix from each SVG link, making the `refuri`
link format-independent, and deriving the external key from the URI — are each
modelled **deeply** (the value identity, the two explicit concatenations, the
trailing-component scan), not hidden behind an axiom about an unchanged callee.
There is no consumed axiom; the only callee the changed function relies on
(`graph.generate_dot`) is unchanged and is the identity on the link string the
tests read back (mapping.md §3).

## E. verify(model) ⇒ resolved

Each function verifies only if its output is exactly the post-patch link/key:
the URI itself in both formats (A), `current_doc_name ++ '#' ++ anchor_id` for
the vector format and the bare `'#' ++ anchor_id` for the raster one (B), and
the trailing component after the last `#` (C) — none prefixed with `../`, and
none free to differ from the gold value in the format the tests do not read for
that particular link. By R (`str` ↔ `List[int]`, `'SVG'`-comparison ↔ `bool`)
and the G-AX A-reference checks, these equal the gold patch's string
expressions on the tested inputs. The gold patch resolves (G-RESOLVE). The
trust points are the two of PLAN §1.1: deep-model fidelity (G-AX,
`axiom_check.py`) and refinement fidelity (this document, G-EQ).

## F. Why the format observable is load-bearing (measured)

Without §0's parameter the spec states the vector link values only, and the
raster values are unconstrained. That is not a harmless gap:

* a rival that keeps the gold vector behaviour and re-introduces `'../'` on the
  raster `refuri` arm satisfies the vector-only spec, but applied to the real
  tree it makes P2P `test_inheritance_diagram_png_html` FAIL while F2P
  `test_inheritance_diagram_svg_html` still passes (measured in the pinned eval
  image). The regression is real because `:421` is the gold statement for both
  formats.
* a rival that prefixes the raster anchor with the document name (i.e. echoes
  the vector value into the raster arm) is not caught by any visible test, but
  it contradicts `:425-426`, which the change deliberately leaves standing.

Both are carried as `expect="reject"` cases (`format-raster-dotdot-destination`,
`format-raster-anchor-echoes-vector`), together with the sub-domain variants
that would survive a spec pinned only on the fixtures' inputs
(`format-raster-short-uri-guard`, `format-raster-scheme-conditional`), a
boundary-token swap in the raster separator
(`format-raster-anchor-colon-separator`), and an over-approximation that keeps
every weaker consequence clause while breaking the identity
(`over-approx-destination-doubles-first-char`). The corresponding positive
control `pos-control-raster-anchor` shows the raster clause pins a value rather
than a syntax.
