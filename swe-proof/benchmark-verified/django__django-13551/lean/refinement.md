# refinement.md — django__django-13551

Maps every operation in `implementation_tokenState` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `tokenState` (`PasswordResetTokenGenerator._make_hash_value`)

Post-patch repo code (`patch.diff`):
```python
def _make_hash_value(self, user, timestamp):
    login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
    email_field = user.get_email_field_name()
    email = getattr(user, email_field, '') or ''
    return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'
```

Lean impl (`implementation_tokenState`):
```lean
def implementation_tokenState
    (pk password loginTs ts : String) (emailRaw : Option String) : String :=
  Id.run do
    let email := emailPart emailRaw
    let mut s := pk
    s := s ++ password
    s := s ++ loginTs
    s := s ++ ts
    s := s ++ email
    return s
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `pk password loginTs ts : String` inputs | `str(user.pk)`, `user.password`, `str(login_timestamp)`, `str(timestamp)` | **R** | each component enters already-stringified; the function only concatenates `str`s, so modeling each as the `String` it contributes is exact (mapping.md bijection). `login_timestamp` computation (`'' if last_login is None else …`) is unchanged by the patch and pre-rendered into `loginTs`. |
| 2 | `emailRaw : Option String` input + `let email := emailPart emailRaw` | `email_field = user.get_email_field_name(); email = getattr(user, email_field, '') or ''` | **R** | the email-locating I/O (`get_email_field_name` + `getattr`) is abstracted at the boundary into `emailRaw` (the account's email value, or `none`); the `... or ''` falsy-normalization is `emailPart emailRaw := emailRaw.getD ""` (`none ↦ ""`, `some e ↦ e`). This is the changed op, modeled DEEPLY (string concatenation), not axiomatized — so no consumed callee axiom (SPEC_GUIDE §3). |
| 3 | `let mut s := pk` | first component of the f-string `{user.pk}` | **I** | initialize the state string with the pk component. |
| 4 | `s := s ++ password` | `{user.password}` | **I** | append the password component. |
| 5 | `s := s ++ loginTs` | `{login_timestamp}` | **I** | append the last-login component. |
| 6 | `s := s ++ ts` | `{timestamp}` | **I** | append the token-timestamp component. |
| 7 | `s := s ++ email` | `{email}` (the appended final component) | **I** (the fixed op) | **the fix.** The post-patch f-string appends the (normalized) email as a final component; pre-patch the concatenation stopped at `{timestamp}`. `s := s ++ email` reproduces this final append exactly. |
| 8 | `return s` | `return f'{...}'` | **I** | the function returns the assembled string. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `_make_hash_value` return-string assembly.

Refinement equivalence (R/I): the post-patch f-string `f'{a}{b}{c}{d}{e}'` is, at
the byte level, exactly `a ++ b ++ c ++ d ++ e` for already-stringified `a..e`;
the Lean impl builds the same concatenation left-to-right. The downstream HMAC
fingerprint (`salted_hmac(...).hexdigest()[::2]`) is an injective function of this
string and is not part of the modeled function — equal state strings produce
equal tokens and distinct security-relevant state strings produce distinct
tokens, which is exactly the property the F2P test depends on.

## Soundness check (verify ⟹ correct)

- `problem_spec_tokenState pk password loginTs ts emailRaw result := result =
  pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw` pins the result EXACTLY
  (full string equality to an input-grounded concatenation) — directive 5
  (frame): every output component, including the email contribution, is pinned to
  its input. No component is left unconstrained; no ungrounded oracle (directive
  8) — the postcondition is dischargeable only by actually concatenating the five
  inputs in order, so a wrong impl cannot echo an answer key.
- The prepatch impl omits `s := s ++ email`, returning `pk ++ password ++ loginTs
  ++ ts`. It violates the spec on the discriminating clause `emailPart emailRaw ≠
  ""` (any account carrying a non-empty email), where it returns a string missing
  the email suffix but the spec requires it. Its carried gold proof (`rfl`) cannot
  close (G-DIFF/G-PANEL): the LHS lacks `emailPart emailRaw`.
- This discriminating case is precisely what the FAIL_TO_PASS test
  `test_token_with_different_email` exercises: a user's email is changed
  (`'test4@example.com'` → `'test4new@example.com'`, and the `None` → value
  cases), and the test asserts a token issued before the change is rejected after
  it. With the email omitted from the state string (prepatch) the two state
  strings are byte-equal, so the old token still validates — the bug. With the
  email appended (gold) the state strings differ, so the token is invalidated.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `_make_hash_value` return-string assembly over hand-picked edge cases
  (`emailRaw = None`, `''`, and non-empty) plus ≥1e5 fuzzed component strings.
