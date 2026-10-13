# refinement.md — astropy__astropy-8707

Operation correspondence between the Lean `implementation_cardFromString`
skeleton and the gold `patch.diff`. Tags: **R** (type refinement),
**A-consumed** (proof uses an axiom's property), **A-reference** (deep model
validated == real callee by G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the two callees on the changed path
(`bytes.decode('latin1')` and `_pad`) are both modeled DEEPLY (`bytesAsText`,
`padCard`). Every row is **R**, **I**, or **A-reference**. The R/I/A-reference
legs are differential-tested by G-CONF; G-AX is a skip stub.

## `implementation_cardFromString` ↔ `Card.fromstring`

patch.diff (card.py) changes `Card.fromstring` from

```python
card = cls()
card._image = _pad(image)
card._verified = False
return card
```

to (the `if isinstance(image, bytes): image = image.decode('latin1')` is added
before `_pad`):

```python
card = cls()
if isinstance(image, bytes):
    image = image.decode('latin1')
card._image = _pad(image)
card._verified = False
return card
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut img := image` | `image` parameter received | I | the mutable carrier mirrors Python rebinding `image = …`. |
| `if let CardImage.bytes bs := img then img := CardImage.text (bytesAsText bs)` | `if isinstance(image, bytes): image = image.decode('latin1')` | R + A-reference | the `bytes`-guard ↦ matching the `CardImage.bytes` constructor; this is exactly the line the patch ADDS. `bytes.decode('latin1')` modeled DEEPLY as `bytesAsText` (byte `n` ↦ `Char.ofNat n`, the latin-1 code-point identity; validated == real callee by G-CONF). |
| `let chars := match img with … ` (now always `text`) | `image` (now always `str`) | I | after the guard, the carrier is textual; the `bytes _ => []` arm is dead (unreachable once the guard has run) and exists only for totality. |
| `return Except.ok (padCard chars)` | `card._image = _pad(image)` (then `return card`) | R + A-reference | `_pad` modeled DEEPLY as `padCard` (pad to a multiple of width 80; validated == real callee by G-CONF). `card._image` is the only state `fromstring` sets and the value the test parses; `Except.ok` wraps the always-successful construction. |

The observable is `card._image` — the padded card-image text, which the F2P test
parses to recover `keyword`/`value`. The spec frames it completely: the result
is exactly `Except.ok (padCard (decodeImage image))` for BOTH input forms
(directive 5 — no output component left unconstrained; the bytes form is pinned
to equal the text form on the byte-reinterpreted characters).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the impl omits the byte-reinterpretation step, so a
  `CardImage.bytes` input is never converted to text and the construction yields
  `Except.error CardErr.illTyped` (modeling the real `TypeError: can't concat str
  to bytes` raised when a `bytes` `image` reaches `_pad`). The carried gold proof
  of `correct_cardFromString` fails to close — on the `bytes bs` case the spec
  requires `Except.ok (padCard (bytesAsText bs))` but the buggy impl computes
  `Except.error illTyped` (the goal reduces to `False`). This is exactly the
  FAIL_TO_PASS test `test_card_from_bytes`. A single added branch ⇒ a single
  prepatch / a single independently-fixed behavior.
