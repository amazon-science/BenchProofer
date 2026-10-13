# P2 adversarial audit — django__django-15499

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
"""Req1.1 + Req1.5 (positive control): CreateModel followed by AlterModelManagers
for the same model reduces to exactly one CreateModel."""
import sys
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import CreateModel, AlterModelManagers
from django.db import models


def managers():
    return [("objects", models.Manager()), ("things", models.Manager())]


create = CreateModel("Foo", fields=[("id", models.AutoField(primary_key=True))])
alter = AlterModelManagers("Foo", managers=managers())

opt = MigrationOptimizer()
result = opt.optimize([create, alter], "myapp")
print("result len:", len(result), "types:", [type(o).__name__ for o in result])
if len(result) == 1 and isinstance(result[0], CreateModel):
    print("HOLDS: single CreateModel")
    sys.exit(0)
print("FAIL: not reduced to single CreateModel")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 + Req1.3: the fused CreateModel carries the managers from
AlterModelManagers (fully replacing originals), and preserves name/fields/options/bases."""
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelManagers
from django.db import models

orig_managers = [("old", models.Manager())]
new_managers = [("objects", models.Manager()), ("things", models.Manager())]

create = CreateModel(
    "Foo",
    fields=[("id", models.AutoField(primary_key=True)), ("name", models.CharField(max_length=10))],
    options={"verbose_name": "foo"},
    bases=(models.Model,),
    managers=orig_managers,
)
alter = AlterModelManagers("Foo", managers=new_managers)

result = create.reduce(alter, "myapp")
assert len(result) == 1, result
new = result[0]

new_mgr_names = [n for n, m in new.managers]
print("managers:", new_mgr_names)
print("name:", new.name, "fields:", [f for f, _ in new.fields])
print("options:", new.options, "bases:", new.bases)

ok = (
    new_mgr_names == ["objects", "things"]
    and new.name == "Foo"
    and [f for f, _ in new.fields] == ["id", "name"]
    and new.options == {"verbose_name": "foo"}
    and new.bases == (models.Model,)
)
if ok:
    print("HOLDS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4: model creation with NO managers followed by manager reconfiguration
yields single CreateModel carrying exactly the reconfigured managers, in order."""
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelManagers
from django.db import models

create = CreateModel("Foo", fields=[("id", models.AutoField(primary_key=True))])
new_managers = [("a", models.Manager()), ("b", models.Manager()), ("c", models.Manager())]
alter = AlterModelManagers("Foo", managers=new_managers)

