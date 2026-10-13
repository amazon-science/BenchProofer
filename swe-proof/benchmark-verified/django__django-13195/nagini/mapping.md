# mapping.md — django__django-13195

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 156a2138db20abc89933121e4ff2ee2ce56a173a`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change (the behavioural core): `django/http/response.py`.
Two further files change only as call-site wiring (see §4).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `delete_cookie(cookie, key, path, domain, policy)` | `HttpResponseBase.delete_cookie(self, key, path='/', domain=None, samesite=None)` — `django/http/response.py:213` | the modeled changed function (cookie-expiry routine) |
| `store_cookie(cookie, path, domain, secure, policy)` *(axiom — A-consumed)* | `HttpResponseBase.set_cookie(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False, samesite=None)` — `django/http/response.py:158`, **as the expiry routine invokes it**: `set_cookie(key, max_age=0, path=path, domain=domain, secure=secure, expires='Thu, 01 Jan 1970 00:00:00 GMT', samesite=samesite)`. Recording sites: the elapsed lifetime at lines 168-175 (`max-age` + `expires`), the reach at lines 188-191 (`if path is not None:` / `if domain is not None:`), the secure/samesite at lines 195-202 | unchanged community callee the expiry routine invokes after computing the two values; it installs **everything** the emitted cookie carries — lifetime, reach, flags — not only the two attributes the change touches |
| `expiry_secure(key, policy)` *(deep model — A-reference)* | the `secure = (...)` expression of post-patch `delete_cookie` — `django/http/response.py:218-221` post-patch | pure spec: the transport-secure decision (prefix OR case-insensitive "none") |
| `is_none_ci(policy)` | `samesite and samesite.lower() == 'none'` — post-patch `delete_cookie` | pure spec: cross-site policy is the unrestricted "none", case-insensitively |
| `has_security_prefix(key)` | `key.startswith(('__Secure-', '__Host-'))` — `delete_cookie` (pre- and post-patch) | pure spec: name carries a reserved security prefix |
| `lower_cp(c)` | the ASCII case fold inside `str.lower()` as applied to a samesite token **or** to a cookie name before the reserved-name test | pure spec: per-code-point ASCII lower-case |
| `secure_prefix()` / `host_prefix()` | the literals `'__Secure-'` / `'__Host-'` | pure spec: the two reserved prefixes as code-point sequences |
| `is_name_char(c)` / `all_name_chars(key)` | `http.cookies._is_legal_key(key)`, i.e. `re.compile('[%s]+' % re.escape(_LegalChars)).fullmatch` over `_LegalChars = ascii_letters + digits + "!#$%&'*+-.^_\`\|~:"` — `Lib/http/cookies.py` (stdlib, unchanged by the patch) | pure spec: the header grammar's cookie-name alphabet, per code point |
| `equals_ci(key, word)` | `key.lower() == word` as `Morsel.set` applies it to the reserved-name table | pure spec: ASCII-folded equality against a literal |
| `is_reserved_name(key)` | `key.lower() in Morsel._reserved` — `Morsel.set`, `Lib/http/cookies.py`; the table is the stdlib's eight names (`expires`, `path`, `comment`, `domain`, `max-age`, `secure`, `httponly`, `version`) plus `samesite`, which Django installs at import time via `cookies.Morsel._reserved.setdefault('samesite', 'SameSite')` in `django/http/cookie.py` | pure spec: the nine names kept for the header's own attributes |
| `is_storable_name(key)` | the conjunction of `Morsel.set`'s two guards: `if key.lower() in self._reserved: raise CookieError(...)` / `if not _is_legal_key(key): raise CookieError(...)` — a name failing either records nothing and propagates out of `set_cookie` and therefore out of `delete_cookie` | pure spec: the domain in which a cookie is recorded under this name at all (a **precondition** of `delete_cookie`, see §2) |
| `Cookie` object (`expired`, `secure`, `has_path`/`path`, `has_domain`/`domain`, `has_policy`/`policy`) | the `http.cookies.Morsel` stored at `self.cookies[key]` — its already-elapsed lifetime (`['expires']` + `['max-age']` + the empty value), its `['path']` and `['domain']` attributes, its `['secure']` flag and its `['samesite']` attribute | the emitted morsel, projected onto the whole footprint of the emitted expiry cookie: what makes it an expiry (the lifetime), what makes a browser match it against the cookie it is meant to drop (the reach: path + domain), and the two attributes the change touches |

The pre-patch repo symbol the change replaces (for the refinement audit, not
referenced from the consumer spec view): the pre-patch `delete_cookie` body at
`django/http/response.py:213-220`, whose `secure = key.startswith(('__Secure-',
'__Host-'))` lacks the "none" disjunct and whose `set_cookie(...)` call passes
no `samesite=`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` cookie name `key`, `str` samesite token | `List[int]` of Unicode code points | `s[k]` ↔ `key[k] == ord(s[k])`; `len(s)` ↔ `len(key)`; `str.startswith(p)` ↔ `starts_with`; `str.lower()` (ASCII-folded comparison) ↔ `lower_cp` per code point |
| `samesite`, `path` or `domain` that is `None` **or** the empty string `''` (both falsey) | the empty `List[int]` `[]` | for each of the three, the two real values are observationally identical **on the emitted cookie**: the recorder installs nothing of its own from either, so whatever the morsel carries afterwards it already carried. For `samesite`: neither is forwarded (`if samesite:` is false) and neither is the "none" policy (`samesite and samesite.lower()=='none'` is false). For `path`/`domain` the two preimages differ only in *how* they leave the morsel alone — `None` skips the write (`if path is not None:`), `''` writes an empty value, which `Morsel.OutputString` omits from the header exactly as an unset attribute is omitted — so they are identical on the morsel an expiry request creates. The spec therefore states the weakest clause true of both (the reach rows below). The single boundary the spec must discriminate is *non-empty* vs *falsey*, which `len(...) > 0` captures exactly. **Measured, not argued:** `conformance_check.py` runs the real routine on EVERY preimage of every falsey argument and requires the emitted projection to agree (> 2e5 inputs), and `axiom_check.py` checks the same against the setter, including over a morsel that already carries such an attribute. Note the **asymmetry in omission**: leaving `samesite`/`domain` out of the call is a third preimage of the falsey value (their default is `None`), whereas leaving `path` out is **not** — its default is `'/'`, a non-empty value — so an omitted `path` is a preimage of the *site root*, not of the empty list. |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` ops |
| the stored `Morsel`'s `['secure']` flag | `Cookie.secure: bool` | `http.cookies` records `True` when the secure flag is set, `''` (falsey) otherwise; modeled as `secure is True` ↔ `Cookie.secure` |
| the stored `Morsel`'s `['samesite']` attribute | `Cookie.has_policy: bool` + `Cookie.policy: List[int]` | unset ↔ `has_policy is False`; set to value `v` ↔ `has_policy is True and policy == v` |
| the stored `Morsel`'s `['path']` attribute (the request path the cookie applies to) | `Cookie.has_path: bool` + `Cookie.path: List[int]` | carrying no path ↔ `has_path is False`; carrying `v` ↔ `has_path is True and path == v`. `Morsel` reads an unset attribute back as `''` and `OutputString` omits an empty attribute from the header, so "carries no path" is `['path'] == ''` either way |
| the stored `Morsel`'s `['domain']` attribute (the host the cookie belongs to) | `Cookie.has_domain: bool` + `Cookie.domain: List[int]` | as for `path` |
| the stored `Morsel`'s already-elapsed lifetime — `['expires'] == 'Thu, 01 Jan 1970 00:00:00 GMT'` **and** `['max-age'] == 0` **and** an empty cookie value | `Cookie.expired: bool` | the three are fixed together at this call site (they are not arguments of the routine, and the change does not touch them), so the model carries their conjunction as one bit: the emitted cookie either has an already-elapsed lifetime or it does not |
| `max_age` / `expires` / `value` / `httponly` kwargs | omitted | constants of this call site, identical pre- and post-patch (`max_age=0`, the epoch `expires` literal, the default empty value, no `httponly`); their whole effect on the emitted cookie is what `Cookie.expired` carries, and that is pinned. Nothing else the emitted cookie carries is left unmodelled — in particular `path` and `domain` **are** modelled (rows above), as forwarded values. An earlier form of this spec omitted them on the argument that the change does not touch them; that is a wrong modelling boundary rather than a harmless omission, and an audit refuted it with a rival that forged the elapsed lifetime directly on the slice where the two touched attributes are trivial and emitted a cookie with no reach at all (properties.py `weak-forged-expiry-default`; verdict.md). The reach is not "untouched by the change" in the sense that matters: it is *what makes the emitted expiry apply to the cookie being deleted*, and the frozen graded set observes it — `DeleteCookieTests.test_default` asserts the emitted cookie's `path`, and `test_session_delete_on_end_with_custom_domain_and_path` / `test_cookie_setings` assert a custom `path` and `domain`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

**Input domain (D-refinements).** `delete_cookie`'s postconditions describe the
*emitted expiry cookie*, so they are stated exactly on the inputs for which the
real routine emits one. The cookie machinery refuses a request outright on two
independent grounds, and each is a `Requires`:

| repo behaviour on the refused input | model statement | consequence |
|---|---|---|
| `samesite` non-empty and `samesite.lower() not in ('lax','none','strict')` → `set_cookie` raises `ValueError` (`django/http/response.py:196-199`) and the exception propagates out of `delete_cookie` | `Requires(Implies(len(policy) > 0, is_known_policy(policy)))` | the routine raises instead of returning, so no expiry cookie is emitted carrying the requested policy. Note the asymmetry with the name row: `set_cookie` writes `self.cookies[key] = value` on its *first* line and validates the token *last*, so a partially-written morsel can survive the raise — measured: `delete_cookie('__Secure-c', samesite='bogus')` leaves `__Secure-c=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; Secure` in `response.cookies` — but never the cross-site attribute that was asked for, and the caller never gets a return. The spec claims nothing on this input either way |
| `key.lower() in Morsel._reserved` (any casing of the nine reserved names) or `not _is_legal_key(key)` (empty name, or any character outside the name alphabet) → `Morsel.set` raises `CookieError` and nothing is recorded (`Lib/http/cookies.py`, reached through `set_cookie`'s `self.cookies[key] = value`) | `Requires(is_storable_name(key))` | likewise: `delete_cookie` propagates the `CookieError` and emits no cookie of any kind |

The **reach** arguments carry **no** restriction, and that too is measured rather
than assumed: the machinery records the path and the domain without inspecting
them (`if path is not None: self.cookies[key]['path'] = path`), so there is no
refusal path to exclude. `axiom_check.py` and the `ax-containment` probe run the
real patched routine on 5 096 `(path, domain)` pairs — separators, spaces, quotes
and non-ASCII included — and assert it returns and records each value verbatim.

Both name/policy restrictions are domain restrictions of the same kind — they say
*where the emitted cookie is observable*, and nothing about how the expiry derives the two
attributes it carries there. Neither excludes an input the change is about:
every name the two call sites (§4) and the F2P/P2P tests reach
(`settings.SESSION_COOKIE_NAME` = `'sessionid'`, `'messages'`, `'c'`,
`'__Secure-c'`, `'__Host-c'`, `'__Secure-'`, `'__Host-'`, `'x'`,
`'cookie_name'`, `'csrftoken'`, `'__Secure-sessionid'`) satisfies
`is_storable_name`, and every samesite value they reach is falsey or a
recognised token. Both restrictions are **measured, not argued**: the
`ax-containment` probe in `properties.py` runs the real patched `delete_cookie`
and asserts `is_storable_name` agrees with its return-vs-`CookieError` decision
on 20 349 names (full `0x20`–`0x7e` sweep in three shapes, the nine reserved
names × five casings, the empty name, nine non-ASCII code points, 20 000 seeded
fuzz names) with every call-site name inside the domain, and `axiom_check.py`
re-measures the same equivalence on 4 364 names against **both** real routines
(§3.1).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `store_cookie` axiom ↔ `HttpResponseBase.set_cookie` (A-consumed)
**Callee:** `django/http/response.py:158` `set_cookie`. The expiry routine calls
it after computing the secure flag and the samesite value; `set_cookie` is
**unchanged** by this issue. Relevant body (lines 195-202):

```python
if secure:
    self.cookies[key]['secure'] = True
