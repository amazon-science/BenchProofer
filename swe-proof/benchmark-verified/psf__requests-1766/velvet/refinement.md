# refinement.md — psf__requests-1766

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `appendQopDirective` `do` block plus the deep `qopSegment` /
`directiveHead` / `quotedValueToken` model in the `pure` region) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
`axiom_check.py` / G-AX), or **I** (identical concrete operation).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
plan §4.1); this narrative is audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

## A. The directive-assembly site — `HTTPDigestAuth.build_digest_header`

Gold hunk (`requests/auth.py:147`, inside `if qop:`):
```
- base += ', qop=auth, nc=%s, cnonce="%s"' % (ncvalue, cnonce)
+ base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)
```

The fix wraps the quality-of-protection value `auth` in double quotes, so the
emitted directive is `qop="auth"` (a quoted string per RFC 2617) rather than the
bare `qop=auth`. Everything else in the appended segment is unchanged.

| # | Solution.lean impl op (`appendQopDirective`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `base`, `ncvalue`, `cnonce` : `List Char` | the `str` `base` and the two `%s` arguments `ncvalue`, `cnonce` | R | a text value is modelled by its character sequence `List Char` (mapping.md §2). `base` is the credential assembled before the branch; `ncvalue`/`cnonce` are the count and client-nonce tokens interpolated verbatim. All three are read-only. |
| A2 | `result := base` then `result := result ++ [...]` per piece | `base += '...' % (ncvalue, cnonce)` | R + I | `str` `+=` of the formatted suffix ↔ rebinding `result` to `base ++ suffix` as a `List Char`. The rebind never mutates the input sequences. |
| A3 | `result ++ [',',' ','q','o','p','='] ++ ['"','a','u','t','h','"'] ++ [',',' ','n','c','=']` — the literal `, qop="auth", nc=` carrying the QUOTED token `"auth"` (`directiveHead`) | the `', qop="auth", nc='` portion of the format template | R + I | `%`-formatting of the constant template head ↔ concatenation of its constant character sequence. The QUOTED value token `"auth"` = `quotedValueToken == ['"','a','u','t','h','"']` is spelled out literally — this is the single behavioural change, modelled DEEPLY (not via any callee). The bare-`auth` pre-image is `[...,'=','a','u','t','h',',',...]` with no surrounding `"` characters. |
| A4 | `result ++ ncvalue` | the `%s` substitution of `ncvalue` | R + I | the count value is interpolated verbatim, BARE (no quotes) — ↔ list `++` of `ncvalue`. |
| A5 | `result ++ [',',' ','c','n','o','n','c','e','=','"']` then `result ++ cnonce` then `result ++ ['"']` — the literal `, cnonce="`, the value, the closing `"` (`directiveMid` … `directiveTail`) | the `', cnonce="%s"'` portion of the format template | R + I | unchanged by the gold patch; `%`-format of the constant template + one `%s` ↔ concatenation of the constant character sequences with `cnonce`. The client-nonce stays quoted in both pre- and post-patch. |
| A6 | `return result` | `base += ...` leaves the updated `base`, which `build_digest_header` returns inside `'Digest %s'` and `handle_401`/`__call__` place into `request.headers['Authorization']` | R | the returned `List Char` is the credential the F2P test inspects; the `'Digest '` prefix and the header dict are untouched by the change and omitted (mapping.md §1). |

The discriminating content of the change — the quality-of-protection value is a
**quoted** string `"auth"` rather than the bare `auth` — lives in
`quotedValueToken == ['"','a','u','t','h','"']` inside `directiveHead`
(Solution.lean) ⇔ the `qop="auth"` portion of the format string (real). The
pre-patch code emitted the bare `qop=auth`; `Solution_prepatch.lean` reproduces
that (the impl appends `['a','u','t','h']`, the value without surrounding `"`)
and **fails** the postcondition
`out = base ++ qopSegment ncvalue cnonce` — exactly the spec sensing the change
(G-DIFF). The F2P test `test_DIGESTAUTH_QUOTES_QOP_VALUE` asserts
`'"auth"' in Authorization`; that substring is a contiguous subsequence of the
verified result precisely because the postcondition pins
`(out.drop base.length).take directiveHead.length == directiveHead` and
`(directiveHead.take (6 + quotedValueToken.length)).drop 6 == quotedValueToken`.

## B. The whitespace-only hunk (not modeled)

The gold patch's other hunk (`requests/auth.py:108`) removes trailing whitespace
from the blank-ish line after `A2 = '%s:%s' % (method, path)`. This changes no
character of any emitted credential and is observed by no test (it is interior
source whitespace, not part of any string literal). It is cosmetic and
intentionally NOT modeled — modeling it would add no differential witness.
`patch.diff` ships it verbatim (it is part of the gold) but it is irrelevant to
`verify ⟹ resolved`.

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The one operation that genuinely *changed* — the
quality-of-protection value being emitted as a quoted string — is modelled
**deeply** as literal characters (`quotedValueToken` inside `directiveHead`,
consumed by the postcondition), not hidden behind any axiom. `%`-formatting of a
constant template with two `%s` substitutions is fully expressible as sequence
concatenation, so there is **no consumed axiom (A-consumed)** and **no deep-model
reference validated against a callee (A-reference)** — and hence no
`axiom_check.py`. There is no dead axiom and no kind-3 step.

## D. verify(Solution) ⇒ resolved

`appendQopDirective` verifies only if its output equals exactly
`base ++ qopSegment ncvalue cnonce` with the value token in its QUOTED form
`"auth"` (steps A3–A6, the `out = ...` postcondition), and only if the quoted
token sits contiguously at the head of the appended segment (the
`drop base.length …` and `directiveHead … drop 6` clauses). By R (`str ↔ List
Char`, `%`-format ↔ concatenation, `+=` ↔ rebind, the unchanged `'Digest '`
prefix and header projection) the verified result equals the credential the gold
patch produces on every `qop`-present challenge; by G-CONF the R/I
transliteration of the assembly agrees with `patch.diff`'s behaviour on the
fuzzed inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axioms, so the only trust point in play is refinement
fidelity (this document, G-EQ + G-CONF); axiom soundness (G-AX) is vacuous here.
