# P2 adversarial audit — django__django-15732

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_core.py`, `probe_pk.py`, `probe_canonical.py`, `probe_single.py`, `probe_error_absent.py`, `probe_index.py`, `probe_create.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_core.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_core.py` → holds on the patched tree (good)

```python
"""Positive control + Req 2.3 (behavioral only, no private-API reference):
removing a unique_together over a column that ALSO declares unique=True must
drop ONLY the unique_together constraint (the canonical name, suffixed `_uniq`)
and leave the field's own unique constraint in place.
Base: ValueError (2 constraints). Naive first-match pick: drops the wrong one."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta:
        app_label="probeapp"; unique_together=(("name",),)
with connection.schema_editor() as ed:
    ed.create_model(Author)
def uniques_on_name():
    with connection.cursor() as c:
        consts=connection.introspection.get_constraints(c, Author._meta.db_table)
    return [n for n,v in consts.items() if v.get("unique") and v.get("columns")==["name"]]
before=uniques_on_name()
print("unique on [name] before:", before)
# the unique_together constraint is the one whose name ends in _uniq
ut_before=[n for n in before if n.endswith("_uniq")]
own_before=[n for n in before if not n.endswith("_uniq")]
print("unique_together (_uniq) before:", ut_before, "| field-own before:", own_before)
try:
    with connection.schema_editor() as ed:
        ed.alter_unique_together(Author, (("name",),), tuple())
    print("removal SUCCEEDED"); ok=True
except ValueError as e:
    print("removal RAISED:", e); ok=False
after=uniques_on_name()
print("unique on [name] after:", after)
# Req 2.3: the _uniq (unique_together) constraint gone; the field's own remains
if (ok and len(ut_before)==1 and len(own_before)==1
        and after==own_before):
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Attack 2 — `probe_pk.py` → holds on the patched tree (good)

```python
"""Req 1.3: single-column unique_together over the PK column, when removed,
drops the unique_together constraint and leaves the PK constraint in place."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class M(models.Model):
    id = models.AutoField(primary_key=True)
    class Meta:
        app_label="probeapp"; unique_together=(("id",),)
with connection.schema_editor() as ed:
    ed.create_model(M)
with connection.cursor() as c:
    consts=connection.introspection.get_constraints(c, M._meta.db_table)
pk_before=[n for n,v in consts.items() if v.get("primary_key")]
print("pk constraints before:", pk_before)
try:
    with connection.schema_editor() as ed:
        ed.alter_unique_together(M, (("id",),), tuple())
    print("removal SUCCEEDED"); ok=True
except ValueError as e:
    print("removal RAISED:", e); ok=False
with connection.cursor() as c:
    consts2=connection.introspection.get_constraints(c, M._meta.db_table)
pk_after=[n for n,v in consts2.items() if v.get("primary_key")]
print("pk constraints after:", pk_after)
if ok and len(pk_after)==len(pk_before) and len(pk_after)>=1:
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Attack 3 — `probe_canonical.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 4.2: _unique_constraint_name(table, columns, quote=False) yields
the SAME name that create_model assigns to an implicit unique_together
constraint, deterministically."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class Au(models.Model):
    name=models.CharField(max_length=50)
    email=models.CharField(max_length=50)
    class Meta:
        app_label="probeapp"; unique_together=(("name","email"),)
with connection.schema_editor() as ed:
    ed.create_model(Au)
    n1=str(ed._unique_constraint_name(Au._meta.db_table, ["name","email"], quote=False))
    n2=str(ed._unique_constraint_name(Au._meta.db_table, ["name","email"], quote=False))
print("canonical name:", n1)
print("deterministic:", n1==n2)
with connection.cursor() as c:
    consts=connection.introspection.get_constraints(c, Au._meta.db_table)
matches=[nm for nm,v in consts.items() if v.get("unique") and sorted(v.get("columns") or [])==["email","name"]]
print("actual unique constraints on cols:", matches)
if n1==n2 and n1 in matches:
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Attack 4 — `probe_single.py` → holds on the patched tree (good)

```python
"""Req 3.4: ordinary single unique_together (no coexisting pk/unique) removal
drops the one constraint unchanged."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class B(models.Model):
    a=models.CharField(max_length=20)
    b=models.CharField(max_length=20)
    class Meta:
        app_label="probeapp"; unique_together=(("a","b"),)
with connection.schema_editor() as ed:
    ed.create_model(B)
with connection.cursor() as c:
    consts=connection.introspection.get_constraints(c, B._meta.db_table)
before=[n for n,v in consts.items() if v.get("unique") and sorted(v.get("columns") or [])==["a","b"]]
print("unique on (a,b) before:", before)
try:
    with connection.schema_editor() as ed:
        ed.alter_unique_together(B, (("a","b"),), tuple())
    print("removal SUCCEEDED"); ok=True
except ValueError as e:
    print("removal RAISED:", e); ok=False
with connection.cursor() as c:
    consts2=connection.introspection.get_constraints(c, B._meta.db_table)
after=[n for n,v in consts2.items() if v.get("unique") and sorted(v.get("columns") or [])==["a","b"]]
print("unique on (a,b) after:", after)
if ok and len(before)==1 and len(after)==0:
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Attack 5 — `probe_error_absent.py` → holds on the patched tree (good)

```python
"""Req 3.2: removing a unique_together entry whose columns have NO matching
uniqueness constraint must still raise ValueError (wrong number: 0)."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class C(models.Model):
    a=models.CharField(max_length=20)
    b=models.CharField(max_length=20)
    class Meta:
        app_label="probeapp"
