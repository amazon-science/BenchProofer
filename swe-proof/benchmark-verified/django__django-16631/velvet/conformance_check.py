#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16631 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`resolveSessionPrincipal`) is the session-credential
acceptance policy the gold patch installs in `get_user(request)`
(django/contrib/auth/__init__.py):

    session_hash = request.session.get(HASH_SESSION_KEY)
    if not session_hash:
        session_hash_verified = False
    else:
        session_auth_hash = user.get_session_auth_hash()
        session_hash_verified = constant_time_compare(session_hash, session_auth_hash)
    if not session_hash_verified:
        if session_hash and any(
            constant_time_compare(session_hash, fallback_auth_hash)
            for fallback_auth_hash in user.get_session_auth_fallback_hash()
        ):
            request.session.cycle_key()                       # <-- the fix
            request.session[HASH_SESSION_KEY] = session_auth_hash
        else:
            request.session.flush()
            user = None

The CHANGED behaviour the spec pins is a set of SIDE EFFECTS on a live
request/session object and on the located principal:

  * `principalKept` — whether `user` survives the block or is replaced by
    `AnonymousUser()`;
  * the session ACTION — `cycle_key()` + refreshing the stored `_auth_user_hash`
    to the current-secret token (the `acceptedPrior` case's effect glue, fixed
    by the refinement — mapping.md §2a), versus `flush()` (the `reject` case),
    versus no change (the `valid` case).

None of these are a pure function of fuzzable scalar inputs. They materialize
only against a live Django stack:

  * To observe "the principal was kept", "the session key was cycled", and "the
    stored hash was refreshed to the current-secret hash" one must drive
    `get_user(request)` end to end with a configured `AUTH_USER_MODEL`, a real
    session store, and `override_settings(SECRET_KEY=…, SECRET_KEY_FALLBACKS=…)`
    — i.e. the F2P integration test itself (`test_get_user_fallback_secret`),
    not a pure transliteration this gate can fuzz over >=1e5 inputs.
  * The decision's pure inputs (the stored token, the current-secret token, the
    prior-secret tokens) are themselves outputs of UNCHANGED crypto plumbing
    (salted_hmac / constant_time_compare) folded into free inputs
    (mapping.md §3). Their only observable relation is equality, which the spec
    (G-VERIFY) already pins exactly; a differential shadow of the boolean
    decision carries no information G-VERIFY does not already hold.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the modeled op's only
discriminating observable is a side effect on a live request/session/ORM with no
DB-free, input-dependent R/I shadow, set meta.json conf_skip=true and ship this
status=skip stub (precedent: django__django-11451, django__django-11179).
Soundness of the modeled behaviour is carried instead by G-VERIFY (the spec
provably forces `principalKept = true` and `action = acceptedPrior` exactly
when the stored token matches a prior — not the current — secret, `valid` when
it matches the current secret, and `reject` otherwise) and G-DIFF (the prepatch,
which lacks the prior-secret path, drops the principal whenever the current
secret does not verify and fails exactly the `acceptedPrior`/`principalKept`
clause).
See mapping.md section 4 and refinement.md sections B/D.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-16631 — the modeled do-block is "
          "the session-credential acceptance policy of get_user(), whose "
          "discriminating observables are side effects (the located principal is "
          "kept rather than replaced by AnonymousUser; the session key is cycled "
          "via cycle_key() and its stored _auth_user_hash refreshed to the "
          "current-secret token; versus flush()) on a live Django "
          "request/session + AUTH_USER_MODEL + database. The decision's scalar "
          "inputs are themselves outputs of unchanged crypto plumbing folded "
          "into free inputs, observed only by equality. No DB-free, "
          "input-dependent R/I shadow exists. conf_skip=true. Soundness covered "
          "by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
