# P2 adversarial audit — django__django-14238

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models.fields import AutoField, BigAutoField

class MyBigAuto(BigAutoField):
    pass

class Deeper(MyBigAuto):
    pass

r1 = issubclass(MyBigAuto, AutoField)
r2 = issubclass(Deeper, AutoField)
print("issubclass(MyBigAuto, AutoField) =", r1)
print("issubclass(Deeper(transitive), AutoField) =", r2)
sys.exit(0 if (r1 and r2) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models.fields import AutoField, SmallAutoField

class MySmallAuto(SmallAutoField):
    pass

class Deeper(MySmallAuto):
    pass

r1 = issubclass(MySmallAuto, AutoField)
r2 = issubclass(Deeper, AutoField)
print("issubclass(MySmallAuto, AutoField) =", r1)
print("issubclass(Deeper(transitive), AutoField) =", r2)
sys.exit(0 if (r1 and r2) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models.fields import (
    AutoField, BigAutoField, SmallAutoField, IntegerField, CharField,
)

# Req 2: designated classes recognized
checks = {
    "issubclass(BigAutoField, AutoField)": (issubclass(BigAutoField, AutoField), True),
    "issubclass(SmallAutoField, AutoField)": (issubclass(SmallAutoField, AutoField), True),
    "issubclass(AutoField, AutoField)": (issubclass(AutoField, AutoField), True),
    # Req 1.4: unrelated field types rejected
    "issubclass(IntegerField, AutoField)": (issubclass(IntegerField, AutoField), False),
    "issubclass(CharField, AutoField)": (issubclass(CharField, AutoField), False),
    "issubclass(int, AutoField)": (issubclass(int, AutoField), False),
}
ok = True
for k, (got, exp) in checks.items():
    print(k, "=", got, "(expected", exp, ")")
    if got != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models.fields import AutoField, BigAutoField, SmallAutoField, CharField

class MyBigAuto(BigAutoField):
    pass

# Req 2.4: instances of designated classes + their subclasses report as AutoField
ok = True
cases = [
    ("AutoField()", isinstance(AutoField(), AutoField), True),
    ("BigAutoField()", isinstance(BigAutoField(), AutoField), True),
    ("SmallAutoField()", isinstance(SmallAutoField(), AutoField), True),
    ("MyBigAuto()", isinstance(MyBigAuto(), AutoField), True),
    ("CharField()", isinstance(CharField(), AutoField), False),
]
for name, got, exp in cases:
    print("isinstance", name, "AutoField =", got, "(expected", exp, ")")
    if got != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, textwrap

d = tempfile.mkdtemp()
# a minimal app package whose AppConfig does NOT set default_auto_field
os.makedirs(os.path.join(d, "myapp"))
open(os.path.join(d, "myapp", "__init__.py"), "w").close()
with open(os.path.join(d, "myapp", "fields.py"), "w") as f:
    f.write(textwrap.dedent("""
        from django.db.models.fields import BigAutoField
        class MyBigAutoField(BigAutoField):
            pass
    """))
sys.path.insert(0, d)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["myapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="myapp.fields.MyBigAutoField",
)
django.setup()

from django.db import models
from myapp.fields import MyBigAutoField

class NoPkModel(models.Model):
    class Meta:
        app_label = "myapp"

pk = NoPkModel._meta.pk
print("auto pk type:", type(pk).__name__)
print("isinstance MyBigAutoField:", isinstance(pk, MyBigAutoField))
sys.exit(0 if isinstance(pk, MyBigAutoField) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, os, tempfile

d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, "myapp6"))
open(os.path.join(d, "myapp6", "__init__.py"), "w").close()
sys.path.insert(0, d)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["myapp6"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="django.db.models.CharField",
)
django.setup()

from django.core.exceptions import ImproperlyConfigured
from django.db import models

# Req 3.3 / 4.2: a non-auto field class named by DEFAULT_AUTO_FIELD must still error.
raised = False
msg = ""
try:
    class BadModel(models.Model):
        class Meta:
            app_label = "myapp6"
except (ValueError, ImproperlyConfigured) as e:
    raised = True
    msg = str(e)
print("raised:", raised)
print("msg:", msg)
ok = raised and "must subclass AutoField" in msg
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models.fields import AutoField, BigAutoField

class MyBigAuto(BigAutoField):
    pass

class Deeper(MyBigAuto):
    pass

r1 = issubclass(MyBigAuto, AutoField)
r2 = issubclass(Deeper, AutoField)
print("issubclass(MyBigAuto, AutoField) =", r1)
print("issubclass(Deeper(transitive), AutoField) =", r2)
sys.exit(0 if (r1 and r2) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: recognize direct/transitive subclasses of BigAutoField/SmallAutoField as AutoField via AutoFieldMeta.__subclasscheck__ (subclass relation, not identity), while preserving existing recognition/rejection and DEFAULT_AUTO_FIELD behavior.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (Req 1.1, 1.3): issubclass(MyBigAuto, AutoField) and transitive subclass -> True. POSITIVE CONTROL: FAILS at base (False), holds patched.
- probe_2 (Req 1.2, 1.3): SmallAutoField subclass direct+transitive -> True.
- probe_3 (Req 1.4, 2.1-2.3): designated classes True; unrelated IntegerField/CharField/int -> False (fallback to ordinary check). Holds at base too (regression criterion).
- probe_4 (Req 2.4): isinstance for AutoField/Big/Small + custom subclass True; CharField False.
- probe_5 (Req 3.1, 3.2, 4.1): DEFAULT_AUTO_FIELD='myapp.fields.MyBigAutoField' (BigAutoField subclass) -> model auto pk is instance of that class. FAILS at base, holds patched. Note: used a custom app without default_auto_field override; contenttypes app overrides DEFAULT_AUTO_FIELD.
- probe_6 (Req 3.3, 4.2): non-auto field (CharField) named by DEFAULT_AUTO_FIELD still raises 'must subclass AutoField' ValueError. Holds both base and patched (regression).

Discrimination: base-tree runs of probes 1,2,5 FAIL (issue reproduced); probes 3,6 hold at base (they encode preserved behavior).

Candidate wrong-fix patches BOTH REJECTED by suite:
- weak.diff (issubclass(subclass, IntegerField)): over-broad; rejected by probe_3 (IntegerField/CharField wrongly True).
- partial.diff (issubclass(subclass, BigAutoField) only): rejected by probe_2 and probe_3 (SmallAutoField no longer recognized).

Suite discriminates wrong implementations in both directions (too-broad and too-narrow). No too-weak finding. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models.fields import AutoField, BigAutoField

class MyBigAuto(BigAutoField):
    pass

class Deeper(MyBigAuto):
    pass

r1 = issubclass(MyBigAuto, AutoField)
r2 = issubclass(Deeper, AutoField)
print("issubclass(MyBigAuto, AutoField) =", r1)
print("issubclass(Deeper(transitive), AutoField) =", r2)
sys.exit(0 if (r1 and r2) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: recognize direct/transitive subclasses of BigAutoField/SmallAutoField as AutoField via AutoFieldMeta.__subclasscheck__ (subclass relation, not identity), while preserving existing recognition/rejection and DEFAULT_AUTO_FIELD behavior.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (Req 1.1, 1.3): issubclass(MyBigAuto, AutoField) and transitive subclass -> True. POSITIVE CONTROL: FAILS at base (False), holds patched.
- probe_2 (Req 1.2, 1.3): SmallAutoField subclass direct+transitive -> True.
- probe_3 (Req 1.4, 2.1-2.3): designated classes True; unrelated IntegerField/CharField/int -> False (fallback to ordinary check). Holds at base too (regression criterion).
- probe_4 (Req 2.4): isinstance for AutoField/Big/Small + custom subclass True; CharField False.
- probe_5 (Req 3.1, 3.2, 4.1): DEFAULT_AUTO_FIELD='myapp.fields.MyBigAutoField' (BigAutoField subclass) -> model auto pk is instance of that class. FAILS at base, holds patched. Note: used a custom app without default_auto_field override; contenttypes app overrides DEFAULT_AUTO_FIELD.
- probe_6 (Req 3.3, 4.2): non-auto field (CharField) named by DEFAULT_AUTO_FIELD still raises 'must subclass AutoField' ValueError. Holds both base and patched (regression).

Discrimination: base-tree runs of probes 1,2,5 FAIL (issue reproduced); probes 3,6 hold at base (they encode preserved behavior).

Candidate wrong-fix patches BOTH REJECTED by suite:
- weak.diff (issubclass(subclass, IntegerField)): over-broad; rejected by probe_3 (IntegerField/CharField wrongly True).
- partial.diff (issubclass(subclass, BigAutoField) only): rejected by probe_2 and probe_3 (SmallAutoField no longer recognized).

Suite discriminates wrong implementations in both directions (too-broad and too-narrow). No too-weak finding. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (patched vs --base) confirmed: patched recognizes MyBig(BigAutoField), MyBig2(MyBig), MySmall(SmallAutoField) as AutoField subclasses/instances, keeps BigAutoField/SmallAutoField/AutoField recognized, and rejects Unrelated; base fails on the first subclass assertion. Requirements pin the changed observable behavior (identity→subclass-relation), not a narrow slice. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The problem_statement is unusually rich: it already publishes the exact reproducer (`class MyBigAutoField(models.BigAutoField): pass`, DEFAULT_AUTO_FIELD='example.core.models.MyBigAutoField'), the crashing call path (Options._get_default_pk_class), the verbatim ValueError message ('Primary key ... must subclass AutoField'), and the fix pointer ('fixed in AutoFieldMeta.__subclasscheck__ by allowing subclasses of those classes in the _subclasses property'). Every identifier in requirements.md — AutoFieldMeta, __subclasscheck__, __instancecheck__, _subclasses, BigAutoField, SmallAutoField, _get_default_pk_class — is thus either public or legitimate module/function localization. The hidden test adds MySmallAutoField and asserts pk isinstance of the configured class; the requirements translate this into behavioral criteria (recognize transitive subclasses of both designated classes; model pk is an instance of the configured class) without quoting test code, test names/paths (test_autofield.py, test_default_pk.py, AutoFieldInheritanceTests, test_default_auto_field_setting_bigautofield_subclass), parametrization ids, or any fix-invented identifier. The gold edit invents no new symbol (issubclass vs `in`), so there is nothing solution-vocabulary to leak. Requirement enumerations mirror the described behavior/domain, not the test parametrization. No semantic reconstruction of the hidden tests beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
