# mapping.md — django__django-13195

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 156a2138db20abc89933121e4ff2ee2ce56a173a`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo files under change:
- `django/http/response.py` — the cookie-clearing routine (the core change).
- `django/contrib/messages/storage/cookie.py` — a message-storage clear site.
- `django/contrib/sessions/middleware.py` — a session middleware clear site.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deleteCookie (key path domain samesite)` | `HttpResponseBase.delete_cookie` — `django/http/response.py:213` | the modeled changed function (the cookie-clearing routine) |
| `clearMessageCookie (cookieName domain configuredPolicy)` | `BaseStorage._update_cookie` clear branch — `django/contrib/messages/storage/cookie.py:81` (delete at body line 95) | modeled changed function (call site forwarding the policy) |
| `clearSessionCookie (sessionName path domain configuredPolicy)` | `SessionMiddleware.process_response` clear branch — `django/contrib/sessions/middleware.py:26` (delete at body line 41) | modeled changed function (call site forwarding the policy) |
| `mkCookie` *(deep model — A-reference)* | `HttpResponseBase.set_cookie` — `django/http/response.py:158` | unchanged attribute-setter callee; deep-modeled on its thirteen touched fields, validated `== set_cookie` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `epochExpiry` / `clearedMaxAge` | the `expires='Thu, 01 Jan 1970 00:00:00 GMT'` / `max_age=0` arguments the clearing call passes — `response.py:220-222` post-image | pure spec: the past expiry moment and the spent lifetime a clearing directive announces |
| `hasSecurePrefix` | `key.startswith(('__Secure-', '__Host-'))` — `response.py:216` post-image | pure spec: reserved-namespace test |
| `crossSiteUnrestricted` | `samesite and samesite.lower() == 'none'` — `response.py:218` post-image | pure spec: unrestricted-policy test |
| `secureForClear` | `key.startswith((...)) or (samesite and samesite.lower()=='none')` — `response.py:217-219` post-image | pure spec: the secure flag a cleared cookie must carry |
| `acceptedPolicy` | the `set_cookie` guard `samesite.lower() in ('lax','none','strict')` else `ValueError` — `response.py:199-203` | precondition: the accepted cross-site-policy domain |
| `recordableKey` / `nameChar` / `reservedAttributeName` / `lowered` | the guard the attribute-setter reaches when it files the morsel (`self.cookies[key] = value`, `response.py:169`): the container's item assignment refuses a name that is empty, contains a character outside the cookie-name alphabet, or (case-insensitively) is one of the names kept for a directive's own attributes — recording NOTHING and failing outright | precondition: the names the setter will actually record |
| `domainStated` | `if domain is not None: morsel['domain'] = domain` — `response.py:193-194`, where the empty text is ALSO the morsel's unset sentinel, so an empty scope and an absent one are indistinguishable on readback | precondition: a domain scope is absent or actually names one |

