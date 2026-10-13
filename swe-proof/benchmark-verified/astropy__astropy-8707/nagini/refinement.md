# refinement.md — astropy__astropy-8707

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_record_image` impl region, the deep `reinterpret` model, and the
`text_form` / `enter_text_form` / `pad_to_width` / `pad_runtime` axioms) and
`patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The tested site — `Card.fromstring` (`astropy/io/fits/card.py:548`)

Gold hunk:
```
 card = cls()
+if isinstance(image, bytes):
+    image = image.decode('latin1')
 card._image = _pad(image)
 card._verified = False
 return card
```

| # | model.py impl op (`build_record_image`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `raw: List[int]`, `from_bytes: bool` | `image` (`str` or `bytes`) argument of `Card.fromstring` | R | `str`/`bytes` ↔ `List[int]` (mapping.md §2); `from_bytes` ↔ `isinstance(image, bytes)`. |
| A2 | the backward loop building `image` so that `ToSeq(image) == reinterpret(ToSeq(raw))` | the **value** half of `if isinstance(image, bytes): image = image.decode('latin1')` (and the str fall-through that leaves a str unchanged) | A-reference | the value content of the changed operation is modeled **deeply**: `reinterpret` (the spelled-out value-preserving fold in the `pure` region) and the verified loop in `build_record_image` ARE the latin-1 decode at the level of values. There is no consumed `decode` axiom for the value half. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `bytes.decode('latin1')` over the whole byte domain and asserts `reinterpret == decode`. latin-1 is the value-preserving identity on bytes 0..255 (mapping.md §3.1), so `reinterpret` == the real decode, and the str path (identity) coincides with it (an already-text input is unchanged). Being value-preserving, this step leaves **no trace in the value it produces** — which is why the type half needs A3. |
| A3 | `text = enter_text_form(image)` | the **type** half of the same guarded step — `image.decode('latin1')` returns a `str` where the argument was `bytes` (`astropy/io/fits/card.py:557-562`, patched: the guard at 557, the decode at 562) | A-consumed | this is the half a `List[int]` carrier cannot express as a value, and it is the half the F2P test turns on. The axiom's two `Ensures` are "content unchanged" (`ToSeq(Result()) == ToSeq(v)`, true because latin-1 is the identity over 0..255) and "the outcome is textual content" (`text_form(Result())`, true because `bytes.decode` returns a `str`, and a value already in text form is returned unchanged). The axiom is about the **stdlib callee** `bytes.decode('latin1')`, not about the function under change. `text_form` is uninterpreted with `enter_text_form` as its ONLY source, so this call is what the postcondition `text_form(Result())` can be discharged from — and no Python operation turns a `bytes` object into a `str`-typed object except a decode, so refining this step to nothing is not a faithful refinement. G-AX runs the real step (identical code points, a `str`, a distinct object). |
| A4 | `res = pad_runtime(text)` | `card._image = _pad(image)` (line 564 patched, 557 at `base_commit`) | A-consumed | `pad_runtime` is the runtime form of the unchanged `_pad`; its `Ensures` (content-preserving pad to a whole multiple of the width) is the axiom the proof consumes (mapping.md §3.2). Its `Requires(text_form(text))` says the padding step is defined on textual content — a **domain restriction**, not a failure claim (the bundle has no `Exsures`) — mirroring the patch, where after the guarded step `image` is always a `str` and `_pad` never hits the `str`+`bytes` `TypeError`. G-AX checks the restriction against the real helper at all 321 lengths in 0..320, whole multiples included. |
| A5 | `return res` (a `List[int]`) | `card._image = ...; return card` | R/I | the result is the padded image content; `card._image` is that content. The F2P `test_card_from_bytes` parses `keyword`/`value` from this image content (`'ABC'`, `'abc'`), which depends only on the (value-preserved) characters. |

The discriminating content of the change — a **byte** input must be taken over
into textual content **before** the padding step, so byte input is accepted and
yields the same image as the value-equal text-form input — lives in the pair
*`enter_text_form` as the ONLY source of `text_form` (A3)* and *`text_form`
demanded by `pad_runtime`'s precondition and by the postcondition of
`build_record_image` (A4)*. It does **not** live in the value clauses: A2 is
provably the identity, so no value clause can see whether the step was applied.

The pre-patch behaviour is "only an input supplied already in text form is
treated as textual content, a byte input is handed to the padding step as it
stands": `model_prepatch.py` reproduces it by padding the un-entered copy on the
byte path and **fails** `pad_runtime`'s `Requires(text_form(text))` there
(`from_bytes == True`), while its text-form path still verifies because such an
input carries `text_form` by virtue of its form — exactly the spec sensing the
change, and nothing wider (G-DIFF). At the repo level this is the `TypeError:
can't concat str to bytes` the pre-patch `_pad(bytes)` raises on every length at
which it must concatenate; axiom_check.py confirms that on the real helper, and
confirms the remaining lengths (positive whole multiples of the width) return the
argument untouched and still non-text, so the model's domain restriction is sound
there too rather than claiming a failure the helper does not have.

## B. The whole-header site — `Header.fromstring` (`astropy/io/fits/header.py:330`)

