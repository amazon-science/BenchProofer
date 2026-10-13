# refinement.md — psf__requests-1766

The operation-by-operation correspondence between `model.py`'s implementation
(the `append_qop_directive` impl region plus the deep `qop_segment` /
`directive_head` / `quoted_value_token` model in the `pure` region) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The directive-assembly site — `HTTPDigestAuth.build_digest_header`

Gold hunk (`requests/auth.py:147`, inside `if qop:`):
```
- base += ', qop=auth, nc=%s, cnonce="%s"' % (ncvalue, cnonce)
+ base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)
```

The fix wraps the quality-of-protection value `auth` in double quotes, so the
emitted directive is `qop="auth"` (a quoted string per RFC 2617) rather than
the bare `qop=auth`. Everything else in the appended segment is unchanged.

| # | model.py impl op (`append_qop_directive`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `base`, `ncvalue`, `cnonce` : `List[int]` | the `str` `base` and the two `%s` arguments `ncvalue`, `cnonce` | R | a text value is modelled by its code-point sequence `List[int]` (mapping.md §2). `base` is the credential assembled before the branch; `ncvalue`/`cnonce` are the count and client-nonce tokens interpolated verbatim. All three are read-only ⇒ half permission (directive 5). |
| A2 | `result = list(base)` then `result = result + [...]` for each piece | `base += '...' % (ncvalue, cnonce)` | R + I | `str` `+=` of the formatted suffix ↔ rebinding `result` to `base ++ suffix` as a `List[int]`. The rebind never mutates the input objects (matching the spec's half-permission frame). |
| A3 | `result + [44,32,113,111,112,61, 34,97,117,116,104,34, 44,32,110,99,61]` — the literal `, qop="auth", nc=` carrying the QUOTED token `"auth"` (`directive_head()`) | the `', qop="auth", nc='` portion of the format template | R + I | `%`-formatting of the constant template head ↔ concatenation of its constant code-point sequence. The QUOTED value token `"auth"` = `quoted_value_token() == PSeq(34,97,117,116,104,34)` is spelled out literally — this is the single behavioural change, modelled DEEPLY as literal code points (not via any callee). The bare-`auth` pre-image is `[...,61,97,117,116,104,44,...]` with no surrounding `34`s. |
| A4 | `result + ncvalue` | the `%s` substitution of `ncvalue` | R + I | the count value is interpolated verbatim, BARE (no quotes) — ↔ list `+` of `ncvalue`'s code points. |
| A5 | `result + [44,32,99,110,111,110,99,101,61,34]` then `result + cnonce` then `result + [34]` — the literal `, cnonce="`, the value, the closing `"` (`directive_mid()` … `directive_tail()`) | the `', cnonce="%s"'` portion of the format template | R + I | unchanged by the gold patch; `%`-format of the constant template + one `%s` ↔ concatenation of the constant code-point sequences with `cnonce`. The client-nonce stays quoted in both pre- and post-patch. |
| A6 | `return result` | `base += ...` leaves the updated `base`, which `build_digest_header` returns inside `'Digest %s'` and `handle_401`/`__call__` place into `request.headers['Authorization']` | R | the returned `List[int]` is the credential the F2P test inspects; the `'Digest '` prefix and the header dict are untouched by the bug and omitted (mapping.md §1). |

The discriminating content of the change — the quality-of-protection value is a
**quoted** string `"auth"` rather than the bare `auth` — lives in
`quoted_value_token() == PSeq(34,97,117,116,104,34)` inside `directive_head()`
(model) ⇔ the `qop="auth"` portion of the format string (real). The pre-patch
code emitted the bare `qop=auth`; `model_prepatch.py` reproduces that (the
impl appends `[...,61,97,117,116,104,44,...]`, the value without surrounding
`34`s) and **fails** the postcondition
`ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)))`,
which is exactly the spec sensing the change (G-DIFF). The F2P test
`test_DIGESTAUTH_QUOTES_QOP_VALUE` asserts `'"auth"' in Authorization`; that
substring (`PSeq(34,97,117,116,104,34)`) is a contiguous subsequence of the
verified result precisely because the postcondition pins
`directive_head().take(6+6).drop(6) == quoted_value_token()`.

## B. The whitespace-only hunk (not modeled)

The gold patch's other hunk (`requests/auth.py:108`) removes trailing
whitespace from the blank-ish line after `A2 = '%s:%s' % (method, path)`:
```
-        <trailing spaces>
+
```
This changes no character of any emitted credential and is observed by no test
(it is interior source whitespace, not part of any string literal). It is
cosmetic and intentionally NOT modeled — modeling it would add no differential
witness. `patch.diff` ships it verbatim (it is part of the gold) but it is
irrelevant to `verify ⟹ resolved`.

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The one operation that genuinely *changed* — the
quality-of-protection value being emitted as a quoted string — is modelled
**deeply** as literal code points (`quoted_value_token()` inside
`directive_head()`, consumed by the postcondition), not hidden behind any
axiom. `%`-formatting of a constant template with two `%s` substitutions is
fully expressible as sequence concatenation, so there is **no consumed axiom
(A-consumed)** and **no deep-model reference validated against a callee
(A-reference)** — and hence no `axiom_check.py`. There is no dead axiom and no
kind-3 step.

## D. verify(model) ⇒ resolved

`append_qop_directive` verifies only if its output equals exactly
`base ++ qop_segment(ncvalue, cnonce)` with the value token in its QUOTED form
`"auth"` (steps A3–A6, the `ToSeq(Result()) == ...` postcondition), and only if
the quoted token sits contiguously at the head of the appended segment (the
`drop(len(base)).take(len(directive_head())) == directive_head()` and
`directive_head()…drop(6) == quoted_value_token()` clauses). By R (str ↔
`List[int]`, `%`-format ↔ concatenation, `+=` ↔ rebind, the unchanged `'Digest '`
prefix and header projection) the verified result equals the credential the
gold patch produces on every `qop`-present challenge. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axioms, so
the only PLAN §1.1 trust point in play is refinement fidelity (this document,
G-EQ); axiom soundness (G-AX) is vacuous here.
