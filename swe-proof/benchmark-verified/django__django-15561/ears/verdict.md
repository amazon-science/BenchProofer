# P2 adversarial audit — django__django-15561

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
"""Req1.1 / Req1.3: choices-only change => _field_should_be_altered falsy."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models


class M(models.Model):
    field = models.CharField(max_length=10)
    class Meta:
        app_label = "contenttypes"

old = M._meta.get_field("field")
new = models.CharField(max_length=10, choices=[("a", "A"), ("b", "B")])
new.set_attributes_from_name("field")

with connection.schema_editor() as se:
    res = se._field_should_be_altered(old, new)
print("choices-only should_be_altered =", res)
raise SystemExit(0 if not res else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2: on SQLite a choices-only alter generates NO schema SQL / no rebuild."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models


class M(models.Model):
    field = models.CharField(max_length=10)
    class Meta:
        app_label = "contenttypes"

# create table first
with connection.schema_editor() as se:
    se.create_model(M)

old = M._meta.get_field("field")
new = models.CharField(max_length=10, choices=[("a", "A"), ("b", "B")])
new.set_attributes_from_name("field")

# collect_sql=True defers execution and records what WOULD run
with connection.schema_editor(collect_sql=True) as se:
    se.alter_field(M, old, new)
    sql = list(se.collected_sql)
print("collected SQL for choices-only alter:", sql)
# any table rebuild would show CREATE/INSERT/DROP/ALTER ... RENAME
raise SystemExit(0 if len(sql) == 0 else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.2: Field.non_db_attrs exposed on the class and includes choices + the
named presentation/validation attrs."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import models

attrs = getattr(models.Field, "non_db_attrs", None)
print("Field.non_db_attrs =", attrs)
if attrs is None:
    raise SystemExit(1)
required = {"blank", "choices", "db_column", "editable", "error_messages",
            "help_text", "limit_choices_to", "on_delete", "related_name",
            "related_query_name", "validators", "verbose_name"}
missing = required - set(attrs)
print("missing:", missing)
raise SystemExit(0 if not missing else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.2 (regression, SHALL keep): a genuine column change (max_length) still
requires an alteration => truthy."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models


class M(models.Model):
    field = models.CharField(max_length=10)
    class Meta:
        app_label = "contenttypes"

old = M._meta.get_field("field")
new = models.CharField(max_length=25)
new.set_attributes_from_name("field")

with connection.schema_editor() as se:
    res = se._field_should_be_altered(old, new)
print("max_length change should_be_altered =", res)
raise SystemExit(0 if res else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.4 (SHALL keep): choices change COMBINED with a real column change
(null) still requires an alteration => truthy."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models


class M(models.Model):
    field = models.CharField(max_length=10)
    class Meta:
        app_label = "contenttypes"

old = M._meta.get_field("field")
# choices added AND null flipped (real column change)
new = models.CharField(max_length=10, choices=[("a", "A")], null=True)
new.set_attributes_from_name("field")

with connection.schema_editor() as se:
    res = se._field_should_be_altered(old, new)
print("choices+null change should_be_altered =", res)
raise SystemExit(0 if res else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.1 (SHALL keep): a help_text-only change (already column-irrelevant
pre-patch) still reports no alteration => falsy. Regression guard."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models


class M(models.Model):
    field = models.CharField(max_length=10)
    class Meta:
        app_label = "contenttypes"

old = M._meta.get_field("field")
new = models.CharField(max_length=10, help_text="hello", verbose_name="Field X")
new.set_attributes_from_name("field")

with connection.schema_editor() as se:
    res = se._field_should_be_altered(old, new)
print("help_text/verbose_name change should_be_altered =", res)
raise SystemExit(0 if not res else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 / Req1.3: choices-only change => _field_should_be_altered falsy."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models


class M(models.Model):
    field = models.CharField(max_length=10)
    class Meta:
        app_label = "contenttypes"

old = M._meta.get_field("field")
new = models.CharField(max_length=10, choices=[("a", "A"), ("b", "B")])
new.set_attributes_from_name("field")

with connection.schema_editor() as se:
    res = se._field_should_be_altered(old, new)
print("choices-only should_be_altered =", res)
raise SystemExit(0 if not res else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithful to gold patch (adds Field.non_db_attrs tuple incl. 'choices' and uses it in _field_should_be_altered).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.3): choices-only diff => _field_should_be_altered falsy. PATCHED HOLDS (=False), BASE VIOLATED (=True). POSITIVE CONTROL, discriminates.
- probe_2 (Req1.2): SQLite collect_sql alter_field of choices-only change emits zero SQL / no table rebuild. PATCHED [] , BASE emits full CREATE/INSERT/DROP/RENAME rebuild. Also discriminates.
- probe_3 (Req2.2): Field.non_db_attrs exposed on class and includes choices + all 11 named attrs. PATCHED HOLDS, BASE non_db_attrs=None (VIOLATED).
- probe_4 (Req3.2 regression): max_length change => truthy. HOLDS patched & base.
- probe_5 (Req3.4): choices+null combined => truthy. HOLDS patched & base.
- probe_6 (Req2.1 regression): help_text/verbose_name-only change => falsy. HOLDS patched & base.

Candidate patch 'choices_local_only_not_exposed' (weak.diff): adds 'choices' to the OLD local non_database_attrs list in schema.py but does NOT introduce Field.non_db_attrs. This satisfies the behavioral Req1/Req3 probes (1,2,4,5,6 all HOLD under it) but is REJECTED by probe_3 (Req2.2: non_db_attrs=None). Demonstrates the suite discriminates a plausible partial fix that fails the interface requirement. Note this candidate would likely actually resolve the hidden functional tests, but it is correctly rejected by the requirements-encoded probe suite, so it is NOT a too-weak finding.

All 6 probes HOLD on patched; positive control (probe_1) fails at base and holds patched (prepatch reproduced). No violation found; no probe-conforming alternative patch discovered that passes every probe. Verdict SOUND.

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
"""Req1.1 / Req1.3: choices-only change => _field_should_be_altered falsy."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models


