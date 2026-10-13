# P2 adversarial audit — django__django-14672

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
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

rel = M2M._meta.get_field("parents").remote_field
try:
    h = hash(rel)
except TypeError as e:
    print("VIOLATION: hash raised TypeError:", e); sys.exit(1)
print("hash =", h, type(h))
assert isinstance(h, int), "hash is not int"
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

rel = M2M._meta.get_field("parents").remote_field
tf = rel.through_fields
print("through_fields =", repr(tf), type(tf))
ok = isinstance(tf, list) and tf == ["child","parent"]
print("is preserved list:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

rel = M2M._meta.get_field("parents").remote_field
ident = rel.identity
print("identity =", ident)
for i,el in enumerate(ident):
    try:
        hash(el)
    except TypeError as e:
        print("element", i, repr(el), "UNHASHABLE:", e); sys.exit(1)
print("all elements hashable; tuple hash:", hash(ident))
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

class M2M2(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=("child","parent"))
    class Meta: app_label="testapp"
# tuple form
r2 = M2M2._meta.get_field("parents").remote_field
print("tuple-form hash:", hash(r2))
# Now a plain m2m without through_fields (None) via a fresh through-less rel object
from django.db.models.fields.reverse_related import ManyToManyRel
f = M2M._meta.get_field("parents")
rel = ManyToManyRel(f, Parent, through=Through, through_fields=None)
print("through_fields:", rel.through_fields)
try:
    print("identity:", rel.identity)
    print("hash:", hash(rel))
except TypeError as e:
    print("VIOLATION None-form raised:", e); sys.exit(1)
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

from django.db.models.fields.reverse_related import ManyToManyRel
f = M2M._meta.get_field("parents")
a = ManyToManyRel(f, Parent, through=Through, through_fields=["child","parent"])
b = ManyToManyRel(f, Parent, through=Through, through_fields=["child","parent"])
c = ManyToManyRel(f, Parent, through=Through, through_fields=["parent","child"])
print("a==b:", a==b, "hash eq:", hash(a)==hash(b))
print("a==c:", a==c)
ok = (a==b) and (hash(a)==hash(b)) and (a!=c)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

from django.utils.hashable import make_hashable
rel = M2M._meta.get_field("parents").remote_field
ident = rel.identity
# through_fields component is second-from-last (before db_constraint)
comp = ident[-2]
print("through_fields component in identity:", repr(comp))
expected = make_hashable(["child","parent"])
print("make_hashable expected:", repr(expected))
ok = comp == expected
try:
    hash(comp)
except TypeError as e:
    print("component unhashable:", e); ok=False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

rel = M2M._meta.get_field("parents").remote_field
try:
    h = hash(rel)
except TypeError as e:
    print("VIOLATION: hash raised TypeError:", e); sys.exit(1)
print("hash =", h, type(h))
assert isinstance(h, int), "hash is not int"
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and observed results (PATCHED / BASE):
- probe_1 (R1.1 positive control): hash() on ManyToManyRel with list through_fields returns int, no TypeError. HOLDS patched / VIOLATED base (TypeError: unhashable type: 'list'). Discriminates.
- probe_2 (R3.1): readable through_fields stays the list ['child','parent'], not coerced to tuple. HOLDS patched / HOLDS base (attribute unchanged by gold patch, as intended). NOT discriminating vs base but is the R3-preservation check that rejects the coercion candidate.
- probe_3 (R1.3): every element of identity tuple is hashable + tuple hashes. HOLDS patched / VIOLATED base (element 10 = list unhashable).
- probe_4 (R1.4): tuple-form and None-form through_fields both hash without raising. HOLDS patched.
- probe_5 (R2.1/2.2/2.3): equal-value rels compare equal and hash-equal; order-differing rels compare unequal. HOLDS patched / errored at base (constructing the rels hashes/compares -> base TypeError), consistent with base being broken.
- probe_6 (R1.2/R1.5): the through_fields component embedded in identity equals make_hashable(through_fields) = ('child','parent') and is hashable. HOLDS patched / VIOLATED base.

CANDIDATE PATCH: weak_coerce.diff — the lazy fix that coerces the STORED self.through_fields to a tuple in __init__ instead of normalizing only the identity component. It makes hashing work (probes 1,3,5,6 HOLD) but is REJECTED by probe_2 (R3.1: readable through_fields must remain the exact list). This demonstrates the suite discriminates a requirements-non-conforming wrong fix: R3's insistence that normalization affect only the identity tuple (R3.3) and not the stored attribute (R3.1) is exactly what separates the gold one-liner from the naive coercion.

No probe-conforming alternative found: any patch that (a) keeps through_fields readable as the list AND (b) makes identity hashable must place make_hashable (or an equivalent hashable, order-preserving, value-equal transform) on the through_fields component of identity — which is the gold change. Positive control fails at base, holds patched. SOUND.

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
import django, sys, types
from django.conf import settings
app = types.ModuleType("testapp"); app.__path__=["/tmp"]; sys.modules["testapp"]=app
settings.configure(DEBUG=True,
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
django.setup()
from django.db import models
class Parent(models.Model):
    class Meta: app_label="testapp"
class Child(models.Model):
    class Meta: app_label="testapp"
class Through(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    class Meta: app_label="testapp"
class M2M(models.Model):
    parents = models.ManyToManyField(Parent, through=Through, through_fields=["child","parent"])
    class Meta: app_label="testapp"

rel = M2M._meta.get_field("parents").remote_field
try:
    h = hash(rel)
except TypeError as e:
    print("VIOLATION: hash raised TypeError:", e); sys.exit(1)
print("hash =", h, type(h))
assert isinstance(h, int), "hash is not int"
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and observed results (PATCHED / BASE):
- probe_1 (R1.1 positive control): hash() on ManyToManyRel with list through_fields returns int, no TypeError. HOLDS patched / VIOLATED base (TypeError: unhashable type: 'list'). Discriminates.
- probe_2 (R3.1): readable through_fields stays the list ['child','parent'], not coerced to tuple. HOLDS patched / HOLDS base (attribute unchanged by gold patch, as intended). NOT discriminating vs base but is the R3-preservation check that rejects the coercion candidate.
- probe_3 (R1.3): every element of identity tuple is hashable + tuple hashes. HOLDS patched / VIOLATED base (element 10 = list unhashable).
- probe_4 (R1.4): tuple-form and None-form through_fields both hash without raising. HOLDS patched.
- probe_5 (R2.1/2.2/2.3): equal-value rels compare equal and hash-equal; order-differing rels compare unequal. HOLDS patched / errored at base (constructing the rels hashes/compares -> base TypeError), consistent with base being broken.
- probe_6 (R1.2/R1.5): the through_fields component embedded in identity equals make_hashable(through_fields) = ('child','parent') and is hashable. HOLDS patched / VIOLATED base.

CANDIDATE PATCH: weak_coerce.diff — the lazy fix that coerces the STORED self.through_fields to a tuple in __init__ instead of normalizing only the identity component. It makes hashing work (probes 1,3,5,6 HOLD) but is REJECTED by probe_2 (R3.1: readable through_fields must remain the exact list). This demonstrates the suite discriminates a requirements-non-conforming wrong fix: R3's insistence that normalization affect only the identity tuple (R3.3) and not the stored attribute (R3.1) is exactly what separates the gold one-liner from the naive coercion.

No probe-conforming alternative found: any patch that (a) keeps through_fields readable as the list AND (b) makes identity hashable must place make_hashable (or an equivalent hashable, order-preserving, value-equal transform) on the through_fields component of identity — which is the gold change. Positive control fails at base, holds patched. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: reverse_related.py ManyToManyRel.identity changes self.through_fields -> make_hashable(self.through_fields). Requirements pin the changed OBSERVABLE behavior (identity hashability + preserved public attribute) at the correct boundary, not a narrow slice. Probe HOLDS on patched (exit 0, through_fields list preserved, identity has ('child','parent')); base raises TypeError. Requirement modeling boundary is the identity property and its hash/equality derivation — exactly what changed. No mandated behavior the code lacks, none forbidden that it has, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md localizes the change to ManyToManyRel.identity in reverse_related.py and names make_hashable/django.utils.hashable — all of which are explicit in the public problem_statement (which even states the solution 'Add missing make_hashable call on self.through_fields in ManyToManyRel' and the through_fields=['child','parent'] list example, the TypeError, and the _check_field_name_clashes context). No hidden-test content is transmitted: none of the test fixture identifiers (PersonChild, Person, Event, through_fields=['event','invitee'], clash/clash_id, models.E006), test names/paths (test_reverse_inherited_m2m_with_through_fields_list_hashable, test_field_name_clash_with_m2m_through, tests/m2m_through/*, tests/invalid_models_tests/*), or gold-patch code lines appear. Req 2.5/3.2 (inherited child relation hashes equal; inherited through_fields equals declaring model's) translate the F2P inheritance test into behavioral requirements without naming the test or fixtures — legitimate behavior translation. Req 4.3/4.4 enumerate generic, publicly-documented m2m behaviors (table-name clashes, ambiguous through_fields, add/set/clear, self-referential/symmetrical) to scope regressions, not fix-invented identifiers or test parametrization ids. No semantic gold reconstruction beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
