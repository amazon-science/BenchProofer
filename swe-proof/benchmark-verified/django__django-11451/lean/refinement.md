# refinement.md — operation correspondence (django__django-11451)

Maps every op in `implementation_credentialAuth` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`ModelBackend.authenticate`) resolves the login name, then
short-circuits with a bare `return` when either the resolved name or the secret
is absent, *before* querying the credential store or running the secret hasher.
Otherwise it performs one store query and: on a miss, exactly one hasher run
via `set_password` (the #20760 uniform-timing hash); on a hit, whatever hashing
`check_password` performs internally — 1 `encode()` via `verify` in the
ordinary case (PASS_TO_PASS `test_authentication_timing` asserts calls == 1 for
an existing user), but 0 when the stored password is unusable
(`hashers.check_password` short-circuits before `hasher.verify`). The hit-path
count is a fixed property of the UNCHANGED `check_password` callee, modeled as
the opaque `checkHashCount`. We model the outcome as a record carrying the
returned principal plus the two observable side-effect counts (`queries`,
`hasherCalls`) the F2P tests measure.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut login := name; if login.isNone then login := fallback` | `if username is None: username = kwargs.get(UserModel.USERNAME_FIELD)` | R | `str`/`None` ↔ `Option (List Char)`; the keyword-fallback resolution, unchanged by the fix, modeled faithfully |
| 2 | `match login, secret with \| some _, some _ => … \| _, _ => return {user:=none, queries:=0, hasherCalls:=0}` | `if username is None or password is None: return` (the **added guard**) | R | the **changed op** modeled deeply: a missing credential abandons the check with both side-effect counts zero. NOT axiomatized. This is the discriminating clause. |
| 3 | `lookupUser loginName` | `UserModel._default_manager.get_by_natural_key(username)` | I | UNCHANGED callee; `DoesNotExist` ↔ `none`. Same `opaque` referenced identically in spec and impl; one such call ↔ `queries = 1` |
| 4 | `none =>` branch `{queries:=1, hasherCalls:=1}` | `except DoesNotExist: UserModel().set_password(password)` | I/R | on a store miss, one secret-hashing operation runs (`hasherCalls = 1`); the hasher's return is discarded, so it is modeled by its effect only |
| 5 | `passwordMatches u pw && userAllowed u` | `user.check_password(password) and self.user_can_authenticate(user)` | I | two UNCHANGED callees referenced identically in spec and impl; `passwordMatches` abstracts only the boolean outcome |
| 6 | `some u =>` branch returns `some u` / `none`, `{queries:=1, hasherCalls:=checkHashCount u pw}` | `else: if … : return user` (implicit `return None` otherwise) | I/R | on a store hit `check_password` performs its inherent hashing internally — `checkHashCount u pw` `encode()` runs (1 via `verify` ordinarily, 0 when the stored password is unusable), an UNCHANGED-callee observable referenced identically in spec and impl; principal returned iff secret matches and allowed |

No A-consumed rows: the proof discharges correctness by case analysis on the
credential-presence branches; no property of any UNCHANGED callee is assumed
(axioms region holds only `opaque` signatures; G-AX is a skip stub).
No A-reference rows: the changed op (the short-circuit guard) is modeled deeply
as control flow, not abstracted behind a model needing G-AX validation.
No changed-inexpressible op.

The discriminating clause is row 2. Post-patch, whenever the resolved login name
or the secret is absent, `problem_spec_credentialAuth` requires
`result.queries = 0 ∧ result.hasherCalls = 0`. The prepatch impl (no guard)
still issues the store query (`queries = 1`) and, when a secret was supplied,
the hasher (`hasherCalls = 1`; with an absent secret `make_password(None)` /
`check_password(None)` skip the hash, but `queries = 1` alone already violates
the spec), so its `correct_credentialAuth` cannot close on the
missing-credential branch — the G-DIFF signal, mirroring the F2P
`assertNumQueries(0)` / `hasher.calls == 0` assertions.