The setting `settings.SESSION_COOKIE_SAMESITE` (default `'Lax'`,
`django/conf/global_settings.py:468`) is the *value* the two call sites forward;
in the spec it is the abstract parameter `configuredPolicy : Option String`
(an accepted policy). The two call sites' delete branch is reached when there is
no data to store / the session is empty (`response.py` is unaffected by which).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the cookie key / name (`str`) | `String` | identity on ASCII; `str.startswith(prefix)` ↔ `String.startsWith` |
| WHICH cookie the emitted directive is filed under (the key of `response.cookies`) | `Cookie.name : String` | identity on ASCII; the single key present in `response.cookies` after the clear ↔ `Cookie.name` |
| the name the filed entry ANNOUNCES on the wire (the name half of the emitted header, read off the entry itself rather than off the container) | `Cookie.transmittedName : String` | identity on ASCII. The emitted header's name half is built from the ENTRY's own name, not from the key it is filed under, so the two are separate observables. Only handing a body over for a cookie fixes the entry's own name; an entry placed into the container ready-made carries no name of its own and announces nothing (the unset state ↔ `""`) |
| `path` (`str`, default `'/'`) | `String` | identity |
| `domain` (`str` or `None`) | `Option String` | `None` ↔ `none`; `d` ↔ `some d` |
| `samesite` (`str` or `None`; an accepted policy) | `Option String` | `None` ↔ `none`; `s` ↔ `some s`; `str.lower()` ↔ `String.toLower` |
| the cleared cookie's `secure` morsel | `Cookie.secure : Bool` | Python sets `morsel['secure']=True` iff truthy; `''` (unset) ↔ `false`, `True` ↔ `true` |
| the cleared cookie's body (`morsel.value`) | `Cookie.value : String` | identity; the clearing call passes the empty body, so `''` ↔ `""` |
| the form that body is TRANSMITTED in (`morsel.coded_value`, what the header carries after the `=`) | `Cookie.codedValue : String` | identity. The cookie container's item assignment runs the body through `value_encode`, so an EMPTY body is transmitted as the quoted empty string `'""'`, never as `''`. Filing a morsel without going through that encoding leaves `coded_value` `''` and emits `k=` where the real one emits `k=""` |
| the cleared cookie's `comment` morsel | `Cookie.comment : Option String` | `''` (unset) ↔ `none`; a NON-EMPTY note ↔ `some c`. The clearing call states none. The empty text is the unset sentinel, so `some ""` is outside this bijection's image — no reachable morsel state corresponds to it |
| the cleared cookie's `version` morsel | `Cookie.version : Option String` | `''` (unset) ↔ `none`; a NON-EMPTY version ↔ `some v`. The clearing call states none. As for `comment`, `some ""` is outside the image |
| the cleared cookie's `max-age` morsel | `Cookie.maxAge : Option Nat` | `''` (unset) ↔ `none`; an integer `n` ↔ `some n`. The clearing call passes `0`, so the granted lifetime is `some 0` |
| the cleared cookie's `expires` morsel | `Cookie.expires : Option String` | `''` (unset) ↔ `none`; a date string ↔ `some s`. The clearing call passes the epoch moment |
| the cleared cookie's `httponly` morsel | `Cookie.httpOnly : Bool` | `morsel['httponly']=True` iff truthy; unset ↔ `false`. The clearing call passes no such flag |
| the cleared cookie's `samesite` morsel | `Cookie.samesite : Option String` | `set_cookie` sets the morsel only when `samesite` truthy; unset ↔ `none`, present value ↔ `some v` |
| the cleared cookie's `path` morsel | `Cookie.path : String` | identity (path is always passed, non-None) |
| the cleared cookie's `domain` morsel | `Cookie.domain : Option String` | unset ↔ `none`, present ↔ `some d` |
| `response.set_cookie(...)` attribute-setter | `mkCookie` (deep model) | records exactly the fields above; see §3.1 |

`Char`/`String` indexing in Lean is total and sound. The carrier for the cookie
is a 13-field `structure` (`Cookie`) holding the addressee, the name the entry
announces on the wire, the two body forms,
and the attributes the behavior touches; the bijection above is the field-wise
correspondence G-AX checks.

That carrier is now COMPLETE for the emitted header, which is what makes this a
closure rather than one more field. The emitted header is a function of exactly
these observables: its name half is the entry's own name, its body half is the
transmitted body form, and its attribute tail is the set attributes rendered in a
FIXED order — the container seeds every attribute slot when it creates an entry,
so the order the attributes come out in is not a further degree of freedom an
implementation could differ on. Measured, 4000 entries reaching the same
observable tuple by different construction routes and different attribute
insertion orders emit byte-identical headers, 0 disagreements. So with the
announced name observed there is no remaining part of the header outside the
carrier.

`Cookie.codedValue` is carried because the header a response TRANSMITS is built
from the name, then the body's encoded form, then the set attributes — so two
directives that agree on every attribute but disagree on the transmitted body
form emit different headers. The two session checks of this behavior compare that
header verbatim against a string containing `{}=""`, so the encoding is directly
observed. Only the cookie container's own item assignment applies it; a routine
that files a morsel by hand agrees on all ten attributes and still transmits `k=`.
`comment`/`version` are carried for the dual reason: a clearing directive states
neither, so they are the attributes a directive could silently ADD without moving
any other observable.