with connection.schema_editor() as ed:
    ed.create_model(C)
# There is no unique_together on (a,b); ask to drop one -> must raise ValueError
try:
    with connection.schema_editor() as ed:
        ed.alter_unique_together(C, (("a","b"),), tuple())
    print("NO error raised (BAD)"); raised=False; msg=""
except ValueError as e:
    raised=True; msg=str(e); print("raised ValueError:", msg)
if raised and "wrong number" in msg and "(0)" in msg:
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Attack 6 — `probe_index.py` → holds on the patched tree (good)

```python
"""Req 4.3: index_together removal locates & drops the non-unique index
(unaffected by unique narrowing); creating then removing works."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class D(models.Model):
    a=models.CharField(max_length=20)
    b=models.CharField(max_length=20)
    class Meta:
        app_label="probeapp"; index_together=(("a","b"),)
with connection.schema_editor() as ed:
    ed.create_model(D)
def idx_on(cols):
    with connection.cursor() as c:
        consts=connection.introspection.get_constraints(c, D._meta.db_table)
    return [n for n,v in consts.items() if v.get("index") and not v.get("unique") and sorted(v.get("columns") or [])==sorted(cols)]
before=idx_on(["a","b"])
print("non-unique indexes on (a,b) before:", before)
try:
    with connection.schema_editor() as ed:
        ed.alter_index_together(D, (("a","b"),), tuple())
    print("index removal SUCCEEDED"); ok=True
except ValueError as e:
    print("index removal RAISED:", e); ok=False
after=idx_on(["a","b"])
print("non-unique indexes on (a,b) after:", after)
if ok and len(before)>=1 and len(after)==0:
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Attack 7 — `probe_create.py` → holds on the patched tree (good)

```python
"""Req 4.1/4.2: adding a unique_together creates a uniqueness constraint whose
name is the canonical _unique_constraint_name for those columns."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class E(models.Model):
    a=models.CharField(max_length=20)
    b=models.CharField(max_length=20)
    class Meta:
        app_label="probeapp"
with connection.schema_editor() as ed:
    ed.create_model(E)
    canonical=str(ed._unique_constraint_name(E._meta.db_table, ["a","b"], quote=False))
    ed.alter_unique_together(E, tuple(), (("a","b"),))
print("canonical:", canonical)
with connection.cursor() as c:
    consts=connection.introspection.get_constraints(c, E._meta.db_table)
matches=[n for n,v in consts.items() if v.get("unique") and sorted(v.get("columns") or [])==["a","b"]]
print("unique constraints on (a,b) after add:", matches)
if canonical in matches:
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_core.py`

```python
"""Positive control + Req 2.3 (behavioral only, no private-API reference):
removing a unique_together over a column that ALSO declares unique=True must
drop ONLY the unique_together constraint (the canonical name, suffixed `_uniq`)
and leave the field's own unique constraint in place.
Base: ValueError (2 constraints). Naive first-match pick: drops the wrong one."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta:
        app_label="probeapp"; unique_together=(("name",),)
