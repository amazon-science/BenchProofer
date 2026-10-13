# refinement.md — django__django-11451

The operation-by-operation correspondence between `model.py`'s implementation
(the `authenticate` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

Gold hunk (`django/contrib/auth/backends.py`, `ModelBackend.authenticate`):
```
     def authenticate(self, request, username=None, password=None, **kwargs):
         if username is None:
             username = kwargs.get(UserModel.USERNAME_FIELD)
+        if username is None or password is None:
+            return
         try:
             user = UserModel._default_manager.get_by_natural_key(username)
         except UserModel.DoesNotExist:
```

The change inserts a guard, BEFORE the directory lookup and the password
hasher, that returns nothing when either credential is absent — so neither
expensive operation runs in that case.

## Operation correspondence

| # | model.py impl op (`authenticate`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| 1 | `eff = identifier` | `username` parameter | R | `str`/`None` ↔ `Optional[int]` (mapping.md §2); only present-vs-absent is observed. |
| 2 | `if eff is None: eff = fallback_identifier` | `if username is None: username = kwargs.get(UserModel.USERNAME_FIELD)` (`backends.py:40-41`) | R + I | the keyword side channel is modeled by the explicit `fallback_identifier` param (R); the `is None`-guarded reassignment is the identical control flow (I). |
| 3 | `if eff is None or secret is None: return None` | `if username is None or password is None: return` (the added hunk) | I | the inserted guard, verbatim; `return` (implicit `None`) ↔ `return None` (`Optional[int]`). This is THE change. |
| 4 | `self.lookups = self.lookups + 1` | `user = UserModel._default_manager.get_by_natural_key(username)` performing one DB query (`backends.py:43`) | R | one directory lookup = one `+1` to the `lookups` counter (mapping.md §2). The query's *occurrence* is the load-bearing observable (`assertNumQueries`). |
| 5 | `self.verifications = self.verifications + 1` | one password-hasher run, incurred on EVERY both-present path: `user.check_password(password)` on the recognised branch (`backends.py:49`) OR `UserModel().set_password(password)` on the unrecognised branch (`backends.py:47`); each runs the hasher's `encode` exactly once | R | one hasher run = one `+1` to `verifications` (mapping.md §2). The P2P `test_authentication_timing` pins `CountingMD5PasswordHasher.calls == 1` for both a recognised account and `no_such_user`, so the increment is unconditional on the both-present path — modeled by hoisting it ahead of the recognition branch. |
| 6 | `if not directory_recognises(eff): return None` (unrecognised branch) | the `try/except UserModel.DoesNotExist:` around the lookup; on `DoesNotExist` the body runs `set_password` (the hasher run of step 5) then falls off the end -> implicit `return None` (`backends.py:42-47`) | A-consumed + I | `directory_recognises` is the weakest contract on the lookup the proof needs: it raises `DoesNotExist` iff no account matches (mapping.md §3.1); the `except` branch ⇔ `not directory_recognises` (A-consumed). Falling off the end returns `None` (I). |
| 7 | `if secret_verifies(eff, secret): return eff else return None` (recognised branch) | `if user.check_password(password) and self.user_can_authenticate(user): return user` then implicit `return None` (`backends.py:48-49`) | A-consumed + R | `secret_verifies` is the weakest contract on `check_password ∧ user_can_authenticate` (mapping.md §3.2): the recognised path returns the account iff the secret verifies (A-consumed); the returned `user` is exactly the account matched by the lookup, whose natural identifier is `eff`, so `Result() == eff` (R: `user` ↔ its `Optional[int]` identifier). The hasher run on this branch (`check_password` -> `encode`) is step 5's increment — it is NOT extra, it is the one run this path makes. |

## The discriminating clause (G-DIFF)

The whole change is step 3 (the inserted guard). The spec senses it through
postcondition clause (1):

```
Implies((identifier is None and fallback_identifier is None) or secret is None,
        Result() is None
        and self.lookups == Old(self.lookups)
        and self.verifications == Old(self.verifications))
```

`model_prepatch.py` (byte-identical spec) omits the guard: it increments
`lookups` unconditionally and, on the unrecognised branch (which an absent
identifier hits), increments `verifications`. It therefore **fails** clause (1)
— exactly the F2P `test_authentication_without_credentials` observation
(`assertNumQueries(0)` and `CountingMD5PasswordHasher.calls == 0`). The two
counters give the two independently-observable fixed effects (no query, no
hasher run) from the single inserted guard, so one prepatch witnesses both.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the early-return shortcut that avoids both expensive operations — is modeled
**deeply** (steps 3, 4, 5 via the `lookups`/`verifications` counters and the
control flow), NOT hidden behind an axiom. The two consumed axioms
(`directory_recognises`, `secret_verifies`) cover only **unchanged** decision
primitives (`get_by_natural_key`, `check_password`/`user_can_authenticate`) the
post-guard branches consult; there is no A-reference and no dead axiom.

## verify(model) ⇒ resolved

`authenticate` verifies only if it returns nothing AND leaves both counters
untouched when a credential is absent (clause 1, step 3), performs exactly one
lookup AND exactly one verification-primitive run when both are present (clause
2, steps 4+5 — on every both-present path, recognised or not), returns nothing
on the unrecognised path (clause 2b, step 6), and on the recognised path returns
exactly the matched account `eff` iff the secret verifies (clause 2a, step 7).
By R (str/None ↔ Optional[int], one query/hasher run ↔ one counter increment,
matched `user` ↔ its identifier `eff`) and the two A-consumed axioms (G-AX:
real `get_by_natural_key`/`check_password` meet them), the verified routine
equals the gold patch on the tested inputs — including the P2P observables
`test_authentication_timing` (hasher exactly once on every both-present path)
and `test_authenticate*` (the returned account identity). The gold patch
resolves (G-RESOLVE). Trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
