# mapping.md — symbol binding & type bijection (django__django-11133)

## Modeled function
- **Lean** `implementation_toBytestring : List Char → PyValue → List UInt8`
- **Python** `HttpResponseBase.make_bytes(self, value)` —
  `django/http/response.py:223-237 @ 879cc3d` (base_commit).
  Post-patch body:
  ```python
  if isinstance(value, (bytes, memoryview)):
      return bytes(value)
  if isinstance(value, str):
      return bytes(value.encode(self.charset))
  return str(value).encode(self.charset)
  ```

The function under spec is `make_bytes`. It turns an arbitrary response-body
`value` into the output bytestring. The observable behavior change demanded by
the F2P test (`test_memoryview_content`) is: a *view over a byte buffer* must
yield those underlying bytes (`b'memoryview'`), instead of the bytes of its
textual rendering (`b'<memory at 0x...>'`).

`self.charset` is the only piece of `self` the method reads; it is modeled as the
explicit `charset : List Char` argument. No other instance state is touched, so
no `structure` is needed.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.charset` (`str`) | `charset : List Char` | output charset name |
| `value` (`bytes`) | `PyValue.bytesV b` (`b : List UInt8`) | already a byte buffer |
| `value` (`memoryview`) | `PyValue.memoryviewV b r` | `b` = underlying bytes (`bytes(value)`); `r` = textual rendering `str(value)` carries |
| `value` (`str`) | `PyValue.strV s` (`s : List Char`) | character string |
| any other `value` | `PyValue.otherV text` | `text` = `str(value)` |
| result (`bytes`) | `List UInt8` | byte sequence |
| `value.encode(charset)` / `str(value).encode(charset)` | `encode charset · : List UInt8` | the standard str→bytes encoding callee |
| `bytes(value)` for bytes/memoryview | identity onto the underlying `List UInt8` | `bytes()` of a bytes/memoryview copies the buffer bytes verbatim |

`PyValue` carries on each constructor exactly the data the corresponding
`isinstance` branch consumes: `bytesV`/`memoryviewV` carry the underlying bytes
(what `bytes(value)` returns); `memoryviewV` additionally carries the textual
rendering `r` (`str(value)`) so the *pre-patch* fall-through behavior is
expressible — the pre-patch impl encodes `r`, the spec pins `b`.

## Callee provenance
- **`encode` (`str.encode(charset)`)** — UNCHANGED standard-library callee, used
  identically by the `strV` and `otherV` branches both pre- and post-patch.
  Declared `opaque encode : List Char → List Char → List UInt8` so it can appear
  in the executable impl. It is NOT the operation the patch changes, and the
  proof uses it only by reflexivity (impl and spec apply the same `encode` to the
  same arguments), so NO `_prop` axiom is consumed — the axioms region declares
  only its signature. G-AX therefore has no callee property to validate (skip
  stub); the str/other branches are I-tagged identity ops in refinement.md.
- `bytes(value)` for the bytes / memoryview branches is the identity onto the
  underlying byte buffer (a verbatim copy), modeled as the `= b` postcondition —
  the changed op itself, modeled directly, not axiomatized.

## Flag dependency
None. `make_bytes` reads no boolean flags; the only configuration is `charset`,
which is threaded through `encode` unchanged.

## G-CONF fuzz seed
Pinned seed: **11133**. ≥10^5 fuzzed `PyValue` inputs across all four
constructors, oversampling the `memoryview` constructor (the discriminating
case) and varying byte buffers, charsets, and textual renderings.
