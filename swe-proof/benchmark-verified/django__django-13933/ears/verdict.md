# P2 adversarial audit — django__django-13933

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
# Positive control. Req1.2 + Req1.3: invalid choice -> ValidationError carrying
# params binding 'value' to the submitted value; a %(value)s template renders it.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelChoiceField
from django.core.exceptions import ValidationError

SUBMITTED = '999999'  # no such pk
f = ModelChoiceField(
    queryset=User.objects.all(),
    error_messages={'invalid_choice': 'Value %(value)s is not valid.'},
)
try:
    f.to_python(SUBMITTED)
    print("NO ValidationError raised -> FAIL")
    raise SystemExit(1)
except ValidationError as e:
    # message must render the submitted value
    msg = ' '.join(e.messages)
    print("rendered message:", repr(msg))
    params_ok = False
    # inspect the error_list params
    for err in e.error_list:
        p = getattr(err, 'params', None)
        print("params:", p)
        if p and p.get('value') == SUBMITTED:
            params_ok = True
    if SUBMITTED in msg and params_ok:
        print("HOLDS: value bound and rendered")
        raise SystemExit(0)
    print("FAIL: value not bound/rendered")
    raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.4: rejection uses error code 'invalid_choice'. Also Req1.1: raises ValidationError.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelChoiceField
from django.core.exceptions import ValidationError

f = ModelChoiceField(queryset=User.objects.all())
try:
    f.to_python('123456')
    print("NO ValidationError -> FAIL")
    raise SystemExit(1)
except ValidationError as e:
    codes = [err.code for err in e.error_list]
    print("codes:", codes)
    if codes == ['invalid_choice']:
        print("HOLDS: code invalid_choice")
        raise SystemExit(0)
    print("FAIL")
    raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.5: resolution failure recognized for ValueError, TypeError, DoesNotExist.
# Non-numeric string -> ValueError from pk coercion; wrong type -> TypeError; missing pk -> DoesNotExist.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelChoiceField
from django.core.exceptions import ValidationError

f = ModelChoiceField(queryset=User.objects.all())
cases = ['not-an-int', '999999', ['a', 'list']]  # ValueError, DoesNotExist, TypeError-ish
ok = True
for c in cases:
    try:
        f.to_python(c)
        print("no error for", repr(c), "-> FAIL")
        ok = False
    except ValidationError as e:
        codes = [err.code for err in e.error_list]
        print(repr(c), "->", codes)
        if codes != ['invalid_choice']:
            ok = False
    except Exception as e:
        print(repr(c), "-> uncaught", type(e).__name__, "-> FAIL")
        ok = False
if ok:
    print("HOLDS")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2.1 + Req2.2: empty value -> None (no error); valid value -> the object.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelChoiceField

u = User.objects.create(username='alice')
f = ModelChoiceField(queryset=User.objects.all())

ok = True
# empty value
r = f.to_python('')
print("empty ->", r)
if r is not None:
    ok = False
r = f.to_python(None)
print("None ->", r)
if r is not None:
    ok = False
# valid pk
r = f.to_python(str(u.pk))
print("valid pk ->", r)
if r != u:
    ok = False
if ok:
    print("HOLDS")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2.3 + Req2.4: default invalid_choice message unchanged (no %(value)s), and
# with the default template the presence of the value param does NOT alter output.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelChoiceField
from django.core.exceptions import ValidationError

# The historical default text.
EXPECTED = 'Select a valid choice. That choice is not one of the available choices.'

f = ModelChoiceField(queryset=User.objects.all())
# default template must be unchanged
tmpl = f.error_messages['invalid_choice']
print("default template:", repr(tmpl))
if '%(value)s' in tmpl:
    print("FAIL: default template references value placeholder")
    raise SystemExit(1)

try:
    f.to_python('987654')
    print("no error -> FAIL")
    raise SystemExit(1)
except ValidationError as e:
    msg = ' '.join(e.messages)
    print("rendered default msg:", repr(msg))
    if msg == EXPECTED:
        print("HOLDS: default message unchanged, unaffected by value param")
        raise SystemExit(0)
    print("FAIL: default message changed")
    raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req2.5: ModelMultipleChoiceField invalid_choice still binds %(value)s (sibling unchanged).
# This is a "SHALL keep other fields unchanged" regression. It should hold on both trees
# since the gold patch only touched ModelChoiceField -- so it's a guard, not a control.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelMultipleChoiceField
from django.core.exceptions import ValidationError

f = ModelMultipleChoiceField(
    queryset=User.objects.all(),
    error_messages={'invalid_choice': 'Bad %(value)s here.'},
)
try:
    f.clean(['424242'])
    print("no error -> FAIL")
    raise SystemExit(1)
except ValidationError as e:
    msg = ' '.join(e.messages)
    print("MMCF rendered:", repr(msg))
    if '424242' in msg:
        print("HOLDS: sibling ModelMultipleChoiceField still interpolates value")
        raise SystemExit(0)
    print("FAIL")
    raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control. Req1.2 + Req1.3: invalid choice -> ValidationError carrying
# params binding 'value' to the submitted value; a %(value)s template renders it.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelChoiceField
from django.core.exceptions import ValidationError

SUBMITTED = '999999'  # no such pk
f = ModelChoiceField(
    queryset=User.objects.all(),
    error_messages={'invalid_choice': 'Value %(value)s is not valid.'},
)
try:
    f.to_python(SUBMITTED)
    print("NO ValidationError raised -> FAIL")
    raise SystemExit(1)
