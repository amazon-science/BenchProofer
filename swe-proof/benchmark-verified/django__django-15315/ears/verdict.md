# P2 adversarial audit — django__django-15315

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
"""Positive control. Req1.2/1.4: a field placed in a set before model
assignment SHALL still be found (membership succeed) after attachment,
because hash(field) is unchanged. FAILS at base (hash folds in model)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models

f = models.IntegerField()
d = {f: "value"}
s = {f}
before = hash(f)
found_before = f in d and f in s

# Attach to a model class:
class M1(models.Model):
    myfield = f
    class Meta:
        app_label = 'probeapp'

after = hash(f)
found_after = f in d and f in s
print("hash before:", before, "hash after:", after)
print("found before:", found_before, "found after:", found_after)
ok = found_before and found_after and (before == after)
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3: hash SHALL be derived solely from creation_counter and SHALL NOT
incorporate model app_label/model_name. Verify hash(field) == hash(creation_counter)
both unattached and attached, and unchanged across attachment."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models

f = models.CharField(max_length=5)
h_unattached = hash(f)
expect_unattached = hash(f.creation_counter)

class M(models.Model):
    x = f
    class Meta:
        app_label = 'probeapp2'

h_attached = hash(f)
expect_attached = hash(f.creation_counter)
print("unattached:", h_unattached, "expect", expect_unattached)
print("attached:", h_attached, "expect", expect_attached)
ok = (h_unattached == expect_unattached == h_attached == expect_attached)
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2: equality semantics. Two distinct fields on different models
compare NOT equal; two unattached fields with distinct creation_counter not
equal; a field equals itself. Mirror of test_abstract_inherited_fields."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models

class AbstractModel(models.Model):
    field = models.IntegerField()
    class Meta:
        abstract = True
        app_label = 'probeapp3'

class InheritAbstractModel1(AbstractModel):
    class Meta:
        app_label = 'probeapp3'

class InheritAbstractModel2(AbstractModel):
    class Meta:
        app_label = 'probeapp3'

a = AbstractModel._meta.get_field('field')
i1 = InheritAbstractModel1._meta.get_field('field')
i2 = InheritAbstractModel2._meta.get_field('field')

# same creation_counter (inherited via deepcopy? actually distinct); different model
c1 = (a != i1)
c2 = (a != i2)
c3 = (i1 != i2)
c4 = (a == a)
print("a!=i1", c1, "a!=i2", c2, "i1!=i2", c3, "a==a", c4)
ok = c1 and c2 and c3 and c4
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.3: hash collisions must NOT cause distinct fields to be treated as
identical. Inherited abstract fields share creation_counter => same hash, but
belong to different models => not equal. A dict must keep them as separate keys."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models

class AbstractModel(models.Model):
    field = models.IntegerField()
    class Meta:
        abstract = True
        app_label = 'probeapp4'

class Inherit1(AbstractModel):
    class Meta:
        app_label = 'probeapp4'
class Inherit2(AbstractModel):
    class Meta:
        app_label = 'probeapp4'

i1 = Inherit1._meta.get_field('field')
i2 = Inherit2._meta.get_field('field')

same_hash = hash(i1) == hash(i2)
not_equal = (i1 != i2)
d = {}
d[i1] = "one"
d[i2] = "two"
distinct_keys = (len(d) == 2 and d[i1] == "one" and d[i2] == "two")
print("same_hash", same_hash, "not_equal", not_equal, "distinct_keys", distinct_keys)
# The core criterion: even if hashes collide, equality resolves them.
ok = not_equal and distinct_keys
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3: ordering semantics preserved. Mirror test_field_ordering and
Req3.2 (unattached orders before attached at equal counter) and Req3.3
(both attached -> order by app_label/model_name)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models
import copy

# Req3.1: ordered by creation serial
f1 = models.Field()
f2 = models.Field(auto_created=True)
f3 = models.Field()
r31 = (f2 < f1) and (f3 > f1)

# Req3.2: equal creation_counter, one attached one not -> unattached orders first
u = models.Field()
att = copy.deepcopy(u)  # shares creation_counter
class M(models.Model):
    x = att
    class Meta:
        app_label = 'zapp'
# u unattached, att attached, same creation_counter
r32 = (u < att) and not (att < u)

# Req3.3: both attached, same creation_counter -> ordered by (app_label, model_name)
b1 = models.Field()
b2 = copy.deepcopy(b1)
class MA(models.Model):
    x = b1
    class Meta:
        app_label = 'aaa'
class MB(models.Model):
    x = b2
    class Meta:
        app_label = 'bbb'
r33 = (b1 < b2) and not (b2 < b1)

print("r31", r31, "r32", r32, "r33", r33)
ok = r31 and r32 and r33
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1.1/1.5: field is hashable (produces a well-defined int hash) both
before and after attachment to a model."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models

f = models.TextField()
try:
    h_before = hash(f)
    ok_before = isinstance(h_before, int)
except TypeError:
    ok_before = False

class M(models.Model):
    x = f
    class Meta:
        app_label = 'happ'

try:
    h_after = hash(f)
    ok_after = isinstance(h_after, int)
except TypeError:
    ok_after = False

print("hashable before:", ok_before, "hashable after:", ok_after)
ok = ok_before and ok_after
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req1.2/1.4: a field placed in a set before model
assignment SHALL still be found (membership succeed) after attachment,
because hash(field) is unchanged. FAILS at base (hash folds in model)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models

f = models.IntegerField()
d = {f: "value"}
s = {f}
before = hash(f)
found_before = f in d and f in s

# Attach to a model class:
class M1(models.Model):
    myfield = f
    class Meta:
        app_label = 'probeapp'

after = hash(f)
found_after = f in d and f in s
print("hash before:", before, "hash after:", after)
print("found before:", found_before, "found after:", found_after)
ok = found_before and found_after and (before == after)
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements mandate Field.__hash__ be immutable across model attachment, derived solely from creation_counter, while preserving equality (Req2) and total-ordering (Req3) semantics. Gold patch: __hash__ = hash(self.creation_counter).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.2/1.4, POSITIVE CONTROL): field in dict/set before attachment still found after; hash unchanged (46==46). HOLDS patched, FAILS at base (hash 7072...->8655..., found_after=False). Discriminates.
- probe_2 (Req1.3): hash(field)==hash(creation_counter) both unattached and attached. HOLDS patched; FAILS base (hash != hash(counter), and changes on attach).
- probe_3 (Req2.1/2.2): distinct abstract-inherited fields on different models compare not-equal; self==self. HOLDS.
- probe_4 (Req2.3): colliding-hash fields still resolved by equality, kept as distinct dict keys. HOLDS.
- probe_5 (Req3.1/3.2/3.3): ordering by creation serial; unattached<attached at equal counter; both attached ordered by (app_label, model_name). HOLDS.
- probe_6 (Req1.1/1.5): field hashable (int hash) before and after attachment. HOLDS.

Candidate wrong-fix patches, both REJECTED by the suite (demonstrating discrimination):
- weak_id (__hash__=id(self)): satisfies immutability + hashability but violates Req1.3 — probe_2 REJECTS (hash != hash(creation_counter)). Would also break equal-objects-equal-hash contract for deepcopied/pickled fields.
- weak_partial (hash of (creation_counter, app_label) only, still folds in model): NOT immutable — probe_1 AND probe_2 REJECT (hash changes on attach). This is the lazy 'drop one field' misreading.

6 distinct probes all hold on patched; positive control discriminates patched-vs-base; >=1 candidate exercised and REJECTED. Suite discriminates wrong implementations. Verdict SOUND.

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
"""Positive control. Req1.2/1.4: a field placed in a set before model
assignment SHALL still be found (membership succeed) after attachment,
because hash(field) is unchanged. FAILS at base (hash folds in model)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={}, USE_TZ=True)
django.setup()
from django.db import models

