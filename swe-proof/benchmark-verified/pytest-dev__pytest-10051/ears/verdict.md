# P2 adversarial audit — pytest-dev__pytest-10051

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
"""POSITIVE CONTROL. Req1 crit 4 (+3): after caplog.clear() during "call",
get_records("call") and caplog.records still refer to the SAME underlying
collection and are equal (both empty). FAILS at base (reset detaches the
per-phase view onto an orphaned list), HOLDS patched.
"""
import logging, sys
from _pytest.logging import (LogCaptureHandler, LogCaptureFixture,
                             caplog_handler_key, caplog_records_key)
from _pytest.stash import Stash


class _Item:
    def __init__(self): self.stash = Stash()


def begin(handler, item, when):
    handler.reset()
    item.stash[caplog_records_key][when] = handler.records


def emit(h, name, msg, lvl=logging.INFO):
    h.emit(logging.LogRecord(name, lvl, "p.py", 1, msg, None, None))


item = _Item()
h = LogCaptureHandler()
item.stash[caplog_handler_key] = h
item.stash[caplog_records_key] = {}
fix = LogCaptureFixture(item, _ispytest=True)

begin(h, item, "call")
emit(h, "x", "before1")
emit(h, "x", "before2")

# invariant before clear
assert fix.get_records("call") == fix.records, "pre-clear not equal"
assert fix.get_records("call") is fix.records, "pre-clear not same object"

fix.clear()

recs = fix.records
gr = fix.get_records("call")
print("after clear: records=%r get_records=%r same_obj=%s" % (recs, gr, gr is recs))

ok = (recs == []) and (gr == []) and (gr == recs)
if not ok:
    print("FAIL: views diverged after clear")
    sys.exit(1)
print("HOLDS: get_records('call') stays coupled to records across clear")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1 crit 5 & 6: a message logged AFTER clear during "call" appears in
BOTH caplog.records and get_records("call"); get_records reflects EXACTLY the
post-clear records in order and NONE captured before the clear.
FAILS at base (get_records still points at orphaned pre-clear list).
"""
import logging, sys
from _pytest.logging import (LogCaptureHandler, LogCaptureFixture,
                             caplog_handler_key, caplog_records_key)
from _pytest.stash import Stash


class _Item:
    def __init__(self): self.stash = Stash()


def begin(handler, item, when):
    handler.reset()
    item.stash[caplog_records_key][when] = handler.records


def emit(h, name, msg, lvl=logging.INFO):
    h.emit(logging.LogRecord(name, lvl, "p.py", 1, msg, None, None))


item = _Item()
h = LogCaptureHandler()
item.stash[caplog_handler_key] = h
item.stash[caplog_records_key] = {}
fix = LogCaptureFixture(item, _ispytest=True)

begin(h, item, "call")
emit(h, "x", "old-A")
emit(h, "x", "old-B")
fix.clear()
emit(h, "x", "new-1")
emit(h, "x", "new-2")

recs_msgs = [r.getMessage() for r in fix.records]
gr_msgs = [r.getMessage() for r in fix.get_records("call")]
print("records=%r get_records('call')=%r" % (recs_msgs, gr_msgs))

expected = ["new-1", "new-2"]
ok = (recs_msgs == expected) and (gr_msgs == expected)
if not ok:
    print("FAIL: post-clear logging not reflected identically in both views")
    sys.exit(1)
print("HOLDS: both views show exactly post-clear records in order")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2 crit 1 & 3: clear() during "call" leaves get_records("setup")
records UNCHANGED (same records, same order, same identity). Also Req2 crit 2:
the set of tracked phase names is unchanged across clear().
"""
import logging, sys
from _pytest.logging import (LogCaptureHandler, LogCaptureFixture,
                             caplog_handler_key, caplog_records_key)
from _pytest.stash import Stash


class _Item:
    def __init__(self): self.stash = Stash()


def begin(handler, item, when):
    handler.reset()
    item.stash[caplog_records_key][when] = handler.records


def emit(h, name, msg, lvl=logging.INFO):
    h.emit(logging.LogRecord(name, lvl, "p.py", 1, msg, None, None))


item = _Item()
h = LogCaptureHandler()
item.stash[caplog_handler_key] = h
item.stash[caplog_records_key] = {}
fix = LogCaptureFixture(item, _ispytest=True)

# setup phase
begin(h, item, "setup")
emit(h, "s", "setup-1")
emit(h, "s", "setup-2")
setup_before = list(fix.get_records("setup"))
setup_before_obj = item.stash[caplog_records_key]["setup"]

