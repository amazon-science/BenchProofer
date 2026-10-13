# refinement.md — django__django-16631

Operation-by-operation correspondence between `Solution.lean`'s
`resolveSessionPrincipal` impl region and `patch.diff` (the gold patch makes
`get_user` accept a session whose retained credential matches a *prior* secret —
re-establishing the session under the current secret — instead of dropping the
principal). Each step is tagged **R** (type refinement), **A** (axiomatized
callee), or **I** (identical concrete op). EVERY step is R, A, or I.

`patch.diff` is the gold patch **verbatim** (applies at base_commit, resolves —
G-RESOLVE).

## A. The session-credential acceptance policy — `get_user`

Gold hunk (`django/contrib/auth/__init__.py`, the session-verification block):
```
-                session_hash_verified = session_hash and constant_time_compare(
-                    session_hash, user.get_session_auth_hash()
-                )
+                if not session_hash:
+                    session_hash_verified = False
+                else:
+                    session_auth_hash = user.get_session_auth_hash()
+                    session_hash_verified = constant_time_compare(
+                        session_hash, session_auth_hash
+                    )
                 if not session_hash_verified:
-                    request.session.flush()
-                    user = None
+                    if session_hash and any(
+                        constant_time_compare(session_hash, fallback_auth_hash)
+                        for fallback_auth_hash in user.get_session_auth_fallback_hash()
+                    ):
+                        request.session.cycle_key()
+                        request.session[HASH_SESSION_KEY] = session_auth_hash
+                    else:
+                        request.session.flush()
+                        user = None
```

| # | Solution.lean impl op (`resolveSessionPrincipal`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `match storedCred with \| none => … reject` | `if not session_hash: session_hash_verified = False` then (since `session_hash` is falsy) the `any(...)` guard's `session_hash and …` short-circuits to false ⇒ `flush(); user = None` | **I** | identical concrete op: an absent/empty retained token cannot be verified and is not eligible for the prior-secret path (the `session_hash and …` conjunct guards it), so the principal is dropped and the session cleared. `request.session.get(HASH_SESSION_KEY)` falsy ↔ `storedCred = none` (mapping.md §2); `flush()`+`user=None` ↔ `{ principalKept := false, action := reject }`. |
| A2 | `if h = currentCred then … valid` | `session_auth_hash = user.get_session_auth_hash(); session_hash_verified = constant_time_compare(session_hash, session_auth_hash)`; when true the `if not session_hash_verified` block is skipped ⇒ session untouched, `user` kept | **I** | identical concrete op: the retained token verifies under the current secret. `constant_time_compare(session_hash, user.get_session_auth_hash())` ↔ `h = currentCred` (a pure equality test, mapping.md §2); skipping the block ↔ `{ principalKept := true, action := valid }`. |
| A3 | `else if priorCreds.contains h then … acceptedPrior` | `if session_hash and any(constant_time_compare(session_hash, fallback_auth_hash) for fallback_auth_hash in user.get_session_auth_fallback_hash()): request.session.cycle_key(); request.session[HASH_SESSION_KEY] = session_auth_hash` | **I** | identical concrete op — the CHANGED op, modeled deeply. `any(constant_time_compare(session_hash, fb) …)` over the prior-secret tokens ↔ `priorCreds.contains h` (mapping.md §2); taking the fallback-acceptance path ↔ `action := acceptedPrior` (whose effect glue — `cycle_key()` + storing `session_auth_hash`, the current-secret token — is FIXED by this refinement, mapping.md §2a, and intentionally NOT described in the spec view); the principal is NOT set to `None` ↔ `principalKept := true`. |
| A4 | `else … reject` | `else: request.session.flush(); user = None` | **I** | identical concrete op: a retained token recognised by neither the current nor any prior secret. `flush()`+`user=None` ↔ `{ principalKept := false, action := reject }`. |

The free inputs (`currentCred`, `priorCreds`) carry the UNCHANGED token-producing
machinery's results (mapping.md §3): `currentCred = user.get_session_auth_hash()`,
`priorCreds` = the tokens from `user.get_session_auth_fallback_hash()`. The
`base_user.py` hunk only refactors `get_session_auth_hash` into
`_get_session_auth_hash(secret=None)` (behaviourally identical: `secret=None`
defaults to the current secret) and adds the generator that yields the
prior-secret tokens — it changes no token's value, only makes the prior-secret
tokens available. So the tokens are taken as given inputs, not re-derived or
axiomatized.

