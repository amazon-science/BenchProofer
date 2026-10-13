# mapping.md — astropy__astropy-8707

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a85a0747c54bac75e9c3b2fe436b105ea029d6cf`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo files under change: `astropy/io/fits/card.py`, `astropy/io/fits/header.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_record_image(raw, from_bytes)` | `Card.fromstring(cls, image)` — `astropy/io/fits/card.py:548` (body 556-559 at `base_commit`; the padding call `card._image = _pad(image)` at 557, and at 564 once the guarded step is inserted) | the modeled changed function: build a single record image from a raw `str`-or-`bytes` input, then pad it (`card._image = _pad(image)`). `from_bytes` ↔ `isinstance(image, bytes)`: false says the input is supplied already in text form (a `str`), true that it is a raw byte sequence. |
| `reinterpret(x)` *(deep model — A-reference)* | `image.decode('latin1')` — the new line added to `Card.fromstring` (the whole-header site has no decode of its own; each record reaches this step per-card) | pure spec: the value-preserving byte→code-point reinterpretation (latin-1), modeled DEEPLY (not a consumed axiom) and validated `reinterpret == bytes.decode('latin1')` by axiom_check.py (G-AX). |
| `pad_to_width(image)` *(axiom — A-consumed, pure)* | `_pad(input)` — `astropy/io/fits/card.py:1269` | unchanged padding helper the changed function calls; pure spec form. |
| `text_form(v)` *(ghost property — uninterpreted)* | the runtime type tag the carrier erases: the concrete value is a `str` rather than a `bytes` | the `List[int]` carrier cannot express `str`-vs-`bytes`, which is the entire subject of this change; `text_form` restores exactly that tag and nothing more. It has no body, so no computation can conjure it, and it has a single source (`enter_text_form`) and a single consumer (`pad_runtime`). |
| `enter_text_form(v)` *(axiom — A-consumed, runtime)* | `if isinstance(image, bytes): image = image.decode('latin1')` — `astropy/io/fits/card.py:557-562` (the guard at 557, the decode at 562, patched); reached per record from the second site | `Ensures(ToSeq(Result()) == ToSeq(v))` holds because latin-1 is the value-preserving identity over 0..255 (the same fact G-AX checks of the deep model `reinterpret`, §3.1); `Ensures(text_form(Result()))` holds because `bytes.decode` returns a `str`, and a value already in text form is returned unchanged. No Python operation turns a `bytes` object into a `str`-typed object except a decode, so refining this step to nothing is not a faithful refinement. G-AX runs the real step: identical code points, a `str`, and a distinct object (the model forces `Result() is not v` by permission arithmetic). |
| `pad_runtime(text)` *(axiom — A-consumed, runtime)* | `_pad(input)` — `astropy/io/fits/card.py:1269` | unchanged padding helper, runtime form. It is a TEXT operation: `input + ' ' * n` concatenates a `str`. The model **restricts its domain by precondition** (`Requires(text_form(text))`) to textual content and claims no failure of its own — there is no `Exsures` anywhere in the bundle. A precondition narrows a callee's domain, so it cannot over-claim, and the patched caller only ever passes a `str`. `Ensures(text_form(Result()))` holds because the real helper returns a `str` on a `str` argument at every length. |
| `all_bytes(x)` | the implicit domain of a raw FITS input (ASCII/latin bytes 0..255) | pure spec helper: every element is a byte value. |
| `WIDTH = 4` | `Card.length == CARD_LENGTH == 80` (`card.py:22,44`) | modeled fixed record width; only multiplicity matters (see §2). |

The second change site, `Header.fromstring` (`astropy/io/fits/header.py:330`),
accepts a raw `bytes` header. There is **no** `data.decode('latin1')` in the
patched `header.py` (grep: 0 occurrences): the whole-header path keeps the input
in the form it arrived in — the `CONTINUE`/`END`/`end_card`/separator/join
literals are taken in the matching encoding — and it is each individual record
image that reaches textual content per-card at site A (`Card.fromstring`, which
now decodes). Modeled by the same `reinterpret` deep model and the same
`enter_text_form` / `pad_to_width` / `pad_runtime` axioms applied per record, and
audited by the same G-AX check. It is not the tested (F2P) behaviour — see
refinement.md §B and meta.json `additional_change_sites`.

Because the division into records is performed by the operations of whichever
form the input arrived in, a `bytes` header and the value-equal `str` header do
NOT always divide into the same records: `str.rstrip()` strips code points that
`bytes.rstrip()` does not (e.g. 0x85, 0xa0, 0x1c-0x1f), so the two forms can
disagree on where the header ends. The model therefore claims nothing about the
division (model.py docstring point (2) declines it explicitly); its modeled
signature has no separator parameter and covers a single record.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` / `bytes` (the `image`/`data` argument) | `List[int]` (`bytes` → byte values 0..255; `str` → code points) | `s[k]` ↔ `raw[k]`; `len(s)` ↔ `len(raw)`; concatenation ↔ list `+`; an empty input ↔ `[]`. The `bytes`/`str` distinction is carried by the `from_bytes` flag (↔ `isinstance(image, bytes)`). |
| `str`/`bytes` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`. |
| `image.decode('latin1')` (the added line) | `reinterpret` (identity on byte values 0..255) | `bytes.decode('latin1')` maps byte b → `chr(b)`, i.e. the identity on the integer value over the whole byte domain — verified exhaustively in axiom_check.py. The "value-equal text input yields the same result" property is exactly that this is the identity. |
| `Card.length == 80` (the record width) | `WIDTH == 4` | the patch's behaviour is width-agnostic: padding to a multiple of the width and reinterpret-before-pad hold for any positive width. The small constant keeps the modular-arithmetic proof obligations cheap; axiom_check.py validates the `_pad` contract against the REAL width 80. |

`str`/`bytes` indexing/iteration is banned in Nagini, so the carrier is
`List[int]` throughout; the specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reinterpret` deep model ↔ `bytes.decode('latin1')` (A-reference)
**Callee:** CPython `bytes.decode('latin1')`. The changed decode operation is
modeled **deeply** by the `@Pure` fold `reinterpret` in the `pure` region; there
is **no `decode` axiom** the proof consumes. The deep model is validated equal
to the real callee out-of-band by axiom_check.py (G-AX). latin-1 (ISO-8859-1)
is the unique codec for which byte value `b` decodes to the code point of the
same numeric value `b`, for every `b` in 0..255 — i.e. the identity on the
integer value. This is
why the gold chose latin-1: it round-trips arbitrary bytes (the patch comment:
"decode as latin1 and just take all bytes for now"). model.py's `reinterpret`
encodes exactly this identity; G-AX asserts `reinterpret(s) == [ord(c) for c in
bytes(s).decode('latin1')]` exhaustively over 0..255, all 65 536 byte pairs, and
20 000 fuzzed byte strings. Docs:
https://docs.python.org/3/library/codecs.html#standard-encodings (latin_1).

