# P2 adversarial audit — django__django-13741

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
"""R1.1 (positive control): default-constructed ReadOnlyPasswordHashField.disabled is True."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.contrib.auth.forms import ReadOnlyPasswordHashField

f = ReadOnlyPasswordHashField()
print("disabled =", repr(f.disabled))
assert f.disabled is True, "expected disabled True by default, got %r" % (f.disabled,)
print("OK R1.1")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2 & R1.4: explicit disabled/required args are honored exactly."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.contrib.auth.forms import ReadOnlyPasswordHashField

f_dis = ReadOnlyPasswordHashField(disabled=False)
print("explicit disabled=False ->", repr(f_dis.disabled))
assert f_dis.disabled is False, "explicit disabled=False not honored: %r" % f_dis.disabled

f_req = ReadOnlyPasswordHashField(required=True)
print("explicit required=True ->", repr(f_req.required))
assert f_req.required is True, "explicit required=True not honored: %r" % f_req.required

# default required is False (R1.3)
f_def = ReadOnlyPasswordHashField()
print("default required ->", repr(f_def.required))
assert f_def.required is False, "default required should be False: %r" % f_def.required
print("OK R1.2/R1.3/R1.4")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1 & R2.2: has_changed always False; bound_data yields initial (disregarding submitted)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.contrib.auth.forms import ReadOnlyPasswordHashField

f = ReadOnlyPasswordHashField()
# R2.1: differing non-empty strings -> no change
hc = f.has_changed("initialhash", "tamperedvalue")
print("has_changed(differing) =", hc)
assert hc is False or hc == False, "expected no change, got %r" % hc
hc2 = f.has_changed("", "x")
print("has_changed('', 'x') =", hc2)
assert not hc2, "expected no change, got %r" % hc2

# R2.2: bound_data yields initial, disregarding submitted
bd = f.bound_data("submitted-client-value", "the-initial")
print("bound_data =", repr(bd))
assert bd == "the-initial", "bound_data should yield initial, got %r" % bd
print("OK R2.1/R2.2")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.3: behavior derives from the disabled state, NOT a bespoke override.
When disabled=False, the field must behave like base Field: report a change on
differing values, and bound_data return the submitted data. This fails on any
implementation that keeps the old hardcoded has_changed/bound_data overrides."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.contrib.auth.forms import ReadOnlyPasswordHashField

f = ReadOnlyPasswordHashField(disabled=False)
hc = f.has_changed("a", "b")
print("disabled=False has_changed('a','b') =", hc)
assert hc, "with disabled=False the field must report a change (base behavior); got %r" % hc

bd = f.bound_data("submitted", "initial")
print("disabled=False bound_data =", repr(bd))
assert bd == "submitted", "with disabled=False bound_data must return submitted data; got %r" % bd
print("OK R2.3 (behavior derived from disabled, not bespoke override)")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3: UserChangeForm keeps the stored password unchanged regardless of submission,
without a clean_password step. Also R3.2: no clean_password method defined on the form."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm

u = User.objects.create_user(username="alice", password="s3cret-orig")
stored = u.password
print("stored password hash starts:", stored[:12])

data = {
    "username": "alice",
    "password": "TAMPERED-VALUE-should-be-ignored",
    "last_login_0": "", "last_login_1": "",
    "date_joined_0": "2020-01-01", "date_joined_1": "00:00:00",
}
form = UserChangeForm(data=data, instance=u)
# Trigger cleaning. A disabled field is populated from initial during
# _clean_fields regardless of overall form validity; we only care about
# the password field's cleaned value here.
form.is_valid()
cleaned = form.cleaned_data.get("password")
print("cleaned password =", repr(cleaned)[:40])
assert cleaned == stored, "cleaned password must equal stored initial, got %r" % (cleaned,)
# password field itself must have no error
print("password errors:", form.errors.get("password"))
assert not form.errors.get("password"), "password field should have no error"
print("OK R3 (password preserved regardless of submission)")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.1 & R4.2: widget renders a graceful summary when password is absent/None
(no error), and UserChangeForm keeps password field present with help-text link."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth.forms import UserChangeForm, ReadOnlyPasswordHashField

# R4.1: rendering with None initial must not raise
f = ReadOnlyPasswordHashField()
html_none = str(f.widget.render("password", None, {}))
print("render(None) len:", len(html_none))
from django.contrib.auth.hashers import make_password
enc = make_password("hunter2")
html_val = str(f.widget.render("password", enc, {}))
print("render(value) rendered len:", len(html_val))
assert len(html_val) > 0

# R4.2: password field present with a link to the password-change form
form = UserChangeForm()
assert "password" in form.fields, "password field must be present"
help_text = str(form.fields["password"].help_text)
print("help_text:", help_text[:80])
assert "password" in help_text.lower(), "help text should reference password change"
# link is typically ../password/ ; accept href presence
assert "href" in help_text or "../" in help_text, "help text should link to password change form"
print("OK R4.1/R4.2")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 (positive control): default-constructed ReadOnlyPasswordHashField.disabled is True."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.contrib.auth.forms import ReadOnlyPasswordHashField

f = ReadOnlyPasswordHashField()
print("disabled =", repr(f.disabled))
assert f.disabled is True, "expected disabled True by default, got %r" % (f.disabled,)
print("OK R1.1")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all 4 requirements. Results on gold-PATCHED tree: all 6 HOLD.

- probe_1 (R1.1, POSITIVE CONTROL): default ReadOnlyPasswordHashField.disabled is True. PATCHED=HOLDS, BASE=FAILS (disabled=False) -> discriminates.
- probe_2 (R1.2/1.3/1.4): explicit disabled=/required= honored exactly; default required=False. PATCHED=HOLDS.
- probe_3 (R2.1/2.2): has_changed on differing values -> False; bound_data yields initial. PATCHED=HOLDS (also holds at base, expected for a refactor).
- probe_4 (R2.3): behavior derives from disabled state, NOT bespoke overrides. With disabled=False the field must report a change and bound_data must return submitted data. PATCHED=HOLDS.
- probe_5 (R3): UserChangeForm cleaned password == stored initial regardless of tampered submission, no password field error. PATCHED=HOLDS.
- probe_6 (R4.1/4.2): widget renders None initial without error and renders a real hash summary; UserChangeForm keeps password field present with help-text link. PATCHED=HOLDS.

CANDIDATE (wrong-fix) weak.diff: adds kwargs.setdefault('disabled', True) but KEEPS the old bespoke bound_data/has_changed overrides (the lazy/partial fix a weak reading permits). This is REJECTED by probe_4 (R2.3): with disabled=False the retained override still forces has_changed->False, so the suite catches that the behavior is not derived from disabled state. Demonstrates discriminating power.

Conclusion: >=5 probes all hold on patched, positive control discriminates (prepatch_reproduced=true), and a plausibly-wrong candidate is rejected by the suite. Requirements are faithful and adequately tight. SOUND.

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
"""R1.1 (positive control): default-constructed ReadOnlyPasswordHashField.disabled is True."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, SECRET_KEY="x",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
django.setup()
from django.contrib.auth.forms import ReadOnlyPasswordHashField