class M(models.Model):
    field = models.CharField(max_length=10)
    class Meta:
        app_label = "contenttypes"

old = M._meta.get_field("field")
new = models.CharField(max_length=10, choices=[("a", "A"), ("b", "B")])
new.set_attributes_from_name("field")

with connection.schema_editor() as se:
    res = se._field_should_be_altered(old, new)
print("choices-only should_be_altered =", res)
raise SystemExit(0 if not res else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithful to gold patch (adds Field.non_db_attrs tuple incl. 'choices' and uses it in _field_should_be_altered).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.3): choices-only diff => _field_should_be_altered falsy. PATCHED HOLDS (=False), BASE VIOLATED (=True). POSITIVE CONTROL, discriminates.
- probe_2 (Req1.2): SQLite collect_sql alter_field of choices-only change emits zero SQL / no table rebuild. PATCHED [] , BASE emits full CREATE/INSERT/DROP/RENAME rebuild. Also discriminates.
- probe_3 (Req2.2): Field.non_db_attrs exposed on class and includes choices + all 11 named attrs. PATCHED HOLDS, BASE non_db_attrs=None (VIOLATED).
- probe_4 (Req3.2 regression): max_length change => truthy. HOLDS patched & base.
- probe_5 (Req3.4): choices+null combined => truthy. HOLDS patched & base.
- probe_6 (Req2.1 regression): help_text/verbose_name-only change => falsy. HOLDS patched & base.

Candidate patch 'choices_local_only_not_exposed' (weak.diff): adds 'choices' to the OLD local non_database_attrs list in schema.py but does NOT introduce Field.non_db_attrs. This satisfies the behavioral Req1/Req3 probes (1,2,4,5,6 all HOLD under it) but is REJECTED by probe_3 (Req2.2: non_db_attrs=None). Demonstrates the suite discriminates a plausible partial fix that fails the interface requirement. Note this candidate would likely actually resolve the hidden functional tests, but it is correctly rejected by the requirements-encoded probe suite, so it is NOT a too-weak finding.

All 6 probes HOLD on patched; positive control (probe_1) fails at base and holds patched (prepatch reproduced). No violation found; no probe-conforming alternative patch discovered that passes every probe. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch replaces the hardcoded non_database_attrs list in BaseDatabaseSchemaEditor._field_should_be_altered with a per-field Field.non_db_attrs tuple that adds 'choices'. Requirements pin the changed observable behavior at the correct boundary (_field_should_be_altered decision + the exposed non_db_attrs collection), not a narrow slice. R2.3 (applying ignored attrs to both old and new field) matches the patch's two separate loops over old_field.non_db_attrs and new_field.non_db_attrs. R1.2's SQLite table-rebuild claim is a faithful downstream consequence documented by the issue; the core decision is what changed and is correctly modeled. All 3 probes (patched, base-diff, combined-change) pass.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change (_field_should_be_altered in base/schema.py, the ignored-attribute set, sqlite3/schema.py consumer) which is legitimate. The fix-invented identifier `Field.non_db_attrs` is NEVER named — the doc paraphrases it as 'the collection of attribute names ... exposed on the field class', a design/behavior description. The attribute enumeration (blank, db_column, editable, error_messages, help_text, limit_choices_to, on_delete, related_name, related_query_name, validators, verbose_name) matches the PRE-EXISTING public non_database_attrs list already in the prepatch Django source, not the hidden test. No test names/paths/ids (schema.tests.SchemaTests / test_alter_field_choices_noop), no quoted test code (Author, CharField(choices=...), max_length=255, assertNumQueries(0)), and no verbatim gold-patch lines appear. Req 1.2 (choices-only change on SQLite yields no SQL / no table rebuild) is a legitimate behavioral translation of what the single hidden test checks, not a reconstruction of it. No parametrization to mirror (one test case).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
