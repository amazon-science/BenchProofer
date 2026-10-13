# P2 adversarial audit — django__django-11790

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
"""Req1.1 & Req1.4 (POSITIVE CONTROL): username widget exposes a 'maxlength'
attribute whose value equals the field's effective max_length.
On the default User model USERNAME_FIELD='username' has max_length=150.
Base (unpatched) does NOT set widget maxlength -> FAIL. Patched -> HOLD."""
import sys, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
)
django.setup()
from django.contrib.auth.forms import AuthenticationForm

form = AuthenticationForm()
field = form.fields['username']
attrs = field.widget.attrs
print("field.max_length =", field.max_length)
print("widget.attrs =", attrs)
ml = attrs.get('maxlength')
print("widget maxlength =", ml)
if ml is None:
    print("FAIL: no maxlength attribute on widget")
    sys.exit(1)
# compare as ints (attr may be str or int)
if int(ml) != int(field.max_length):
    print("FAIL: widget maxlength != field.max_length")
    sys.exit(1)
print("HOLD: widget maxlength equals field.max_length")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 & Req2.1: with a user model whose USERNAME_FIELD declares max_length,
widget maxlength AND field.max_length equal that declared value.
Default User.username has max_length=150."""
import sys, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
)
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

UserModel = get_user_model()
declared = UserModel._meta.get_field(UserModel.USERNAME_FIELD).max_length
print("declared USERNAME_FIELD max_length =", declared)
assert declared, "test premise: default username field should declare a max_length"

form = AuthenticationForm()
field = form.fields['username']
ml = field.widget.attrs.get('maxlength')
print("field.max_length =", field.max_length, "widget maxlength =", ml)
if int(field.max_length) != int(declared):
    print("FAIL: field.max_length != declared")
    sys.exit(1)
if ml is None or int(ml) != int(declared):
    print("FAIL: widget maxlength != declared")
    sys.exit(1)
print("HOLD: both equal declared max_length", declared)
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3 & Req2.2: IF USERNAME_FIELD declares no max_length (falsy) THEN both
the field.max_length and the widget maxlength SHALL equal 254.
Simulate by temporarily forcing the model field's max_length to None."""
import sys, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
)
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

UserModel = get_user_model()
mfield = UserModel._meta.get_field(UserModel.USERNAME_FIELD)
saved = mfield.max_length
try:
    mfield.max_length = None  # falsy
    form = AuthenticationForm()
    field = form.fields['username']
    ml = field.widget.attrs.get('maxlength')
    print("field.max_length =", field.max_length, "widget maxlength =", ml)
    ok = (int(field.max_length) == 254) and (ml is not None and int(ml) == 254)
finally:
    mfield.max_length = saved

if not ok:
    print("FAIL: falsy max_length did not fall back to 254 on both")
    sys.exit(1)
print("HOLD: falls back to 254 on field and widget")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req1.1 rendering-level: the rendered <input> for username carries a
maxlength HTML attribute equal to field.max_length (150 by default).
This is the user-visible client-side limit the requirement is about."""
import sys, re, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
)
django.setup()
from django.contrib.auth.forms import AuthenticationForm

form = AuthenticationForm()
html = str(form['username'])
print("rendered username field:", html)
m = re.search(r'maxlength="(\d+)"', html)
if not m:
    print("FAIL: rendered <input> has no maxlength attribute")
    sys.exit(1)
rendered = int(m.group(1))
if rendered != int(form.fields['username'].max_length):
    print("FAIL: rendered maxlength != field.max_length")
    sys.exit(1)
print("HOLD: rendered maxlength =", rendered)
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1 & Req3.3 (regression 'SHALL keep'): label defaults to capfirst of the
USERNAME_FIELD verbose_name, the password field/autocomplete is unchanged, and
the autofocus attr on username survives. Also Req2.3: within-length input is
free of length-based validation errors."""
import sys, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
)
django.setup()
from django.utils.text import capfirst
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

UserModel = get_user_model()
vn = UserModel._meta.get_field(UserModel.USERNAME_FIELD).verbose_name

form = AuthenticationForm()
ufield = form.fields['username']
pfield = form.fields['password']
print("username label =", repr(str(ufield.label)))
print("expected label =", repr(str(capfirst(vn))))
print("username widget attrs =", ufield.widget.attrs)
print("password widget attrs =", pfield.widget.attrs)

