# mapping.md — symbol binding & type bijection (django__django-16642)

## Modeled function
- **Lean** `implementation_contentType : Option String → Option String → String`
- **Python** the content-type selection block inside `FileResponse.set_headers`
  — `django/http/response.py:606-618 @ base_commit` (the
  `if self._no_explicit_content_type:` branch with `filename` truthy). The
  modeled computation is exactly the three statements:

```python
content_type, encoding = mimetypes.guess_type(filename)   # boundary callee — supplies inputs
content_type = {                                          # the encoding→type override dict
    "bzip2": "application/x-bzip",
    "gzip": "application/gzip",
    "xz": "application/x-xz",
}.get(encoding, content_type)
self.headers["Content-Type"] = content_type or "application/octet-stream"
```

The gold patch adds two entries to the override dict (`"br"`, `"compress"`):

```python
# base (buggy)        dict = {bzip2, gzip, xz}
# patched             dict = {br, bzip2, compress, gzip, xz}
```

`mimetypes.guess_type(filename)` returns the pair `(content_type, encoding)`
where `content_type : str | None` and `encoding : str | None`. The encoding is
drawn from `mimetypes.encodings_map`, i.e. one of
`{"gzip","compress","bzip2","xz","br"}` or `None`. This routine is at the INPUT
boundary: it produces the two arguments the modeled selection consumes. It is
NOT changed by the patch and NOT part of the modeled computation, so it is
neither axiomatized nor reproduced — the spec ranges over all `(Option String,
Option String)` pairs the boundary could yield.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `content_type : str \| None` (guessed type) | `contentType : Option String` | `None ↔ none`, a `str ↔ some` |
| `encoding : str \| None` (compression scheme) | `encoding : Option String` | `None ↔ none`; values from `encodings_map` ↔ `some` of that ASCII string |
| `{...}.get(encoding, content_type)` | `encodingContentType`-driven override in `finalContentType`/impl | dict lookup ↔ the per-key `if` chain; `.get` default ↔ keep `contentType` |
| `content_type or "application/octet-stream"` | the `isEmpty`/`none → "application/octet-stream"` fallback | Python truthiness of a `str`: `None` and `""` are falsy ⇒ both map to the octet-stream default; any non-empty `str` is truthy |
| `self.headers["Content-Type"] = …` (the assigned string) | `result : String` | the final selected content type |

Note on Python `or`: for a value `v : str | None`, `v or D` yields `D` exactly
when `v` is `None` or the empty string `""`, else `v`. The Lean fallback matches
this: `none → D`, `some "" → D` (via `String.isEmpty`), `some s (s≠"") → s`.

## Callee provenance
- The override dict literal and `.get`/`or` are pure language constructs,
  reproduced concretely (R/I), not axiomatized. The CHANGED op is the dict's key
  set (`{bzip2,gzip,xz}` → `{br,bzip2,compress,gzip,xz}`), modeled deeply by
  `encodingContentType`.
- `mimetypes.guess_type` is an UNCHANGED boundary callee that supplies the two
  inputs; it is not consumed inside the modeled computation, so no axiom about it
  is needed and the axioms region is empty (G-AX is a skip stub).

## Flag dependency
The block is gated by `self._no_explicit_content_type` and `filename` being
truthy. Both are unchanged structural context; when either is false the override
block does not run at all. The modeled function captures the selection performed
INSIDE that block (the patch touches only the dict), so the flag is not part of
the modeled inputs.

## Scope note
`set_headers` also sets `Content-Length` and `Content-Disposition`; the patch
touches ONLY the content-type override dict (lines 611-615), so the observable
F2P behavior is fully captured by the `(content_type, encoding) → Content-Type`
selection. The length/disposition logic is orthogonal and unchanged, hence not
modeled.

## G-CONF fuzz seed
Pinned seed: **16642**. ≥10^5 fuzzed `(content_type, encoding)` pairs over an
alphabet of realistic guessed media types (incl. `None` and `""`) crossed with
every encodings_map value plus `None` and unrecognized encodings, plus targeted
boundary cases (each compression scheme; the two newly-added schemes `br`,
`compress`; empty/None type).
