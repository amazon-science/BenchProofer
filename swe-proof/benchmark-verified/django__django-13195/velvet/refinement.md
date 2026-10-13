# refinement.md — django__django-13195

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `deleteCookie`, `clearMessageCookie`, `clearSessionCookie` `do` blocks and
the deep `mkCookie` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). Every step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A-reference leg and this narrative are audited by **G-AX** / **G-EQ**.
`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The core change — `HttpResponseBase.delete_cookie` (`response.py:213`)

Gold hunk:
```
- def delete_cookie(self, key, path='/', domain=None):
-     secure = key.startswith(('__Secure-', '__Host-'))
+ def delete_cookie(self, key, path='/', domain=None, samesite=None):
+     secure = (
+         key.startswith(('__Secure-', '__Host-')) or
+         (samesite and samesite.lower() == 'none')
+     )
      self.set_cookie(
          key, max_age=0, path=path, domain=domain, secure=secure,
-         expires='Thu, 01 Jan 1970 00:00:00 GMT',
+         expires='Thu, 01 Jan 1970 00:00:00 GMT', samesite=samesite,
      )
```

| # | Solution.lean impl op (`deleteCookie`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `key path : String`, `domain samesite : Option String` | the new signature `(self, key, path='/', domain=None, samesite=None)` | R | `str ↔ String`, `str|None ↔ Option String` (mapping.md §2). The new `samesite` param IS the change. |
| A2 | `secureForClear key samesite = hasSecurePrefix key || crossSiteUnrestricted samesite` | `secure = key.startswith((...)) or (samesite and samesite.lower()=='none')` | I | concrete boolean computation, transliterated by G-CONF. `hasSecurePrefix ↔ key.startswith`, `crossSiteUnrestricted ↔ samesite and samesite.lower()=='none'`. This is the changed `secure` derivation. |
| A3 | `mkCookie key secure samesite path domain` | `self.set_cookie(key, max_age=0, path=path, domain=domain, secure=secure, expires=..., samesite=samesite)` | A-reference + I | the unchanged attribute-setter is modeled deeply by `mkCookie` on its TWELVE touched fields (A-reference, G-AX-validated == real `set_cookie`); passing `samesite=samesite` (the change) and `path`/`domain`/`secure` is the **I** field-wise wiring G-CONF transliterates. |
| A8 | `ensures c.value = ""`, `c.maxAge = clearedMaxAge`, `c.expires = some epochExpiry`, `c.httpOnly = false` | the `max_age=0` / `expires='Thu, 01 Jan 1970 00:00:00 GMT'` arguments of that same call, the empty `value` default, and the absence of an `httponly` argument | I + directive frame | what makes the emitted entry a CLEARING directive rather than an ordinary cookie assignment carrying the same flags and scope. Both are `Option`-valued in the carrier so an OMITTED attribute is a distinct observable from a stated one. Pinned exactly, for the same directive-5 reason as A6/A7: otherwise a verifying routine could emit every flag correctly while granting the cookie a lifetime that leaves it standing, which is not a clearing of anything. Unchanged by the patch on this routine. |
| A9 | `ensures c.codedValue = quotedEmptyBody`, `c.comment = none`, `c.version = none` | the same call's filing step, `self.cookies[key] = value` (`response.py:169`): the cookie container's item assignment ENCODES the body before storing it, so an empty body is transmitted as the quoted empty string; and neither a note nor a version is ever argued | A-reference + directive frame | what the response actually TRANSMITS for the cleared cookie, as distinct from the attributes it records. The emitted header is the name, then the body's encoded form, then the set attributes, so the transmitted form is an observable of the same filed entry as the flags; the two session checks of this behavior compare that header verbatim. Pinned for the same directive-frame reason as A6/A7/A8: otherwise a routine could agree with the modelled attribute-setter on every ATTRIBUTE while transmitting something else for the body, or silently adding an attribute of its own, and still verify. Unchanged by the patch on this routine. |
| A10 | `ensures c.transmittedName = key` (via `mkCookie`) | the same call's filing step, `self.cookies[key] = value` (`response.py:169`): handing a body over for a cookie is what fixes the name the resulting entry ANNOUNCES, so the entry names that cookie on the wire | A-reference + directive frame | the name the response actually PUTS ON THE WIRE for the cleared cookie, which is a different observable from the cookie the entry is filed under. The emitted header's name half is read off the entry itself, so an entry can be filed against exactly the right cookie and still announce another name, or none — and a recipient told to drop another name does not drop this cookie. Pinned for the same directive-frame reason as A7/A8/A9, and separately from A7 because A7 constrains only WHERE the entry sits: the two session checks compare the emitted header verbatim and read the announced name directly. Unchanged by the patch on this routine. |
| A4 | `ensures c.samesite = samesite` | the new `samesite=samesite` kwarg reaching the morsel | I | the carried-through policy; `Option String ↔ str|None` (mapping.md §2). |
| A5 | `ensures c.secure = secureForClear key samesite` | the new `secure` value reaching the morsel | I | the secure flag now also true for the unrestricted policy. |
| A6 | `ensures c.path = path`, `ensures c.domain = domain` | `path=path`, `domain=domain` (unchanged) | I + directive-5 frame | the unchanged-flow fields are pinned exactly, so no verifying impl may silently drop them (the `mut`-frame analogue, SPEC_GUIDE §0.5). |
| A7 | `ensures c.name = key` | `self.set_cookie(key, ...)` — the directive is filed under the requested key (`self.cookies[key] = value`, `response.py:169`) | I + addressee frame | the ADDRESSEE of the clearing directive: it targets the cookie the caller asked to clear and no other. Unchanged by the patch on this routine, and pinned exactly for the same directive-5 reason as A6 — otherwise a verifying impl could clear an arbitrary cookie while satisfying every attribute clause. `str ↔ String` (mapping.md §2). |

`require acceptedPolicy samesite` (R) mirrors `set_cookie`'s upstream guard that
a present `samesite` is one of `lax`/`none`/`strict` (else `ValueError`); we model
behavior on the accepted domain (mapping.md §1, §3.1).

`require recordableKey key` and `require domainStated domain` (both R) declare the
rest of that same domain, on the same principle and for the same callee. The
clearing call reaches the container's item assignment at `response.py:169`, which
refuses a name that is empty, carries a character outside the cookie-name
alphabet, or (case-insensitively) is one of the names kept for a directive's OWN
attributes: it records nothing and fails outright, so on those names there is no
filed directive for any `ensures` to describe. `domainStated` excludes the empty
scope, where `if domain is not None` stores the morsel's own unset sentinel and an
empty scope becomes indistinguishable from an absent one on readback. Both bounds
are measured rather than asserted: G-AX confirms the boundary in both directions
(every admitted name is recorded; every excluded name raises), and both fuzzers
now draw from the whole recordable-name alphabet rather than a safe subset. The
two clear sites carry the same two requires on their own name/domain binders,
which is what discharges `deleteCookie`'s at their call. Nothing the behavior's
own checks exercise is excluded — they clear `sessionid`, `messages`, `c`,
`__Secure-c` and `__Host-c`, all recordable, with absent or dotted domains.

**Discriminating content:** (i) the policy is carried through —
`c.samesite = samesite` (A4); (ii) the secure flag is also set when the policy is
unrestricted — `crossSiteUnrestricted` disjunct of A2/A5. `Solution_prepatch.lean`
reproduces the pre-change derivation (`secure = hasSecurePrefix key`, policy
dropped) and fails **both** A4 and A5; `Solution_prepatch_securenone.lean`
forwards the policy but drops the `none`-secure disjunct and fails **only** A5
(isolating the secure-on-`none` behavior, F2P `test_delete_cookie_secure_samesite_none`).

## B. The message-storage clear site — `_update_cookie` (`messages/storage/cookie.py:95`)

Gold hunk:
```
- response.delete_cookie(self.cookie_name, domain=settings.SESSION_COOKIE_DOMAIN)
+ response.delete_cookie(
+     self.cookie_name,
+     domain=settings.SESSION_COOKIE_DOMAIN,
+     samesite=settings.SESSION_COOKIE_SAMESITE,
+ )
```

| # | Solution.lean impl op (`clearMessageCookie`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `deleteCookie cookieName "/" domain configuredPolicy` | the patched `response.delete_cookie(self.cookie_name, domain=..., samesite=settings.SESSION_COOKIE_SAMESITE)` | I (callee-under-spec) | the changed callee is `deleteCookie` itself; `prove_correct` applies `deleteCookie_correct` directly (SPEC_GUIDE §3). `path` defaults to `'/'` (Python default), `configuredPolicy ↔ settings.SESSION_COOKIE_SAMESITE` (mapping.md §1). |
| B2 | `ensures c.samesite = configuredPolicy`, `c.domain = domain`, `c.path = "/"` | the morsel now carries the configured policy | I | the observable effect of forwarding the policy through the clear site (F2P `test_cookie_setings`). |
| B3 | `ensures c.name = cookieName` | `response.delete_cookie(self.cookie_name, ...)` — the first positional argument | I | the site clears its OWN cookie. `self.cookie_name ↔ cookieName` (mapping.md §1); the test reads the cleared cookie back under that name, so the addressee is part of what the site must get right. |
| B4 | `ensures c.secure = secureForClear cookieName configuredPolicy` | the `secure` value the patched callee derives from THIS site's name and forwarded policy, reaching the morsel | I (via the callee's contract) | the flag the cleared cookie carries at this site is a function of the name it clears and the policy it forwards — the composed image of A5 under B1. Pinned on the caller so a site that emits its own flag cannot verify. |

`Solution_prepatch_messages.lean` passes `none` for the policy (the pre-change
call that omitted `samesite=`) and fails `c.samesite = configuredPolicy`.

## C. The session middleware clear site — `process_response` (`sessions/middleware.py:41`)

Gold hunk:
```
  response.delete_cookie(
      settings.SESSION_COOKIE_NAME,
      path=settings.SESSION_COOKIE_PATH,
      domain=settings.SESSION_COOKIE_DOMAIN,
+     samesite=settings.SESSION_COOKIE_SAMESITE,
  )
