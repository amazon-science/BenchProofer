# P2 adversarial audit — django__django-11820

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control. Req1.2: ordering ('parent__pk',) => no models.E015.
HOLDS patched, FAILS at base (base wrongly raises E015)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes',
        'django.contrib.auth'], DATABASES={}, SILENCED_SYSTEM_CHECKS=[])
django.setup()
from django.db import models

class Parent(models.Model):
    class Meta: app_label = 'probeapp'

class Child(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta:
        app_label = 'probeapp'
        ordering = ('parent__pk',)

errs = [e for e in Child.check() if getattr(e, 'id', None) == 'models.E015']
print("E015 errors for parent__pk:", errs)
raise SystemExit(0 if not errs else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.3: ('parent__field1__field2',) => exactly one models.E015.
Second bug: base wrongly ACCEPTS (walk kept current model past non-relation field)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes',
        'django.contrib.auth'], DATABASES={}, SILENCED_SYSTEM_CHECKS=[])
django.setup()
from django.db import models

class Parent(models.Model):
    field1 = models.CharField(max_length=100)
    field2 = models.CharField(max_length=100)
    class Meta: app_label = 'probeapp'

class Child(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta:
        app_label = 'probeapp'
        ordering = ('parent__field1__field2',)

errs = [e for e in Child.check() if getattr(e, 'id', None) == 'models.E015']
print("E015 errors:", errs)
ok = len(errs) == 1 and 'parent__field1__field2' in errs[0].msg
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3 regressions preserved:
 3.1 relation field directly -> no error
 3.2 nonexistent field -> E015
 3.3 relation to nonexistent field on related -> E015
 3.6 two resolvable related fields -> no error
 3.8 pk alias used directly -> no error
All must hold together."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes',
        'django.contrib.auth'], DATABASES={}, SILENCED_SYSTEM_CHECKS=[])
django.setup()
from django.db import models

def e015(model):
    return [e for e in model.check() if getattr(e,'id',None)=='models.E015']

class GP(models.Model):
    name = models.CharField(max_length=10)
    class Meta: app_label='probeapp'

class Parent(models.Model):
    gp = models.ForeignKey(GP, models.CASCADE)
    name = models.CharField(max_length=10)
    class Meta: app_label='probeapp'

