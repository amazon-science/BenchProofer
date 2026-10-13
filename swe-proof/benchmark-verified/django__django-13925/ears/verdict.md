# P2 adversarial audit — django__django-13925

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 3: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 2 were not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2 + positive control: an MTI child whose PK is an auto-created
inheritance-link OneToOne back to a concrete ancestor SHALL NOT get models.W042,
even when no DEFAULT_AUTO_FIELD is configured.

HOLDS iff the child model emits no W042. On base (buggy) code the child DOES get
W042 -> probe fails at base (discriminating power)."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    # NB: DEFAULT_AUTO_FIELD intentionally NOT set -> not overridden.
)
import sys, types
from importlib.machinery import ModuleSpec
mod = types.ModuleType('probeapp')
mod.__path__ = ['/testbed']
mod.__file__ = '/testbed/__init__.py'
mod.__spec__ = ModuleSpec('probeapp', loader=None, origin='/testbed/__init__.py', is_package=True)
mod.__spec__.submodule_search_locations = ['/testbed']
sys.modules['probeapp'] = mod
django.setup()

from django.db import models

class Ancestor(models.Model):
    name = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

class Child(Ancestor):  # MTI: auto-created parent_link OneToOne PK
    extra = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

pk = Child._meta.pk
print("Child pk:", type(pk).__name__, "auto_created=", pk.auto_created,
      "parent_link=", getattr(getattr(pk, 'remote_field', None), 'parent_link', None))

errs = Child._check_default_pk()
ids = [e.id for e in errs]
print("Child _check_default_pk errors:", ids)

if 'models.W042' in ids:
    print("FAIL: W042 emitted for inheritance-link child")
    sys.exit(1)
print("OK: no W042 for inheritance-link child")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2: a standalone model with an auto-created PK and NO
DEFAULT_AUTO_FIELD configured SHALL get exactly one models.W042, whose subject
is that model and whose id/message/hint text is preserved. This is a 'SHALL
keep' regression criterion (holds on base AND patched)."""
import django, sys, types
from importlib.machinery import ModuleSpec
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
)
mod = types.ModuleType('probeapp'); mod.__path__=['/testbed']; mod.__file__='/testbed/__init__.py'
mod.__spec__ = ModuleSpec('probeapp', loader=None, origin='/testbed/__init__.py', is_package=True)
mod.__spec__.submodule_search_locations=['/testbed']
sys.modules['probeapp']=mod
django.setup()
from django.db import models

class Plain(models.Model):
    name = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

errs = Plain._check_default_pk()
print("errors:", [(e.id, e.obj) for e in errs])
w042 = [e for e in errs if e.id == 'models.W042']
if len(w042) != 1:
    print("FAIL: expected exactly one W042, got", len(w042)); sys.exit(1)
e = w042[0]
if e.obj is not Plain:
    print("FAIL: subject is not the model:", e.obj); sys.exit(1)
msg, hint = e.msg, e.hint
print("msg:", repr(msg)); print("hint:", repr(hint))
if 'auto-created primary key' not in msg.lower():
    print("FAIL: message text changed"); sys.exit(1)
if 'DEFAULT_AUTO_FIELD' not in hint or 'default_auto_field' not in hint:
    print("FAIL: hint must reference project setting and app default_auto_field"); sys.exit(1)
