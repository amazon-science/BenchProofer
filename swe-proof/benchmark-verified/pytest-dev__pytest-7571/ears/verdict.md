# P2 adversarial audit — pytest-dev__pytest-7571

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: Req 1.3/1.4/1.6 — after a test raises capture level via a
# single set_level starting from default 0, finalization restores handler level to 0.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key

class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}

fx = LogCaptureFixture(FakeItem())
start = fx.handler.level
print("initial handler level:", start)
fx.set_level(41)
print("after set_level(41):", fx.handler.level)
fx._finalize()
restored = fx.handler.level
print("after _finalize:", restored)
ok = (start == 0 and restored == 0)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2: during the test body, set_level sets the capture handler to requested level.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key
class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}
fx = LogCaptureFixture(FakeItem())
fx.set_level(logging.WARNING)
lvl = fx.handler.level
print("handler level after set_level(WARNING=30):", lvl)
ok = (lvl == logging.WARNING == 30)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.5: a test that never calls set_level -> _finalize must NOT change handler level.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key
class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}
fx = LogCaptureFixture(FakeItem())
fx.handler.setLevel(17)   # some pre-existing level, no set_level called on fixture
before = fx.handler.level
fx._finalize()
after = fx.handler.level
print("before finalize:", before, "after finalize:", after)
ok = (before == 17 and after == 17)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 1.1/1.3: on multiple set_level calls in one test, the RECORDED (restored)
# handler level is the one in effect immediately before the LAST set_level call
# (overwrite semantics), NOT the pre-test level. set_level(41) then set_level(43)
# starting from 0 -> restore to 41.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key
class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}
fx = LogCaptureFixture(FakeItem())
print("initial:", fx.handler.level)
fx.set_level(41)
print("after set_level(41):", fx.handler.level)
fx.set_level(43)
print("after set_level(43):", fx.handler.level)
fx._finalize()
restored = fx.handler.level
print("restored after finalize:", restored)
ok = (restored == 41)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2/2.3: logger-level save-and-restore. set_level on a named logger
# sets it during test and finalize restores original; first-call setdefault semantics.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key
class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}
name = "sbu_probe_logger_5"
lg = logging.getLogger(name)
lg.setLevel(logging.ERROR)  # original
orig = lg.level
fx = LogCaptureFixture(FakeItem())
fx.set_level(logging.DEBUG, logger=name)
during = lg.level
# second call to a different level; restore must go back to ORIGINAL (first recorded)
fx.set_level(logging.INFO, logger=name)
fx._finalize()
after = lg.level
print("orig:", orig, "during(DEBUG=10):", during, "after finalize:", after)
ok = (during == logging.DEBUG and after == orig == logging.ERROR)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2: at_level sets both logger and handler during block, restores both on exit.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key
class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}
name = "sbu_probe_logger_6"
lg = logging.getLogger(name)
lg.setLevel(logging.ERROR)
orig_lg = lg.level
fx = LogCaptureFixture(FakeItem())
fx.handler.setLevel(5)
orig_h = fx.handler.level
with fx.at_level(logging.DEBUG, logger=name):
    in_lg = lg.level
    in_h = fx.handler.level
out_lg = lg.level
out_h = fx.handler.level
print("logger during:", in_lg, "handler during:", in_h)
print("logger after:", out_lg, "(orig", orig_lg, ") handler after:", out_h, "(orig", orig_h, ")")
ok = (in_lg == logging.DEBUG and in_h == logging.DEBUG
      and out_lg == orig_lg and out_h == orig_h)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 4.1/4.3: records/record_tuples/messages/text expose captures; clear() resets them.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key
class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}
fx = LogCaptureFixture(FakeItem())
h = fx.handler
h.setLevel(0)
rec = logging.LogRecord("mylog", logging.WARNING, __file__, 1, "hello %s", ("world",), None)
h.emit(rec)
print("records:", len(fx.records))
print("record_tuples:", fx.record_tuples)
print("messages:", fx.messages)
print("text nonempty:", bool(fx.text))
rt_ok = fx.record_tuples == [("mylog", logging.WARNING, "hello world")]
msg_ok = fx.messages == ["hello world"]
pre_ok = (len(fx.records) == 1 and rt_ok and msg_ok and bool(fx.text))
fx.clear()
print("after clear -> records:", len(fx.records), "text repr:", repr(fx.text))
post_ok = (len(fx.records) == 0 and fx.text == "")
ok = pre_ok and post_ok
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.3/1.4/1.6 — after a test raises capture level via a
# single set_level starting from default 0, finalization restores handler level to 0.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key

