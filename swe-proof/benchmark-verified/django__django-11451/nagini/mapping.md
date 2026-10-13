# mapping.md — django__django-11451

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e065b293878b1e3ea56655aa9d33e87576cd77ff`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/contrib/auth/backends.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `authenticate(self, identifier, secret, fallback_identifier)` | `ModelBackend.authenticate(self, request, username=None, password=None, **kwargs)` — `django/contrib/auth/backends.py:39` | the modeled changed function (credential checker) |
| `Checker` (fields `lookups`, `verifications`) | `ModelBackend` instance + the two externally-observable expensive operations it triggers (a DB query and the password hasher) | the checker carrying the two cost counters |
| `Checker.lookups` | the database round trip performed by `UserModel._default_manager.get_by_natural_key(username)` (`backends.py:43`) | counter: how many directory lookups (DB queries) have run |
| `Checker.verifications` | the password-hasher invocation, which runs exactly once on every both-present path: `user.check_password(password)` on the recognised branch (`backends.py:49`, which calls the hasher's `encode` once) and `UserModel().set_password(password)` on the `DoesNotExist`/unrecognised branch (`backends.py:47`, the timing-defence run) | counter: how many verification-primitive (password-hasher) runs have happened |
| `directory_recognises(identifier)` *(axiom — A-consumed)* | `UserModel._default_manager.get_by_natural_key(username)` raising / not raising `UserModel.DoesNotExist` — `BaseUserManager.get_by_natural_key`, `django/contrib/auth/base_user.py:43` (`self.get(**{USERNAME_FIELD: username})`) | unchanged directory-lookup decision: does an account with this natural key exist |
| `secret_verifies(identifier, secret)` *(axiom — A-consumed)* | `user.check_password(password) and self.user_can_authenticate(user)` — `backends.py:49`; `check_password` at `base_user.py:101`, `user_can_authenticate` at `backends.py:52` | unchanged verification-and-permission decision for a recognised account |

The kwargs side channel `username = kwargs.get(UserModel.USERNAME_FIELD)`
(`backends.py:40-41`) is modeled by the explicit `fallback_identifier`
parameter and the `if eff is None: eff = fallback_identifier` recovery step.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `username` (a `str` / `None`) | `identifier: Optional[int]` | `None` ↔ absent; any present username ↔ a present opaque `int` code. The bug + tested behaviour turn ONLY on present-vs-absent, never on the character content, so a single `Optional[int]` is faithful (mapping.md §3). |
| `password` (a `str` / `None`) | `secret: Optional[int]` | as above: `None` ↔ absent; present secret ↔ present `int`. |
| `kwargs.get(UserModel.USERNAME_FIELD)` (`str`/`None`) | `fallback_identifier: Optional[int]` | the recovered identifier from the keyword side channel; `None` ↔ not supplied. |
| the returned `user` object / implicit `None` | `Optional[int]` | a non-`None` result ↔ an authenticated account (its identifier); `None` ↔ no authentication. The F2P/P2P tests observe only authenticated-vs-not, which `Optional[int]` captures exactly. |
| a database query (one round trip) | `+1` to `Checker.lookups` | the externally-counted cost the F2P test pins with `assertNumQueries(0)`. |
| one password-hasher run | `+1` to `Checker.verifications` | the externally-counted cost: the F2P `test_authentication_without_credentials` pins it at `CountingMD5PasswordHasher.calls == 0` on the absent-credential path, while the P2P `test_authentication_timing` ("Hasher is run once regardless of whether the user exists. Refs #20760.") pins it at exactly `1` on every both-present path — recognised AND unrecognised alike. |

The `request` parameter is not read by the modeled behaviour and is omitted.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `directory_recognises` ↔ `get_by_natural_key` (A-consumed)
**Callee:** `BaseUserManager.get_by_natural_key(self, username)`
(`django/contrib/auth/base_user.py:43`):

```python
def get_by_natural_key(self, username):
    return self.get(**{self.model.USERNAME_FIELD: username})
```

`self.get(...)` issues exactly one `SELECT … WHERE <USERNAME_FIELD> = username`
and raises `UserModel.DoesNotExist` iff no row matches. The axiom encodes the
WEAKEST property the proof needs: a pure recognition decision (account exists?).
It does NOT claim the lookup is side-effect-free in reality — the side effect
(one DB query) is accounted for separately and deeply by the `lookups` counter
in `authenticate`. The decision is deterministic for a fixed directory.

### 3.2 `secret_verifies` ↔ `check_password` + `user_can_authenticate` (A-consumed)
**Callees:** `AbstractBaseUser.check_password(self, raw_password)`
(`base_user.py:101`, delegates to `django.contrib.auth.hashers.check_password`)
and `ModelBackend.user_can_authenticate(self, user)` (`backends.py:52`, returns
`is_active or is_active is None`). On the recognised branch the real code is
`if user.check_password(password) and self.user_can_authenticate(user): return user`
(`backends.py:49`). The axiom encodes the weakest property the proof needs: a
pure decision whether the supplied secret matches AND the account may
authenticate, determining whether the recognised path returns the account or
nothing.

The hash-compare cost is accounted for separately by the `verifications`
counter, and it is incurred on EVERY both-present path: the recognised path
runs the hasher once (`check_password` -> `hashers.check_password` ->
`MD5PasswordHasher.verify` -> `encode`, exactly one `encode` call for both a
correct and a wrong secret), and the unrecognised path runs it once via the
timing-defence `UserModel().set_password(password)` (`backends.py:47`). The
P2P `test_authentication_timing` confirms this: `CountingMD5PasswordHasher.calls
== 1` for a recognised account AND for `no_such_user`. So `verifications`
increments by exactly 1 whenever both credentials are present, regardless of
recognition; the `secret_verifies` axiom carries only the recognised path's
return *decision*, not its cost.

### 3.3 What is modeled DEEPLY (not axiomatized)
The behaviour the patch CHANGES — the early-return shortcut that avoids BOTH
expensive operations when a credential is absent — is modeled deeply via the
`lookups`/`verifications` counters and the impl control flow, NOT hidden behind
any axiom. The axioms cover only the two unchanged decision primitives the
recognised/unrecognised branches consult. There is no axiom about the changed
control flow.

**Soundness check (G-AX):** `axiom_check.py` drives the REAL
`ModelBackend.authenticate` against a live in-memory auth database with the real
MD5 hasher instrumented to count `encode` calls and Django's
`CaptureQueriesContext` to count queries. It asserts, over the full credential
matrix (both absent / one absent / recognised-correct / recognised-wrong /
unrecognised, plus determinism): absent ⇒ `None` (post-patch tree: + 0 queries +
0 hasher runs; base_commit tree: the useless lookup still runs — the bug the
patch fixes); both present ⇒ exactly 1 query + exactly 1 hasher run on EVERY
path; recognised ⇒ result is the matched account iff the secret verifies;
unrecognised ⇒ `None`. These are exactly the axioms' Ensures and the deep
counter model. The check detects whether the mounted tree carries the absent-
credential guard and asserts the matching (post-patch vs pre-patch) absent-path
behaviour, so it reaches exit 0 on either tree. It imports only Django (the
framework under test, present in the eval image) and the standard library. Exit
0 iff sound.
