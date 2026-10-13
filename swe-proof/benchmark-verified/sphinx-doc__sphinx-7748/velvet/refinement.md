# refinement.md — sphinx-doc__sphinx-7748

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `collectSignatures` `do` block, plus the deep `collectSigs` model and the
`LineInfo` carrier) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model / carrier validated == the real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs and this narrative are audited by **G-AX** and
**G-EQ**. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

> Gate ownership: **G-AX** audits the patch-independent A-reference only — the
> `LineInfo` bridge == the real unchanged callees (it runs against the *unpatched*
> repo, so it cannot and does not assert any property of the changed function).
> The end-to-end equivalence "deep model `collectSigs` == the real *patched*
> `_find_signature`/`_signatures` + `format_signature` render" is owned entirely
> by **G-CONF** (it applies the gold patch; oracle = patched repo).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change — `DocstringSignatureMixin._find_signature` (`sphinx/ext/autodoc/__init__.py:1040`)

Gold hunk (essence): the inner scan changes from "examine only `doclines[0]`,
take the first matching signature, then `break`" to "scan every line of the
docstring (`for j, line in enumerate(doclines)`): a blank line `break`s; a line
ending in a continuation marker is stripped and flagged `multiline`; a line whose
stripped form matches `py_ext_sig_re` and whose base name is in `valid_names`
yields a signature — the first into `result`, each later one appended to
`self._signatures`; a matched line continues the scan iff it was `multiline`,
else `break`s." `format_signature` then joins `[sig] + self._signatures` with
newlines; `valid_names` is hoisted above the loop; overload documenters get
`objpath = [None]`.

| # | Solution.lean impl op (`collectSignatures`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `lines : List LineInfo` | one docstring `doclines : List[str]` (after `get_doc`/`prepare_docstring` dedent) | R | `List[str]` ↔ `List LineInfo`; each `LineInfo` is derived from the line by the unchanged callees (mapping.md §3). The dedent (`prepare_docstring`) is unchanged and applied before the scan; the carrier is the post-dedent line list. |
| A2 | `LineInfo` fields `blank`/`cont`/`isSig`/`sig` | `not line` / `line.endswith('\\')` / `bool(py_ext_sig_re.match(stripped)) and base in valid_names` / `match.group(4),(5)` | A-reference | the per-line classification uses only **unchanged** callees (`py_ext_sig_re`, `str.endswith`/`rstrip`, the `valid_names` membership). Modeled as the input carrier; G-AX validates the `line_info` bridge == the real callees. NOT the operation the patch changes. |
| A3 | `out := out ++ [l.sig]` inside the `while`, with `stopped`/`i` updates implementing `collectSigs` | the changed loop body (`result`/`self._signatures` accumulation, `break`/`continue` on `multiline`/blank/no-match) | I | the changed control flow is modeled **deeply**: `collectSigs` (pure region) and the verified forward `while` fold ARE the scan. No consumed axiom about the function under change. The fold ops (`l.blank`/`l.isSig`/`l.cont` tests, `++`, the loop) are concrete (I), transliterated by G-CONF. |
| A4 | result `out : List Sig` | `result` (= `out.head?`) + `self._signatures` (= `out.tail`, rendered `"(args) -> retann"`) + `format_signature`'s `"\n".join` | R | `out` ↔ the rendered signature block: head is `result`, tail is the appended `_signatures`. The newline join changes no signature, only concatenates; checked end-to-end by G-CONF (`shadow_render` vs the real `_find_signature` + render). |
| A5 | (the outer `for i, doclines in enumerate(docstrings)` loop) | unchanged: first docstring producing a signature wins | R (identity, omitted) | the modeled method covers ONE docstring's scan — the locus of the change (collecting >1 signature). The outer loop is byte-unchanged pre/post (`if result: break`), so it is not modeled; mapping.md §1. |

Discriminating content of the change — a continuation-marked signature line is
followed by FURTHER signatures, all collected, rather than the scan stopping at
the first match — lives in `collectSigs`'s `if l.cont then l.sig :: collectSigs ls
else [l.sig]` (model) ⇔ the `if multiline: continue else: break` of the new loop
(real). The pre-patch examined only line 0 and produced at most one signature;
`Solution_prepatch.lean` reproduces that (the `else` branch sets `stopped := true`
unconditionally after the first match) and **fails** `out = collectSigs lines`
exactly on the `l.cont` clause (G-DIFF; see the unsolved-goal witness below).

## B. No consumed axioms

This bundle ships **no** consumed `axiom`. The only kind-A construct is the
`LineInfo` carrier (A-reference, A2): the per-line classification is the unchanged
recognizer, supplied as input and validated == the real callees by G-AX. The
changed collection logic is modeled deeply (A3), not hidden behind an axiom about
the function under change. There is therefore no dead axiom and no over-claim
(SPEC_GUIDE §0.7).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
multi-signature collection control flow — is modeled **deeply** (the spelled-out
front-recursive `collectSigs`, step A3, an I op verified against the frozen
postcondition), not behind an axiom. The only A-reference (A2) covers the
**unchanged** per-line recognizer.

## C′. Total-correctness semantics (no vacuity)

Both twins use `loom.semantics.termination "total"` with an explicit
`decreasing` measure `(lines.length - i) + (if stopped then 0 else 1)` on the
scan loop: every step either advances `i` or flips `stopped`, so the measure
strictly drops. Under total semantics a non-terminating impl (e.g. a loop that
never makes progress) cannot verify vacuously — the spec admits only impls
that terminate AND produce `collectSigs lines`.

## D. verify(Solution) ⇒ resolved

`collectSignatures` verifies only if its output equals the exact reading-order
collection `collectSigs lines` (A3) — i.e. it collects the FIRST signature and
every continuation-marked subsequent signature, stopping at a blank line or a
non-continued match. By R (A1/A4: `List[str] ↔ List LineInfo`, `out` ↔
`result`+`_signatures`+join) the verified collector equals the patched
`_find_signature` + `format_signature` on the tested docstrings; by G-AX the
`LineInfo` bridge equals the real unchanged callees (A-reference, audited on the
unpatched repo since the callees are patch-independent); by
G-CONF the R/I transliteration of the fold + render — i.e. the deep model
`collectSigs` rendered as `result`+`_signatures` — agrees with `patch.diff`'s
patched behaviour on ≥10⁵ inputs (this is where the end-to-end
model↔patched-function equivalence is established). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited unchanged
recognizer — and the gold patch resolves (G-RESOLVE). Trust points are exactly
the two of plan §1.1: carrier/abstraction soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