ok = True
if str(ufield.label) != str(capfirst(vn)):
    print("FAIL: label not defaulted to capfirst(verbose_name)"); ok = False
# username autofocus preserved
if not ufield.widget.attrs.get('autofocus'):
    print("FAIL: username autofocus lost"); ok = False
# password field must NOT carry a maxlength (unchanged by the username change)
if 'maxlength' in pfield.widget.attrs:
    print("FAIL: password widget unexpectedly got maxlength"); ok = False

# Req2.3: within-length input -> no length-based error on username.
# Validate the field directly to avoid DB-backed authenticate().
from django.core.exceptions import ValidationError
try:
    cleaned = ufield.clean('a' * (int(ufield.max_length) - 1))
    print("username field.clean(within-length) ok ->", repr(cleaned))
except ValidationError as e:
    print("FAIL: within-length username produced field errors:", e); ok = False

if not ok:
    sys.exit(1)
print("HOLD: label default, autofocus, password unchanged, no length errors")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.2 (regression): authentication still works — a valid user authenticates
and a bad password reports the invalid_login error."""
import sys, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
django.setup()
from django.test.utils import setup_test_environment
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.db import connection

connection.creation.create_test_db(verbosity=0)
User = get_user_model()
User.objects.create_user(username='bob', password='secretpw')

ok = True
good = AuthenticationForm(data={'username': 'bob', 'password': 'secretpw'})
print("valid creds -> is_valid:", good.is_valid(), "errors:", good.errors)
if not good.is_valid() or good.get_user() is None:
    print("FAIL: valid credentials did not authenticate"); ok = False

bad = AuthenticationForm(data={'username': 'bob', 'password': 'wrong'})
print("bad creds -> is_valid:", bad.is_valid())
codes = [e.code for e in bad.errors.as_data().get('__all__', [])]
print("bad creds error codes:", codes)
if bad.is_valid() or 'invalid_login' not in codes:
    print("FAIL: bad credentials did not raise invalid_login"); ok = False

if not ok:
    sys.exit(1)
print("HOLD: authentication behavior preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 & Req1.4 (POSITIVE CONTROL): username widget exposes a 'maxlength'
attribute whose value equals the field's effective max_length.
On the default User model USERNAME_FIELD='username' has max_length=150.
Base (unpatched) does NOT set widget maxlength -> FAIL. Patched -> HOLD."""
import sys, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
)
django.setup()
from django.contrib.auth.forms import AuthenticationForm

form = AuthenticationForm()
field = form.fields['username']
attrs = field.widget.attrs
print("field.max_length =", field.max_length)
print("widget.attrs =", attrs)
ml = attrs.get('maxlength')
print("widget maxlength =", ml)
if ml is None:
    print("FAIL: no maxlength attribute on widget")
    sys.exit(1)
# compare as ints (attr may be str or int)
if int(ml) != int(field.max_length):
    print("FAIL: widget maxlength != field.max_length")
    sys.exit(1)
print("HOLD: widget maxlength equals field.max_length")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: restore widget-level maxlength on AuthenticationForm username field mirroring field.max_length, preserving computed max_length, label defaulting, authentication, validation.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.4, POSITIVE CONTROL): widget.attrs['maxlength'] present and == field.max_length (150). FAILS at base (no maxlength attr -> None) = prepatch reproduced.
- probe_2 (Req1.2/2.1): with declared USERNAME_FIELD max_length (150), both widget maxlength and field.max_length equal it.
- probe_3 (Req1.3/2.2): forcing model field max_length falsy (None) -> both field and widget fall back to 254.
- probe_4 (Req1.1 rendering): rendered <input> HTML carries maxlength="150" matching field.max_length.
- probe_5 (Req3.1/3.3/2.3): label defaults to capfirst(verbose_name), username autofocus preserved, password widget carries NO maxlength (unchanged), within-length input clean() raises no error.
- probe_6 (Req3.2): valid creds authenticate (get_user non-None); bad password raises invalid_login. (Uses in-memory test DB.)

