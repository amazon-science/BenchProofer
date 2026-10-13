# mapping.md — pytest-dev__pytest-7521

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 41d211c24a6781843b174379d6d6538f5c17adb9`, states the type
abstraction, and gives the provenance of the deep-model reference (callee
source + the exact behaviour validated by G-AX).

Repo file under change: `src/_pytest/capture.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `captured_readback(written)` | the captured-text read-back of an fd-capture: `FDCapture.snap()` calling `self.tmpfile.read()` on the `EncodedFile` constructed in `FDCaptureBinary.__init__` (`src/_pytest/capture.py:386-392`, read at `:478-484`) | the modeled changed behaviour: the text a captured fd reproduces when read back |
| `cr_folded(s)` *(deep model — A-reference)* | the read-side newline translation of `io.TextIOWrapper` (the class `EncodedFile` subclasses, `src/_pytest/capture.py:177`) when newline preservation is NOT requested | pure spec: the carriage-return-losing translation capture must avoid; validated == the real reader's carriage-return handling by axiom_check.py (G-AX), NOT consumed as an axiom |

The construction site the change edits: `EncodedFile(TemporaryFile(buffering=0),
encoding="utf-8", errors="replace", write_through=True)` at
`src/_pytest/capture.py:386-392`. `EncodedFile` is an `io.TextIOWrapper`
subclass (`:177`), so its read behaviour is governed by the `newline` argument
its constructor forwards to `TextIOWrapper`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the text written to the captured fd and the `str` returned by `snap()`/`readouterr()`) | `List[int]` of Unicode code points | `s[k]` ↔ `written[k] == ord(s[k])`; `len(s)` ↔ `len(written)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the byte round trip (encode to utf-8 on write, decode on read) | identity on code points | the F2P inputs (`"test\n"`, `"test\r\n"`, `"test\r"`) are pure ASCII/whitespace; utf-8 encode∘decode is the identity on every code point the tests observe, and `errors="replace"` never triggers. The OBSERVED behavioural difference is entirely the newline translation, which is what the model carries. |
| `FDCapture.snap()` seek/read/truncate plumbing | omitted | mechanical buffer bookkeeping; it returns exactly the decoded text of the captured bytes — modeled as the read-back transform of `written`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `cr_folded` deep model ↔ `io.TextIOWrapper` read translation (A-reference)
**Callee:** CPython `io.TextIOWrapper.read`, the read-side universal-newline
translation. `EncodedFile(io.TextIOWrapper)` is constructed without forwarding a
`newline` argument at base_commit, so `TextIOWrapper` uses its **default**
newline policy on read. Per the CPython docs
(https://docs.python.org/3/library/io.html#io.TextIOWrapper):

> If `newline` is `None`, universal newlines mode is enabled. Lines in the input
> can end in `'\n'`, `'\r'`, or `'\r\n'`, and these are translated into `'\n'`
> before being returned to the caller. ... If `newline` is `''`, universal
> newlines mode is enabled but line endings are returned to the caller
> untranslated.

So the **default** reader rewrites every line ending — standalone `'\r'`,
`'\r\n'`, and `'\n'` — to `'\n'`, **losing the carriage return**. The patch
forwards `newline=""`, which disables translation: line endings are returned
untranslated, i.e. **verbatim**.

The changed read-back behaviour is modeled **deeply** by the `@Pure`
front-recursive fold `cr_folded` (pure region): every carriage return (13) →
line feed (10), all else identity. There is **no `@ContractOnly` axiom** the
proof consumes. `cr_folded` is validated against the real reader out-of-band by
axiom_check.py (G-AX), on the two properties that bind it soundly:

* **carriage-return loss (universal):** the default reader's output NEVER
  contains a carriage return — exactly `cr_folded`'s defining effect (every
  13 → 10). Checked on 21 boundary + 20000 fuzz inputs.
* **exact equality on lone-CR inputs:** when the input contains no line feed,
  the default reader's only translation is `'\r' → '\n'`, so it equals
  `cr_folded` code-point for code-point. Checked on 21 boundary + 20000 fuzz
  LF-free inputs.

(`cr_folded` deliberately does NOT model the `'\r\n' → '\n'` *collapse* — that
two-character fold is not needed to express the regression. The single tested
defect, carriage-return loss, is fully captured by `'\r' → '\n'`, which on the
F2P inputs `"test\r\n"` and `"test\r"` already breaks the `endswith('\r\n')` /
`endswith('\r')` assertions. The deep model is the *weakest* fold that exhibits
the bug; G-AX validates it against the real reader on exactly those properties.)

### 3.2 The verified (fixed) behaviour ↔ `io.TextIOWrapper(newline="")` read
**Callee:** CPython `io.TextIOWrapper.read` with `newline=""` (what the gold
patch forwards). axiom_check.py confirms that reading the captured bytes back
through `newline=""` reproduces the written code points VERBATIM (the identity)
— exactly model.py's postcondition `ToSeq(Result()) == ToSeq(written)` — on the
F2P-shaped inputs plus boundary and 20000 fuzz cases. This is the soundness of
the *fix* the model.py implementation encodes (and the gold patch realizes).

**Flag dependency:** the soundness of both 3.1 and 3.2 is exactly the
distinction between `TextIOWrapper`'s default `newline=None` (regression) and
`newline=""` (fix); axiom_check.py exercises both explicitly. utf-8 encoding
with `errors="replace"` (the constructed wrapper's other arguments) is the
identity on every code point the tests observe and is held fixed in the round
trip.
