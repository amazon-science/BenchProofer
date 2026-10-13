# mapping.md — psf__requests-1766

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 847735553aeda6e6633f2b32e14ba14ba86887a4`, states the type
abstraction, and records that there are no axiomatized callees.

Repo file under change: `requests/auth.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `appendQopDirective base ncvalue cnonce` | the `if qop:` branch of `HTTPDigestAuth.build_digest_header` (`requests/auth.py:146-147`): assembling the credential's quality-of-protection directive segment onto the already-built `base` | the modeled changed code |
| `qopSegment ncvalue cnonce` | the literal `', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)` appended to `base` at `requests/auth.py:147` (post-patch) | pure spec: the directive segment as a character sequence |
| `directiveHead` | the literal head `', qop="auth", nc='` of that format string (post-patch) | pure spec: the head carrying the QUOTED value token |
| `quotedValueToken` | the literal `"auth"` inside that format string (post-patch) | pure spec: the quality-of-protection value emitted as a quoted string |
| `directiveMid` | the literal `', cnonce="'` of that format string | pure spec: the segment between the count value and the client-nonce value |
| `directiveTail` | the literal closing `'"'` of that format string | pure spec: the closing double quote of the client-nonce value |

The pre-patch repo symbol the change replaces (for the refinement audit, not
referenced from the consumer spec view): the same `if qop:` line emitting the
BARE value `', qop=auth, nc=%s, cnonce="%s"'` (`requests/auth.py:147`
pre-patch). The whitespace-only hunk at `requests/auth.py:108` (trailing
spaces removed after `A2 = '%s:%s' % (method, path)`) is cosmetic — it changes
no character of any emitted string and no test observes it; it is NOT modeled.

`build_digest_header` is invoked through `HTTPDigestAuth.handle_401`
(`requests/auth.py:174`) and `HTTPDigestAuth.__call__` (`requests/auth.py:188`),
which place the returned credential into `request.headers['Authorization']` —
exactly the value the F2P test `test_DIGESTAUTH_QUOTES_QOP_VALUE` inspects
(`assert '"auth"' in r.request.headers['Authorization']`).

## 2. Type abstraction (R-refinements)

| repo reality | Solution.lean carrier | bijection |
|---|---|---|
| `base` — the `str` credential already assembled before the `if qop:` branch | `List Char` | `s[k]` ↔ `base[k]`; `len(s)` ↔ `base.length`; `str` `+=` of a suffix ↔ list `++` of the suffix; empty `str` ↔ `[]` |
| `ncvalue` — the nonce-count token (`'%08x' % self.nonce_count`, a `str`) interpolated by `%s` | `List Char` | `%s` interpolation ↔ list `++` of the token (verbatim, no quoting) |
| `cnonce` — the client-nonce token (a `str`) interpolated by `%s` | `List Char` | `%s` interpolation ↔ list `++` of the token |
| the `str` `%`-format literal `', qop="auth", nc=%s, cnonce="%s"'` | `List Char` literals (`directiveHead` / `directiveMid` / `directiveTail`) with the two `%s` holes replaced by `++ ncvalue` / `++ cnonce` | `%`-formatting of constant text + two `%s` substitutions ↔ concatenation of constant character sequences with the two interpolated tokens |
| the credential value carried into `request.headers['Authorization']` | the returned `List Char` | the header is the raw `str`, so the F2P substring test `'"auth"' in header` ↔ the contiguous-subsequence property the postcondition pins |

The three inputs are read-only: the credential is rebuilt by re-binding the
local `result` to `result ++ suffix`; the original `base`, `ncvalue`, `cnonce`
sequences are never mutated. `'Digest '` prefix and the surrounding header dict
are untouched by the change and omitted (§1).

## 3. Callee provenance (kind-A)

None. The directive segment is assembled DEEPLY: every operation is either a
type refinement of a `str`/`%s`/`+=` operation (R) or an identical concatenation
(I). No unchanged opaque library callee is invoked on this path — `%`-formatting
of a constant template with two string substitutions is fully expressible as
sequence concatenation — so there is **no axiom**, **no deep-model reference
validated against a callee**, and therefore **no `axiom_check.py`** (nothing for
G-AX to execute). See refinement.md.
