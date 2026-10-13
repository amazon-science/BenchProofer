# P2 adversarial audit — django__django-13786

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_clear_empty.py`, `probe_2_clear_partial.py`, `probe_3_keep_nonmanaged.py`, `probe_4_identity.py`, `probe_5_overlay.py`, `probe_6_other_ops.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_clear_empty.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak patch (clear managed keys only when change options is empty) produces folded options {'verbose_name':'New','ordering':['name']} for CreateModel(ordering=['name'],verbose_name='Old') + AlterModelOptions(verbose_name='New'); 'ordering' should be cleared per Req1.4. Probe_2 REJECTS it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_clear_empty.py` → holds on the patched tree (good)

```python
# Req1.4/1.5 (POSITIVE CONTROL): a managed option key set at creation but absent
# from an empty AlterModelOptions must be CLEARED in the folded result.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions

create = CreateModel("Pony", fields=[], options={"verbose_name": "Pony", "permissions": [("x", "X")]})
alter = AlterModelOptions("Pony", options={})
result = create.reduce(alter, "app")

assert isinstance(result, list) and len(result) == 1, f"expected single op, got {result!r}"
op = result[0]
assert isinstance(op, CreateModel), f"expected CreateModel, got {type(op)}"
print("folded options:", op.options)
# verbose_name and permissions are managed keys; must be cleared
for k in ("verbose_name", "permissions"):
    if k in op.options:
        print(f"FAIL: managed key {k!r} was not cleared")
        sys.exit(1)
print("PASS: all creation-supplied managed options cleared")
sys.exit(0)
```

Attack 2 — `probe_2_clear_partial.py` → holds on the patched tree (good)

```python
# Req1.4: a managed key set at creation but NOT in change options is removed,
# while a managed key present in change options is retained with change's value.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions

create = CreateModel("Pony", fields=[], options={"verbose_name": "Old", "ordering": ["name"]})
alter = AlterModelOptions("Pony", options={"verbose_name": "New"})
op = create.reduce(alter, "app")[0]
print("folded options:", op.options)

if op.options.get("verbose_name") != "New":
    print("FAIL: verbose_name not overridden to change value"); sys.exit(1)
if "ordering" in op.options:
    print("FAIL: managed key 'ordering' (absent from change) not cleared"); sys.exit(1)
print("PASS: unset managed key cleared, present managed key overridden")
sys.exit(0)
```

Attack 3 — `probe_3_keep_nonmanaged.py` → holds on the patched tree (good)

```python
# Req1.7 / Req2.3: a NON-managed key present only at creation is retained;
# no spurious keys appear. 'indexes' is not in ALTER_OPTION_KEYS.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions

nonmanaged = {"indexes": ["idx1"]}  # not a managed key
create = CreateModel("Pony", fields=[], options={**nonmanaged, "verbose_name": "V"})
alter = AlterModelOptions("Pony", options={})
op = create.reduce(alter, "app")[0]
print("folded options:", op.options)

if op.options.get("indexes") != ["idx1"]:
    print("FAIL: non-managed creation key 'indexes' not retained"); sys.exit(1)
if "verbose_name" in op.options:
    print("FAIL: managed 'verbose_name' should have been cleared"); sys.exit(1)
# no key absent from both
allowed = set(create.options) | set(alter.options)
extra = set(op.options) - allowed
if extra:
    print(f"FAIL: spurious keys present: {extra}"); sys.exit(1)
print("PASS: non-managed key kept, managed cleared, no spurious keys")
sys.exit(0)
```

Attack 4 — `probe_4_identity.py` → holds on the patched tree (good)

```python
# Req1.1/1.2: single replacement CreateModel with same name/fields/bases/managers.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions
from django.db import models

