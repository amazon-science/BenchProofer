# mapping.md — pytest-dev__pytest-7521

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 41d211c24a6781843b174379d6d6538f5c17adb9`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo file under change: `src/_pytest/capture.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `readbackStream (text : List Char)` | the read-back of the captured FD buffer: `FDCaptureBinary.__init__`'s `tmpfile` construction (`src/_pytest/capture.py:385-392`) feeds `FDCapture.snap` (`src/_pytest/capture.py:478-484`, `res = self.tmpfile.read()`); `text` is the sequence of code points previously written into that buffer | the modeled changed function (text-capture read-back) |
| `readback (cs : List Char)` *(deep model — A-reference)* | the decode/read-back transformation the buffered text stream applies on `read()` — i.e. `io.TextIOWrapper(buffer, encoding="utf-8", errors="replace", newline="", write_through=True)` after the patch (`src/_pytest/capture.py:385-392`) | pure spec: the content recovered when buffered stream text is read back; deep model of the (unchanged-callee) stream reader, validated `readback == real read-back` by axiom_check.py (G-AX), NOT consumed as an axiom |

The behavioural distinction the change makes (refinement audit only, not in the
consumer spec view): pre-patch, the wrapper is built **without** the newline
argument, so the platform default universal-newline mode rewrites every
carriage return (U+000D) and CR+LF pair to a single line feed (U+000A) on read;
post-patch it is built with `newline=""`, so read-back is verbatim.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the captured text `str` (the bytes previously written, decoded by the wrapper) and `snap()`'s returned `str` | `List Char` | `s` (Python str) ↔ `s`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| the buffer write/decode round-trip (`EncodedFile`/`FDCapture`) | identity round-trip carrier | the patched stream encodes UTF-8 on write and decodes UTF-8 on read with `errors="replace"`; on the printable + newline code points the F2P/P2P tests exercise this is the identity on `str`, and the only behavioural variable is newline translation (modeled by `readback`) |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-code-point.

## 3. Callee provenance — the deep model (kind-A, checked by G-AX)

### 3.1 `readback` deep model ↔ the patched text-stream read-back (A-reference)

**Callee:** `io.TextIOWrapper.read()` configured exactly as the patched
`FDCaptureBinary.__init__` configures it:

```python
EncodedFile(                       # EncodedFile(io.TextIOWrapper)
    TemporaryFile(buffering=0),
    encoding="utf-8",
    errors="replace",
    newline="",                    # <-- the post-patch configuration
    write_through=True,
)
```

The read-back transformation is modeled **deeply** by `readback` in the `pure`
region (with the `readback_id` lemma proving it is the identity); there is **no
consumed `readback` axiom**. With `newline=""`, `TextIOWrapper` disables
universal-newline translation in BOTH directions: bytes written pass through
unchanged, and on `read()` no `\r`/`\r\n` is rewritten to `\n`. Hence the
write→read round-trip recovers the buffered code points verbatim — which is what
`readback`/`readback_id` encode (`readback cs = cs`).

The single behavioural change the F2P tests observe is exactly here: a buffered
carriage return (U+000D) survives read-back instead of being rewritten to a line
feed (U+000A). `Solution_prepatch.lean` reproduces the pre-patch
universal-newline translation (`'\r' → '\n'`) and **fails** the `out = text`
postcondition on any input containing U+000D (G-DIFF).

**Soundness check (G-AX):** `axiom_check.py` constructs the real patched stream
(a `TextIOWrapper` with the exact post-patch arguments over a `BytesIO`), writes
each test input, reads it back, and asserts the recovered string equals the
input verbatim (`readback == identity`) over boundary cases (every newline
form: `\n`, `\r`, `\r\n`, `\n\r`, lone/runs/mixed) plus 20 000 randomized fuzz
strings. It also asserts the *negative*: the pre-patch (default-newline) wrapper
DOES translate `\r`→`\n`, so the modeled distinction is real and the fix is
necessary. Imports only stdlib `io`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`7521`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`readback` (the R/I-tagged identity fold) to Python and compares it against
patch.diff's behaviour — the post-patch stream's write→read round-trip
(`TextIOWrapper(..., newline="")`). There is no A-tagged callee left as a live
repo call in the computed `out` (the read-back is the deep model itself,
validated by G-AX), so the escape shadow is pure R/I.
