# refinement.md — astropy__astropy-8707

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildImage` `do` block and the deep `codepointsOf`/`imageSpec` models) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/deep-modeled callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviorally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The accept-bytes site — `Card.fromstring()` (`astropy/io/fits/card.py:556`)

Gold hunk:
```
  card = cls()
+ if isinstance(image, bytes):
+     image = image.decode('latin1')
  card._image = _pad(image)
```

| # | Solution.lean impl op (`buildImage`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `src : Source` (`text`/`raw`) | the `image` argument, a `str` OR `bytes` | R | `str ↔ Source.text (List Char)`, `bytes ↔ Source.raw (List Nat)` (mapping.md §2). The `isinstance(image, bytes)` dispatch ↔ the `match src` on the constructor tag. |
| A2 | `Source.text s ⇒ Except.ok s` (image used as-is) | the non-bytes path: `image` flows unchanged into `_pad` | I | a character source's image is the source itself; identical concrete op. |
| A3 | `Source.raw b ⇒ Except.ok (codepointsOf b)` (decode each octet to its code-point character) | `image = image.decode('latin1')` | A-reference + R | the changed op is modeled **deeply**: `codepointsOf` (pure region) IS the per-octet code-point interpretation. The fold ops (`Char.ofNat b`, `::`) are concrete/R (transliterated by G-CONF as `bytes.decode('latin-1')`); the equality of that deep model to the real built-in `bytes.decode('latin-1')` is the **A-reference** G-AX validates. mapping.md §3.1. No consumed axiom. |
| A4 | (not modeled) result image fed to the unchanged normalizer | `card._image = _pad(image)` | I | `_pad` is unchanged and applied identically in both branches (mapping.md §3.2). Left as the real callee in the G-CONF shadow; cancels out of the behavior under spec. |
| A5 | `out : Except ImageErr (List Char)`, always `ok` post-patch | construction never refuses a source | R | the `error` constructor exists only to express the pre-patch refusal (Solution_prepatch). Post-patch, both branches are `ok`. |

Discriminating content of the change — a raw octet source is **accepted** (and
decoded byte-for-byte) rather than **refused** — lives in
`imageSpec (Source.raw b) = Except.ok (codepointsOf b)` (model) ⇔ the inserted
`image.decode('latin1')` (real). Pre-patch, a `bytes` `image` reaches `_pad`,
where `input + ' ' * n` raises `TypeError`; `Solution_prepatch.lean` reproduces
that refusal as `Except.error ImageErr.rawNotAccepted` and **fails**
`out = imageSpec src` on the `Source.raw` clause (G-DIFF).

## B. The second change site — `Header.fromstring()` (`header.py:329`)

Gold hunks: `Header.fromstring(cls, data, sep='')` gains an
`if isinstance(data, bytes):` block that decodes `sep`/sentinels
(`CONTINUE`/`END`/`END_CARD`) to `bytes` and splits the raw `data` into per-card
octet slices, each passed to the now-fixed `Card.fromstring`; plus a docstring
`str → str or bytes` update.

**Not separately modeled.** Tagged here for completeness, no Lean construct:
- The per-card decode is **delegated** to `Card.fromstring` (site A) — the same
  accept-bytes behavior, already modeled and discriminated.
- Its control flow uses constructs **outside Velvet's measured fragment**:
  `continue`/`break` inside a `while` loop and a loop-internal early `break`
  (SPEC_GUIDE §2 banned list). Modeling it would require a different algorithm,
  forbidden by Prime Directive 3.
- It is **ungraded**: the sole FAIL_TO_PASS is `test_card_from_bytes`
  (`Card.fromstring`); `test_header_fromstring_bytes` is in neither
  FAIL_TO_PASS nor PASS_TO_PASS. No independently-graded fixed behavior ⇒ no
  separate `Solution_prepatch_2.lean` is required (G-DIFF: one prepatch per
  independently-fixed *graded* behavior; here there is one).

`patch.diff` still includes site B **verbatim** so G-RESOLVE applies the
complete gold patch. The docstring/doctest-skip edits are pure documentation and
behavior-neutral.

## C. No kind-3 (inexpressible-changed-op) steps

Every modeled step is R, A, or I. The one operation that genuinely *changed* in
the graded path — accept a raw octet source by decoding it byte-for-byte — is
modeled **deeply** (`codepointsOf`/`imageSpec`, step A3, an A-reference + R), not
hidden behind an axiom about the function under change. There are **no consumed
axioms**. The unchanged downstream normalizer `_pad` (A4) is an **I** op left as
the real callee in G-CONF, never axiomatized — so no dead/over-claimed axiom
ships (SPEC_GUIDE §0.7). Site B (header) is an ungraded delegation to the
modeled `Card.fromstring`, excluded for fragment + grading reasons (§B), not a
mislabeled kind-3.

## D. verify(Solution) ⇒ resolved

`buildImage` verifies only if, for a raw octet source, its output equals
`Except.ok (codepointsOf b)` — i.e. the source is **accepted** and decoded
byte-for-byte (A3) — and for a character source equals `Except.ok s` (A2). By R
(`str ↔ List Char`, `bytes ↔ List Nat`, `Char.ofNat ↔ chr`) the verified builder
equals the patched `Card.fromstring`'s pre-`_pad` image on every input; by G-AX
the deep model `codepointsOf` equals the real `bytes.decode('latin-1')`
(A-reference); by G-CONF the R/I transliteration — including the real unchanged
`_pad` — agrees with the patched `Card.fromstring(.)._image` on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited deep model — and the gold patch
resolves (G-RESOLVE: `test_card_from_bytes` passes because
`Card.fromstring(b"ABC     = 'abc'")` now decodes instead of raising). Trust
points are exactly the two of plan §1.1: deep-model soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