# 3.1 relation directly
class M31(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta: app_label='probeapp'; ordering=('parent',)
# 3.2 nonexistent
class M32(models.Model):
    class Meta: app_label='probeapp'; ordering=('nope',)
# 3.3 relation to nonexistent on related
class M33(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta: app_label='probeapp'; ordering=('parent__nope',)
# 3.6 two related fields resolvable
class M36(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta: app_label='probeapp'; ordering=('parent__gp__name',)
# 3.8 pk direct
class M38(models.Model):
    name = models.CharField(max_length=10)
    class Meta: app_label='probeapp'; ordering=('pk',)

r = {
 '3.1 parent': len(e015(M31))==0,
 '3.2 nope': len(e015(M32))==1,
 '3.3 parent__nope': len(e015(M33))==1,
 '3.6 parent__gp__name': len(e015(M36))==0,
 '3.8 pk direct': len(e015(M38))==0,
}
print(r)
raise SystemExit(0 if all(r.values()) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.4: registered transform/lookup accepted -> no error.
Uses Lower registered on CharField; ordering ('test__lower',)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes',
        'django.contrib.auth'], DATABASES={}, SILENCED_SYSTEM_CHECKS=[])
django.setup()
from django.db import models
from django.db.models.functions import Lower
from django.test.utils import register_lookup

class M(models.Model):
    test = models.CharField(max_length=100)
    class Meta:
        app_label='probeapp'
        ordering=('test__lower',)

with register_lookup(models.CharField, Lower):
    errs = [e for e in M.check() if getattr(e,'id',None)=='models.E015']
print("E015 with registered lookup:", errs)
raise SystemExit(0 if not errs else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.9 + 3.5: expressions/? skipped, leading '-' stripped;
nonexistent first segment -> E015.
Checks: ordering ('?', OrderBy expr, '-parent') all fine; ('-nope',) -> E015 naming '-nope' stripped? gold names the entry text after strip."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes',
        'django.contrib.auth'], DATABASES={}, SILENCED_SYSTEM_CHECKS=[])
django.setup()
from django.db import models
from django.db.models.expressions import OrderBy, F

class Parent(models.Model):
    class Meta: app_label='probeapp'

# ? and expression and descending valid relation -> no error
class Mok(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta:
        app_label='probeapp'
        ordering=('?', OrderBy(F('parent')), '-parent')

# descending on nonexistent -> E015, entry named with stripped '-'
class Mbad(models.Model):
    class Meta:
        app_label='probeapp'
        ordering=('-nope',)

ok_errs=[e for e in Mok.check() if getattr(e,'id',None)=='models.E015']
bad_errs=[e for e in Mbad.check() if getattr(e,'id',None)=='models.E015']
print("ok(skip/strip) E015:", ok_errs)
print("bad(-nope) E015:", bad_errs)
cond = (len(ok_errs)==0 and len(bad_errs)==1 and "'nope'" in bad_errs[0].msg)
raise SystemExit(0 if cond else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req1.2: ordering ('parent__pk',) => no models.E015.
HOLDS patched, FAILS at base (base wrongly raises E015)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes',
        'django.contrib.auth'], DATABASES={}, SILENCED_SYSTEM_CHECKS=[])
django.setup()
from django.db import models

class Parent(models.Model):
    class Meta: app_label = 'probeapp'

class Child(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta:
        app_label = 'probeapp'
        ordering = ('parent__pk',)

errs = [e for e in Child.check() if getattr(e, 'id', None) == 'models.E015']
print("E015 errors for parent__pk:", errs)
raise SystemExit(0 if not errs else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes covering both fixed behaviors and Req3 regressions. probe_1 (Req1.2, positive control): ('parent__pk',) => no E015; HOLDS patched, FAILS at base (base raises E015). probe_2 (Req2.3): ('parent__field1__field2',) => exactly one E015; HOLDS patched, FAILS at base (base wrongly accepts). probe_3 (Req3.1/3.2/3.3/3.6/3.8 regressions): all HOLD. probe_4 (Req3.4 registered Lower lookup): HOLDS. probe_5 (Req3.9 skip ?/expr + strip '-', Req3.5 nonexistent first segment): HOLDS. Two requirements-partial candidate patches constructed and BOTH rejected by the suite: weak_pkonly (pk fix only, no walk-stop) => probe_2 VIOLATED; weak_stoponly (walk-stop only, no pk fix) => probe_1 VIOLATED. Suite discriminates each half of the gold fix independently. No probe fails on the patched tree; positive control discriminates base vs patched.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req1.2: ordering ('parent__pk',) => no models.E015.
HOLDS patched, FAILS at base (base wrongly raises E015)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes',
        'django.contrib.auth'], DATABASES={}, SILENCED_SYSTEM_CHECKS=[])
django.setup()
from django.db import models

class Parent(models.Model):
    class Meta: app_label = 'probeapp'

class Child(models.Model):
    parent = models.ForeignKey(Parent, models.CASCADE)
    class Meta:
        app_label = 'probeapp'
        ordering = ('parent__pk',)

errs = [e for e in Child.check() if getattr(e, 'id', None) == 'models.E015']
print("E015 errors for parent__pk:", errs)
raise SystemExit(0 if not errs else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes covering both fixed behaviors and Req3 regressions. probe_1 (Req1.2, positive control): ('parent__pk',) => no E015; HOLDS patched, FAILS at base (base raises E015). probe_2 (Req2.3): ('parent__field1__field2',) => exactly one E015; HOLDS patched, FAILS at base (base wrongly accepts). probe_3 (Req3.1/3.2/3.3/3.6/3.8 regressions): all HOLD. probe_4 (Req3.4 registered Lower lookup): HOLDS. probe_5 (Req3.9 skip ?/expr + strip '-', Req3.5 nonexistent first segment): HOLDS. Two requirements-partial candidate patches constructed and BOTH rejected by the suite: weak_pkonly (pk fix only, no walk-stop) => probe_2 VIOLATED; weak_stoponly (walk-stop only, no pk fix) => probe_1 VIOLATED. Suite discriminates each half of the gold fix independently. No probe fails on the patched tree; positive control discriminates base vs patched.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes: author__pk patched=[] base=['models.E015'] (Req1.2 fix). title__title/title__author/author__name__name patched=['models.E015'] base=[] (Req2 non-relation-field false-negative fix). title__lower=[] (Req2.2/Req3.4 transform exception), title__isnull=['models.E015'] both. author=[], nope=E015, author__nope=E015, pk=[], title=[], -author__pk=[] (Req3 preservation). Requirements correctly identify both defects from the issue and the wrong-boundary trap is avoided — the walk's _cls=None after non-relation field is the actual changed behavior and is modeled.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes both defects behaviorally without transmitting the hidden tests. Defect #1 (pk-of-related false positive) is public in problem_statement (example 'option__pk'). Defect #2 (stop walk after non-relation field) is derived from the gold edit's `else: _cls = None`, but is described as a behavioral requirement — legitimate translation, not test transmission. Identifiers named (_check_ordering, Options.get_field, Options.pk, get_transform, models.E015, LOOKUP_SEP/__) are all real Django API used to localize the change, none fix-invented. The two test-shaped ACs use abstract placeholders (`<relation>__pk`, `<relation>__<value_field>__<extra>`), NOT the concrete test class/field names (Parent/Child/field1/field2) or verbatim test code. No test names, file paths, parametrization ids, or quoted gold/test lines appear. `<relation>__pk` closely mirrors the public problem-statement example. The enumerated ACs describe the general E015 validation contract as behavior rather than mirroring the FAIL_TO_PASS parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
