# mapping.md — sympy__sympy-20916

## Symbol binding (base_commit 82298df6a51491bfaad0c6d1980e7e3ca808ae93)

- Modeled function: `split_super_sub` @ `sympy/printing/conventions.py:13`, but
  the **only fixed behavior** is the trailing-digit split step at
  `sympy/printing/conventions.py:65-68`:
  ```python
  m = _name_with_digits_p.match(name)
  if m:
      name, sub = m.groups()
      subs.insert(0, sub)
  ```
  driven by the module-level regex `_name_with_digits_p` @ line 10, which the
  gold patch rewrites:
  - pre-patch: `re.compile(r'^([a-zA-Z]+)([0-9]+)$')`
  - post-patch: `re.compile(r'^([^\W\d_]+)(\d+)$', re.U)`

  The rest of `split_super_sub` (the `^`/`_`/`__` scanning loop) is UNCHANGED by
  the patch and does not affect this step — the `name` handed to the regex is
  the leading token before any `^`/`_`. The bundle models exactly the changed
  step: given the base `name` token, decide whether it splits into
  `(letters, digits)`.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | note |
|---|---|---|
| `name : str` (the base token) | `name : List Char` | per-code-point; Lean `List Char` indexing is total |
| regex group 1 `([^\W\d_]+)` (the base) | `base : List Char` | the leading maximal letter run |
| regex group 2 `(\d+)` (the subscript) | `Option (List Char)` = `some tail` | the trailing all-digit run; `none` when no split |
| `m is None` (no match) | `(name, none)` | name returned unchanged |
| `(name, sub)` from `m.groups()` | `(base, some tail)` | |

Result carrier: the split is modeled as `List Char × Option (List Char)`:
`(base, some subscript)` on a successful split, `(name, none)` otherwise. This
mirrors the Python `if m:` decision (`m.groups()` vs. leaving `name` intact).

### The `$` anchor's end-of-input rule (single-final-newline tolerance)

Python's `$` outside `re.MULTILINE` matches at end of string **or just before
one final `'\n'`** (`re` docs). So `_name_with_digits_p.match("a1\n")` matches
with groups `('a', '1')` — the newline is tolerated and dropped — while
`"a1\n\n"`, `"a1\r"`, `"a1\r\n"` do not match (only exactly one final `'\n'`
is tolerated, and `\r` is not it). The spec models this faithfully: the split
succeeds when the post-digit trailer is empty **or the single char `'\n'`**,
and the tolerated newline is not part of the returned subscript. This rule is
identical pre- and post-patch (it is `re` engine semantics, not the edit).

## Callee provenance (A-reference — validated by G-AX, driven by G-CONF)

The post-patch regex classes are the **unchanged, library-provided** Unicode
character categories that Python's `re` engine consults under `re.U`:

- `isUnicodeLetter c`  ↔ Python `re.match(r'[^\W\d_]', c, re.U)` — a Unicode
  *word* character that is neither a decimal digit nor `_`, i.e. an alphabetic
  character in ANY script (`str.isalpha`-like for the regex `\w` minus `\d`/`_`).
- `isUnicodeDigit c`   ↔ Python `re.match(r'\d', c, re.U)` — a Unicode decimal
  digit in ANY script (e.g. `𝟙` U+1D7D9 MATHEMATICAL DOUBLE-STRUCK DIGIT ONE is
  a `\d` match; `ω` is not).

These CANNOT be computed in vanilla Lean (Lean core `Char.isAlpha`/`Char.isDigit`
are ASCII-only and would misclassify `ω`, `𝟙`, …), so they are declared `opaque`
and their behavior is supplied by the real classification: G-AX runs Python's
`re` engine over boundary + fuzzed code points and asserts the opaque signature
matches; G-CONF uses the real classification to drive the differential test.
They are **A-reference**, NOT consumed axioms — the proof needs no `_prop`
about them (the spec is stated directly over the same `opaque` symbols and
discharged by `rfl`/`simp`).

## Flag dependency

The post-patch regex uses `re.U` (Unicode mode). Both classes are evaluated in
Unicode mode; G-AX fuzzes code points across scripts (ASCII, Greek, Cyrillic,
CJK, mathematical-alphanumeric digits) in `re.U`.

## G-CONF fuzz seed

Pinned seed: **20916** (also referenced in conformance_check.py).
