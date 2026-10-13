# P2 adversarial audit — django__django-16595

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1 crit1 + positive control: AlterField.reduce against a following same-field
# AlterField returns [operation] (the later one).
import sys
from django.db import models
from django.db.migrations.operations.fields import AlterField

a1 = AlterField("Model", "field", models.IntegerField(default=1))
a2 = AlterField("Model", "field", models.IntegerField(default=2, null=True))
res = a1.reduce(a2, "app")
print("reduce result:", res)
ok = isinstance(res, list) and len(res) == 1 and res[0] is a2
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1 crit2+3+4: optimizer collapses a run of same-field AlterFields to a
# single AlterField carrying the LAST field definition.
import sys
from django.db import models
from django.db.migrations.operations.fields import AlterField
from django.db.migrations.optimizer import MigrationOptimizer

ops = [
    AlterField("Model", "field", models.IntegerField()),
    AlterField("Model", "field", models.CharField(max_length=100, null=True)),
    AlterField("Model", "field", models.TextField(help_text="last", default="x")),
]
out = MigrationOptimizer().optimize(ops, "app")
print("in:", len(ops), "out:", len(out), [type(o).__name__ for o in out])
ok = len(out) == 1 and isinstance(out[0], AlterField)
if ok:
    fld = out[0].field
    print("surviving field:", type(fld).__name__, "help_text=", getattr(fld, "help_text", None))
    ok = isinstance(fld, models.TextField) and fld.help_text == "last"
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2 crit2+3: case-insensitive same-field match collapses; different field name
# does NOT collapse.
import sys
from django.db import models
from django.db.migrations.operations.fields import AlterField

# case-insensitive: should collapse
a1 = AlterField("Model", "Field", models.IntegerField())
a2 = AlterField("model", "field", models.CharField(max_length=5))
res_ci = a1.reduce(a2, "app")
print("case-insensitive reduce:", res_ci)
ok_ci = isinstance(res_ci, list) and len(res_ci) == 1 and res_ci[0] is a2

# different field name: should NOT collapse into [operation]
b1 = AlterField("Model", "field", models.IntegerField())
b2 = AlterField("Model", "other", models.CharField(max_length=5))
res_diff = b1.reduce(b2, "app")
print("diff-field reduce:", res_diff)
# must not be a single-element list that is just b2
bad = isinstance(res_diff, list) and res_diff == [b2]
ok = ok_ci and not bad
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3: AlterField-then-RemoveField still collapses to [RemoveField].
import sys
from django.db import models
from django.db.migrations.operations.fields import AlterField, RemoveField

a = AlterField("Model", "field", models.IntegerField())
r = RemoveField("Model", "field")
res = a.reduce(r, "app")
print("reduce:", res)
ok = isinstance(res, list) and len(res) == 1 and res[0] is r
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req4: AlterField-then-RenameField => [RenameField, AlterField(new_name, field)].
import sys
from django.db import models
from django.db.migrations.operations.fields import AlterField, RenameField

a = AlterField("Model", "field", models.IntegerField(null=True))
rn = RenameField("Model", "field", "field2")
res = a.reduce(rn, "app")
print("reduce:", res)
ok = (isinstance(res, list) and len(res) == 2
      and isinstance(res[0], RenameField) and res[0] is rn
      and isinstance(res[1], AlterField)
      and res[1].name == "field2"
      and res[1].field.null is True)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req5: AddField+AlterField collapses into a single AddField carrying altered field;
# and unrelated ops (Req6) commute / single op unchanged.
import sys
from django.db import models
from django.db.migrations.operations.fields import AddField, AlterField
from django.db.migrations.optimizer import MigrationOptimizer

ops = [
    AddField("Model", "field", models.IntegerField()),
    AlterField("Model", "field", models.CharField(max_length=99, null=True)),
]
out = MigrationOptimizer().optimize(ops, "app")
print("out:", [type(o).__name__ for o in out])
ok = len(out) == 1 and isinstance(out[0], AddField)
if ok:
    ok = isinstance(out[0].field, models.CharField) and out[0].field.max_length == 99
# single op unchanged (Req6 crit2)
single = [AlterField("Model", "field", models.IntegerField())]
out2 = MigrationOptimizer().optimize(single, "app")
print("single out len:", len(out2))
ok = ok and len(out2) == 1
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
# Req1 crit2+3+4: optimizer collapses a run of same-field AlterFields to a
# single AlterField carrying the LAST field definition.
import sys
from django.db import models
from django.db.migrations.operations.fields import AlterField
from django.db.migrations.optimizer import MigrationOptimizer

