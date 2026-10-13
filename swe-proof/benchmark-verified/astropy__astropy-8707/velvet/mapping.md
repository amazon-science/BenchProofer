# mapping.md — astropy__astropy-8707

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a85a0747c54bac75e9c3b2fe436b105ea029d6cf`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo files under change: `astropy/io/fits/card.py`, `astropy/io/fits/header.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildImage (src : Source)` | `Card.fromstring(cls, image)` — `astropy/io/fits/card.py:547` (body 556–559) | the modeled changed function: normalize a construction source to the character image to store |
| `Source.text` / `Source.raw` | the type of `image` — a `str` OR a `bytes` object (post-patch `isinstance(image, bytes)` branch) | the two acceptable input kinds the issue asks for |
| `codepointsOf (b : List Nat)` *(deep model — A-reference)* | `image.decode('latin1')` — the line the gold patch inserts at `astropy/io/fits/card.py:557` | pure spec: octet → character code-point interpretation; deep model of the unchanged built-in callee `bytes.decode('latin-1')`, validated `codepointsOf == bytes.decode('latin-1')` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `imageSpec (src)` | the value `card._image` is set from: `_pad(image)` after the (possible) decode | pure spec: the character image stored for each source kind (before the unchanged normalizer) |
| `_pad` (NOT in the Lean model) | `_pad(input)` — `astropy/io/fits/card.py:1269` | unchanged downstream normalizer; applied identically in both branches, so it is orthogonal to the behavior under spec and excluded from the model (refinement.md C) |

The pre-patch repo behavior the change fixes (refinement audit only, not in the
consumer spec view): with no `isinstance(image, bytes)` branch, a `bytes`
`image` flows straight into `_pad`, where `input + ' ' * n` raises `TypeError`
(`bytes` + `str`) — construction from a raw octet source is effectively refused.

### 1.1 Second change site — `Header.fromstring` (`astropy/io/fits/header.py:329`)
The gold patch also teaches `Header.fromstring(cls, data, sep='')` to accept
`bytes`: when `data` is `bytes` it decodes the separator/sentinels to `bytes`
and splits `data` into per-card octet slices, each handed to `Card.fromstring`.
This is the SAME byte-acceptance behavior applied at the header level, and its
per-card decode is **delegated** to the now-fixed `Card.fromstring`. It is **not
separately modeled** because (a) its control flow uses constructs outside
Velvet's measured fragment — `continue`/`break` inside a `while` loop and an
early `break` — and (b) it is **ungraded**: the only FAIL_TO_PASS test is
`test_card_from_bytes` (exercising `Card.fromstring`); the header-level
`test_header_fromstring_bytes` is in neither FAIL_TO_PASS nor PASS_TO_PASS. The
graded behavior the issue demands — "accept bytes, decoding latin-1" — is fully
captured by the `Card.fromstring` model. See refinement.md §B.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` `image` (a character image already in hand) | `Source.text (s : List Char)` | Python `str` `s` ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| `bytes` `image` (a raw octet sequence) | `Source.raw (b : List Nat)` | Python `bytes` `bs` ↔ `[x for x in bs]` as `List Nat`; each octet `0 ≤ x < 256` ↔ a `Nat` with the `require x < 256`; `len(bs)` ↔ `b.length` |
| a single octet value `x` (0–255) → its character | `Char.ofNat x` | `chr(x)` ↔ `Char.ofNat x`; on 0–255 (the latin-1 block) this is the identity on code points and total |
| `image.decode('latin1')` | `codepointsOf b` | `bs.decode('latin-1')` ↔ `codepointsOf (octets bs)`; element-wise `chr` ↔ `Char.ofNat` |
| `_pad(image)` | (omitted; I-tagged downstream op) | the unchanged normalizer; same function applied to the resulting image in both branches, so it cancels out of the behavior under spec |
| `TypeError` raised pre-patch on a bytes source | `Except.error ImageErr.rawNotAccepted` | the pre-patch refusal-to-accept of a raw octet source (modeled only in `Solution_prepatch.lean`) |

Lean `String`/`List Char` indexing is total and sound; the carrier for a raw
source is `List Nat` because the operation is per-octet (each octet a value
0–255) and `Char.ofNat` maps it to a code point.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `codepointsOf` deep model ↔ `bytes.decode('latin-1')` (A-reference)
**Callee:** Python built-in `bytes.decode('latin-1')`. The changed operation —
turning a raw octet sequence into a character image — is modeled **deeply** by
`codepointsOf` in the `pure` region; there is **no consumed axiom**. The gold
patch's inserted line is exactly `image = image.decode('latin1')`. latin-1
(ISO-8859-1) maps octet `b` (0–255) to the Unicode code point `U+00b`,
byte-for-byte with no multi-byte interpretation — precisely what
`Char.ofNat b` per octet computes. The patch comment explains the choice: FITS
is ASCII, but latin-1 round-trips ALL 256 octet values, so invalid/mojibake
bytes are retained rather than raising, "still gives us the opportunity to
display warnings later during validation."

**Soundness check (G-AX):** `axiom_check.py` runs the real
`bytes.decode('latin-1')` on every single octet 0–255, a set of boundary
sequences (empty, high bytes, all-256-in-order, UTF-8 byte pairs), and 20 000
randomized fuzz sequences, asserting `codepointsOf == real decode` on each. It
additionally runs the modeled function end-to-end through the REAL repo callee
`Card.fromstring(bytes)._image == _pad(bytes.decode('latin-1'))` when the repo
is importable, confirming the deep model composes with the unchanged `_pad`
exactly as refinement.md C claims. Imports only built-ins (+ astropy for the
optional e2e leg). Exit 0 iff sound.

### 3.2 `_pad` — the unchanged downstream normalizer (I, not axiomatized)
`_pad` (`card.py:1269`) is the fixed-width normalizer applied to the character
image AFTER the (possible) decode, identically in the str and bytes branches. It
is unchanged by the patch and orthogonal to the accept-bytes behavior, so it is
**not modeled** in Lean (no `axiom`, no `ensures` about it) and is left as the
**real repo callee** in `conformance_check.py`'s shadow (an I-tagged op). This
avoids shipping a dead/over-claimed axiom (SPEC_GUIDE §0.7).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

Both `conformance_check.py` and `axiom_check.py` seed their `random.Random` with
**`8707`** so the consumer-side verdict (§11.3) is reproducible.
`conformance_check.py` builds the R/I shadow of `buildImage`
(`Source.text s → s`, `Source.raw b → bytes.decode('latin-1')`) and applies the
REAL `_pad` (the I-tagged downstream op), diffing against the patched
`Card.fromstring(.)._image` over ≥10⁵ fuzzed str/bytes inputs.