f = models.IntegerField()
d = {f: "value"}
s = {f}
before = hash(f)
found_before = f in d and f in s

# Attach to a model class:
class M1(models.Model):
    myfield = f
    class Meta:
        app_label = 'probeapp'

after = hash(f)
found_after = f in d and f in s
print("hash before:", before, "hash after:", after)
print("found before:", found_before, "found after:", found_after)
ok = found_before and found_after and (before == after)
print("OK" if ok else "VIOLATION")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements mandate Field.__hash__ be immutable across model attachment, derived solely from creation_counter, while preserving equality (Req2) and total-ordering (Req3) semantics. Gold patch: __hash__ = hash(self.creation_counter).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.2/1.4, POSITIVE CONTROL): field in dict/set before attachment still found after; hash unchanged (46==46). HOLDS patched, FAILS at base (hash 7072...->8655..., found_after=False). Discriminates.
- probe_2 (Req1.3): hash(field)==hash(creation_counter) both unattached and attached. HOLDS patched; FAILS base (hash != hash(counter), and changes on attach).
- probe_3 (Req2.1/2.2): distinct abstract-inherited fields on different models compare not-equal; self==self. HOLDS.
- probe_4 (Req2.3): colliding-hash fields still resolved by equality, kept as distinct dict keys. HOLDS.
- probe_5 (Req3.1/3.2/3.3): ordering by creation serial; unattached<attached at equal counter; both attached ordered by (app_label, model_name). HOLDS.
- probe_6 (Req1.1/1.5): field hashable (int hash) before and after attachment. HOLDS.