except ValidationError as e:
    # message must render the submitted value
    msg = ' '.join(e.messages)
    print("rendered message:", repr(msg))
    params_ok = False
    # inspect the error_list params
    for err in e.error_list:
        p = getattr(err, 'params', None)
        print("params:", p)
        if p and p.get('value') == SUBMITTED:
            params_ok = True
    if SUBMITTED in msg and params_ok:
        print("HOLDS: value bound and rendered")
        raise SystemExit(0)
    print("FAIL: value not bound/rendered")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-13933: ModelChoiceField.to_python must bind the offending submitted value to the 'value' interpolation param on invalid_choice.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.2/1.3, POSITIVE CONTROL): custom template 'Value %(value)s is not valid.' renders '999999' AND error param value=='999999'. HOLDS patched, FAILS at base (base: param None, template unrendered '%(value)s'). Discriminates.
- probe_2 (Req1.4/1.1): rejection code == ['invalid_choice']. HOLDS patched.
- probe_3 (Req1.5): ValueError ('not-an-int'), DoesNotExist ('999999'), and list-value inputs all -> ValidationError code invalid_choice, none uncaught. HOLDS patched.
- probe_4 (Req2.1/2.2): ''/None -> None (no error); valid pk -> the object. HOLDS patched.
- probe_5 (Req2.3/2.4): default template has no %(value)s and default message renders unchanged text unaffected by the new param. HOLDS both trees (guard).
- probe_6 (Req2.5): sibling ModelMultipleChoiceField still interpolates %(value)s. HOLDS both trees (guard).

Candidate wrong-fix (weak.diff): identical to gold but binds params={'val': value} instead of {'value': value} — a plausible weak reading that adds params but with the wrong key. REJECTED by probe_1s template renders => value not bound). Demonstrates the suite discriminates: adding SOME params is insufficient; the 'value' key is mandated. probes 2/4/5 pass under it (they don't reference the value key), which is expected.

Verdict SOUND: 6 distinct probes cover every acceptance criterion, all hold on the patched tree, positive control fails at base, and a requirements-conforming-looking-but-wrong candidate is rejected by the suite.

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
# Positive control. Req1.2 + Req1.3: invalid choice -> ValidationError carrying
# params binding 'value' to the submitted value; a %(value)s template renders it.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.forms import ModelChoiceField
from django.core.exceptions import ValidationError

SUBMITTED = '999999'  # no such pk
f = ModelChoiceField(
    queryset=User.objects.all(),
    error_messages={'invalid_choice': 'Value %(value)s is not valid.'},
)
try:
    f.to_python(SUBMITTED)
    print("NO ValidationError raised -> FAIL")
    raise SystemExit(1)
except ValidationError as e:
    # message must render the submitted value
    msg = ' '.join(e.messages)
    print("rendered message:", repr(msg))
    params_ok = False
    # inspect the error_list params
    for err in e.error_list:
        p = getattr(err, 'params', None)
        print("params:", p)
        if p and p.get('value') == SUBMITTED:
            params_ok = True
    if SUBMITTED in msg and params_ok:
        print("HOLDS: value bound and rendered")
        raise SystemExit(0)
    print("FAIL: value not bound/rendered")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-13933: ModelChoiceField.to_python must bind the offending submitted value to the 'value' interpolation param on invalid_choice.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.2/1.3, POSITIVE CONTROL): custom template 'Value %(value)s is not valid.' renders '999999' AND error param value=='999999'. HOLDS patched, FAILS at base (base: param None, template unrendered '%(value)s'). Discriminates.
- probe_2 (Req1.4/1.1): rejection code == ['invalid_choice']. HOLDS patched.
- probe_3 (Req1.5): ValueError ('not-an-int'), DoesNotExist ('999999'), and list-value inputs all -> ValidationError code invalid_choice, none uncaught. HOLDS patched.
- probe_4 (Req2.1/2.2): ''/None -> None (no error); valid pk -> the object. HOLDS patched.
- probe_5 (Req2.3/2.4): default template has no %(value)s and default message renders unchanged text unaffected by the new param. HOLDS both trees (guard).
- probe_6 (Req2.5): sibling ModelMultipleChoiceField still interpolates %(value)s. HOLDS both trees (guard).

Candidate wrong-fix (weak.diff): identical to gold but binds params={'val': value} instead of {'value': value} — a plausible weak reading that adds params but with the wrong key. REJECTED by probe_1s template renders => value not bound). Demonstrates the suite discriminates: adding SOME params is insufficient; the 'value' key is mandated. probes 2/4/5 pass under it (they don't reference the value key), which is expected.

Verdict SOUND: 6 distinct probes cover every acceptance criterion, all hold on the patched tree, positive control fails at base, and a requirements-conforming-looking-but-wrong candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified in the instance image via nl_attack probe on the gold-patched tree. Requirements pin the exact changed observable behavior (offending value bound to the 'value' interpolation param) rather than a narrow slice, and preserve-behavior clauses hold. Modeling boundary is correct.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements are a clean behavioral translation. Everything mentioned is public via problem_statement: ModelChoiceField in django/forms/models.py, to_python, the invalid_choice code, the %(value)s placeholder (shown in the quoted ModelMultipleChoiceField source), and the fix approach ('Passing in parameters with the invalid value'). Naming the 'value' interpolation param is derivable from the placeholder name and is legitimate localization. No hidden-test content leaks: no test function/class name (test_modelchoicefield_value_placeholder / ModelChoiceFieldErrorMessagesTestCase), no test file path, no ChoiceModel identifier, no literal submitted value ('invalid'), and no verbatim test message string ('"%(value)s" is not one of the available choices.'). Req 1.5's enumeration of ValueError/TypeError/DoesNotExist mirrors the UNCHANGED pre-existing except clause (context, not the gold edit), so it describes preserved behavior rather than reconstructing the test. The gold edit adds only params={'value': value}, which is expressed as a behavioral requirement, not quoted code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
