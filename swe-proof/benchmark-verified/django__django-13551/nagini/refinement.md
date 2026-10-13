# refinement.md — django__django-13551

The operation-by-operation correspondence between `model.py`'s implementation
(the `make_hash_value` impl region plus the deep `effective_address` /
concatenation model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee/construction by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fingerprint site — `_make_hash_value()` (`django/contrib/auth/tokens.py:79`)

Gold hunk (the behavioural hunk; the docstring hunk above it is comment-only):
```
- return str(user.pk) + user.password + str(login_timestamp) + str(timestamp)
+ email_field = user.get_email_field_name()
+ email = getattr(user, email_field, '') or ''
+ return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'
```

| # | model.py impl op (`make_hash_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `user: Account` with `pk`, `password`, `login_repr`, `address: Optional[List[int]]` | the `user` (`AbstractBaseUser`) argument; fields `user.pk`, `user.password`, `login_timestamp`, the contact attribute | R | each `str` field ↔ `List[int]` code points; the contact attribute ↔ `Optional[List[int]]` (mapping.md §1, §2). |
| A2 | `timestamp: List[int]` | the `timestamp` argument (`str(timestamp)` in the body) | R | `str` ↔ `List[int]` (mapping.md §2); the model takes the already-rendered timestamp sequence. |
| A3 | loops appending `pk`, then `password`, then `login_repr`, then `timestamp` into `result` (first four loops) | `f'{user.pk}{user.password}{login_timestamp}{timestamp}…'` (the four leading interpolations) | R + I | f-string interpolation of already-`str` values is left-to-right concatenation; `str` `+` ↔ list `+` element-wise; the four-component prefix is identical between pre- and post-patch and is the unchanged part of the hunk. |
| A4 | resolve the email: `addr = user.address`; the email contributes `effective_address(addr)` — `[]` when `addr is None` or empty, else `addr` — appended as the final loop | `email_field = user.get_email_field_name(); email = getattr(user, email_field, '') or ''` then the `…{email}` interpolation | A-reference | the changed string operation is modelled **deeply**: `effective_address` + the trailing concatenation ARE the email resolution and append. There is no consumed axiom. The deep model is validated **== the real construction** out-of-band: G-AX (axiom_check.py) reconstructs `get_email_field_name` + `getattr(..., '') or ''` + the f-string and asserts equality at the code-point level (mapping.md §3.1). `get_email_field_name` only selects WHICH attribute is read; `getattr(..., '') or ''` coerces a falsy (`None`/`''`) contact value to `''`. |
| A5 | `result` returned (a `List[int]`) | the `f'…'` return value (a `str`) | R | `str` ↔ `List[int]` code points; the returned fingerprint feeds `salted_hmac` (`tokens.py:68`, unchanged) which observes only the character content. |

The discriminating content of the change — the email is now part of the
fingerprint — lives in the trailing `effective_address(user.address)` segment of
the postcondition `ToSeq(Result()) == ToSeq(pk) + … + ToSeq(timestamp) +
effective_address(user.address)` and the redundant trailing-segment clause
`ToSeq(Result()).drop(prefix_len) == effective_address(user.address)`. The
pre-patch body returned only the four-component concatenation;
`model_prepatch.py` reproduces that (it never folds in the address) and **fails**
that postcondition whenever the resolved address is non-empty — exactly the spec
sensing the change (G-DIFF). This is the behaviour the F2P test
`test_token_with_different_email` exercises (a token minted before an email
change is rejected after it).

## B. The docstring hunk — comment-only

The first gold hunk rewrites the `_make_hash_value` docstring ("Hash the user's
primary key, **email (if available)**, and some user state…"). It is a
documentation-only edit with no executable effect; it has no model
counterpart and no F2P observation. (The model docstring, per G-LEAK, describes
the abstract behaviour without quoting this hunk or naming the patched symbol.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — incorporating the email into the fingerprint — is modelled
**deeply** (`effective_address` + the trailing concatenation, step A4, an
**A-reference**), not hidden behind an axiom about the function under change:
there is **no consumed `@ContractOnly` axiom** in this bundle. `get_email_field_name`
and `getattr` are folded into the email-value resolution (their only effect is
which string is read), validated as part of the A-reference by G-AX.

## D. verify(model) ⇒ resolved

`make_hash_value` verifies only if its output equals the exact five-component
concatenation with the resolved email as the trailing segment (A4). By R
(`str` ↔ `List[int]`, f-string ↔ concatenation, `salted_hmac` observes only the
content) the verified fingerprint equals
`f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'` on the tested
inputs; by G-AX the deep model `effective_address` + concatenation equals the
real `getattr(..., '') or ''` + f-string construction (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited deep model — and the gold patch resolves
(G-RESOLVE). The trust points reduce to the single one of PLAN §1.1 applicable
here: refinement fidelity (this document, G-EQ) plus the A-reference soundness
check (G-AX); there is no consumed-axiom trust point.
