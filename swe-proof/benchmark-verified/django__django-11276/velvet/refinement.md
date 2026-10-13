# refinement.md — django__django-11276

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `escapeCodepoints` `do` block, the deep `escapedSeq` model, and the
`entityDecode` axioms) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so the `while` fold
carries a `decreasing i` measure and a verifying impl must TERMINATE and
return `escapedSeq text`. (An earlier revision used partial correctness, which
a same-spec diverging impl — a `while true` loop with a trivial invariant —
vacuously satisfied; the G-PANEL-1 audit found that counterexample, and total
semantics excludes the whole class. The real `html.escape` is a straight-line
chain of five `str.replace` calls that always terminates and returns, and the
F2P `test_escape`/urlize tests observe its return value, so total correctness
is the faithful semantics.)

## A. The escape site — `escape()` (`django/utils/html.py:46`)

Gold hunk:
```
- return mark_safe(str(text).translate(_html_escapes))   # _html_escapes maps ' -> &#39;
+ return mark_safe(html.escape(str(text)))
```

| # | Solution.lean impl op (`escapeCodepoints`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text : List Char` | `text: str` arg of `escape` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | (no node) | `str(text)` coercion | R | identity on the `List Char` for the `str` inputs F2P passes (mapping.md §2). |
| A3 | result is `escapedSeq text`: the per-code-point substitution `& → &amp; … ' → &#x27;`, computed by the backward `while` fold | `html.escape(str(text))` | A-reference + I | the changed string op is modeled **deeply**: `escapedSeq`/`entity` (pure region) and the verified loop ARE the substitution. No consumed `escapeHtml` axiom. The fold ops (`entity c`, `++`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `html.escape` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A4 | `result` returned (`List Char`) | `mark_safe(...)` wraps the `str` | R | `mark_safe` is identity on character content (mapping.md §2); `test_escape` compares rendered characters. |

Discriminating content of the change — `'` (U+0027) → `&#x27;` not `&#39;` —
lives in `entity '\'' = "&#x27;".toList` (model) ⇔ the `.replace('\'', "&#x27;")`
step of `html.escape` (real). The pre-patch `_html_escapes` mapped `'` → `&#39;`;
`Solution_prepatch.lean` reproduces that and **fails** `out = escapedSeq text`
(G-DIFF).

## B. The urlize decode site — `urlize.unescape` → `html.unescape`

Gold hunks: the nested `unescape(text)` helper (`.replace('&amp;','&')…
replace('&#39;',"'")`, lines 262-269) is deleted; its three call sites become
`html.unescape(...)`. A pure **callee replacement** (kind A).

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `entityDecode` axioms (five single-token facts) | the `html.unescape(...)` call | A-consumed | `entityDecode` is the weakest contract on `html.unescape` the spec needs: it inverts the five emitted entities (mapping.md §3.2). The proof consumes the axioms via the round-trip postconditions (B2). G-AX confirms against real `html.unescape`. |
| B2 | `ensures entityDecode (entity c) = [c]` for `c ∈ {&,<,>,",'}` | the obligation the urlize change preserves: decoding what `escape` emits returns the original char | A-consumed + I | round-trip clause ties the two callees; holds because `html.unescape` inverts `html.escape` on these entities. The new escaper emits `&#x27;` and `html.unescape` decodes it back to `'`; the old urlize `unescape` knew only `&#39;` — why the F2P urlize tests change to `&#x27;`. |

No separate failing prepatch for site B: the urlize change is a callee swap whose
content lives entirely in the frozen `entityDecode` axioms (a prepatch must keep
the spec byte-identical, G-DIFF). Its soundness is audited by G-AX and its
necessity by the round-trip postconditions. Site A's prepatch already exercises
the shared apostrophe mapping.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
escaper's character substitution — is modeled **deeply** (the spelled-out fold
`escapedSeq`, step A3, an A-reference + I), not hidden behind an axiom about the
function under change: there is no consumed `escapeHtml` axiom. The only consumed
axioms, `entityDecode_*` (site B), cover an **unchanged** stdlib callee
(`html.unescape`).

## D. verify(Solution) ⇒ resolved

`escapeCodepoints` verifies only if its output equals the exact per-code-point
substitution with `' → &#x27;` (A3) and the round trips hold (B2). By R
(`str ↔ List Char`, `mark_safe`/`str()` identities) the verified escaper equals
`mark_safe(html.escape(str(text)))` on the tested `str` inputs; by G-AX the deep
model `escapedSeq` equals the real `html.escape` (A-reference) and the real
`html.unescape` meets the `entityDecode` axioms (A-consumed); by G-CONF the R/I
transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: axiom soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
