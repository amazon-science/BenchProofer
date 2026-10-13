# P2 adversarial audit — django__django-16560

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2/1.3/1.4: constructor accepts violation_error_code, stores it, defaults None,
# subclasses forward to base identically. (POSITIVE CONTROL: fails at base where kwarg absent.)
import sys
from django.db.models import Q
from django.db.models.constraints import BaseConstraint, CheckConstraint, UniqueConstraint

ok = True
# BaseConstraint
b = BaseConstraint(name="b", violation_error_code="mycode")
print("BaseConstraint.violation_error_code =", b.violation_error_code)
ok &= (b.violation_error_code == "mycode")
b2 = BaseConstraint(name="b2")
print("BaseConstraint default =", b2.violation_error_code)
ok &= (b2.violation_error_code is None)

# CheckConstraint
c = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="cc")
print("CheckConstraint.violation_error_code =", c.violation_error_code)
ok &= (c.violation_error_code == "cc")
c2 = CheckConstraint(check=Q(x__gt=0), name="c2")
print("CheckConstraint default =", c2.violation_error_code)
ok &= (c2.violation_error_code is None)

# UniqueConstraint
u = UniqueConstraint(fields=["x"], name="u", violation_error_code="uu")
print("UniqueConstraint.violation_error_code =", u.violation_error_code)
ok &= (u.violation_error_code == "uu")
u2 = UniqueConstraint(fields=["x"], name="u2")
print("UniqueConstraint default =", u2.violation_error_code)
ok &= (u2.violation_error_code is None)

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2.1 + 2.6: CheckConstraint.validate raises ValidationError whose code == configured code,
# and message unchanged (default message) independent of code.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, USE_I18N=False)
    django.setup()

import sys
from django.db.models import Q
from django.db.models.constraints import CheckConstraint
from django.core.exceptions import ValidationError

class FakeMeta:
    pass
class FakeInstance:
    def _get_field_value_map(self, meta, exclude=None):
        return {"x": -5}  # violates x__gt=0
class FakeModel:
    _meta = FakeMeta()

c = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="my_code")
raised = None
try:
    c.validate(FakeModel, FakeInstance())
except ValidationError as e:
    raised = e
print("raised:", raised is not None, "code:", None if raised is None else raised.code)
print("message:", None if raised is None else raised.messages)
ok = raised is not None and raised.code == "my_code"
# message must be the default violation message
ok &= (raised.messages == ['Constraint “c” is violated.'])
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.4 + 2.5: no configured code -> ValidationError.code is None; and no violation -> no raise.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, USE_I18N=False)
    django.setup()

import sys
from django.db.models import Q
from django.db.models.constraints import CheckConstraint
from django.core.exceptions import ValidationError

class FakeMeta: pass
class FakeModel: _meta = FakeMeta()
class BadInstance:
    def _get_field_value_map(self, meta, exclude=None): return {"x": -1}
class GoodInstance:
    def _get_field_value_map(self, meta, exclude=None): return {"x": 10}

c = CheckConstraint(check=Q(x__gt=0), name="c")  # no code
raised = None
try:
    c.validate(FakeModel, BadInstance())
except ValidationError as e:
    raised = e
print("violation code (no code configured):", None if raised is None else raised.code)
ok = raised is not None and raised.code is None

# no violation -> nothing raised
noraise = True
try:
    c.validate(FakeModel, GoodInstance())
except ValidationError:
    noraise = False
print("no violation raised nothing:", noraise)
ok &= noraise
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2/4.3/4.4: deconstruct includes violation_error_code only when set;
# other kwargs preserved; violation_error_message only under its existing condition.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_I18N=False)
    django.setup()

import sys
from django.db.models import Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint

ok = True
# with code
c = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="zzz")
path, args, kwargs = c.deconstruct()
print("check w/code kwargs:", kwargs)
ok &= kwargs.get("violation_error_code") == "zzz"
ok &= "check" in kwargs and "name" in kwargs  # other entries preserved
ok &= "violation_error_message" not in kwargs  # msg not set -> absent

# without code
c2 = CheckConstraint(check=Q(x__gt=0), name="c2")
_, _, k2 = c2.deconstruct()
print("check no-code kwargs:", k2)
ok &= "violation_error_code" not in k2

