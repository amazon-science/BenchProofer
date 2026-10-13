# P2 adversarial audit — django__django-15252

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Requirement 1 crit 1 & 3.
plan=[] and has_table()==False:
  - ensure_schema() MUST NOT be called (R1.1)
  - NO db queries issued (R1.3)
HOLDS iff ensure_schema not called and 0 queries. At base ensure_schema IS
called, so this VIOLATES at base -> discriminating.
"""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from unittest import mock
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

executor = MigrationExecutor(connection)

with mock.patch.object(MigrationRecorder, "has_table", return_value=False), \
     mock.patch.object(MigrationRecorder, "ensure_schema") as m_ensure:
    connection.queries_log.clear()
    force_debug = connection.force_debug_cursor
    connection.force_debug_cursor = True  # record queries
    try:
        result = executor.migrate([], plan=[])
    finally:
        connection.force_debug_cursor = force_debug
    nqueries = len(connection.queries)

print("ensure_schema called:", m_ensure.called)
print("num queries:", nqueries)
print("result type:", type(result).__name__)

ok = (not m_ensure.called) and nqueries == 0 and result is not None
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1 crit 2: plan=[] AND has_table()==False -> returns immediately
a project state equal to _create_project_state(with_applied_migrations=False),
without executing the remainder. We verify the returned state equals the
executor's own _create_project_state(False) result (same set of models).
"""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from unittest import mock
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

executor = MigrationExecutor(connection)
expected = executor._create_project_state(with_applied_migrations=False)

with mock.patch.object(MigrationRecorder, "has_table", return_value=False), \
     mock.patch.object(MigrationRecorder, "ensure_schema"):
    # If the remainder ran, record_migration/apply would be attempted; sentinel
    # via patching apply_migration to raise.
    with mock.patch.object(MigrationExecutor, "apply_migration",
                           side_effect=AssertionError("remainder executed!")):
        result = executor.migrate([], plan=[])

exp_keys = set(expected.models.keys())
res_keys = set(result.models.keys())
print("expected model count:", len(exp_keys))
print("result model count:", len(res_keys))
print("keys equal:", exp_keys == res_keys)

ok = (result is not None) and exp_keys == res_keys
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 1 crit 4: plan=[] AND has_table()==True ->
ensure_schema() NOT called, but executor PROCEEDS through remaining steps and
returns the resulting project state (does NOT early-return).
We detect "proceeded" by patching check_replacements (called near the end of
migrate) and asserting it WAS reached.
"""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from unittest import mock
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

executor = MigrationExecutor(connection)

with mock.patch.object(MigrationRecorder, "has_table", return_value=True), \
     mock.patch.object(MigrationRecorder, "ensure_schema") as m_ensure, \
     mock.patch.object(MigrationExecutor, "check_replacements") as m_check:
    result = executor.migrate([], plan=[])

print("ensure_schema called:", m_ensure.called)
print("check_replacements reached (proceeded):", m_check.called)
print("result is not None:", result is not None)

ok = (not m_ensure.called) and m_check.called and result is not None
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2 crit 1 & 2 (and R2.3): provisioning still happens for
plan=None (unset) and for a non-empty plan.
- plan=None  -> ensure_schema() called.
- plan=[('x',False)] non-empty -> ensure_schema() called.
We mock migration_plan / apply etc. minimally by intercepting after ensure.
"""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from unittest import mock
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder


class _Stop(Exception):
    pass


def run_case(plan):
    executor = MigrationExecutor(connection)
    with mock.patch.object(MigrationRecorder, "has_table", return_value=False), \
         mock.patch.object(MigrationRecorder, "ensure_schema") as m_ensure, \
         mock.patch.object(MigrationExecutor, "migration_plan",
                           side_effect=_Stop("stop after ensure")):
        called = None
        try:
            executor.migrate([], plan=plan)
        except _Stop:
            pass
        called = m_ensure.called
    return called


# plan=None : migration_plan is called after ensure -> _Stop; ensure must be called
none_called = run_case(None)
# non-empty plan: a fake plan list; migration_plan still called (full_plan) -> _Stop
nonempty_called = run_case([("fake", False)])

