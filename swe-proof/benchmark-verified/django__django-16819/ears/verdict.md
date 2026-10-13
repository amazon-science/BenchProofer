# P2 adversarial audit — django__django-16819

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
# Positive control + Req1.2: optimizer collapses AddIndex + matching RemoveIndex to empty.
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import AddIndex, RemoveIndex
from django.db.models import Index

ops = [AddIndex("Foo", Index(fields=["a"], name="idx_foo")),
       RemoveIndex("Foo", "idx_foo")]
result = MigrationOptimizer().optimize(ops, "app")
print("optimized result:", result)
sys.exit(0 if result == [] else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1 & Req1.3: AddIndex.reduce against matching RemoveIndex returns [] (exact name match).
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.operations.models import AddIndex, RemoveIndex
from django.db.models import Index

add = AddIndex("Foo", Index(fields=["a"], name="idx_foo"))
rem = RemoveIndex("Foo", "idx_foo")
r = add.reduce(rem, "app")
print("reduce(matching) ->", r)
sys.exit(0 if r == [] else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.3 & Req2 case-sensitivity: different name (incl. case difference) must NOT collapse to [].
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.operations.models import AddIndex, RemoveIndex
from django.db.models import Index

# different name
add = AddIndex("Foo", Index(fields=["a"], name="idx_foo"))
rem_diff = RemoveIndex("Foo", "other_idx")
r1 = add.reduce(rem_diff, "app")
print("reduce(diff name) ->", r1)

# case-mismatch: must be exact case-sensitive equality, so should NOT return []
rem_case = RemoveIndex("Foo", "IDX_FOO")
r2 = add.reduce(rem_case, "app")
print("reduce(case mismatch) ->", r2)

ok = (r1 != []) and (r2 != [])
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2.2 & Req2.3: following op not a RemoveIndex -> defer to base Operation.reduce,
# returning exactly what the base yields (False for non-elidable ops).
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.operations.base import Operation
from django.db.migrations.operations.models import AddIndex, DeleteModel
from django.db.models import Index

add = AddIndex("Foo", Index(fields=["a"], name="idx_foo"))
other = DeleteModel("Bar")  # not a RemoveIndex, not elidable
got = add.reduce(other, "app")
expected = Operation.reduce(add, other, "app")
print("AddIndex.reduce(non-RemoveIndex) ->", got, "| base ->", expected)
sys.exit(0 if got == expected else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3 regression: preserve CreateModel+DeleteModel collapse, AddField-into-CreateModel,
# single-op unchanged. These must remain unaffected by the AddIndex change.
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import CreateModel, DeleteModel, AddIndex
from django.db.migrations.operations.fields import AddField
from django.db import models

opt = MigrationOptimizer()

# Req3.1: CreateModel + DeleteModel -> []
r1 = opt.optimize([CreateModel("Foo", [("id", models.AutoField(primary_key=True))]),
                   DeleteModel("Foo")], "app")
print("CreateModel+DeleteModel ->", r1)

# Req3.2: AddField folds into CreateModel -> single CreateModel
r2 = opt.optimize([CreateModel("Foo", [("id", models.AutoField(primary_key=True))]),
                   AddField("Foo", "age", models.IntegerField(default=0))], "app")
print("CreateModel+AddField ->", len(r2), r2)

# Req3.6: single operation unchanged
single = AddIndex("Foo", models.Index(fields=["a"], name="idx"))
r3 = opt.optimize([single], "app")
print("single ->", r3)

ok = (r1 == []) and (len(r2) == 1 and isinstance(r2[0], CreateModel)) and (r3 == [single])
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req1.2: optimizer collapses AddIndex + matching RemoveIndex to empty.
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import AddIndex, RemoveIndex
from django.db.models import Index

ops = [AddIndex("Foo", Index(fields=["a"], name="idx_foo")),
       RemoveIndex("Foo", "idx_foo")]
result = MigrationOptimizer().optimize(ops, "app")
print("optimized result:", result)
sys.exit(0 if result == [] else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: teach the migration optimizer that AddIndex followed by RemoveIndex of the same-named index collapses to []. Gold patch adds AddIndex.reduce that returns [] iff isinstance(op, RemoveIndex) and self.index.name == op.name, else super().reduce.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.2, POSITIVE CONTROL): optimizer.optimize([AddIndex idx_foo, RemoveIndex idx_foo]) == []. HOLDS patched, VIOLATED at base (base leaves both ops) => discriminates.
- probe_2 (Req1.1/1.3): AddIndex.reduce(matching RemoveIndex) == []. HOLDS patched, False at base.
- probe_3 (Req1.3/Req2.1 exact case-sensitive name match): reduce with a differently-named RemoveIndex AND a case-mismatched name ('IDX_FOO') must NOT return [] (both -> False). HOLDS patched.
- probe_4 (Req2.2/2.3): following op not a RemoveIndex (DeleteModel) defers to base Operation.reduce and returns exactly base's result (False). HOLDS patched.
- probe_5 (Req3.1/3.2/3.6 regression): CreateModel+DeleteModel->[], CreateModel+AddField folds to single CreateModel, single op unchanged. HOLDS patched.

Candidate wrong patch weak.diff: cancels on ANY following RemoveIndex regardless of name (drops the self.index.name == operation.name check). It PASSES probes 1,2,4,5 but is REJECTED by probe_3 (VIOLATED: returns [] for mismatched/case-differing names), demonstrating the suite discriminates the name-equality requirement. Thus no requirements-conforming weak fix found; suite has discriminating power.

Verdict SOUND: 5 distinct probes all hold on patched tree, positive control fails at base and holds patched, and the naive weak candidate is caught by probe_3.

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
# Positive control + Req1.2: optimizer collapses AddIndex + matching RemoveIndex to empty.
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import AddIndex, RemoveIndex
from django.db.models import Index

ops = [AddIndex("Foo", Index(fields=["a"], name="idx_foo")),
       RemoveIndex("Foo", "idx_foo")]
result = MigrationOptimizer().optimize(ops, "app")
print("optimized result:", result)
sys.exit(0 if result == [] else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: teach the migration optimizer that AddIndex followed by RemoveIndex of the same-named index collapses to []. Gold patch adds AddIndex.reduce that returns [] iff isinstance(op, RemoveIndex) and self.index.name == op.name, else super().reduce.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.2, POSITIVE CONTROL): optimizer.optimize([AddIndex idx_foo, RemoveIndex idx_foo]) == []. HOLDS patched, VIOLATED at base (base leaves both ops) => discriminates.
- probe_2 (Req1.1/1.3): AddIndex.reduce(matching RemoveIndex) == []. HOLDS patched, False at base.
- probe_3 (Req1.3/Req2.1 exact case-sensitive name match): reduce with a differently-named RemoveIndex AND a case-mismatched name ('IDX_FOO') must NOT return [] (both -> False). HOLDS patched.
- probe_4 (Req2.2/2.3): following op not a RemoveIndex (DeleteModel) defers to base Operation.reduce and returns exactly base's result (False). HOLDS patched.
- probe_5 (Req3.1/3.2/3.6 regression): CreateModel+DeleteModel->[], CreateModel+AddField folds to single CreateModel, single op unchanged. HOLDS patched.

Candidate wrong patch weak.diff: cancels on ANY following RemoveIndex regardless of name (drops the self.index.name == operation.name check). It PASSES probes 1,2,4,5 but is REJECTED by probe_3 (VIOLATED: returns [] for mismatched/case-differing names), demonstrating the suite discriminates the name-equality requirement. Thus no requirements-conforming weak fix found; suite has discriminating power.

Verdict SOUND: 5 distinct probes all hold on patched tree, positive control fails at base and holds patched, and the naive weak candidate is caught by probe_3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds exactly one method: AddIndex.reduce(op, app_label): if isinstance(op, RemoveIndex) and self.index.name == op.name: return []; else super().reduce(...). Requirements 1-2 pin precisely this changed observable behavior (empty-list cancellation on matching name/model+type, else defer to base) with correct case-sensitive-equality boundary. Requirement 3's preservation clauses are all about behavior the patch does not touch, and are trivially true since only AddIndex.reduce was added. No mandated behavior the code lacks, no forbidden behavior it has, correct modeling boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the AddIndex/RemoveIndex cancellation behavior without transmitting any hidden-test artifacts. The FAIL_TO_PASS test's concrete fixtures (model 'Pony', fields ['weight','pink'], index name 'idx_pony_weight_pink', function name test_add_remove_index) appear nowhere. No quoted test/gold code; the gold fix invents no identifiers, and the exact-string-equality comparison described is a faithful behavioral translation of self.index.name == operation.name, not a leak. Naming AddIndex/RemoveIndex/index.name/model_name and the operations/models.py path is legitimate localization. Requirement 3's enumeration of preserved optimizer behaviors overlaps the PASS_TO_PASS suite conceptually, but each item is a publicly-documented Django optimizer behavior stated as regression-preservation prose — not test ids, parametrization cases, or reconstructable test code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