# unique with code + message
u = UniqueConstraint(fields=["x"], name="u", violation_error_code="qc", violation_error_message="msg")
_, _, ku = u.deconstruct()
print("unique kwargs:", ku)
ok &= ku.get("violation_error_code") == "qc"
ok &= ku.get("violation_error_message") == "msg"
ok &= ku.get("fields") == ("x",) and ku.get("name") == "u"

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 5: code participates in equality.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_I18N=False)
    django.setup()

import sys
from django.db.models import Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint

ok = True
a = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="A")
b = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="B")
c = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="A")
print("A==B:", a==b, "A==C:", a==c)
ok &= (a != b)
ok &= (a == c)

# both None equal
d = CheckConstraint(check=Q(x__gt=0), name="c")
e = CheckConstraint(check=Q(x__gt=0), name="c")
print("noneNone eq:", d==e)
ok &= (d == e)

# unique
ua = UniqueConstraint(fields=["x"], name="u", violation_error_code="A")
ub = UniqueConstraint(fields=["x"], name="u", violation_error_code="B")
print("unique A==B:", ua==ub)
ok &= (ua != ub)

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 6: repr includes ' violation_error_code=<repr>' only when set, before message segment.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_I18N=False)
    django.setup()

import sys
from django.db.models import Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint

ok = True
c = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="mycode")
r = repr(c)
print("repr with code:", r)
ok &= (" violation_error_code='mycode'" in r)

c2 = CheckConstraint(check=Q(x__gt=0), name="c2")
r2 = repr(c2)
print("repr no code:", r2)
ok &= ("violation_error_code" not in r2)

# ordering: code before message
c3 = CheckConstraint(check=Q(x__gt=0), name="c3", violation_error_code="cd", violation_error_message="mm")
r3 = repr(c3)
print("repr both:", r3)
ok &= ("violation_error_code" in r3 and "violation_error_message" in r3)
ok &= (r3.index("violation_error_code") < r3.index("violation_error_message"))

# unique repr
u = UniqueConstraint(fields=["x"], name="u", violation_error_code="uc")
ru = repr(u)
print("unique repr:", ru)
ok &= (" violation_error_code='uc'" in ru)

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3: field-based UniqueConstraint violation uses model unique_error_message:
# code "unique" (single field) / "unique_together" (multi), and NOT replaced by configured code/message.
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()

from django.db import models, connection
from django.core.exceptions import ValidationError

class M(models.Model):
    a = models.IntegerField()
    b = models.IntegerField()
    class Meta:
        app_label = "auth"
        constraints = [
            models.UniqueConstraint(fields=["a"], name="uniq_a",
                                    violation_error_code="CONFIGURED", violation_error_message="CONFIGMSG"),
            models.UniqueConstraint(fields=["a", "b"], name="uniq_ab",
                                    violation_error_code="CONFIGURED2", violation_error_message="CONFIGMSG2"),
        ]

with connection.schema_editor() as se:
    se.create_model(M)

M.objects.create(a=1, b=2)
ok = True
c_single = M._meta.constraints[0]
raised = None
try:
    c_single.validate(M, M(a=1, b=99))
except ValidationError as e:
    raised = e
print("single: code=", getattr(raised,'code',None), "msg=", getattr(raised,'messages',None))
ok &= raised is not None and raised.code == "unique"
ok &= raised is not None and "CONFIGMSG" not in " ".join(raised.messages)

M.objects.create(a=5, b=6)
c_multi = M._meta.constraints[1]
raised2 = None
try:
    c_multi.validate(M, M(a=5, b=6))
except ValidationError as e:
    raised2 = e
print("multi: code=", getattr(raised2,'code',None), "msg=", getattr(raised2,'messages',None))
ok &= raised2 is not None and raised2.code == "unique_together"
ok &= raised2 is not None and "CONFIGMSG2" not in " ".join(raised2.messages)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1/1.2/1.3/1.4: constructor accepts violation_error_code, stores it, defaults None,
# subclasses forward to base identically. (POSITIVE CONTROL: fails at base where kwarg absent.)
import sys
from django.db.models import Q
from django.db.models.constraints import BaseConstraint, CheckConstraint, UniqueConstraint

ok = True
# BaseConstraint
b = BaseConstraint(name="b", violation_error_code="mycode")
print("BaseConstraint.violation_error_code =", b.violation_error_code)
ok &= (b.violation_error_code == "mycode")
b2 = BaseConstraint(name="b2")
print("BaseConstraint default =", b2.violation_error_code)
ok &= (b2.violation_error_code is None)

