# mapping.md — django__django-13195

## Symbol binding (file:line @ base_commit 156a2138db20abc89933121e4ff2ee2ce56a173a)

Code the patch ADDS has no base-commit line and is cited as `patch.diff`.
`stdlib http/cookies.py:N` line numbers are at CPython 3.10.20 (the interpreter
the measurements below were taken on); the container's interpreter is 3.6.13, so
its line numbers differ while the code cited is the same — the one place where
the two interpreters genuinely DISAGREE is called out under `keyAccepted` below.

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_deleteCookie` / `problem_spec_deleteCookie` / `correct_deleteCookie` | `HttpResponseBase.delete_cookie` | `django/http/response.py:213-220` (signature + body; the patch rewrites both) |
| `implementation_messagesDelete` / `problem_spec_messagesDelete` | the `else:` deletion branch of `CookieStorage._update_cookie` (one statement) | `django/contrib/messages/storage/cookie.py:94-95` |
| `implementation_sessionDelete` / `problem_spec_sessionDelete` | the empty-session deletion branch of `SessionMiddleware.process_response` — BOTH of its statements: the `delete_cookie` call AND the `patch_vary_headers` call | `django/contrib/sessions/middleware.py:40-46` (deletion call at `:41-45`, vary marking at `:46`) |
| `setCookie` (pure helper) | `HttpResponseBase.set_cookie`: the container entry it selects (`self.cookies[key] = value`), the two components that entry is RENDERED with, its payload and all nine of its attributes, with the other entries and the rest of the response left as they were | `django/http/response.py:158-202` (index write at `:169`) |
| `varyMarked` / `variesAfter` (pure helpers) | `django.utils.cache.patch_vary_headers` | `django/utils/cache.py:276-298` |
| `deleteSecure` (pure helper) | the `secure = …` expression inside `delete_cookie` | `patch.diff` (post-patch text) |
| `valueEncode` (pure helper) | `SimpleCookie.value_encode`'s second component, i.e. `http.cookies._quote`: the payload as given when `_is_legal_key` matches it, otherwise the payload quoted with `_Translator` applied | stdlib `http/cookies.py:611-613` (`value_encode`), `:183-193` (`_quote`) |
| `quoteChar` / `octalEscape` / `octalDigit` (pure helpers) | the per-character action of `_Translator` inside `str.translate`: `'\\%03o' % n` for a byte outside `_UnescapedChars`, `\"` for `"`, `\\` for `\`, and NO entry — hence the character itself — for a codepoint at or above 256, which is what bounds the table's domain | stdlib `http/cookies.py:165-170` |
| `cookieUnescapedChar` (pure helper) | `http.cookies._UnescapedChars` (`_LegalChars + ' ()/<=>?@[]{}'`) | stdlib `http/cookies.py:163` |
| `cookieNameChar` (pure helper) | `http.cookies._LegalChars`, the alphabet BOTH `_is_legal_key` (the name a cookie may be filed under) and `_quote` (a payload that needs no quoting) match against | stdlib `http/cookies.py:162` |
| `Cookie` (structure) | the `http.cookies.Morsel` stored at `response.cookies[key]`, observed through every slot a `Morsel` has: the two components `OutputString` renders it with (`Morsel.key`, `Morsel.coded_value`), the payload it reads back (`Morsel.value`), and all nine attributes `Morsel._reserved` holds (`max-age`, `expires`, `path`, `domain`, `secure`, `httponly`, `samesite`, `comment`, `version`) — twelve components, which is a total enumeration and not a projection | stdlib `http/cookies.py` |
| `CookieJar` (`String → Option Cookie`) | `response.cookies` (the `SimpleCookie` dict): which names carry an entry, and what each entry holds | `django/http/response.py:169` |
| `Response` (structure) | the `HttpResponse` the routine acts on: its `cookies`, its `Vary` declaration, its other header fields, its status and its body | `django/http/response.py` |
| `keyAccepted` (precondition) | the keys `Morsel.set` files instead of raising `CookieError` | stdlib `http/cookies.py:162,172,347` |
| `samesiteValid` (precondition) | the `samesite` values `set_cookie` accepts instead of raising `ValueError` | `django/http/response.py:199-201` |
| `epochExpires` (pure const) | the literal `'Thu, 01 Jan 1970 00:00:00 GMT'` | `django/http/response.py:219` |

## Lean ↔ Python type bijection

`*` marks the components inside `conformance_check.py`'s projection (the cookie
decision of `delete_cookie`, which is what G-CONF fuzzes). That projection is now
the WHOLE entry: all twelve `Cookie` components, compared against a real
`http.cookies.SimpleCookie` the oracle writes into and reads every component
back off, over fuzzed `(key, path, domain, samesite)` AND a fuzzed pre-existing
entry at the same index (which is what makes the four guarded attribute writes
and the two parameterless attributes reachable). `valueEncode` gets a second leg
of its own over fuzzed payloads, since a deletion only ever encodes the empty
one. The unstarred rows are the response-level components — `varies`, the other
header fields, `status`, `body` — which are outside the cookie decision and are
pinned by the postcondition and exercised by the G-PBT rival battery instead:
`riv-write-extra-header`, `riv-reset-status-and-body`, and the `riv-session-*`
vary rivals. The starred components are covered TWICE, since the battery also
carries a rival per component: `riv-nonempty-payload`, `riv-mark-httponly`,
`riv-stamp-annotation`, `riv-stamp-protocol-version`, `riv-unrecorded-lifetime`,
`riv-lifetime-only-with-policy`, `riv-restamp-rendered-name` and
`riv-restamp-rendered-payload`. The written IDENTITY is a special case, called
out in its row below.

| Python | Lean | notes |
|---|---|---|
| `key: str` | `key : String` | cookie name |
| `path: str` (`'/'` default) | `path : String` | |
| `domain: str \| None` | `domain : Option String` | `None` ↔ `none` |
| `samesite: str \| None` | `samesite : Option String` | `None` ↔ `none`; the empty string `''` is falsy (attribute unset) |
| `secure: bool` | `secure : Bool` | |
| `max_age: int \| None` | `maxAge : Option Nat` | `set_cookie` writes `max-age` ONLY under `if max_age is not None:` (`response.py:186-187`), so `None` ↔ `none` is "no lifetime recorded" and emits no `Max-Age` directive, while a recorded lifetime `n` ↔ `some n` emits `Max-Age=n`. `delete_cookie` passes `0` ↔ `some 0`, which is NOT `none`: `Morsel.OutputString` skips an attribute whose value is `''` but renders the int `0` as `Max-Age=0` (measured) |
| the entry `key` that `self.cookies[key] = value` writes (`response.py:169`)* | the INDEX of `CookieJar` the postcondition demands the entry at (`jar key = some c`) | which cookie the write is FILED under. This is the container index, a separate component from the name the entry is rendered under (`Cookie.key`, next row); `∀ k, k ≠ key → jar k = resp.cookies k` pins every other index. Discriminated by G-CONF only in the weak sense that both sides file at the requested index by construction (`"index": key`), so the G-PBT rivals `riv-mistarget-folded-name` and `riv-mistarget-fixed-slot` remain what really exercise it |
| `response.cookies[key].key`* (`Morsel.key`) | `Cookie.key : String` | the name the entry is RENDERED under: `Morsel.OutputString`'s first act is `append("%s=%s" % (self.key, self.coded_value))` (`http/cookies.py:395`). `Morsel.set` re-stamps it on every write (`:344`), so after `self.cookies[key] = value` the index and the rendered name agree — a fact about the write, which is why `setCookie` stamps `key := key` and the postcondition pins `c.key = key`. Derived on BOTH sides in `conformance_check.py`: the oracle reads it off the real `Morsel`, the shadow computes it from `setCookie`. Also exercised by `riv-restamp-rendered-name` |
| `response.cookies[key].coded_value`* (`Morsel.coded_value`) | `Cookie.codedValue : String` | the payload the entry is RENDERED with, i.e. `SimpleCookie.value_encode(value)[1]`. `value_encode('')` is `('', '""')` (measured on CPython 3.10.20), so a deletion's entry reads back the empty payload and renders the two-character quoted empty payload — different bytes, hence a component of its own. Modeled by `valueEncode`; pinned by `c.codedValue = valueEncode ""`. Derived on both sides in `conformance_check.py` (oracle off the real `Morsel`, shadow through the `valueEncode` transliteration, plus a dedicated encoder leg over fuzzed payloads). Also exercised by `riv-restamp-rendered-payload` |
| `response.cookies[key]['max-age']`* | `Cookie.maxAge : Option Nat` | `''` (never written) ↔ `none`; the int `n` ↔ `some n` |
| `response.cookies[key]['expires']`* | `Cookie.expires : String` | `''` ↔ `""` |
| `response.cookies[key]['path']`* | `Cookie.path : String` | `''` ↔ `""` |
| `response.cookies[key]['domain']`* | `Cookie.domain : String` | `''` ↔ `""` |
| `response.cookies[key]['secure']`* (`True` / `''`) | `Cookie.secure : Bool` | `True`↔`true`, `''`↔`false` |
| `response.cookies[key]['samesite']`* (defaults to `''` when unset) | `Cookie.samesite : String` | `''` ↔ `""` |
| `response.cookies[key].value`* | `Cookie.value : String` | the payload a deletion writes (`''`). This is `Morsel.value`, the payload the entry READS BACK, and it is not the `Morsel.coded_value` the header renders — the two have separate rows and separate clauses because `value_encode` is not the identity |
| `response.cookies[key]['httponly']`* (`True` / `''`) | `Cookie.httpOnly : Bool` | `True`↔`true`, `''`↔`false`; written only under `if httponly:` (`response.py:197-198`), so a write can add but not clear it |
| `response.cookies[key]['comment']`* | `Cookie.comment : String` | `''` ↔ `""`. `set_cookie` has NO parameter for it and `Morsel.set` does not clear it, so a re-write leaves it standing; rendered by `OutputString` when non-empty |
| `response.cookies[key]['version']`* | `Cookie.version : String` | `''` ↔ `""`; same as `comment` |
| `response['Vary']` (absent ↔ no declaration) | `Response.varies : List String` | the `Vary` field split on the comma delimiter; `[]` ↔ header absent. `patch_vary_headers` appends each new field whose `.lower()` is not already present, preserves order, and collapses to `'*'` — `variesAfter` op for op |
| every other response header field | `Response.headers : String → String` | `""` for a field the response does not carry |
| `response.status_code` / `response.content` | `Response.status : Nat` / `Response.body : String` | carried so that what the routine did NOT touch is observable |
| — (nothing else) | — | the bijection is TOTAL over a `Morsel`: its three own slots (`_key`, `_value`, `_coded_value`) and the nine names `Morsel._reserved` holds (`http/cookies.py:266`) are twelve components, and `Cookie` has exactly twelve fields. There is no thirteenth slot for a deletion to stamp unobserved, so the enumeration has an external stopping point rather than ending where the gold call happens to stop writing |

### What the functions do (base_commit → post-patch)

`delete_cookie(key, path='/', domain=None)` calls `set_cookie(key, max_age=0,
path=path, domain=domain, secure=<prefix?>, expires=<epoch>)`. The post-patch
version adds a `samesite=None` parameter: `secure` is additionally forced when
`samesite and samesite.lower() == 'none'`, and `samesite` is forwarded to
`set_cookie`. `set_cookie` records `samesite` only when truthy (a non-empty
string), and rejects values outside `{lax, none, strict}` (case-insensitive) by
raising `ValueError` — modeled by the `samesiteValid` precondition. It writes
`value`/`max-age`/`expires`/`path` for this call and writes
`domain`/`secure`/`httponly`/`samesite` only under their guards
(`response.py:186-202`), which is why the model's `*After` helpers let a write ADD
but never CLEAR those four; `comment` and `version` have no parameter at all and
survive a re-write untouched (`BaseCookie.__set` reuses the existing `Morsel`).

The two call-site fixes (`messages` `_update_cookie`, sessions `middleware`) only
add `samesite=settings.SESSION_COOKIE_SAMESITE` to their `delete_cookie` calls;
in Lean they delegate to `implementation_deleteCookie` with the session policy
argument, so their behavior is `delete_cookie`'s contract instantiated. The
sessions branch is TWO statements, not one: the deletion is followed by
`patch_vary_headers(response, ('Cookie',))` (`middleware.py:46`), which the patch
leaves unchanged but which is part of the bound branch and is asserted by the same
F2P test (`test_session_delete_on_end` checks `response['Vary'] == 'Cookie'`
alongside the `Set-Cookie` header). It is modeled by `varyMarked`, and
`problem_spec_sessionDelete` requires it.

`keyAccepted` bounds the declared domain to the keys the container files:
`reservedCookieNames` is exactly `sorted(Morsel._reserved)` and
`cookieNameChar`'s alphabet is exactly `_LegalChars` (`string.ascii_letters +
string.digits` plus the 16 punctuation characters, 78 in total, set-equal both
ways), which is the alphabet `_is_legal_key` matches, with its `+` excluding the
empty key. `''`, `'path'`, `'Path'`, `'a b'`, `'é'` all raise `CookieError` and
file nothing; `sessionid`, `messages`, `c`, `__Secure-x`, `__Host-y` — every key
the tests and the fuzzers use — are admitted. Measured twice, and the second
measurement matters: on CPython 3.10.20 `Morsel._reserved` already has nine
entries, but the container's interpreter is CPython 3.6.13, whose table has only
EIGHT — `samesite` is absent. The ninth is put there by the repo:
`django/http/cookie.py` runs
`cookies.Morsel._reserved.setdefault('samesite', 'SameSite')`, and
`django/http/response.py:16` is `from django.http.cookie import SimpleCookie`, so
every `set_cookie` call goes through a table with `samesite` in it. Measured
in-container: eight before that import, nine after, and `_LegalChars` /
`_UnescapedChars` / `_quote` identical to 3.10.20 in every case checked below.
`conformance_check.py` therefore imports its container from
`django.http.cookie` rather than from `http.cookies`.

`valueEncode` is the same alphabet used for the other purpose. Measured on both
interpreters, with identical results: `_quote(s)` returns `s` unchanged exactly
when `_is_legal_key(s)`
matches, i.e. when `s` is non-empty and lies wholly in `_LegalChars`; otherwise
it returns `'"' + s.translate(_Translator) + '"'`, where `_Translator` maps `"`
to `\"`, `\` to `\\`, and every byte in `range(256)` outside `_UnescapedChars`
to `'\\%03o' % n` — and has NO entry for a codepoint at or above 256, which
`str.translate` therefore passes through. Spot-measured: `_quote('')` is `'""'`
(the case a deletion hits), `_quote('a b')` is `'"a b"'` (space unescaped),
`_quote(',')` is `'"\\054"'`, `_quote('é')` is `'"\\351"'` (U+00E9 is 233, still
a byte), `_quote('中')` is `'"中"'`. G-CONF's second leg re-measures all of this
against the real `value_encode` over fuzzed payloads on every run.

### Callee provenance + flag deps
- `setCookie` is the **A-reference** deep model of `set_cookie`: the index it
  writes (`self.cookies[key] = value`, `response.py:169`), all twelve components
  of the entry it leaves there, and the frame over the other entries and the rest
  of the response (impl is all-R so G-AX skips — see refinement.md, including the
  correction notes on the three earlier revisions this model was refuted at).
- `varyMarked` / `variesAfter` is the **A-reference** deep model of
  `patch_vary_headers` (`django/utils/cache.py:276-298`), op for op against its
  four steps (take the existing field list, append the new fields whose lowercase
  form is absent, keep the order, collapse to `*`). No axiom is consumed; it is
  outside `conformance_check.py`'s projection and is exercised by the G-PBT
  `riv-session-*` rivals.
- `valueEncode` (with `quoteChar` / `octalEscape` / `octalDigit` /
  `cookieUnescapedChar`) is the deep model of `SimpleCookie.value_encode`'s coded
  component, i.e. `http.cookies._quote`. It is reached from `setCookie`, not from
  the impl region directly, and it consumes no axiom; G-CONF's second leg diffs
  it against the real `value_encode` over fuzzed payloads.
- No consumed `_prop` axiom: the changed decision (`deleteSecure` + samesite
  forwarding) is modeled DEEPLY (SPEC_GUIDE §3 forbids axiomatizing it).
- No flag-dependent callee.

### G-CONF fuzz seed
Pinned seed: **13195** (also in meta.json `verifier_pins.conf_seed`). Two legs
share one disagreement count: the deletion itself (150,000 draws over
`(prior entry, key, path, domain, samesite)`, of which ~132,000 clear the
`keyAccepted` / `samesiteValid` preconditions) and the payload encoder (60,000
fuzzed payloads), for ~192,000 checked inputs — above the 1e5 the gate requires.
The oracle asserts nothing about the resulting entry: it writes into a real
`http.cookies.SimpleCookie` and reads all twelve components back off the
`Morsel`, so a component the model gets wrong is a disagreement rather than an
agreement by construction. An earlier revision hardcoded `"name": key` on BOTH
sides, which is why two impls re-stamping the rendered components went
undetected here.
