# refinement.md — operation correspondence (pytest-dev__pytest-7521)

Maps every op in `implementation_readCaptured` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patch adds `newline=""` to the `EncodedFile(TemporaryFile(...), ...)` call in
`FDCaptureBinary.__init__`. The observable effect is on the readback path
(`FDCapture.snap()` → `tmpfile.read()`): `newline=None` (base) applies
universal-newline translation (`\r\n`,`\r` → `\n`); `newline=""` (patched)
returns the buffered text verbatim. We model the readback transformation
directly.

## Post-patch (`Solution.lean` — the verbatim readback)

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `written : List Char` | the character stream written into the capture tmpfile | R | str ↔ List Char, per-code-point (mapping.md) |
| 2 | `for c in written do out := out.push c` | `read()` on a `TextIOWrapper` with `newline=""` — no newline translation, text returned verbatim | R | the **changed op**: the new `newline=""` flag disables translation, so the readback is the identity copy. Modeled deeply (the identity scan), NOT axiomatized. |
| 3 | `return out.toList` | the `str` returned by `snap()` | R/I | the assembled verbatim text |

## Pre-patch (`Solution_prepatch.lean` — universal-newline translation)

| # | Lean impl op | base-source counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `written : List Char` | same written stream | R | as above |
| 2 | `if c = '\r' then push '\n'; prevCR := true` | universal-newline: a CR becomes LF | R | base `newline=None` translation rule |
| 3 | `else if c = '\n' then (if prevCR then skip else push '\n')` | universal-newline: an LF right after a CR is swallowed (so `\r\n`→`\n`); a standalone LF passes through | R | base `newline=None` translation rule |
| 4 | `else push c; prevCR := false` | any other code point passes through | R/I | non-newline chars are unchanged |
| 5 | `return out.toList` | the corrupted `str` returned by `snap()` | R/I | assembled translated text |

No A-consumed rows: the proof discharges the identity directly; no UNCHANGED
callee property is assumed (axioms region empty → G-AX is a skip stub).
No A-reference rows: `TextIOWrapper.read` is not abstracted behind a model
needing G-AX validation — its two newline modes are reproduced concretely as R
ops (identity post-patch, translation pre-patch). No changed-inexpressible op.

## Discriminating clause (G-DIFF)
The frozen `problem_spec_readCaptured` requires `result = written` (verbatim).
On any input containing a `\r` — e.g. `written = ['  0%', '\r']` i.e.
`['  ','0','%','\r']` (the issue's reproducer `print('...', end='\r')`) — the
post-patch impl returns it unchanged (spec holds), while the prepatch impl
returns the stream with `\r`→`\n` (and `\r\n`→`\n`), so `result ≠ written` and
the prepatch `correct_readCaptured` cannot close. This mirrors the F2P tests
`test_cafd_preserves_newlines[\r]` and `[\r\n]` (which the prepatch fails) versus
`[\n]` (which both pass — LF-only is unchanged by either mode).