# CheckConstraint
c = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="cc")
print("CheckConstraint.violation_error_code =", c.violation_error_code)
ok &= (c.violation_error_code == "cc")
c2 = CheckConstraint(check=Q(x__gt=0), name="c2")
print("CheckConstraint default =", c2.violation_error_code)
ok &= (c2.violation_error_code is None)

# UniqueConstraint
u = UniqueConstraint(fields=["x"], name="u", violation_error_code="uu")
print("UniqueConstraint.violation_error_code =", u.violation_error_code)
ok &= (u.violation_error_code == "uu")
u2 = UniqueConstraint(fields=["x"], name="u2")
print("UniqueConstraint default =", u2.violation_error_code)
ok &= (u2.violation_error_code is None)

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on the gold-patched tree; each maps to a requirement:
- probe_1 (Req 1.1/1.2/1.3/1.4): constructor accepts violation_error_code on BaseConstraint/CheckConstraint/UniqueConstraint, stores it, defaults None. POSITIVE CONTROL — VIOLATED at base (kwarg absent -> TypeError), HOLDS patched.
- probe_2 (Req 2.1, 2.6): CheckConstraint.validate raises ValidationError.code == configured code; message stays the default message (independent of code).
- probe_3 (Req 2.4, 2.5): no configured code -> ValidationError.code is None; no violation -> nothing raised.
- probe_4 (Req 4.1/4.2/4.3/4.4): deconstruct includes violation_error_code only when set, omits when None, preserves check/name/fields and message-under-its-own-condition.
- probe_5 (Req 5): code participates in equality (differ->unequal, same/both-None->equal) for Check & Unique.
- probe_6 (Req 6): repr shows ' violation_error_code=<repr>' only when set, before the message segment.
- probe_7 (Req 3.1/3.2/3.3): field-based UniqueConstraint violation uses the model-derived unique error — code 'unique' (single) / 'unique_together' (multi) and the '...already exists' message, NOT replaced by configured code/message. Real sqlite DB.

Base run: probe_1 VIOLATED at base, HOLDS patched => positive control discriminates.

CANDIDATE PATCHES: two constructed.
1) An initial candidate added code=self.violation_error_code to the field-based unique branch (would violate Req 3.2). It applied and probe_7 still HELD — because Django ignores the code= arg when the first arg is a pre-built ValidationError message object, so this candidate is behaviorally EQUIVALENT to gold, not wrong; discarded as a non-discriminator.
2) SUBMITTED weak.diff = gold minus the CheckConstraint.validate code wiring (reverts to `raise ValidationError(self.get_violation_error_message())`, a partial fix a weak reading permits: storage/repr/eq/deconstruct all present but code never surfaced on the check error). Applies cleanly at base_commit. probe_2 REJECTS it (VIOLATED: code stays None instead of configured 'my_code'), while probe_1 still HOLDS (storage unaffected) — demonstrating the suite discriminates a wrong/partial implementation.

>=5 distinct probes hold patched, positive control discriminates base vs patched, and >=1 candidate patch is exercised and rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1/1.2/1.3/1.4: constructor accepts violation_error_code, stores it, defaults None,
# subclasses forward to base identically. (POSITIVE CONTROL: fails at base where kwarg absent.)
import sys
from django.db.models import Q
from django.db.models.constraints import BaseConstraint, CheckConstraint, UniqueConstraint

ok = True
# BaseConstraint
b = BaseConstraint(name="b", violation_error_code="mycode")
print("BaseConstraint.violation_error_code =", b.violation_error_code)
ok &= (b.violation_error_code == "mycode")
b2 = BaseConstraint(name="b2")
print("BaseConstraint default =", b2.violation_error_code)
ok &= (b2.violation_error_code is None)

# CheckConstraint
c = CheckConstraint(check=Q(x__gt=0), name="c", violation_error_code="cc")
print("CheckConstraint.violation_error_code =", c.violation_error_code)
ok &= (c.violation_error_code == "cc")
c2 = CheckConstraint(check=Q(x__gt=0), name="c2")
print("CheckConstraint default =", c2.violation_error_code)
ok &= (c2.violation_error_code is None)

