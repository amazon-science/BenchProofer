# P2 adversarial audit — django__django-15268

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 11 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 11 | `probe_1_reduce_unique_across_index.py`, `probe_2_reduce_index_across_unique.py`, `probe_3_same_option_merge.py`, `probe_4_collapse_clear_then_set.py`, `probe_5_collapse_empty_target.py`, `probe_6_no_reduce_across_addfield.py`, `probe_7_no_reduce_across_removefield.py`, `probe_8_no_reduce_across_renamefield.py`, +3 more |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4_collapse_clear_then_set.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (11):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_reduce_unique_across_index.py` → holds on the patched tree (good)

```python
# R1.1: AlterUniqueTogether.reduce across a later AlterIndexTogether (same model)
# SHALL report it can be optimized across (reduce returns truthy, non-list -> reorder allowed).
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
u = AlterUniqueTogether(name='mymodel', unique_together=set())
i = AlterIndexTogether(name='mymodel', index_together={('col',)})
res = u.reduce(i, 'myapp')
print("reduce result:", repr(res), "type:", type(res).__name__)
ok = bool(res) and not isinstance(res, list)
print("can optimize across (truthy, non-merge):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2_reduce_index_across_unique.py` → holds on the patched tree (good)

```python
# R1.2: AlterIndexTogether.reduce across a later AlterUniqueTogether (same model)
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
i = AlterIndexTogether(name='mymodel', index_together=set())
u = AlterUniqueTogether(name='mymodel', unique_together={('col',)})
res = i.reduce(u, 'myapp')
print("reduce result:", repr(res), "type:", type(res).__name__)
ok = bool(res) and not isinstance(res, list)
print("can optimize across (truthy, non-merge):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3_same_option_merge.py` → holds on the patched tree (good)

```python
# R1.4: later op is same option type on same model -> merged into single op carrying later's value.
from django.db.migrations.operations.models import AlterUniqueTogether
first = AlterUniqueTogether(name='mymodel', unique_together=set())
later = AlterUniqueTogether(name='mymodel', unique_together={('col',)})
res = first.reduce(later, 'myapp')
print("reduce result:", repr(res))
ok = (isinstance(res, list) and len(res) == 1
      and isinstance(res[0], AlterUniqueTogether)
      and res[0].option_value == {('col',)})
print("merged to single op carrying later value:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4_collapse_clear_then_set.py` → holds on the patched tree (good)

```python
# R2.1 + R2.2: optimize clear-then-set of both options -> exactly one Unique + one Index,
# each carrying the FINAL non-empty value.  (POSITIVE CONTROL: fails at base.)
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
from django.db.migrations.optimizer import MigrationOptimizer
ops = [
    AlterUniqueTogether(name='mymodel', unique_together=set()),
    AlterIndexTogether(name='mymodel', index_together=set()),
    AlterUniqueTogether(name='mymodel', unique_together={('col',)}),
    AlterIndexTogether(name='mymodel', index_together={('col',)}),
]
out = MigrationOptimizer().optimize(ops, 'myapp')
print("optimized types:", [type(o).__name__ for o in out])
uni = [o for o in out if isinstance(o, AlterUniqueTogether)]
idx = [o for o in out if isinstance(o, AlterIndexTogether)]
ok = (len(out) == 2 and len(uni) == 1 and len(idx) == 1
      and uni[0].option_value == {('col',)}
      and idx[0].option_value == {('col',)})
print("values:", [(type(o).__name__, o.option_value) for o in out])
print("collapsed to one op per option with final values:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5_collapse_empty_target.py` → holds on the patched tree (good)

```python
# R2.3: collapse holds even when the final target is the empty set (remove-all).
# clear(set()) then set(set()) for both -> collapse; result must not increase op count (<=2) (R2.4).
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
from django.db.migrations.optimizer import MigrationOptimizer
ops = [
    AlterUniqueTogether(name='mymodel', unique_together=set()),
    AlterIndexTogether(name='mymodel', index_together=set()),
    AlterUniqueTogether(name='mymodel', unique_together=set()),
    AlterIndexTogether(name='mymodel', index_together=set()),
]
out = MigrationOptimizer().optimize(ops, 'myapp')
print("optimized types:", [type(o).__name__ for o in out])
# duplicate identical alters should collapse; total must not grow, and no more than one per option.
uni = [o for o in out if isinstance(o, AlterUniqueTogether)]
idx = [o for o in out if isinstance(o, AlterIndexTogether)]
ok = len(out) <= len(ops) and len(uni) <= 1 and len(idx) <= 1
print("count:", len(out), "uni:", len(uni), "idx:", len(idx))
print("collapse holds for empty target, no op-count increase:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6_no_reduce_across_addfield.py` → holds on the patched tree (good)

```python
# R3.1: alter-together SHALL NOT be optimized across an AddField on same model.
from django.db.migrations.operations.models import AlterUniqueTogether
from django.db.migrations.operations.fields import AddField
from django.db import models
u = AlterUniqueTogether(name='mymodel', unique_together={('col',)})
add = AddField(model_name='mymodel', name='col', field=models.IntegerField(default=0))
res = u.reduce(add, 'myapp')
print("reduce across AddField(same model):", repr(res))
ok = res is False   # cannot optimize across
print("blocked (reduce is False):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7_no_reduce_across_removefield.py` → holds on the patched tree (good)

```python
# R3.2: alter-together SHALL NOT be optimized across a RemoveField on same model.
from django.db.migrations.operations.models import AlterUniqueTogether
from django.db.migrations.operations.fields import RemoveField
u = AlterUniqueTogether(name='mymodel', unique_together={('col',)})
rm = RemoveField(model_name='mymodel', name='col')
res = u.reduce(rm, 'myapp')
print("reduce across RemoveField(same model):", repr(res))
ok = res is False
print("blocked (reduce is False):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 8 — `probe_8_no_reduce_across_renamefield.py` → holds on the patched tree (good)

```python
# R3.3: alter-together SHALL NOT be optimized across a RenameField on same model.
from django.db.migrations.operations.models import AlterUniqueTogether
from django.db.migrations.operations.fields import RenameField
u = AlterUniqueTogether(name='mymodel', unique_together={('col',)})
ren = RenameField(model_name='mymodel', old_name='col', new_name='col2')
res = u.reduce(ren, 'myapp')
print("reduce across RenameField(same model):", repr(res))
ok = res is False
print("blocked (reduce is False):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 9 — `probe_9_reduce_across_unrelated_model.py` → holds on the patched tree (good)

```python
# R3.4: alter-together SHALL be optimizable across any op not referencing same model.
from django.db.migrations.operations.models import AlterUniqueTogether
from django.db.migrations.operations.fields import AddField
from django.db import models
u = AlterUniqueTogether(name='mymodel', unique_together={('col',)})
add = AddField(model_name='othermodel', name='x', field=models.IntegerField(default=0))
res = u.reduce(add, 'myapp')
print("reduce across AddField(other model):", repr(res))
ok = bool(res) and not isinstance(res, list)
print("optimizable across unrelated op:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 10 — `probe_10_collapse_with_removefield.py` → holds on the patched tree (good)

```python
# R3.5: sequence = redundant clear-then-set + field removal same model ->
# collapsed one Unique + one Index FOLLOWED BY RemoveField.
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
from django.db.migrations.operations.fields import RemoveField
from django.db.migrations.optimizer import MigrationOptimizer
ops = [
    AlterUniqueTogether(name='mymodel', unique_together=set()),
    AlterIndexTogether(name='mymodel', index_together=set()),
    AlterUniqueTogether(name='mymodel', unique_together={('a','b')}),
    AlterIndexTogether(name='mymodel', index_together={('a','b')}),
    RemoveField(model_name='mymodel', name='c'),
]
out = MigrationOptimizer().optimize(ops, 'myapp')
names = [type(o).__name__ for o in out]
print("optimized types:", names)
ok = names == ['AlterUniqueTogether','AlterIndexTogether','RemoveField']
uni = [o for o in out if isinstance(o, AlterUniqueTogether)][0] if 'AlterUniqueTogether' in names else None
ok = ok and uni.option_value == {('a','b')}
print("collapse then RemoveField last:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 11 — `probe_11_rename_then_collapse.py` → holds on the patched tree (good)

```python
# R3.6: RenameField for model FOLLOWED BY redundant clear-then-set ->
# rename first, then collapsed one Unique + one Index.
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
from django.db.migrations.operations.fields import RenameField
from django.db.migrations.optimizer import MigrationOptimizer
ops = [
    RenameField(model_name='mymodel', old_name='c', new_name='d'),
    AlterUniqueTogether(name='mymodel', unique_together=set()),
    AlterIndexTogether(name='mymodel', index_together=set()),
    AlterUniqueTogether(name='mymodel', unique_together={('d',)}),
    AlterIndexTogether(name='mymodel', index_together={('d',)}),
]
out = MigrationOptimizer().optimize(ops, 'myapp')
names = [type(o).__name__ for o in out]
print("optimized types:", names)
ok = names == ['RenameField','AlterUniqueTogether','AlterIndexTogether']
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4_collapse_clear_then_set.py`

```python
# R2.1 + R2.2: optimize clear-then-set of both options -> exactly one Unique + one Index,
# each carrying the FINAL non-empty value.  (POSITIVE CONTROL: fails at base.)
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
from django.db.migrations.optimizer import MigrationOptimizer
ops = [
    AlterUniqueTogether(name='mymodel', unique_together=set()),
    AlterIndexTogether(name='mymodel', index_together=set()),
    AlterUniqueTogether(name='mymodel', unique_together={('col',)}),
    AlterIndexTogether(name='mymodel', index_together={('col',)}),
]
out = MigrationOptimizer().optimize(ops, 'myapp')
print("optimized types:", [type(o).__name__ for o in out])
uni = [o for o in out if isinstance(o, AlterUniqueTogether)]
idx = [o for o in out if isinstance(o, AlterIndexTogether)]
ok = (len(out) == 2 and len(uni) == 1 and len(idx) == 1
      and uni[0].option_value == {('col',)}
      and idx[0].option_value == {('col',)})
print("values:", [(type(o).__name__, o.option_value) for o in out])
print("collapsed to one op per option with final values:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: collapse redundant clear-then-set of unique_together/index_together via AlterTogetherOptionOperation.reduce/can_reduce_through, feeding MigrationOptimizer.optimize.

11 probes, all HOLD on gold-patched tree:
- probe_1 (R1.1): AlterUniqueTogether.reduce across later AlterIndexTogether (same model) -> truthy non-list (reorder allowed).
- probe_2 (R1.2): AlterIndexTogether.reduce across later AlterUniqueTogether -> truthy.
- probe_3 (R1.4): same-option-type later op -> merged to single op carrying later value.
- probe_4 (R2.1/R2.2, POSITIVE CONTROL): optimize clear-then-set of both options -> exactly one Unique + one Index, each with final non-empty value.
- probe_5 (R2.3/R2.4): collapse holds for empty target, no op-count increase.
- probe_6/7/8 (R3.1/3.2/3.3): reduce across AddField/RemoveField/RenameField on same model returns False (ordering guards preserved).
- probe_9 (R3.4): reduce across op referencing a DIFFERENT model -> truthy (optimizable as before).
- probe_10 (R3.5): clear-then-set + RemoveField -> [Unique, Index, RemoveField].
- probe_11 (R3.6): RenameField + clear-then-set -> [RenameField, Unique, Index].

Positive control (probe_4): FAILS at base (base yields 4 ops: two clears + two sets) and HOLDS patched -> discriminating power confirmed. probes 1,2,10,11 also confirmed VIOLATED at base.

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite):
- weak_diff_type.diff: lazy fix letting reduce cross ANY different-type op on the same model. Collapses correctly (probe_4/10/11 HOLD) but REJECTED by probe_6/7/8 (reduce now returns True across AddField/RemoveField/RenameField -> breaks ordering guards R3.1-3.3, would corrupt migration order / regress hidden ordering tests).
- weak_diff_asym.diff: asymmetric partial fix allowing only AlterUniqueTogether-across-AlterIndexTogether. probe_1 HOLDS but probe_2 REJECTS (Index cannot reduce across Unique -> R1.2 violated); also reorders output ([Index, Unique]).

Suite discriminates both plausible weak implementations; no probe-conforming alternative found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 11 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 11 | `probe_1_reduce_unique_across_index.py`, `probe_2_reduce_index_across_unique.py`, `probe_3_same_option_merge.py`, `probe_4_collapse_clear_then_set.py`, `probe_5_collapse_empty_target.py`, `probe_6_no_reduce_across_addfield.py`, `probe_7_no_reduce_across_removefield.py`, `probe_8_no_reduce_across_renamefield.py`, +3 more |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4_collapse_clear_then_set.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (11):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_reduce_unique_across_index.py` → holds on the patched tree (good)

Attack 2 — `probe_2_reduce_index_across_unique.py` → holds on the patched tree (good)

Attack 3 — `probe_3_same_option_merge.py` → holds on the patched tree (good)

Attack 4 — `probe_4_collapse_clear_then_set.py` → holds on the patched tree (good)

Attack 5 — `probe_5_collapse_empty_target.py` → holds on the patched tree (good)

Attack 6 — `probe_6_no_reduce_across_addfield.py` → holds on the patched tree (good)

Attack 7 — `probe_7_no_reduce_across_removefield.py` → holds on the patched tree (good)

Attack 8 — `probe_8_no_reduce_across_renamefield.py` → holds on the patched tree (good)

Attack 9 — `probe_9_reduce_across_unrelated_model.py` → holds on the patched tree (good)

Attack 10 — `probe_10_collapse_with_removefield.py` → holds on the patched tree (good)

Attack 11 — `probe_11_rename_then_collapse.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4_collapse_clear_then_set.py`

```python
# R2.1 + R2.2: optimize clear-then-set of both options -> exactly one Unique + one Index,
# each carrying the FINAL non-empty value.  (POSITIVE CONTROL: fails at base.)
from django.db.migrations.operations.models import AlterUniqueTogether, AlterIndexTogether
from django.db.migrations.optimizer import MigrationOptimizer
ops = [
    AlterUniqueTogether(name='mymodel', unique_together=set()),
    AlterIndexTogether(name='mymodel', index_together=set()),
    AlterUniqueTogether(name='mymodel', unique_together={('col',)}),
    AlterIndexTogether(name='mymodel', index_together={('col',)}),
]
out = MigrationOptimizer().optimize(ops, 'myapp')
print("optimized types:", [type(o).__name__ for o in out])
uni = [o for o in out if isinstance(o, AlterUniqueTogether)]
idx = [o for o in out if isinstance(o, AlterIndexTogether)]
ok = (len(out) == 2 and len(uni) == 1 and len(idx) == 1
      and uni[0].option_value == {('col',)}
      and idx[0].option_value == {('col',)})
print("values:", [(type(o).__name__, o.option_value) for o in out])
print("collapsed to one op per option with final values:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: collapse redundant clear-then-set of unique_together/index_together via AlterTogetherOptionOperation.reduce/can_reduce_through, feeding MigrationOptimizer.optimize.

11 probes, all HOLD on gold-patched tree:
- probe_1 (R1.1): AlterUniqueTogether.reduce across later AlterIndexTogether (same model) -> truthy non-list (reorder allowed).
- probe_2 (R1.2): AlterIndexTogether.reduce across later AlterUniqueTogether -> truthy.
- probe_3 (R1.4): same-option-type later op -> merged to single op carrying later value.
- probe_4 (R2.1/R2.2, POSITIVE CONTROL): optimize clear-then-set of both options -> exactly one Unique + one Index, each with final non-empty value.
- probe_5 (R2.3/R2.4): collapse holds for empty target, no op-count increase.
- probe_6/7/8 (R3.1/3.2/3.3): reduce across AddField/RemoveField/RenameField on same model returns False (ordering guards preserved).
- probe_9 (R3.4): reduce across op referencing a DIFFERENT model -> truthy (optimizable as before).
- probe_10 (R3.5): clear-then-set + RemoveField -> [Unique, Index, RemoveField].
- probe_11 (R3.6): RenameField + clear-then-set -> [RenameField, Unique, Index].

Positive control (probe_4): FAILS at base (base yields 4 ops: two clears + two sets) and HOLDS patched -> discriminating power confirmed. probes 1,2,10,11 also confirmed VIOLATED at base.

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite):
- weak_diff_type.diff: lazy fix letting reduce cross ANY different-type op on the same model. Collapses correctly (probe_4/10/11 HOLD) but REJECTED by probe_6/7/8 (reduce now returns True across AddField/RemoveField/RenameField -> breaks ordering guards R3.1-3.3, would corrupt migration order / regress hidden ordering tests).
- weak_diff_asym.diff: asymmetric partial fix allowing only AlterUniqueTogether-across-AlterIndexTogether. probe_1 HOLDS but probe_2 REJECTS (Index cannot reduce across Unique -> R1.2 violated); also reorders output ([Index, Unique]).

Suite discriminates both plausible weak implementations; no probe-conforming alternative found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch replaces the AlterTogether reduce's `not operation.references_model(...)` with `can_reduce_through`, and overrides can_reduce_through in AlterTogetherOptionOperation to also permit reduction across a different-typed AlterTogetherOptionOperation on the same model. Requirements model exactly this observable behavior: R1 pins the reduce decision (cross-option optimizable both directions, same-option still merges), R2 pins the observable optimize() collapse to one op per option, R3 pins preserved add/remove/rename ordering guarantees. Boundary is correct — requirements pin the changed observable behavior via MigrationOptimizer.optimize and reduce, not a narrower helper slice. Requirements matched the test_patch assertions (test_foo_together_ordering, test_remove_field_and_foo_together, test_rename_field_and_foo_together). Probe HOLDS on patched (exit 0), diverges on base (R2 len 4, R1.1 False).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document translates the hidden tests into behavioral requirements without transmitting them. The fix-invented method `can_reduce_through` (the core of the gold patch) is NOT named — only the pre-existing public `reduce`/`references_model`/`optimize` API and the affected classes are referenced, which is legitimate localization. Req 2.1's enumerated clear-then-set sequence is verbatim the PUBLIC problem_statement example, not hidden-test content. Reqs 2.3, 3.1-3.6 (ordering on column reorder, add-before-use, remove-after, rename-before) restate optimizer ordering invariants as behavioral guarantees rather than reproducing test parametrization; they align with FAIL_TO_PASS docstrings only at the level of behavior. No test file paths, test function/class names, parametrization ids, or quoted test/gold code appear.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
