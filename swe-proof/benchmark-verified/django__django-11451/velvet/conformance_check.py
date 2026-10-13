#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11451 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`authGuard`) is the admissibility short-circuit the gold
patch adds to `ModelBackend.authenticate`:

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:   # <-- the fix
            return
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)      # password hasher
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

The CHANGED behaviour the spec pins is a SIDE EFFECT: when the effective
`username` or the `password` is `None`, the routine must perform NO database
query (`get_by_natural_key`) and run NO password hasher (`set_password`), and
return `None`. Crucially the RETURN VALUE does not discriminate the fix — both
before and after the patch, missing credentials yield `None`. The only
observable that distinguishes the buggy and fixed code is "did the expensive
backend work happen", which the F2P test asserts via
`assertNumQueries(0)` and `CountingMD5PasswordHasher.calls == 0`.

There is no DB-free, input-dependent R/I shadow to differential-test:

  * The side effect materializes only against a live Django `AUTH_USER_MODEL` +
    a real database connection: to observe "a query happened" one must call
    `authenticate(...)` through the real backend with a configured User model
    and a query counter — i.e. the F2P integration test itself
    (`test_authentication_without_credentials`), not a pure transliteration this
    gate can fuzz over >=1e5 inputs.
  * The proceed-path's returned principal is the FREE INPUT `backendOutcome`
    (the UNCHANGED downstream lookup/check chain, mapping.md §3); its R/I shadow
    is a constant pass-through with no input-dependent computation to refute.
    The changed op's content is the boolean guard `(effective is None) or
    (password is None)`, whose only shadow is a constant decision over presence
    bits — diffing it carries no information the spec (G-VERIFY) does not already
    pin.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the modeled op's only observable
is a side effect on a live ORM + DB with no DB-free R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub (precedent:
django__django-11179). Soundness of the modeled behaviour is carried instead by
G-VERIFY (the spec provably forces `queried = false` and `principal = none` when
credentials are incomplete) and G-DIFF (the prepatch, which lacks the guard and
always runs the expensive path, fails exactly the `queried = false` clause). See
mapping.md section 4 and refinement.md sections B/D.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-11451 — the modeled do-block is "
          "an admissibility short-circuit whose only discriminating observable "
          "is a side effect (no DB query via get_by_natural_key, no password "
          "hasher via set_password) on a live AUTH_USER_MODEL + database when "
          "credentials are incomplete; the return value is None in both the "
          "buggy and fixed code, and the proceed-path principal is a free input "
          "(the unchanged backend chain). No DB-free, input-dependent R/I "
          "shadow exists. conf_skip=true. Soundness covered by G-VERIFY + "
          "G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
