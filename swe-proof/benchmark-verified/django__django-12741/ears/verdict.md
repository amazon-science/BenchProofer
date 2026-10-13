# P2 adversarial audit — django__django-12741

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
"""Req1.1 / Req1.3: execute_sql_flush accepts a SINGLE positional argument (the
SQL statement list) and runs without TypeError. Positive control candidate."""
import contextlib, inspect, sys

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db import transaction


class FakeCursor:
    def __init__(self, log): self.log = log
    def execute(self, sql): self.log.append(sql)

class FakeFeatures:
    can_rollback_ddl = True

class FakeConnection:
    def __init__(self):
        self.alias = "my_alias"; self.features = FakeFeatures(); self.executed = []
    def cursor(self):
        log = self.executed
        @contextlib.contextmanager
        def cm(): yield FakeCursor(log)
        return cm()


# Inspect signature: exactly one caller-supplied positional besides self.
sig = inspect.signature(BaseDatabaseOperations.execute_sql_flush)
params = [p for p in sig.parameters.values() if p.name != "self"]
pos = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
print("signature params:", [p.name for p in params])
if len(pos) != 1:
    print("FAIL: expected exactly one positional param, got", [p.name for p in pos])
    sys.exit(1)

# no-op atomic
@contextlib.contextmanager
def fake_atomic(*a, **k): yield
transaction.atomic = fake_atomic

conn = FakeConnection()
ops = BaseDatabaseOperations(conn)
sql_list = ["DELETE FROM a;", "DELETE FROM b;"]
try:
    ops.execute_sql_flush(sql_list)
except TypeError as e:
    print("FAIL: TypeError on single-arg call:", e)
    sys.exit(1)
print("executed:", conn.executed)
if conn.executed != sql_list:
    print("FAIL: statements not executed correctly")
    sys.exit(1)
print("PASS: single positional arg accepted, statements executed")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 / Req2.1 / Req2.2: transaction opened with using=self.connection.alias
and savepoint=self.connection.features.can_rollback_ddl."""
import contextlib, sys

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db import transaction


class FakeCursor:
    def __init__(self, log): self.log = log
    def execute(self, sql): self.log.append(sql)

class FakeFeatures:
    can_rollback_ddl = "SENTINEL_ROLLBACK"  # distinctive object

class FakeConnection:
    def __init__(self):
        self.alias = "DISTINCT_ALIAS_XYZ"; self.features = FakeFeatures(); self.executed = []
    def cursor(self):
        log = self.executed
        @contextlib.contextmanager
        def cm(): yield FakeCursor(log)
        return cm()


captured = {}
@contextlib.contextmanager
def fake_atomic(*args, **kwargs):
    captured["args"] = args
    captured["kwargs"] = kwargs
    yield
transaction.atomic = fake_atomic

conn = FakeConnection()
ops = BaseDatabaseOperations(conn)
ops.execute_sql_flush(["DELETE FROM t;"])

# Reconstruct effective using/savepoint from args+kwargs.
# atomic signature: atomic(using=None, savepoint=True)
args = captured.get("args", ())
kw = captured.get("kwargs", {})
print("atomic args:", args, "kwargs:", kw)
using = kw.get("using", args[0] if len(args) >= 1 else None)
savepoint = kw.get("savepoint", args[1] if len(args) >= 2 else None)
print("effective using:", using, "savepoint:", savepoint)

if using != "DISTINCT_ALIAS_XYZ":
    print("FAIL: transaction not bound to self.connection.alias")
    sys.exit(1)
if savepoint != "SENTINEL_ROLLBACK":
    print("FAIL: savepoint not from can_rollback_ddl")
    sys.exit(1)
print("PASS: transaction bound to connection alias with can_rollback_ddl savepoint")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4: the OLD two-arg form (database, sql_list) SHALL fail (TypeError),
not silently accept the extra value."""
import contextlib, sys

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db import transaction


class FakeCursor:
    def __init__(self, log): self.log = log
    def execute(self, sql): self.log.append(sql)