Gold hunks (`header.py`): `data : str` becomes `data : str or bytes`; a
`isinstance(data, bytes)` branch sets `CONTINUE = b'CONTINUE'`, `END = b'END'`,
`end_card = END_CARD.encode('ascii')`, `sep = sep.encode('latin1')`,
`empty = b''` so that the split/compare operations stay in the input's
encoding; and the `''.join(image)` calls become `empty.join(image)`. Net
behaviour: a **raw `bytes` header is ACCEPTED and is processed in its byte
encoding, each record image it yields reaching textual content per-card** at
`Card.fromstring`, which itself now decodes — site A. The recovered images are
**not** claimed identical to those from the value-equal `str` header: the
division into records is performed by the operations of the input's own form,
and `str.rstrip()` strips code points `bytes.rstrip()` does not (0x85, 0xa0,
0x1c-0x1f), so the two forms can disagree on where the header ends. model.py
docstring point (2) declines that claim explicitly; see mapping.md §1.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `reinterpret` deep model + the `build_record_image` contract (each record image is the value-preserving reinterpretation, padded, and in text form) | the `bytes`-branch literals and `empty.join` in `Header.fromstring`, then per-card `Card.fromstring` | A-reference + I | the only behavioural content of the header hunk is to keep the byte path value-preserving until the per-card `Card.fromstring` (site A) decodes — the same `reinterpret` identity. The split/compare are I (identical concrete operations) performed in whichever encoding matches the input; **which** records they produce is outside what the spec claims (§B note above), the two forms' end/whitespace tests not agreeing on every input. |

Why no separate failing `model_prepatch` for site B: the header change is the
same reinterpret-before-text-operation delta as site A, and it shares the frozen
spec (`reinterpret`, and the `text_form` / `enter_text_form` / `pad_to_width` /
`pad_runtime` axioms). A
prepatch must keep the spec byte-identical (G-DIFF's `same_spec`); site A's
prepatch already exercises the byte-vs-text discriminator both sites share, and
B's soundness is audited by the same G-AX decode/text-only check. The tested
(F2P) behaviour is site A (`test_card_from_bytes`); the `Header.fromstring`
bytes test is not in FAIL_TO_PASS.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* — the
guarded latin-1 reinterpretation of a byte input — is split by what the carrier
can express, and neither half is hidden behind an axiom about the function under
change:

  - its **value** half is modeled **deeply** (the spelled-out value-preserving
    fold `reinterpret`, consumed in `build_record_image`, an **A-reference**),
    spelled out step for step by the loop and validated == the real callee by
    G-AX;
  - its **type** half — that the outcome is textual content rather than a raw
    byte sequence — is not a value at all, and a `List[int]` carrier cannot
    express it, so it is carried by the axiom `enter_text_form` over the
    uninterpreted property `text_form` (**A-consumed**, A3). That axiom is about
    the **stdlib callee** `bytes.decode('latin1')`: its two `Ensures` are
    "content unchanged" and "the outcome is textual content", and G-AX asserts
    both of the real `bytes.decode('latin1')` (identical code points, a `str`, a
    distinct object). It says nothing about `Card.fromstring` itself, whose body
    is spelled out in the impl region.

The remaining consumed axioms (`pad_to_width` / `pad_runtime`, **A-consumed**)
cover the **unchanged** `_pad` helper the new code still calls.

## D. verify(model) ⇒ resolved

`build_record_image` verifies only if both halves of the change hold, and the two
halves are carried by different clauses. Being explicit about which is *forced*
and which is *validated* is the whole of this section.

**The type half is FORCED by the clauses.** `Ensures(text_form(Result()))` can be
discharged only from `text_form`'s single source, `enter_text_form` (A3): the
property is uninterpreted — it has no body, nothing computes it, and no caller may
assert it of a value of its own choosing — and `pad_runtime` demands it of its
argument (A4). A byte-form input (`from_bytes` true) carries nothing but its
element values, so on that form the only way to reach either the padding step or
the postcondition is to apply the step that takes a value over into textual
content. An implementation that pads the raw input instead does not verify;
`model_prepatch.py` is that implementation on the byte path and fails there
(G-DIFF). By R (`str`/`bytes` ↔ `List[int]`, `from_bytes` ↔
`isinstance(image, bytes)`, `enter_text_form` ↔ the guarded
`image = image.decode('latin1')`) that step **is** the gold hunk, and G-AX grounds
the correspondence on the real callees: the real step returns textual content with
identical code points, and the real `_pad` never returns textual content from an
argument that is not textual content, at any length.

**The value half is deep and validated, but NOT forced by the clauses.**
`reinterpret` is proved `Ensures(Result() == x)` — it is the identity — so
`pad_to_width(reinterpret(ToSeq(raw)))` is extensionally
`pad_to_width(ToSeq(raw))`, and no value clause can see whether the step was
applied. That is a property of the operation rather than a gap in the argument:
latin-1 **is** the value-preserving identity over 0..255, which is exactly why the
gold chose it, and G-AX asserts `reinterpret ==` the real `bytes.decode('latin1')`
exhaustively (mapping.md §3.1). So the value clauses pin what the image IS — the
padded content of the input, the same for both input forms, hence the same
`keyword` and `value` recovered from either — while the type half above pins that
the step was taken.

Together: a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — the padded content of the input,
reached through the reinterpretation on the byte form — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX, which covers `enter_text_form` and `pad_runtime` as well as the
deep model) and refinement fidelity (this document, G-EQ).
