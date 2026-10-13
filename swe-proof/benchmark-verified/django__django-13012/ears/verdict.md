# P2 adversarial audit — django__django-13012

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
"""Req2: wrapped constant contributes NO grouping columns (positive control).
HOLDS on patched (delegates to Value.get_group_by_cols -> []),
FAILS at base (inherits BaseExpression -> returns [wrapper])."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes', 'django.contrib.auth'])
    django.setup()
from django.db.models import Value, IntegerField
from django.db.models.expressions import ExpressionWrapper

w = ExpressionWrapper(Value(42), output_field=IntegerField())
cols = w.get_group_by_cols(alias=None)
print("cols =", cols)
ok = (cols == []) and (w not in cols)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1/Req1.4: wrapper returns EXACTLY the wrapped expr's grouping cols,
not itself. Uses a probe expression that reports a sentinel list."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes', 'django.contrib.auth'])
    django.setup()
from django.db.models import IntegerField
from django.db.models.expressions import ExpressionWrapper, Expression

sentinel = object()
class Probe(Expression):
    def get_group_by_cols(self, alias=None):
        return [sentinel]

inner = Probe()
w = ExpressionWrapper(inner, output_field=IntegerField())
cols = w.get_group_by_cols(alias=None)
print("cols =", cols)
ok = (cols == [sentinel]) and (w not in cols) and (inner not in cols)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.2: wrapper passes the SAME alias value to the wrapped expr."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes', 'django.contrib.auth'])
    django.setup()
from django.db.models import IntegerField
from django.db.models.expressions import ExpressionWrapper, Expression

seen = []
class Probe(Expression):
    def get_group_by_cols(self, alias=None):
        seen.append(alias)
        return []

inner = Probe()
w = ExpressionWrapper(inner, output_field=IntegerField())
w.get_group_by_cols(alias="MYALIAS")
print("seen =", seen)
ok = (seen == ["MYALIAS"])
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3: wrapped non-constant, non-aggregate expr -> list containing exactly
that wrapped expression object (F() resolves to a Col reporting [self])."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes', 'django.contrib.auth'])
    django.setup()
from django.db.models import IntegerField
from django.db.models.expressions import ExpressionWrapper, Expression

# A non-constant, non-aggregate leaf that reports itself (like a Col/RawSQL).
class Leaf(Expression):
    contains_aggregate = False
    def get_group_by_cols(self, alias=None):
        return [self]

inner = Leaf()
w = ExpressionWrapper(inner, output_field=IntegerField())
cols = w.get_group_by_cols(alias=None)
print("cols =", cols, "inner is elem0:", cols and cols[0] is inner)
ok = (len(cols) == 1) and (cols[0] is inner)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4: preserve existing behavior — single source expression is the wrapped
expr; as_sql delegates to wrapped expr; output_field/expression retained."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes', 'django.contrib.auth'])
    django.setup()
from django.db.models import Value, IntegerField
from django.db.models.expressions import ExpressionWrapper

of = IntegerField()
inner = Value(7)
w = ExpressionWrapper(inner, output_field=of)

# Req4.1 single source expression
srcs = w.get_source_expressions()
r1 = (srcs == [inner])
# Req4.3 retained expression + output_field
r3 = (w.expression is inner) and (w.output_field is of)
# Req4.2 as_sql delegates to wrapped expression
calls = []
class SqlProbe(Value):
    def as_sql(self, compiler, connection):
        calls.append("inner")
        return "INNERSQL", []
inner2 = SqlProbe(9)
w2 = ExpressionWrapper(inner2, output_field=IntegerField())
sql, params = w2.as_sql(compiler=None, connection=None)
r2 = (calls == ["inner"]) and (sql == "INNERSQL")

print("r1", r1, "r2", r2, "r3", r3)
ok = r1 and r2 and r3
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req2: wrapped constant contributes NO grouping columns (positive control).
HOLDS on patched (delegates to Value.get_group_by_cols -> []),
FAILS at base (inherits BaseExpression -> returns [wrapper])."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes', 'django.contrib.auth'])
    django.setup()
from django.db.models import Value, IntegerField
from django.db.models.expressions import ExpressionWrapper

w = ExpressionWrapper(Value(42), output_field=IntegerField())
cols = w.get_group_by_cols(alias=None)
print("cols =", cols)
ok = (cols == []) and (w not in cols)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

ExpressionWrapper.get_group_by_cols must delegate to self.expression.get_group_by_cols(alias=alias). Base (unpatched) inherits BaseExpression.get_group_by_cols -> returns [self] (the wrapper) for non-aggregate, wrongly adding a wrapped constant to GROUP BY.

Probes (all HOLD on patched):
- probe_1 (Req2.1/2.2, POSITIVE CONTROL): wrapped Value(42) -> cols == []. HOLDS patched, FAILS base (base -> [ExpressionWrapper]). Discriminates.
- probe_2 (Req1.1/1.4): wrapper returns exactly the wrapped expr's sentinel list, not itself. FAILS base.
- probe_3 (Req1.2): alias 'MYALIAS' is passed through to the wrapped expr. FAILS base (base never calls inner -> seen==[]).
- probe_4 (Req3.1/3.2): wrapped non-constant leaf reporting [self] -> wrapper returns exactly [inner]. FAILS base (base returns [wrapper]).
- probe_5 (Req4.1/4.2/4.3): single source expr == [inner]; as_sql delegates to inner; expression/output_field retained. Holds on both trees (regression-preservation criterion).

Wrong-fix candidates, both REJECTED by the suite:
- weak_empty (return []): rejected by probe_2, probe_3, probe_4 — kills grouping cols for non-constant wrapped exprs, breaking Req3.
- weak_noalias (return self.expression.get_group_by_cols() dropping alias): rejected by probe_3 — passes None instead of the caller's alias, violating Req1.2.

Suite discriminates wrong implementations and the gold patch satisfies all criteria.

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
"""Req2: wrapped constant contributes NO grouping columns (positive control).
HOLDS on patched (delegates to Value.get_group_by_cols -> []),
FAILS at base (inherits BaseExpression -> returns [wrapper])."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes', 'django.contrib.auth'])
    django.setup()