class FakeFeatures:
    can_rollback_ddl = True

class FakeConnection:
    def __init__(self):
        self.alias = "my_alias"; self.features = FakeFeatures(); self.executed = []
    def cursor(self):
        log = self.executed
        @contextlib.contextmanager
        def cm(): yield FakeCursor(log)
        return cm()


@contextlib.contextmanager
def fake_atomic(*a, **k): yield
transaction.atomic = fake_atomic

conn = FakeConnection()
ops = BaseDatabaseOperations(conn)
try:
    ops.execute_sql_flush("some_db_alias", ["DELETE FROM t;"])
except TypeError as e:
    print("PASS: two-arg form raised TypeError:", e)
    sys.exit(0)
print("FAIL: two-arg form did NOT raise; executed:", conn.executed)
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.3: each supplied statement executed exactly once, in order, through a
cursor on the connection."""
import contextlib, sys

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db import transaction


class FakeCursor:
    def __init__(self, log): self.log = log
    def execute(self, sql): self.log.append(sql)

class FakeFeatures:
    can_rollback_ddl = True

class FakeConnection:
    def __init__(self):
        self.alias = "my_alias"; self.features = FakeFeatures()
        self.executed = []; self.cursor_calls = 0
    def cursor(self):
        self.cursor_calls += 1
        log = self.executed
        @contextlib.contextmanager
        def cm(): yield FakeCursor(log)
        return cm()


@contextlib.contextmanager
def fake_atomic(*a, **k): yield
transaction.atomic = fake_atomic

conn = FakeConnection()
ops = BaseDatabaseOperations(conn)
sql_list = ["S1;", "S2;", "S3;", "S2;"]  # includes a repeat to catch dedup/reorder
ops.execute_sql_flush(sql_list)
print("executed:", conn.executed, "cursor_calls:", conn.cursor_calls)
if conn.executed != sql_list:
    print("FAIL: statements not executed once each in order")
    sys.exit(1)
if conn.cursor_calls < 1:
    print("FAIL: no cursor obtained from connection")
    sys.exit(1)
print("PASS: each statement executed exactly once in order via connection cursor")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1 / Req3.4: the flush management command calls execute_sql_flush with
only the SQL list (no separate database identifier). We assert the call arity
statically from the command source and dynamically by intercepting the call."""
import contextlib, sys, inspect

import django.core.management.commands.flush as flushmod

src = inspect.getsource(flushmod)
# Find the execute_sql_flush call and verify it does not pass `database` first.
import re
calls = re.findall(r"execute_sql_flush\(([^)]*)\)", src)
print("execute_sql_flush call args in flush.py:", calls)
if not calls:
    print("FAIL: no execute_sql_flush call found in flush command")
    sys.exit(1)
for c in calls:
    argstr = c.strip()
    # split top-level commas
    parts = [p.strip() for p in argstr.split(",") if p.strip()]
    print("parsed args:", parts)
    # Must be exactly one argument, and it must be the sql list, not `database`.
    if len(parts) != 1:
        print("FAIL: flush command passes", len(parts), "args to execute_sql_flush")
        sys.exit(1)
    if parts[0] == "database" or parts[0].startswith("database,"):
        print("FAIL: flush command passes a database identifier")
        sys.exit(1)
