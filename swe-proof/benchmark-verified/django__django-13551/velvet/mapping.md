# mapping.md — django__django-13551

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7f9e4524d6b23424cf44fbe1bf1f4e70f6bb066e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee/flag provenance.

Repo file under change: `django/contrib/auth/tokens.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `makeHashInput (u : UserState) (timestamp : String)` | `PasswordResetTokenGenerator._make_hash_value(self, user, timestamp)` — `django/contrib/auth/tokens.py:79` (return at `:97`) | the modeled changed function: the string fed to `salted_hmac` to build a single-use password-reset token |
| `UserState` | the slice of the `user` model the function reads: `user.pk`, `user.password`, `user.last_login`, and the email field | structure carrying only the observed fields (mapping.md §2) |
| `emailValue (u : UserState)` | `email = getattr(user, email_field, '') or ''` — `tokens.py:96` post-patch, where `email_field = user.get_email_field_name()` (`tokens.py:95` post-patch) | the email's contribution to the input: stored address or `''` |
| `hashInput (u) (timestamp)` *(deep model — R/I)* | the concatenation `f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'` — `tokens.py:97` post-patch | pure spec: the ordered string the function returns |

Pre-patch repo symbol the change supersedes (refinement audit only, not in the
consumer spec view): the return `str(user.pk) + user.password +
str(login_timestamp) + str(timestamp)` (`tokens.py:97` @ base_commit) — the
email is absent.

The fields' string forms are computed upstream of the modeled return and are
unchanged by the patch:
- `login_timestamp` (`tokens.py:96`): `'' if user.last_login is None else
  user.last_login.replace(microsecond=0, tzinfo=None)`, then `str(...)` in the
  return. Modeled as the already-reduced string `loginTimestamp` (empty ⇔ no
  last login). UNCHANGED by the patch — identical in both legs, so it is not a
  discriminator and is carried as an opaque string.
- `user.get_email_field_name()` (`django/contrib/auth/base_user.py:144`,
  `@classmethod`): returns `cls.EMAIL_FIELD` (default `'email'` on the standard
  `User`; e.g. `'email_address'` on a custom model). The patch reads the email
  via `getattr(user, that_name, '') or ''`, so a `None`/missing/empty email all
  collapse to `''`. Modeled by `emailRaw : Option String` + `emailValue`
  (`some e ↦ e`, `none ↦ ""`). This is an UNCHANGED helper (it exists at
  base_commit); the patch only starts *calling* it. It is not axiomatized — its
  one relevant fact (present ⇒ the address, absent/null/empty ⇒ `''`) is folded
  into the `Option`/`getD ""` model and validated by G-CONF.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the returned hash input (`str`) and every field's string form | `String` | Python `str` ↔ Lean `String`; `str` concatenation (`+` / f-string juxtaposition) ↔ Lean `++`; empty `str` ↔ `""` |
| `str(user.pk)` | `UserState.pk : String` | the pk already coerced to its string form; the patch does not change how pk is stringified (f-string `{user.pk}` == `str(user.pk)` for the pk values the F2P tests use — ints / UUIDs) |
| `user.password` (`str`) | `UserState.password : String` | identity on the string |
| `str(login_timestamp)` (`tokens.py:96`) | `UserState.loginTimestamp : String` | the last-login already reduced to its stable string (`''` when `last_login is None`); unchanged by the patch, carried opaque |
| `str(timestamp)` | `timestamp : String` | the request timestamp's string form; identity on the string |
| `email = getattr(user, user.get_email_field_name(), '') or ''` | `emailRaw : Option String` via `emailValue` | a present non-empty address ↦ `some e` (`emailValue = e`); a `None`/missing/empty-string email ↦ `none` (`emailValue = ""`). The `or ''` makes `None` and `''` indistinguishable, matching `none ↦ ""`. |

f-string interpolation `f'{a}{b}{c}{d}{e}'` is exactly `str(a)+str(b)+...` for
the already-string components, i.e. Lean `a ++ b ++ c ++ d ++ e` — the
mechanical fidelity G-CONF checks.

## 3. Callee / flag provenance

No consumed axioms and no A-reference deep model of an outside callee. The only
helper read, `get_email_field_name`, is an UNCHANGED classmethod whose single
relevant behaviour (which attribute holds the address) is folded into the
`emailRaw : Option String` carrier and the `getattr(..., '') or ''` collapse;
its end-to-end effect is exercised by G-CONF, which invokes the REAL patched
`_make_hash_value` on user objects emulating both the default `User`
(`EMAIL_FIELD='email'`) and a custom email-field model
(`EMAIL_FIELD='email_address'`, possibly `None`) — the function reads only
`pk`, `password`, `last_login`, `get_email_field_name()` and the email
attribute, so a duck-typed user drives the actual patched code path. There is
therefore nothing for G-AX to check (`conf_skip=false`, `G-AX=skip`).

**Flag/branch dependency:** the email contribution depends on whether the user
has an email (`getattr(..., '') or ''`): present-and-nonempty vs
absent/None/empty. G-CONF fuzzes both — the standard `User` with and without an
email, and a custom model whose email field is `None` — so the present and the
empty branches of `emailValue` are both observed.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13551`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `hashInput`/`emailValue` (R/I-tagged ops) to Python and compares
against the patched `_make_hash_value` invoked on user objects emulating the
default `User` and a custom-email-field model, bridging values via the §2
bijection.
