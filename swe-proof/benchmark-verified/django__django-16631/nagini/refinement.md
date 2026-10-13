# refinement.md — django__django-16631

The operation-by-operation correspondence between `model.py`'s implementation
(the `session_outcome` impl, the `fallback_auth_hashes` impl, the deep
`matches_any` / `tokens_under` models, and the live `token_for_secret` axiom)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses the axiom's contract), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The session-verification site — `get_user` (`django/contrib/auth/__init__.py`)

Gold hunk (condensed):
```
- session_hash_verified = session_hash and constant_time_compare(
-     session_hash, user.get_session_auth_hash())
- if not session_hash_verified:
-     request.session.flush(); user = None
+ if not session_hash: session_hash_verified = False
+ else:
+     session_auth_hash = user.get_session_auth_hash()
+     session_hash_verified = constant_time_compare(session_hash, session_auth_hash)
+ if not session_hash_verified:
+     if session_hash and any(constant_time_compare(session_hash, fb)
+                             for fb in user.get_session_auth_fallback_hash()):
+         request.session.cycle_key(); request.session[HASH_SESSION_KEY] = session_auth_hash
+     else:
+         request.session.flush(); user = None
```

| # | model.py impl op (`session_outcome`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `session_token: List[int]`, `current_token: List[int]` | `session_hash` (`str`/`None`), `user.get_session_auth_hash()` (`str`) | R | `str` ↔ `List[int]` code points; absent/falsy `session_hash` ↔ `len == 0` (mapping.md §2). |
| A2 | `len(session_token) == 0 → return 0` | `if not session_hash: session_hash_verified = False` → falls to the `else: flush(); user=None` branch | R + I | a falsy stored hash is rejected; the empty list models the falsy value. |
| A3 | `ToSeq(session_token) == ToSeq(current_token) → return 1` | `session_hash_verified = constant_time_compare(session_hash, session_auth_hash)`; if true, no session mutation, user kept | R + A-reference | `constant_time_compare` on hex digests == byte equality (mapping.md §3.2, validated by G-AX). Outcome 1 = "kept, session untouched". |
| A4 | `matches_any(ToSeq(session_token), previous_tokens) → return 2` | `any(constant_time_compare(session_hash, fb) for fb in user.get_session_auth_fallback_hash())` ⇒ `cycle_key()` + rewrite `session[HASH_SESSION_KEY] = session_auth_hash` | R + A-reference | `matches_any` is the deep front-recursive membership over the previous-token sequence; `any(constant_time_compare(...))` is the same membership (each compare == byte equality). Outcome 2 = "kept, key cycled, stored token rewritten to current". |
| A5 | final `return 0` | `else: flush(); user = None` | I | no current and no previous match ⇒ reject. |

The discriminating content of site A — *consult the previous tokens before
flushing, and upgrade on a match* — lives in the A4 branch. `model_prepatch.py`
deletes that branch (verifies only against the current token) and **fails** the
postcondition `(Result()==2) == (... matches_any(...))`, exactly the spec
sensing the change (G-DIFF). This is what the F2P
`test_get_user_fallback_secret` observes: after rotating `SECRET_KEY` and
putting the old key in `SECRET_KEY_FALLBACKS`, `get_user` returns the user
(outcome ≠ 0) and the session key changes (outcome 2 cycles the key); then with
the fallback removed the session still verifies (outcome 2 rewrote the stored
token to the current one).

## B. The previous-token-sequence site — `base_user.py`

Gold hunk:
```
  def get_session_auth_hash(self):
+     return self._get_session_auth_hash()
+ def get_session_auth_fallback_hash(self):
+     for fallback_secret in settings.SECRET_KEY_FALLBACKS:
+         yield self._get_session_auth_hash(secret=fallback_secret)
+ def _get_session_auth_hash(self, secret=None):
      key_salt = "...get_session_auth_hash"
-     return salted_hmac(key_salt, self.password, algorithm="sha256").hexdigest()
+     return salted_hmac(key_salt, self.password, secret=secret, algorithm="sha256").hexdigest()
```

| # | model.py impl op (`fallback_auth_hashes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `password: List[int]`, `fallback_secrets: PSeq[PSeq[int]]` | `self.password` (`str`), `settings.SECRET_KEY_FALLBACKS` (iterable of `str`) | R | mapping.md §2. |
| B2 | loop yielding `token_for_secret(password, s)` for each `s` in `fallback_secrets`, in order (`result == tokens_under(...)`) | `for fallback_secret in settings.SECRET_KEY_FALLBACKS: yield self._get_session_auth_hash(secret=fallback_secret)` | R + A-consumed | the generator's per-element body is `salted_hmac(..., secret=fallback_secret, ...).hexdigest()` ≙ `token_for_secret(password, s)`; the proof consumes only the axiom's determinism. |
| B3 | `token_for_secret(password, s)` keyed by the **iterated** secret `s` | `_get_session_auth_hash(secret=fallback_secret)` ⇒ `salted_hmac(..., secret=fallback_secret, ...)` | A-consumed | the *changed* fact is that the keyed hash is re-keyed per previous secret (the missing `secret=` argument is now threaded). Captured by keying `token_for_secret` on `s`, not on `default_secret`. |

The discriminating content of site B — *each previous token is keyed by its own
previous secret, not by the active secret* — lives in B3. `model_prepatch_2.py`
keys every token on `default_secret` (the pre-patch missing-`secret` behaviour)
and **fails** the invariant `result == tokens_under(ToSeq(password),
fallback_secrets.drop(i))` (G-DIFF). Site B is the enabler of site A: without
correctly-keyed previous tokens, the `matches_any` in site A could never fire on
a genuinely rotated session.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The two operations that
genuinely *changed* are modeled **directly**: the previous-token membership /
upgrade decision (site A, deep `matches_any` over the supplied sequence) and the
per-previous-secret token sequence (site B, deep `tokens_under` fold). The only
**consumed axiom**, `token_for_secret` (**A-consumed**), is the *unchanged*
keyed-hash callee (`salted_hmac(...).hexdigest()`) both sites invoke; the only
**A-reference** is `constant_time_compare` == byte equality (site A's compare),
validated by G-AX. There is no axiom about either changed function itself.

## D. verify(model) ⇒ resolved

`session_outcome` verifies only if it returns 1 exactly on a present stored
token equal to the current token (A3), 2 exactly on a present stored token that
mismatches the current token but matches a previous token (A4), and 0 otherwise
(A2/A5). By R (str↔List[int], `constant_time_compare`==byte-equality validated
by G-AX) this is the gold `get_user` branch structure: keep-untouched / cycle+
upgrade / flush. `fallback_auth_hashes` verifies only if its output equals the
per-previous-secret token sequence (B2/B3), which by A-consumed
(`token_for_secret` == `salted_hmac(...).hexdigest()`, G-AX-checked determinism)
is exactly what the gold generator yields. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