# UniqueConstraint
u = UniqueConstraint(fields=["x"], name="u", violation_error_code="uu")
print("UniqueConstraint.violation_error_code =", u.violation_error_code)
ok &= (u.violation_error_code == "uu")
u2 = UniqueConstraint(fields=["x"], name="u2")
print("UniqueConstraint default =", u2.violation_error_code)
ok &= (u2.violation_error_code is None)

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on the gold-patched tree; each maps to a requirement:
- probe_1 (Req 1.1/1.2/1.3/1.4): constructor accepts violation_error_code on BaseConstraint/CheckConstraint/UniqueConstraint, stores it, defaults None. POSITIVE CONTROL — VIOLATED at base (kwarg absent -> TypeError), HOLDS patched.
- probe_2 (Req 2.1, 2.6): CheckConstraint.validate raises ValidationError.code == configured code; message stays the default message (independent of code).
- probe_3 (Req 2.4, 2.5): no configured code -> ValidationError.code is None; no violation -> nothing raised.
- probe_4 (Req 4.1/4.2/4.3/4.4): deconstruct includes violation_error_code only when set, omits when None, preserves check/name/fields and message-under-its-own-condition.
- probe_5 (Req 5): code participates in equality (differ->unequal, same/both-None->equal) for Check & Unique.
- probe_6 (Req 6): repr shows ' violation_error_code=<repr>' only when set, before the message segment.
- probe_7 (Req 3.1/3.2/3.3): field-based UniqueConstraint violation uses the model-derived unique error — code 'unique' (single) / 'unique_together' (multi) and the '...already exists' message, NOT replaced by configured code/message. Real sqlite DB.

Base run: probe_1 VIOLATED at base, HOLDS patched => positive control discriminates.

CANDIDATE PATCHES: two constructed.
1) An initial candidate added code=self.violation_error_code to the field-based unique branch (would violate Req 3.2). It applied and probe_7 still HELD — because Django ignores the code= arg when the first arg is a pre-built ValidationError message object, so this candidate is behaviorally EQUIVALENT to gold, not wrong; discarded as a non-discriminator.
2) SUBMITTED weak.diff = gold minus the CheckConstraint.validate code wiring (reverts to `raise ValidationError(self.get_violation_error_message())`, a partial fix a weak reading permits: storage/repr/eq/deconstruct all present but code never surfaced on the check error). Applies cleanly at base_commit. probe_2 REJECTS it (VIOLATED: code stays None instead of configured 'my_code'), while probe_1 still HOLDS (storage unaffected) — demonstrating the suite discriminates a wrong/partial implementation.

>=5 distinct probes hold patched, positive control discriminates base vs patched, and >=1 candidate patch is exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Ran two probes via nl_attack probe. probe.py: CheckConstraint/UniqueConstraint store code, default None; deconstruct includes code only when set; equality differentiates by code and treats None==None equal; repr includes violation_error_code='...' only when set, ordered before message. probe2.py (live sqlite): FIELD code='unique' msg='M with this F already exists.'; COND code='CONDCODE'; CHECK code='CHK'; CHECK none code=None. Requirements pin the changed observable behavior across all constraint classes/branches rather than a narrow slice, and correctly preserve legacy field-unique semantics.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the feature (adding an optional `violation_error_code` kwarg mirroring `violation_error_message`) entirely in behavioral terms. Everything material is either public in the problem_statement (customize the ValidationError code, add a parameter to BaseConstraint, docs recommend descriptive error codes) or legitimate localization of the change: naming the modules/classes/methods edited (`django/db/models/constraints.py`, `django/contrib/postgres/constraints.py`, BaseConstraint/CheckConstraint/UniqueConstraint/ExclusionConstraint, validate/deconstruct/repr/__eq__). `violation_error_code` is the actual new public API (paraphrased in the problem statement), not a fix-invented private identifier.

No test-only artifacts appear: none of the test literals ('custom_code', 'fake_discount', 'more_than_one', 'baz', 'overlapping_must_be_excluded', 'discount is fake') are present; no test file paths, function/class names, parametrization ids, or quoted test/gold code. The `"unique"`/`"unique_together"` distinction in Req 3.2 describes pre-existing, publicly-documented Django model uniqueness error codes (framework behavior the fix preserves), stated more generally than the single test that checks only `unique_together` — behavioral description, not test reconstruction. The enumeration of unconditional vs. conditional Exclusion/Unique validate branches mirrors the code structure being changed, not the test parametrization. This is exactly the intended translation of test-checked behavior into requirements.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