print("plan=None ensure_schema called:", none_called)
print("non-empty plan ensure_schema called:", nonempty_called)

ok = bool(none_called) and bool(nonempty_called)
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 3 crit 4 (regression): MigrationRecorder retains semantics.
On a fresh in-memory DB:
  - has_table() False before ensure_schema
  - ensure_schema() creates the table on demand -> has_table() True
  - record_applied adds a row (applied_migrations reflects it)
  - record_unapplied removes it
"""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

rec = MigrationRecorder(connection)
before = rec.has_table()
rec.ensure_schema()
after = rec.has_table()

rec.record_applied("myapp", "0001_initial")
applied = rec.applied_migrations()
has_after_record = ("myapp", "0001_initial") in applied

rec.record_unapplied("myapp", "0001_initial")
applied2 = rec.applied_migrations()
gone_after_unrecord = ("myapp", "0001_initial") not in applied2

print("has_table before ensure:", before)
print("has_table after ensure:", after)
print("recorded present:", has_after_record)
print("unrecorded removed:", gone_after_unrecord)

ok = (not before) and after and has_after_record and gone_after_unrecord
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Requirement 1 crit 1 & 3.
plan=[] and has_table()==False:
  - ensure_schema() MUST NOT be called (R1.1)
  - NO db queries issued (R1.3)
HOLDS iff ensure_schema not called and 0 queries. At base ensure_schema IS
called, so this VIOLATES at base -> discriminating.
"""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from unittest import mock
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

executor = MigrationExecutor(connection)

with mock.patch.object(MigrationRecorder, "has_table", return_value=False), \
     mock.patch.object(MigrationRecorder, "ensure_schema") as m_ensure:
    connection.queries_log.clear()
    force_debug = connection.force_debug_cursor
    connection.force_debug_cursor = True  # record queries
    try:
        result = executor.migrate([], plan=[])
    finally:
        connection.force_debug_cursor = force_debug
    nqueries = len(connection.queries)

print("ensure_schema called:", m_ensure.called)
print("num queries:", nqueries)
print("result type:", type(result).__name__)

ok = (not m_ensure.called) and nqueries == 0 and result is not None
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15252: MigrationExecutor.migrate() must skip recorder.ensure_schema() for an explicitly empty plan (plan==[]) and early-return _create_project_state(with_applied_migrations=False) when has_table() is False, while still provisioning for plan=None or non-empty plans.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1 + R1.3, POSITIVE CONTROL): plan=[] & has_table()==False -> ensure_schema NOT called AND 0 queries. HOLDS patched; VIOLATED at base (base unconditionally calls ensure_schema) -> discriminates. prepatch_reproduced=true.
- probe_2 (R1.2): plan=[] & has_table()==False -> returns state equal to _create_project_state(with_applied_migrations=False) and does NOT run the remainder (apply_migration patched to raise; never triggered). HOLDS.
- probe_3 (R1.4): plan=[] & has_table()==True -> ensure_schema NOT called but executor PROCEEDS (check_replacements reached) and returns state. HOLDS.
- probe_4 (R2.1/R2.2/R2.3): plan=None and non-empty plan both call ensure_schema. HOLDS on gold.
- probe_5 (R3.4 regression): MigrationRecorder semantics intact — has_table False->ensure_schema creates table->True, record_applied/record_unapplied add/remove rows. HOLDS.

Discrimination demonstrated: weak candidate weak.diff uses `if not plan:` instead of `if plan == []:`, conflating plan=None with plan=[] and thereby skipping provisioning for the unset-plan case (violates R2.1/R2.3). probe_4 REJECTS it (VIOLATED); probes 1,2,3,5 pass. This wrong fix would also break the F2P behavior (plan=None path no longer ensures schema). Suite discriminates wrong implementations -> not a rubber stamp.

All 5 probes hold on the gold-patched tree; positive control fails at base and holds patched. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control + Requirement 1 crit 1 & 3.
plan=[] and has_table()==False:
  - ensure_schema() MUST NOT be called (R1.1)
  - NO db queries issued (R1.3)