ops = [
    AlterField("Model", "field", models.IntegerField()),
    AlterField("Model", "field", models.CharField(max_length=100, null=True)),
    AlterField("Model", "field", models.TextField(help_text="last", default="x")),
]
out = MigrationOptimizer().optimize(ops, "app")
print("in:", len(ops), "out:", len(out), [type(o).__name__ for o in out])
ok = len(out) == 1 and isinstance(out[0], AlterField)
if ok:
    fld = out[0].field
    print("surviving field:", type(fld).__name__, "help_text=", getattr(fld, "help_text", None))
    ok = isinstance(fld, models.TextField) and fld.help_text == "last"
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; positive controls (probe_1 Req1.1, probe_2 Req1.2/3/4 optimizer-collapse-to-last-def) both FAIL at base (base leaves run of 3 AlterFields un-reduced) and HOLD patched => discriminating power confirmed. Coverage: probe_1 Req1.1 (reduce returns [operation]); probe_2 Req1.2/1.3/1.4 (optimizer collapses same-field run to single AlterField with LAST field def, TextField help_text='last'); probe_3 Req2.2/2.3 (case-insensitive match collapses; different field name does NOT collapse); probe_4 Req3 (AlterField->RemoveField => [RemoveField]); probe_5 Req4 (AlterField->RenameField => [RenameField, AlterField(new_name, receiver field)]); probe_6 Req5.1 (AddField+AlterField -> single AddField w/ altered field) + Req6.2 (single op unchanged). Candidate wrong-fix weak.diff collapses ANY following AlterField ignoring is_same_field_operation (violates Req2); probe_3 REJECTS it (exit 1: different-field AlterField wrongly collapsed) => suite discriminates wrong implementations. Gold patch adds AlterField to the isinstance tuple guarded by is_same_field_operation, exactly matching all requirements.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
# Req1 crit2+3+4: optimizer collapses a run of same-field AlterFields to a
# single AlterField carrying the LAST field definition.
import sys
from django.db import models
from django.db.migrations.operations.fields import AlterField
from django.db.migrations.optimizer import MigrationOptimizer

ops = [
    AlterField("Model", "field", models.IntegerField()),
    AlterField("Model", "field", models.CharField(max_length=100, null=True)),
    AlterField("Model", "field", models.TextField(help_text="last", default="x")),
]
out = MigrationOptimizer().optimize(ops, "app")
print("in:", len(ops), "out:", len(out), [type(o).__name__ for o in out])
ok = len(out) == 1 and isinstance(out[0], AlterField)
if ok:
    fld = out[0].field
    print("surviving field:", type(fld).__name__, "help_text=", getattr(fld, "help_text", None))
    ok = isinstance(fld, models.TextField) and fld.help_text == "last"
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; positive controls (probe_1 Req1.1, probe_2 Req1.2/3/4 optimizer-collapse-to-last-def) both FAIL at base (base leaves run of 3 AlterFields un-reduced) and HOLD patched => discriminating power confirmed. Coverage: probe_1 Req1.1 (reduce returns [operation]); probe_2 Req1.2/1.3/1.4 (optimizer collapses same-field run to single AlterField with LAST field def, TextField help_text='last'); probe_3 Req2.2/2.3 (case-insensitive match collapses; different field name does NOT collapse); probe_4 Req3 (AlterField->RemoveField => [RemoveField]); probe_5 Req4 (AlterField->RenameField => [RenameField, AlterField(new_name, receiver field)]); probe_6 Req5.1 (AddField+AlterField -> single AddField w/ altered field) + Req6.2 (single op unchanged). Candidate wrong-fix weak.diff collapses ANY following AlterField ignoring is_same_field_operation (violates Req2); probe_3 REJECTS it (exit 1: different-field AlterField wrongly collapsed) => suite discriminates wrong implementations. Gold patch adds AlterField to the isinstance tuple guarded by is_same_field_operation, exactly matching all requirements.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: `isinstance(operation, RemoveField)` → `isinstance(operation, (AlterField, RemoveField))` guarded by is_same_field_operation, returning [operation]. Requirement 1.1 precisely mirrors this (return list containing only the following operation). Req 2 correctly grounds same-field matching in FieldOperation.is_same_field_operation's case-insensitive model+field comparison. All preservation requirements (3,4,5,6) verified unchanged on patched tree. base_commit diverges only on the new Alter+AlterField collapse, as expected.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes AlterField.reduce behavior in terms fully derivable from the public problem_statement (which itself contains the AddField/AlterField example with max_length/null/help_text/default and the proposed isinstance(AlterField)+is_same_field_operation fix). None of the hidden-test-only identifiers appear: test name test_alter_alter_field, the renamed helper _test_alter_alter, the test model 'Foo', field 'name', or models.IntegerField are absent. Naming AlterField.reduce, is_same_field_operation, and the sibling operations (AlterModelTable/AlterUniqueTogether/AlterIndexTogether/AlterOrderWithRespectTo) is legitimate localization discoverable from the source, not from the hidden tests. The gold edit (adding AlterField to the isinstance tuple) is transmitted as behavior, not quoted code. Attribute enumerations (max_length, null, help_text, default) come straight from the public problem_statement example, not the test (which uses only help_text on an IntegerField).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
