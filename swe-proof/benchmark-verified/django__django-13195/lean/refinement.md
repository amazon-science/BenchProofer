# refinement.md — django__django-13195

Operation-by-operation correspondence between the Solution.lean impl regions and
`patch.diff` (the POST-PATCH cookie-deletion code). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

Line numbers are at `base_commit 156a2138db20abc89933121e4ff2ee2ce56a173a`;
code the patch ADDS has no base-commit line and is cited as `patch.diff`.

## What the model observes

The observed value is a whole `Response`, not one cookie in isolation: its cookie
container (`cookies : CookieJar = String → Option Cookie`), the request fields its
content is declared to depend on (`varies : List String`, the model of the `Vary`
header), the value of every other header field (`headers`), its `status` and its
`body`. One container entry (`Cookie`) carries every slot a
`http.cookies.Morsel` has, and the enumeration is closed rather than open:

- the two components the entry is RENDERED with, `key` and `codedValue`, which
  are `Morsel._key` and `Morsel._coded_value`. `Morsel.OutputString`'s FIRST act
  is `append("%s=%s" % (self.key, self.coded_value))` (`http/cookies.py:395`), so
  these are the two components that always reach the wire, ahead of every
  attribute.
- the payload the entry reads back, `value` = `Morsel._value`.
- all nine attributes `Morsel._reserved` holds — `max-age`, `expires`, `path`,
  `domain`, `secure`, `httponly`, `samesite`, `comment`, `version` (measured:
  `sorted(Morsel._reserved)` is exactly those nine) — because `OutputString`
  renders each of them too, whenever its value is non-empty.

Three plus nine is twelve, and `Cookie` has twelve fields. A `Morsel` has no
thirteenth slot, so the carrier is bounded by the callee's own structure rather
than by the set of components the gold call happens to write; a deletion has
nowhere left to stamp something unobserved. Three encodings are load-bearing:

- `maxAge : Option Nat`. `set_cookie` writes `max-age` only under
  `if max_age is not None:` (response.py:186-187), so "no lifetime recorded"
  (`none` — the value `defaultCookie.maxAge` carries, emitting NO `Max-Age`
  directive) and "the lifetime zero recorded" (`some 0` — emitting `Max-Age=0`,
  since `OutputString` skips an attribute whose value is `''` but renders the int
  `0`) are DIFFERENT observable outputs. A deletion must produce the second.
- `expires`, `path`, `domain`, `samesite`, `comment`, `version` use `""` for
  "attribute unset" (the `''` a `Morsel` reads back for an attribute never
  written), and `secure` / `httpOnly` are flags that stay off unless set.
- `codedValue` is `value` ENCODED, not `value`. `SimpleCookie.value_encode(v)` is
  `(str(v), _quote(str(v)))`, and `_quote('')` is `'""'` — measured on CPython
  3.10.20 — so for the payload a deletion writes the two components are `''` and
  the two-character `'""'`, DIFFERENT strings. Pinning the payload therefore says
  nothing about what goes on the wire; the encoding is modeled by `valueEncode`
  and pinned separately.

WHICH entry was written is carried by TWO components, and they are not the same
component. The container INDEX is one: `deletesCookie` demands the entry at
`jar key` and pins every other index to what it held. The entry's own rendered
name (`Cookie.key`) is the other: `Morsel.set` re-stamps `_key` on every write
(`http/cookies.py:344`), so `self.cookies[key] = value` leaves the index and the
rendered name in agreement — a fact about the write, which is why `setCookie`
stamps `key := key` and the postcondition pins `c.key = key`. An entry filed at
the right index and rendered under a different spelling puts a different
`Set-Cookie` line on the wire while every attribute read-back agrees, so the
index alone does not determine it.

## Precondition ↔ callee domain

