# P2 adversarial audit — django__django-14007

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
"""Probe 1 / POSITIVE CONTROL — Req 1.2, 4.1: a BigAutoField subclass whose
from_db_value wraps the value must yield the wrapper object on create()."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp")
app.__path__ = ["/tmp"]
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection


class MyIntWrapper:
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return "<MyIntWrapper: %s>" % self.value


class MyAutoField(models.BigAutoField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return MyIntWrapper(value)

    def get_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, MyIntWrapper):
            return value.value
        return int(value)


class AutoModel(models.Model):
    id = MyAutoField(primary_key=True)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(AutoModel)

am = AutoModel.objects.create()
print("created id:", repr(am.id), "type:", type(am.id).__name__)

ok = isinstance(am.id, MyIntWrapper)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Req 2.1, 4.5: for a field declaring NO converters (an ordinary
AutoField pk), execute_sql returns rows unchanged; create() populates the pk
with the plain integer the backend returned, equal to the stored value."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp"); app.__path__ = ["/tmp"]; sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection


class Plain(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Plain)

obj = Plain.objects.create(name="a")
refetched = Plain.objects.get(pk=obj.pk)
print("created pk:", repr(obj.pk), "type:", type(obj.pk).__name__)
print("refetched pk:", repr(refetched.pk))

ok = (type(obj.pk) is int) and obj.pk == refetched.pk and obj.pk == 1
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Req 3.1, 4.2: bulk_create on a backend that can return rows from
bulk insert must populate each instance's pk with the CONVERTED (wrapped)
value. sqlite3 in modern Django supports can_return_rows_from_bulk_insert."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp"); app.__path__ = ["/tmp"]; sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection


class MyIntWrapper:
    def __init__(self, value):
        self.value = int(value)
    def __repr__(self):
        return "<MyIntWrapper: %s>" % self.value


class MyAutoField(models.BigAutoField):
    def from_db_value(self, value, expression, connection):
        return None if value is None else MyIntWrapper(value)
    def get_prep_value(self, value):
        if value is None:
            return None
        return value.value if isinstance(value, MyIntWrapper) else int(value)


class AutoModel(models.Model):
    id = MyAutoField(primary_key=True)
    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(AutoModel)

if not connection.features.can_return_rows_from_bulk_insert:
    print("backend cannot return rows from bulk insert; criterion vacuous here")
    # This probe only meaningfully tests the bulk pathway when supported.
    sys.exit(0)

objs = [AutoModel(), AutoModel()]
AutoModel.objects.bulk_create(objs)
for o in objs:
    print("bulk id:", repr(o.id), "type:", type(o.id).__name__)

ok = all(isinstance(o.id, MyIntWrapper) for o in objs)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Req 1 (consistency) + 4.1: the value set on the created instance
must match what a READ query yields for the same row (both wrapped), and the
wrapped value must equal the stored integer. Also checks Req 2.3: exactly one
row, one cell (single pk) — create() populated exactly the pk."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp"); app.__path__ = ["/tmp"]; sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection


class MyIntWrapper:
    def __init__(self, value):
        self.value = int(value)
    def __repr__(self):
        return "<MyIntWrapper: %s>" % self.value
    def __eq__(self, other):
        if isinstance(other, MyIntWrapper):
            return self.value == other.value
        return self.value == other
    def __hash__(self):
        return hash(self.value)


class MyAutoField(models.BigAutoField):
    def from_db_value(self, value, expression, connection):
        return None if value is None else MyIntWrapper(value)
    def get_prep_value(self, value):
        if value is None:
            return None
        return value.value if isinstance(value, MyIntWrapper) else int(value)


class AutoModel(models.Model):
    id = MyAutoField(primary_key=True)
    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(AutoModel)

created = AutoModel.objects.create()
read = AutoModel.objects.get(pk=created.id.value)
print("created:", repr(created.id), "read:", repr(read.id))

ok = (isinstance(created.id, MyIntWrapper)
      and isinstance(read.id, MyIntWrapper)
      and created.id == read.id
      and created.id.value == 1)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Req 4.3: models with a custom (non-auto) primary key field type
must keep working across create/save/filter/get/in_bulk by both `pk` and the
field's own attribute name, with unchanged results. Mirrors custom_pk.Bar with
a CharField-based wrapper pk (explicitly supplied on create)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp"); app.__path__ = ["/tmp"]; sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection


class MyWrapper:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return "<MyWrapper: %s>" % self.value
    def __eq__(self, other):
        if isinstance(other, MyWrapper):
            return self.value == other.value
        return self.value == other
    def __hash__(self):
        return hash(self.value)
    def __str__(self):
        return self.value


class MyWrapperField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 10
        super().__init__(*args, **kwargs)
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return MyWrapper(value)
    def to_python(self, value):
        if value is None or isinstance(value, MyWrapper):
            return value
        return MyWrapper(value)
    def get_prep_value(self, value):
        if isinstance(value, MyWrapper):
            return value.value
        return value


class Bar(models.Model):
    id = MyWrapperField(primary_key=True, db_index=True)
    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Bar)

Bar.objects.create(id=MyWrapper("k1"))
Bar.objects.create(id="k2")

by_pk = Bar.objects.get(pk="k1")
by_attr = Bar.objects.get(id="k2")
filt = list(Bar.objects.filter(pk="k1"))
inb_pk = Bar.objects.in_bulk(["k1", "k2"], field_name="pk")
print("get pk:", repr(by_pk.id), "get id:", repr(by_attr.id))
inb_vals = {str(k) for k in inb_pk.keys()}
print("filter:", filt, "in_bulk keys:", inb_vals)

ok = (by_pk.pk == "k1" and by_attr.id == "k2"
      and len(filt) == 1 and inb_vals == {"k1", "k2"}
      and isinstance(by_pk.id, MyWrapper))
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Req 4.4: when a required (non-nullable, non-auto) primary key is
omitted/None on creation, the operation SHALL still raise an integrity error.

We use a non-auto pk that keeps None as SQL NULL (empty_strings_allowed=False
+ identity get_prep_value), so the NOT NULL pk column receives NULL and the DB
must reject it. This is a regression criterion (holds on base and patched);
the converter step must not swallow the error."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp"); app.__path__ = ["/tmp"]; sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection, IntegrityError, transaction


class StrictPKField(models.CharField):
    empty_strings_allowed = False  # None must NOT be coerced to ''

    def get_prep_value(self, value):
        return value  # keep None as None -> SQL NULL


class Widget(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    # required non-auto pk-like column
    key = StrictPKField(max_length=10, null=False)
    class Meta:
        app_label = "probeapp"


# Simpler: make the pk itself the strict field.
class Emp(models.Model):
    code = StrictPKField(max_length=10, primary_key=True)
    name = models.CharField(max_length=20)
    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

raised = False
try:
    with transaction.atomic():
        Emp.objects.create(name="Tom")  # pk omitted -> None -> NULL
except IntegrityError as e:
    raised = True
    print("raised IntegrityError:", str(e)[:100])
except Exception as e:
    print("raised OTHER:", type(e).__name__, str(e)[:100])
else:
    print("NO EXCEPTION: pk=", repr(Emp.objects.first().pk))

print("HOLDS" if raised else "VIOLATED")
sys.exit(0 if raised else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 / POSITIVE CONTROL — Req 1.2, 4.1: a BigAutoField subclass whose
from_db_value wraps the value must yield the wrapper object on create()."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp")
app.__path__ = ["/tmp"]
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection


class MyIntWrapper:
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return "<MyIntWrapper: %s>" % self.value


class MyAutoField(models.BigAutoField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return MyIntWrapper(value)

    def get_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, MyIntWrapper):
            return value.value
        return int(value)


class AutoModel(models.Model):
    id = MyAutoField(primary_key=True)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(AutoModel)

am = AutoModel.objects.create()
print("created id:", repr(am.id), "type:", type(am.id).__name__)

ok = isinstance(am.id, MyIntWrapper)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14007: apply field converters (from_db_value) to values returned by an insert in SQLInsertCompiler.execute_sql, across all three return pathways (bulk rows / returned columns / last_insert_id), while leaving no-converter behavior unchanged.

Six probes, all HOLD on the gold-patched tree, run in the official Docker image:
- probe_1 (POSITIVE CONTROL; Req 1.2, 4.1): BigAutoField subclass with a wrapping from_db_value -> create() yields the wrapper (MyIntWrapper), not a raw int. HOLDS patched; VIOLATED at base ('created id: 1 type: int'), so it discriminates (prepatch reproduced).
- probe_2 (Req 2.1, 4.5): ordinary AutoField pk (no converters) -> create() pk is a plain int equal to stored/refetched value; conversion step is a no-op. HOLDS.
- probe_3 (Req 3.1, 4.2): bulk_create path; sqlite reports can_return_rows_from_bulk_insert=False, so the criterion is vacuous on this backend and the probe exits 0 (explicitly noted; no false-positive claimed for the bulk pathway).
- probe_4 (Req 1 consistency + 4.1): the value set on the created instance equals what a READ query yields for the same row (both wrapped), and wrapped value == stored int. HOLDS.
- probe_5 (Req 4.3): custom CharField-based wrapper pk works across create/get(pk=/id=)/filter/in_bulk with unchanged results. HOLDS.
- probe_6 (Req 4.4): a required non-nullable non-auto pk left None on create() still raises IntegrityError (NOT NULL constraint). HOLDS (regression criterion, base+patched).

DISCRIMINATION: weak.diff (converts only the can_return_rows_from_bulk_insert and can_return_columns_from_insert pathways, leaving the last_insert_id fallback unconverted). On sqlite (both features False), single create() takes the last_insert_id path, so the wrapper is never applied. Under weak.diff: probes 2,3,5,6 HOLD but the positive control probe_1 and probe_4 are VIOLATED ('created id: 1 type: int'). The suite REJECTS this plausible partial fix, demonstrating discriminating power against a requirements-under-satisfying implementation. No probe-conforming alternative patch was found.

Verdict: SOUND. >=5 distinct probes all hold on the patched tree; positive control holds patched and fails at base; at least one wrong-fix candidate is exercised and rejected by the suite. Requirements faithfully match the gold patch.

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
"""Probe 1 / POSITIVE CONTROL — Req 1.2, 4.1: a BigAutoField subclass whose
from_db_value wraps the value must yield the wrapper object on create()."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType("probeapp")
app.__path__ = ["/tmp"]
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection


class MyIntWrapper:
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return "<MyIntWrapper: %s>" % self.value


class MyAutoField(models.BigAutoField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return MyIntWrapper(value)

    def get_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, MyIntWrapper):
            return value.value
        return int(value)


class AutoModel(models.Model):
    id = MyAutoField(primary_key=True)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(AutoModel)

am = AutoModel.objects.create()
print("created id:", repr(am.id), "type:", type(am.id).__name__)

ok = isinstance(am.id, MyIntWrapper)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14007: apply field converters (from_db_value) to values returned by an insert in SQLInsertCompiler.execute_sql, across all three return pathways (bulk rows / returned columns / last_insert_id), while leaving no-converter behavior unchanged.

Six probes, all HOLD on the gold-patched tree, run in the official Docker image:
- probe_1 (POSITIVE CONTROL; Req 1.2, 4.1): BigAutoField subclass with a wrapping from_db_value -> create() yields the wrapper (MyIntWrapper), not a raw int. HOLDS patched; VIOLATED at base ('created id: 1 type: int'), so it discriminates (prepatch reproduced).
- probe_2 (Req 2.1, 4.5): ordinary AutoField pk (no converters) -> create() pk is a plain int equal to stored/refetched value; conversion step is a no-op. HOLDS.
- probe_3 (Req 3.1, 4.2): bulk_create path; sqlite reports can_return_rows_from_bulk_insert=False, so the criterion is vacuous on this backend and the probe exits 0 (explicitly noted; no false-positive claimed for the bulk pathway).
- probe_4 (Req 1 consistency + 4.1): the value set on the created instance equals what a READ query yields for the same row (both wrapped), and wrapped value == stored int. HOLDS.
- probe_5 (Req 4.3): custom CharField-based wrapper pk works across create/get(pk=/id=)/filter/in_bulk with unchanged results. HOLDS.
- probe_6 (Req 4.4): a required non-nullable non-auto pk left None on create() still raises IntegrityError (NOT NULL constraint). HOLDS (regression criterion, base+patched).