with connection.schema_editor() as ed:
    ed.create_model(Author)
def uniques_on_name():
    with connection.cursor() as c:
        consts=connection.introspection.get_constraints(c, Author._meta.db_table)
    return [n for n,v in consts.items() if v.get("unique") and v.get("columns")==["name"]]
before=uniques_on_name()
print("unique on [name] before:", before)
# the unique_together constraint is the one whose name ends in _uniq
ut_before=[n for n in before if n.endswith("_uniq")]
own_before=[n for n in before if not n.endswith("_uniq")]
print("unique_together (_uniq) before:", ut_before, "| field-own before:", own_before)
try:
    with connection.schema_editor() as ed:
        ed.alter_unique_together(Author, (("name",),), tuple())
    print("removal SUCCEEDED"); ok=True
except ValueError as e:
    print("removal RAISED:", e); ok=False
after=uniques_on_name()
print("unique on [name] after:", after)
# Req 2.3: the _uniq (unique_together) constraint gone; the field's own remains
if (ok and len(ut_before)==1 and len(own_before)==1
        and after==own_before):
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on the gold-patched tree; each maps to a requirement criterion: probe_core=Req2.3 (positive control), probe_pk=Req1.3, probe_canonical=Req2.1/4.2, probe_single=Req3.4, probe_error_absent=Req3.2, probe_index=Req4.3, probe_create=Req4.1/4.2. All run on sqlite in the instance image (allows_multiple_constraints_on_same_fields=True).

POSITIVE CONTROL (probe_core): removing a unique_together over a column that also has its own unique=True must drop ONLY the canonical `_uniq` constraint and keep the field's own. HOLDS patched (after == field-own only); FAILS at base of constraints) => prepatch_reproduced=true. Written purely behaviorally (no private-API reference) so it discriminates on observable constraint state.