# call phase
begin(h, item, "call")
emit(h, "c", "call-1")

keys_before = set(item.stash[caplog_records_key].keys())
fix.clear()
keys_after = set(item.stash[caplog_records_key].keys())

setup_after = list(fix.get_records("setup"))
setup_after_obj = item.stash[caplog_records_key]["setup"]

print("setup before=%r after=%r same_obj=%s keys_before=%s keys_after=%s" % (
    [r.getMessage() for r in setup_before],
    [r.getMessage() for r in setup_after],
    setup_after_obj is setup_before_obj, keys_before, keys_after))

ok = (setup_after == setup_before
      and [r.getMessage() for r in setup_after] == ["setup-1", "setup-2"]
      and setup_after_obj is setup_before_obj
      and keys_before == keys_after == {"setup", "call"})
if not ok:
    print("FAIL: clear() disturbed other-phase records or phase keys")
    sys.exit(1)
print("HOLDS: other-phase records and phase keys untouched by clear")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3 crit 1,2,3: clear() empties records AND resets caplog.text to empty;
after clear, records/record_tuples/messages reflect only new messages.
(Regression: existing documented clear semantics preserved.)
"""
import logging, sys
from _pytest.logging import (LogCaptureHandler, LogCaptureFixture,
                             caplog_handler_key, caplog_records_key)
from _pytest.stash import Stash


class _Item:
    def __init__(self): self.stash = Stash()


def begin(handler, item, when):
    handler.reset()
    item.stash[caplog_records_key][when] = handler.records


def emit(h, name, msg, lvl=logging.INFO):
    rec = logging.LogRecord(name, lvl, "p.py", 1, msg, None, None)
    h.emit(rec)


item = _Item()
h = LogCaptureHandler()
item.stash[caplog_handler_key] = h
item.stash[caplog_records_key] = {}
fix = LogCaptureFixture(item, _ispytest=True)

begin(h, item, "call")
emit(h, "log", "hello-old")
assert fix.records, "precondition: should have a record"
assert fix.text != "", "precondition: text should be non-empty"

fix.clear()
print("post-clear: records=%r text=%r" % (fix.records, fix.text))
if fix.records != []:
    print("FAIL: records not emptied"); sys.exit(1)
if fix.text != "":
    print("FAIL: text not reset to empty"); sys.exit(1)

emit(h, "log", "hello-new")
msgs = fix.messages
tuples = fix.record_tuples
print("after new log: messages=%r record_tuples=%r" % (msgs, tuples))
ok = (msgs == ["hello-new"]
      and tuples == [("log", logging.INFO, "hello-new")]
      and "hello-new" in fix.text
      and "hello-old" not in fix.text)
if not ok:
    print("FAIL: post-clear views leaked old messages or missed new"); sys.exit(1)
print("HOLDS: clear resets records+text; new messages reflected, old gone")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4 crit 4: when logging.raiseExceptions is enabled, the capture handler
SHALL surface an emit error (handleError re-raises) rather than swallowing it.
Also Req4 crit 1: normal records/record_tuples/messages/text capture works.
"""
import logging, sys
from _pytest.logging import LogCaptureHandler

# --- crit 4: handleError re-raises under raiseExceptions ---
h = LogCaptureHandler()
saved = logging.raiseExceptions
logging.raiseExceptions = True
surfaced = False
try:
    try:
        raise ValueError("boom-during-emit")
    except ValueError:
        # emulate logging's flow: an exception occurred formatting/emitting a
        # record, logging calls handler.handleError(record) inside the except.
        rec = logging.LogRecord("e", logging.ERROR, "p.py", 1, "m", None, None)
        h.handleError(rec)
except ValueError as e:
    surfaced = ("boom-during-emit" in str(e))
finally:
    logging.raiseExceptions = saved
print("emit error surfaced=%s" % surfaced)
if not surfaced:
    print("FAIL: handleError swallowed the emit error"); sys.exit(1)

# --- crit 1: normal capture still works ---
h2 = LogCaptureHandler()
h2.setFormatter(logging.Formatter("%(name)s %(message)s"))
for m in ("a", "b"):
    h2.emit(logging.LogRecord("cap", logging.WARNING, "p.py", 1, m, None, None))
tuples = [(r.name, r.levelno, r.getMessage()) for r in h2.records]
msgs = [r.getMessage() for r in h2.records]
text = h2.stream.getvalue()
print("records=%d tuples=%r msgs=%r text_has_a=%s" % (
    len(h2.records), tuples, msgs, "a" in text))
