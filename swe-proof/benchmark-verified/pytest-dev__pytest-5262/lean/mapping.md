# mapping.md — symbol binding & type bijection (pytest-dev__pytest-5262)

## Modeled function
- **Lean** `implementation_mode : List Char → List Char`
- **Python** the `mode` property of `_pytest.capture.EncodedFile` —
  `src/_pytest/capture.py:450-451 @ 58e6a09db` (post-patch:
  `return self.buffer.mode.replace("b", "")`).

The object under spec wraps an underlying byte stream and reports a text-stream
mode to its consumers. The new property reads the underlying stream's mode
string and removes every binary-indicator character `'b'`, keeping all other
characters in order. Before the change there was no such property, so attribute
access fell through to the underlying stream and returned its mode verbatim
(still containing `'b'`). The observable behavior the F2P test demands is simply
that the reported mode contains no `'b'`; the spec pins the full transformation
(remove every `'b'`, preserve everything else in order) so the behavior is
grounded in the input, not merely "b absent".

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `str` (input `self.buffer.mode`) | `List Char` | per-code-point operation; total/sound indexing |
| `str` (output / reported mode) | `List Char` | same character sequence |
| character `c` | `Char` | one code point |
| binary-indicator character `"b"` | `'b'` | literal |
| `s.replace("b", "")` | drop every `'b'`, keep rest in order | for single-char `"b"`, `str.replace` removes every occurrence of that one character |

`self.buffer` is the underlying byte stream; reading its `.mode` attribute is the
input to the modeled function. It is a framing access with no transformation of
its own, so the buffer's mode string is taken directly as `bufferMode`.

## Callee provenance
- The mode-string transformation (`str.replace("b", "")`) is the operation the
  change introduces; it is modeled DEEPLY as the `stripBinary` fold / the `for`
  loop (an **A-reference**, validated by G-AX against the real
  `str.replace("b", "")` builtin), NOT axiomatized.
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.

## Flag dependency
None. `str.replace("b", "")` has no configuration; G-AX fuzzes mode-like strings
plus arbitrary code points.

## G-CONF fuzz seed
Pinned seed: **5262**. ≥10^5 fuzzed inputs over a mode-flavoured alphabet
(`r w a + t x b` oversampled) plus arbitrary BMP/astral code points.
