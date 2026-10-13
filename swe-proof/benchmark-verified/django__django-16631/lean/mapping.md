# mapping.md — symbol binding & type bijection (django__django-16631)

## Modeled function
- **Lean** `implementation_validateToken : List Char → List Char → List (List Char) → VerifyDecision`
- **Python** the session-token verification DECISION inside
  `get_user(request)` — `django/contrib/auth/__init__.py:198-208 @ base_commit`
  (the `if hasattr(user, "get_session_auth_hash"):` body), together with the
  fallback-token producer
  `AbstractBaseUser.get_session_auth_fallback_hash` /
  `_get_session_auth_hash` added in
  `django/contrib/auth/base_user.py:136-153 @ patched`.

### What the code does
`get_user` has already loaded a candidate user from the session backend. It then
verifies the session by comparing the stored `_auth_user_hash`
(`session_hash = request.session.get(HASH_SESSION_KEY)`) against the hash derived
from the user's password under the *current* secret
(`user.get_session_auth_hash()`).

Pre-patch:
```python
session_hash = request.session.get(HASH_SESSION_KEY)
session_hash_verified = session_hash and constant_time_compare(
    session_hash, user.get_session_auth_hash()
)
if not session_hash_verified:
    request.session.flush()      # clears the session state
    user = None                  # request becomes AnonymousUser
```

Post-patch: if the current-secret hash does not verify, the code tries the hashes
derived under each fallback secret
(`user.get_session_auth_fallback_hash()` yields one hash per
`settings.SECRET_KEY_FALLBACKS`). If any fallback hash matches the stored hash
the user is kept (with the session state refreshed — see "Effect glue" below);
otherwise it flushes and drops the user as before.

### The modeled decision (modeling boundary)
The fix is a pure three-way classification over three opaque token values:
- the stored token (`session_hash`),
- the current-secret token (`session_auth_hash = user.get_session_auth_hash()`),
- the sequence of fallback-secret tokens
  (`user.get_session_auth_fallback_hash()`).

`implementation_validateToken` models exactly this classification, returned as a
`VerifyDecision`:
- `.rejected` ↔ the flush-and-drop path is taken (`request.session.flush()`,
  `user = None`);
- `.acceptedCurrent` ↔ the stored token verified against the current-secret
  token: the block is a no-op (user and session untouched);
- `.acceptedAlternate` ↔ the stored token verified against a fallback-secret
  token: the user is kept and the fallback-acceptance path is taken.

### Effect glue (OUTSIDE the modeled slice; fixed by the refinement)
What `get_user` *does* on each decision is unmodeled glue, held fixed by the
refinement (refinement.md): `.rejected` ⇒ `flush()` + `user = None`;
`.acceptedCurrent` ⇒ no state change; `.acceptedAlternate` ⇒ user kept and the
gold patch's fallback-acceptance body runs verbatim
(`request.session.cycle_key()`;
`request.session[HASH_SESSION_KEY] = session_auth_hash`). A refined patch is
*faithful* only if it attaches each decision to exactly this glue — the same
convention as the nagini twin of this instance (outcomes 0/1/2 with the
per-outcome session effects fixed by the refinement, not free choices of the
implementation). The spec region intentionally does not describe the glue: it is
derivable only from hints_text/gold and disclosing it would leak (see the
G-PANEL-3 history of this bundle).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `session_hash` (a hex digest str, or `None`/empty when absent) | `storedToken : List Char` | per-character; the empty list models a missing/falsy session hash |
| `session_auth_hash = user.get_session_auth_hash()` (current-secret hex digest) | `currentToken : List Char` | per-character |
| `[h for h in user.get_session_auth_fallback_hash()]` (one digest per fallback secret) | `alternateTokens : List (List Char)` | order preserved; one entry per `SECRET_KEY_FALLBACKS` element |
| `constant_time_compare(a, b)` | `a == b` (list equality) | constant-time string equality ⟺ value equality; modeled as an **I** op |
| flush-and-drop path taken | `.rejected` | ⟺ `request.session.flush(); user = None` |
| verified against current token (block no-op) | `.acceptedCurrent` | user/session untouched |
| fallback-acceptance path taken (user kept) | `.acceptedAlternate` | the gold glue runs on this path (see "Effect glue") |

## Callee provenance
- `constant_time_compare(stored, candidate)` (`django.utils.crypto`) — UNCHANGED
  by the patch; a timing-safe equality test. Its observable result is exactly
  value equality of the two byte/str arguments, so it is reproduced concretely as
  list equality (`==`), an **I**-tagged op. No `opaque`/axiom needed.
- `user.get_session_auth_hash()` and `get_session_auth_fallback_hash()` produce
  the token values; in the model these are the *inputs* `currentToken` and
  `alternateTokens`. They are opaque to this decision (their internal HMAC
  computation is not part of the modeled control flow), so they are not callees of
  the modeled function — they supply its inputs.
- `request.session.flush()` / `cycle_key()` / `__setitem__` are state effects of
  the surrounding glue, not operations of the modeled decision; the decision
  selects which glue path runs (see "Effect glue").
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub.

## Flag / configuration dependency
`get_session_auth_fallback_hash()` iterates `settings.SECRET_KEY_FALLBACKS`; when
that setting is empty, `alternateTokens = []` and the post-patch behavior reduces
to the pre-patch behavior (mismatch ⇒ the rejected path). G-CONF fuzzes both the
empty and non-empty alternate-list cases, and inputs where the stored token
does/does not appear among the alternates.

## Scope note
The surrounding `get_user` logic (loading the backend, `_get_user_session_key`,
the `KeyError`/backend-membership guards, the final
`return user or AnonymousUser()`) is unchanged by the patch and orthogonal to the
fix; only the verification decision is modeled. The HMAC derivation in
`_get_session_auth_hash` (the `secret=` plumbing) is what *produces* the token
values; it is captured by treating those values as inputs, and is not re-derived.

## G-CONF fuzz seed
Pinned seed: **16631**. ≥10^5 fuzzed inputs over token alphabets, both empty and
non-empty alternate lists, and cases where the stored token equals the current
token, equals an alternate, or matches neither.
