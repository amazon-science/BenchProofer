# mapping.md — sphinx-doc__sphinx-10614

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ac2b7599d212af7d04649959ce6926c63c3133fa`, states the type
abstraction, and gives the provenance of every modelled operation.

Repo file under change: `sphinx/ext/inheritance_diagram.py`.
Changed function: `html_visit_inheritance_diagram(self, node)`
(`sphinx/ext/inheritance_diagram.py:398`; pre-patch body lines 408-423,
post-patch 408-426). It builds the `urls` dict (fully-qualified class name →
hyperlink target) that `graph.generate_dot(name, urls, ...)` (`:276`, consumed
at `:309`, `URL="<url>"`) writes into each clickable diagram node.

The function reads the **image format** at `:409`
(`graphviz_output_format = self.builder.env.config.graphviz_output_format
.upper()`) and branches on `== 'SVG'`. The format decides what the links inside
the image resolve against:

* `'SVG'` (vector): the diagram is embedded through an `<object>` tag and its
  internal links resolve relative to the image file's own directory (the image
  directory, one level below the document-tree root);
* anything else (raster, `'PNG'` by default): the diagram is a bitmap with a
  clickable `<map>` written into the page, so its links resolve relative to the
  document being rendered.

Both format values are caller-reachable (`graphviz_output_format` defaults to
`'png'`; the F2P test selects `'svg'`, the P2P `test_inheritance_diagram_png_html`
uses the default), and the gold hunk touches BOTH: it removes the format branch
entirely from the `refuri` case (making that link format-independent) and edits
only the `'SVG'` arm of the `refid` case. So the format is a modelled **input**
(`vector_format`), not an implicit context: every clause is pinned for both
values of it.

## 1. Symbol ↔ repo binding

| model.py symbol | repo construct (file:line) | role |
|---|---|---|
| `vector_format` (model param) | `graphviz_output_format == 'SVG'`, where `graphviz_output_format` is `self.builder.env.config.graphviz_output_format.upper()` (`:409`) | the image-format observable both link values are stated against; `True` = vector/SVG, `False` = raster (PNG/PDF/...) |
| `url_for_destination(dest_uri, vector_format)` | the `refuri` branch value: post-patch `:421` `urls[refname] = child.get('refuri')`, which sits OUTSIDE any format test (pre-patch `:415-418`, `"../" + child.get('refuri')` under `if graphviz_output_format == 'SVG'` and `child.get('refuri')` in the `else`) | modelled changed behaviour 1: the link for an explicit destination URI, in either format |
| `url_for_self_doc_anchor(current_doc_name, anchor_id, vector_format)` | the `refid` branch value: post-patch `:423-424` (`'SVG'` arm) `current_filename + '#' + child.get('refid')` and `:425-426` (`else` arm) `'#' + child.get('refid')` (pre-patch the `'SVG'` arm was `'../' + current_filename + '#' + refid`) | modelled changed behaviour 2: the link for an anchor in the current document — the one value that is format-dependent |
| `trailing_name_for_destination(dest_uri)` | the new external-reference key, post-patch `:417` `refname = child['refuri'].rsplit('#', 1)[-1]` (also outside any format test) | modelled changed behaviour 3: the dict key for an externally-sourced (intersphinx, `internal=False`) target |
| `after_last_hash(s)` *(deep model, A-reference)* | `str.rsplit('#', 1)[-1]` | pure spec: trailing component after the final `#` |
| `has_scheme(s)` *(deep model, A-reference)* | the absolute-URL test `'://' in url` | pure spec: scheme-separator membership, used to state scheme preservation |
| `is_scheme_sep_at(s, i)` | the three-character match `s[i:i+3] == '://'` | pure helper for `has_scheme` |
| `current_doc_name` (model param) | repo local `current_filename` = `self.builder.current_docname + self.builder.out_suffix` (`:410`, computed for both formats) | the current document's output name; treated as an opaque string |

