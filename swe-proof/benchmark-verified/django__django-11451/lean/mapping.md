# mapping.md — symbol binding & type bijection (django__django-11451)

## Modeled function
- **Lean** `implementation_credentialAuth :
  Option (List Char) → Option (List Char) → Option (List Char) → AuthOutcome`
- **Python** `ModelBackend.authenticate(self, request, username=None, password=None, **kwargs)`
  — `django/contrib/auth/backends.py:39-50 @ base_commit`.

The method resolves the username (falling back to the keyword argument named by
`UserModel.USERNAME_FIELD` when the positional one is absent), then — in the
patched code — short-circuits with a bare `return` (i.e. returns `None`) when
either the resolved username or the password is absent, *before* touching the
database or the password hasher. Only when both are present does it query the
user store and, depending on the outcome, run the password hasher and/or the
password check.

```python
def authenticate(self, request, username=None, password=None, **kwargs):
    if username is None:
        username = kwargs.get(UserModel.USERNAME_FIELD)
    if username is None or password is None:      # patched guard
        return
    try:
        user = UserModel._default_manager.get_by_natural_key(username)
    except UserModel.DoesNotExist:
        UserModel().set_password(password)        # hasher run once (#20760)
    else:
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
```

## The observable behavior demanded
The F2P tests `test_authentication_without_credentials` assert, for each of
`{}`, `{username}`, `{password}`:
- `assertNumQueries(0)` — **no database query is performed**, and
- `CountingMD5PasswordHasher.calls == 0` — **the password hasher is not run**.

Pre-patch, the missing-credential inputs reach `get_by_natural_key(None)`
(emitting `... WHERE username IS NULL`, i.e. one query) and, on the resulting
`DoesNotExist`, `set_password` (one hasher call, when a password was supplied —
`make_password(None)` builds an unusable password without invoking the hasher).
The fix drops both side effects to zero. We therefore model the outcome as a
record that carries, beside the returned user, the **number of store queries**
and **number of hasher invocations** performed — the two side effects the tests
observe.

The hasher counter (`CountingMD5PasswordHasher.calls`) counts `encode()`
invocations, and — per the PASS_TO_PASS `test_authentication_timing` ("Hasher
is run once regardless of whether the user exists") — it is also incremented on
the **store-hit** path: `check_password → hashers.check_password →
hasher.verify → self.encode`. However the hit-path count is not a constant 1:
`hashers.check_password` short-circuits (`if password is None or not
is_password_usable(encoded): return False`, hashers.py @ base_commit) **before**
`hasher.verify` when the stored password is unusable, giving 0 encodes. The
hit-path count is a fixed property of the UNCHANGED `check_password` callee
(determined by the stored password's state), so it is modeled as the opaque
`checkHashCount : User → List Char → Nat` — referenced identically in spec and
impl, exactly like the boolean `passwordMatches`. The spec demands: miss →
`hasherCalls = 1` (the #20760 `set_password` run); hit → `hasherCalls =
checkHashCount u pw`; missing credential → `queries = 0 ∧ hasherCalls = 0`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `username` (`str` or `None`) | `username : Option (List Char)` | positional credential; `None ↔ none` |
| `password` (`str` or `None`) | `password : Option (List Char)` | secret credential; `None ↔ none` |
| `kwargs.get(UserModel.USERNAME_FIELD)` (`str` or `None`) | `kwargsUsername : Option (List Char)` | the keyword fallback the resolution step reads |
| returned `User` or `None` | `result.user : Option User` | identity of the authenticated user, if any |
| number of `_default_manager.get_by_natural_key` calls | `result.queries : Nat` | a store query == one DB query (`assertNumQueries`) |
| number of hasher `encode()` runs (`set_password` on a miss; `check_password`'s internal cost on a hit) | `result.hasherCalls : Nat` | the `CountingMD5PasswordHasher.calls` counter |
| `User` row | `User` (a `structure` with an opaque identity `uid`) | rich object; only identity is observed |

## Callee provenance (UNCHANGED callees the fix uses)
All three are UNCHANGED by the patch and appear **identically** in spec and impl;
each is declared `opaque` (signature only) and is NOT given any `_prop` axiom —
the proof discharges correctness by case analysis without assuming any property
of them, so none is consumed (G-AX is a skip stub). They are renamed to neutral
behavior-describing identifiers per the no-leakage directive.

| Lean opaque | Python callee | provenance @ base_commit | tag |
|---|---|---|---|
| `lookupUser : List Char → Option User` | `UserModel._default_manager.get_by_natural_key(username)` (raises `DoesNotExist` ↔ returns `none`) | `backends.py:43` | used identically in spec+impl (I) |
| `passwordMatches : User → List Char → Bool` | `user.check_password(password)` (its boolean result) | `backends.py:49` | used identically (I) |
| `userAllowed : User → Bool` | `self.user_can_authenticate(user)` | `backends.py:49,52-58` | used identically (I) |
| `checkHashCount : User → List Char → Nat` | number of hasher `encode()` runs `user.check_password(password)` performs internally (0 if the stored password is unusable — `hashers.check_password` short-circuits before `hasher.verify`; else 1 from `verify → encode`; MD5's `must_update` is False so `harden_runtime` never runs) | `hashers.py:check_password` @ base_commit | used identically (I) |

The miss-path hasher run `UserModel().set_password(password)` (`backends.py:47`,
return discarded) is modeled only by its **effect** — it increments
`hasherCalls` by 1. The hit-path hashing is a fixed cost of the UNCHANGED
`check_password` callee, so it is modeled as the second opaque observable of
that callee (`checkHashCount`), alongside its boolean result
(`passwordMatches`).

## Flag / resolution dependency
The username-resolution step (`if username is None: username = kwargs.get(...)`)
is pre-existing and unchanged; it is modeled faithfully as
`resolved = if username.isNone then kwargsUsername else username`. G-CONF fuzzes
all four `None`/present combinations of (`username`, `kwargsUsername`,
`password`) plus random lookup/check oracles.

## Scope note
`request` is unused by the body and not modeled. The `**kwargs` dict is modeled
only through the single value the resolution step reads
(`kwargs.get(UserModel.USERNAME_FIELD)`), since no other key affects the
modeled behavior.

## G-CONF fuzz seed
Pinned seed: **11451**. ≥10⁵ fuzzed inputs over the four credential-presence
combinations and randomized callee oracles (lookup table, password-match,
active-allowed).