fields = [("id", models.AutoField(primary_key=True))]
bases = (models.Model,)
managers = [("objects", models.Manager())]
create = CreateModel("Pony", fields=fields, options={"ordering": ["id"]}, bases=bases, managers=managers)
alter = AlterModelOptions("pony", options={"ordering": ["id"]})  # case-insensitive match
res = create.reduce(alter, "app")
assert isinstance(res, list) and len(res) == 1, f"expected single op: {res!r}"
op = res[0]
print("name:", op.name, "nfields:", len(op.fields), "bases:", op.bases, "nmanagers:", len(op.managers))
if op.name != "Pony": print("FAIL: name changed"); sys.exit(1)
if op.fields != fields: print("FAIL: fields changed"); sys.exit(1)
if op.bases != bases: print("FAIL: bases changed"); sys.exit(1)
if op.managers != managers: print("FAIL: managers changed"); sys.exit(1)
print("PASS: identity preserved, single op, case-insensitive match")
sys.exit(0)
```

Attack 5 — `probe_5_overlay.py` → holds on the patched tree (good)

```python
# Req2.1/2.2/Req1.6: change adds a new key and overrides an existing key value.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions

create = CreateModel("Pony", fields=[], options={"verbose_name": "Old"})
alter = AlterModelOptions("Pony", options={"verbose_name": "New", "verbose_name_plural": "News"})
op = create.reduce(alter, "app")[0]
print("folded options:", op.options)
if op.options.get("verbose_name") != "New":
    print("FAIL: overridden key not updated"); sys.exit(1)
if op.options.get("verbose_name_plural") != "News":
    print("FAIL: added key missing"); sys.exit(1)
print("PASS: overlay of changed and added options preserved")
sys.exit(0)
```

Attack 6 — `probe_6_other_ops.py` → holds on the patched tree (good)

```python
# Req3.1/3.2: other reductions and name-mismatch are unaffected.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions

# name mismatch: AlterModelOptions targeting a different model must NOT fold.
create = CreateModel("Pony", fields=[], options={"verbose_name": "V"})
alter_other = AlterModelOptions("Horse", options={})
res = create.reduce(alter_other, "app")
print("mismatch reduce result:", res)
# When not foldable, reduce returns False (or a list not equal to our folded form).
if isinstance(res, list) and len(res) == 1 and isinstance(res[0], CreateModel):
    # Would only be a list if optimizer allows through-reduction; ensure it did NOT clear.
    if "verbose_name" not in res[0].options:
        print("FAIL: mismatched-model alter wrongly cleared managed options"); sys.exit(1)
print("PASS: name mismatch not folded with clearing semantics")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_clear_empty.py`

```python
# Req1.4/1.5 (POSITIVE CONTROL): a managed option key set at creation but absent
# from an empty AlterModelOptions must be CLEARED in the folded result.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions

create = CreateModel("Pony", fields=[], options={"verbose_name": "Pony", "permissions": [("x", "X")]})
alter = AlterModelOptions("Pony", options={})
result = create.reduce(alter, "app")

assert isinstance(result, list) and len(result) == 1, f"expected single op, got {result!r}"
op = result[0]
assert isinstance(op, CreateModel), f"expected CreateModel, got {type(op)}"
print("folded options:", op.options)
# verbose_name and permissions are managed keys; must be cleared
for k in ("verbose_name", "permissions"):
    if k in op.options:
        print(f"FAIL: managed key {k!r} was not cleared")
        sys.exit(1)
