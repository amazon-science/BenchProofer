# refinement.md — pytest-dev__pytest-7236

The operation-by-operation correspondence between `model.py`'s implementation
(the `decide_teardown` impl region and the deep `skip_marker_set` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed** / **A-reference**), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

The gold patch introduces one helper and uses it at three sites in
`src/_pytest/unittest.py`:

```
+def _is_skipped(obj) -> bool:
+    """Return True if the given object has been marked with @unittest.skip"""
+    return bool(getattr(obj, "__unittest_skip__", False))
```

Sites:
- `collect()` (line 44): `skipped = getattr(cls, "__unittest_skip__", False)`
  → `skipped = _is_skipped(cls)`.
- `_make_xunit_fixture.fixture` (line 92):
  `if getattr(self, "__unittest_skip__", None):` → `if _is_skipped(self):`.
- `runtest()` (line 223): `if self.config.getoption("usepdb"):`
  → `if self.config.getoption("usepdb") and not _is_skipped(self.obj):`.

The single FAIL_TO_PASS, `test_pdb_teardown_skipped[@unittest.skip]`, runs a
skipped `unittest.TestCase` under `--pdb` and asserts that `tearDown` is NOT
executed. The pre-patch `runtest()` unconditionally records
`self._explicit_tearDown = self._testcase.tearDown` whenever `usepdb` is set,
and that recorded routine is invoked later in `teardown()` — so for a skipped
test it runs `tearDown`. The fix guards the recording with `not _is_skipped`.

This is the **only independently-observable behaviour change**. The `collect()`
and `_make_xunit_fixture` sites are pure refactors: `_is_skipped(x)` is
*defined* as `bool(getattr(x, "__unittest_skip__", False))`, so it returns the
same truthiness as the inlined `getattr` they replace, and both sites only test
that truthiness in a boolean context. They are tagged **I** below and have no
separate failing prepatch (no observable behaviour to discriminate; the spec is
byte-identical between twin and prepatch, G-DIFF's `same_spec`).

## A. The teardown-recording decision — `runtest()` (`src/_pytest/unittest.py:223`)

Gold hunk:
```
- if self.config.getoption("usepdb"):
+ if self.config.getoption("usepdb") and not _is_skipped(self.obj):
      self._explicit_tearDown = self._testcase.tearDown
      setattr(self._testcase, "tearDown", lambda *args: None)
```

| # | model.py impl op (`decide_teardown`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `item.postmortem_mode` (`bool`) | `self.config.getoption("usepdb")` | R | the `--pdb` option is read as a truthy config value; modelled as a `bool`. Read-only at `Acc(item.postmortem_mode, 1/2)`. |
| A2 | `skip_marker_set(item.skip_marker)` (deep `@Pure` model) | `_is_skipped(self.obj)` | A-reference | the introduced helper is modelled **deeply**: `skip_marker_set(m) == (m != 0)`. The real helper is `bool(getattr(obj, "__unittest_skip__", False))`, i.e. "the skip marker is present with a truthy value". `skip_marker` (R) models the marker value under the default-absent lookup: `0` ↔ absent-or-falsy, non-zero ↔ present-and-truthy; `!= 0` ↔ `bool(...)`. There is no consumed axiom — the deep model is validated `== bool(getattr(...))` out-of-band by axiom_check.py (G-AX). |
| A3 | `item.postmortem_mode and not skip_marker_set(...)` | `self.config.getoption("usepdb") and not _is_skipped(self.obj)` | I | identical short-circuit boolean conjunction with `not`. |
| A4 | `item.teardown_recorded = True` (the True branch) | `self._explicit_tearDown = self._testcase.tearDown; setattr(..., "tearDown", lambda: None)` | R | recording the teardown routine for explicit later invocation is modelled by the boolean `teardown_recorded`. The later `teardown()` invokes it iff `self._explicit_tearDown is not None`, i.e. iff it was recorded — so the observable "pytest later runs tearDown for this skipped/non-skipped case under --pdb" ↔ `teardown_recorded`. Mutated object, full permission, post-state stated exactly. |

The discriminating content of the change — recording the teardown routine only
when `not skipped` — lives in `item.teardown_recorded == (item.postmortem_mode and not
skip_marker_set(item.skip_marker))` (model) ⇔ the guarded `if usepdb and not
_is_skipped(self.obj)` (real). `model_prepatch.py` reproduces the pre-patch
`if usepdb:` (records whenever `usepdb`, ignoring the marker) and **fails** that
postcondition on the discriminating case `usepdb ∧ skip_marker_set` — exactly the
F2P scenario (G-DIFF).

The P2P companion `test_pdb_teardown_called` (non-skipped under `--pdb`,
tearDown MUST eventually run) is preserved by the same clause: when
`skip_marker_set(marker) == False` and `usepdb == True`, the spec REQUIRES
`teardown_recorded == True`, so a verifying impl still records the teardown for
the non-skipped case. The conjunction pins both directions.

## B. The collect / fixture sites — refactor (`unittest.py:44`, `:92`)

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `skip_marker_set(skip_marker)` (deep model) used as the skip predicate | `getattr(cls, "__unittest_skip__", False)` → `_is_skipped(cls)` (`collect`); `getattr(self, "__unittest_skip__", None)` → `_is_skipped(self)` (`fixture`) | I (behaviour) / A-reference (the predicate) | both sites only consume the *truthiness* of the marker in a boolean context (`if not skipped:` / `if ...:`). `_is_skipped` returns the same truthiness as the inlined `getattr` it replaces (G-AX checks `bool(getattr(...)) == _is_skipped`). No behaviour change ⇒ no separate prepatch. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— gating the teardown recording on `not skipped` — is modelled **deeply** (the
boolean conjunction in `decide_teardown` consuming the spelled-out `skip_marker_set`
model), not hidden behind an axiom about the function under change. The
introduced helper `_is_skipped` is the **A-reference** that G-AX validates the
deep model `skip_marker_set` against (`bool(getattr(obj, "__unittest_skip__",
False))`). There is **no consumed `@ContractOnly` axiom** — the changed code
calls no unchanged opaque callee whose contract the proof needs.

## D. verify(model) ⇒ resolved

`decide_teardown` verifies only if `teardown_recorded` equals the exact
conjunction `usepdb ∧ ¬skip_marker_set(marker)` (A3) over a read-only mode flag and
marker (A1, A2) with the result recorded exactly (A4). By R (config option ↔
`bool`; explicit-teardown recording ↔ `teardown_recorded`; marker value ↔
`skip_marker`) the verified decision equals the gold's guarded `if usepdb and
not _is_skipped(self.obj)` on the tested inputs; by G-AX the deep model
`skip_marker_set` equals the real `bool(getattr(obj, "__unittest_skip__", False))`
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited helper — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom/deep-model soundness (G-AX) and refinement fidelity (this document, G-EQ).
