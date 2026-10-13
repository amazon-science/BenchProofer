# refinement.md — psf__requests-1766

Maps every operation in `implementation_digestAuthHeader` to its `patch.diff`
counterpart in `HTTPDigestAuth.build_digest_header` (requests/auth.py:138-149).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** op left as the real repo callee in G-CONF (not axiomatized),
**I** identical concrete op.

## Patch (post-patch `build_digest_header`, header-assembly tail)
```python
base = 'username="%s", realm="%s", nonce="%s", uri="%s", ' \
       'response="%s"' % (self.username, realm, nonce, path, respdig)
if opaque:
    base += ', opaque="%s"' % opaque
if algorithm:
    base += ', algorithm="%s"' % algorithm
if entdig:
    base += ', digest="%s"' % entdig
if qop:
    base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)   # <-- fixed token
return 'Digest %s' % (base)
```

The single changed token is the `qop` directive's value: `qop=auth` (bare token)
→ `qop="auth"` (double-quoted string parameter). Per RFC 2617 the `qop-options`
value is a quoted string. Everything else in the assembly (directive order,
separators, the quoting of the other quoted-string parameters, the bare `nc`
token, the `Digest ` prefix) is unchanged. The second gold hunk (line 108) is a
whitespace-only edit with no behavioral effect.

## Modeling decision
The observable behavior of `build_digest_header` is the returned header string.
Its assembly consumes a fixed set of component values — `username`, `realm`,
`nonce`, the request `uri`/path, the response digest `respdig`, the optional
`opaque`/`algorithm`/`entdig`, the nonce-count `ncvalue` and client-nonce
`cnonce` — all computed UPSTREAM in the same function and unchanged by the patch.
Each is modeled as a free `String` parameter; an empty string denotes an absent
optional directive (Python falsy). The `qop` directive value, when present, is
the literal `auth` (the function reaches this tail only on the `qop == 'auth' or
'auth' in qop.split(',')` branch), so the model takes the fixed token directly;
the change is solely whether that token is double-quoted.

Modeling the component values as free parameters makes the spec hold for EVERY
set of components, so the only thing it can pin is the assembly structure —
directive order, separators, present-iff-non-empty, and the quoting of each
parameter (in particular `qop="auth"`) — which is exactly the fix.

## Operation correspondence
| # | Lean op (`implementation_digestAuthHeader`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut base := "username=\"" ++ username ++ … ++ respdig ++ "\""` | `base = 'username="%s", realm="%s", nonce="%s", uri="%s", response="%s"' % (...)` | R | `str` ↔ `String` byte-identity; the mandatory quoted-string directives. |
| 2 | `if opaqueVal ≠ "" then base := base ++ ", opaque=\"" ++ opaqueVal ++ "\""` | `if opaque: base += ', opaque="%s"' % opaque` | R | Python truthiness ↔ non-empty `String`; quoted-string parameter. |
| 3 | `if algorithm ≠ "" then base := base ++ ", algorithm=\"" ++ algorithm ++ "\""` | `if algorithm: base += ', algorithm="%s"' % algorithm` | R | as #2. |
| 4 | `if entdig ≠ "" then base := base ++ ", digest=\"" ++ entdig ++ "\""` | `if entdig: base += ', digest="%s"' % entdig` | R | as #2 (`entdig` is always `None` here — XXX-not-implemented — so this directive is never emitted; modeled for fidelity). |
| 5 | `if qop ≠ "" then base := base ++ ", qop=\"auth\", nc=" ++ ncvalue ++ ", cnonce=\"" ++ cnonce ++ "\""` | `if qop: base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)` | R | **the fixed op**: `qop` value is the double-quoted literal `auth`; `nc` is a bare token; `cnonce` is a quoted string. Pre-patch emitted bare `qop=auth`. |
| 6 | `return "Digest " ++ base` | `return 'Digest %s' % (base)` | I | the `Digest ` prefix; string concatenation ↔ `%`-format. |

Every op is R or I. No callee is consumed as an axiom and none is deep-modeled as
an A-reference that needs `opaque`: the component-producing callees (`hash_utf8`,
`KD`, `urlparse`, `hashlib.sha1`, `'%08x' % …`) run UPSTREAM and only supply the
free `String` parameters; the assembly itself is pure string concatenation.

## R/I legs ⇒ G-CONF
The entire impl region is R/I content (directive assembly), so `conf_skip =
false`. `conformance_check.py` drives the REAL patched `build_digest_header` over
≥10^5 fuzzed component configurations (realm / nonce / uri / opaque / algorithm /
qop-present combinations), recovers the variable component values from the real
output, rebuilds the header with the Python transliteration of
`assembledDigestHeader` (with the `qop="auth"` quoting MODEL-sourced, not parsed),
and asserts byte-equality. The discriminating clause — `qop` emitted as the
quoted string `"auth"` — is supplied by the model, so a bare-token model would
disagree with the patched oracle.

## No A row
There is no `opaque`/`axiom` declaration in `Solution.lean` (`meta.json axioms =
[]`, `deep_model_references = []`); `axiom_check.py` is a skip stub.

## F2P alignment
`test_DIGESTAUTH_QUOTES_QOP_VALUE` performs a digest-auth request and asserts
`'"auth"' in r.request.headers['Authorization']` — i.e. the `qop` directive value
must be double-quoted. Pre-patch the assembly emitted `qop=auth` (bare), so
`"auth"` (with quotes) was absent — the discriminating clause `problem_spec_…`
pins (`qop` present ⇒ value is the quoted string `"auth"`) and the prepatch impl
(bare `qop=auth`) cannot satisfy it. `patch.diff` (gold verbatim) makes the
harness resolve. (The remaining F2P entries — `test_HTTP_200_OK_GET_ALTERNATIVE`,
`test_cookie_sent_on_redirect`, etc. — are pre-existing tests whose state in the
verified instance flips for unrelated environmental reasons; the behavioral fix
under spec is the qop-quoting change exercised by `test_DIGESTAUTH_QUOTES_QOP_VALUE`.)
