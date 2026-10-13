# mapping.md — django__django-11451

Binds `Solution.lean` symbols to the repo at
`base_commit = e065b293878b1e3ea56655aa9d33e87576cd77ff`.

Repo file under change: `django/contrib/auth/backends.py`
(the credentials short-circuit added to `ModelBackend.authenticate`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `authGuard (usernameArg fallbackUsername : Option Name) (password : Option Secret) (backendOutcome : Option Principal)` | `ModelBackend.authenticate(self, request, username=None, password=None, **kwargs)` — `django/contrib/auth/backends.py:39-49` | the modeled changed function (the front entry of the model-backed credentials check) |
| `usernameArg` | the `username` keyword parameter (`backends.py:39`) | the directly-supplied identifier (present `some u` / absent `none`) |
| `fallbackUsername` | `kwargs.get(UserModel.USERNAME_FIELD)` (`backends.py:41`) | the identifier recovered from the extra kwargs when `username` is absent |
| `password` | the `password` keyword parameter (`backends.py:39`) | the supplied secret (only its PRESENCE is observed: `some s` / `none`) |
| `backendOutcome` | the result of the unchanged backend lookup chain `UserModel._default_manager.get_by_natural_key(...)` + `user.check_password(...)` + `self.user_can_authenticate(user)` (`backends.py:42-49`) | FREE INPUT: the principal the proceed-path would return (`some p`) or `none` if the lookup/check declines. Unchanged by the fix; see §3. |
| `effectiveUsername arg fallback` | the value of the local `username` after `if username is None: username = kwargs.get(UserModel.USERNAME_FIELD)` (`backends.py:40-41`) | pure helper: the identifier actually used downstream |
| `out.queried` (`AuthOutcome` field) | whether control reaches the expensive backend path — the `try: ... get_by_natural_key(...)` database query and the `set_password(...)` password-hasher run (`backends.py:42-46`) | the SIDE-EFFECT observable the F2P tests assert via `assertNumQueries(0)` and `CountingMD5PasswordHasher.calls == 0` |
| `out.user` (`AuthOutcome` field) | the function's return value (`return` ⇒ `None`, or `return user`) | the returned principal |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `username` argument / `kwargs.get(USERNAME_FIELD)` : a `str` identifier or `None` | `Option Name` (`Name := Nat`) | `some u` ↔ a present identifier (its concrete spelling is never observed by the guard, only its presence); `none` ↔ Python `None`. |
| the `password` argument : a `str` secret or `None` | `Option Secret` (`Secret := Nat`) | `some s` ↔ a present secret; `none` ↔ Python `None`. Only presence is observed (the secret's content feeds only unchanged callees). |
| the returned user object, or implicit/explicit `None` | `Option Principal` (`Principal := Nat`) | `some p` ↔ an authenticated user object; `none` ↔ Python `None` (declined / short-circuited). |
| "an expensive backend lookup + hasher run occurred" | `Bool` (`queried`) | `true` ↔ control entered the `try`/`except` block (≥1 DB query and possibly a `set_password` hasher call); `false` ↔ the early `return` was taken with NO query and NO hasher call. `assertNumQueries(0)` ⇔ `queried = false`. |

`Name`, `Secret`, `Principal` are modeled as `Nat` because the guard observes
only PRESENCE (`isSome`/`isNone`), never the underlying value; the value flows
untouched through the unchanged callee chain folded into `backendOutcome`.

## 3. Callee provenance

No axioms and no A-reference deep models.

- The backend lookup chain `get_by_natural_key(...)` / `check_password(...)` /
  `user_can_authenticate(...)` is **UNCHANGED** by the fix. The patch does not
  alter what that chain computes; it only decides WHETHER to run it. Its result
  is therefore taken as the **free input** `backendOutcome : Option Principal`.
  The spec makes no behavioural claim about it and holds for EVERY value, so
  there is nothing to check against a real callee — hence **no G-AX**
  (mirrors django__django-11149's free-input `userHasPerm`/`superResult`).
- The CHANGED op is the early-return guard itself
  (`if username is None or password is None: return`), modeled **deeply** as the
  conditional that (a) suppresses the expensive path (`queried := false`) and
  (b) returns `none`. No outside contract is consumed (I-tagged, refinement.md).

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The fix's only DISCRIMINATING
observable is a **side effect** — that NO database query is issued and the
password hasher is NOT run when credentials are missing
(`assertNumQueries(0)` + `CountingMD5PasswordHasher.calls == 0`). The return
value does NOT discriminate: both before and after the fix, missing credentials
yield `None`.

There is no DB-free R/I shadow to differential-test:

- The side effect (`queried`) materializes only against a **live Django
  `AUTH_USER_MODEL` + database connection**: to observe "a query happened" one
  must call `authenticate(...)` through the real backend with a configured User
  model and count queries — i.e. the F2P integration test itself
  (`test_authentication_without_credentials`), not a pure transliteration this
  gate can fuzz over ≥10⁵ inputs.
- The proceed-path's returned principal is the free input `backendOutcome`
  (the unchanged callee chain, §3); its R/I shadow is the constant pass-through
  with no input-dependent computation to refute.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the modeled op's only observable is a
side effect on a live ORM + DB with no DB-free R/I shadow, set
`meta.json conf_skip=true` and ship a `status=skip` stub (precedent:
django__django-11179). Soundness of the modeled behavior is carried instead by
**G-VERIFY** (the spec provably forces `queried = false` ∧ `user = none` when
credentials are missing) and **G-DIFF** (the prepatch, lacking the guard, runs
the expensive path unconditionally and fails exactly the `queried = false`
clause — refinement.md §B).

## 5. Notes

The four FAIL_TO_PASS entries across `ModelBackendTest`,
`CustomPermissionsUserModelBackendTest` and `ExtensionUserModelBackendTest`
(`test_authentication_without_credentials`, `test_custom_perms`) exercise the
SAME single fixed behavior under different `UserModel`s; the
`test_custom_perms` entries are collateral re-runs of the suite, not a distinct
behavior. One modeled function + one prepatch covers the fixed behavior; the
gold-verbatim `patch.diff` resolves all of them (G-RESOLVE).

`usernameArg`, `fallbackUsername`, `password`, `backendOutcome` are all
read-only inputs — none is declared `mut` (directive 5): the guard reads them
and produces a fresh `AuthOutcome`, mutating nothing it is handed.
