# mapping.md — psf__requests-2931

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5f7a3a74aab1625c2bb65f643197ee885e3da576`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one modeled callee.

Repo file under change: `requests/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `encodePayload (data : Payload)` | `RequestEncodingMixin._encode_params(data)` — `requests/models.py:75` (changed body line 83-84) | modeled changed function: the str/bytes branch of the param/body encoder (the F2P-pinned fix) |
| `toNativeString` *(deep model — A-reference)* | `requests.utils.to_native_string(string, encoding='ascii')` — `requests/utils.py:686` | UNCHANGED callee; the native-string coercion. Deep model validated `== ` the real callee by axiom_check.py (G-AX), NOT consumed as an axiom. Used by the prepatch baseline to reproduce the pre-patch coercion bug |
| `Payload` (`.text` / `.binary`) | the `str` / `bytes` runtime alternatives of `data` | the touched value carrier: text vs binary payload |

The patched repo symbol modeled here is `_encode_params`. The spec-view
identifiers (`encodePayload`, `toNativeString`, `Payload`) do not echo it.
`to_native_string` is named verbatim in the public `problem_statement` ("fails
due to calling to_native_string"), so the abstract `toNativeString` is public,
not a leak.

The gold patch's second hunk (`prepare_url`, `models.py:387-388`, a
behaviour-preserving `to_native_string` guard for str/bytes params) is **not**
modeled: it is not F2P-pinned and is behaviour-preserving, so modeling it would
disclose the gold's compensating-edit design without strengthening the
F2P-pinned obligation (refinement.md §B). It remains in `patch.diff` (gold
verbatim) so the patch still resolves.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a text payload — Python `str` | `Payload.text (List Char)` | `s` (str) ↔ `.text s.toList`; `str` concat ↔ `List` `++`; empty `str` ↔ `.text []` |
| a binary payload — Python `bytes` | `Payload.binary (List UInt8)` | `bs` (bytes) ↔ `.binary` of its octet list; `len(bs)` ↔ `b.length` |
| a single octet `u` (0..255) | Lean `UInt8` | `u` ↔ `UInt8.ofNat u`; decode to code point: `chr(u)` ↔ `Char.ofNat u.toNat` |
| the str-vs-bytes runtime distinction (`isinstance(x, bytes)`) | the `Payload` constructor tag (`.text` / `.binary`) | the DECIDABLE distinction the consumer observes (`isinstance(request.body, bytes)`); `DecidableEq Payload` makes `.binary b ≠ .text s` |

The carrier is a tagged `Payload` (not a bare `List Char`) precisely because the
behaviour under test is **type preservation** — `isinstance(body, bytes)` — which
is invisible to a content-only model. Lean's `Payload` constructor tag is the
faithful analogue of the Python runtime type.

## 3. Callee provenance (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `toNativeString` deep model ↔ `requests.utils.to_native_string`
**Callee (UNCHANGED):** `to_native_string(string, encoding='ascii')`
(`requests/utils.py:686`). Source at base_commit (Python-3 branch):

```python
def to_native_string(string, encoding='ascii'):
    if isinstance(string, builtin_str):   # str on py3 -> identity
        out = string
    else:                                 # bytes -> decode(encoding)
        out = string.decode(encoding)     # is_py2 is False in the image
    return out
```

On py3 (the container interpreter): a `str` is returned unchanged; `bytes` is
`decode('ascii')`-d. The deep model `toNativeString` (Solution.lean pure region)
encodes exactly this: identity on `.text`, and per-octet decode
`Char.ofNat u.toNat` on `.binary` — which on the ASCII octets `0..127` is
`bytes([u]).decode('ascii')`. Always yields a `.text` payload (the real callee
always returns `str`).

**FLAG / DOMAIN dependency:** the default `encoding='ascii'` means the bytes
domain is the ASCII octets `0..127`; outside that range the real callee raises
`UnicodeDecodeError`, and the gold-patched `_encode_params` passes such payloads
through untouched, so the coercion is never reached. G-AX fuzzes exactly the
in-domain region (where model == real exactly) and ALSO confirms the real callee
raises on out-of-ASCII bytes, documenting the domain choice.

**Soundness check (G-AX):** `axiom_check.py` runs the real `to_native_string` on
text + ASCII-bytes boundary inputs plus 20 000 fuzz inputs, asserting
`toNativeString_model == to_native_string` and that the result is always a
native `str`. There are **no consumed axioms** in this bundle; this is the only
modeled callee. Imports only the repo's own `requests`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` seed their `random.Random` with
**`2931`** so the consumer-side verdict (§11.3) is reproducible.
`conformance_check.py`'s I shadow transliterates `encodePayload` (identity) and
compares it against the gold-patched `_encode_params` (bytes preserved as bytes).
`axiom_check.py`'s A-reference check validates the `toNativeString` deep model
`== ` the real `to_native_string`. Bytes fuzz is ASCII-only per §3.1.
