# refinement.md — matplotlib__matplotlib-21568

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `renderTexLabel` `do` block, the deep `protectSeq` model, and the opaque
`reSub`/`removeEmpty` axioms) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses the axiom's
`ensures`), **A-reference** (deep model validated == the real op by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The label wrapper — `_wrap_in_tex(text)` (`lib/matplotlib/dates.py:594`)

Gold hunk (post-patch body, the single changed statement bolded by the diff):
```
  p = r'([a-zA-Z]+)'
  ret_text = re.sub(p, r'}$\1$\\mathdefault{', text)        # CONTEXT (unchanged)
- ret_text = '$\\mathdefault{'+ret_text.replace('-', '{-}')+'}$'
+ ret_text = ret_text.replace('-', '{-}').replace(':', '{:}')
+ ret_text = ret_text.replace(' ', r'\;')
+ ret_text = '$\\mathdefault{' + ret_text + '}$'
  ret_text = ret_text.replace('$\\mathdefault{}$', '')      # CONTEXT (unchanged)
  return ret_text
```

| # | Solution.lean impl op (`renderTexLabel`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text : List Char` | `text: str` arg of `_wrap_in_tex` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `let s := reSub text` | `ret_text = re.sub(p, …, text)` (`dates.py:596`, CONTEXT) | A-consumed (vacuous) | `reSub` is the opaque UNCHANGED letter-run pre-processor; spec asserts nothing about it. Identical in spec, impl, and gold (same real callee), so it carries no discriminator. G-AX checks it is a deterministic function of input. |
| A3 | result of the backward `while` fold = `protectSeq s`: per-code-point `- → {-}`, `: → {:}`, ' ' → `\;`, else identity | `ret_text.replace('-','{-}').replace(':','{:}').replace(' ', r'\;')` | A-reference + I | the CHANGED string op is modeled **deeply**: `protectSeq`/`mathProtect` (pure region) and the verified loop ARE the substitution. No consumed behavioral axiom for it. The fold ops (`mathProtect c`, `++`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of the deep model to the real chained `.replace` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A4 | `"$\\mathdefault{".toList ++ result ++ "}$".toList` | `'$\\mathdefault{' + ret_text + '}$'` | I | concrete string concatenation with literal delimiters; identical on both sides (mapping.md §2). |
| A5 | `removeEmpty (…)` | `ret_text.replace('$\\mathdefault{}$', '')` (`dates.py:600`, CONTEXT) | A-consumed (vacuous) | `removeEmpty` is the opaque UNCHANGED empty-group collapse; spec asserts nothing about it. Identical in spec, impl, and gold (same real callee). G-AX checks determinism. |
| A6 | `out` returned (`List Char`) | `return ret_text` | R | `str` ↔ `List Char` identity on character content the F2P tests compare. |

Discriminating content of the change — the colon `:` (U+003A) → `{:}` and the
space ` ` (U+0020) → `\;`, in addition to the pre-existing `- → {-}` — lives in
`mathProtect ':' = "{:}".toList` and `mathProtect ' ' = "\\;".toList` (model)
⇔ the new `.replace(':', '{:}')` / `.replace(' ', r'\;')` steps (real). The
pre-patch protected only `-`; `Solution_prepatch.lean` reproduces that (`if c =
'-' then "{-}" else [c]`) and **fails** `out = … protectSeq (reSub text) …`
(G-DIFF) precisely on a `:` or ` ` code point.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
math-protection character substitution — is modeled **deeply** (the spelled-out
fold `protectSeq`, step A3, an A-reference + I), not hidden behind an axiom
about the changed op. The only axioms, `reSub`/`removeEmpty`, are
**uninterpreted** maps for the two UNCHANGED context callees (zero behavioural
claim), so they cannot over-claim.

## C. verify(Solution) ⇒ resolved

`renderTexLabel` verifies only if its output equals
`removeEmpty ("$\mathdefault{" ++ protectSeq (reSub text) ++ "}$")` — i.e. the
full per-code-point protection with `: → {:}` and ' ' → `\;` (A3) wrapped and
empty-collapsed exactly as the gold does. By R (`str ↔ List Char`) the verified
wrapper equals the patched `_wrap_in_tex` on the tested `str` inputs; by G-AX
the deep model `protectSeq` equals the real chained `.replace` (A-reference) and
`reSub`/`removeEmpty` are the real unchanged callees (A-consumed, vacuous); by
G-CONF the R/I transliteration of the fold + wrap agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs (with `re.sub`/empty-removal run as the REAL callees).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: axiom soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
