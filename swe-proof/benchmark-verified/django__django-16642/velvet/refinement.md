# refinement.md — django__django-16642

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `resolveMediaType` `do` block, plus the deep `compressionMediaType` /
`resolvedMediaType` models) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (a deep model validated == a real callee
by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A-tagged steps** (no axioms, no deep-model references): the impl region is
pure R/I, so its soundness rests entirely on G-CONF + G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The media-type resolution site — `FileResponse.set_headers`

Gold hunk (`django/http/response.py:611-615`):
```
                content_type = {
+                    "br": "application/x-brotli",
                     "bzip2": "application/x-bzip",
+                    "compress": "application/x-compress",
                     "gzip": "application/gzip",
                     "xz": "application/x-xz",
                 }.get(encoding, content_type)
```
with the surrounding resolution (`content_type, encoding = mimetypes.guess_type(...)`
above and `self.headers["Content-Type"] = content_type or "application/octet-stream"`
below).

| # | Solution.lean impl op (`resolveMediaType`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `guessed : Option String` | `content_type` from `mimetypes.guess_type(filename)` | R | `str|None ↔ Option String` (mapping.md §2). The unchanged sniffer's output is the modeled input (mapping.md §3); G-CONF drives the real `guess_type`. |
| A2 | parameter `encoding : Option String` | `encoding` from `mimetypes.guess_type(filename)` | R | `str|None ↔ Option String` (mapping.md §2). Same input-provenance as A1. |
| A3 | `compressionMediaType encoding` (the five-key `match`) | the dict literal `{ "br":…, "bzip2":…, "compress":…, "gzip":…, "xz":… }` indexed by `encoding` | I | identical concrete op: the `match … | some "br" => some "application/x-brotli" | …` is the dict-membership lookup transliterated key-for-key (mapping.md §2). The patch's ADDED keys `"br"`, `"compress"` are present in the model's table. |
| A4 | `(compressionMediaType encoding).orElse (fun _ => guessed)` | `{…}.get(encoding, content_type)` | R + I | `dict.get(k, default)` ↔ `Option.orElse`: the table value when the label is recognised, else the guessed type. Concrete control flow identical; the `Option` carrier is the R-refinement of `str|None`. |
| A5 | `.getD "application/octet-stream"` | `content_type or "application/octet-stream"` | R | the present/absent split. `x or d` ↔ `Option.getD d` because every recognised/guessed media type is a non-empty truthy string (mapping.md §2); G-CONF refutes any divergence over 10⁵ inputs. |
| A6 | result `out : String` returned | `self.headers["Content-Type"] = …` | R | the resolved Content-Type the F2P `test_compressed_response` reads via `response.headers["Content-Type"]` (mapping.md §1). |

Discriminating content of the change — a file whose name advertises `br` or
`compress` must announce `application/x-brotli` / `application/x-compress`, NOT
the wrapped payload's guessed type — lives in `compressionMediaType (some "br")
= some "application/x-brotli"` and `compressionMediaType (some "compress") =
some "application/x-compress"` (A3) ⇔ the two ADDED dict keys (real). The
pre-patch table omitted both, so `Solution_prepatch.lean` reproduces that
three-key table and **fails** `out = resolvedMediaType guessed encoding`
(G-DIFF) precisely on the `br` / `compress` cases.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The real resolution is a straight-line dict lookup plus an
`or` fallback that always terminates and returns, and the F2P test observes its
return value (the response's Content-Type header), so total correctness is the
faithful semantics. Partial correctness would admit a same-spec implementation
that diverges (an infinite loop vacuously satisfies every `ensures`) — a wrong
impl the tests would fail — so it would leave the spec too weak.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the
compression-label → media-type table — is modeled **deeply and concretely** as
`compressionMediaType` (the spelled-out `match`), an **I** op the patch
transliterates key-for-key, NOT hidden behind an axiom. There is no consumed
axiom and no A-reference deep model: the modeled function reads two values that
the unchanged upstream sniffer (`mimetypes.guess_type`) already produced
(mapping.md §3), so there is no outside contract to assume. `axiom_check.py` is
therefore absent (G-AX skips, vacuously sound).

## C. verify(Solution) ⇒ resolved

`resolveMediaType` verifies only if its output equals `resolvedMediaType`, i.e.
the override table (with `br`/`compress` present, A3) winning over the guessed
type (A4) and the generic fallback (A5). By R (`str|None ↔ Option String`, the
`get`/`or` bijections of §2) the verified resolution equals the patched
`set_headers` Content-Type on the tested inputs; by G-CONF the R/I
transliteration agrees with `patch.diff`'s real `FileResponse` behaviour on ≥10⁵
fuzzed file names (including every recognised label and names that miss the
table). Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
sole trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms to trust (G-AX vacuous).
