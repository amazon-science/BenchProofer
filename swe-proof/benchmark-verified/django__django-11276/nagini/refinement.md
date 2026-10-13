# refinement.md — django__django-11276

The operation-by-operation correspondence between `model.py`'s implementation
(the `escape_codepoints` impl region, the deep `escaped_seq` model, and the
live `entity_decode` axiom) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The escape site — `escape()` (`django/utils/html.py:46`)

Gold hunk:
```
- return mark_safe(str(text).translate(_html_escapes))   # _html_escapes maps ' -> &#39;
+ return mark_safe(html.escape(str(text)))
```

| # | model.py impl op (`escape_codepoints`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text: List[int]` | `text: str` argument of `escape` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | (no node) | `str(text)` coercion | R | identity on the code-point list for the `str` inputs the F2P tests pass (mapping.md §2). |
| A3 | the result is `escaped_seq(ToSeq(text))`, i.e. the per-code-point substitution `& → &amp; … ' → &#x27;`, computed by the backward fold over `text` | `html.escape(str(text))` | A-reference | the changed string operation is modeled **deeply**: `escaped_seq` (the spelled-out per-code-point fold in the `pure` region) and the verified loop in `escape_codepoints` ARE the substitution. There is no consumed `escape_html` axiom — the proof never depends on one. Instead the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `html.escape` on boundary+fuzz and asserts `html.escape == escaped_seq`. The real callee `html.escape` IS that substitution (mapping.md §3.1; ampersand-first ⇒ a single per-code-point map). The model loop and the real callee compute the same function. |
| A4 | `result` returned (a `List[int]`) | `mark_safe(...)` wraps the `str` | R | `mark_safe` is the identity on character content (mapping.md §2); the F2P `test_escape` compares the rendered characters, which `mark_safe` does not change. |

The discriminating content of the change — `'` (U+0027) → `&#x27;` rather than
`&#39;` — lives in `entity(39) == seq_apos_hex()` (model) ⇔ the `.replace('\'',
"&#x27;")` step of `html.escape` (real). The pre-patch `_html_escapes` mapped
`'` → `&#39;`; `model_prepatch.py` reproduces that (`[38,35,51,57,59]`) and
**fails** the postcondition `ToSeq(Result()) == escaped_seq(ToSeq(text))`,
which is exactly the spec sensing the change (G-DIFF).

**Delivery (total correctness):** the precondition carries a termination
obligation (`MustTerminate(2)`), and the impl's substitution loop discharges
it with the strictly decreasing, bounded-below measure `i`. Without it Nagini
proves only partial correctness, so an implementation that computes the right
escape and then never returns (a frozen trailing loop), or that never computes
anything at all, would satisfy the value postcondition vacuously while its
refined counterpart hangs or misbehaves instead of delivering the escaped
text. The obligation excludes exactly that class: any non-decreasing loop now
fails Nagini's obligation-leak check.

## B. The urlize decode site — `urlize.unescape` → `html.unescape`

Gold hunks (`django/utils/html.py`): the nested helper `unescape(text)` (the
`.replace('&amp;','&')…replace('&#39;',"'")` chain, lines 262-269) is deleted,
and its three call sites become `html.unescape(...)`:
```
- middle_unescaped = unescape(middle)
+ middle_unescaped = html.unescape(middle)
- url = smart_urlquote(unescape(middle))
+ url = smart_urlquote(html.unescape(middle))
- url = smart_urlquote('http://%s' % unescape(middle))
+ url = smart_urlquote('http://%s' % html.unescape(middle))
```

This is a pure **callee replacement** (kind A): a hand-rolled decoder is
replaced by the stdlib decoder. It is modeled by the `entity_decode` axiom.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `entity_decode(tok)` axiom (six single-token implications) | the `html.unescape(...)` call | A-consumed | `entity_decode` is the weakest contract on `html.unescape` the spec needs: it inverts the five emitted entities and the legacy `&#39;` (mapping.md §3.2). The proof consumes its `Ensures` (the round-trip clauses B2). G-AX confirms it against the real `html.unescape`. |
| B2 | `Ensures(entity_decode(entity(c)) == PSeq(c))` for `c ∈ {38,60,62,34,39}` in `escape_codepoints` | the correctness obligation the urlize change preserves: decoding what `escape` emits returns the original character | A-consumed + I | the round-trip clause ties the two callees: it holds because `html.unescape` inverts `html.escape` on these entities. The new escaper emits `&#x27;`, and `html.unescape` decodes `&#x27;` back to `'`; the old urlize `unescape` knew only `&#39;` and would leave `&#x27;` undecoded — which is precisely why the F2P urlize tests (`test_url_split_chars`, `test_wrapping_characters`) change to `&#x27;`. |

Why no separate failing `model_prepatch` for site B: the urlize change is a
callee swap whose content lives entirely in the `entity_decode` **axiom**
(shared, frozen spec — a prepatch must keep the spec byte-identical, G-DIFF's
`same_spec`). Its soundness is therefore audited by G-AX (real `html.unescape`)
and its necessity by the round-trip postcondition, rather than by a second
verification-failing skeleton. Site A’s prepatch already exercises the apostrophe
mapping that both sites share.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
the escaper’s character substitution — is modeled **deeply** (the spelled-out
per-code-point fold `escaped_seq` consumed in `escape_codepoints`, step A3,
an **A-reference**), not hidden behind an axiom about the function under change:
there is no consumed `escape_html` axiom. The only consumed axiom,
`entity_decode` (**A-consumed**, site B), covers an **unchanged** stdlib callee
(`html.unescape`) the new code invokes; the escaper's `html.escape` appears only
as the **A-reference** that G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`escape_codepoints` verifies only if it TERMINATES (the precondition's
`MustTerminate` obligation must be fully consumed, so a diverging impl cannot
verify vacuously), only if its output equals the exact per-code-point
substitution with `' → &#x27;` (A3), and only if the escape/decode round trip
holds (B2). By R (str ↔ List[int], `mark_safe`/`str()` identities) the verified
escaper equals `mark_safe(html.escape(str(text)))` on the tested `str` inputs;
by G-AX the deep model `escaped_seq` equals the real `html.escape` (A-reference)
and the real `html.unescape` meets the `entity_decode` axiom it stands in for
(A-consumed). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
