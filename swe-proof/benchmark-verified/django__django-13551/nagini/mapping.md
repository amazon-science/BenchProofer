# mapping.md — django__django-13551

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7f9e4524d6b23424cf44fbe1bf1f4e70f6bb066e`, states the type
abstraction, and gives the provenance of the (unchanged) callee the deep model
is validated against.

Repo file under change: `django/contrib/auth/tokens.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `make_hash_value(user, timestamp)` | `PasswordResetTokenGenerator._make_hash_value(self, user, timestamp)` — `django/contrib/auth/tokens.py:79` (body line 97) | the modeled changed function (the reset-token fingerprint) |
| `Account` (fields `pk`, `password`, `login_repr`, `address`) | the `user` argument — an `AbstractBaseUser` instance; fields read are `user.pk`, `user.password`, `str(login_timestamp)` (derived from `user.last_login`), and `getattr(user, user.get_email_field_name(), '')` | minimal object exposing only the four touched user fields |
| `Account.address` *(Optional[List[int]])* | the contact-email attribute, resolved via `user.get_email_field_name()` then `getattr(user, email_field, '') or ''` — `tokens.py:97-98` post-patch | the newly-incorporated component |
| `timestamp` | the `timestamp` argument (`str(timestamp)` in the body) | the issuing instant component |
| `effective_address(addr)` *(deep model — A-reference)* | `getattr(user, user.get_email_field_name(), '') or ''` (`tokens.py:97`, plus `AbstractBaseUser.get_email_field_name`, `django/contrib/auth/base_user.py:143`) | pure spec: the email's contribution, '' when absent/None/empty; validated == the real coercion by axiom_check.py (G-AX), NOT consumed as an axiom |
| `make_hash_value`'s concatenation postcondition *(deep model — A-reference)* | `f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'` (`tokens.py:98` post-patch) | pure spec: the fingerprint is the in-order concatenation of the five components, the email last |

The pre-patch repo body the change replaces (for the refinement audit, not
referenced from the consumer spec view):
`return str(user.pk) + user.password + str(login_timestamp) + str(timestamp)`
(`tokens.py:97` @ base_commit) — the four-component concatenation with NO email.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| each `str` component (`str(user.pk)`, `user.password`, `str(login_timestamp)`, `str(timestamp)`, the email `str`) | `List[int]` of Unicode code points | `s[k]` ↔ `comp[k] == ord(s[k])`; `len(s)` ↔ `len(comp)`; `str` concatenation / f-string interpolation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the f-string `f'{a}{b}{c}{d}{e}'` (`tokens.py:98`) | `ToSeq(a) + ToSeq(b) + ToSeq(c) + ToSeq(d) + ToSeq(e)` | each `{x}` interpolates the already-`str` component; `str.__format__` with no spec is identity on a `str`, so the f-string is exactly the 5-way concatenation |
| `getattr(user, field, '') or ''` (`tokens.py:97`) | `effective_address(addr)`: `[]` when `addr is None` or `len(addr)==0`, else `addr` | a falsy contact value (`None` or `''`) becomes `''`; a non-empty `str` is itself. `Optional[List[int]]`: `None` ↔ a missing/None attribute; `[]` ↔ `''` |
| `user.get_email_field_name()` (`base_user.py:143`) | folded into the resolution of `address` | returns `EMAIL_FIELD` (e.g. `'email_address'`) or falls back to `'email'`; selects WHICH attribute is read. Observationally its only effect is which string `getattr` returns, which is the `address` value the model already takes as input |

`str` indexing/iteration is banned in Nagini, so each component is a `List[int]`
carrier; the specification is phrased over `PSeq[int]` via `ToSeq`.

`str(user.pk)`, `str(login_timestamp)`, `str(timestamp)` coercions and the
microsecond-truncation of `login_timestamp` (`tokens.py:96`) are unchanged by
the patch and produce the four leading components; the model takes the
already-rendered component sequences as input. The patch's only behavioural
delta is the appended fifth component (`email`), so the model's discriminating
content is the trailing `effective_address` segment.

## 3. Callee provenance (the A-reference checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom** in this bundle: the changed
operation is pure string concatenation over the user's own fields plus the
`getattr(..., '') or ''` coercion, which Nagini expresses directly as a
`List[int]` concatenation and an `Optional`-guard. So the entire derivation is
modelled **deeply** and validated against the real construction out-of-band.

### 3.1 `effective_address` + concatenation ↔ gold `_make_hash_value` (A-reference)
**Callee / construction:** the gold patch body
```python
email_field = user.get_email_field_name()
email = getattr(user, email_field, '') or ''
return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'
```
(`django/contrib/auth/tokens.py:97-98` post-patch) together with
`AbstractBaseUser.get_email_field_name` (`base_user.py:143`, returns
`EMAIL_FIELD` or `'email'`).

The deep model encodes:
- `effective_address(addr)`: `''` for an absent/None/empty contact value,
  otherwise the value itself — exactly `getattr(user, email_field, '') or ''`
  (a falsy `None`/`''` yields `''`).
- the fingerprint = `pk ++ password ++ login_timestamp ++ timestamp ++ email`
  — exactly the f-string, since `str.__format__('')` is identity on a `str` and
  f-string interpolation is left-to-right concatenation.

**Soundness check (G-AX):** `axiom_check.py` reconstructs the real derivation
faithfully (the `get_email_field_name` `EMAIL_FIELD`/`'email'` fallback, the
`getattr(..., '') or ''` coercion, and the f-string) and asserts, at the
code-point level: (a) `derived_value` deep model == the real fingerprint; (b)
the trailing segment after the four fixed components equals the resolved email
(asserted on the REAL output — no double-mask through a model-decided
predicate); (c) the email-change discriminator the F2P test demands (changing
only the email changes the fingerprint whenever the resolved email differs).
10 boundary cases (None / '' / missing-attr / renamed `EMAIL_FIELD` /
non-ASCII / empty components) + 20 000 randomized fuzz inputs, 0 mismatches,
exit 0. Imports only the standard library — the real construction is plain
Python `getattr` + f-string formatting, reproduced faithfully.

The discriminating behaviour the F2P test `test_token_with_different_email`
observes — a token issued before an email change must be rejected afterwards —
is exactly clause (c): the email is part of the fingerprint, so a different
resolved email yields a different fingerprint, hence a non-matching token. The
pre-patch body omits the email entirely (four-component concatenation), so the
fingerprint is invariant under email changes — which `model_prepatch.py`
reproduces and which fails the spec's trailing-concatenation postcondition.