### 3.2 `pad_to_width` / `pad_runtime` ↔ `_pad`, and the `text_form` tag (A-consumed)
**Callee:** `astropy.io.fits.card._pad(input)` (`card.py:1269`), unchanged by
the patch:

```python
def _pad(input):
    _len = len(input)
    if _len == Card.length:           # 80
        return input
    elif _len > Card.length:
        strlen = _len % Card.length
        if strlen == 0:
            return input
        else:
            return input + ' ' * (Card.length - strlen)
    else:
        strlen = _len % Card.length
        return input + ' ' * (Card.length - strlen)
```

The axiom encodes only the obligations the caller relies on, each true of the
real `_pad` (the **weakest** sufficient contract, not the full branch logic):

  - content prefix preserved: `Result().take(len(image)) == image`;
  - output length a whole multiple of the width: `len(Result()) % WIDTH == 0`;
  - at most `WIDTH` elements added: `len(Result()) <= len(image) + WIDTH`
    (NB: an EMPTY input pads to a full record, adding exactly `WIDTH` — so the
    bound is `<=`, never the stronger `< WIDTH`; axiom_check.py exercises this
    boundary);
  - every appended element is a space (32).

**The padding step is defined on textual content, and the model says so with a
precondition.** `_pad` does `input + ' ' * n` — a `str` concatenation. Handed a
raw `bytes` `input` it raises `TypeError: can't concat str to bytes` at every
length where it must concatenate (the EMPTY input included — that one is padded
out to a full record), and at a positive whole multiple of the width
(80, 160, 240, …) it returns its argument untouched and still `bytes`. Either
way, **a value that is not textual content never comes back as textual
content.** That is the behaviour under repair: pre-patch, `Card.fromstring`
passes a raw byte input straight to `_pad`.