from django.db.models import Value, IntegerField
from django.db.models.expressions import ExpressionWrapper

w = ExpressionWrapper(Value(42), output_field=IntegerField())
cols = w.get_group_by_cols(alias=None)
print("cols =", cols)
ok = (cols == []) and (w not in cols)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

ExpressionWrapper.get_group_by_cols must delegate to self.expression.get_group_by_cols(alias=alias). Base (unpatched) inherits BaseExpression.get_group_by_cols -> returns [self] (the wrapper) for non-aggregate, wrongly adding a wrapped constant to GROUP BY.

Probes (all HOLD on patched):
- probe_1 (Req2.1/2.2, POSITIVE CONTROL): wrapped Value(42) -> cols == []. HOLDS patched, FAILS base (base -> [ExpressionWrapper]). Discriminates.
- probe_2 (Req1.1/1.4): wrapper returns exactly the wrapped expr's sentinel list, not itself. FAILS base.
- probe_3 (Req1.2): alias 'MYALIAS' is passed through to the wrapped expr. FAILS base (base never calls inner -> seen==[]).
- probe_4 (Req3.1/3.2): wrapped non-constant leaf reporting [self] -> wrapper returns exactly [inner]. FAILS base (base returns [wrapper]).
- probe_5 (Req4.1/4.2/4.3): single source expr == [inner]; as_sql delegates to inner; expression/output_field retained. Holds on both trees (regression-preservation criterion).

Wrong-fix candidates, both REJECTED by the suite:
- weak_empty (return []): rejected by probe_2, probe_3, probe_4 — kills grouping cols for non-constant wrapped exprs, breaking Req3.
- weak_noalias (return self.expression.get_group_by_cols() dropping alias): rejected by probe_3 — passes None instead of the caller's alias, violating Req1.2.

Suite discriminates wrong implementations and the gold patch satisfies all criteria.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a 3-line addition of ExpressionWrapper.get_group_by_cols(alias=None) delegating to self.expression.get_group_by_cols(alias=alias). Requirements 1-4 pin exactly this observable behavior at the changed boundary: delegation of grouping-column resolution (empty for constants, [expr] for non-constants), alias pass-through, and preservation of source-expression/as_sql/output_field forwarding. No mandated behavior the code lacks, no forbidden behavior it has, correct boundary (the changed get_group_by_cols, not a narrow slice).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe ExpressionWrapper.get_group_by_cols delegating to the wrapped expression. All concrete anchors (ExpressionWrapper, Value/constant, GROUP BY, the wrapped-vs-unwrapped divergence, invalid-Postgres-SQL) are already in the PUBLIC problem_statement. The `alias`/`alias=None` detail is the genuine base-class method signature being overridden in the gold edit — legitimate localization, not test transmission. No test names/paths (ExpressionWrapperTests, test_empty_group_by, test_non_empty_group_by, tests/expressions/tests.py), no quoted test/gold code beyond the method being named, no parametrization ids, no fix-invented identifiers. Requirement 3's 'non-constant expression returns list containing exactly the wrapped expression' is a behavioral translation of test_non_empty_group_by's assertion, and crucially the test's actual fixture Lower(Value('f')) is NOT named — the doc stays generic. The empty/non-empty two-case structure tracks the real base-class semantics (constant->[] vs non-constant->[self]) rather than reconstructing the parametrization. Behavior described, tests not leaked.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
