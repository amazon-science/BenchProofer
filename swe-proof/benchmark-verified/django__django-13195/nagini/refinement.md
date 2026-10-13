# refinement.md — django__django-13195

The operation-by-operation correspondence between `model.py`'s implementation
(the `delete_cookie` impl region, the deep models `expiry_secure` /
`has_security_prefix` / `is_none_ci`, and the live `store_cookie` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural core — `delete_cookie` (`django/http/response.py:213`)

Gold hunk:
```python
-    def delete_cookie(self, key, path='/', domain=None):
-        # Most browsers ignore the Set-Cookie header if the cookie name starts
-        # with __Host- or __Secure- and the cookie doesn't use the secure flag.
-        secure = key.startswith(('__Secure-', '__Host-'))
+    def delete_cookie(self, key, path='/', domain=None, samesite=None):
+        # Browsers can ignore the Set-Cookie header if the cookie doesn't use
+        # the secure flag and:
+        # - the cookie name starts with "__Host-" or "__Secure-", or
+        # - the samesite is "none".
+        secure = (
+            key.startswith(('__Secure-', '__Host-')) or
+            (samesite and samesite.lower() == 'none')
+        )
         self.set_cookie(
             key, max_age=0, path=path, domain=domain, secure=secure,
-            expires='Thu, 01 Jan 1970 00:00:00 GMT',
+            expires='Thu, 01 Jan 1970 00:00:00 GMT', samesite=samesite,
         )
```

| # | model.py impl op (`delete_cookie`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `key: List[int]`, `path: List[int]`, `domain: List[int]`, `policy: List[int]` | `key: str`, `path='/'`, `domain=None`, `samesite=None` arguments | R | `str` ↔ `List[int]` code points; a falsey argument (`None`/`''`) ↔ the empty list, for each of `samesite`, `path` and `domain` (mapping.md §2 — the two preimages are observationally identical on the emitted cookie, and that is measured on every preimage by `conformance_check.py`, not argued). The reach arguments are modelled as VALUES because the emitted expiry only reaches the cookie it is meant to drop if it carries them; they carry no domain restriction, the machinery recording them without inspecting them (measured). **Domain (D):** the two `Requires` — `Implies(len(policy) > 0, is_known_policy(policy))` and `is_storable_name(key)` — carve out exactly the inputs on which the gold routine emits an expiry cookie at all. Outside either, the real code refuses the request and raises instead of returning (`ValueError` from the samesite validation; `CookieError` from `Morsel.set` for an empty name, a name outside the header grammar's alphabet, or any casing of the nine reserved attribute names), so there is no emitted cookie for A4/A5's clauses to be about. The two paths differ in their residue, and only the name path leaves none: `Morsel.set` raises *before* `BaseCookie.__set` inserts, so nothing at all is recorded, whereas `set_cookie` stores the value on its first line and validates the token last, so an unrecognised policy can leave a partially-written morsel behind (measured: `delete_cookie('__Secure-c', samesite='bogus')` → `__Secure-c=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; Secure`) that never carries the requested cross-site attribute. Either way the routine does not return and the spec claims nothing there. Both refusal regions are excluded, not re-specified; mapping.md §2 gives the repo sites and the measured equivalence. |
| A2 | `has_security_prefix(key)` = `starts_with(key, secure_prefix()) or starts_with(key, host_prefix())` | `key.startswith(('__Secure-', '__Host-'))` | R + I | `str.startswith(tuple)` ↔ disjunction of two `starts_with` over code-point prefixes (mapping.md §2). Identical decision. |
| A3 | `is_none_ci(policy)` = length-4 and `lower_cp`-folded code points spell n,o,n,e | `samesite and samesite.lower() == 'none'` | R + I | `str.lower() == 'none'` ↔ per-code-point ASCII fold equal to `[110,111,110,101]`; the `samesite and ...` short-circuit (falsey `None`/`''`) ↔ empty list giving `len != 4` ⇒ false. The changed condition is modelled **deeply**, not axiomatized. |
| A4 | `secure = has_security_prefix(key) or is_none_ci(policy)` (= `expiry_secure(key, policy)`) | `secure = key.startswith(...) or (samesite and samesite.lower()=='none')` | I (under A2+A3) | the introduced disjunction is spelled out identically; this is the discriminating logic of the change, modelled deeply (no `delete_cookie` axiom). |
| A5 | `store_cookie(cookie, path, domain, secure, policy)` | `self.set_cookie(key, max_age=0, path=path, domain=domain, secure=secure, expires='...', samesite=samesite)` | A-consumed | `store_cookie` is the weakest contract on the **unchanged** callee `set_cookie` the proof needs, covering everything that call installs on the emitted cookie: the already-elapsed lifetime (the `max_age=0` + epoch `expires` constants of this call site, carried as `cookie.expired`), the reach (`path` and `domain`, each installed verbatim when non-empty and installing nothing of its own when empty), the `secure` flag cumulatively, and `samesite` present-iff-non-empty, verbatim (mapping.md §3.1). The proof consumes its `Ensures` to discharge `delete_cookie`'s postconditions. The added `samesite=samesite` kwarg is the forwarding the change introduces; the remaining kwargs (`value`/`max_age`/`expires`/`httponly`) are constants of this call site, identical pre- and post-patch, whose whole effect on the emitted cookie is the `expired` bit. |
| A6 | the reach postconditions — `Implies(len(path) > 0, cookie.has_path)` + verbatim value, the empty-path installs-nothing clause, and both again for `domain` | the `path=path, domain=domain` kwargs already present in the pre-patch call and kept by the gold patch | I (under A5) | not a changed operation: it is the routine's **pre-existing** behaviour, and it is in the spec because the emitted expiry must still do its original job. A browser drops a live cookie only when the expiry it receives matches by reach as well as by name, so an implementation that produced the right lifetime and the right two attributes but lost the reach would satisfy every clause about the change while failing to delete anything. That is not hypothetical: an audit refuted an earlier form of this spec, which omitted the reach, with a rival that routed through the setter only where a samesite value was supplied and forged the elapsed lifetime directly on the complementary slice; it passed 5/5 FAIL_TO_PASS and broke `DeleteCookieTests.test_default` on the emitted cookie's `path` (properties.py `weak-forged-expiry-default`, `weak-drop-path-forwarding`, `weak-drop-domain-forwarding`, `weak-hardcode-root-reach`). |

The two discriminating changes:

  - **forwarding** `samesite=samesite` (model: `store_cookie(..., policy)`) is
    sensed by the postcondition `cookie.has_policy == (Old(cookie.has_policy) or
    len(policy) > 0)` plus the verbatim-value clause. The pre-patch passed no
    `samesite`, so the cookie carried none; `model_prepatch.py` and
    `model_prepatch_3.py` reproduce that (call `store_cookie(..., [])`) and
    **fail** the forwarding postcondition (`model_prepatch_3.py` fails exactly
    on that `has_policy` clause).
  - **secure from "none"** (the `or (samesite and samesite.lower()=='none')`
    disjunct) is sensed by `cookie.secure == expiry_secure(key, policy)`. The
    pre-patch computed `secure = key.startswith(...)` only; `model_prepatch.py`
    and `model_prepatch_2.py` reproduce that and **fail** on the `secure`
    postcondition.

The reach clauses (A6) are deliberately NOT among those two: they pin behaviour the
patch does not change, and the differential twins therefore still fail on the two
clauses above and not on them (measured: `model_prepatch.py` and
`model_prepatch_2.py` fail the `secure` clause, `model_prepatch_3.py` the
`has_policy` forwarding clause). Their job is the other half of "verify ⇒
resolved": an implementation must not be able to buy the new behaviour by
abandoning the old. Note also what the reach clauses do NOT say — they do not say
the emitted cookie reaches the site root. `path` is a caller-supplied argument
whose value varies (`settings.SESSION_COOKIE_PATH`, e.g. `/example/`), so a
fixed-value claim would be false of the gold routine itself; what is pinned is that
the emitted cookie carries the reach it was ASKED for. The rival that hard-codes
the site root (`weak-hardcode-root-reach`, right on every default call and wrong on
a custom path) is the control for exactly that distinction.

## B. Call-site wiring (`sessions/middleware.py`, `messages/storage/cookie.py`)

Gold hunks add `samesite=settings.SESSION_COOKIE_SAMESITE` to two existing
`delete_cookie(...)` calls. These introduce no new operation: they pass an
already-existing setting into the now-`samesite`-aware routine.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no node) — the behaviour is exactly `delete_cookie` reached with `policy = settings.SESSION_COOKIE_SAMESITE` | `+ samesite=settings.SESSION_COOKIE_SAMESITE` at each call | I | pure argument wiring. The observed effect (the expiry cookie now carries `SameSite=...`) is identical to the modelled `delete_cookie` forwarding clause; the F2P tests `test_cookie_setings` / `test_session_delete_on_end*` observe exactly that. No separate contracted function (mapping.md §4). |

