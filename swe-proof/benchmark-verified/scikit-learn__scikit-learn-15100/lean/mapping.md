# mapping.md — scikit-learn__scikit-learn-15100

## Symbol binding (file:line @ base_commit af8a6e592a1a15d92d77011856d5aa0ec4db4c6c)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_stripAccents` / `problem_spec_stripAccents` / `correct_stripAccents` | `strip_accents_unicode(s)` | `sklearn/feature_extraction/text.py:114-137` |
| `isAscii` | `c` is ASCII-encodable (`ord(c) < 128`) | post-patch `text.py:133` (the `s.encode("ASCII", strict)` test) |
| `canonDecompose` (opaque) | `unicodedata.normalize('NFKD', s)` | `text.py:132/136` |
| `isCombiningMark` (opaque) | `unicodedata.combining(c)` | `text.py:137` |

The modeled function is `strip_accents_unicode`, the only behavior the patch
changes and the only behavior the FAIL_TO_PASS test
(`test_strip_accents`) observes.

### What the function does

**Pre-patch (base_commit):**
```python
def strip_accents_unicode(s):
    normalized = unicodedata.normalize('NFKD', s)
    if normalized == s:
        return s
    else:
        return ''.join([c for c in normalized if not unicodedata.combining(c)])
```

**Post-patch (patch.diff):**
```python
def strip_accents_unicode(s):
    try:
        # If `s` is ASCII-compatible, then it does not contain any accented
        # characters and we can avoid an expensive list comprehension
        s.encode("ASCII", errors="strict")
        return s
    except UnicodeEncodeError:
        normalized = unicodedata.normalize('NFKD', s)
        return ''.join([c for c in normalized if not unicodedata.combining(c)])
```

The patch REPLACES the early-return guard. Pre-patch the function returns the
input unchanged when its NFKD decomposition equals the input — which is TRUE for
any string already in decomposed form (e.g. `"n" + "̃"`), so its combining
marks are never stripped (the reported bug). Post-patch the function returns the
input unchanged ONLY when it is pure ASCII (no code point ≥ 128); any string
containing a non-ASCII code point — pre-composed OR decomposed — falls through to
the unchanged decompose-and-drop-combining-marks branch. The decomposition and
the combining-mark filter are UNCHANGED by the patch.

### Lean modeling

- A string is `List Char` (per-code-point; Lean indexing total/sound).
- `isAscii c := decide (c.toNat < 128)`. Python's `s.encode("ASCII",
  errors="strict")` raises `UnicodeEncodeError` iff some code point is ≥ 128, so
  "s is ASCII-encodable" ⇔ "every code point < 128" ⇔ `s.all isAscii`. This is
  the discriminating clause the patch introduces (the R refinement of the
  `encode`/exception mechanism).
- `canonDecompose` (opaque) models `unicodedata.normalize('NFKD', ·)` — an
  unchanged standard-library decomposition the function reads but does not
  redefine. Declared `opaque` so it appears in the executable impl; the proof
  consumes NO property of it (A-reference). Validated against the real callee by
  G-CONF.
- `isCombiningMark` (opaque) models `unicodedata.combining(·) != 0` — the
  unchanged standard-library combining-class predicate. A-reference; validated by
  G-CONF.
- The stripping branch `''.join([c for c in normalized if not
  unicodedata.combining(c)])` is `(canonDecompose s).filter (fun c =>
  !isCombiningMark c)` — per-code-point filter then concatenation.
- The post-patch `implementation_stripAccents` branches on `s.all isAscii`; the
  pre-patch `Solution_prepatch.lean` branches on `canonDecompose s = s` — the
  single discriminating difference.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `str` | `List Char` | per-code-point |
| `ord(c) < 128` | `isAscii c` (`c.toNat < 128`) | identity on scalar value |
| `s.encode("ASCII", strict)` succeeds | `s.all isAscii` | success ⇔ all code points < 128 |
| `unicodedata.normalize('NFKD', s)` | `canonDecompose s` | opaque; real callee in G-CONF |
| `unicodedata.combining(c) != 0` | `isCombiningMark c` | opaque; real callee in G-CONF |
| list comprehension filter + `''.join` | `List.filter` | per-code-point keep, concat |
| `strip_accents_unicode`'s return | `result : List Char` | the stripped string |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** `unicodedata.normalize('NFKD', ·)` and
  `unicodedata.combining(·)` are UNCHANGED dependency callees that enter the
  impl as opaque references; the proof needs no property of either (spec and impl
  are structurally identical, closed by `split <;> rfl`). They are A-references,
  validated against the real `unicodedata` routines by G-CONF. The `axioms`
  region declares only their `opaque` signatures; no `axiom <callee>_prop` is
  shipped. **G-AX is a skip stub.**
- No flag dependencies: `strip_accents_unicode` reads no configuration flags.

## G-CONF fuzz seed

Pinned LCG seed: **15100** (see `conformance_check.py` `SEED`). Corpus: random
unicode strings drawn from a mix of ASCII letters, pre-composed Latin accented
letters (U+00C0–U+017F), bare combining marks (U+0300–U+036F), and assorted
non-ASCII BMP code points, with random interleaving so the ASCII / non-ASCII
branches and single- vs multi-mark glyphs are all exercised. Plus hand-picked
edge cases: the F2P inputs (`chr(241)`, `"n"+chr(771)`, `"o"+"̈"`,
`"̀́̂̃"`, `"ȫ"`), empty string, pure ASCII, and
mixed ASCII/decomposed text. The R/I/A-reference shadow of
`implementation_stripAccents` (using the REAL `unicodedata` callees) is diffed
against an in-process replica of the POST-PATCH `strip_accents_unicode`.
