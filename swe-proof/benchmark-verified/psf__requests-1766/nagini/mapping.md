# mapping.md — psf__requests-1766

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 847735553aeda6e6633f2b32e14ba14ba86887a4`, states the type
abstraction, and records that there are no axiomatized callees.

Repo file under change: `requests/auth.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `append_qop_directive(base, ncvalue, cnonce)` | the `if qop:` branch of `HTTPDigestAuth.build_digest_header` — `requests/auth.py:146-147` (the appended credential segment) | the modeled changed code: assembling the credential's quality-of-protection directive segment |
| `qop_segment(ncvalue, cnonce)` | the literal `', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)` appended to `base` at `requests/auth.py:147` (post-patch) | pure spec: the directive segment as a code-point sequence |
| `directive_head()` | the literal head `', qop="auth", nc='` of that format string (post-patch) | pure spec: the head carrying the QUOTED value token |
| `quoted_value_token()` | the literal `"auth"` inside that format string (post-patch) | pure spec: the quality-of-protection value emitted as a quoted string |
| `directive_mid()` | the literal `', cnonce="'` of that format string | pure spec: the segment between the count value and the client-nonce value |
| `directive_tail()` | the literal closing `'"'` of that format string | pure spec: the closing double quote of the client-nonce value |

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

| repo reality | model carrier | bijection |
|---|---|---|
| `base` — the `str` credential already assembled before the `if qop:` branch | `List[int]` of Unicode code points (read-only here) | `s[k]` ↔ `base[k] == ord(s[k])`; `len(s)` ↔ `len(base)`; `str` `+=` of a suffix ↔ list `+` of the suffix code points; empty `str` ↔ `[]` |
| `ncvalue` — the nonce-count token (`'%08x' % self.nonce_count`, a `str`) interpolated by `%s` | `List[int]` of code points (read-only) | `%s` interpolation ↔ list `+` of the token's code points (verbatim, no quoting) |
| `cnonce` — the client-nonce token (a `str`) interpolated by `%s` | `List[int]` of code points (read-only) | `%s` interpolation ↔ list `+` of the token's code points |
| the `str` `%`-format literal `', qop="auth", nc=%s, cnonce="%s"'` | `PSeq[int]` literals (`directive_head` / `directive_mid` / `directive_tail`) with the two `%s` holes replaced by `+ ToSeq(ncvalue)` / `+ ToSeq(cnonce)` | `%`-formatting of constant text + two `%s` substitutions ↔ concatenation of constant code-point sequences with the two interpolated token sequences |
| the credential value carried into `request.headers['Authorization']` | the returned `List[int]` | `mark_safe`-free; the header is the raw `str`, so the F2P substring test `'"auth"' in header` ↔ the contiguous-subsequence property the postcondition pins |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`. The
three inputs are read-only (the credential is rebuilt by re-binding the local
`base` to `base + suffix`; the original `base`, `ncvalue`, `cnonce` objects are
never mutated), so all three are required AND ensured at half permission
(`Acc(list_pred(·), 1/2)`) per SPEC_GUIDE directive 5.

## 3. Callee provenance (kind-A)

None. The directive segment is assembled DEEPLY: every operation is either a
type refinement of a `str`/`%s`/`+=` operation (R) or an identical concatenation
(I). No unchanged opaque library callee is invoked on this path — `%`-formatting
of a constant template with two string substitutions is fully expressible as
sequence concatenation — so there is **no `@ContractOnly` axiom**, **no
A-reference deep model validated against a callee**, and therefore **no
`axiom_check.py`** (nothing for G-AX to execute). See refinement.md.

## G-CONF (differential conformance)

`conformance_check.py` refutes the refinement leg: the model's impl region vs
the REAL patched repo code. Pinned fuzz seed: **1766** (module constant `SEED`).

* **Shadow** — the `# impl-start`/`# impl-end` region of `model.py`, copied
  byte-identically (contract calls stripped; the region has none inside it), plus
  the whole `# pure-start`/`# pure-end` region (`quoted_value_token`,
  `directive_head`, `directive_mid`, `directive_tail`, `qop_segment`) over a
  `PSeq` shim, so the postcondition's right-hand side is diffed too. No
  `@ContractOnly` callees exist in this bundle (§3), so nothing is assumed.
* **Oracle** — §1's repo symbol, `requests.auth.HTTPDigestAuth.build_digest_header`,
  CALLED (never transliterated), on two legs: (A) the `if qop:` statement at
  `requests/auth.py:146-147` located by `ast` in the installed patched source at
  runtime, compiled and executed as repo bytecode over arbitrary
  `base`/`ncvalue`/`cnonce` (the enclosing method derives all three internally
  and exposes no injection point); (B) the whole method driven end-to-end with a
  synthetic Digest challenge, `sys.settrace` recovering the interpreter's own
  `base`/`ncvalue`/`cnonce` around that line. Leg B asserts the executed line is
  the one leg A extracted, so leg A cannot be reading dead code, and that the F2P
  discriminator `'"auth"'` occurs in the returned credential.
* **Type bridge** — §2 inverted: `List[int]` code points ↔ `str` via
  `to_str(cps) = ''.join(chr(c) for c in cps)` / `to_cps(s) = [ord(c) for c in s]`
  (mutual inverses on the generated non-surrogate code points); `%s`
  interpolation ↔ list `+` of the token's code points. Comparison is in the
  code-point domain.
* **Inputs** — 102 017 total, every one satisfying the model's `Requires` (pure
  half-permission over three lists, so any list qualifies): 17 boundary triples
  (all-empty, singleton, the exact F2P credential shape, `%s`/`%d`/`%%`/`%(x)s`
  format-injection tokens, embedded `"`/`,`/`=`, NUL, non-ASCII and astral code
  points, 300-char base) + 100 000 seeded fuzz triples on leg A + 2 000
  end-to-end real-function drives on leg B (qop `auth`, `auth,auth-int`,
  `auth-int,auth`; five HTTP methods; with and without a query string). The impl
  region is straight-line, so one input covers it structurally; the fuzz covers
  the interpolation domain.
* **Recorded verdict** — `G-CONF=pass`, 0 disagreements. Falsification controls
  (run out-of-band, not shipped): against the UNPATCHED /testbed the check fails
  on the first boundary input (`, qop=auth` vs `, qop="auth"`); mutating the
  shadow's quote code points fires the `impl-region` leg; mutating
  `quoted_value_token` alone fires the `pure-region/qop_segment` leg; perturbing
  the recovered client-nonce fires the `build_digest_header` leg.