The lifetime pair (`maxAge` / `expires`) is carried because it is what
distinguishes a CLEARING directive from an ordinary cookie assignment that
happens to carry the same flags and scope: a morsel stating neither is retained by
the browser for the rest of the session, so an entry lacking them has not dropped
the cookie at all. Both are `Option`-valued precisely so an OMITTED attribute
(`''`, the morsel's unset sentinel) is a different observable value from a stated
one, rather than collapsing onto it. An earlier revision of this bundle projected
only the five flag/scope fields; that projection could not see the difference, and
the two hidden checks that read `max-age` and `expires` back off the cleared
cookie were outside everything the spec observed.

`Cookie.name` is the ADDRESSEE of the clearing directive — which cookie the
response is telling the browser to drop. In the repo it is not a morsel
*attribute* but the key the morsel is filed under in `response.cookies`, which is
what the tests of this behavior read when they look a cleared cookie up
(`response.cookies['messages']`). Both executable checks read
it as the key actually present after the clear rather than assuming the requested
one, so a routine clearing some other cookie is observably different.

`Cookie.transmittedName` is the name that same directive ANNOUNCES, and it is a
SECOND observable rather than a restatement of the first. Where an entry is filed
is a fact about the response's container; what the entry announces is a fact about
the entry, and it is the announced name that reaches a recipient — the emitted
`Set-Cookie: <name>=...` header takes its name half from the entry itself. The two
can disagree: an entry can sit under exactly the right cookie and announce another
name, or none at all, and a check that looks the cookie up by the key it is filed
under, or reads any single attribute off it, cannot tell. The session checks of
this behavior compare that emitted header verbatim against a string naming the
session cookie, so they read the announced name directly. Both carried names are
therefore observed, and `mkCookie` states that the real callee makes them agree.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `mkCookie` deep model ↔ `HttpResponseBase.set_cookie` (A-reference)
**Callee:** `HttpResponseBase.set_cookie` (`django/http/response.py:158`), the
unchanged low-level attribute-setter. The clear routine calls
`set_cookie(key, max_age=0, path=path, domain=domain, secure=secure,
expires='Thu, 01 Jan 1970 00:00:00 GMT', samesite=samesite)`. On the thirteen fields
the requested behavior observes, `set_cookie`:

- files the morsel under `key` (`self.cookies[key] = value`, `response.py:169`),
  so the directive is addressed to that cookie and to no other;
- and makes that same entry ANNOUNCE that cookie: the hand-over at
  `response.py:169` goes through the container's own item assignment, which fixes
  the entry's own name as well as encoding the body, so the name the entry puts on
  the wire is `key`. This holds for a cookie that ALREADY had an entry on file too
  — the hand-over restates the entry's own name rather than leaving whatever it
  announced before — so the announced name cannot be stale. An entry placed into
  the container ready-made never goes through that step, carries no name of its
  own, and announces nothing;
- stores the body it is handed as `morsel.value` — the clearing call hands over
  the empty body (the `value` parameter's default, `response.py:158`);
- transmits that body in its ENCODED form: the assignment at `response.py:169`
  goes through the cookie container's own item assignment, which runs the body
  through `value_encode` and stores the result as `morsel.coded_value`. An empty
  body encodes to the quoted empty string, so the emitted header reads `k=""`;
- leaves `comment` and `version` unset (`''`) — the clearing call states neither;
- sets `morsel['max-age'] = max_age` iff `max_age is not None`
  (`response.py:186-187`), else leaves it unset (`''`);
- sets `morsel['expires'] = expires` for a string `expires`
  (`response.py:182-183`), else leaves it `''`; when `max_age` is given and
  `expires` is falsy it derives an expiry from the clock instead
  (`response.py:187-188`), so an omitted epoch string is observably different;
- sets `morsel['secure'] = True` iff `secure` is truthy (else leaves it `''`);
- sets `morsel['httponly'] = True` iff `httponly` is truthy — the clearing call
  passes no such flag, so it stays unset (`''`);
- sets `morsel['samesite'] = samesite` iff `samesite` is truthy (an accepted
  value), else leaves it unset (`''`);
- always sets `morsel['path'] = path` (path is never None here);
- sets `morsel['domain'] = domain` iff `domain` is not None, else leaves unset.

`mkCookie key secure samesite path domain` records exactly this field-wise image
(absent policy/domain ↔ `none`), with the emptied body, that body's transmitted
form `quotedEmptyBody`, the announced name `key` the hand-over fixes,
the spent lifetime `clearedMaxAge` and the announced
expiry `epochExpiry` the clearing call supplies, and no note or version.

**Declared domain.** This correspondence holds on the names the setter will
actually record. Handed an empty name, a name containing a character outside the
cookie-name alphabet, or (case-insensitively) one of the names kept for a
directive's own attributes, the container's item assignment records NOTHING and
fails outright — there is no filed directive for `mkCookie` to be the image of.
`recordableKey` declares that region, for exactly the reason `acceptedPolicy`
declares the policy region; `domainStated` likewise excludes the empty scope,
where the morsel cannot distinguish "set to empty" from "never set". G-AX measures
this boundary in BOTH directions: every name the predicate admits is recorded, and
every name it excludes raises. There is **no consumed `setCookie` axiom**; the
deep model `mkCookie` IS the relevant projection, validated equal to the real
`set_cookie` by `axiom_check.py` (G-AX) over the accepted-policy domain.

**`path` and `domain` are deliberately UNCONSTRAINED, and that is faithful in the
reference environment.** No `require` bounds the *characters* of `path`, and
`domainStated` excludes only the empty scope, so a `path` or `domain` containing a
C0 control character (`\x00`–`\x1F`, `\x7F` — 33 codepoints, `'\n'` and `'\t'`
among them) is in-domain and the postcondition demands the morsel carry it
verbatim. That is what the real callee does *here*. The reference is the pinned
instance image — the same container `run_in_container` starts for G-AX and G-CONF
and the same one the resolve oracle runs FAIL_TO_PASS / PASS_TO_PASS in — whose
interpreter is **CPython 3.6.13**, and whose `http.cookies.Morsel.__setitem__`
performs no control-character screening: it is `dict.__setitem__` after the
reserved-key test. Measured in that container on the post-patch worktree,
`delete_cookie('c', path='\n')` returns normally with `morsel['path'] == '\n'`,
and `delete_cookie('c', path='/', domain='a\nb', samesite='none')` returns with
`domain == 'a\nb'` and `secure is True` — field-for-field `mkCookie`. `axiom_check.py`
now measures this census in both parameters rather than leaving it to prose.

This is a live trap for a reader who materializes the worktree at `base_commit`
and drives it with a *host* interpreter instead: CPython gained
`http.cookies._has_control_character` and the `Morsel.__setitem__` guard that
raises `CookieError("Control characters are not allowed in cookies ...")` in a
later security release (present in the 3.10.20 build on this host, absent in
3.6.13). The screening lives wholly in the CPython stdlib, so it moves with the
*interpreter*, not with the repository or the patch: the same `base_commit` bytes
accept `path='\n'` under the pinned interpreter and reject it under a newer one.
The pinned interpreter is the reference, because the release claim is "verify ⇒
the FAIL_TO_PASS/PASS_TO_PASS oracle passes" and that oracle runs in this image.
Adding a control-character `require` would narrow the spec off the real callee's
domain and drop obligations the panel batteries rely on; the spec is correct as it
stands.

The changed operations themselves — deriving `secure` from key-prefix **or** an
unrestricted policy, and forwarding the addressee and `samesite`/`path`/`domain`
— are modeled
**concretely** in the impl (`secureForClear`, the field-wise `mkCookie` call),
so they are **R/I** ops (G-CONF), not axioms.

**Soundness check (G-AX):** `axiom_check.py` constructs a real `HttpResponse`
in-container, calls `delete_cookie` (post-patch) on boundary + fuzzed
`(key, path, domain, samesite)` tuples, reads back the resulting morsel *and the
key it is filed under*, and asserts it equals the field-wise model
`mkCookie(key, secureForClear key samesite, samesite, path, domain)` on all thirteen
observed fields — the lifetime pair, the transmitted body form, the name the entry
announces on the wire (read off the entry itself, not off the container) and the
note/version attributes included — over the whole alphabet a recordable name
admits, and separately confirms every name outside the declared domain raises. Imports only Django (the repo under
test). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`13195`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`secureForClear` / `crossSiteUnrestricted` / `hasSecurePrefix` and the field-wise
`mkCookie` (the R/I-tagged ops) to Python and compares the thirteen observed morsel
fields — the addressee, the name the entry announces on the wire, the lifetime
pair, the transmitted body form and the
note/version attributes included — against the real patched `delete_cookie` over
≥10⁵ fuzzed inputs drawn from the whole recordable-name alphabet.
There are no A-consumed callees, so nothing is left as a real-callee stub on the
shadow side; the single callee `set_cookie` is exercised live by the oracle.