f = ReadOnlyPasswordHashField()
print("disabled =", repr(f.disabled))
assert f.disabled is True, "expected disabled True by default, got %r" % (f.disabled,)
print("OK R1.1")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all 4 requirements. Results on gold-PATCHED tree: all 6 HOLD.

- probe_1 (R1.1, POSITIVE CONTROL): default ReadOnlyPasswordHashField.disabled is True. PATCHED=HOLDS, BASE=FAILS (disabled=False) -> discriminates.
- probe_2 (R1.2/1.3/1.4): explicit disabled=/required= honored exactly; default required=False. PATCHED=HOLDS.
- probe_3 (R2.1/2.2): has_changed on differing values -> False; bound_data yields initial. PATCHED=HOLDS (also holds at base, expected for a refactor).
- probe_4 (R2.3): behavior derives from disabled state, NOT bespoke overrides. With disabled=False the field must report a change and bound_data must return submitted data. PATCHED=HOLDS.
- probe_5 (R3): UserChangeForm cleaned password == stored initial regardless of tampered submission, no password field error. PATCHED=HOLDS.
- probe_6 (R4.1/4.2): widget renders None initial without error and renders a real hash summary; UserChangeForm keeps password field present with help-text link. PATCHED=HOLDS.

CANDIDATE (wrong-fix) weak.diff: adds kwargs.setdefault('disabled', True) but KEEPS the old bespoke bound_data/has_changed overrides (the lazy/partial fix a weak reading permits). This is REJECTED by probe_4 (R2.3): with disabled=False the retained override still forces has_changed->False, so the suite catches that the behavior is not derived from disabled state. Demonstrates discriminating power.

Conclusion: >=5 probes all hold on patched, positive control discriminates (prepatch_reproduced=true), and a plausibly-wrong candidate is rejected by the suite. Requirements are faithful and adequately tight. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe HOLDS (gold-patched) exit=0 'ALL OK'; base shows disabled=False, has_changed override present, clean_password present — confirming the requirements pin exactly the changed observable behavior (disabled-default => non-editability + no-change + form password preservation via removal of overrides), the correct modeling boundary rather than a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior derivable from the public problem_statement (set disabled=True on ReadOnlyPasswordHashField, remove clean_password/has_changed/bound_data overrides). All named identifiers (disabled, required, has_changed, bound_data, clean_password, UserChangeForm, django/contrib/auth/forms.py, django/forms/fields.py) are legitimate localization of the change and appear in the public issue or the real Django API — none are fix-invented. The single hidden FAIL_TO_PASS test merely asserts field.disabled is True and has_changed('aaa','bbb') is False; nothing quotes the test path/name/ids or gold-patch lines. Req 2.1's phrase 'two differing non-empty strings' generically restates has_changed semantics rather than transmitting the test's specific 'aaa'/'bbb' literals, and does not enumerate parametrized cases. No test-shaped reconstruction present.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
