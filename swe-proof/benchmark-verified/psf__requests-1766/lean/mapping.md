# mapping.md — psf__requests-1766

## Instance
- repo: psf/requests
- base_commit: 847735553aeda6e6633f2b32e14ba14ba86887a4
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`HTTPDigestAuth.build_digest_header` (requests/auth.py:68) assembles the value of
the HTTP **Digest** scheme `Authorization` header by appending a comma-separated
list of directives to a `base` string and prefixing `Digest `. The
quality-of-protection (`qop`) directive was emitted with a *bare token* value:

```python
-            base += ', qop=auth, nc=%s, cnonce="%s"' % (ncvalue, cnonce)
+            base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)
```

Per RFC 2617 the `qop-options` directive value is a quoted string, so the fix
wraps the `auth` value in double quotes (`qop="auth"`). The nonce-count (`nc`)
value remains a bare token; the `cnonce` value remains a quoted string. (The other
hunk in the gold patch is a whitespace-only edit on line 108 — trailing spaces
removed — with no behavioral effect; it is carried in `patch.diff` verbatim.)

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_digestAuthHeader` | `HTTPDigestAuth.build_digest_header` (requests/auth.py:68) — specifically the `base`-assembly tail at :138-149 |
| `problem_spec_digestAuthHeader`   | the post-condition the assembled header value must satisfy |
| `assembledDigestHeader` (pure helper) | the assembled `base` plus the `'Digest %s'` prefix (requests/auth.py:138-149) |

The component values consumed by the assembly are all computed upstream in the
SAME function and are NOT changed by the patch; each is modeled as a free
`String` parameter:

| Lean parameter | Python source @ base_commit |
|---|---|
| `username` | `self.username` |
| `realm`    | `realm = self.chal['realm']` (:70) |
| `nonce`    | `nonce = self.chal['nonce']` (:71) |
| `uri`      | `path` (:102-104) — the request path/query |
| `respdig`  | `respdig` (:128/:130) — `KD(...)`, the response digest hex string |
| `opaqueVal`| `opaque = self.chal.get('opaque')` (:74) |
| `algorithm`| `algorithm = self.chal.get('algorithm')` (:73) |
| `entdig`   | `entdig` (:100, always `None` here — "XXX not implemented yet") |
| `qop`      | `qop = self.chal.get('qop')` (:72) |
| `ncvalue`  | `ncvalue = '%08x' % self.nonce_count` (:116) |
| `cnonce`   | `cnonce = hashlib.sha1(s).hexdigest()[:16]` (:122) |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| every parameter `: String` | the corresponding `str` value | byte-for-byte `str` ↔ `String` identity bijection |
| optional directive "supplied" = non-empty string | Python truthiness of the value (`if opaque:`, `if algorithm:`, `if entdig:`, `if qop:`) | a present optional value is a non-empty `str`; absent ⇒ `None`/`''`, both modeled as `""`. For `qop`, the real code reaches this assembly tail only when `qop` is truthy AND took the `qop == 'auth' or 'auth' in qop.split(',')` branch, so the assembled `qop` directive value is the literal `auth` either way (see refinement.md). |
| result `: String` | the returned `'Digest %s' % base` string | byte-for-byte |

`String` ↔ Python `str` is the identity bijection (byte-for-byte).

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The hash / nonce / path
  computations that PRODUCE the component values (`hash_utf8`, `KD`, `urlparse`,
  `hashlib.sha1`, `time.ctime`, `os.urandom`, `'%08x' % …`) all run UPSTREAM of
  the modeled assembly and are not touched by the patch; their results enter the
  assembly as the free `String` parameters above. The spec holds for EVERY set of
  component values, so the proof consumes no property of any callee and there is
  no `axiom <callee>_prop`. `axiom_check.py` is a skip stub.
- Optional-directive dependency: whether each of the `opaque`, `algorithm`,
  `digest` (entdig) and `qop` directives is appended depends on the truthiness of
  its component value. G-CONF fuzzes all of these present/absent plus the value
  strings.
- `qop` value: when the `qop` directive is appended, its emitted value is the
  literal `auth` (the fixed token); the patch changes only whether that token is
  double-quoted. G-CONF drives `build_digest_header` with `chal['qop']` values
  that take the `qop` branch (`'auth'`, `'auth,auth-int'`) so the appended
  directive is exercised, and with `qop` absent so the directive is omitted.

## G-CONF fuzz seed
- pinned seed: `1766`
- ≥10^5 fuzzed component tuples (the directive strings + present/absent flags for
  the optional directives), bridged to the REAL patched `build_digest_header` via
  a stubbed `HTTPDigestAuth` instance whose `self.chal` and counters are set so
  the upstream computation yields the chosen component values; the shadow is the
  op-for-op transliteration of `implementation_digestAuthHeader`.
