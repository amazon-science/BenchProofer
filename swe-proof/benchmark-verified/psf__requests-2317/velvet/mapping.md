# mapping.md — psf__requests-2317

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 091991be0da19de9108dbe5e3752917fea3d7fdc`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference (the callee the deep model is
validated against by G-AX).

Repo file under change: `requests/sessions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `nativeToken (token : List Char)` | the method-coercion statement `method = builtin_str(method)` in `Session.request` — `requests/sessions.py:428` (changed to `method = to_native_string(method)`) | the modeled changed operation: coerce the `method` token to its native text form |
| `nativeSeq (token : List Char)` *(deep model — A-reference)* | `to_native_string` — `requests/utils.py:655` (called at `requests/sessions.py:428` post-patch) | pure spec: the native text representation of a token; deep model of the post-patch coercion, validated `nativeSeq == to_native_string` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `nativeChar (c : Char)` | the per-character contribution of the coercion | pure spec: the native representation of one carried token character (itself) |

The pre-patch repo symbol the change removes from `Session.request` (refinement
audit only, not referenced from the consumer spec view): the call
`builtin_str(method)`, where `builtin_str` is `str` on Python 3
(`requests/compat.py:96,111`). The import edit on `requests/sessions.py:16`
(dropping `builtin_str`, which is no longer used in this function) is a pure
import-list bookkeeping change with no behavioural content.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `method` argument, which is either a native `str` or a `bytes` object carrying ASCII bytes | `token : List Char` (the carried character / byte values as characters) | for a `str` token, `token[k] == Char.ofNat (ord method[k])`; for a `bytes` token, `token[k] == Char.ofNat method[k]` (the byte value). The two carriers coincide because the methods of interest are ASCII (every value `< 128`), so a byte value and the code point of its ASCII decoding are equal. |
| the native-`str` RESULT of the coercion | `List Char` of character values | `out[k] == Char.ofNat (ord method_native[k])`; `out` ↔ `to_native_string(method)` materialized as its character sequence |
| `str`/`bytes` value inside a specification | `List Char` | `str` concat ↔ `List` `++`; `len(method)` ↔ `token.length`; empty token ↔ `[]`; index ↔ `List` index |

Lean `List Char` indexing is total and sound (no Nagini `List[int]`
workaround needed); the carrier is `List Char` because the operation is
per-code-point. The methods of interest are ASCII (every value `< 128`), the
regime in which a byte token's textual-object rendering is exactly the `b'...'`
wrapping and in which a byte value equals the code point of its ASCII decoding,
so the single carrier serves both the text and byte forms.

## 3. Callee provenance (the deep-model reference — checked by G-AX / axiom_check.py)

### 3.1 `nativeSeq` deep model ↔ `to_native_string` (A-reference)
**Callee:** requests' own `to_native_string(string, encoding='ascii')`,
`requests/utils.py:655`:

```python
def to_native_string(string, encoding='ascii'):
    out = None
    if isinstance(string, builtin_str):   # builtin_str is str on Py3
        out = string
    else:
        if is_py2:
            out = string.encode(encoding)
        else:
            out = string.decode(encoding)
    return out
```

On the Python 3 eval interpreter (`builtin_str == str`, `is_py2 == False`): a
native `str` token is returned unchanged; a `bytes` token is
`string.decode('ascii')`. For an ASCII token both branches yield the token's own
characters — i.e. the identity on the carried code-point sequence. This is
exactly what the deep model `nativeSeq` computes (the verified copy loop
returning `out = nativeSeq token` with `nativeSeq token = token`). There is **no
`to_native_string` axiom the proof consumes**; the deep model is validated equal
to the real callee out-of-band by axiom_check.py (G-AX) over boundary + fuzz
tokens.

The pre-patch coercion the change removes is `builtin_str(method)` = `str(method)`
on Python 3 (`requests/compat.py:96,111`): for a `bytes` object it produces the
object's textual `b'...'` rendering, a sequence strictly longer than the carried
content (a leading marker character `b`, a surrounding pair of quote characters).
`Solution_prepatch.lean` exhibits that wrong behaviour concretely (byte branch
emitting prefix `['b', '\'']`, the content, suffix `['\'']`); it is rejected by
the dominant postcondition `out = token` (equivalently `out = nativeSeq token`
and `out.length = token.length`), so no separate spec oracle for the rejected
behaviour is required (G-DIFF).

**Soundness check (G-AX):** `axiom_check.py` runs the real `to_native_string`
on boundary method tokens (`GET`, `POST`, etc., as both `str` and `bytes`, plus
the empty token), on an exhaustive single-value sweep of the ASCII domain
(every code point `0..127`, as both text and bytes), and on randomized fuzz
tokens drawn from that same ASCII alphabet, asserting the deep model
`nativeSeq == to_native_string`. The fuzz alphabet is generated directly from the
spec domain (ASCII), so the checked domain equals the spec domain. It imports
only requests' own `to_native_string` (the very callee the patch introduces) and
stdlib; exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`2317`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`nativeSeq` (R/I-tagged ops — the identity copy of the carried character
sequence) to Python and compares it against the patched coercion behaviour
(`to_native_string(method)`). The impl region's computed `out` contains no
A-tagged callee output (the deep model `nativeSeq` is the A-reference validated
by G-AX, and it IS the computed value), so the shadow is the R/I leg and
conf_skip is `false`.
