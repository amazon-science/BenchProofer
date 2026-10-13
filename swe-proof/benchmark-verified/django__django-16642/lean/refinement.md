# refinement.md — operation correspondence (django__django-16642)

Maps every op in `implementation_contentType` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python adds two entries (`"br"`, `"compress"`) to the dict that maps
a compression `encoding` to a dedicated media type, then keeps `content_type` as
the `.get` default and applies the `or "application/octet-stream"` fallback. The
modeled function decides the final Content-Type string from the guessed
`(content_type, encoding)` pair.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `contentType encoding : Option String` | the `content_type, encoding` produced by `mimetypes.guess_type(filename)` | R | `str\|None ↔ Option String` bijection (mapping.md); the guess routine is the input boundary, not a modeled op |
| 2 | `let mut ct := contentType` | the dict-lookup default: `.get(encoding, content_type)` keeps `content_type` when the key is absent | I | the `.get` default is the unchanged starting value |
| 3 | `if let some e := encoding then …` | the dict is indexed by `encoding`; a `None` encoding never matches a key | I | `None`/`none` ⇒ no override, default kept |
| 4 | the `if e = "br"/"bzip2"/"compress"/"gzip"/"xz"` chain assigning the dedicated type | the override dict literal `{br, bzip2, compress, gzip, xz}` and its `.get` | R | the **changed op**: the post-patch key set is `{br,bzip2,compress,gzip,xz}`. The dict literal ↔ the per-key `if` chain under the `str ↔ some` refinement. `br`/`compress` are the added keys; the others were already present. Modeled deeply, NOT axiomatized. |
| 5 | `match ct with some s => if s.isEmpty then octet-stream else s \| none => octet-stream` | `content_type or "application/octet-stream"` | R | Python truthiness of `str\|None`: `None` and `""` are falsy ⇒ octet-stream; any non-empty `str` is truthy ⇒ itself. `none`/`some ""` ↔ falsy, `some s (s≠"")` ↔ truthy |

No A-consumed rows: the proof discharges the selection-vs-spec equivalence
directly; no UNCHANGED callee property is assumed (axioms region empty, G-AX is a
skip stub).
No A-reference rows: the dict/`.get`/`or` are reproduced concretely as R/I ops,
not abstracted behind a model that needs G-AX validation. `mimetypes.guess_type`
is a boundary input producer, not a modeled callee. No changed-inexpressible op.

The discriminating clause is row 4: the post-patch key set includes `"br"` and
`"compress"`. The prepatch impl's chain omits both keys, so for
`encoding = some "br"` (a `.tar.br` / `.html.br` payload) it keeps the guessed
type (e.g. `some "application/x-tar"` or `some "text/html"`) instead of
selecting `"application/x-brotli"`; likewise `encoding = some "compress"` (a
`.Z` payload) keeps the guessed type instead of `"application/x-compress"`.
Hence on input `(some "text/html", some "br")` the prepatch impl returns
`"text/html"` while `finalContentType` (and thus the frozen
`problem_spec_contentType`) requires `"application/x-brotli"`, so prepatch
`correct_contentType` cannot close — the G-DIFF signal. These are exactly the
two cases added to `test_compressed_response` (`.tar.br`, `.tar.Z`).