print("OK: exactly one W042 with preserved id/msg/hint, subject=model")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.4/2.5: IF DEFAULT_AUTO_FIELD is configured at project level, THEN no
W042 for a plain auto-pk model. 'SHALL keep' regression (holds base+patched)."""
import django, sys, types
from importlib.machinery import ModuleSpec
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
)
mod = types.ModuleType('probeapp'); mod.__path__=['/testbed']; mod.__file__='/testbed/__init__.py'
mod.__spec__ = ModuleSpec('probeapp', loader=None, origin='/testbed/__init__.py', is_package=True)
mod.__spec__.submodule_search_locations=['/testbed']
sys.modules['probeapp']=mod
django.setup()
from django.db import models

class Plain(models.Model):
    name = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

errs = Plain._check_default_pk()
ids = [e.id for e in errs]
print("errors:", ids, "DEFAULT_AUTO_FIELD overridden=", settings.is_overridden('DEFAULT_AUTO_FIELD'))
if 'models.W042' in ids:
    print("FAIL: W042 emitted despite DEFAULT_AUTO_FIELD configured"); sys.exit(1)
print("OK: no W042 when DEFAULT_AUTO_FIELD configured")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3: a model that explicitly declares its own primary key (pk NOT
auto-created) SHALL NOT get W042. 'SHALL keep' regression."""
import django, sys, types
from importlib.machinery import ModuleSpec
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
)
mod = types.ModuleType('probeapp'); mod.__path__=['/testbed']; mod.__file__='/testbed/__init__.py'
mod.__spec__ = ModuleSpec('probeapp', loader=None, origin='/testbed/__init__.py', is_package=True)
mod.__spec__.submodule_search_locations=['/testbed']
sys.modules['probeapp']=mod
django.setup()
from django.db import models

