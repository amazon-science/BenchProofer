# mapping.md — django__django-16642

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fbe850106b2e4b85f838219cb9e1df95fba6c164`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/http/response.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_content_type(content_type, encoding)` | the `content_type = {...}.get(encoding, content_type)` table-lookup expression inside `FileResponse.set_headers` — `django/http/response.py:611-615` | the modeled changed operation (compression-scheme → content-type table lookup) |
| `dedicated_type(enc)` / `is_known_encoding(enc)` | the literal dict `{"br":…, "bzip2":…, "compress":…, "gzip":…, "xz":…}` keyed by the compression scheme (`django/http/response.py:611-615` post-patch) | pure spec: the table mapping a recognised compression scheme to its dedicated content type |
| `resolved_type(content_type, enc)` | the whole `{...}.get(encoding, content_type)` expression (lookup with the guessed content type as default) | pure spec: dedicated type if the scheme is recognised, else the guessed type |
| `tok_br/tok_bzip2/tok_compress/tok_gzip/tok_xz` | the five dict KEYS `"br" "bzip2" "compress" "gzip" "xz"` | encoding tokens as code-point sequences |
| `ct_brotli/ct_bzip/ct_compress/ct_gzip/ct_xz` | the five dict VALUES `"application/x-brotli" "application/x-bzip" "application/x-compress" "application/gzip" "application/x-xz"` | dedicated content types as code-point sequences |

The pre-patch table the change extends (for the refinement audit, not
referenced from the consumer spec view): the dict at `response.py:611-615`
contained only `{"bzip2", "gzip", "xz"}`, so the keys `"br"` and `"compress"`
were absent and the lookup fell through to the guessed `content_type`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `encoding: str` (second element of `mimetypes.guess_type(filename)`) | `List[int]` of Unicode code points | `s[k]` ↔ `encoding[k] == ord(s[k])`; `len`/`+`/equality mirror `str`; an empty `str` (or `None`) ↔ `[]` |
| `content_type: str` (first element of `mimetypes.guess_type(filename)`) | `List[int]` of Unicode code points | same code-point bijection |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `==`/`+`/`take`/`len`/`[i]` mirror `str` operations |
| `dict.get(encoding, content_type)` (the table lookup) | `resolved_type` / branch chain over `PSeq` equality | a Python `dict` keyed by string literals is, for these five distinct keys, a finite case split on key equality; `.get(k, default)` is "value if `k` is a key, else `default`" |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance

There are **no consumed axioms** and **no deep-model references** in this
bundle. The only Python-level callee in the changed expression is `dict.get`,
which is not an opaque library callee but a finite case split on string-literal
key equality — modeled directly (the branch chain in `select_content_type`),
expressible without axiomatization.

The producer of the `(content_type, encoding)` pair — `mimetypes.guess_type`
(`django/http/response.py:608`) — is **not changed by the patch** and is **not
part of the modeled operation**: the modeled function takes the already-guessed
pair as inputs. Under the refinement (refinement.md §A), supplying that pair to
`select_content_type` corresponds to the unchanged `guess_type` call feeding the
unchanged table-lookup statement. No `@ContractOnly` is needed or shipped, so
G-AX has nothing to execute beyond the no-op soundness assertion in
`axiom_check.py` (which records that the model carries no axioms/deep-model
references and re-confirms the five literal token/value encodings byte-for-byte
against their `str` originals).

### 3.1 The discriminating behaviour (problem statement)
The public problem statement names the two regressing file types directly:
`"br"` and `"Z"`. For a name like `test.html.br`, `mimetypes.guess_type`
returns `("text/html", "br")`; for `test.html.Z` it returns
`("text/html", "compress")` (the `.Z` suffix is the historic UNIX `compress`
scheme). Pre-patch the table lacked the `"br"` and `"compress"` keys, so the
lookup returned the guessed `"text/html"` — a compressed payload served under
the uncompressed content type, the reported bug. The five recognised schemes
and their dedicated content types are exactly the post-patch dict; this is the
behaviour the F2P test (`test_compressed_response`, extended in the test patch
with `.tar.br → application/x-brotli` and `.tar.Z → application/x-compress`)
observes.
