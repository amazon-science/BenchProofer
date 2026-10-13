# refinement.md — pytest-dev__pytest-7521

The operation-by-operation correspondence between `model.py`'s implementation
(the `captured_readback` impl region and the deep `cr_folded` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `FDCaptureBinary.__init__` (`src/_pytest/capture.py:386-392`)

Gold hunk:
```
             TemporaryFile(buffering=0),  # type: ignore[arg-type]
             encoding="utf-8",
             errors="replace",
+            newline="",
             write_through=True,
         )
```

`EncodedFile` is an `io.TextIOWrapper` subclass (`:177`). Adding `newline=""`
switches the wrapper from its **default** read policy (universal-newline
translation: every line ending — standalone `\r`, `\r\n`, `\n` — rewritten to
`\n`, losing the carriage return) to **no translation** (line endings returned
verbatim). The behaviour the model specifies is the captured-text read-back of
`FDCapture.snap()` (`self.tmpfile.read()`, `:478-484`), which post-patch
reproduces the written code points verbatim.

| # | model.py impl op (`captured_readback`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `written: List[int]` | the `str` text written to the captured fd | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | (no node) | utf-8 encode-on-write / decode-on-read of the byte buffer | R | encode∘decode is the identity on every code point the F2P tests observe (ASCII/whitespace, `errors="replace"` never triggers); mapping.md §2. |
| A3 | `result` built as a verbatim code-point copy of `written`, proven `ToSeq(result) == ToSeq(written)` | reading the captured text back through the now-`newline=""` `EncodedFile` (`snap()` → `TextIOWrapper.read`) | A-reference | the changed read-back operation is modeled **deeply**: the verified identity loop in `captured_readback` IS the verbatim read-back the fix produces. There is **no consumed read-translation axiom** — the proof depends on none. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `io.TextIOWrapper(newline="")` read and asserts it reproduces the written code points verbatim (mapping.md §3.2), and validates the regression's carriage-return-losing fold `cr_folded` == the real default reader (mapping.md §3.1). |
| A4 | `result` returned (a `List[int]`) | the `str` returned by `snap()` / surfaced by `readouterr()` | R | `snap()`'s seek/read/truncate plumbing returns exactly the decoded captured text; modeled as the read-back transform's output (mapping.md §2). |

The discriminating content of the change — a carriage return (U+000D) must be
**preserved**, not folded to a line feed (U+000A) — lives in the postcondition
`ToSeq(Result()) == ToSeq(written)` (model), which under the default reader
fails for any `\r`-bearing input. `model_prepatch.py` reproduces the regression
(`cr_folded`: `\r → \n`) and **fails** that exact postcondition (the
`captured_readback` postcondition `ToSeq(Result()) == ToSeq(written)`), which is
precisely the spec sensing the change (G-DIFF). The F2P inputs `"test\r\n"` and
`"test\r"` are exactly the `\r`-bearing witnesses.

## B. The `cr_folded` deep model (A-reference, not consumed)

`cr_folded` (pure region) is the carriage-return-losing read translation the
regression exhibits. It is shared, byte-for-byte, by both twins (same frozen
spec, G-DIFF's `same_spec`): in `model.py` it documents the behaviour the fix
avoids; in `model_prepatch.py` its fold is the buggy impl the prepatch verifies
against and then fails the preservation postcondition. It is **never a consumed
axiom** — `model.py`'s proof uses only the identity. Its soundness as a model of
the real regression is audited by G-AX:

| # | model.py construct | real callee | tag | justification |
|---|---|---|---|---|
| B1 | `cr_folded(s)` (front-recursive fold, every 13 → 10, else identity) | `io.TextIOWrapper.read` with the **default** newline policy | A-reference | G-AX asserts (i) the default reader's output never contains a carriage return (every captured `\r` lost — the regression), matching `cr_folded`'s defining effect, and (ii) on LF-free inputs the default reader equals `cr_folded` code-point for code-point (mapping.md §3.1). 20000+ fuzz each, 0 violations. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the captured-text read-back — is modeled **deeply** (the verified
identity loop in `captured_readback`, step A3, an **A-reference** to the real
`newline=""` reader; the regression it must avoid spelled out as the `cr_folded`
fold, step B1), not hidden behind an axiom about the function under change.
There is **no consumed `@ContractOnly` axiom** in this bundle.

## D. verify(model) ⇒ resolved

`captured_readback` verifies only if its output equals the written code points
verbatim (A3), i.e. it preserves every carriage return. By R (str ↔ List[int],
utf-8 encode∘decode identity, `snap()` plumbing identity) the verified read-back
equals the text the patched `EncodedFile` reproduces on the tested inputs; by
G-AX the real `io.TextIOWrapper(newline="")` read IS that verbatim read-back
(A-reference, mapping.md §3.2) and the default reader loses carriage returns
exactly as `cr_folded` models (mapping.md §3.1). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited reader behaviour — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX)
and refinement fidelity (this document, G-EQ).
