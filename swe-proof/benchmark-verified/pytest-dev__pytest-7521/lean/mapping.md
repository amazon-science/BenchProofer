# mapping.md — symbol binding & type bijection (pytest-dev__pytest-7521)

## Instance
- repo: pytest-dev/pytest @ base_commit `41d211c24a6781843b174379d6d6538f5c17adb9`
- changed file: `src/_pytest/capture.py`
- changed function: `FDCaptureBinary.__init__` (the `EncodedFile(...)` construction)

## What the fix does (cold-derived from problem_statement + patch + base source)
`FDCaptureBinary.__init__` (`src/_pytest/capture.py:357`) wraps the capture
temporary file in an `EncodedFile` (a subclass of `io.TextIOWrapper`,
`capture.py:177`). Captured output is later read back by `FDCapture.snap()`
(`capture.py:478`) via `self.tmpfile.read()`, which decodes the buffer into
`str`. Because the wrapper was constructed WITHOUT a `newline=` argument
(`capture.py:386–392` at base), `TextIOWrapper` defaults to `newline=None`,
which enables **universal-newline translation on read**: every `\r\n` and every
lone `\r` is collapsed to a single `\n`. So captured text containing carriage
returns (e.g. `'  0%\r'`) was corrupted to `'  0%\n'`.

The patch adds `newline=""` to that `EncodedFile(...)` call
(`patch.diff` hunk @ line 388): with `newline=""`, translation is disabled and
`read()` returns the buffered text **verbatim**.

Empirically confirmed (CPython `io.TextIOWrapper`):
```
written      newline=None (pre)   newline="" (post)
'  0%\r'  -> '  0%\n'             '  0%\r'
'a\r\nb'  -> 'a\nb'               'a\r\nb'
'a\r\r\nb'-> 'a\n\nb'             'a\r\r\nb'
'a\nb'    -> 'a\nb'               'a\nb'      (LF-only unchanged either way)
```

## Modeled function
`implementation_readCaptured` models the *readback transformation*: the function
from the character stream WRITTEN into the capture buffer to the text RETURNED
to the caller by `snap()`. Post-patch this is the identity (verbatim copy);
pre-patch it is universal-newline translation.

| Lean symbol | Python binding (file:line @ base_commit) |
|---|---|
| `implementation_readCaptured` (Solution) | the `newline=""` readback path: `EncodedFile(...)` @ `capture.py:386–392` + `FDCapture.snap` read @ `capture.py:478–484` |
| `implementation_readCaptured` (prepatch) | the base `newline=None` readback path (same lines, before the patch) |
| `problem_spec_readCaptured` | the contract `snap() text == bytes-as-written text` |

## Type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| captured text as a sequence of Unicode code points (`str`) | `List Char` |
| `len(s)` | `.length` |
| character `'\r'` (U+000D) | `'\r'` |
| character `'\n'` (U+000A) | `'\n'` |
| `str` identity (verbatim readback) | `result = written` |

Per-code-point modeling is used (`List Char`), since the fix is entirely about
which code points survive the read. The bijection is the obvious Unicode
code-point ↔ `Char` map.

## Callee provenance / flag deps
- `io.TextIOWrapper.read()` is the unchanged callee whose behavior the readback
  depends on. The fix does NOT change `TextIOWrapper`; it changes the **flag**
  (`newline`) passed at construction. The flag dependency is the crux: with
  `newline=None` translation is ON, with `newline=""` it is OFF. This is modeled
  DEEPLY (the prepatch impl spells out the translation; the postpatch impl is the
  identity), so `TextIOWrapper.read` is NOT an axiomatized callee — no `opaque`
  decl, no `_prop` axiom. The axioms region is empty.

## G-CONF fuzz seed
Pinned seed: `7521`. Fuzz domain: random strings over an alphabet that
oversamples `\r`, `\n`, and ASCII letters (so `\r`, `\r\n`, `\r\r\n`, trailing
`\r`, and plain text are all exercised), lengths 0–64, ≥10^5 cases.
