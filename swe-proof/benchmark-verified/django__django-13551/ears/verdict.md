# P2 adversarial audit — django__django-13551

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1 (POSITIVE CONTROL): changing email invalidates outstanding token.
HOLDS iff check_token returns False after email changed to a different value."""
import django
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class U:
    pk = 1
    password = 'pw-hash'
    last_login = None
    email = 'old@example.com'
    def get_email_field_name(self):
        return 'email'


g = PasswordResetTokenGenerator()
u = U()
tok = g.make_token(u)
u.email = 'new@example.com'
res = g.check_token(u, tok)
print("check_token after email change =", res)
import sys
sys.exit(0 if res is False else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 / Req3.1: token stays valid when nothing (incl. email) changes."""
import django, sys
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class U:
    pk = 1
    password = 'pw-hash'
    last_login = None
    email = 'stable@example.com'
    def get_email_field_name(self):
        return 'email'


g = PasswordResetTokenGenerator()
u = U()
tok = g.make_token(u)
res = g.check_token(u, tok)
print("check_token unchanged =", res)
sys.exit(0 if res is True else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4 + Req1.3: email read via get_email_field_name() (custom name), and
two states differing only in email produce different tokens.
HOLDS iff (a) a differently-named email field is honored (changing it
invalidates the token) and (b) two users differing only in that email give
different tokens at the same timestamp."""
import django, sys
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class U:
    pk = 7
    password = 'pw'
    last_login = None
    primary_email = 'a@x.com'   # NOT named "email"
    email = 'DECOY-should-be-ignored'
    def get_email_field_name(self):
        return 'primary_email'


g = PasswordResetTokenGenerator()
ts = 1000000

u1 = U()
h1 = g._make_hash_value(u1, ts)
u2 = U(); u2.primary_email = 'b@x.com'
h2 = g._make_hash_value(u2, ts)
# decoy: changing the literal "email" attr must NOT change the hash
u3 = U(); u3.email = 'anything-else'
h3 = g._make_hash_value(u3, ts)

print("h1==h2 (diff primary_email):", h1 == h2)
print("h1==h3 (diff decoy email):", h1 == h3)
ok = (h1 != h2) and (h1 == h3)

# token invalidation via the custom field
u = U()
tok = g.make_token(u)
u.primary_email = 'changed@x.com'
res = g.check_token(u, tok)
print("check_token after primary_email change:", res)
ok = ok and (res is False)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1 / 2.2 / 2.3 / 2.4: users without email supported.
- no email attribute at all: _make_hash_value does not raise (treat as empty)
- email None: no raise, treated as empty
- empty/absent email unchanged: check_token True
- empty/absent -> non-empty: check_token False"""
import django, sys
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator

g = PasswordResetTokenGenerator()
ts = 1000000
ok = True


class NoEmail:
    pk = 1
    password = 'pw'
    last_login = None
    def get_email_field_name(self):
        return 'email'   # attribute does not exist


class NoneEmail:
    pk = 1
    password = 'pw'
    last_login = None
    email = None
    def get_email_field_name(self):
        return 'email'


# 2.1 no attribute -> no raise
try:
    h_missing = g._make_hash_value(NoEmail(), ts)
    print("no-attr hash produced OK")
except Exception as e:
    print("no-attr RAISED:", repr(e)); ok = False

# 2.2 None -> no raise
try:
    h_none = g._make_hash_value(NoneEmail(), ts)
    print("None-email hash produced OK")
except Exception as e:
    print("None-email RAISED:", repr(e)); ok = False

# missing and None should both behave as empty -> equal hashes
if ok:
    print("missing==None hash (both empty):", h_missing == h_none)
    ok = ok and (h_missing == h_none)

# 2.3 empty/absent unchanged -> True
u = NoEmail()
tok = g.make_token(u)
r_same = g.check_token(u, tok)
print("check_token empty-unchanged:", r_same)
ok = ok and (r_same is True)

# 2.4 empty/absent -> set non-empty -> False
class Settable:
    pk = 1
    password = 'pw'
    last_login = None
    def get_email_field_name(self):
        return 'email'

u2 = Settable()
tok2 = g.make_token(u2)   # no email attribute
u2.email = 'now@present.com'
r_changed = g.check_token(u2, tok2)
print("check_token empty->nonempty:", r_changed)
ok = ok and (r_changed is False)

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2/3.3/3.4/3.6: preserved behaviors.
- password change -> check_token False
- None user or None/empty token -> False
- secret: same secret validates, different secret rejects
- reloaded identical user at same timestamp -> equal & mutually acceptable"""
import django, sys
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator

ok = True


def mkuser(pw='pw', email='e@x.com'):
    class U:
        pk = 3
        password = pw
        last_login = None
        def get_email_field_name(self):
            return 'email'
    u = U(); u.email = email
    return u


g = PasswordResetTokenGenerator()

# 3.2 password change -> False
u = mkuser()
tok = g.make_token(u)
u.password = 'newpwhash'
r = g.check_token(u, tok)
print("password-change:", r); ok = ok and (r is False)

# 3.3 None user / None token / empty token -> False
u = mkuser()
tok = g.make_token(u)
print("None user:", g.check_token(None, tok))
print("None token:", g.check_token(u, None))
print("empty token:", g.check_token(u, ''))
ok = ok and (g.check_token(None, tok) is False)
ok = ok and (g.check_token(u, None) is False)
ok = ok and (g.check_token(u, '') is False)

# 3.4 secret behavior
class GenA(PasswordResetTokenGenerator):
    secret = 'secretA'
class GenB(PasswordResetTokenGenerator):
    secret = 'secretB'
ga, gb = GenA(), GenB()
u = mkuser()
toka = ga.make_token(u)
same = ga.check_token(u, toka)
diff = gb.check_token(u, toka)
print("same-secret accepts:", same, "diff-secret rejects:", diff)
ok = ok and (same is True) and (diff is False)

# 3.6 reloaded identical user, same timestamp -> equal tokens, mutually acceptable
u1 = mkuser(); u2 = mkuser()
ts = g._num_seconds(g._now())
t1 = g._make_token_with_timestamp(u1, ts)
t2 = g._make_token_with_timestamp(u2, ts)
print("equal-state tokens equal:", t1 == t2)
ok = ok and (t1 == t2) and (g.check_token(u2, t1) is True)

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.5: legacy sha1 token continues to validate under legacy path.
A token created with the legacy sha1 algorithm must still be accepted by
check_token (which retries with legacy=True)."""
import django, sys
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator

g = PasswordResetTokenGenerator()


class U:
    pk = 9
    password = 'pw'
    last_login = None
    email = 'legacy@x.com'
    def get_email_field_name(self):
        return 'email'


u = U()
ts = g._num_seconds(g._now())
legacy_tok = g._make_token_with_timestamp(u, ts, legacy=True)
res = g.check_token(u, legacy_tok)
print("legacy sha1 token accepted:", res)

# also default-algorithm round trip
default_tok = g.make_token(u)
res2 = g.check_token(u, default_tok)
print("default-algorithm round trip:", res2)

sys.exit(0 if (res is True and res2 is True) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (POSITIVE CONTROL): changing email invalidates outstanding token.
HOLDS iff check_token returns False after email changed to a different value."""
import django
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class U:
    pk = 1
    password = 'pw-hash'
    last_login = None
    email = 'old@example.com'
    def get_email_field_name(self):
        return 'email'


g = PasswordResetTokenGenerator()
u = U()
tok = g.make_token(u)
u.email = 'new@example.com'
res = g.check_token(u, tok)
print("check_token after email change =", res)
import sys
sys.exit(0 if res is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-13551: password reset token must depend on the user's email, read via get_email_field_name(), invalidating outstanding tokens on email change while preserving all prior behavior.

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): email change -> check_token False. HOLDS patched, VIOLATED at base (returned True) => discriminates, prepatch reproduced.
- probe_2 (Req1.2/3.1): unchanged email -> check_token True. HOLDS.
- probe_3 (Req1.3/1.4): email read via get_email_field_name() custom name 'primary_email' (literal 'email' attr is a decoy); differing primary_email -> different hash, differing decoy -> same hash; token invalidated on primary_email change. HOLDS patched; VIOLATED at base.
- probe_4 (Req2.1-2.4): no email attribute and None email both produce hash without raising and equal (empty); empty-unchanged -> True; empty->non-empty -> False. HOLDS.
- probe_5 (Req3.2/3.3/3.4/3.6): password change -> False; None user / None / empty token -> False; same-secret accepts & diff-secret rejects; equal-state tokens equal & mutually acceptable. HOLDS.
- probe_6 (Req3.5): legacy sha1 token accepted via legacy path; default-algorithm round trip. HOLDS.

Candidate wrong-fix (weak.diff): reads user.email directly (fixed attribute name, no get_email_field_name, no None/absent guard). REJECTED by the suite: probe_3 VIOLATED (ignores custom email field name; uses decoy 'email' attr) and probe_4 VIOLATED (AttributeError raised for a user with no 'email' attribute). Demonstrates the suite discriminates against the naive-reading fix that a weak reading of the requirements permits. probes 1,2,5,6 pass under it (as expected).

No requirement-mandated behavior is missing from the gold patch (no VIOLATION), and the requirements-conforming space is tight enough that the plausible naive fix is caught. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (POSITIVE CONTROL): changing email invalidates outstanding token.
HOLDS iff check_token returns False after email changed to a different value."""
import django
from django.conf import settings
settings.configure(SECRET_KEY='k', DEFAULT_HASHING_ALGORITHM='sha256',
                   PASSWORD_RESET_TIMEOUT=60*60*24*3, USE_TZ=False)
django.setup()
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class U:
    pk = 1
    password = 'pw-hash'
    last_login = None
    email = 'old@example.com'
    def get_email_field_name(self):
        return 'email'


g = PasswordResetTokenGenerator()
u = U()
tok = g.make_token(u)
u.email = 'new@example.com'
res = g.check_token(u, tok)
print("check_token after email change =", res)
import sys
sys.exit(0 if res is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-13551: password reset token must depend on the user's email, read via get_email_field_name(), invalidating outstanding tokens on email change while preserving all prior behavior.

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): email change -> check_token False. HOLDS patched, VIOLATED at base (returned True) => discriminates, prepatch reproduced.
- probe_2 (Req1.2/3.1): unchanged email -> check_token True. HOLDS.
- probe_3 (Req1.3/1.4): email read via get_email_field_name() custom name 'primary_email' (literal 'email' attr is a decoy); differing primary_email -> different hash, differing decoy -> same hash; token invalidated on primary_email change. HOLDS patched; VIOLATED at base.
- probe_4 (Req2.1-2.4): no email attribute and None email both produce hash without raising and equal (empty); empty-unchanged -> True; empty->non-empty -> False. HOLDS.
- probe_5 (Req3.2/3.3/3.4/3.6): password change -> False; None user / None / empty token -> False; same-secret accepts & diff-secret rejects; equal-state tokens equal & mutually acceptable. HOLDS.
- probe_6 (Req3.5): legacy sha1 token accepted via legacy path; default-algorithm round trip. HOLDS.

Candidate wrong-fix (weak.diff): reads user.email directly (fixed attribute name, no get_email_field_name, no None/absent guard). REJECTED by the suite: probe_3 VIOLATED (ignores custom email field name; uses decoy 'email' attr) and probe_4 VIOLATED (AttributeError raised for a user with no 'email' attribute). Demonstrates the suite discriminates against the naive-reading fix that a weak reading of the requirements permits. probes 1,2,5,6 pass under it (as expected).

No requirement-mandated behavior is missing from the gold patch (no VIOLATION), and the requirements-conforming space is tight enough that the plausible naive fix is caught. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch (django/contrib/auth/tokens.py _make_hash_value) appends email = getattr(user, user.get_email_field_name(), '') or '' to the hashed state. Requirements pin the changed OBSERVABLE behavior (token invalidation on email change) at the correct boundary — _make_hash_value and its callers make_token/check_token — not a narrow slice. R1.4 correctly requires reading via get_email_field_name(); R2 correctly captures the getattr default + `or ''` null/absent handling; R3 preserves pre-existing pk/password/last_login/timeout/secret/algorithm behavior, all consistent with the diff (only additive). No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes token behavior in EARS form. All named identifiers (_make_hash_value, make_token, check_token, get_email_field_name, AbstractBaseUser, PASSWORD_RESET_TIMEOUT, secret, legacy sha1) are pre-existing public Django API — _make_hash_value and AbstractBaseUser/no-email are even named in the public problem_statement, and the gold patch invents no new identifiers (only a local `email` var, not surfaced). No hidden-test artifacts appear: absent are the test name test_token_with_different_email, file test_tokens.py, model CustomEmailField, literal 'test4new@example.com', null=True, and the subTest parametrization tuples. Requirement 2 (missing-attr/None email) is grounded in the public 'Nothing forces a user to even have an email' line. Requirement 3's enumeration parallels PASS_TO_PASS but each item states pre-existing, publicly observable preserved behavior (no-regression), which is legitimate behavioral description rather than transmitting the tests. This is faithful test-to-requirement translation, not gold/test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
