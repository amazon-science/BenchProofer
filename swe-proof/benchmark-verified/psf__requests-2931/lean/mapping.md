# mapping.md — symbol binding & type bijection (psf__requests-2931)

## Modeled function
- **Lean** `implementation_encodeParams : Datum → Datum`
- **Python** `requests.models.RequestEncodingMixin._encode_params`
  — `requests/models.py:73-98 @ 5f7a3a7`, **restricted to its string/bytes
  branch** (`requests/models.py:81-82`).

`_encode_params` is a staticmethod with four branches on the shape of `data`:
str/bytes, file-like (`read`), iterable (dict / list-of-2-tuples), else. Only the
**first branch** (`isinstance(data, (str, bytes))`) is touched by the patch. The
post-patch first branch is:

```python
if isinstance(data, (str, bytes)):
    return data
```

Pre-patch it was `return to_native_string(data)`. `to_native_string` (Python 3,
`requests/utils.py:686`) returns a native `str`: a `str` passes through, but
`bytes` are `.decode('ascii')`-ed — turning a binary payload into text (and
raising `UnicodeDecodeError` on any non-ASCII byte, e.g. the UTF-8 of `u"ööö"` in
the F2P `test_binary_put`). The fix returns the payload unchanged so a binary
body stays binary.

The other three branches and the second patch hunk are out of the modeled scope
(see "Scope" below).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `data : str` (in the str/bytes branch) | `Datum.text (s : List Char)` | per-codepoint text value |
| `data : bytes` (in the str/bytes branch) | `Datum.binary (b : List UInt8)` | byte sequence |
| the branch's return value | `Datum` | post-patch: the same `Datum`; pre-patch: `toNativeString data` |
| `to_native_string(bytes)` = `bytes.decode('ascii')` | `toNativeString (.binary b) = .text …` (prepatch only) | kind flips binary→text |

The predicate `isinstance(data, (str, bytes))` is the branch precondition; by
construction every `Datum` value is in that branch (text or binary), which is the
exact domain the patch modifies. The modeled function is the branch body.

## Scope (unmodeled by design, per SPEC_GUIDE §2/§3)
- **Hunk 2** (`prepare_url`: add `if isinstance(params, (str, bytes)): params =
  to_native_string(params)`) is a *compensating* coercion. Once `_encode_params`
  stops coercing str/bytes, `prepare_url` must coerce URL params itself so the
  query-string path (`test_params_bytes_are_encoded`, a PASS_TO_PASS) does not
  regress. It re-establishes, at the URL-params call site only, the very coercion
  hunk 1 removed from the body path — it observably changes nothing the F2P test
  demands and nothing the spec frames (the body path, `prepare_body →
  _encode_params`, never reaches it). The single independently-observable fixed
  behavior the F2P test (`test_binary_put`) pins is hunk 1: a binary body is
  returned unchanged. Modeling hunk 1 is sufficient and complete for the F2P.
- The file-like / iterable / else branches of `_encode_params` are unchanged and
  out of scope.

## Callee provenance
- `to_native_string` is a callee, but it appears ONLY in the pre-patch impl
  (modeled deeply as `toNativeString` to exhibit the bug). The post-patch modeled
  branch calls NOTHING — it is the identity. There is therefore no UNCHANGED
  callee consumed by the proof; the `axioms` region is empty and `axiom_check.py`
  is a skip stub.

## Flag dependency
None.

## G-CONF fuzz seed
Pinned seed: **2931**. ≥10^5 fuzzed inputs over text values (random ASCII +
non-ASCII codepoints) and binary values (random byte sequences, including
non-ASCII bytes and empty), diffing the identity shadow against the post-patch
Python branch `return data`.
