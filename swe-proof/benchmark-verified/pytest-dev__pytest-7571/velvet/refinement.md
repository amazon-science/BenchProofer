# refinement.md — pytest-dev__pytest-7571

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `initStep`, `setLevelStep`, `restoreStep`, and `runLifecycle` `do` blocks,
plus the deep models `initState`/`setLevelState`/`restoreState`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs** (no foreign callee is axiomatized — §C), so G-CONF carries the
full mechanical burden and G-EQ audits only the narrative.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The construction site — `LogCaptureFixture.__init__` (`logging.py:344–349`)

Gold hunk:
```
         self._item = item
         # dict of log name -> log level
+        self._initial_handler_level = None  # type: Optional[int]
         self._initial_logger_levels = {}  # type: Dict[Optional[str], int]
```

Modeled method: `initStep`, deep model `initState`.

| # | Solution.lean impl op (`initStep`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `lvl0 : Int` | the ambient `self.handler.level` at fixture creation | R | handler level ↔ `Int` (mapping.md §2); a fresh `LogCaptureHandler` is NOTSET==0, the F2P-tested ambient. |
| A2 | `savedLevel := none` | the gold-added `self._initial_handler_level = None` | I + R | `None` ↔ `none` (mapping.md §2). Initializing the restore-slot to "nothing recorded" is exactly the added line. |
| A3 | `level := lvl0` | the handler is left at its current level by `__init__` (no level change there) | I | construction does not change the capture level. |

## B. The level-set site — `LogCaptureFixture.set_level` (`logging.py:437–441`)

Gold hunk:
```
         self._initial_logger_levels.setdefault(logger, logger_obj.level)
         logger_obj.setLevel(level)
+        self._initial_handler_level = self.handler.level
         self.handler.setLevel(level)
```

Modeled method: `setLevelStep`, deep model `setLevelState`.

| # | Solution.lean impl op (`setLevelStep`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `savedLevel := some st.level` | the gold-added `self._initial_handler_level = self.handler.level` | I + R | record the handler level **currently in effect** (`st.level`) for later reinstatement. R: handler level ↔ `Int`. This is an *unconditional assignment* (NOT `setdefault`), so a second set overwrites — `setLevelState` reproduces this (mapping.md §2 second-set note). |
| B2 | `level := lvl` | `self.handler.setLevel(level)` | I | move the capture level to the requested value; ordered AFTER the save (B1 precedes B2), matching the gold line order. |

## C. The teardown site — `LogCaptureFixture._finalize` (`logging.py:354–361`)

Gold hunk:
```
         # restore log levels
+        if self._initial_handler_level is not None:
+            self.handler.setLevel(self._initial_handler_level)
         for logger_name, level in self._initial_logger_levels.items():
             logger = logging.getLogger(logger_name)
             logger.setLevel(level)
```

Modeled method: `restoreStep`, deep model `restoreState`.

| # | Solution.lean impl op (`restoreStep`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `match st.savedLevel with | some v => …` | `if self._initial_handler_level is not None:` | I + R | the `is not None` guard ↔ matching the `some` branch (mapping.md §2: `Optional[int]` ↔ `Option Int`). |
| C2 | `some v => { st with level := v }` | `self.handler.setLevel(self._initial_handler_level)` | I | reinstate the recorded handler level — the gold-added body of the guard. |
| C3 | `none => pure st` | the guard is false ⇒ no handler `setLevel` call (level left as set) | I | when nothing was recorded, the cleanup leaves the handler untouched. |

## B′/C′. The lifecycle — `runLifecycle`

| # | Solution.lean op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| D1 | `let st0 ← initStep lvl0` | `f = LogCaptureFixture(item)` (handler at ambient `lvl0`) | I | callee-under-spec: `prove_correct` supplies `initStep_correct` (`st0 = initState lvl0`). |
| D2 | `let st1 ← setLevelStep st0 lvl` | `f.set_level(lvl)` | I | callee-under-spec: `setLevelStep_correct` (`st1 = setLevelState st0 lvl`). |
| D3 | `let st2 ← restoreStep st1` | `f._finalize()` | I | callee-under-spec: `restoreStep_correct` (`st2 = restoreState st1`). Composition gives `st2 = restoreState (setLevelState (initState lvl0) lvl)`. |

`runLifecycle`'s postconditions `out = restoreState (setLevelState (initState
lvl0) lvl)` AND `out.level = lvl0` are the exact property the F2P test asserts:
after a test sets the handler level and teardown runs, the next test sees the
handler back at the ambient level (`assert caplog.handler.level == 0`). With
`lvl0 = 0`, `out.level = 0` for any set `lvl` — the set is undone.

## Discriminating clause / prepatch

The behavioral change lives in two places, both reproduced by
`Solution_prepatch.lean` (byte-identical spec, G-DIFF):

1. `setLevelStep` pre-image sets `savedLevel := none` (does not record the
   handler level) ⇒ fails `st' = setLevelState st lvl`.
2. `restoreStep` pre-image returns `pure st` unconditionally (no reinstatement)
   ⇒ fails `st' = restoreState st` whenever a level was recorded.

Either reversion makes `runLifecycle` leave `out.level = lvl` (the level set
during the test) instead of `lvl0` — exactly the bug the F2P test catches
(`caplog.handler.level` printing `42`/`41` in the next test instead of `0`). A
single prepatch suffices: both reversions sit on the one F2P-observable behavior
(handler level after a set-then-teardown cycle), and the spec must stay
byte-identical across the prepatch, so they are reverted together in
`Solution_prepatch.lean`. The prepatch fails on both `setLevelStep` and
`restoreStep` clauses (verified: two `unsolved goals` errors), confirming the
spec sees the bug at both edited sites.

## C. No kind-3 (inexpressible-changed-op) steps; no A legs

Every step is R or I. The operations that genuinely changed — recording the
handler level at `set_level` (B1) and reinstating it at `_finalize` (C1/C2) —
are modeled **directly** in the impl/deep-models, not behind an axiom. There is
no unchanged foreign callee the proof depends on (`self.handler.setLevel` /
`self.handler.level` are the handler's level register, modeled as the
`FixtureState.level` field — an R refinement of the handler's level, checked by
G-CONF), so there is **no consumed axiom and no deep-model reference** (`axioms`
region empty; `meta.json axioms=[]`, `deep_model_references=[]`; G-AX skips).

## D. verify(Solution) ⇒ resolved

`runLifecycle` verifies only if `setLevelStep` records the in-effect level (B1)
and `restoreStep` reinstates it (C1/C2) — i.e. only the gold data-flow satisfies
the frozen spec (`out.level = lvl0`). By R (handler level ↔ `Int`,
`Optional[int]` ↔ `Option Int`) the verified lifecycle equals the real
`LogCaptureFixture` set-then-teardown cycle on the tested inputs; G-CONF refutes
any R/I infidelity over fuzzed level sequences (including multi-set, pinning the
unconditional-overwrite save) by differential execution against the patched real
fixture. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The only trust point is refinement fidelity (this doc + G-CONF); there is no
axiom trust point for this bundle.