print("PASS: all creation-supplied managed options cleared")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Six probes cover Req1.1/1.2 (identity+single op, probe_4), Req1.4 partial clear (probe_2), Req1.5 empty-change full clear (probe_1, positive control), Req1.6/2.1/2.2 overlay (probe_5), Req1.7/2.3 non-managed retention & no spurious keys (probe_3), Req3.1/3.2 name-mismatch not folded (probe_6). ALTER_OPTION_KEYS confirmed = base_manager_name, default_manager_name, default_permissions, default_related_name, get_latest_by, managed, ordering, permissions, select_on_save, verbose_name, verbose_name_plural. All 6 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (folded={'verbose_name':'Pony','permissions':[...]}) and HOLDS patched (folded={}) — discriminates. Probes 2,3 also VIOLATED at base, confirming base overlay-only behavior. Wrong-fix candidate 'clear_only_when_empty' REJECTED by probe_2 (Req1.4 not satisfied for the partial/non-empty change case), demonstrating the suite discriminates weak implementations. No probe-conforming alternative found that would leave hidden tests unresolved. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_clear_empty.py`, `probe_2_clear_partial.py`, `probe_3_keep_nonmanaged.py`, `probe_4_identity.py`, `probe_5_overlay.py`, `probe_6_other_ops.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_clear_empty.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak patch (clear managed keys only when change options is empty) produces folded options {'verbose_name':'New','ordering':['name']} for CreateModel(ordering=['name'],verbose_name='Old') + AlterModelOptions(verbose_name='New'); 'ordering' should be cleared per Req1.4. Probe_2 REJECTS it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_clear_empty.py` → holds on the patched tree (good)

Attack 2 — `probe_2_clear_partial.py` → holds on the patched tree (good)

Attack 3 — `probe_3_keep_nonmanaged.py` → holds on the patched tree (good)

Attack 4 — `probe_4_identity.py` → holds on the patched tree (good)

Attack 5 — `probe_5_overlay.py` → holds on the patched tree (good)

Attack 6 — `probe_6_other_ops.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_clear_empty.py`

```python
# Req1.4/1.5 (POSITIVE CONTROL): a managed option key set at creation but absent
# from an empty AlterModelOptions must be CLEARED in the folded result.
import sys
from django.db.migrations.operations.models import CreateModel, AlterModelOptions

create = CreateModel("Pony", fields=[], options={"verbose_name": "Pony", "permissions": [("x", "X")]})
alter = AlterModelOptions("Pony", options={})
result = create.reduce(alter, "app")

assert isinstance(result, list) and len(result) == 1, f"expected single op, got {result!r}"
op = result[0]
assert isinstance(op, CreateModel), f"expected CreateModel, got {type(op)}"
print("folded options:", op.options)
# verbose_name and permissions are managed keys; must be cleared
for k in ("verbose_name", "permissions"):
    if k in op.options:
        print(f"FAIL: managed key {k!r} was not cleared")
        sys.exit(1)
print("PASS: all creation-supplied managed options cleared")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Six probes cover Req1.1/1.2 (identity+single op, probe_4), Req1.4 partial clear (probe_2), Req1.5 empty-change full clear (probe_1, positive control), Req1.6/2.1/2.2 overlay (probe_5), Req1.7/2.3 non-managed retention & no spurious keys (probe_3), Req3.1/3.2 name-mismatch not folded (probe_6). ALTER_OPTION_KEYS confirmed = base_manager_name, default_manager_name, default_permissions, default_related_name, get_latest_by, managed, ordering, permissions, select_on_save, verbose_name, verbose_name_plural. All 6 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (folded={'verbose_name':'Pony','permissions':[...]}) and HOLDS patched (folded={}) — discriminates. Probes 2,3 also VIOLATED at base, confirming base overlay-only behavior. Wrong-fix candidate 'clear_only_when_empty' REJECTED by probe_2 (Req1.4 not satisfied for the partial/non-empty change case), demonstrating the suite discriminates weak implementations. No probe-conforming alternative found that would leave hidden tests unresolved. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `options = {**self.options, **operation.options}; for key in operation.ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key, None)` in the CreateModel.reduce AlterModelOptions branch. Requirements correctly identify managed keys as AlterModelOptions.ALTER_OPTION_KEYS (verified: default_permissions, permissions, verbose_name, ordering, get_latest_by, etc.), pin both the clearing direction (the new fix) AND the retained overlay direction (regression guard), and correctly scope the change to the name_lower-matching AlterModelOptions branch only (R3). Modeling boundary is the changed observable behavior, biconditionally. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the public problem_statement (models.py, CreateModel.reduce(), the options={**self.options,**operation.options} bug line, the AlterModelOptions options={} case, and the AlterModelOptions.state_forwards() reference are all public). The gold-patch identifier ALTER_OPTION_KEYS is never named — the doc uses the generic descriptive term 'managed option keys' tied to state_forwards, which is legitimate localization/behavioral translation. No test names (test_create_model_and_remove_model_options), no test literals ('MyModel', 'verbose_name', 'verbose_name_plural', 'My Model'), no quoted test/gold code, and no case enumeration mirroring the two parametrized test cases. Criteria 4/5 describe partial-clear and empty-clear as general behavior, not the specific parametrized values (the empty-options case is itself in the public problem_statement).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