class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}

fx = LogCaptureFixture(FakeItem())
start = fx.handler.level
print("initial handler level:", start)
fx.set_level(41)
print("after set_level(41):", fx.handler.level)
fx._finalize()
restored = fx.handler.level
print("after _finalize:", restored)
ok = (start == 0 and restored == 0)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance restores caplog capture-handler level in LogCaptureFixture._finalize. Probes exercise LogCaptureFixture directly with a fake item holding a _store[caplog_handler_key]=LogCaptureHandler(); stdlib + repo package only, no pytest.

Probe/criterion/result (all on gold-PATCHED tree unless noted):
PATCHED: HOLDS (0). BASE: FAILS (leaks 41). Discriminates.
- probe_2 (Req 1.2): set_level(WARNING) sets handler level to 30 during body. HOLDS.
- probe_3 (Req 1.5): a fixture that never called set_level -> _finalize must NOT touch handler level (pre-set 17 stays 17). PATCHED: HOLDS.
- probe_4 (Req 1.1/1.3 overwrite semantics): set_level(41) then set_level(43) from 0 -> _finalize restores the level in effect immediately before the LAST call = 41 (not the pre-test 0, not 43). PATCHED: HOLDS (41). BASE: FAILS (leaks 43).
- probe_5 (Req 2.1/2.2/2.3): named-logger set_level applied during test; first-call setdefault recording; _finalize restores original logger level. HOLDS.
- probe_6 (Req 3.1/3.2): at_level sets both logger and handler during block, restores both on exit. HOLDS.
- probe_7 (Req 4.1/4.3): records/record_tuples/messages/text expose captures with correct tuple shape; clear() empties records and text. HOLDS.