No separate failing `model_prepatch` for the call sites: their entire content is
the `delete_cookie` forwarding behaviour, whose differential witness is already
`model_prepatch_3.py` (forwarding dropped). A pre-patch that keeps the
byte-identical shared spec cannot additionally model "the setting is not passed"
without re-stating site A's dropped-forwarding skeleton.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operations that genuinely *changed* — the
secure decision gaining the "none" disjunct (A3/A4) and the policy forwarding
(A5's added kwarg) — are modelled **deeply** (the spelled-out `expiry_secure`
predicate and the value carried through `store_cookie`), not hidden behind an
axiom about the function under change: there is no `delete_cookie`
`@ContractOnly`. The only consumed axiom, `store_cookie` (**A-consumed**, A5),
covers the **unchanged** callee `set_cookie`. Every obligation is stated over
values the emitted cookie carries and the arguments it was given; the spec
introduces no ghost state, no witness or store counter, and no capability that
would demand a particular callee be *called* rather than a particular cookie be
*emitted*. That boundary is load-bearing in both directions and both directions
are measured: an implementation that reaches the gold emitted cookie by two
successive stores verifies (`pos-control-two-store`), and so does one that
reproduces the whole record in place without calling the setter at all
(`pos-control-reimplemented-recorder` — measured on the real tree to emit
byte-identical `Set-Cookie` headers to the gold patch and to pass
`responses.test_cookie`, `sessions_tests.tests` and `messages_tests.test_cookie`),
while the forging rivals, which differ from the gold patch in what the emitted
cookie carries, are all rejected. The changed routine itself appears
only as the **A-reference** that G-AX validates the deep model against (mapping
§3.2).