`keyAccepted key` (non-empty, `key.toLower ∉ reservedCookieNames`, every
character in `cookieNameChar`) is the domain the container will store a cookie
under: `set_cookie`'s first act is `self.cookies[key] = value` (response.py:169),
which reaches `Morsel.set`, and that raises `CookieError` — filing NOTHING — for a
reserved attribute name or an out-of-alphabet key. Measured on CPython 3.10.20
(`http.cookies`, the stdlib module Django imports): `reservedCookieNames` is
exactly `Morsel._reserved`'s nine keys, and `cookieNameChar`'s alphabet is exactly
`_LegalChars` (`string.ascii_letters + string.digits` plus the same 16 punctuation
characters, 78 in total, set-equal both ways), which is the alphabet
`_is_legal_key` matches, with its `+` excluding the empty key. `''`, `'path'`,
`'Path'`, `'a b'`, `'é'` all raise; `sessionid`, `messages`, `c`, `__Secure-x`,
`__Host-y` — every key the F2P/P2P tests and `conformance_check.py` exercise — are
admitted. Re-measured in the instance container, whose interpreter is CPython
3.6.13: `_LegalChars`, `_UnescapedChars` and `_quote` are identical there, but
`Morsel._reserved` has only EIGHT keys — no `samesite`. The ninth is the repo's:
`django/http/cookie.py` runs
`cookies.Morsel._reserved.setdefault('samesite', 'SameSite')`, and
`django/http/response.py:16` imports `SimpleCookie` from that module, so the
container every `set_cookie` call writes into does have nine. `reservedCookieNames`
and the carrier's ninth attribute are both correct, but they are correct BECAUSE
of a repo-level patch to the stdlib table, not because the stdlib carries it — so
`conformance_check.py` imports `django.http.cookie` rather than `http.cookies`,
and asserts the nine before it fuzzes anything. `samesiteValid samesite` is the
other hypothesis: `set_cookie` raises
`ValueError` on a truthy `samesite` outside `{lax, none, strict}`
(response.py:199-201).

