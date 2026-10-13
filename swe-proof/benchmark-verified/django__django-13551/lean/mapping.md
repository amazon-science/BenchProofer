# mapping.md — django__django-13551

## Symbol binding (file:line @ base_commit 7f9e4524d6b23424cf44fbe1bf1f4e70f6bb066e)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_tokenState` / `problem_spec_tokenState` | `PasswordResetTokenGenerator._make_hash_value` (its return-value assembly) | `django/contrib/auth/tokens.py:79-97` |
| `emailPart` (pure helper) | the normalized email contribution `getattr(user, email_field, '') or ''` | `django/contrib/auth/tokens.py:96` (post-fix) |

The modeled function is `_make_hash_value`. It is the only function whose behavior
changes and the only one whose output is observed (transitively, through the HMAC
fingerprint) by the FAIL_TO_PASS test `test_token_with_different_email`
("Updating the user email address invalidates the token."). That test asserts a
token issued before an email change is rejected afterwards — which holds iff the
email participates in the hashed state string.

### What the function does (base_commit)

```python
def _make_hash_value(self, user, timestamp):
    login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
    return str(user.pk) + user.password + str(login_timestamp) + str(timestamp)
```

It returns the ordered concatenation of `str(user.pk)`, `user.password`,
`str(login_timestamp)`, and `str(timestamp)`. The string is then run through
`salted_hmac(...).hexdigest()[::2]` by the caller `_make_token_with_timestamp`;
two state strings produce the same token iff they are byte-equal. At base_commit
the email is NOT among the components, so an email change leaves the state string
(and hence the token) unchanged — the defect in the issue.

The post-fix behavior appends the user's (normalized) email address as a final
component, so any change to the email changes the state string and invalidates
the token.

### Inputs ↔ Python expression bijection

Each input models the *string value* of one already-stringified component the
function concatenates. `_make_hash_value` builds its result purely by string
concatenation, so modeling each component as the `String` it contributes is exact
for the observable (byte-level) behavior; the HMAC step downstream is an injective
fingerprint of that string and is not part of the modeled function.

| Lean input | Python expression | type | notes |
|---|---|---|---|
| `pk` | `str(user.pk)` | `String` | the user's primary key, already stringified. |
| `password` | `user.password` | `String` | the stored password representation (already a `str`). |
| `loginTs` | `str(login_timestamp)` | `String` | last-login timestamp rendered to a string; `''` when `user.last_login is None`. This rendering is unchanged by the patch and enters pre-stringified. |
| `ts` | `str(timestamp)` | `String` | the token timestamp, already stringified. |
| `emailRaw` | the email value carried by the account: `getattr(user, user.get_email_field_name(), None)`, or `None`/`''` when absent | `Option String` | `some e` when the account carries an email value `e`; `none` when it carries no value. The post-fix code normalizes a missing/falsy value to `''` via `... or ''`. |
| `emailPart emailRaw` | `getattr(user, email_field, '') or ''` | `String` | the normalized email *contribution*: the email's own characters when present, `''` when absent (`emailRaw.getD ""`). |

### result bijection

| Lean | Python | bijection |
|---|---|---|
| `result : String` (the return of `implementation_tokenState`) | the `str` returned by `_make_hash_value` | identity on the carrier; both are the ordered concatenation of the five components (post-fix). |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `str(user.pk)` | `pk : String` | identity (already a `str`). |
| `user.password` | `password : String` | identity. |
| `str(login_timestamp)` | `loginTs : String` | identity. |
| `str(timestamp)` | `ts : String` | identity. |
| account email value, possibly absent | `emailRaw : Option String` | `some e ↔ e`; `none ↔` no value / falsy (`None`, `''`). |
| `_make_hash_value(...)` return | `result : String` | identity on the concatenated string. |

`str` ↔ Lean `String`: the function operates at the value level (concatenation
only, no per-code-point logic), so `String` is the apt model (§2 cheatsheet).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — appending the
  email contribution to the concatenated state string — is modeled DEEPLY as a
  string concatenation over the component inputs, not axiomatized (SPEC_GUIDE §3:
  a deeply-modeled changed op is never axiomatized). The post-fix code introduces
  `email_field = user.get_email_field_name()` and `email = getattr(user,
  email_field, '') or ''`; these are the *email-locating I/O*, abstracted at the
  boundary into the `emailRaw : Option String` input plus the `... or ''`
  normalization captured by `emailPart`. There is no opaque callee whose contract
  the proof consumes, so `axiom_check.py` is a skip stub and G-AX skips.
- **Normalization (`... or ''`).** The post-fix code coerces a falsy email
  (`None`, `''`) to `''`. Modeled by `emailPart emailRaw := emailRaw.getD ""`:
  `none` (no value) ↦ `""`. Note the real `or ''` also coerces an empty-string
  value to `''` (a no-op) — both an absent value and an empty value contribute
  `''`, which `emailPart` reproduces (`none ↦ ""`, `some "" ↦ ""`).
- **No flag dependency.** `_make_hash_value` takes no mode flag; the `legacy`
  argument lives in the caller `_make_token_with_timestamp` and only selects the
  HMAC algorithm, not the state string. Out of scope for the modeled function.
- **`get_email_field_name()`** (`AbstractBaseUser`) returns the model's
  `EMAIL_FIELD` name (default `'email'`). It selects WHICH attribute holds the
  email; its result is folded into "the account's email value" = `emailRaw`. It
  is not an unchanged callee whose property the proof consumes — its only role is
  to pick the field whose value becomes `emailRaw`.

## G-CONF fuzz seed

Pinned LCG seed: **13551** (see `conformance_check.py` `SEED`). Corpus: random
component strings (`pk`, `password`, `loginTs`, `ts` drawn from a small alphabet,
lengths 0–6) crossed with `emailRaw ∈ {None} ∪ {random strings incl. ''}`, over
≥1e5 fuzzed inputs, diffed against an in-process replica of the post-patch
`_make_hash_value` return-string assembly (`f'{pk}{password}{loginTs}{ts}{email}'`
with `email = emailRaw or ''`).
