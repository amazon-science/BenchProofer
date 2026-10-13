# refinement.md — pytest-dev__pytest-7521

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `readbackStream` `do` block, the deep `readback` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — **A-consumed** where the proof uses the axiom's `ensures`,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The capture-stream read-back site — `FDCaptureBinary.__init__` / `FDCapture.snap`

Gold hunk (`src/_pytest/capture.py:388`):
```
              TemporaryFile(buffering=0),  # type: ignore[arg-type]
              encoding="utf-8",
              errors="replace",
+             newline="",
              write_through=True,
```

The captured FD's tmpfile is wrapped in an `EncodedFile`(`io.TextIOWrapper`).
Adding `newline=""` disables universal-newline translation, so what is written
into the buffer is read back verbatim by `FDCapture.snap` (`res =
self.tmpfile.read()`). The modeled function `readbackStream` is that write→read
round-trip: `text` is the buffered code-point sequence, `out` the recovered one.

| # | Solution.lean impl op (`readbackStream`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text : List Char` | the code points previously written into the capture tmpfile | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | result is `readback text`, the verbatim per-code-point copy computed by the backward `while` fold (`result := c :: result`, peeling `text[i-1]`) | the `tmpfile.read()` of the `newline=""`-configured `TextIOWrapper` in `snap()` | A-reference + I | the read-back operation is modeled **deeply**: `readback` (pure region) and the verified loop ARE the recovered sequence. No consumed read-back axiom. The fold ops (`c :: result`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `newline=""` stream read-back is the **A-reference** G-AX validates. mapping.md §3.1. |
| A3 | `out = readback text` **and** `out = text` (via `readback_id`) | the post-patch behaviour: read-back is verbatim (no newline rewriting) | A-reference + I | `readback_id` proves the deep model is the identity, so the spec pins `out = text`. This is exactly the post-patch guarantee; the F2P assertion `out.endswith(nl)` for `nl ∈ {\n, \r\n, \r}` holds iff read-back preserves the trailing newline verbatim. |

Discriminating content of the change — a buffered carriage return (U+000D) is
recovered **as U+000D**, not rewritten to a line feed (U+000A) — lives in the
`out = text` postcondition (model) ⇔ the `newline=""` configuration (real). The
pre-patch wrapper omitted `newline`, applying universal-newline translation
(`\r`→`\n`, `\r\n`→`\n`); `Solution_prepatch.lean` reproduces that (`if c = '\r'
then '\n' else c`) and **fails** the `out = text` clause: the unsolved goal is
`¬ text[i-1]!.getD … = '\x0d'`, i.e. it cannot rule out a carriage return —
precisely the U+000D behaviour the F2P tests `[\r]` and `[\r\n]` exercise (G-DIFF).

## B. No second change site

The patch is a single one-line addition (`newline=""`). There is no second
independently-fixed behavior, so there is one `Solution_prepatch.lean` and no
`Solution_prepatch_<k>.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the stream's newline handling on read — is modeled **deeply** (the spelled-out
identity fold `readback` + `readback_id`, step A2/A3, an A-reference + I), not
hidden behind an axiom about the function under change: there is **no consumed
axiom at all**. The deep model captures the CHANGED property (verbatim vs.
translated) directly and G-AX validates it against the real `newline=""` stream.

## D. verify(Solution) ⇒ resolved

`readbackStream` verifies only if its output equals the verbatim per-code-point
copy of the input (`out = readback text = text`, A2/A3). By R (`str ↔ List
Char`, the UTF-8 encode/decode round-trip identity on the tested code points)
the verified read-back equals the patched `TextIOWrapper(..., newline="").read()`
on the captured text; by G-AX the deep model `readback` equals the real
`newline=""` read-back (A-reference, including the negative check that the
pre-patch default-newline wrapper translates `\r`→`\n`); by G-CONF the R/I
transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited deep model — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