## `implementation_deleteCookie` ↔ `HttpResponseBase.delete_cookie` (post-patch)

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let secure := deleteSecure key samesite` | `secure = (key.startswith(('__Secure-', '__Host-')) or (samesite and samesite.lower() == 'none'))` (patch.diff) | R |
| 2 | `return setCookie resp key "" (some 0) epochExpires path domain secure false samesite` | `self.set_cookie(key, max_age=0, path=path, domain=domain, secure=secure, expires='Thu, 01 Jan 1970 00:00:00 GMT', samesite=samesite)` (patch.diff; callee at response.py:158-202) | A-reference |

- Op 1 is the soundness-critical fix: `deleteSecure` adds the `samesite=='none'`
  disjunct that the pre-patch code lacked. Modeled DEEPLY as a boolean over the
  inputs — string-prefix tests + case-insensitive `none` check. **R** (the
  `str.startswith(tuple)` / `str.lower()` ops refine to `String.startsWith` /
  `String.toLower`).
- Op 2 is the **A-reference** deep model of `set_cookie` (response.py:158-202).
  What it models, component by component:
  - the entry it selects: `self.cookies[key] = value` (response.py:169) writes the
    container index `key`, so `setCookie` writes `cookies key` and the
    postcondition demands the written entry AT that index (`jar key = some c`).
  - the two components the entry is RENDERED with. That same statement reaches
    `BaseCookie.__setitem__`, which computes
    `rval, cval = self.value_encode(value)` and calls
    `Morsel.set(key, rval, cval)` (`http/cookies.py:344`), and `set` assigns all
    three of `_key`, `_value`, `_coded_value` unconditionally. So a write STAMPS
    the rendered name and the rendered payload rather than merging them:
    `setCookie` writes `key := key` and `codedValue := valueEncode value`, and the
    postcondition pins both (`c.key = key`, `c.codedValue = valueEncode ""`).
    `valueEncode` is the model of `SimpleCookie.value_encode`'s coded component
    (`:611-613`), i.e. `_quote` (`:183-193`): the payload unchanged when
    `_is_legal_key` matches it, otherwise quoted with `_Translator` applied —
    `\"` for `"`, `\\` for `\`, `'\\%03o' % n` for a byte outside
    `_UnescapedChars`, and nothing at all for a codepoint at or above 256, which
    `str.translate` passes through. Measured on CPython 3.10.20, including the
    case this routine actually hits: `_quote('')` is `'""'`.
  - the attributes the carrier holds. The four `set_cookie` writes
    unconditionally for this call — `value`, `max-age` (guarded by
    `max_age is not None`, 186-187, and `some 0` is supplied), `expires` (170/183,
    supplied as the epoch string, which is also why the `if not expires`
    recomputation at 189-190 does not fire), `path` (191-192; a Lean `String` is
    never `None`, so that guard is vacuous here) — are written by `setCookie`; the
    four it writes only under a guard are modeled by the `*After` helpers, which
    is what makes a write unable to CLEAR what the entry already carried:
    `domainAfter` (193-194, `domain is not None`), `secureAfter` (195-196,
    `if secure`), `httpOnlyAfter` (197-198, `if httponly`), `samesiteAfter`
    (199-202, `if samesite`, i.e. non-empty). `comment` and `version` are the two
    reserved attributes `set_cookie` has NO parameter for:
    `BaseCookie.__set` reuses the existing morsel (`M = self.get(key, Morsel())`)
    and `Morsel.set` touches only `key`/`value`/`coded_value`, so a re-write
    leaves them standing — `setCookie` carries them over unchanged and the
    postcondition pins them to what the entry already had, so a deletion cannot
    annotate the entry it deletes.
  - every OTHER entry, and everything else about the response: `setCookie`
    rebuilds `{ resp with cookies := … }`, so a cookie write is not a `Vary`,
    header, status or body write.
  - nothing is left out. The components above are `_key`, `_value`,
    `_coded_value` and the nine names in `Morsel._reserved` (`:266`) — twelve, and
    a `Morsel` has no thirteenth slot, so this is the callee's whole observable
    effect on the entry rather than a chosen projection of it.
  No `_prop` axiom is consumed — the proof reasons over `setCookie`'s definition
  directly — so **G-AX skips**, and the R legs are checked by G-CONF, whose
  projection is now the whole entry: its oracle writes into a real
  `http.cookies.SimpleCookie` and reads all twelve components back off the
  `Morsel`, over fuzzed arguments AND a fuzzed pre-existing entry at the same
  index (which is what makes the four guarded writes and the two parameterless
  attributes reachable), with a second leg diffing `valueEncode` against the real
  `value_encode` over fuzzed payloads.
- **Correction (spec repair, three rounds; claims RETRACTED, not restated).**
  Three earlier revisions of this bundle were refuted by adversarial audits, and
  what this file argued for them is withdrawn:
  1. An early revision modeled `set_cookie`'s first parameter as `_key` and
     DISCARDED it, and this section claimed the deep model's equivalence to the
     real callee was "asserted structurally". False as written: the key selects
     the container entry the write lands in, so it is an observable output. Two
     impls writing the correct attributes into a DIFFERENT entry (a case-folded
     name; a fixed name) satisfied every clause and their faithful patches did not
     resolve. The index is now written by the model and pinned by the
     postcondition (`jar key = some c`, plus
     `∀ k, k ≠ key → jar k = resp.cookies k`). That revision's note also claimed
     "G-CONF's oracle/shadow both observe it"; that claim was withdrawn as well,
     because `conformance_check.py` then hardcoded `"name": key` on BOTH sides, so
     the two agreed on the identity by construction and the fuzz discriminated no
     identity defect at all. The hardcoding is gone (see 3 below), but the
     WITHDRAWAL stands as stated: what discriminates the container index is the
     postcondition plus the G-PBT rivals `riv-mistarget-folded-name` and
     `riv-mistarget-fixed-slot`, since both sides still file at the requested
     index by construction. What G-CONF does now discriminate is the entry's
     RENDERED name, which is a different component.
  2. The next revision carried an 8-field `Cookie` with `maxAge : Nat`, and this
     section claimed `setCookie` modeled `set_cookie` "restricted to the touched
     attributes". That restriction is to the attributes the GOLD implementation
     happens to touch, which is not a bound on what a rival may touch, and a
     frame over a projection only frames the projection. Three refutations
     followed, all with faithful non-resolving patches: `maxAge = 0` was
     DEGENERATE (`defaultCookie.maxAge` was the same `Nat`, so "never supplied"
     and "stamped zero" were one value, and the emitted header silently lost
     `Max-Age=0`); a deletion could stamp `comment` / `version`, neither of which
     the carrier held; and the sessions branch could drop `patch_vary_headers`,
     which no modeled component observed. The carrier is now `Option Nat` for the
     lifetime and holds all nine reserved attributes, the observed value is the
     whole `Response`, and the sessions leg pins the vary marking (op 5 below).
     Those three are refuted against the current file — the audit of
     2026-08-15T23:53Z re-encoded them as `atk_7_maxage_default`,
     `atk_8_comment_stamp` and `atk_6_no_vary` and each exits 1.
  3. The revision before this one carried a 10-field `Cookie` (payload + the nine
     reserved attributes) and this file argued, under the heading "Boundary of the
     carrier", that the entry was observed through "the payload `value`, the nine
     reserved attributes, and the index". That was an honest boundary but it was
     still a projection, and it left the two components `OutputString` renders
     FIRST — `"%s=%s" % (self.key, self.coded_value)` — free. Two attacks in the
     audit of 2026-08-15T23:53Z kept the container index, every modeled attribute
     and the whole response frame correct, VERIFIED with clean axioms, and their
     faithful patches did not resolve (F2P 3/5, P2P 382/382):
     `atk_2_morsel_key` re-stamped the entry's own name
     (`morsel.set(key.upper(), morsel.value, morsel.coded_value)` → header
     `SESSIONID=""` where the tests pin `sessionid=""`), and `atk_3_coded_value`
     re-stamped the rendered payload (`morsel.set(morsel.key, morsel.value,
     '"deleted"')` → `sessionid="deleted"`; `value_encode('')` is `('', '""')`, so
     the gold rendered payload is the quoted empty payload, which
     `Cookie.value = ""` does not determine). That revision's note also recorded
     the two components as a KNOWN GAP and said closing it needed a spec change,
     not a prose change; this is that change, so the note is gone rather than
     restated. The carrier now holds `key` and `codedValue`, `setCookie` stamps
     both, `deletesCookie` pins both (`c.key = key`,
     `c.codedValue = valueEncode ""`), `valueEncode` models
     `SimpleCookie.value_encode`'s coded component, and
     `conformance_check.py` DERIVES every component on both sides instead of
     hardcoding the identity. Both attacks are refuted against the current file in
     their expressible form: the battery carries them as
     `riv-restamp-rendered-name` and `riv-restamp-rendered-payload`, each with a
     witness that elaborates against the rival and fails against gold. The
     enumeration now has an external stopping point — twelve components against a
     `Morsel`'s twelve slots — which is what the previous two rounds lacked.

## `implementation_messagesDelete` ↔ `_update_cookie` else-branch (post-patch)

| # | Lean impl op | patch.diff Python op | tag |
|---|---|---|---|
| 3 | `return implementation_deleteCookie resp cookieName "/" domain sessionSamesite` | `response.delete_cookie(self.cookie_name, domain=settings.SESSION_COOKIE_DOMAIN, samesite=settings.SESSION_COOKIE_SAMESITE)` (messages/storage/cookie.py:94-95 + patch.diff) | R |

- The patch adds `samesite=settings.SESSION_COOKIE_SAMESITE` to the existing
  `delete_cookie` call (path defaults to `'/'`). Refines to calling
  `implementation_deleteCookie` with the session policy. **R** (the settings
  constant ↔ the `sessionSamesite` argument; bijection in mapping.md). The branch
  is that one statement, so `problem_spec_messagesDelete` is
  `problem_spec_deleteCookie` at `(cookieName, "/", domain, sessionSamesite)`,
  frame included.

## `implementation_sessionDelete` ↔ `process_response` deletion branch (post-patch)

| # | Lean impl op | patch.diff Python op | tag |
|---|---|---|---|
| 4 | `let deleted := implementation_deleteCookie resp name sessionPath domain sessionSamesite` | `response.delete_cookie(settings.SESSION_COOKIE_NAME, path=settings.SESSION_COOKIE_PATH, domain=settings.SESSION_COOKIE_DOMAIN, samesite=settings.SESSION_COOKIE_SAMESITE)` (sessions/middleware.py:41-45 + patch.diff) | R |
| 5 | `return varyMarked deleted ["Cookie"]` | `patch_vary_headers(response, ('Cookie',))` (sessions/middleware.py:46) | A-reference |

- Op 4: the patch adds `samesite=settings.SESSION_COOKIE_SAMESITE` to the
  existing `delete_cookie` call. Refines to `implementation_deleteCookie` with the
  session policy and the configured path. **R**.
- Op 5 is the branch's SECOND statement, and it is independently observable:
  `test_session_delete_on_end` asserts `response['Vary'] == 'Cookie'` in the same
  test that asserts the `Set-Cookie` header, so an impl that drops it fails F2P.
  The patch leaves it unchanged — the map carries it verbatim — but it is part of
  the branch mapping.md binds, so it is modeled rather than dropped:
  `varyMarked resp ["Cookie"] = { resp with varies := variesAfter resp.varies ["Cookie"] }`
  is the **A-reference** deep model of `django.utils.cache.patch_vary_headers`
  (utils/cache.py:276-298), op for op — take the existing field list (`[]` when the
  header is absent), append each new field whose `.lower()` is not among the
  existing fields' `.lower()`s, keep the order, and collapse to `["*"]` if `"*"` is
  present. `variesAfter` is total and consumes no axiom, so **G-AX skips** for it
  too. Its correspondence is by inspection against those four steps;
  `conformance_check.py`'s oracle/shadow cover the cookie decision (ops 1-2), not
  this op, and the G-PBT `riv-session-*` rivals are what exercise it.

## Summary
- **Every step is R or A-reference — no consumed axiom.** The changed decision
  (`deleteSecure` + samesite forwarding) is modeled deeply; SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op. The `axioms` region declares no
  `_prop`; **G-AX skips**. The R legs are mechanically refuted by G-CONF, whose
  projection over the written entry is now that entry in full.
- Directive 5 (frame): the postcondition leaves no component of the MODELED value
  free, and it states the frame by REBUILDING the response rather than by listing
  components that must not move, so a modeled component is framed whether or not a
  clause names it. There is no component of a `Morsel` outside the model for a
  frame to fail to reach.
  - `deletesCookie` pins the written entry at the index `key`
    (`∃ c, jar key = some c`) and all twelve of its fields: `key = key` (the name
    the entry is RENDERED under, which the index alone does not determine),
    `value = ""`, `codedValue = valueEncode ""` (the quoted empty payload, which
    the read-back payload alone does not determine),
    `maxAge = some 0` (an entry STATING a lifetime, not `none`),
    `expires = epochExpires`, `path = path`, `domain = domainAfter …`,
    `samesite = samesiteAfter …`,
    `secure = secureAfter … (deleteSecure key samesite)`,
    `httpOnly = httpOnlyAfter … false`, and `comment` / `version` equal to what
    the entry already held.
  - It pins every OTHER entry too: `∀ k, k ≠ key → jar k = resp.cookies k`.
  - `problem_spec_deleteCookie` adds
    `result = { resp with cookies := result.cookies }`, which frames `varies`,
    every other header field, `status` and `body` in one clause.
    `problem_spec_messagesDelete` inherits it unchanged.
  - `problem_spec_sessionDelete` REQUIRES the second effect instead of framing it:
    `result = { resp with cookies := result.cookies, varies := variesAfter resp.varies ["Cookie"] }`,
    so dropping the vary marking is rejected while the headers, status and body
    stay framed.
- The three call sites share one independently-observable fixed behavior
  (samesite preserved on deletion), so a single `Solution_prepatch.lean` (the
  pre-patch `delete_cookie` that drops samesite) discriminates all three.