The three model functions take **abstracted** parameter names — `dest_uri`,
`current_doc_name`, `anchor_id`, `vector_format` — rather than the repo's
`refuri` / `refid` / `current_filename` / `graphviz_output_format`. The repo
symbols are patched-repo identifiers absent from the solver-visible
`problem_statement`, so they are NOT used in the consumer spec view (model.py);
the binding to the real repo names is recorded here in this consumer-hidden
mapping for the audit.

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the literal `"../"` / `'../'` prefix on
the two `'SVG'`-arm link expressions (pre-patch `:416`, `:421`), and the
unconditional use of `child['reftitle']` as the dict key for `refuri`
references, which the change replaces — for external references — with the
refname derived from the destination URI.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`refuri`, `current_filename`, `refid`, the URL strings, the dict key) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` `+` ↔ list/`PSeq` `+`; the literal `'#'` ↔ `35`; the literal `"../"` ↔ `PSeq(46, 46, 47)`; `':'`/`'/'` ↔ `58`/`47` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `str.rsplit('#', 1)[-1]` | `after_last_hash(PSeq)` | trailing component after the last `#`; equals `s` when `s` has no `#` |
| `'://' in url` | `has_scheme(PSeq)` | True iff some index `i` has `s[i:i+3] == '://'` |
| `graphviz_output_format == 'SVG'` (`:409`, the config value already `.upper()`'d) | `vector_format: bool` | `True` ↔ the vector branch, `False` ↔ the raster/`else` branch; total (the config is a `str`, so the comparison is a `bool` and both values occur) |
| `urls[key] = value` dict assignment + `generate_dot` URL emission | the value strings returned by the three functions, plus the key string | the tests parse the emitted `href="<value>"` for each node (`<object>` SVG contents for the vector format, the `<map><area href=...>` for the raster one) and the presence of the registered class names; modelled as the value/key strings themselves |
| `child.get('internal', True)` external-vs-internal selection | precondition-free split (external ⇒ key = `after_last_hash(refuri)`; internal ⇒ key = reftitle, unchanged) | the key function models the external case (the changed one); the internal case keeps the pre-existing reftitle key (`I`, not modelled) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; specifications are phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A)

**There are NO consumed `@ContractOnly` axioms in this bundle** (the `axioms`
region is empty). Every operation the changed function performs in either
format branch is plain string concatenation, slicing, and membership — all
modelled **deeply** in `model.py`'s `pure` region and the three implemented
functions. The changed function calls no unchanged library helper whose
behaviour the proof must assume; `graph.generate_dot` (the consumer of `urls`)
is unchanged and merely substitutes each value into `URL="<value>"`, which is
the identity on the link string the tests read back.

### 3.1 Deep models validated by G-AX (A-reference)
`axiom_check.py` validates each deep model against the REAL Python operation
the gold patch performs, **in both image formats**, on 19 boundary inputs +
40 000 randomized fuzz inputs (stdlib-only, exit 0 iff sound):

- `url_for_destination(dest_uri, vector_format) == dest_uri` for either format ↔ post-patch `:421` `urls[refname] = child.get('refuri')`, which no longer sits under a format test (the `"../"` prefix and the branch itself are gone).
- `url_for_self_doc_anchor(cf, anchor_id, True) == cf + '#' + anchor_id` ↔ post-patch `:423-424`; `url_for_self_doc_anchor(cf, anchor_id, False) == '#' + anchor_id` ↔ `:425-426`. `axiom_check.py` also asserts the two differ whenever `cf` is non-empty, so a format-blind deep model could not pass.
- `trailing_name_for_destination(dest_uri) == after_last_hash(dest_uri) == dest_uri.rsplit('#', 1)[-1]` ↔ the new external-key derivation at `:417`.

## 4. Why this resolves the issue

The reported bug: SVG inheritance diagrams in a non-root document produced
links prefixed with an extra `../`, which (because the SVG's links are already
relative to the image directory) climbed one directory too far and 404'd. The
change removes that `../` prefix from the `'SVG'` link expressions, and
additionally derives the dict key for external (intersphinx) references from
the destination URI so that an absolute external URL is registered and emitted
verbatim. The F2P test `test_inheritance_diagram_svg_html` asserts exactly
this: absolute URLs (`'://' in href`) start with `https://example.org/` (never
`../https://…`), and every relative URL resolves to an existing output file.

The raster format is not a bystander. Because the gold change deletes the
`refuri` format branch rather than one of its arms, the raster link value is
part of the changed behaviour, and the P2P test
`test_inheritance_diagram_png_html` reads exactly those raster `<area href=…>`
values. A specification that pinned only the vector link would admit a rival
that re-introduces `'../'` on the raster arm; that rival was built and measured
against the real tree — F2P still passes, P2P `test_inheritance_diagram_png_html`
fails — which is why `vector_format` is an observable here and every clause is
stated for both of its values (properties.py section 5 carries the rival, and
the sub-domain variants of it, as reject cases).
