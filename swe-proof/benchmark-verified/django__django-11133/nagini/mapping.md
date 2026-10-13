# mapping.md — django__django-11133

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 879cc3da6249e920b8d54518a0ae06de835d7373`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/http/response.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `coerce_to_octets(v)` | `HttpResponseBase.make_bytes(self, value)` — `django/http/response.py:223` (body 232-237) | the modeled changed function (value → output bytestring) |
| `Value` (`kind`, `buf`, `cps`, `data`) | the runtime `value` argument + its byte/str type discrimination + the returned bytestring | minimal carrier of the touched state (representation tag, raw octet buffer, encoded code points, output octets) |
| `charset_encode(cps)` *(axiom — A-consumed)* | `str.encode(self.charset)` / `bytes(...).encode` — CPython str encoding (called as `value.encode(self.charset)` and `str(value).encode(self.charset)`) | unchanged stdlib encoder the non-buffer branches invoke; not changed by the patch |
| `is_buffer_kind(kind)` | the `isinstance(value, (bytes, memoryview))` type test (post-patch) | pure spec: is `value` one of the two raw-octet-bearing representations |
| `KIND_OCTETS / KIND_VIEW / KIND_TEXT / KIND_OTHER` | the `bytes` / `memoryview` / `str` / fallthrough branches of the `isinstance` cascade | representation tags for the four dispatch arms |

The pre-patch repo symbol the change widens (for the refinement audit, not
referenced from the consumer spec view): the type test `isinstance(value,
bytes)` at `response.py:232`, which the gold patch widens to `isinstance(value,
(bytes, memoryview))`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `value: bytes` | `Value(kind=KIND_OCTETS, buf=<octets>, ...)` | the `bytes` object ↔ a `Value` whose `kind` is `KIND_OCTETS` and whose `buf` is the `PSeq[int]` of its octet values |
| `value: memoryview` | `Value(kind=KIND_VIEW, buf=<octets>, ...)` | a `memoryview` ↔ a `Value` whose `kind` is `KIND_VIEW` and whose `buf` is the `PSeq[int]` of the octets the view exposes (`bytes(view)`) |
| `value: str` | `Value(kind=KIND_TEXT, cps=<code points>, ...)` | a `str` ↔ a `Value` whose `kind` is `KIND_TEXT` and whose `cps` is the `PSeq[int]` of its Unicode code points |
| any other `value` (e.g. an `int`) | `Value(kind=KIND_OTHER, cps=<code points of str(value)>, ...)` | the value ↔ a `Value` whose `cps` is the code points of its native-text rendering `str(value)` |
| the returned `bytes` | `Result().data : PSeq[int]` | the output bytestring ↔ a `PSeq[int]` of its octet values |
| `bytes(value)` (the buffer branch) | `Result().data == v.buf` | `bytes()` of a `bytes`/`memoryview` yields exactly the underlying octets — copies them verbatim, no decode/encode/render |
| `value.encode(charset)` / `str(value).encode(charset)` | `Result().data == charset_encode(v.cps)` | the charset encoder applied to the value's code points (text branch) or to its native-text rendering's code points (other branch) |

`bytes`/`str` indexing/iteration is banned in Nagini, so octets and code points
are carried as `PSeq[int]`; the discrimination is carried by the integer `kind`
tag rather than by `isinstance`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `charset_encode` ↔ `str.encode(charset)` (A-consumed)
**Callee:** CPython `str.encode(encoding)` — the standard text encoder, invoked
by `make_bytes` as `value.encode(self.charset)` (the `str` branch) and
`str(value).encode(self.charset)` (the fallthrough branch). The patch does NOT
change this callee; only the type test guarding the buffer branch is widened.

The axiom encodes only what the proof needs: that the encoder is a **pure,
deterministic function of its code-point argument** (`@Pure @ContractOnly`,
`Ensures(True)`). The proof does not depend on any specific octet value the
encoder produces — only that the non-buffer branches deterministically return
`charset_encode(v.cps)` (the same encoder applied to the same code points),
which is exactly the unchanged behaviour. The weakest sufficient contract is
therefore "a pure function," and that is all the axiom claims; an axiom that
pinned exact UTF-8 bytes would be needlessly strong (and charset-dependent).

The buffer branch (`bytes`/`memoryview`) does NOT call the encoder at all — its
output is the underlying octets verbatim (`bytes(value)`), which is the whole
point of the fix and is modeled directly as `Result().data == v.buf`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL Django `make_bytes`
logic (and `str.encode`) on boundary + fuzz inputs across all four
representations — `bytes`, `memoryview`, `str`, and non-string values — and
asserts: (a) the buffer branch returns the underlying octets verbatim
(`make_bytes(memoryview(b)) == b == make_bytes(b)`), the discriminating
behaviour the F2P test demands; (b) `charset_encode` is a deterministic pure
function of its code-point argument (same input → same output). Imports only
the standard library; exit 0 iff sound.

Flag dependency: none. `str.encode` defaults are irrelevant to the modeled
property (determinism); the charset is supplied by the caller and the buffer
branch — the only behaviour the F2P test pins — never encodes.
