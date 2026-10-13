# refinement.md — operation correspondence (django__django-14765)

Maps every op in `implementation_initRealApps` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python is:

```python
if real_apps is None:
    real_apps = set()
else:
    assert isinstance(real_apps, set)
self.real_apps = real_apps
```

The modeled output component is the produced `self.real_apps` value (or the
`AssertionError`). The argument's runtime kind (None / set / other collection) is
refined to the `RealAppsArg` constructor tag; `AssertionError` is refined to
`Except.error ()`; a produced set is refined to `Except.ok` of its elements.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `arg : RealAppsArg` dispatch on the constructor tag | `real_apps is None` / `isinstance(real_apps, set)` test | R | argument-kind ↔ constructor-tag bijection (mapping.md): `None`↔`absent`, a `set`↔`isSet`, any other collection↔`nonSet`. The `is None` + `isinstance` tests are a total 3-way classification, modeled as the 3 constructors. |
| 2 | `.absent => realApps := []` | `if real_apps is None: real_apps = set()` | I | empty result on the absent branch (`Except.ok []`) |
| 3 | `.isSet xs => realApps := xs` | `else: assert isinstance(...set)` passes, `self.real_apps = real_apps` | I | the set is taken unchanged; `Except.ok` of its elements (set identity preserved — R on the set↔`List String` carrier) |
| 4 | `.nonSet _ => return Except.error ()` | `else: assert isinstance(...set)` FAILS → `AssertionError` | R | the failed assertion aborts the constructor with no value; refined to `Except.error ()` (exception ↔ `Except.error`, mapping.md) |
| 5 | `return Except.ok realApps` | `self.real_apps = real_apps` | I | the produced value is the (possibly emptied) collection |

No A-consumed rows: the proof discharges the constructor-tag dispatch directly;
no UNCHANGED callee property is assumed (axioms region empty). No A-reference
rows: `isinstance`/`set()` are Python builtins modeled structurally, not deep
models of repo callees. No changed-inexpressible op.

The discriminating clause is row 4: the `.nonSet` case. Post-patch, a non-set
collection is **rejected** (`Except.error ()`). The prepatch impl instead
silently coerces it (`realApps := xs`, i.e. `Except.ok xs`), so its
`correct_initRealApps` cannot close against the frozen `problem_spec_initRealApps`
(which pins `Except.error ()` on `.nonSet`). That mismatch is exactly the G-DIFF
signal, and it is the behavior the F2P test `test_real_apps_non_set` exercises
(`ProjectState(real_apps=['contenttypes'])` must raise `AssertionError`).
