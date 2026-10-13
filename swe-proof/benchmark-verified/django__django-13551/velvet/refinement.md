# refinement.md — django__django-13551

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`makeHashInput` `do` block and the deep `hashInput`/`emailValue` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs. Claim: any impl verifying against this frozen spec,
refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The hash-input site — `_make_hash_value()` (`django/contrib/auth/tokens.py:97`)

Gold hunk (return expression):
```
- return str(user.pk) + user.password + str(login_timestamp) + str(timestamp)
+ email_field = user.get_email_field_name()
+ email = getattr(user, email_field, '') or ''
+ return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'
```
(The docstring edit in the first hunk is prose only — no behaviour.)

| # | Solution.lean impl op (`makeHashInput`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `u : UserState` | the `user` argument (its read fields `pk`, `password`, `last_login`, email) | R | the rich `user` model ↦ a structure of only the observed string fields (mapping.md §2). |
| A2 | param `timestamp : String` | `timestamp` argument (used as `str(timestamp)`) | R | the timestamp's string form ↔ Lean `String` (mapping.md §2). |
| A3 | `u.pk ++ u.password ++ u.loginTimestamp ++ timestamp` | `f'{user.pk}{user.password}{login_timestamp}{timestamp}…'` (the unchanged prefix; pre-patch `str(user.pk)+user.password+str(login_timestamp)+str(timestamp)`) | I + R | the ordered concatenation of the four durable fields is identical (concrete `++`, transliterated by G-CONF); each field's string form is the R-refined carrier of mapping.md §2. The patch switches `+`-concat of `str(...)` to an f-string but the produced string is identical for already-string components. |
| A4 | `let email := u.emailRaw.getD ""` then `... ++ email` | `email_field = user.get_email_field_name(); email = getattr(user, email_field, '') or ''` then `…{email}` | I + R | the email's contribution: present non-empty address ↦ itself, absent/None/empty ↦ `''`. `emailRaw : Option String` with `getD ""` is the R-carrier of `getattr(user, …, '') or ''` (mapping.md §2); the append is concrete `++` (I). `get_email_field_name` is an unchanged helper folded into the carrier, NOT an axiom. |
| A5 | `out` returned (`String`) | the returned `str` fed to `salted_hmac` | R | identity on the string; the token's behaviour is a deterministic function of this input (the F2P test toggles only the email and observes a token change). |

Discriminating content of the change — the email is folded into the input, so
two user states differing only in email produce **different** inputs — lives in
the trailing `++ emailValue u` of `hashInput`. The pre-patch return omits it;
`Solution_prepatch.lean` reproduces that and **fails** `out = hashInput u
timestamp` precisely on the goal `… = … ++ u.emailRaw.getD ""` (G-DIFF).

## B. No second site

The patch touches one function (`_make_hash_value`) and a prose docstring; there
is one independently-observable behavioural change (email-in-input). A single
prepatch covers it.

## C. No kind-A, no kind-3

There are **no consumed axioms** and **no A-reference deep models of outside
callees**. The one helper read by the patch — `get_email_field_name` (an
unchanged classmethod) — is not axiomatized: its only relevant behaviour (which
attribute holds the email, and the `… or ''` collapse of null/empty to empty) is
folded into the `emailRaw : Option String` carrier and validated end-to-end by
G-CONF against real Django user objects. Every step is R or I. No operation that
genuinely changed is inexpressible: the change is a string append, modeled
concretely.

## D. verify(Solution) ⇒ resolved

`makeHashInput` verifies only if its output equals `hashInput u timestamp` —
the four durable fields concatenated in order **followed by the email** (A3+A4).
By R (the field-string and `Option`-email bijections of mapping.md §2) the
verified input equals the gold f-string `f'{user.pk}{user.password}
{login_timestamp}{timestamp}{email}'` on the tested user objects; by G-CONF the
R/I transliteration agrees with the patched `_make_hash_value` on ≥10⁵ inputs
spanning present / absent / empty email and the custom email-field model.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The lone
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom
trust point (G-AX skipped).