DISCRIMINATION: weak.diff (converts only the can_return_rows_from_bulk_insert and can_return_columns_from_insert pathways, leaving the last_insert_id fallback unconverted). On sqlite (both features False), single create() takes the last_insert_id path, so the wrapper is never applied. Under weak.diff: probes 2,3,5,6 HOLD but the positive control probe_1 and probe_4 are VIOLATED ('created id: 1 type: int'). The suite REJECTS this plausible partial fix, demonstrating discriminating power against a requirements-under-satisfying implementation. No probe-conforming alternative patch was found.

Verdict: SOUND. >=5 distinct probes all hold on the patched tree; positive control holds patched and fails at base; at least one wrong-fix candidate is exercised and rejected by the suite. Requirements faithfully match the gold patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe run via nl_attack on instance image: single create() returns MyIntWrapper on gold-patched (exit 0 HOLDS), raw int on base (VIOLATED at the isinstance-wrapper assertion) — the exact issue behavior. bulk_create pk-return is not exercised on sqlite (lacks can_return_rows_from_bulk_insert, so id is None), consistent with Req 4.2's conditional 'on a backend that can return primary-key values'; requirements do not over-claim sqlite bulk behavior. No requirement mandates behavior absent from the patch, forbids present behavior, invents behavior, or pins a narrower slice than the changed converter-application behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to SQLInsertCompiler.execute_sql (django/db/models/sql/compiler.py) and reference get_converters/apply_converters and the three backend return pathways (bulk multi-row / single-row columns / last-inserted-id). These are legitimate module/function localizations of the gold edit, not test transmission. Much of the domain (BigAutoField subclass, from_db_value, wrapper object, create()/bulk_create) is already public in the problem_statement. None of the hidden-test-only identifiers leak: no test function names (test_auto_field_subclass_create/_bulk_create), no MyWrapper/MyWrapperField/CustomAutoFieldModel model or field names, no skipUnlessDBFeature('can_return_rows_from_bulk_insert') flag, no quoted test/gold code, no fix-invented identifiers (get_col/get_meta not surfaced as such). Borderline: Req 4.3 enumerates creating/saving/filtering/get/in_bulk lookups 'by both pk and the field's own attribute name', which parallels the PASS_TO_PASS test descriptions — but these are generic pre-existing custom-pk behaviors translated into preservation requirements (the charter's stated legitimate purpose), not verbatim test names, parametrization ids, or hidden identifiers, so it does not reconstruct the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