### Candidates
- weak_naive.diff: adds a lazy 'drop the first matching uniqueness constraint on ambiguity' branch (no primary_key:False, no canonical-name selection). REJECTED by probe_core: on the unique-field case it drops the field's OWN constraint (introspection order), leaving the _uniq index and raising 'no such index: __unnamed_constraint_1__' on execute. Also rejected by probe_canonical/probe_create (helper absent). This proves the suite discriminates a plausibly-wrong fix.
- weak_partial.diff: the gold patch minus the `primary_key: False` kwarg line. It PASSES every probe including probe_pk (on sqlite the PK is not separately reported as a competing unique constraint on the id column, so the pk case isn't exercised by the probe). Submitted for the harness to re-check against the official F2P/P2P; NOT claimed as too-weak (it retains the full canonical-name narrowing, so it most likely still resolves the hidden test).

Verdict SOUND advisory: >=5 distinct probes hold on patched, positive control discriminates (holds patched, fails base), and >=1 candidate (weak_naive) is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_core.py`, `probe_pk.py`, `probe_canonical.py`, `probe_single.py`, `probe_error_absent.py`, `probe_index.py`, `probe_create.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_core.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_core.py` → holds on the patched tree (good)

Attack 2 — `probe_pk.py` → holds on the patched tree (good)

Attack 3 — `probe_canonical.py` → holds on the patched tree (good)

Attack 4 — `probe_single.py` → holds on the patched tree (good)

Attack 5 — `probe_error_absent.py` → holds on the patched tree (good)

Attack 6 — `probe_index.py` → holds on the patched tree (good)

Attack 7 — `probe_create.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_core.py`

```python
"""Positive control + Req 2.3 (behavioral only, no private-API reference):
removing a unique_together over a column that ALSO declares unique=True must
drop ONLY the unique_together constraint (the canonical name, suffixed `_uniq`)
and leave the field's own unique constraint in place.
Base: ValueError (2 constraints). Naive first-match pick: drops the wrong one."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta:
        app_label="probeapp"; unique_together=(("name",),)
with connection.schema_editor() as ed:
    ed.create_model(Author)
def uniques_on_name():
    with connection.cursor() as c:
        consts=connection.introspection.get_constraints(c, Author._meta.db_table)
    return [n for n,v in consts.items() if v.get("unique") and v.get("columns")==["name"]]
before=uniques_on_name()
print("unique on [name] before:", before)
# the unique_together constraint is the one whose name ends in _uniq
ut_before=[n for n in before if n.endswith("_uniq")]
own_before=[n for n in before if not n.endswith("_uniq")]
print("unique_together (_uniq) before:", ut_before, "| field-own before:", own_before)
try:
    with connection.schema_editor() as ed:
        ed.alter_unique_together(Author, (("name",),), tuple())
    print("removal SUCCEEDED"); ok=True
except ValueError as e:
    print("removal RAISED:", e); ok=False
after=uniques_on_name()
print("unique on [name] after:", after)
# Req 2.3: the _uniq (unique_together) constraint gone; the field's own remains
if (ok and len(ut_before)==1 and len(own_before)==1
        and after==own_before):
    print("CRITERION HOLDS"); sys.exit(0)
print("CRITERION FAILS"); sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on the gold-patched tree; each maps to a requirement criterion: probe_core=Req2.3 (positive control), probe_pk=Req1.3, probe_canonical=Req2.1/4.2, probe_single=Req3.4, probe_error_absent=Req3.2, probe_index=Req4.3, probe_create=Req4.1/4.2. All run on sqlite in the instance image (allows_multiple_constraints_on_same_fields=True).

POSITIVE CONTROL (probe_core): removing a unique_together over a column that also has its own unique=True must drop ONLY the canonical `_uniq` constraint and keep the field's own. HOLDS patched (after == field-own only); FAILS at base of constraints) => prepatch_reproduced=true. Written purely behaviorally (no private-API reference) so it discriminates on observable constraint state.

### Candidates
- weak_naive.diff: adds a lazy 'drop the first matching uniqueness constraint on ambiguity' branch (no primary_key:False, no canonical-name selection). REJECTED by probe_core: on the unique-field case it drops the field's OWN constraint (introspection order), leaving the _uniq index and raising 'no such index: __unnamed_constraint_1__' on execute. Also rejected by probe_canonical/probe_create (helper absent). This proves the suite discriminates a plausibly-wrong fix.
- weak_partial.diff: the gold patch minus the `primary_key: False` kwarg line. It PASSES every probe including probe_pk (on sqlite the PK is not separately reported as a competing unique constraint on the id column, so the pk case isn't exercised by the probe). Submitted for the harness to re-check against the official F2P/P2P; NOT claimed as too-weak (it retains the full canonical-name narrowing, so it most likely still resolves the hidden test).

Verdict SOUND advisory: >=5 distinct probes hold on patched, positive control discriminates (holds patched, fails base), and >=1 candidate (weak_naive) is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes on gold-patched image confirm: _constraint_names has 'primary_key' param; _unique_constraint_name exists with 'quote' arg; _delete_composed_index contains the narrowing block and the count!=1 ValueError. Behavioral boundary (drop unique_together while leaving PK or field-own unique constraint intact) is exactly what the two acceptance cases (Req1.3, Req2.3) describe, matching the issue and the single FAIL_TO_PASS test test_remove_unique_together_on_unique_field.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe only behavior derivable from the public problem_statement + hints (both scenarios — unique_together on a pk column, and on a unique=True field — the ValueError message, the PostgreSQL/multiple-constraints condition, and the unique_together naming-scheme distinction are all public). No hidden-test artifacts leak: test function names (test_remove_unique_together_on_pk_field/_on_unique_field), the test file path, app labels (test_rutopkf/test_rutouf), and literal constraint-name strings (test_rutopkf_pony_id_fb61f881_uniq, *_pkey, *_name_key) are absent. The gold-patch's new method _unique_constraint_name is NOT named (doc says 'canonical constraint name it generates' generically), and the gold edit {'unique': True, 'primary_key': False} is described behaviorally, not quoted. Named symbols (alter_unique_together, _delete_composed_index, _constraint_names, allows_multiple_constraints_on_same_fields, sql_delete_unique) are pre-existing public Django identifiers = legitimate localization. The two-requirement structure mirrors the two public scenarios, not the test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