Candidate wrong-fixes (both REJECTED by suite => discriminating):
- weak_setdefault_first_call: records handler level with setdefault/first-call semantics instead of gold's plain-assignment overwrite. probe_4 REJECTS (restores 0 instead of the required 41). Note this candidate would still pass the single FAIL_TO_PASS hidden test (test1/test2/test3 each make exactly one set_level call), yet the requirements (Req 1.1 explicit overwrite/last-call semantics) forbid it -- probe_4 encodes that distinction and rejects it.
- weak_unconditional_reset_to_0: _finalize unconditionally sets handler level to 0. probe_3 REJECTS (mutates a never-set_level fixture's handler 17->0, violating Req 1.5) and probe_4 also REJECTS.

7/7 probes hold on patched; positive control fails at base and holds patched (prepatch reproduced); 2/2 wrong-fix candidates rejected by the suite. Note: meta.json records a separate G-PANEL-2 UNFAITHFUL flag about the two-call restore value (41 vs 0) -- that is a faithfulness observation about the gold patch's assignment semantics and is consistent with probe_4; the requirements (Req 1.1, Req 1.4 last sentence, Req 1.6) explicitly acknowledge the >1-call case restores the pre-last-call level, so the spec faithfully describes gold. G-EQ (spec-too-weak) is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.3/1.4/1.6 — after a test raises capture level via a
# single set_level starting from default 0, finalization restores handler level to 0.
import sys, logging
from _pytest.logging import LogCaptureFixture, LogCaptureHandler, caplog_handler_key

class FakeItem:
    def __init__(self):
        self._store = {caplog_handler_key: LogCaptureHandler()}

fx = LogCaptureFixture(FakeItem())
start = fx.handler.level
print("initial handler level:", start)
fx.set_level(41)
print("after set_level(41):", fx.handler.level)
fx._finalize()
restored = fx.handler.level
print("after _finalize:", restored)
ok = (start == 0 and restored == 0)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance restores caplog capture-handler level in LogCaptureFixture._finalize. Probes exercise LogCaptureFixture directly with a fake item holding a _store[caplog_handler_key]=LogCaptureHandler(); stdlib + repo package only, no pytest.

Probe/criterion/result (all on gold-PATCHED tree unless noted):
PATCHED: HOLDS (0). BASE: FAILS (leaks 41). Discriminates.
- probe_2 (Req 1.2): set_level(WARNING) sets handler level to 30 during body. HOLDS.
- probe_3 (Req 1.5): a fixture that never called set_level -> _finalize must NOT touch handler level (pre-set 17 stays 17). PATCHED: HOLDS.
- probe_4 (Req 1.1/1.3 overwrite semantics): set_level(41) then set_level(43) from 0 -> _finalize restores the level in effect immediately before the LAST call = 41 (not the pre-test 0, not 43). PATCHED: HOLDS (41). BASE: FAILS (leaks 43).
- probe_5 (Req 2.1/2.2/2.3): named-logger set_level applied during test; first-call setdefault recording; _finalize restores original logger level. HOLDS.
- probe_6 (Req 3.1/3.2): at_level sets both logger and handler during block, restores both on exit. HOLDS.
- probe_7 (Req 4.1/4.3): records/record_tuples/messages/text expose captures with correct tuple shape; clear() empties records and text. HOLDS.

Candidate wrong-fixes (both REJECTED by suite => discriminating):
- weak_setdefault_first_call: records handler level with setdefault/first-call semantics instead of gold's plain-assignment overwrite. probe_4 REJECTS (restores 0 instead of the required 41). Note this candidate would still pass the single FAIL_TO_PASS hidden test (test1/test2/test3 each make exactly one set_level call), yet the requirements (Req 1.1 explicit overwrite/last-call semantics) forbid it -- probe_4 encodes that distinction and rejects it.
- weak_unconditional_reset_to_0: _finalize unconditionally sets handler level to 0. probe_3 REJECTS (mutates a never-set_level fixture's handler 17->0, violating Req 1.5) and probe_4 also REJECTS.

7/7 probes hold on patched; positive control fails at base and holds patched (prepatch reproduced); 2/2 wrong-fix candidates rejected by the suite. Note: meta.json records a separate G-PANEL-2 UNFAITHFUL flag about the two-call restore value (41 vs 0) -- that is a faithfulness observation about the gold patch's assignment semantics and is consistent with probe_4; the requirements (Req 1.1, Req 1.4 last sentence, Req 1.6) explicitly acknowledge the >1-call case restores the pre-last-call level, so the spec faithfully describes gold. G-EQ (spec-too-weak) is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The meta.json shows a recorded G-PANEL-2=fail whose reasoning (assignment-not-setdefault, restores 41 not 0 for multi-call) was correct against an EARLIER version of requirements.md. The current requirements.md has been rewritten to explicitly and correctly describe this overwrite/last-call semantics (Req 1.1, 1.4, 1.6). No divergence remains between the current requirements and the patched code. G-PANEL-1 (spec adequacy) and G-EQ pass; G-PANEL-3 (leakage) passes. Verified via nl_attack probes on the gold-patched instance image: probe.py (single + multi set_level restore) exit 0; probe_atlevel.py (at_level dual restore, normal + exception) exit 0.

Counterexample / evidence:

```
Probe test1: set_level(41); set_level(43) -> test2 observes caplog.handler.level == 41 (not 0). This is exactly what Req 1.4/1.6 predict (restore to level before last call = 41), and the probe passes on the patched tree (exit 0). Single-call case: set_level(41) -> next test sees 0, per Req 1.4/1.6, also passes. at_level restore of both logger and handler levels (normal + exception exit) per Req 3 also probed and passes.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the fix to public/documented API (LogCaptureFixture, set_level, at_level, caplog.handler, _finalize, records/record_tuples/messages/text/get_records/clear) — legitimate. Numeric level `0` and the cross-test contamination scenario come straight from the public problem_statement. None of the hidden-test specifics leak: test names (test_change_level_undos_handler_level, test_change_level_undo), the test file path (testing/logging/test_fixture.py), the concrete levels used by the tests (41/43), Issue #7569, and the test1/test2/test3 structure are all absent. The gold-invented identifier `_initial_handler_level` is never named (referred to only as 'the value recorded in criterion 1'). The 'most recent set_level call'/overwrite-not-setdefault nuance is behavioral prose describing gold semantics for the multi-call case, which the hidden tests do NOT exercise (each test calls set_level at most once) — so it is not mirroring the parametrization. Requirement 4's API enumeration matches PASS_TO_PASS names but only lists documented fixture API, i.e. behavior not test content. Verdict: describes behavior, does not transmit the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