## D. verify(model) ⇒ resolved

`delete_cookie` verifies only if, **wherever an expiry cookie is emitted at all**
(A1's domain), the emitted cookie carries an already-elapsed lifetime and the reach
it was asked for (A6), its secure flag equals `expiry_secure(key, policy)` (A4),
and the policy value is forwarded verbatim (A5 / the forwarding postconditions) —
i.e. the whole footprint the emitted `Set-Cookie` header exposes, not only the two
attributes the change adds. The excluded region costs nothing: there the gold routine
records no cookie and raises, so every input the F2P/P2P tests and the two call
sites (§B) reach is inside the domain — measured, not assumed, by the
`ax-containment` probe and `axiom_check.py`'s `(A-domain)` section (mapping.md
§2, §3.1). By R (str ↔ List[int]; falsey samesite ↔ empty list;
`startswith`/`lower` correspondences) the verified routine equals the
gold `delete_cookie` on the tested inputs; by G-AX the deep model `expiry_secure`
+ forwarding + the reach equals the real post-patch `delete_cookie` (A-reference)
and the unchanged `set_cookie` meets the `store_cookie` axiom it stands in for
(A-consumed), the cumulative clauses included (they are checked over a morsel that
already carries a record, not only over a fresh one). The two call-site hunks are pure wiring (I) of that same routine.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