HOLDS iff ensure_schema not called and 0 queries. At base ensure_schema IS
called, so this VIOLATES at base -> discriminating.
"""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from unittest import mock
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

executor = MigrationExecutor(connection)

with mock.patch.object(MigrationRecorder, "has_table", return_value=False), \
     mock.patch.object(MigrationRecorder, "ensure_schema") as m_ensure:
    connection.queries_log.clear()
    force_debug = connection.force_debug_cursor
    connection.force_debug_cursor = True  # record queries
    try:
        result = executor.migrate([], plan=[])
    finally:
        connection.force_debug_cursor = force_debug
    nqueries = len(connection.queries)

print("ensure_schema called:", m_ensure.called)
print("num queries:", nqueries)
print("result type:", type(result).__name__)

ok = (not m_ensure.called) and nqueries == 0 and result is not None
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15252: MigrationExecutor.migrate() must skip recorder.ensure_schema() for an explicitly empty plan (plan==[]) and early-return _create_project_state(with_applied_migrations=False) when has_table() is False, while still provisioning for plan=None or non-empty plans.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1 + R1.3, POSITIVE CONTROL): plan=[] & has_table()==False -> ensure_schema NOT called AND 0 queries. HOLDS patched; VIOLATED at base (base unconditionally calls ensure_schema) -> discriminates. prepatch_reproduced=true.
- probe_2 (R1.2): plan=[] & has_table()==False -> returns state equal to _create_project_state(with_applied_migrations=False) and does NOT run the remainder (apply_migration patched to raise; never triggered). HOLDS.
- probe_3 (R1.4): plan=[] & has_table()==True -> ensure_schema NOT called but executor PROCEEDS (check_replacements reached) and returns state. HOLDS.
- probe_4 (R2.1/R2.2/R2.3): plan=None and non-empty plan both call ensure_schema. HOLDS on gold.
- probe_5 (R3.4 regression): MigrationRecorder semantics intact — has_table False->ensure_schema creates table->True, record_applied/record_unapplied add/remove rows. HOLDS.

Discrimination demonstrated: weak candidate weak.diff uses `if not plan:` instead of `if plan == []:`, conflating plan=None with plan=[] and thereby skipping provisioning for the unset-plan case (violates R2.1/R2.3). probe_4 REJECTS it (VIOLATED); probes 1,2,3,5 pass. This wrong fix would also break the F2P behavior (plan=None path no longer ensures schema). Suite discriminates wrong implementations -> not a rubber stamp.

All 5 probes hold on the gold-patched tree; positive control fails at base and holds patched. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch replaces the unconditional self.recorder.ensure_schema() at the head of MigrationExecutor.migrate() with: `if plan == []: if not self.recorder.has_table(): return self._create_project_state(with_applied_migrations=False); else: self.recorder.ensure_schema()`. The requirements pin exactly this changed observable behavior (the branch keyed on the explicitly-empty plan and the has_table/ensure_schema/_create_project_state interplay), not a narrow slice or a helper. R3 correctly scopes regression protection; R3.5/R3.6 (TEST['MIGRATE']) faithfully reflect the issue's multi-database/test-DB motivation. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements track the gold fix closely (plan==[] vs None branch; early return via _create_project_state for the no-applied-migrations case; ensure_schema/has_table; 'no queries' mirroring assertNumQueries(0); TEST['MIGRATE'] false→still sync unmigrated apps). However every identifier named is PRE-EXISTING and used for legitimate localization (executor.migrate, MigrationRecorder.has_table/ensure_schema, _create_project_state, with_applied_migrations) — none is fix-invented. No test file paths, no test function/class names (test_migrate_skips_schema_creation, test_migrate_test_setting_false_ensure_schema, TestDbCreationTests, ExecutorTests), no parametrization ids, and no quoted test/gold source appear. The (plan==[], has_table) case matrix and the empty-vs-None distinction describe the observable behavioral contract of migrate() rather than mirroring test parametrization (the tests are not parametrized). 'No database queries' and 'still synchronize unmigrated applications' are observable behaviors, not transcribed assertions. Borderline on gold-reconstruction because the fix is a ~5-line diff, but the doc stays within behavioral description + localization, which the rubric deems legitimate.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
