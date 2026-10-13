# mapping.md — django__django-11133

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 879cc3da6249e920b8d54518a0ae06de835d7373`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of every abstracted callee.

Repo file under change: `django/http/response.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `makeBytes (encodeStr) (fallback) (value : Body)` | `HttpResponseBase.make_bytes(self, value)` — `django/http/response.py:223` (dispatch body at lines 232–238) | the modeled changed function (turns a body value into the output bytestring) |
| `Body` (inductive) | the runtime type of the `value` argument, classified by which `isinstance` branch it takes | the value-shape `make_bytes` dispatches on |
| `bodyBytes (encodeStr) (fallback) value` | the body of `make_bytes` post-patch: the chained `isinstance` dispatch | pure spec: output bytestring for one body value |
| `encodeStr : List Char → List UInt8` *(free input)* | `value.encode(self.charset)` for the `str` branch (`response.py:235`) | UNCHANGED callee, abstracted as a free input (str→bytes encoder); no relied-on property |
| `fallback : List UInt8` *(free input)* | `str(value).encode(self.charset)` for the non-string branch (`response.py:238`) | UNCHANGED callee chain, abstracted as a free input (the encoded textual rendering); no relied-on property |
| `bodyBytes (.buffer b) = b` *(A-reference)* | `bytes(value)` applied to a `memoryview` (`response.py:233`, reached post-patch) | the one semantic fact: materialising a byte-buffer view yields its underlying bytes — identical to `bytes(value)` on a plain `bytes`. Validated `bytes(memoryview(x)) == x` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch behaviour the change fixes (refinement audit only, not in the
consumer spec view): a `memoryview` value fails the `isinstance(value, bytes)`
and `isinstance(value, str)` tests, so it reaches `return str(value).encode(...)`
(`response.py:238`) — `str(memoryview(b'x'))` is the repr `'<memory at 0x…>'`, so
the body becomes the encoded repr instead of the buffer's bytes.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `bytes` value `v` | `Body.bytes b` with `b : List UInt8` | `b = [v[0], …, v[len(v)-1]]` (each byte 0–255 ↔ `UInt8`); `len(v) ↔ b.length` |
| a `memoryview` value `v` over a byte region | `Body.buffer b` with `b : List UInt8` | `b = list(bytes(v))` — the materialised underlying bytes; `bytes(v) ↔ b` byte-for-byte |
| a `str` value `s` | `Body.text cs` with `cs : List Char` | `s` ↔ `s`-shaped `List Char`; `len(s) ↔ cs.length` (BMP code points, total/exact) |
| any other value (int, list, object, …) | `Body.other` | the routine's content does not depend on the value beyond "not bytes/memoryview/str"; its bytestring is the free input `fallback` |
| the output bytestring `make_bytes` returns | `List UInt8` (`out`) | `bytes` object ↔ `List UInt8` byte-for-byte; `out.length ↔ len(result)` |
| `value.encode(self.charset)` (str branch) | `encodeStr : List Char → List UInt8` | UNCHANGED str→bytes encoder; abstracted as a total free function (no property relied on) |
| `str(value).encode(self.charset)` (other branch) | `fallback : List UInt8` | UNCHANGED render-then-encode chain; abstracted as a free constant (no property relied on) |

`memoryview` and `bytes` are the two binary branches the patch unifies; the model
gives them distinct constructors (`buffer`/`bytes`) carrying the SAME `List UInt8`
content so the spec can pin that both yield that content (the discriminator).

## 3. Callee provenance

### 3.1 `bytes(value)` on a `memoryview` (A-reference)
**Callee:** the CPython builtin `bytes(...)` applied to a `memoryview`
(`response.py:233`, `return bytes(value)`, reached for `memoryview` only after the
patch widens the guard to `isinstance(value, (bytes, memoryview))`). The model
claims `bodyBytes (.buffer b) = b`: materialising the view yields its underlying
bytes. This is the deep content of the binary branch for buffers; it is modeled
directly (the `.buffer b => b` arm), and its equality to the real builtin is the
**A-reference** validated by G-AX.

**Soundness check (G-AX):** `axiom_check.py` constructs real `memoryview` objects
over fuzzed byte regions (empty, single byte, all 256 byte values, large,
slices/subviews, non-`bytes` backings like `bytearray`) and asserts
`list(bytes(mv)) == list(underlying_bytes)` — i.e. the buffer arm `.buffer b => b`
is sound — AND, as the contrast the bug turns on, that `bytes(mv) != str(mv).encode()`
for non-empty buffers (the pre-patch fallback produced the repr, not the content).
It also confirms `bytes(plain_bytes) == plain_bytes` (the `bytes` arm). stdlib /
builtins only. Exit 0 iff sound.

### 3.2 `encodeStr` / `fallback` (free inputs — no G-AX)
`value.encode(self.charset)` and `str(value).encode(self.charset)` are UNCHANGED
by the patch (pre- and post-patch both run them on their respective branches). The
spec relies on no property of either, so they are abstracted as free inputs and
need no validation against a real callee.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11133`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the `Body` dispatch (`makeBytes`/`bodyBytes`) to Python over the
real repo types (`bytes`/`memoryview`/`str`/other) and compares against the
patched `make_bytes` behaviour; the free inputs `encodeStr`/`fallback` are
realised by the real unchanged encoder (`value.encode(charset)` /
`str(value).encode(charset)`), since they are A-tagged → run real callee.
