# mapping.md — psf__requests-2931

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5f7a3a74aab1625c2bb65f643197ee885e3da576`, states the type
abstraction, and gives the provenance of the single axiom.

Repo file under change: `requests/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serialize_request_body(v)` | the `isinstance(data, (str, bytes))` branch of `PreparedRequest._encode_params(data)` — `requests/models.py:75` (branch body line 84) | modeled changed function (site A): how a textual-or-binary value is turned into the outgoing body |
| `normalize_query_string(v)` | the textual-or-binary handling of `params` in `PreparedRequest.prepare_url(self, url, params)` — `requests/models.py:324`, just before `enc_params = self._encode_params(params)` (line 388) | modeled changed function (site B): how a textual-or-binary value supplied as the query component is coerced before being appended to the query |
| `to_native(v_is_bytes, v_data)` *(axiom — A-consumed)* | `to_native_string(string, encoding='ascii')` — `requests/utils.py:686` | unchanged utility callee; the native-string decoder. Site B calls it; site A (post-change) does NOT |
| `is_ascii(b)` | the implicit precondition of `bytes.decode('ascii')` inside `to_native_string` | pure spec: every octet is ASCII (< 128) |
| `Value(is_bytes, data)` | a `str`/`bytes` Python value (the `data`/`params` argument) | carrier object: a type tag (str vs bytes) plus content |

The pre-change repo expression the patch removes/relocates (for the refinement
audit, not referenced from the consumer spec view): site A's branch body was
`return to_native_string(data)` (`models.py:84`); the patch changes it to
`return data` and *adds* the textual-or-binary coercion
`if isinstance(params, (str, bytes)): params = to_native_string(params)` at
site B, immediately before the `_encode_params(params)` call (`models.py:388`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `str` value | `Value(is_bytes=False, data=cps)` where `cps[k] == ord(s[k])` | text content as `PSeq[int]` of code points; `len(s)` ↔ `len(data)` |
| a `bytes` value | `Value(is_bytes=True, data=octets)` where `octets[k] == s[k]` (the k-th octet, 0..255) | binary content as `PSeq[int]` of octet values |
| `isinstance(x, bytes)` | `x.is_bytes` | the type tag the F2P test observes via `isinstance(request.body, bytes)` |
| `isinstance(x, str)` | `not x.is_bytes` | — |
| identity of content under `str(...)`/return | `Result().data == v.data` | the characters/octets are unchanged |

`str`/`bytes` indexing is banned in Nagini, so the content carrier is
`PSeq[int]` (held inside the `Value.data` field); the type tag is a plain
`bool` field (`Value.is_bytes`). A read-only value is held at `1/2` permission
on both fields (directive 5); the freshly constructed `Result()` is held at full
permission with its post-state pinned exactly.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `to_native` ↔ `requests.utils.to_native_string` (A-consumed)
**Callee:** `to_native_string(string, encoding='ascii')`, `requests/utils.py:686`:

```python
def to_native_string(string, encoding='ascii'):
    out = None
    if isinstance(string, builtin_str):   # Python 3: builtin_str is str
        out = string
    else:
        if is_py2:
            out = string.encode(encoding)
        else:
            out = string.decode(encoding)   # the eval interpreter is Python 3
    return out
```

On the Python-3 eval interpreter (`builtin_str is str`, `is_py2 is False`):
- a native-text (`str`) input is returned unchanged — identity on content;
- a binary (`bytes`) input is `bytes.decode('ascii')` — defined ONLY when every
  octet is ASCII (< 128), in which case each octet `b` decodes to the code
  point `b`, so the content is unchanged; for any octet ≥ 128 it raises
  `UnicodeDecodeError`.

Hence the **weakest** contract the proof needs:
`Requires(Implies(v_is_bytes, is_ascii(v_data)))` (binary ⇒ ASCII octets) and
`Ensures(Result() == v_data)` (content preserved; the result is always native
text and the caller, site B, drops the binary tag by constructing
`Value(False, ...)`). The axiom does not over-claim: it says nothing about
non-ASCII binary, exactly where the real callee is undefined.

**Why site A no longer calls it (the change):** the gold patch replaces site
A's `return to_native_string(data)` with `return data`. The body path therefore
preserves the value verbatim — its type tag and content unchanged — so a binary
payload survives as binary even when its octets are not ASCII (the F2P input
`u"ööö".encode("utf-8") == b"\xc3\xb6\xc3\xb6\xc3\xb6"` has all
octets ≥ 128). `serialize_request_body` consequently has NO ASCII precondition
and pins `Result().is_bytes == v.is_bytes` ∧ `Result().data == v.data`. Site B
keeps the long-standing query-parameter coercion (`Value(False, to_native(...))`)
so the P2P URL-encoding behaviour (`params=b'test=foo'` ⇒ `?test=foo`) is
retained.

**Soundness check (G-AX):** `axiom_check.py` imports the REAL
`requests.utils.to_native_string` (installed in the eval container; a
byte-identical Python-3-branch replica is the documented host fallback) and
asserts, on 8 text + 6 bytes boundary inputs and 40 000 randomized
ASCII-octet fuzz inputs (str and bytes), that the decoded content equals the
input content and the result is native `str` — i.e. the axiom's
`Ensures(Result() == v_data)` holds throughout its `Requires` domain. It
additionally confirms the decoder *rejects* the five non-ASCII binary witnesses
(incl. the F2P payload), which is exactly why the body path must not route
through it. Exit 0 iff sound. Encoding dependency: the axiom is sound for the
default `encoding='ascii'` (requests' call site and the function default);
recorded here so G-AX fuzzes that configuration.
