# mapping.md — psf__requests-2317

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 091991be0da19de9108dbe5e3752917fea3d7fdc`, states the type
abstraction, and gives the provenance of the deep-model reference (the callee
the deep model is validated against by G-AX).

Repo file under change: `requests/sessions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `native_method(content, is_bytes)` | the method-coercion statement `method = builtin_str(method)` in `Session.request` — `requests/sessions.py:428` (changed to `method = to_native_string(method)`) | the modeled changed operation: coerce the `method` token to its native text form |
| `native_method`'s body (the verified copy loop) *(deep model — A-reference)* | `to_native_string` — `requests/utils.py:655` (called at `requests/sessions.py:428` post-patch) | the post-patch coercion: returns a native `str` unchanged and ASCII-decodes a byte string; modeled deeply, validated `native_method == to_native_string` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo symbol the change removes from `Session.request` (for the
refinement audit, not referenced from the consumer spec view): the call
`builtin_str(method)`, where `builtin_str` is `str` on Python 3
(`requests/compat.py:111`). The import edit on `requests/sessions.py:16`
(dropping `builtin_str`, which is no longer used in this function) is a pure
import-list bookkeeping change with no behavioural content.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `method` argument, which is either a native `str` or a `bytes` object | `content: List[int]` (the carried character / byte values) + `is_bytes: bool` (which kind of token it was) | for a `str` token, `content[k] == ord(method[k])`; for a `bytes` token, `content[k] == method[k]` (the byte value). `is_bytes == True` iff `method` is a `bytes` object. The two carriers coincide because the methods of interest are ASCII (every value `< 128`), so a byte value and the code point of its ASCII decoding are equal. |
| `str` / `bytes` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str`/`bytes` `+`/slice/`len`/index |
| the native-`str` RESULT of the coercion | `List[int]` of character values | `Result()[k] == ord(method_native[k])` |
| the coercion returns in finite time (bounded work over a finite token) | `Requires(MustTerminate(len(content) + 2))` on `native_method`, discharged in the copy loop by the strictly decreasing, bounded-below measure `n - j` | total-correctness obligation: the native token must actually be delivered, not merely be correct if it returns |

`str`/`bytes` indexing/iteration is banned in Nagini, so the carrier is
`List[int]` throughout; the specification is phrased over `PSeq[int]` via
`ToSeq`. The `Requires` restricts the carrier to ASCII (every value `< 128`)
without an embedded quote (`39`) or backslash (`92`): this is the regime of
HTTP method tokens, and the bound `< 128` is what makes a byte value equal to
the code point of its ASCII decoding, so the single carrier serves both the
text and byte forms (the quote/backslash exclusions are vestigial of an earlier
model and are harmless — they only shrink the domain, never enlarge it).

## 3. Callee provenance (the deep-model reference — checked by G-AX / axiom_check.py)

### 3.1 `native_method` body ↔ `to_native_string` (A-reference)
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

On the Python 3 eval interpreter (`builtin_str == str`, `is_py2 == False`):
a native `str` token is returned unchanged; a `bytes` token is `string.decode('ascii')`.
For an ASCII token both branches yield the token's own characters — i.e. the
identity on the carried code-point sequence. This is exactly what the deep
model `native_method` computes (the verified copy loop returning
`ToSeq(Result()) == ToSeq(content)`). There is **no `to_native_string` axiom
the proof consumes**; the deep model is validated equal to the real callee
out-of-band by axiom_check.py (G-AX) over boundary + fuzz tokens.

The pre-patch coercion the change removes is `builtin_str(method)` = `str(method)`
on Python 3 (`requests/compat.py:111`): for a `bytes` object it produces the
object's textual `b'...'` rendering, a sequence strictly longer than the carried
content. `model_prepatch.py` exhibits that wrong behaviour concretely (byte
branch building prefix `[98, 39]`, content, suffix `[39]`); it is rejected by
the dominant postcondition `ToSeq(Result()) == ToSeq(content)` (the result
sequence differs and is length `len+3 ≠ len`), so no separate spec oracle for
the rejected behaviour is required (G-DIFF).

**Soundness check (G-AX):** `axiom_check.py` runs the real `to_native_string`
on boundary method tokens (`GET`, `POST`, etc., as both `str` and `bytes`, plus
the empty token), on an EXHAUSTIVE single-value sweep of the whole Requires
domain (every code point `0..127` except `39`/`92`, as both text and bytes), and
on 20000 randomized fuzz tokens drawn from that same full domain alphabet,
asserting the deep model `native_method == to_native_string` (A-reference, §3.1).
The fuzz alphabet is generated directly from the model `Requires`, so the
checked domain equals the spec domain (no strict-subset hole). It imports only
requests' own `to_native_string` (the very callee the patch introduces) and
stdlib; exit 0 iff sound.