result = create.reduce(alter, "myapp")
assert len(result) == 1
names = [n for n, m in result[0].managers]
print("original managers:", create.managers)
print("fused managers order:", names)
if names == ["a", "b", "c"]:
    print("HOLDS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3: fuse only when model names match (case-insensitively);
different model names must NOT collapse."""
import sys
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import CreateModel, AlterModelManagers
from django.db import models

# case-insensitive match SHOULD fuse
create = CreateModel("Foo", fields=[("id", models.AutoField(primary_key=True))])
alter_ci = AlterModelManagers("foo", managers=[("objects", models.Manager())])
r_ci = create.reduce(alter_ci, "myapp")
print("case-insensitive same-model reduce:", r_ci and len(r_ci), [type(o).__name__ for o in (r_ci or [])])
ci_ok = bool(r_ci) and len(r_ci) == 1 and type(r_ci[0]).__name__ == "CreateModel"

# different model -> must NOT collapse into a single CreateModel.
# Note: reduce() returning True/bool means "independent ops, can optimize
# through" (NOT a merge); the merge test is whether optimize() keeps both ops
# and, critically, that reduce() never returns a merged CreateModel list here.
alter_diff = AlterModelManagers("Bar", managers=[("objects", models.Manager())])
r_diff = create.reduce(alter_diff, "myapp")
print("different-model reduce return:", r_diff)
opt = MigrationOptimizer()
seq = opt.optimize([create, alter_diff], "myapp")
print("optimize seq types:", [type(o).__name__ for o in seq])
# reduce must NOT return a list that fuses the pair into a CreateModel
reduce_not_merged = not (isinstance(r_diff, list) and len(r_diff) == 1 and isinstance(r_diff[0], CreateModel))
diff_ok = (
    reduce_not_merged
    and len(seq) == 2
    and any(isinstance(o, CreateModel) for o in seq)
    and any(isinstance(o, AlterModelManagers) for o in seq)
)

if ci_ok and diff_ok:
    print("HOLDS")
    sys.exit(0)
print("FAIL ci_ok=%s diff_ok=%s" % (ci_ok, diff_ok))
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3 (regression): existing CreateModel reductions still work:
AlterModelOptions, DeleteModel, RenameModel, field add."""
import sys
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import (
    CreateModel, AlterModelOptions, DeleteModel, RenameModel,
)
from django.db.migrations.operations.fields import AddField
from django.db import models

opt = MigrationOptimizer()
failures = []

# 3.1 AlterModelOptions: fuse, dropping omitted keys
create = CreateModel("Foo", fields=[("id", models.AutoField(primary_key=True))],
                     options={"verbose_name": "x", "ordering": ["id"]})
alter_opts = AlterModelOptions("Foo", options={"verbose_name": "y"})
r = opt.optimize([create, alter_opts], "app")
print("opts:", len(r), r[0].options if r else None)
if not (len(r) == 1 and r[0].options == {"verbose_name": "y"}):
    failures.append("AlterModelOptions")

# 3.4 DeleteModel: reduce to nothing
create2 = CreateModel("Bar", fields=[("id", models.AutoField(primary_key=True))])
delete = DeleteModel("Bar")
r = opt.optimize([create2, delete], "app")
print("delete:", len(r))
if len(r) != 0:
    failures.append("DeleteModel")

# 3.5 RenameModel: single CreateModel under new name
create3 = CreateModel("Baz", fields=[("id", models.AutoField(primary_key=True))],
                      managers=[("objects", models.Manager())])
rename = RenameModel("Baz", "Qux")
r = opt.optimize([create3, rename], "app")
print("rename:", len(r), r[0].name if r else None)
if not (len(r) == 1 and r[0].name == "Qux" and [n for n, _ in r[0].managers] == ["objects"]):
    failures.append("RenameModel")

# 3.6 field add folded in
create4 = CreateModel("Zap", fields=[("id", models.AutoField(primary_key=True))])
addf = AddField("Zap", "name", models.CharField(max_length=5))
r = opt.optimize([create4, addf], "app")
print("addfield:", len(r), [f for f, _ in r[0].fields] if r else None)
if not (len(r) == 1 and "name" in [f for f, _ in r[0].fields]):
    failures.append("AddField")

if not failures:
    print("HOLDS")
    sys.exit(0)
print("FAIL:", failures)
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 + Req1.5 (positive control): CreateModel followed by AlterModelManagers
for the same model reduces to exactly one CreateModel."""
import sys
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import CreateModel, AlterModelManagers
from django.db import models


def managers():
    return [("objects", models.Manager()), ("things", models.Manager())]


create = CreateModel("Foo", fields=[("id", models.AutoField(primary_key=True))])
alter = AlterModelManagers("Foo", managers=managers())

opt = MigrationOptimizer()
result = opt.optimize([create, alter], "myapp")
print("result len:", len(result), "types:", [type(o).__name__ for o in result])
if len(result) == 1 and isinstance(result[0], CreateModel):
    print("HOLDS: single CreateModel")
    sys.exit(0)
print("FAIL: not reduced to single CreateModel")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle adds the CreateModel+AlterModelManagers fusion in CreateModel.reduce. 5 probes encode the criteria:
- probe_1 (Req1.1/1.5, POSITIVE CONTROL): CreateModel followed by AlterModelManagers for same model reduces via optimizer to a single CreateModel. HOLDS patched, FAILS at base (base returns 2 ops) -> discriminating power confirmed.
- probe_2 (Req1.2/1.3): fused CreateModel carries managers from the AlterModelManagers (fully replacing originals) and preserves name/fields/options/bases. HOLDS patched.
- probe_3 (Req1.4): no-manager CreateModel + reconfiguration yields exactly the reconfigured managers in order [a,b,c]. HOLDS patched.
- probe_4 (Req2.1/2.2/2.3): case-insensitive same-model fuses; a different target model is NOT collapsed (optimize keeps both ops; reduce does not return a merged CreateModel). HOLDS patched. (Initial version mis-read reduce()'s bool 'independent-ops' return as a merge; corrected to check optimize() output + that reduce returns no merged list.)
- probe_5 (Req3.1/3.4/3.5/3.6 regression): AlterModelOptions (drops omitted keys), DeleteModel->0 ops, RenameModel->renamed CreateModel preserving managers, AddField folded in. HOLDS patched.

CANDIDATE PATCH 'keep_original_managers' (weak.diff): the naive/lazy fix that adds the fusion branch but sets managers=self.managers instead of operation.managers. Applies cleanly at base. Probes 1,4,5 HOLD under it, but probes 2 and 3 REJECT it (fused managers = ['old'] / [] instead of the reconfigured managers) — demonstrating the suite discriminates a requirements-violating implementation of Req1.2/1.4. This wrong fix would also fail the hidden test asserting the new managers are carried.

All 5 probes HOLD on the gold-patched tree; positive control discriminates base vs patched; the wrong-fix candidate is rejected by the suite. Verdict SOUND.

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
"""Req1.1 + Req1.5 (positive control): CreateModel followed by AlterModelManagers
for the same model reduces to exactly one CreateModel."""
import sys
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.operations.models import CreateModel, AlterModelManagers
from django.db import models


def managers():
    return [("objects", models.Manager()), ("things", models.Manager())]


create = CreateModel("Foo", fields=[("id", models.AutoField(primary_key=True))])
alter = AlterModelManagers("Foo", managers=managers())

opt = MigrationOptimizer()
result = opt.optimize([create, alter], "myapp")
print("result len:", len(result), "types:", [type(o).__name__ for o in result])
if len(result) == 1 and isinstance(result[0], CreateModel):
    print("HOLDS: single CreateModel")
    sys.exit(0)
print("FAIL: not reduced to single CreateModel")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle adds the CreateModel+AlterModelManagers fusion in CreateModel.reduce. 5 probes encode the criteria:
- probe_1 (Req1.1/1.5, POSITIVE CONTROL): CreateModel followed by AlterModelManagers for same model reduces via optimizer to a single CreateModel. HOLDS patched, FAILS at base (base returns 2 ops) -> discriminating power confirmed.
- probe_2 (Req1.2/1.3): fused CreateModel carries managers from the AlterModelManagers (fully replacing originals) and preserves name/fields/options/bases. HOLDS patched.
- probe_3 (Req1.4): no-manager CreateModel + reconfiguration yields exactly the reconfigured managers in order [a,b,c]. HOLDS patched.
- probe_4 (Req2.1/2.2/2.3): case-insensitive same-model fuses; a different target model is NOT collapsed (optimize keeps both ops; reduce does not return a merged CreateModel). HOLDS patched. (Initial version mis-read reduce()'s bool 'independent-ops' return as a merge; corrected to check optimize() output + that reduce returns no merged list.)
- probe_5 (Req3.1/3.4/3.5/3.6 regression): AlterModelOptions (drops omitted keys), DeleteModel->0 ops, RenameModel->renamed CreateModel preserving managers, AddField folded in. HOLDS patched.

CANDIDATE PATCH 'keep_original_managers' (weak.diff): the naive/lazy fix that adds the fusion branch but sets managers=self.managers instead of operation.managers. Applies cleanly at base. Probes 1,4,5 HOLD under it, but probes 2 and 3 REJECT it (fused managers = ['old'] / [] instead of the reconfigured managers) — demonstrating the suite discriminates a requirements-violating implementation of Req1.2/1.4. This wrong fix would also fail the hidden test asserting the new managers are carried.

All 5 probes HOLD on the gold-patched tree; positive control discriminates base vs patched; the wrong-fix candidate is rejected by the suite. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements correctly model the full changed behavior including manager replacement semantics (operation.managers fully replaces self.managers), same-model case-insensitive gating, and preservation of the other four CreateModel components. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior, and the modeling boundary matches the changed observable (optimizer output for the CreateModel+AlterModelManagers pair).

Counterexample / evidence:

```
None found. Patch is a pure additive elif branch in CreateModel.reduce for isinstance(operation, AlterModelManagers) and self.name_lower == operation.name_lower, returning [CreateModel(self.name, fields=self.fields, options=self.options, bases=self.bases, managers=operation.managers)]. It leaves all pre-existing reduction branches (AlterModelOptions, AlterTogether, order_with_respect_to, DeleteModel, RenameModel, field ops) untouched, so Req 3's no-regression claims hold trivially.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the CreateModel+AlterModelManagers fusion at a behavioral level, consistent with the public problem_statement ('CreateModel + AlterModelManagers can become just CreateModel'). No hidden-test artifacts are transmitted: no test file path (tests/migrations/test_optimizer.py), no test function/class names (test_create_alter_model_managers, OptimizerTests), no parametrization ids, and none of the test's invented identifiers ('Foo', 'objects', 'things'). Module/function localization (django/db/migrations/operations/models.py, CreateModel.reduce, name_lower, the case-insensitive match) is legitimate and drawn from public source, not the gold edit — the gold branch invents no new identifiers. Req 3's enumeration of preserved reductions (options, unique/index_together, order_with_respect_to, delete, rename, field-level) mirrors the reduce() case chain that already exists in the public source, not the hidden test suite; it is behavioral preservation, not test transcription. Req 1.4 ('several managers, in order given') is a general replacement-semantics translation, not a copy of the test's specific two-manager literals. This is translating what the tests check into behavioral requirements — the intended purpose — rather than transmitting the tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