Candidate wrong-fix patches, both REJECTED by the suite (demonstrating discrimination):
- weak_id (__hash__=id(self)): satisfies immutability + hashability but violates Req1.3 — probe_2 REJECTS (hash != hash(creation_counter)). Would also break equal-objects-equal-hash contract for deepcopied/pickled fields.
- weak_partial (hash of (creation_counter, app_label) only, still folds in model): NOT immutable — probe_1 AND probe_2 REJECT (hash changes on attach). This is the lazy 'drop one field' misreading.

6 distinct probes all hold on patched; positive control discriminates patched-vs-base; >=1 candidate exercised and REJECTED. Suite discriminates wrong implementations. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes only Field.__hash__ from hash((creation_counter, model app_label/model_name-if-attached)) to hash(creation_counter). Requirements center exactly on this: R1 = hash immutable across model attachment, derived solely from creation_counter. Probe on patched tree: hash(f)==hash(f.creation_counter) before and after attaching f to a model class; f remains findable in dict/set after attachment (R1.2/1.3/1.4/1.5 hold). Base probe confirms the bug: hash changed 7072477421621140107 -> -2478528652015118895 on attachment. R2 (equality) and R3 (ordering) correctly assert PRESERVED semantics — the patch does NOT touch __eq__/__lt__, so requiring them unchanged is faithful. Probed: distinct fields on different models compare unequal (R2.2); same creation_counter unattached fields equal (R2.1); ordering by creation_counter then unattached<attached then by (app_label,model_name) (R3.1/3.2/3.3) — all hold on patched code. Modeling boundary is correct: requirements pin the full changed observable (hash constancy across lifetime) rather than one internal branch. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the hash-immutability fix behaviorally. The only F2P test (test_hash_immutability) is translated into Req 1.2/1.4 as behavior (hash unchanged before/after model attachment; dict/set membership survives) — no test name, path, function/class name, or parametrization id appears. `creation_counter`, `model._meta.app_label`, `model._meta.model_name` are long-standing public Django field attributes visible in the base field class (not fix-invented), and the public problem_statement already directs reverting __hash__ to a creation-serial-only hash — so naming them is legitimate localization, not gold-code leakage. The gold patch line (`hash(self.creation_counter)`) is not quoted; Reqs 2/3 restate pre-existing __eq__/__lt__ invariants (mirroring PASS_TO_PASS behaviors like ordering-by-creation and abstract-model inequality) as behavior, not as test enumerations. No case list mirrors test parametrization (the F2P case is singular). Faithful behavioral spec.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
