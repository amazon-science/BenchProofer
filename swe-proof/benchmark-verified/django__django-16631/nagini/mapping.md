# mapping.md — django__django-16631

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9b224579875e30203d079cc2fee83b116d98eb78`, states the type
abstraction, and gives the provenance of the axiomatised callee.

Repo files under change:
* `django/contrib/auth/__init__.py` — the `get_user(request)` session check.
* `django/contrib/auth/base_user.py` — `AbstractBaseUser.get_session_auth_hash`
  / the new `get_session_auth_fallback_hash` / `_get_session_auth_hash`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `session_outcome(session_token, current_token, previous_tokens)` | the session-verification block of `get_user` — `django/contrib/auth/__init__.py:200-207` | modeled changed function (site A): the accept-current / accept-previous-and-upgrade / reject decision |
| `fallback_auth_hashes(password, default_secret, fallback_secrets)` | `AbstractBaseUser.get_session_auth_fallback_hash` (new) + `_get_session_auth_hash(secret=…)` (new) — `django/contrib/auth/base_user.py:139-153` (post-patch) | modeled changed function (site B): the previous-secret token sequence |
| `token_for_secret(password, secret)` *(axiom — A-consumed)* | `salted_hmac(key_salt, self.password, secret=secret, algorithm="sha256").hexdigest()` — built on `django.utils.crypto.salted_hmac` (`django/utils/crypto.py:18`) | unchanged keyed-hash callee that `_get_session_auth_hash` invokes once per secret |
| `matches_any(token, candidates)` | the `any(constant_time_compare(session_hash, fallback_auth_hash) for fallback_auth_hash in user.get_session_auth_fallback_hash())` expression — `__init__.py:212-215` (post-patch) | pure spec: stored-token membership in the previous-token sequence |
| `tokens_under(password, secrets)` | the generator body of `get_session_auth_fallback_hash` (`yield self._get_session_auth_hash(secret=fallback_secret)` over `settings.SECRET_KEY_FALLBACKS`) — `base_user.py:140-141` (post-patch) | pure spec: the per-previous-secret token sequence |

The pre-patch repo facts the change targets (for the refinement audit, not
referenced from the consumer spec view): `get_user` verified the stored hash
only against `user.get_session_auth_hash()` and flushed otherwise
(`__init__.py:202-207`, pre-patch); `get_session_auth_hash` called
`salted_hmac(key_salt, self.password, algorithm="sha256")` with **no `secret`
argument**, so it always keyed on `settings.SECRET_KEY` (`base_user.py:134-143`,
pre-patch); there was no `get_session_auth_fallback_hash`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` session hash (the `_auth_user_hash` cookie value) and the HMAC hex digests | `List[int]` / `PSeq[int]` of code points | `s[k]` ↔ `ord`; `len`; an absent/falsy `session_hash` (`request.session.get(HASH_SESSION_KEY)` → `None`/empty) ↔ the empty list `[]` (`len == 0`) |
| `str` secret (`settings.SECRET_KEY`, each `settings.SECRET_KEY_FALLBACKS` element) and the password field | `PSeq[int]` / `List[int]` of code points | identity on code points |
| `settings.SECRET_KEY_FALLBACKS` (a list/tuple of secrets) | `fallback_secrets: PSeq[PSeq[int]]` | element-wise as above; order preserved (the generator yields in order, and `any(...)` short-circuits, but membership is order-independent) |
| the generator returned by `get_session_auth_fallback_hash` | `PSeq[PSeq[int]]` materialised token sequence | the model materialises what the gold consumes lazily inside `any(...)`; `matches_any` ⇔ `any(constant_time_compare(...))` over the same tokens (R) |
| `constant_time_compare(a, b)` (`crypto.py:64`, = `secrets.compare_digest(force_bytes(a), force_bytes(b))`) | sequence equality `==` on `PSeq[int]` | for two equal-length ASCII hex digests, `compare_digest` returns `True` iff the byte strings are equal; the model uses `PSeq` `==`. Validated == the real callee by axiom_check.py (A-reference, §3.2). |
| the three branch effects (`return user` unchanged / `cycle_key()`+rewrite `session[HASH_SESSION_KEY]` / `flush()`+`user=None`) | the abstract outcome code `0/1/2` | each effect is a distinct, observable post-state; the F2P test observes the outcome via `assertIsInstance(user, User)` (kept), `assertNotEqual(session_key, prev)` (cycled), and re-validation after the fallback is removed (rewrite to current token). Modeled as the result code (R). |

`str` indexing/iteration is banned in Nagini, so tokens/secrets are `List[int]`;
the specification is phrased over `PSeq[int]` / `PSeq[PSeq[int]]` via `ToSeq`.

## 3. Callee provenance

### 3.1 `token_for_secret` ↔ `salted_hmac(...).hexdigest()` (A-consumed)
**Callee:** `django.utils.crypto.salted_hmac(key_salt, value, secret=…, algorithm="sha256")`
followed by `.hexdigest()` (`django/utils/crypto.py:18-44`). For a fixed
`key_salt` (the constant
`"django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"`) and a
fixed `value` (the user's `password`), the digest is a **deterministic pure
function of the secret**: `key = sha256(force_bytes(key_salt) + force_bytes(secret))`,
result = `hmac.new(key, msg=force_bytes(password), sha256).hexdigest()`.

The axiom states no `Ensures` at all: the proof consumes ONLY functional
determinism — equal `(password, secret)` arguments give equal tokens — which
`@Pure` supplies automatically and which any deterministic hash satisfies. This
is the weakest possible contract (strictly weaker than naming any concrete
output), so it cannot over-claim. The token-distinctness that makes rotation
observable (a token under the old secret differs from the token under the new
secret, with overwhelming probability) is NOT asserted by the axiom; it is a
property of the *inputs* the F2P test supplies, and the spec pins behaviour
purely structurally (membership / equality of the supplied tokens).

**Soundness check (G-AX):** `axiom_check.py` runs the real
`salted_hmac(...).hexdigest()` keyed exactly as `_get_session_auth_hash` keys
it (the auth key_salt, `algorithm="sha256"`, `secret=` threaded) and asserts
(a) determinism — same `(password, secret)` ⇒ identical digest across repeated
calls; (b) secret-sensitivity — distinct secrets give distinct digests on the
fuzzed inputs (the rotation premise); it never asserts an exact digest value.

### 3.2 `constant_time_compare` ↔ sequence equality (A-reference)
**Callee:** `django.utils.crypto.constant_time_compare(a, b)` =
`secrets.compare_digest(force_bytes(a), force_bytes(b))` (`crypto.py:64-66`).
On two `str` hex digests this is exactly `force_bytes(a) == force_bytes(b)`,
i.e. equality of the underlying byte strings (constant-time, but the *value*
returned is plain equality). The model uses `PSeq[int]` `==`. This is a deep,
direct model (no consumed axiom), validated == the real callee by
`axiom_check.py`: for equal and unequal hex-digest pairs,
`constant_time_compare(a, b) == (a == b)`.

`settings.SECRET_KEY_FALLBACKS` is a documented setting (Django 4.1+); the auth
key_salt and `algorithm="sha256"` are the fixed arguments of
`get_session_auth_hash`. Docs:
https://docs.djangoproject.com/en/stable/ref/settings/#secret-key-fallbacks .
