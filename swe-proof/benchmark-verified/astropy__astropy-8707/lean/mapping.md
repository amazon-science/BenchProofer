# mapping.md — astropy__astropy-8707

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`a85a0747c54bac75e9c3b2fe436b105ea029d6cf`).

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_cardFromString` / `problem_spec_cardFromString` / `correct_cardFromString` | `Card.fromstring` (classmethod) | `astropy/io/fits/card.py:546-558` |
| `padCard` | `_pad` (module function) | `astropy/io/fits/card.py:1269-1284` |
| `bytesAsText` | `bytes.decode('latin1')` | added by the gold patch in `Card.fromstring` |
| `cardWidth` (= 80) | `Card.length` (`CARD_LENGTH`) | `astropy/io/fits/card.py:22,44` |

The CHANGED function modeled here is `Card.fromstring`. The graded behavior is
the FAIL_TO_PASS test `test_card_from_bytes`:

```python
c = fits.Card.fromstring(b"ABC     = 'abc'")
assert c.keyword == 'ABC'
assert c.value == 'abc'
```

i.e. constructing a card from a raw `bytes` object must succeed (it crashed
pre-patch).

## The changed code (card.py)

At base_commit `Card.fromstring(cls, image)` is:

```python
card = cls()
card._image = _pad(image)        # _pad does  image + ' ' * k   -> str-only
card._verified = False
return card
```

The gold patch inserts, before `_pad`:

```python
if isinstance(image, bytes):
    # decode as latin1 and take all bytes
    image = image.decode('latin1')
```

`_pad(input)` pads `input` with trailing spaces to a multiple of `Card.length`
(= 80): length already 80 → unchanged; length > 80 and a multiple of 80 →
unchanged; otherwise `input + ' ' * (80 - len%80)`. Pre-patch, a `bytes` `image`
reaches `_pad`, which does `image + ' ' * k` — `str` cannot concat to `bytes`,
raising `TypeError: can't concat str to bytes` (the reproducer). The downstream
`._image` is the only state `fromstring` sets; the keyword/value the test asserts
are lazily parsed FROM `._image`, so pinning the produced image text fully
determines the observable.

The companion hunk to `Header.fromstring` (header.py) is type-plumbing: it keeps
the raw bytes flowing through the card-splitting loop and hands them to
`Card.fromstring(b''.join(image))` — i.e. it DELEGATES the actual latin-1 decode
to the now-fixed `Card.fromstring`. The behavioral fix (and the only graded
test, `test_card_from_bytes`) lives entirely in `Card.fromstring`; the header
test added by the test_patch (`test_header_fromstring_bytes`) is in NEITHER
FAIL_TO_PASS nor PASS_TO_PASS (it needs a data file), so a single triple over
`Card.fromstring` captures the graded behavior.

## Lean ↔ Python type bijection

| Python | Lean | bijection |
|---|---|---|
| `image : str` | `CardImage.text cs` | a `str` ↦ its `List Char` of code points |
| `image : bytes` | `CardImage.bytes bs` | a `bytes` ↦ its `List UInt8` of byte values |
| `image.decode('latin1')` | `bytesAsText bs` | byte `b` (0..255) ↦ `Char.ofNat b` — latin1 maps byte `n` to U+00`nn`, i.e. code point == byte value (verified ∀ n∈0..255) |
| `_pad(text)` | `padCard cs` | width = `Card.length` = 80; `len==80 → unchanged`; `len>80, len%80==0 → unchanged`; else `text + ' '*(80 - len%80)` |
| `card._image` (the value the test then parses) | `Except.ok (padCard …)` | construction always succeeds → `Except.ok`; `CardErr.illTyped` is unreachable in the patched/spec behavior (it exists only to express the pre-patch crash in the prepatch impl) |

`Card.length` is a fixed module constant (80); modeling it as the literal
`cardWidth := 80` is faithful (the patch does not touch it).

## Callee provenance / flag deps

- No UNCHANGED callee needs an axiom. The two operations on the changed path —
  the latin-1 reinterpretation (`bytes.decode('latin1')`) and the width-padding
  (`_pad`) — are both modeled DEEPLY (`bytesAsText`, `padCard`). They are
  A-reference (validated == real callee by G-CONF over fuzzed inputs), not
  consumed axioms. → `axioms` region declares only the data types; `axiom_check.py`
  is a skip stub.
- No flag dependency: the only branch is `isinstance(image, bytes)`.

## G-CONF fuzz seed

Pinned seed: **20240626**. `conformance_check.py` builds the Python R/I shadow of
`implementation_cardFromString` and diffs it against the REAL patched
`Card.fromstring(...)._image` over the str/bytes input matrix plus ≥1e5
randomized draws (random lengths 0..200, random byte/char content incl. the
0x80..0xFF non-ASCII range that exercises latin-1).