```

| # | Solution.lean impl op (`clearSessionCookie`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `deleteCookie sessionName path domain configuredPolicy` | the patched `response.delete_cookie(settings.SESSION_COOKIE_NAME, path=..., domain=..., samesite=settings.SESSION_COOKIE_SAMESITE)` | I (callee-under-spec) | same as B1; `path`/`domain` flow from the session settings, `configuredPolicy ↔ settings.SESSION_COOKIE_SAMESITE`. |
| C2 | `ensures c.samesite = configuredPolicy`, `c.domain = domain`, `c.path = path` | the morsel now carries the configured policy | I | F2P `test_session_delete_on_end` / `..._with_custom_domain_and_path`. |
| C3 | `ensures c.name = sessionName` | `response.delete_cookie(settings.SESSION_COOKIE_NAME, ...)` — the first positional argument | I | the middleware clears the SESSION's own cookie. The two session F2P tests compare `str(response.cookies[settings.SESSION_COOKIE_NAME])` verbatim, so the addressee is directly observed. |
| C4 | `ensures c.secure = secureForClear sessionName configuredPolicy` | the `secure` value the patched callee derives from the session cookie name and the forwarded policy, reaching the morsel | I (via the callee's contract) | as B4, on this site's own binders. The verbatim header comparison in both session tests would not match a directive carrying a Secure attribute the real one does not. |

`Solution_prepatch_sessions.lean` passes `none` and fails
`c.samesite = configuredPolicy`.

**C5 — the clear branch's OTHER statement, carried by the map (frame).** The
branch this method models has a second statement beside the clearing call: it also
marks the response as varying by the request's cookies, so the cleared
`Set-Cookie` is not served from a cache. The gold hunk leaves that statement
untouched — it appears as context, not as a changed line — so under this map it is
carried VERBATIM into the refined patch rather than re-derived from the spec, on
the same frame convention as every other unchanged surrounding statement. It is
therefore deliberately outside `Filed`, which carries clearing directives and not
response headers: widening the carrier to headers would put the modelled
attribute-setter's own projection (what G-AX validates) out of scope, for a
statement the patch does not change. A refinement that DROPPED it would not be a
faithful image of this map, and would in any case fail one of the behaviour's own
checks, which reads that marking back off the response.

## D. No kind-3 (inexpressible-changed-op) steps

Every changed op is expressed concretely: the `secure` derivation (A2, an **I**
boolean computation), the `samesite`/`path`/`domain` wiring into the attribute
setter (A3, **I** field-wise), and the two call-site forwardings (B1/C1,
callee-under-spec **I**). The only deep model, `mkCookie`, stands for the
**unchanged** `set_cookie` callee and is an **A-reference** (G-AX-validated),
not a consumed axiom. There are **no consumed axioms** in this bundle.

## E. verify(Solution) ⇒ resolved

The three routines are contracted over what a response has ON FILE, not over a
returned value: `Filed` is the list of clearing directives a response carries (one
entry per cookie it is telling the browser to drop), and `fileDirective` is the
single act of filing one — replacing that cookie's entry where it already sits, by
`mergeDirective`, and otherwise adding one, leaving every OTHER cookie's entry
alone. That is why each obligation is ONE equation between what is on file
afterwards and `fileDirective filed (mkCookie …)`: it pins the filed entry's
thirteen observables, the arity (exactly one directive filed, so no spurious
second one leaves sticky attributes behind) and the frame (no other cookie
disturbed) in a single claim, rather than as a list of clauses about one entry
that would say nothing about the rest of the file.

`deleteCookie` verifies only if its output records the policy (A4), the secure
flag including the unrestricted-policy disjunct (A5), the unchanged path/domain
frame (A6), the addressee — the directive targets the cookie it was asked to
clear (A7) — the name that directive ANNOUNCES on the wire, which must be that
same cookie (A10) — and the clearing character of the directive itself: the emptied
body, the spent lifetime and the announced past expiry that make the browser drop
the cookie (A8). The two caller methods verify only if the configured policy reaches
the cleared cookie (B2/C2), each site clears its OWN cookie (B3/C3), and the flag
that site emits is the one its name and policy call for (B4/C4), applying
`deleteCookie_correct`.

A10 was added by the MOST RECENT SPEC-REPAIR pass.

TOO WEAK, in the ONE PART OF THE EMITTED HEADER the carrier still did not observe.
The audit produced a verify-but-not-resolve counterexample that got every
ATTRIBUTE of the filed entry right, got the transmitted body form right, AND filed
the entry against exactly the cookie it was asked to clear — `response.cookies`
had the right single key — and differed only in the name that entry ANNOUNCES.
It assembled the entry directly instead of routing it through the modelled
hand-over, so the entry never acquired a name of its own and the emitted header
named nothing where the real one names the cookie. Measured completed=True
resolved=FALSE: the two session checks that compare that header verbatim failed,
while the three checks that read attributes back off the cleared cookie and all
382 regression checks passed, because every one of those reads the entry through
the key it is FILED under and never asks what it announces.

The structural fault is the one the previous two repairs each met one field
further out: where an entry is filed and what an entry announces are two
observables, and the carrier collapsed them into one. A7 pinned the first and was
silent about the second, so the bypass simply chose it. A10 closes the collapse by
observing the announced name in its own right and stating that the real hand-over
makes the two agree — true of the real patched routine, whose clearing call reaches
the container's item assignment (`response.py:169`), and false of any routine that
files an entry announcing another name or none.

This closure TERMINATES the field-chasing rather than advancing it one rung, which
is the test the previous repairs failed. The emitted header is a function of
exactly the carried observables: its name half is the announced name, its body half
the transmitted body form, and its attribute tail the set attributes in a FIXED
order, because the container seeds every attribute slot when it creates an entry
— so attribute ORDER is not a further freedom. Measured: 4000 entries reaching the
same observable tuple by different construction routes and different attribute
insertion orders emit byte-identical headers, 0 disagreements. With the announced
name observed, no part of what the response transmits for the cleared cookie
remains outside the carrier. `mergeDirective` was extended in step, and correctly:
the announced name is restated by a later hand-over rather than sticky (measured —
an entry on file announcing `OTHERNAME`, handed over again for `sessionid`,
announces `sessionid`), so a routine may not leave a stale announced name standing
on a cookie that already had an entry. Both differential oracles now read the
announced name off the entry itself, so neither is narrower than the claim it
validates.

TOO WEAK, in what the carrier observed (an earlier pass). The audit produced a
verify-but-not-resolve counterexample that agreed with the modelled
attribute-setter on all nine of its then-observed ATTRIBUTES and differed only in
what the response put on the wire for the emptied body: it assembled the entry's
image directly instead of routing it through the modelled call, so the body never
went through the container's encoding step and the emitted header read `k=`
where the real one reads `k=""`. Measured completed=True resolved=FALSE, failing
the two session checks that compare that header verbatim against a string
containing `{}=""`, with the other three checks and all 382 regression checks
passing — the defect was invisible to every clause because the transmitted form
was outside the carrier. The structural fault was that `mkCookie`, at nine
fields, was a TRANSPARENT constructor over exactly the attributes an
implementation could set by hand: agreeing with it on those attributes did not
require going through the modelled callee, and everything the callee determines
BEYOND them was a free choice. A9 closes it by observing what the response
transmits — the body's encoded form — alongside the attributes, alongside the
note and version attributes a clearing directive never states and could
therefore have added unobserved. The clause is true of the real patched routine,
whose filing step encodes the body it is handed (`response.py:169`), and false of
any routine that transmits something else for it or adds an attribute of its own.
Both differential oracles were widened in step with that pass.

TOO STRONG, in the domain it declared. The same audit found the spec asserting,
on inputs its `require` admitted, behavior the patched repo does not have: with
`total` termination semantics the single equation claims the routine TERMINATES
and files exactly one directive, but handed an empty name, a name outside the
cookie-name alphabet, or one of the names reserved for a directive's own
attributes, the real routine records nothing and fails outright. The raise is
byte-identical before and after the patch and originates in the UNCHANGED callee,
so it condemned the declared domain rather than the behavior the patch
introduces; the earlier evidence missed it because both fuzzers drew names from a
subset that could not produce such a name, so both passed vacuously over the
divergent region. `recordableKey` and `domainStated` declare the region the
callee actually records, which is the same carve-out `acceptedPolicy` already
made for the policy value, and G-AX now measures that boundary in both
directions rather than assuming it.

A8 was added by an earlier SPEC-REPAIR pass, after the audit produced a
verify-but-not-resolve counterexample of a different shape: the carrier projected
only the five flag/scope fields, so the lifetime a directive grants was outside
everything the spec could observe. An impl assembling that five-field image
without going through the audited attribute-setter call VERIFIED — and its
faithful counterpart emitted an entry with the right flags but no spent lifetime
and no past expiry, which a browser keeps for the rest of the session rather than
dropping. Measured completed=True resolved=FALSE on three consecutive harness
runs, failing three of the five target checks and regressing two that had passed
(both of the latter read `max-age` and `expires` back off the cleared cookie).
Widening the carrier to the nine fields, and pinning the lifetime pair in A8,
makes that counterexample WRONG rather than merely untested: the clause is true of
the real patched routine, whose clearing call passes both arguments
(`response.py:220-222`), and false of any routine that omits either. The
`mergeDirective` model was extended in step, and G-AX/G-CONF now compare all nine
fields, so the A-reference's projection is no longer narrower than the spec's
claim.

A7/B3/B4/C3/C4 were added by an earlier SPEC-REPAIR pass after the P2 audit
produced verify-but-not-resolve counterexamples: with the addressee unobserved, an
impl substituting its own literal for the caller-supplied cookie name at either
clear site VERIFIED, and its faithful patch was measured completed=True
resolved=FALSE on three consecutive harness runs. Those clauses hold of the real patched
routine and its two patched call sites — `set_cookie` files the morsel under the
key it is given (`response.py:169`) and each site passes its own cookie name —
so the counterexamples are now WRONG rather than excluded. All four prepatch
twins still fail on their own original A4/A5-shaped goals, so the added clauses
do not mask the pre-change bug. By R
(`str/str|None ↔ String/Option String`, the field-wise morsel bijection) the
verified routines equal the patched `delete_cookie` and its two patched call
sites; by G-AX the deep model `mkCookie` equals the real `set_cookie` on the
observed fields (A-reference); by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the one
audited callee — and the gold patch resolves (G-RESOLVE). The sole trust point
is A-reference fidelity (G-AX) + refinement fidelity (this doc, G-EQ + G-CONF);
there is no axiom-soundness trust point because no axiom is consumed.