Discrimination: candidate 'hardcoded_150' sets widget maxlength = literal 150 instead of the computed value. Probe suite REJECTS it via probe_3 (falsy-max_length fallback must be 254 on BOTH field and widget; the candidate leaves widget at 150 while field=254), demonstrating the suite distinguishes the correct computed-length propagation from a naive constant. Note this candidate coincidentally passes probes 1/2/4 because the default User model max_length is 150; probe_3 is the discriminator.

Conclusion: >=5 distinct probes all hold on patched, positive control discriminates (holds patched, fails base), and a probe-conforming-looking wrong fix is rejected by the suite. Requirements are faithful and not too weak w.r.t. the encoded criteria.

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
"""Req1.1 & Req1.4 (POSITIVE CONTROL): username widget exposes a 'maxlength'
attribute whose value equals the field's effective max_length.
On the default User model USERNAME_FIELD='username' has max_length=150.
Base (unpatched) does NOT set widget maxlength -> FAIL. Patched -> HOLD."""
import sys, django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    AUTH_PASSWORD_VALIDATORS=[], USE_TZ=True, SECRET_KEY='x',
)
django.setup()
from django.contrib.auth.forms import AuthenticationForm

form = AuthenticationForm()
field = form.fields['username']
attrs = field.widget.attrs
print("field.max_length =", field.max_length)
print("widget.attrs =", attrs)
ml = attrs.get('maxlength')
print("widget maxlength =", ml)
if ml is None:
    print("FAIL: no maxlength attribute on widget")
    sys.exit(1)
# compare as ints (attr may be str or int)
if int(ml) != int(field.max_length):
    print("FAIL: widget maxlength != field.max_length")
    sys.exit(1)
print("HOLD: widget maxlength equals field.max_length")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: restore widget-level maxlength on AuthenticationForm username field mirroring field.max_length, preserving computed max_length, label defaulting, authentication, validation.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.4, POSITIVE CONTROL): widget.attrs['maxlength'] present and == field.max_length (150). FAILS at base (no maxlength attr -> None) = prepatch reproduced.
- probe_2 (Req1.2/2.1): with declared USERNAME_FIELD max_length (150), both widget maxlength and field.max_length equal it.
- probe_3 (Req1.3/2.2): forcing model field max_length falsy (None) -> both field and widget fall back to 254.
- probe_4 (Req1.1 rendering): rendered <input> HTML carries maxlength="150" matching field.max_length.
- probe_5 (Req3.1/3.3/2.3): label defaults to capfirst(verbose_name), username autofocus preserved, password widget carries NO maxlength (unchanged), within-length input clean() raises no error.
- probe_6 (Req3.2): valid creds authenticate (get_user non-None); bad password raises invalid_login. (Uses in-memory test DB.)

Discrimination: candidate 'hardcoded_150' sets widget maxlength = literal 150 instead of the computed value. Probe suite REJECTS it via probe_3 (falsy-max_length fallback must be 254 on BOTH field and widget; the candidate leaves widget at 150 while field=254), demonstrating the suite distinguishes the correct computed-length propagation from a naive constant. Note this candidate coincidentally passes probes 1/2/4 because the default User model max_length is 150; probe_3 is the discriminator.

Conclusion: >=5 distinct probes all hold on patched, positive control discriminates (holds patched, fails base), and a probe-conforming-looking wrong fix is rejected by the suite. Requirements are faithful and not too weak w.r.t. the encoded criteria.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a 3-line change in AuthenticationForm.__init__; requirements pin the exact changed observable (widget maxlength) at the right boundary and correctly separate the new behavior (Req 1) from preserved behavior (Req 2/3). No mandated-but-absent, forbidden-but-present, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements translate the public problem_statement ('AuthenticationForm's username field doesn't set maxlength HTML attribute') into behavioral criteria. Naming forms.py / AuthenticationForm.__init__ / self.fields['username'].widget is legitimate localization. The two-case split (declared max_length → equal; falsy → 254) reflects the actual code branch (`max_length or 254`), i.e. described behavior — not the hidden test parametrization. The test-specific value 255 (CustomEmailField case) never appears; only the code-intrinsic 254 fallback does. No test names/paths/ids, no quoted test or gold code, no fix-invented identifiers. Req 3's reference to the password field's autocomplete attribute is generic preserved-behavior prose, not a reconstruction of the PASS_TO_PASS suite.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
