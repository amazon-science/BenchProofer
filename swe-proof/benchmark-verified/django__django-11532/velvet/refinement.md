# refinement.md — django__django-11532

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`punycodeDomain` `do` block and the `aceEncode` axiom) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom's `ensures`, **A-reference** where a
deep model is validated == the real callee by G-AX), or **I** (identical concrete
op). The A legs and this narrative are audited by **G-EQ**; G-AX checks the axiom
against the real codec. There is no R/I computational content, so G-CONF is
skipped (`conf_skip=true`, see §C).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled change — `CachedDnsName.get_fqdn` (`django/core/mail/utils.py:14`)

Gold hunks (utils.py + the new helper in encoding.py):
```
# django/utils/encoding.py  (new helper — its body is the pre-existing idiom)
+ def punycode(domain):
+     return domain.encode('idna').decode('ascii')

# django/core/mail/utils.py  get_fqdn
-     self._fqdn = socket.getfqdn()
+     self._fqdn = punycode(socket.getfqdn())
```

| # | Solution.lean impl op (`punycodeDomain`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `host : List Char` | the value of `socket.getfqdn()` (the OS host name `str`) | R | `str` ↔ `List Char` (mapping.md §2). The OS lookup is an unchanged callee whose value is the input; no obligation is placed on it, so it is the free input `host`, not an axiom. |
| A2 | `out :| out = aceEncode host` (the `:|` imperative-callee stub) | `punycode(...)` = `domain.encode('idna').decode('ascii')` | A-consumed | the unchanged IDNA ACE codec. The proof consumes `aceEncode_ascii` to discharge the ASCII postcondition; the `ensures out = aceEncode host` pins the result to the codec's output (directive 8 — grounded in the real computation, not an echoable oracle). G-AX validates `aceEncode_ascii` against the real codec. mapping.md §3.1. |
| A3 | `return out` (`List Char`) | `self._fqdn = ...; return self._fqdn` | R + I | caching is an unobservable storage detail (the cache holds exactly the returned value); on character content this is identity. `str` ↔ `List Char` (mapping.md §2). |

Discriminating content of the change — the host is returned **ASCII-normalized**,
not verbatim — lives in the postconditions `out = aceEncode host` and
`∀ c ∈ out, c.val.toNat < 128`. The pre-patch returned the host unchanged;
`Solution_prepatch.lean` reproduces that (`out := host`) and **fails** on exactly
`host = aceEncode host` (and, for a non-ASCII host, the ASCII clause) — G-DIFF.

## B. The behavior-preserving refactor sites (I-refactor — not modeled)

The patch also replaces the inline idiom `X.encode('idna').decode('ascii')` with a
call to the new `punycode(X)` helper at five further sites:

| site | repo location | nature |
|---|---|---|
| `sanitize_address` (domain) | `django/core/mail/message.py:105` | extract idiom → `punycode(domain)`; the surrounding `try/except UnicodeEncodeError` around the *localpart* is unrelated and unchanged. Same codec, behavior-identical. |
| `URLValidator.__call__` (netloc) | `django/core/validators.py:127` | `netloc.encode('idna')...` → `punycode(netloc)`; identical, same `except UnicodeError` surface. |
| `EmailValidator.__call__` (domain_part) | `django/core/validators.py:203` | `domain_part.encode('idna')...` → `punycode(domain_part)`; identical. |
| `Urlizer` (netloc) | `django/utils/html.py:214` | `netloc.encode('idna')...` → `punycode(netloc)`; identical. |
| `is_email_simple` (domain) | `django/utils/html.py:323` | `domain.encode('idna')...` → `punycode(domain)`; identical. |

Each is a pure **callee extraction**: the call site computes the *same value via
the same codec with the same exception behavior* before and after. No observable
behavior changes, so there is no independently-fixed behavior to model and no
failing prepatch is owed (a prepatch must keep the spec byte-identical, G-DIFF).
The PASS_TO_PASS list confirms these sites' existing tests are unaffected; the
sole FAIL_TO_PASS test exercises only the `get_fqdn` site (§A). The codec these
sites share is the same `aceEncode` already audited by G-AX.

## C. No kind-3 (inexpressible-changed-op) steps; G-CONF skipped

Every step is R, A, or I. The one operation that genuinely changed observable
behavior — routing the host through the ACE codec — is an **A-consumed** callee
(an unchanged library codec), not the function under spec. The impl region is a
single A-tagged op, so there is no R/I content to transliterate: `conf_skip=true`
and `conformance_check.py` exits `status=skip`. The A leg's soundness is G-AX; the
refinement fidelity is this doc + G-EQ.

## D. verify(Solution) ⇒ resolved

`punycodeDomain` verifies only if its output equals the ACE codec's output of the
host (A2) and that output is ASCII (`aceEncode_ascii`, G-AX-validated). By R
(`str ↔ List Char`, caching-identity) the verified routine equals
`punycode(socket.getfqdn())` on the host name; that ASCII-normalized host is then
safe to place in the Message-ID header under a single-byte charset, which is
exactly the crash the issue reports and the F2P test
`test_non_ascii_dns_non_unicode_email` checks. The five refactor sites (§B) are
behavior-identical and test-neutral (PASS_TO_PASS). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the one audited callee — and the gold patch resolves (G-RESOLVE). Trust points:
axiom soundness (G-AX) and refinement fidelity (this doc, G-EQ).
