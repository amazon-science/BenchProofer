# refinement.md — pytest-dev__pytest-7571

The operation-by-operation correspondence between `model.py`'s implementation
(the `CaptureController.__init__`, `set_level`, `teardown_restore` impl regions, and the
`run_raise_then_teardown` driver) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deeply-modelled callee is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim: any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). The patch touches three sites in
`src/_pytest/logging.py`, all inside `LogCaptureFixture`.

## A. The constructor — `__init__` (`src/_pytest/logging.py:344`)

Gold hunk:
```
  self._item = item
  # dict of log name -> log level
+ self._initial_handler_level = None  # type: Optional[int]
  self._initial_logger_levels = {}  # type: Dict[Optional[str], int]
```

| # | model.py impl op (`CaptureController.__init__`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `self.saved_level = None` | `self._initial_handler_level = None  # type: Optional[int]` | R + I | identical assignment of the `None` sentinel; carrier `Optional[int]` ↔ `Optional[int]` (mapping §2). |
| A2 | `self.sink_level = sink_level` | (no node) — the handler pre-exists; `__init__` does not set its level | R | the model materializes the sink's ambient threshold as a constructor parameter so the object is fully initialized (Nagini requires every field set in `__init__`). `self._item` / `self._initial_logger_levels` are unmodelled (unchanged facets, mapping §2). |

## B. The level-setting operation — `set_level` (`src/_pytest/logging.py:422`)

Gold hunk:
```
  self._initial_logger_levels.setdefault(logger, logger_obj.level)
  logger_obj.setLevel(level)
+ self._initial_handler_level = self.handler.level
  self.handler.setLevel(level)
```

| # | model.py impl op (`set_level`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no node) | `self._initial_logger_levels.setdefault(...)`, `logger_obj.setLevel(level)` | R | the *logger*-level save/set is the unchanged, pre-existing facet (mapping §2); unmodelled. |
| B2 | `self.saved_level = self.sink_level` | `self._initial_handler_level = self.handler.level` | R + A-reference | reads the sink's current threshold and records it as the restore point. `self.handler.level` ↔ `self.sink_level` read; assignment to `saved_level` ↔ assignment to `_initial_handler_level` (mapping §2). `self.handler.level` is the unchanged `logging.Handler.level` accessor, validated as the modelled field by G-AX (mapping §3.1). |
| B3 | `self.sink_level = level` | `self.handler.setLevel(level)` | R + A-reference | moves the sink to the requested threshold. `self.handler.setLevel(L)` ↔ `self.sink_level = L`; `setLevel` stores the (integer) level verbatim (mapping §3.1, `_checkLevel` identity on the int levels the tests use). |

The discriminating content of this hunk — recording the pre-change handler
level (B2) — is the line the gold patch adds. `model_prepatch.py` omits B2 and
**fails** the postcondition `self.saved_level is not None` (and
`self.saved_level == Old(self.sink_level)`): the spec senses the missing record
(G-DIFF).

## C. The teardown — `_finalize` (`src/_pytest/logging.py:350`)

Gold hunk:
```
  # restore log levels
+ if self._initial_handler_level is not None:
+     self.handler.setLevel(self._initial_handler_level)
  for logger_name, level in self._initial_logger_levels.items():
      ...
```

| # | model.py impl op (`teardown_restore`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `if self.saved_level is not None:` | `if self._initial_handler_level is not None:` | R + I | identical `is not None` guard on the restore point; carrier `Optional[int]` ↔ `Optional[int]` (mapping §2). |
| C2 | `self.sink_level = self.saved_level` | `self.handler.setLevel(self._initial_handler_level)` | R + A-reference | returns the sink to the recorded threshold. `self.handler.setLevel(x)` ↔ `self.sink_level = x` (mapping §2, §3.1). |
| C3 | (no node) | the `for logger_name, level in self._initial_logger_levels.items(): ... logger.setLevel(level)` loop | R | the unchanged logger-level restoration (mapping §2); unmodelled. |

The discriminating content of this hunk — restoring the handler level (C1+C2) —
is what the gold patch adds. `model_prepatch.py` omits C1+C2 and **fails** the
postcondition `Implies(Old(self.saved_level) is not None, self.sink_level ==
Old(self.saved_level))`: the spec senses the missing restore (G-DIFF).

## D. The end-to-end observable — `run_raise_then_teardown`

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| D1 | `controller = CaptureController(ambient)`; `set_level(controller, level)`; `teardown_restore(controller)`; `return controller.sink_level` | the lifecycle a test exercises: the caplog fixture is created (`__init__`), the test calls `set_level`, the fixture finalizer runs (`_finalize`) | R + I | the composition of A/B/C. Its postcondition `Result() == ambient` is exactly what the F2P test `test_change_level_undos_handler_level` observes: after a test raises the handler level (`set_level(41)`) and teardown runs, the *next* test sees `caplog.handler.level == 0` (the ambient). The driver makes the cross-test restore guarantee explicit as a human-readable end-to-end observable. It carries **no** independent discriminating power: Nagini verifies the driver **modularly** against the (strong) contracts of `set_level`/`teardown_restore`, so the driver is satisfiable in isolation against those contracts in BOTH model.py and `model_prepatch.py` (cf. attack atk_5, a cheating driver that verifies but maps to no repo symbol). The entire G-DIFF discrimination comes from the two core postconditions — `set_level`'s record clause (model.py:81-82) and `teardown_restore`'s restore implication (model.py:100-101) — which `model_prepatch.py` fails on the modular bodies of `set_level`/`teardown_restore` themselves, not via the driver. |

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operations that genuinely
*changed* — recording the pre-change handler level (B2) and restoring it at
teardown (C1+C2) — are modelled **deeply** as ordinary integer field reads/
writes and an `Optional` guard, not hidden behind a consumed axiom. There is
**no `@ContractOnly` axiom**; the only callees the changed code invokes
(`logging.Handler.level` / `setLevel`, both unchanged) appear only as the
**A-reference** §3.1 that G-AX validates the field abstraction against, plus the
end-to-end **A-reference** §3.2 (the real `set_level`/`_finalize` round trip).

## F. verify(model) ⇒ resolved

`set_level` verifies only if it records the sink's pre-change threshold (B2) and
moves the sink to the requested one (B3); `teardown_restore` verifies only if it
returns the sink to the recorded threshold when one was recorded (C); the driver
verifies only if the composed round trip lands back at the ambient threshold
(D). By R (`self.handler.level`/`setLevel` ↔ the `sink_level` field, mapping
§2, §3.1) the verified controller is the gold-patched `LogCaptureFixture` on the
tested integer levels; by G-AX the field abstraction equals the real
`logging.Handler` level semantics (A-reference §3.1) and the real
`set_level`/`_finalize` reproduce the round trip (A-reference §3.2). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited references — and the gold patch resolves
(G-RESOLVE). The trust point is exactly the A-reference soundness of §1.1
(G-AX) and the refinement fidelity of this document (G-EQ).