The model encodes this as a **domain restriction** — `Requires(text_form(text))`
on `pad_runtime` — and makes **no failure claim of its own**: the bundle contains
no `Exsures` at all. A precondition narrows a callee's domain and so cannot
over-claim, and in particular the model does not claim the real helper *raises*
on the whole-multiple family, where it does not. `Ensures(text_form(Result()))`
is the other half: the real helper returns a `str` when handed a `str`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`bytes.decode('latin1')` and the REAL `astropy.io.fits.card._pad`, imported
in-container, and cross-checks the latter against the verbatim reimplementation
of the source above at every length it tests. It asserts, in four legs:

  - **L0** (A-consumed, §3.2) the real `_pad` meets the `pad_to_width` contract
    over 245 input lengths around the width boundary — content prefix preserved,
    length a whole multiple, at most one width added (the empty input adds a
    full record, so the bound is `<=`), appended elements all spaces;
  - **L1** (`enter_text_form`) the real step yields textual content with
    identical code points and a **distinct object**, over samples including all
    256 byte values;
  - **L2** (`Requires(text_form(text))` / `Ensures(text_form(Result()))`) at all
    321 lengths in 0..320 — **whole multiples INCLUDED, not skipped** — a
    non-text argument either fails on the concatenation (317 lengths) or comes
    back untouched and still non-text (80, 160, 240, 320), and a text argument
    comes back text;
  - **L3** the observable that grounds `text_form(Result())`: the record image
    the caller parses, probed on the module as the image ships it (G-AX runs at
    `base_commit`, so the byte form is not yet reinterpreted there).

Also asserts the deep model `reinterpret` equals the real latin-1 decode
(A-reference, §3.1). Exit 0 iff sound.

## G-CONF (differential conformance)

`conformance_check.py` refutes the refinement leg: it diffs the SHADOW — the
`# impl-start`/`# impl-end` region of `build_record_image`, copied **verbatim**
with only the contract calls (`Requires`/`Ensures`/`Invariant`/`Assert`) and the
`# invariants-*` markers deleted — against the ORACLE, the **real patched**
`Card.fromstring(image)` (`astropy/io/fits/card.py:548`, §1), **called** in the
instance container with the gold patch applied. No transliteration: the modeled
function takes a bare `str`/`bytes` and needs no Table/session/file context.

Neither `@ContractOnly` callee has a body to copy, so each shim **calls the real
repo operation it axiomatizes** — the axioms are exercised, not assumed:

  - `enter_text_form(v)` ↔ the guarded step the gold hunk adds,
    `if isinstance(image, bytes): image = image.decode('latin1')`
    (`card.py:557-562` patched, §1). Its shim additionally receives
    `from_bytes`, because a `List[int]` alone does not name which concrete value
    — `bytes` or `str` — the real step is to run on; that is the type bridge
    below, and on a text-form value the real step is the identity.
  - `pad_runtime(text)` ↔ the real `astropy.io.fits.card._pad`
    (`card.py:1269`, §3.2), so the shadow's padding is the real 80-column
    helper. Its `Requires(text_form(text))` is separately cross-checked against
    that callee at all 321 lengths in 0..320 — whole multiples INCLUDED — as in
    §3.2 L2: a value that is not textual content never comes back as textual
    content, and textual content comes back padded and content-preserving. The
    check makes no claim that the helper *raises* anywhere, matching a model
    that carries no `Exsures`.

The `@Pure` helpers copy over as plain functions; `all_bytes`
becomes a bounded loop used to assert each generated input satisfies the
`Requires`, and the deep model `reinterpret` (§3.1) is used only for the
model-internal `loop == reinterpret` check, never as the oracle.

**Type bridge (§2, inverted).** A generated `List[int]` with all elements in
0..255 becomes `bytes(raw)` when `from_bytes` is true and
`''.join(chr(c) for c in raw)` when false (↔ `isinstance(image, bytes)`); the
oracle's `str` observable `card._image` returns to the carrier as
`[ord(ch) for ch in ...]`. The same bridge is applied at each `@ContractOnly`
callee boundary (the guarded step and `_pad`).
The modeled `WIDTH = 4` is spec-only and absent from the impl region, so —
because the shadow calls the real `_pad` — the executable diff runs at the real
width **80** and the width abstraction never enters the comparison.

**Inputs.** 100 586 `Requires`-satisfying inputs: 586 boundary (empty input =
the loop-not-taken and pad-a-whole-record corner; every single byte value
0..255; the exact F2P image `b"ABC     = 'abc'"`; `bytes(range(256))`; the
0x80..0xFF high-bit range only latin-1 round-trips; lengths straddling both
width 80 — 79/80/81/159/160/161 — and the modeled WIDTH 4 — 3/4/5/8/9) each
driven in **both** input forms, then 100 000 seeded fuzz draws with
`from_bytes` sampled per draw, so the branch the gold patch added is taken on
about half of all inputs.

**Pinned seed: `SEED = 8707`** (`random.Random`, stdlib only; hypothesis not
required). Exit 0 iff zero disagreements; the last stdout line is a JSON report.

Refutation controls (run out-of-band, not shipped): the check FAILS against a
pre-patch oracle (`_pad` on raw bytes → `TypeError` vs the shadow's padded
image), against a shadow whose loop appends instead of prepending, and against
a shadow that substitutes a non-value-preserving decode for the identity.