class Explicit(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

print("pk auto_created=", Explicit._meta.pk.auto_created)
errs = Explicit._check_default_pk()
ids = [e.id for e in errs]
print("errors:", ids)
if 'models.W042' in ids:
    print("FAIL: W042 emitted for explicit pk model"); sys.exit(1)
print("OK: no W042 for explicit-pk model")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.1 + Req 1.3: per-model reporting across a chain. Ancestor leaves pk
unspecified (auto AutoField), Child_auto uses auto inheritance link, Child_expl
explicitly declares its own parent_link OneToOne. With no DEFAULT_AUTO_FIELD:
  - Ancestor SHALL get W042
  - both children SHALL NOT get W042
Also verifies independence (Req 3.4)."""
import django, sys, types
from importlib.machinery import ModuleSpec
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
)
mod = types.ModuleType('probeapp'); mod.__path__=['/testbed']; mod.__file__='/testbed/__init__.py'
mod.__spec__ = ModuleSpec('probeapp', loader=None, origin='/testbed/__init__.py', is_package=True)
mod.__spec__.submodule_search_locations=['/testbed']
sys.modules['probeapp']=mod
django.setup()
from django.db import models

class Ancestor(models.Model):
    name = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

class ChildAuto(Ancestor):
    extra = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

class ChildExpl(Ancestor):
    ancestor_ptr = models.OneToOneField(Ancestor, on_delete=models.CASCADE,
                                         parent_link=True, primary_key=True)
    extra = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

def w042(cls):
    return 'models.W042' in [e.id for e in cls._check_default_pk()]

a, ca, ce = w042(Ancestor), w042(ChildAuto), w042(ChildExpl)
print("ChildExpl pk auto_created=", ChildExpl._meta.pk.auto_created,
      "parent_link=", ChildExpl._meta.pk.remote_field.parent_link)
print("W042: Ancestor=", a, "ChildAuto=", ca, "ChildExpl=", ce)
ok = a and (not ca) and (not ce)
if not ok:
    print("FAIL: expected Ancestor=True, both children=False"); sys.exit(1)
print("OK: W042 for ancestor only, suppressed for both children")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1/1.2 + positive control: an MTI child whose PK is an auto-created
inheritance-link OneToOne back to a concrete ancestor SHALL NOT get models.W042,
even when no DEFAULT_AUTO_FIELD is configured.

HOLDS iff the child model emits no W042. On base (buggy) code the child DOES get
W042 -> probe fails at base (discriminating power)."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    # NB: DEFAULT_AUTO_FIELD intentionally NOT set -> not overridden.
)
import sys, types
from importlib.machinery import ModuleSpec
mod = types.ModuleType('probeapp')
mod.__path__ = ['/testbed']
mod.__file__ = '/testbed/__init__.py'
mod.__spec__ = ModuleSpec('probeapp', loader=None, origin='/testbed/__init__.py', is_package=True)
mod.__spec__.submodule_search_locations = ['/testbed']
sys.modules['probeapp'] = mod
django.setup()

from django.db import models

class Ancestor(models.Model):
    name = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

class Child(Ancestor):  # MTI: auto-created parent_link OneToOne PK
    extra = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

pk = Child._meta.pk
print("Child pk:", type(pk).__name__, "auto_created=", pk.auto_created,
      "parent_link=", getattr(getattr(pk, 'remote_field', None), 'parent_link', None))

errs = Child._check_default_pk()
ids = [e.id for e in errs]
print("Child _check_default_pk errors:", ids)

if 'models.W042' in ids:
    print("FAIL: W042 emitted for inheritance-link child")
    sys.exit(1)
print("OK: no W042 for inheritance-link child")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements target django/db/models/base.py:_check_default_pk suppressing models.W042 for MTI inheritance-link primary keys.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): MTI child with auto-created parent_link OneToOne PK -> no W042. HOLDS patched, VIOLATED at base (base emits W042). Discriminates.
- probe_2 (Req 2.1/2.2, regression): plain auto-pk model with no DEFAULT_AUTO_FIELD -> exactly one W042, subject=model, id='models.W042', message contains 'auto-created primary key', hint references DEFAULT_AUTO_FIELD and AppConfig.default_auto_field. HOLDS.
- probe_3 (Req 2.4, regression): DEFAULT_AUTO_FIELD configured -> no W042. HOLDS.
- probe_4 (Req 2.3, regression): model with explicit AutoField pk (not auto_created) -> no W042. HOLDS.
- probe_5 (Req 3.1/1.3/3.4, per-model): Ancestor(auto pk)=W042; ChildAuto(auto link)=no W042; ChildExpl(explicit parent_link O2O)=no W042. HOLDS.

Candidate patches:
- weak_remove.diff: contradictory clause disabling the check entirely. REJECTED by probe_2 and probe_5 (ancestor/plain model lose their W042). Demonstrates the suite discriminates wrong implementations.
- weak_always.diff (suppress whenever cls._meta.parents truthy) and weak_o2o.diff (suppress whenever pk isinstance OneToOneField): both conform to ALL 5 probes. These are alternative-equivalent formulations (an auto-created pk is a parent_link OneToOne exactly in the MTI-link case; Req 1.4's non-parent-link auto O2O pk is not constructible in normal Django), so I expect them to also resolve the hidden harness rather than being genuinely too-weak. Submitted for the runner's harness re-check.

Environment: probes run in the official image (django 4.0, /testbed). Verdict SOUND: >=5 distinct probes hold on patched, positive control fails at base, and >=1 candidate (weak_remove) is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 3: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 2 were not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Req 1.1/1.2 + positive control: an MTI child whose PK is an auto-created
inheritance-link OneToOne back to a concrete ancestor SHALL NOT get models.W042,
even when no DEFAULT_AUTO_FIELD is configured.

HOLDS iff the child model emits no W042. On base (buggy) code the child DOES get
W042 -> probe fails at base (discriminating power)."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    # NB: DEFAULT_AUTO_FIELD intentionally NOT set -> not overridden.
)
import sys, types
from importlib.machinery import ModuleSpec
mod = types.ModuleType('probeapp')
mod.__path__ = ['/testbed']
mod.__file__ = '/testbed/__init__.py'
mod.__spec__ = ModuleSpec('probeapp', loader=None, origin='/testbed/__init__.py', is_package=True)
mod.__spec__.submodule_search_locations = ['/testbed']
sys.modules['probeapp'] = mod
django.setup()

from django.db import models

class Ancestor(models.Model):
    name = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

class Child(Ancestor):  # MTI: auto-created parent_link OneToOne PK
    extra = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'

pk = Child._meta.pk
print("Child pk:", type(pk).__name__, "auto_created=", pk.auto_created,
      "parent_link=", getattr(getattr(pk, 'remote_field', None), 'parent_link', None))

errs = Child._check_default_pk()
ids = [e.id for e in errs]
print("Child _check_default_pk errors:", ids)

if 'models.W042' in ids:
    print("FAIL: W042 emitted for inheritance-link child")
    sys.exit(1)
print("OK: no W042 for inheritance-link child")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements target django/db/models/base.py:_check_default_pk suppressing models.W042 for MTI inheritance-link primary keys.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): MTI child with auto-created parent_link OneToOne PK -> no W042. HOLDS patched, VIOLATED at base (base emits W042). Discriminates.
- probe_2 (Req 2.1/2.2, regression): plain auto-pk model with no DEFAULT_AUTO_FIELD -> exactly one W042, subject=model, id='models.W042', message contains 'auto-created primary key', hint references DEFAULT_AUTO_FIELD and AppConfig.default_auto_field. HOLDS.
- probe_3 (Req 2.4, regression): DEFAULT_AUTO_FIELD configured -> no W042. HOLDS.
- probe_4 (Req 2.3, regression): model with explicit AutoField pk (not auto_created) -> no W042. HOLDS.
- probe_5 (Req 3.1/1.3/3.4, per-model): Ancestor(auto pk)=W042; ChildAuto(auto link)=no W042; ChildExpl(explicit parent_link O2O)=no W042. HOLDS.

Candidate patches:
- weak_remove.diff: contradictory clause disabling the check entirely. REJECTED by probe_2 and probe_5 (ancestor/plain model lose their W042). Demonstrates the suite discriminates wrong implementations.
- weak_always.diff (suppress whenever cls._meta.parents truthy) and weak_o2o.diff (suppress whenever pk isinstance OneToOneField): both conform to ALL 5 probes. These are alternative-equivalent formulations (an auto-created pk is a parent_link OneToOne exactly in the MTI-link case; Req 1.4's non-parent-link auto O2O pk is not constructible in normal Django), so I expect them to also resolve the hidden harness rather than being genuinely too-weak. Submitted for the runner's harness re-check.

Environment: probes run in the official image (django 4.0, /testbed). Verdict SOUND: >=5 distinct probes hold on patched, positive control fails at base, and >=1 candidate (weak_remove) is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds a single guard to _check_default_pk: skip W042 when cls._meta.pk is a OneToOneField with remote_field.parent_link (an MTI inheritance link). Base-commit probe reproduces the bug exactly (child_of_explicit and child_of_auto both emit models.W042); patched probe suppresses both while preserving W042 for genuine auto-created pks (plain, auto_anc) and for the unspecified ancestor itself. Requirements pin the changed OBSERVABLE behavior (the W042 emit/suppress decision), not a narrow helper slice, and the boundary condition (parent_link OneToOneField) is precisely the code discriminator. Behavior neutralized DEFAULT_AUTO_FIELD/app-config overrides in the probe to surface the raw decision; matches gold F2P (test_auto_created_inherited_pk, test_explicit_inherited_pk) and P2P (test_auto_created_inherited_parent_link, test_explicit_inherited_parent_link, test_auto_created_pk, test_explicit_pk).

Counterexample / evidence:

```
N/A — no divergence found.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior in abstract terms. The gold predicate (isinstance(pk, OneToOneField) and pk.remote_field.parent_link) is deliberately abstracted to 'to-one relation'/'inheritance-link' — the concrete identifiers OneToOneField, parent_link, parent_ptr, remote_field are NOT present. models.W042, its message and hint (DEFAULT_AUTO_FIELD + app_config.default_auto_field) are all public via problem_statement. Naming _check_default_pk and django/db/models/base.py is legitimate change localization. No test function names (test_auto_created_inherited_pk etc.), no test file path, no parametrization ids, no quoted test/gold code. The 2x2-ish scenario matrix (ancestor explicit vs unspecified × child auto-link vs explicit-link) coincides with the test cases, but it is the genuine behavioral decomposition of the fix's boolean condition; the explicit-parent-link branch (present only in hidden tests, not the problem_statement) is a direct behavioral consequence of the OneToOneField+parent_link predicate, so describing it is behavioral translation rather than test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