print("PASS: flush command calls execute_sql_flush with a single sql-list arg")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 / Req1.3: execute_sql_flush accepts a SINGLE positional argument (the
SQL statement list) and runs without TypeError. Positive control candidate."""
import contextlib, inspect, sys

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db import transaction


class FakeCursor:
    def __init__(self, log): self.log = log
    def execute(self, sql): self.log.append(sql)

class FakeFeatures:
    can_rollback_ddl = True

class FakeConnection:
    def __init__(self):
        self.alias = "my_alias"; self.features = FakeFeatures(); self.executed = []
    def cursor(self):
        log = self.executed
        @contextlib.contextmanager
        def cm(): yield FakeCursor(log)
        return cm()


# Inspect signature: exactly one caller-supplied positional besides self.
sig = inspect.signature(BaseDatabaseOperations.execute_sql_flush)
params = [p for p in sig.parameters.values() if p.name != "self"]
pos = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
print("signature params:", [p.name for p in params])
if len(pos) != 1:
    print("FAIL: expected exactly one positional param, got", [p.name for p in pos])
    sys.exit(1)

# no-op atomic
@contextlib.contextmanager
def fake_atomic(*a, **k): yield
transaction.atomic = fake_atomic

conn = FakeConnection()
ops = BaseDatabaseOperations(conn)
sql_list = ["DELETE FROM a;", "DELETE FROM b;"]
try:
    ops.execute_sql_flush(sql_list)
except TypeError as e:
    print("FAIL: TypeError on single-arg call:", e)
    sys.exit(1)
print("executed:", conn.executed)
if conn.executed != sql_list:
    print("FAIL: statements not executed correctly")
    sys.exit(1)
print("PASS: single positional arg accepted, statements executed")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover simplifying BaseDatabaseOperations.execute_sql_flush from (using, sql_list) to (sql_list), inferring the target DB from self.connection.alias, and updating the flush management command caller.

Probes (all HOLD on gold-patched, all VIOLATED at base):
- probe_1 (Req1.1/1.3): signature has exactly one caller-supplied positional; single-arg call executes without TypeError and runs all statements. PATCHED=HOLDS, BASE=VIOLATED (base signature is ['using','sql_list']). POSITIVE CONTROL.
- probe_2 (Req1.2/2.1/2.2): transaction.atomic is called with using=self.connection.alias (distinct sentinel alias) and savepoint=self.connection.features.can_rollback_ddl (distinct sentinel). PATCHED=HOLDS, BASE=VIOLATED.
- probe_3 (Req1.4): the OLD two-arg form execute_sql_flush(db, sql_list) must raise TypeError. PATCHED=HOLDS (raises), BASE=VIOLATED (two-arg accepted).
- probe_4 (Req2.3): each statement (incl. a duplicate) executed exactly once, in order, via a single connection cursor. PATCHED=HOLDS, BASE=VIOLATED.
- probe_5 (Req3.1/3.4): flush management command calls execute_sql_flush with a single sql-list arg, no database identifier. PATCHED=HOLDS, BASE=VIOLATED (base passes 'database, sql_list').

Weak candidate (weak.diff): correct body (using=self.connection.alias) but signature kept a trailing optional `using=None` param, so the removed identifier is still ACCEPTED. REJECTED by the suite: probe_1 (two positionals allowed) and probe_3 (two-arg form silently accepted — violates Req1.4). probe_2/4/5 hold under it. This demonstrates the suite discriminates the lazy 'keep-backward-compat' fix that requirement 1.4 forbids.

All 5 probes hold on patched; positive control discriminates base vs patched; >=1 candidate exercised and rejected. Verdict SOUND.

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
"""Req1.1 / Req1.3: execute_sql_flush accepts a SINGLE positional argument (the
SQL statement list) and runs without TypeError. Positive control candidate."""
import contextlib, inspect, sys

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db import transaction


class FakeCursor:
    def __init__(self, log): self.log = log
    def execute(self, sql): self.log.append(sql)

class FakeFeatures:
    can_rollback_ddl = True

class FakeConnection:
    def __init__(self):
        self.alias = "my_alias"; self.features = FakeFeatures(); self.executed = []
    def cursor(self):
        log = self.executed
        @contextlib.contextmanager
        def cm(): yield FakeCursor(log)
        return cm()


# Inspect signature: exactly one caller-supplied positional besides self.
sig = inspect.signature(BaseDatabaseOperations.execute_sql_flush)
params = [p for p in sig.parameters.values() if p.name != "self"]
pos = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
print("signature params:", [p.name for p in params])
if len(pos) != 1:
    print("FAIL: expected exactly one positional param, got", [p.name for p in pos])
    sys.exit(1)

# no-op atomic
@contextlib.contextmanager
def fake_atomic(*a, **k): yield
transaction.atomic = fake_atomic

conn = FakeConnection()
ops = BaseDatabaseOperations(conn)
sql_list = ["DELETE FROM a;", "DELETE FROM b;"]
try:
    ops.execute_sql_flush(sql_list)
except TypeError as e:
    print("FAIL: TypeError on single-arg call:", e)
    sys.exit(1)
print("executed:", conn.executed)
if conn.executed != sql_list:
    print("FAIL: statements not executed correctly")
    sys.exit(1)
print("PASS: single positional arg accepted, statements executed")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover simplifying BaseDatabaseOperations.execute_sql_flush from (using, sql_list) to (sql_list), inferring the target DB from self.connection.alias, and updating the flush management command caller.

Probes (all HOLD on gold-patched, all VIOLATED at base):
- probe_1 (Req1.1/1.3): signature has exactly one caller-supplied positional; single-arg call executes without TypeError and runs all statements. PATCHED=HOLDS, BASE=VIOLATED (base signature is ['using','sql_list']). POSITIVE CONTROL.
- probe_2 (Req1.2/2.1/2.2): transaction.atomic is called with using=self.connection.alias (distinct sentinel alias) and savepoint=self.connection.features.can_rollback_ddl (distinct sentinel). PATCHED=HOLDS, BASE=VIOLATED.
- probe_3 (Req1.4): the OLD two-arg form execute_sql_flush(db, sql_list) must raise TypeError. PATCHED=HOLDS (raises), BASE=VIOLATED (two-arg accepted).
- probe_4 (Req2.3): each statement (incl. a duplicate) executed exactly once, in order, via a single connection cursor. PATCHED=HOLDS, BASE=VIOLATED.
- probe_5 (Req3.1/3.4): flush management command calls execute_sql_flush with a single sql-list arg, no database identifier. PATCHED=HOLDS, BASE=VIOLATED (base passes 'database, sql_list').

Weak candidate (weak.diff): correct body (using=self.connection.alias) but signature kept a trailing optional `using=None` param, so the removed identifier is still ACCEPTED. REJECTED by the suite: probe_1 (two positionals allowed) and probe_3 (two-arg form silently accepted — violates Req1.4). probe_2/4/5 hold under it. This demonstrates the suite discriminates the lazy 'keep-backward-compat' fix that requirement 1.4 forbids.

All 5 probes hold on patched; positive control discriminates base vs patched; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a pure signature simplification: execute_sql_flush(self, using, sql_list) -> (self, sql_list), deriving using from self.connection.alias. Requirements pin exactly this changed observable boundary (signature + alias-inferred transaction target) plus preserved transactional/ordering/caller behavior (Req2.3/2.4, Req3.2/3.3) which the unchanged inner cursor loop and flush command retain. No requirement mandates absent behavior, forbids present behavior, invents behavior, or pins a narrow slice. Modeling boundary is correct and biconditional against base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to BaseDatabaseOperations.execute_sql_flush and the flush management command, and translates the signature simplification into behavioral requirements. All key facts (old vs new signature, self.connection.alias inference, the two-arg caller form execute_sql_flush(connection.alias, sql_list)) are already public in the problem_statement. Preserved-behavior details cited (transaction.atomic, savepoint via self.connection.features.can_rollback_ddl, per-cursor statement execution in order) are pre-existing source code being preserved, not fix-invented identifiers and not test-derived. No test file paths (tests/backends/base/test_operations.py, tests/backends/tests.py), no test/class names (SqlFlushTests, LongNameTest, test_execute_sql_flush_statements, test_sequence_name_length_limits_flush), no parametrization ids, and no quoted test/gold code appear. Req 2.4 ('affected tables SHALL contain no rows') is a behavioral description of flushing, not a mirror of the test's assertIs(...exists(), False) enumeration. Naming the modules/functions is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