No A (axiom) steps; no A-reference deep models; no kind-3 (changed
inexpressible) steps. The single changed op (A3) is the prior-secret acceptance
branch, modeled deeply and tagged **I**.

## B. verify(Solution) ⇒ resolved; prepatch fails on the right clause

`resolveSessionPrincipal` verifies only if `out = verifyDecision …`, i.e.:
- `storedCred = none` ⇒ `principalKept = false`, `action = reject` (A1);
- `storedCred = some h`, `h = currentCred` ⇒ `principalKept = true`,
  `action = valid` (A2);
- `storedCred = some h`, `h ≠ currentCred`, `h ∈ priorCreds` ⇒
  `principalKept = true`, `action = acceptedPrior` (A3);
- `storedCred = some h`, `h ≠ currentCred`, `h ∉ priorCreds` ⇒
  `principalKept = false`, `action = reject` (A4).

By R (mapping.md §2) this is exactly the patched `get_user` session block. The
F2P test `test_get_user_fallback_secret` exercises the A3 leg then the A2 leg:
under `SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=[<old secret>]`, the stored
token (made under the old secret) does NOT match the current-secret token but
DOES match a prior-secret token — so the principal is kept and the
fallback-acceptance path (with its refinement-fixed effect glue, mapping.md §2a)
runs (A3): the session key is cycled
(`assertNotEqual(session_key, prev_session_key)`) and the stored token is
refreshed to the current-secret token. The test then re-calls `get_user`
under `SECRET_KEY="newsecret"` with NO fallbacks: the now-refreshed stored token
matches the current secret, so the principal is kept with the session untouched
(A2). The PASS_TO_PASS suite (`test_get_user`, `test_get_user_anonymous`)
requires the unchanged `valid`/`reject` behaviour when no rotation is in play.

The prepatch (`Solution_prepatch.lean`) omits the prior-secret path: any
`h ≠ currentCred` goes straight to `reject` (drop the principal). With a token
matching a prior secret the frozen spec demands `principalKept = true` and
`action = acceptedPrior`, so `prove_correct` fails on exactly the
discriminating clause:
```
case «ensures_1: out = verifyDecision storedCred currentCred priorCreds»
storedCred = some i, ¬ i = currentCred
⊢ i ∉ priorCreds          -- unprovable: the stored token may match a prior secret
```
This is the precise bug the issue describes ("SECRET_KEY_FALLBACKS is not used
for sessions" — rotating the key logs everyone out). G-DIFF passes.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — accepting
a session under a prior secret instead of dropping the principal — is modeled
**deeply** (the `verifyDecision` `priorCreds.contains h` branch yielding
`acceptedPrior` / the `if … else if …` impl, A3, **I**), not hidden behind
an axiom. There are no consumed axioms: the only callees the policy touches
(`constant_time_compare`, `get_session_auth_hash`,
`get_session_auth_fallback_hash`) are UNCHANGED token-producing/comparing
plumbing folded into the free inputs `currentCred`/`priorCreds`, about which the
spec claims nothing (mapping.md §3), so there is nothing for G-AX to check.

## D. G-CONF — conf_skip=true

The fix's discriminating observables — the principal being kept, the session key
being cycled, and the stored token being refreshed to the current-secret token —
are side effects on a live Django request/session + `AUTH_USER_MODEL` + database;
there is no DB-free, input-dependent R/I shadow whose oracle is anything other
than the patched `get_user` running against that live stack (the decision's
scalar inputs are themselves outputs of unchanged crypto plumbing folded into
free inputs). `conformance_check.py` is a documented `status=skip` stub
(`meta.json conf_skip=true`; precedent: django__django-11451,
django__django-11179). Soundness is carried by G-VERIFY (the spec forces the
exact four-way decision above) and G-DIFF (the prepatch fails the
`acceptedPrior` clause). See mapping.md §4.