...
if samesite:
    if samesite.lower() not in ('lax', 'none', 'strict'):
        raise ValueError('samesite must be "lax", "none", or "strict".')
    self.cookies[key]['samesite'] = samesite
```

The same call also stamps the lifetime and the reach (lines 168-175, 188-191):

```python
if max_age is not None:
    self.cookies[key]['max-age'] = int(max_age)
    if not expires:
        self.cookies[key]['expires'] = http_date(time.time() + max_age)
if path is not None:
    self.cookies[key]['path'] = path
if domain is not None:
    self.cookies[key]['domain'] = domain
```

The axiom encodes only the obligations the expiry site relies on, in the
**cumulative** form the code above has — a set branch and no clearing branch,
writing into whatever morsel `self.cookies[key]` already holds:

  - storing through this setter is what stamps the already-elapsed lifetime, so a
    cookie stored through it always carries one (`cookie.expired`). The lifetime
    constants are not parameters of the axiom because they are constants of the
    call site: the expiry routine always passes `max_age=0` with the epoch
    `expires` literal, pre- and post-patch alike;
  - the transport-secure flag accumulates: a request to set it turns it on and
    nothing turns it off (`cookie.secure == (Old(cookie.secure) or secure)`);
  - a **non-empty** path installs itself verbatim as the stored cookie's reach,
    and a non-empty domain likewise (`Implies(len(path) > 0, cookie.has_path)`
    plus the verbatim-value clause). Handed an **empty** one the setter installs
    none of its own, so any value the stored cookie carries afterwards is one it
    already carried, unchanged — the weakest clause true of BOTH falsey
    preimages, since `None` skips the write while `''` writes a value the header
    omits (§2); and
  - a **non-empty** samesite value installs itself verbatim as the cross-site
    attribute while an empty one changes nothing, so an attribute already
    present survives (`cookie.has_policy == (Old(cookie.has_policy) or
    len(policy) > 0)`, value forwarded when non-empty, untouched when empty).

This is the **weakest** contract the proof needs: it says nothing about
`httponly`, nothing about the cookie's value, and nothing about how the lifetime
is spelled (only that storing through the setter yields an already-elapsed one).
It does not over-claim either of the two refusal paths, both of which are out of
the consumed domain because the caller's `Requires` (§2) exclude them:

  - the samesite validation `ValueError`: the spec only ever passes the *valid*
    policy tokens that flow through `delete_cookie` (lax / none / strict in any
    casing, or nothing at all; the call sites pass
    `settings.SESSION_COOKIE_SAMESITE`, validated elsewhere); and
  - the `Morsel.set` `CookieError` for a name the machinery records nothing
    under: `Requires(is_storable_name(key))` at the caller confines every
    invocation this axiom speaks about to a name the setter accepts. The name is
    not a parameter of the axiom — the `Cookie` **is** the morsel held under it —
    so without that caller-side restriction the axiom's `Ensures` would be
    describing a morsel that was never created.

**Flag dependency:** the axiom is sound for the default `httponly`/`secure`
semantics of `set_cookie`; the only behaviour relied on is the
`secure`/`samesite` recording above.

**Soundness check (G-AX):** `axiom_check.py` constructs a real `HttpResponse`
and calls the real `set_cookie` **exactly as the expiry call site invokes it**
(the elapsed-lifetime constants included) over the full cross product of
representative names, the valid samesite tokens `{None, '', lax/Lax/LAX,
none/None/NONE/nOnE, strict/Strict/STRICT}`, the reach values `{None, '', '/',
'/example/', '/a b', '/é'} × {None, '.example.com'}` and `{secure True/False}`,
plus 4000 fuzzed tuples, and asserts every emitted morsel meets the axiom's
`Ensures` (10 240 cases). The clauses stated against `Old(...)` — the secure
accumulation, the policy survival, and the installs-nothing-of-its-own reach
clauses — are claims about a morsel that ALREADY carries attributes, so a
dedicated block gives the morsel a pre-existing record through the same real
setter first and checks them against that observed pre-state; measured from a
fresh morsel alone they would be trivially true. Its
`(A-domain)` section additionally measures the domain the axiom and the spec
speak about: on 4 364 names (the boundary names, the full printable-ASCII sweep
in three shapes, the nine reserved names in five casings, the empty name,
non-ASCII, and 4 000 seeded fuzz names) it asserts `is_storable_name` agrees
with *records-vs-refuses* for the real `set_cookie` **and** with
*returns-vs-raises* for the real post-patch `delete_cookie`, and that every
boundary name is inside the domain.

### 3.2 `expiry_secure` + forwarding deep model ↔ post-patch `delete_cookie` (A-reference)
The two decisions the change *introduces* are modelled **deeply** (spelled-out
predicates over the code-point strings), not behind a consumed axiom:

  - `expiry_secure(key, policy) = has_security_prefix(key) or is_none_ci(policy)`
    mirrors `key.startswith(('__Secure-','__Host-')) or (samesite and
    samesite.lower() == 'none')`. The short-circuit `samesite and ...` is
    falsey for `None`/`''` (→ empty list → `is_none_ci([])` false), and the
    case-insensitive `.lower() == 'none'` is `is_none_ci` (ASCII fold, length 4
    spelling n,o,n,e). Source: `django/http/response.py:218-221` post-patch.
  - the verbatim forwarding `samesite=samesite` onto `set_cookie`.

These are validated **== the real post-patch `delete_cookie`** out-of-band by
`axiom_check.py` (G-AX): it calls the real `delete_cookie(key, path=..., domain=...,
samesite=policy)` over the same boundary + fuzz set (7 300 cases, including a
pre-existing-record block and the omitted-`path` form the graded tests reach most
often) and asserts the emitted morsel meets EVERY postcondition `model.py` states
of it — the already-elapsed lifetime, the secure flag equal to `expiry_secure(key,
policy)` accumulated, the samesite attribute equal to the forwarded value, and the
reach the routine was asked for. This is an **A-reference** (deep model checked against the real
callee), NOT a consumed axiom — there is no `delete_cookie` `@ContractOnly`.

## 4. Call-site wiring (R/I — no separate model)

The patch also threads the existing `settings.SESSION_COOKIE_SAMESITE` value
into two `delete_cookie` call sites, with no new behaviour of their own:

| repo site (file:line @ base_commit) | change | handling |
|---|---|---|
| `django/contrib/sessions/middleware.py:41-45` | add `samesite=settings.SESSION_COOKIE_SAMESITE` to the `response.delete_cookie(...)` call | pure argument wiring (I): passes an already-existing setting into the now-`samesite`-aware routine modelled by `delete_cookie`. No independent behaviour. |
| `django/contrib/messages/storage/cookie.py:92-96` | likewise add `samesite=settings.SESSION_COOKIE_SAMESITE` to the `response.delete_cookie(...)` call | pure argument wiring (I). |

Both sites observe the SAME behaviour as the modelled `delete_cookie` reached
with `policy = settings.SESSION_COOKIE_SAMESITE` (default `'Lax'`): the emitted
expiry cookie now carries `SameSite=Lax`. Their F2P tests
(`test_cookie_setings`, `test_session_delete_on_end*`) are exactly the
`delete_cookie` forwarding behaviour observed through the call site. No separate
contracted function is needed: the wiring adds no operation Nagini cannot
already see in `delete_cookie`'s spec.