ok = (len(h2.records) == 2
      and tuples == [("cap", logging.WARNING, "a"), ("cap", logging.WARNING, "b")]
      and msgs == ["a", "b"] and "a" in text and "b" in text)
if not ok:
    print("FAIL: normal capture regressed"); sys.exit(1)
print("HOLDS: emit errors surfaced; normal capture intact")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL. Req1 crit 4 (+3): after caplog.clear() during "call",
get_records("call") and caplog.records still refer to the SAME underlying
collection and are equal (both empty). FAILS at base (reset detaches the
per-phase view onto an orphaned list), HOLDS patched.
"""
import logging, sys
from _pytest.logging import (LogCaptureHandler, LogCaptureFixture,
                             caplog_handler_key, caplog_records_key)
from _pytest.stash import Stash


class _Item:
    def __init__(self): self.stash = Stash()


def begin(handler, item, when):
    handler.reset()
    item.stash[caplog_records_key][when] = handler.records


def emit(h, name, msg, lvl=logging.INFO):
    h.emit(logging.LogRecord(name, lvl, "p.py", 1, msg, None, None))


item = _Item()
h = LogCaptureHandler()
item.stash[caplog_handler_key] = h
item.stash[caplog_records_key] = {}
fix = LogCaptureFixture(item, _ispytest=True)

begin(h, item, "call")
emit(h, "x", "before1")
emit(h, "x", "before2")

# invariant before clear
assert fix.get_records("call") == fix.records, "pre-clear not equal"
assert fix.get_records("call") is fix.records, "pre-clear not same object"

fix.clear()

recs = fix.records
gr = fix.get_records("call")
print("after clear: records=%r get_records=%r same_obj=%s" % (recs, gr, gr is recs))

ok = (recs == []) and (gr == []) and (gr == recs)
if not ok:
    print("FAIL: views diverged after clear")
    sys.exit(1)
print("HOLDS: get_records('call') stays coupled to records across clear")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-10051: caplog.clear() must empty records in place (not replace the list) so get_records(<current phase>) stays coupled to caplog.records. FAIL_TO_PASS: test_clear_for_call_stage.

Probes (all run in instance image; simulate _pytest.logging._runtest_for wiring — handler.reset() at phase start, handler.records bound into caplog_records_key[when]):
- probe_1 (Req1 crit 3,4; POSITIVE CONTROL): after clear() during 'call', records and get_records('call') are equal, empty, and same object. PATCHED: HOLDS (same_obj=True, both []). BASE: VIOLATED (get_records still shows before1/before2, same_obj=False). Discriminates.
- probe_2 (Req1 crit 5,6): message logged after clear appears identically in both views, exactly post-clear records in order, no pre-clear records. PATCHED HOLDS; BASE would fail (get_records keeps old list).
- probe_3 (Req2 crit 1,2,3): clear() during 'call' leaves get_records('setup') records unchanged (same identity/order) and phase-key set {'setup','call'} unchanged. PATCHED HOLDS.
- probe_4 (Req3 crit 1,2,3): clear() empties records AND resets text to ''; post-clear record_tuples/messages/text reflect only new messages. PATCHED HOLDS.
- probe_5 (Req4 crit 1,4): handleError re-raises the emit error under logging.raiseExceptions; normal records/record_tuples capture intact. PATCHED HOLDS.

Candidate patch (weak_partial.diff): the partial/lazy fix — adds LogCaptureHandler.clear() (records.clear() in place) but does NOT rewire the fixture, so LogCaptureFixture.clear() still calls handler.reset() which replaces the list. Applies cleanly at base_commit. Under this candidate: probe_1 REJECTED (same_obj=False, get_records keeps old records) and probe_2 REJECTED (records=[new-1,new-2] but get_records('call')=[old-A,old-B]). probes 3/4/5 hold. This demonstrates the suite discriminates the wrong fix and would not resolve the hidden test — the alternative is correctly rejected, not a too-weak finding.

All 5 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced). Verdict SOUND.

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
"""POSITIVE CONTROL. Req1 crit 4 (+3): after caplog.clear() during "call",
get_records("call") and caplog.records still refer to the SAME underlying
collection and are equal (both empty). FAILS at base (reset detaches the
per-phase view onto an orphaned list), HOLDS patched.
"""
import logging, sys
from _pytest.logging import (LogCaptureHandler, LogCaptureFixture,
                             caplog_handler_key, caplog_records_key)
from _pytest.stash import Stash


class _Item:
    def __init__(self): self.stash = Stash()


def begin(handler, item, when):
    handler.reset()
    item.stash[caplog_records_key][when] = handler.records


def emit(h, name, msg, lvl=logging.INFO):
    h.emit(logging.LogRecord(name, lvl, "p.py", 1, msg, None, None))


item = _Item()
h = LogCaptureHandler()
item.stash[caplog_handler_key] = h
item.stash[caplog_records_key] = {}
fix = LogCaptureFixture(item, _ispytest=True)

begin(h, item, "call")
emit(h, "x", "before1")
emit(h, "x", "before2")

# invariant before clear
assert fix.get_records("call") == fix.records, "pre-clear not equal"
assert fix.get_records("call") is fix.records, "pre-clear not same object"

fix.clear()

recs = fix.records
gr = fix.get_records("call")
print("after clear: records=%r get_records=%r same_obj=%s" % (recs, gr, gr is recs))

ok = (recs == []) and (gr == []) and (gr == recs)
if not ok:
    print("FAIL: views diverged after clear")
    sys.exit(1)
print("HOLDS: get_records('call') stays coupled to records across clear")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-10051: caplog.clear() must empty records in place (not replace the list) so get_records(<current phase>) stays coupled to caplog.records. FAIL_TO_PASS: test_clear_for_call_stage.

Probes (all run in instance image; simulate _pytest.logging._runtest_for wiring — handler.reset() at phase start, handler.records bound into caplog_records_key[when]):
- probe_1 (Req1 crit 3,4; POSITIVE CONTROL): after clear() during 'call', records and get_records('call') are equal, empty, and same object. PATCHED: HOLDS (same_obj=True, both []). BASE: VIOLATED (get_records still shows before1/before2, same_obj=False). Discriminates.
- probe_2 (Req1 crit 5,6): message logged after clear appears identically in both views, exactly post-clear records in order, no pre-clear records. PATCHED HOLDS; BASE would fail (get_records keeps old list).
- probe_3 (Req2 crit 1,2,3): clear() during 'call' leaves get_records('setup') records unchanged (same identity/order) and phase-key set {'setup','call'} unchanged. PATCHED HOLDS.
- probe_4 (Req3 crit 1,2,3): clear() empties records AND resets text to ''; post-clear record_tuples/messages/text reflect only new messages. PATCHED HOLDS.
- probe_5 (Req4 crit 1,4): handleError re-raises the emit error under logging.raiseExceptions; normal records/record_tuples capture intact. PATCHED HOLDS.

Candidate patch (weak_partial.diff): the partial/lazy fix — adds LogCaptureHandler.clear() (records.clear() in place) but does NOT rewire the fixture, so LogCaptureFixture.clear() still calls handler.reset() which replaces the list. Applies cleanly at base_commit. Under this candidate: probe_1 REJECTED (same_obj=False, get_records keeps old records) and probe_2 REJECTED (records=[new-1,new-2] but get_records('call')=[old-A,old-B]). probes 3/4/5 hold. This demonstrates the suite discriminates the wrong fix and would not resolve the hidden test — the alternative is correctly rejected, not a too-weak finding.

All 5 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: adds LogCaptureHandler.clear() (records.clear() + new StringIO) and points LogCaptureFixture.clear() at it instead of reset(). FAIL_TO_PASS test_clear_for_call_stage matches R1's invariant. Probe on gold-patched image exit=0 (SAME_OBJ_BEFORE True, ALL_OK); on base exit=1 (diverged after clear). Boundary is correct: requirements pin the changed observable coupling, not a single branch/helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document stays within the public problem_statement plus legitimate source localization. The problem_statement already exposes the caplog.get_records()/caplog.clear() divergence, the 'call' phase, the replace-not-clear defect, and the logging.py source locations. All identifiers named (LogCaptureFixture, LogCaptureHandler, reset(), clear(), caplog_records_key, the get_records phase names setup/call/teardown) are real public/source symbols used to localize the change; none are fix-invented. The gold's new handler.clear() delegation is described behaviorally. The hidden test's literal artifacts are NOT present: message strings ('a_call_log', 'a_setup_log', 'a_call_log_after_clear'), the test function name test_clear_for_call_stage, the file path testing/logging/test_fixture.py, and the fixture logging_during_setup_and_teardown all absent. Req 2 / Req 4-AC5 mention leaving 'setup' records untouched and tracked phase names {setup, call}, which parallels the test's stash-key assertion, but these are stated as behavioral invariants (natural consequences of clearing during one phase), not as a transcription of the test parametrization — this is the intended translation of test checks into requirements, not a leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
