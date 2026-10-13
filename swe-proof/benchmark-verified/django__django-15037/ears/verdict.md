# P2 adversarial audit — django__django-15037

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 1.1 & 1.5 (POSITIVE CONTROL): FK to a non-PK unique column -> to_field='<col>'
ddl("CREATE TABLE foo (id integer primary key, other_id integer UNIQUE)",
    "CREATE TABLE bar (id integer primary key, other_id integer REFERENCES foo(other_id))")
o = inspect('bar')
print(o)
ok = ("models.ForeignKey" in o and "to_field='other_id'" in o)
print("OBSERVED to_field present:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 1.4: FK referencing the target table's PK column -> NO to_field
ddl("CREATE TABLE foo (id integer primary key, other_id integer UNIQUE)",
    "CREATE TABLE bar (id integer primary key, foo_id integer REFERENCES foo(id))")
o = inspect('bar')
print(o)
ok = ("models.ForeignKey" in o and "to_field" not in o)
print("OBSERVED no to_field for PK-targeting FK:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 2.1: relation column is UNIQUE => OneToOneField, NO to_field even to non-PK col
ddl("CREATE TABLE foo (id integer primary key, other_id integer UNIQUE)",
    "CREATE TABLE bar (id integer primary key, other_id integer UNIQUE REFERENCES foo(other_id))")
o = inspect('bar')
print(o)
ok = ("models.OneToOneField" in o and "to_field" not in o)
print("OBSERVED OneToOne + no to_field:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 1.5: emitted value is EXACTLY the introspected referenced-column name, as a string literal.
# Use a distinctively named referenced column to guard against hardcoding.
ddl("CREATE TABLE foo (id integer primary key, weird_ref_col integer UNIQUE)",
    "CREATE TABLE bar (id integer primary key, fk_col integer REFERENCES foo(weird_ref_col))")
o = inspect('bar')
print(o)
ok = ("to_field='weird_ref_col'" in o)
print("OBSERVED exact string-literal ref col:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 4.1: a non-relation column gets NO to_field and keeps its plain field type
ddl("CREATE TABLE solo (id integer primary key, name varchar(20))")
o = inspect('solo')
print(o)
# 'ForeignKey' appears in the inspectdb banner comment, so don't test it; check the field body.
body = "\n".join(l for l in o.splitlines() if not l.lstrip().startswith('#'))
ok = ("to_field" not in body and "name = models.CharField" in body and "models.ForeignKey(" not in body)
print("OBSERVED plain field, no to_field:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 3.1 & 3.4: self-reference target preserved; on-delete marker + blank/null kept.
# Self FK to non-PK unique col: target must be 'self', still to_field, still DO_NOTHING/null.
ddl("CREATE TABLE node (id integer primary key, code integer UNIQUE, "
    "parent_code integer REFERENCES node(code))")
o = inspect('node')
print(o)
ok = ("models.ForeignKey('self'" in o and "to_field='code'" in o
      and "models.DO_NOTHING" in o and "blank=True, null=True" in o)
print("OBSERVED self target + on-delete + params:", ok)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 1.2 & 1.4: PK column of the REFERENCED table (named 'code', not 'id') must be
# introspected from the referenced table. FK targets foo's PK => NO to_field.
# A fix that introspects the CURRENT table's PK ('id') would wrongly emit to_field='code'.
ddl("CREATE TABLE foo (code integer primary key, label varchar(10))",
    "CREATE TABLE bar (id integer primary key, foo_code integer REFERENCES foo(code))")
o = inspect('bar')
print(o)
body = "\n".join(l for l in o.splitlines() if not l.lstrip().startswith('#'))
ok = ("models.ForeignKey(" in body and "to_field" not in body)
print("OBSERVED FK to referenced-table PK => no to_field:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 1.1 & 1.5 (POSITIVE CONTROL): FK to a non-PK unique column -> to_field='<col>'
ddl("CREATE TABLE foo (id integer primary key, other_id integer UNIQUE)",
    "CREATE TABLE bar (id integer primary key, other_id integer REFERENCES foo(other_id))")
o = inspect('bar')
print(o)
ok = ("models.ForeignKey" in o and "to_field='other_id'" in o)
print("OBSERVED to_field present:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15037: inspectdb must emit to_field for FKs referencing a non-PK column. Reproduced live in the official image against a temp sqlite DB running `call_command('inspectdb', ...)`.

### PROBES (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.5, POSITIVE CONTROL): FK to non-PK unique col -> `to_field='other_id'`. HOLDS patched, VIOLATED at base (prepatch reproduced).
- probe_2 (Req 1.4): FK to referenced table's PK col -> NO to_field. HOLDS patched & base (regression criterion).
- probe_3 (Req 2.1/2.2): unique relation col -> OneToOneField, NO to_field even to non-PK. HOLDS patched & base.
- probe_4 (Req 1.5): distinctively-named ref col 'weird_ref_col' -> exact string literal to_field='weird_ref_col' (guards against hardcoding). HOLDS patched, VIOLATED base.
- probe_5 (Req 4.1): non-relation column -> plain field, no to_field (excludes inspectdb banner comment which contains 'ForeignKey'). HOLDS patched & base.
- probe_6 (Req 3.1/3.4): self-referential FK to non-PK unique col -> target 'self', to_field, models.DO_NOTHING, blank/null preserved. HOLDS patched, VIOLATED base.
- probe_7 (Req 1.2/1.4): referenced table has PK named 'code' (not 'id'); FK targets it -> NO to_field. HOLDS patched & base; catches fixes that introspect the wrong table's PK.

DISCRIMINATION: probe_1 fails at base and holds patched (positive control leg confirmed). probes 4 and 6 also flip base->patched.

### WRONG-FIX CANDIDATES (both REJECTED, proving the suite discriminates):
- weak_A (always adds to_field to every ForeignKey, no PK comparison): REJECTED by probe_2 and probe_7.
- weak_B (introspects CURRENT table's PK `table_name` instead of the REFERENCED table `ref_db_table`): REJECTED by probe_7 (emits spurious to_field when referenced-table PK name differs from current-table PK name).

No requirements-conforming alternative patch was found that would fail the hidden tests; the suite pins the exact behavior (correct referenced-table PK comparison, OneToOne exclusion, exact string-literal ref column, self/target and param preservation). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import tempfile, sys, django
from io import StringIO
from django.conf import settings
db = tempfile.mktemp(suffix='.sqlite3')
settings.configure(
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':db}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import connection
from django.core.management import call_command
def inspect(table):
    out = StringIO(); call_command('inspectdb', table, stdout=out); return out.getvalue()
def ddl(*stmts):
    with connection.cursor() as c:
        for s in stmts: c.execute(s)
# Req 1.1 & 1.5 (POSITIVE CONTROL): FK to a non-PK unique column -> to_field='<col>'
ddl("CREATE TABLE foo (id integer primary key, other_id integer UNIQUE)",
    "CREATE TABLE bar (id integer primary key, other_id integer REFERENCES foo(other_id))")
o = inspect('bar')
print(o)
ok = ("models.ForeignKey" in o and "to_field='other_id'" in o)
print("OBSERVED to_field present:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15037: inspectdb must emit to_field for FKs referencing a non-PK column. Reproduced live in the official image against a temp sqlite DB running `call_command('inspectdb', ...)`.

### PROBES (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.5, POSITIVE CONTROL): FK to non-PK unique col -> `to_field='other_id'`. HOLDS patched, VIOLATED at base (prepatch reproduced).
- probe_2 (Req 1.4): FK to referenced table's PK col -> NO to_field. HOLDS patched & base (regression criterion).
- probe_3 (Req 2.1/2.2): unique relation col -> OneToOneField, NO to_field even to non-PK. HOLDS patched & base.
- probe_4 (Req 1.5): distinctively-named ref col 'weird_ref_col' -> exact string literal to_field='weird_ref_col' (guards against hardcoding). HOLDS patched, VIOLATED base.
- probe_5 (Req 4.1): non-relation column -> plain field, no to_field (excludes inspectdb banner comment which contains 'ForeignKey'). HOLDS patched & base.
- probe_6 (Req 3.1/3.4): self-referential FK to non-PK unique col -> target 'self', to_field, models.DO_NOTHING, blank/null preserved. HOLDS patched, VIOLATED base.
- probe_7 (Req 1.2/1.4): referenced table has PK named 'code' (not 'id'); FK targets it -> NO to_field. HOLDS patched & base; catches fixes that introspect the wrong table's PK.

DISCRIMINATION: probe_1 fails at base and holds patched (positive control leg confirmed). probes 4 and 6 also flip base->patched.

### WRONG-FIX CANDIDATES (both REJECTED, proving the suite discriminates):
- weak_A (always adds to_field to every ForeignKey, no PK comparison): REJECTED by probe_2 and probe_7.
- weak_B (introspects CURRENT table's PK `table_name` instead of the REFERENCED table `ref_db_table`): REJECTED by probe_7 (emits spurious to_field when referenced-table PK name differs from current-table PK name).

No requirements-conforming alternative patch was found that would fail the hidden tests; the suite pins the exact behavior (correct referenced-table PK comparison, OneToOne exclusion, exact string-literal ref column, self/target and param preservation). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds exactly: unpack ref_db_column/ref_db_table; in ForeignKey branch compute ref_pk_column and set extra_params['to_field']=ref_db_column when a distinct non-null pk exists; rel_to refactored to use ref_db_table (semantically identical to prior relations[column_name][1]). Requirements pin the changed observable behavior (to_field emission) biconditionally and correctly scope it to plain FKs — the modeling boundary is the actual behavior change, not a narrow slice. Confirmed against the gold-patched source in the instance image and the FAIL_TO_PASS test expectation.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior only. The foo/bar schema example and the FK-to-non-pk-column problem are public in problem_statement. No hidden test identifiers appear: test_foreign_key_to_field, class ForeignKeyToField, field to_field_fk, PeopleMoreData/InspectdbPeoplemoredata, column people_unique_id, and tests/inspectdb/*.py paths are all absent. `to_field` is a standard public Django ForeignKey keyword (not fix-invented); get_primary_key_column and connection.introspection are legitimate localization of the changed module. The branch enumeration (emit to_field when ref-col != referenced-table pk; skip when equal/empty pk; skip for OneToOne) reflects the gold patch's conditional logic expressed as behavior, and does not mirror test parametrization (the suite has a single F2P case). No quoted test/gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
