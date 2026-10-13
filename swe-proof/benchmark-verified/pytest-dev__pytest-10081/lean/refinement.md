# refinement.md — pytest-dev__pytest-10081

Operation correspondence between `implementation_deferTeardown` (Solution.lean,
impl region) and `patch.diff`. Every op is tagged **R** (type refinement) /
**A-consumed** / **A-reference** / **I** (identical concrete op).

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let skipped := testItselfSkipped \|\| classSkipped` | `skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)` | R | Python `or` over two boolean observables ↔ Lean `\|\|` over two `Bool` inputs. `_is_skipped(self.obj) ↔ testItselfSkipped`, `_is_skipped(self.parent.obj) ↔ classSkipped` (mapping.md). The two `_is_skipped` calls are UNCHANGED observations entering as data — not modeled internally. |
| 2 | `if pdbEnabled && !skipped then return true` | `if self.config.getoption("usepdb") and not skipped:` (guard taken ⇒ teardown captured & stubbed) | R | `and`/`not` ↔ `&&`/`!`; `getoption("usepdb")` truthiness ↔ `pdbEnabled` (mapping.md). The taken-guard event ("specially defer teardown") ↔ `result = true`. The body (capture `self._testcase.tearDown`, set `tearDown` to a no-op) is the deferral act itself, abstracted to the single boolean outcome. |
| 3 | `return false` | guard not taken (control falls through; teardown runs normally) | R | guard-not-taken ↔ `result = false`. |
| — | `assert isinstance(self.parent, UnitTestCase)` | patch adds the assertion | I-reference | Total/no-op on every valid run (a `TestCaseFunction`'s parent is always a `UnitTestCase`); carries no behavior into the modeled boolean, so it has no impl counterpart. |

## Tag summary

- **R**: ops 1–3 — the whole impl is a type-only refinement of the boolean
  decision (Python truthiness/`or`/`and`/`not` ↔ Lean `Bool`/`||`/`&&`/`!`).
  Mechanically refuted by G-CONF (conformance_check.py).
- **A-consumed**: none.
- **A-reference**: none (no callee is deeply modeled; `_is_skipped`'s outcome is
  an input observable, not an internal model).
- **I**: none beyond the behavior-neutral `assert` (tagged I-reference above; no
  impl op).

No changed op is inexpressible: the fix is a pure boolean combinator over three
observables, modeled exactly.

## Bug witness (G-DIFF)

The pre-patch impl computes `pdbEnabled && !testItselfSkipped`, dropping the
`classSkipped` disjunct. The discriminating input is
`pdbEnabled = true, testItselfSkipped = false, classSkipped = true`
(the F2P scenario: `--pdb`, class decorated `@unittest.skip`, method itself not
skipped). Spec demands `result = false`; pre-patch yields `true`. The carried
gold proof's `rfl` fails on exactly this case (`true.false.true`).
