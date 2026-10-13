# P2 adversarial audit — matplotlib__matplotlib-23299

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

Counterexample / evidence:

```
The weak candidate patch only deletes orig['backend'] on the NORMAL exit path (after yield), so when the rc_context block exits via an exception, the snapshotted backend value is still written back by dict.update(rcParams, orig). probe_4 (Req1 ac4 / Req3) catches this: it changes backend to 'module://zzz' inside a block that raises, and observes rcParams['backend'] reverted to 'module://aardvark' under the weak patch (VIOLATED) but correctly kept as 'module://zzz' under the gold patch (HOLDS).
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1 ac2 (positive control): backend changed inside rc_context is preserved after exit.
import matplotlib as mpl
from matplotlib import rc_context

assert mpl.rcParams['backend'] != 'module://aardvark'
with rc_context():
    mpl.rcParams['backend'] = 'module://aardvark'
after = mpl.rcParams['backend']
print("backend after ctx:", after)
assert after == 'module://aardvark', "backend was reset by rc_context"
print("OK: backend change preserved")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req2 ac1/ac2: non-backend values ARE reverted on normal exit.
import matplotlib as mpl
from matplotlib import rc_context

mpl.rcParams['lines.linewidth'] = 1.0
before = mpl.rcParams['lines.linewidth']
with rc_context():
    mpl.rcParams['lines.linewidth'] = 99.0
    assert mpl.rcParams['lines.linewidth'] == 99.0
after = mpl.rcParams['lines.linewidth']
print("linewidth before/after:", before, after)
assert after == before, "non-backend value not reverted"
print("OK: non-backend reverted")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1 ac3: backend NOT changed inside block retains its value (and is preserved, not reverted-away).
# Use a fake backend set BEFORE entering; inside we don't touch backend; after exit it must remain.
import matplotlib as mpl
from matplotlib import rc_context

mpl.rcParams['backend'] = 'module://aardvark'
with rc_context():
    mpl.rcParams['lines.linewidth'] = 5.0  # touch something else
after = mpl.rcParams['backend']
print("backend after (unchanged inside):", after)
assert after == 'module://aardvark', "backend value not retained"
print("OK: backend retained")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3 ac1/ac2 & Req2 ac3: on exception, non-backend reverted, backend preserved, exception propagates.
import matplotlib as mpl
from matplotlib import rc_context

mpl.rcParams['lines.linewidth'] = 2.0
before_lw = mpl.rcParams['lines.linewidth']
mpl.rcParams['backend'] = 'module://aardvark'

raised = False
try:
    with rc_context():
        mpl.rcParams['lines.linewidth'] = 42.0
        mpl.rcParams['backend'] = 'module://zzz'  # change backend too
        raise ValueError("boom")
except ValueError:
    raised = True

after_lw = mpl.rcParams['lines.linewidth']
after_be = mpl.rcParams['backend']
print("raised:", raised, "lw before/after:", before_lw, after_lw, "backend after:", after_be)
assert raised, "exception did not propagate"
assert after_lw == before_lw, "non-backend not reverted after exception"
# backend must NOT be reverted to pre-block value; it keeps whatever it was at exit
assert after_be == 'module://zzz', "backend was reset on exception path"
print("OK: exception path preserves backend, reverts others, propagates")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req4 ac1/ac2/ac3: get_backend() after creating a figure in rc_context must NOT drop Gcf figures,
# and figure must remain closable. Reproduces the original bug (issue #23298).
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import get_backend, rc_context
from matplotlib import _pylab_helpers as ph

# emulate the exact upstream reproducer
with rc_context():
    fig = plt.figure()
before = len(ph.Gcf.figs)
get_backend()
after = len(ph.Gcf.figs)
print("figs before/after get_backend:", before, after)
assert before == 1, "figure not registered"
assert after == before, "get_backend dropped figures from Gcf"
# closable
plt.close(fig)
print("figs after close:", len(ph.Gcf.figs))
assert len(ph.Gcf.figs) == 0, "figure not closable"
print("OK: Gcf intact, figure closable")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1 ac2 (positive control): backend changed inside rc_context is preserved after exit.
import matplotlib as mpl
from matplotlib import rc_context

assert mpl.rcParams['backend'] != 'module://aardvark'
with rc_context():
    mpl.rcParams['backend'] = 'module://aardvark'
after = mpl.rcParams['backend']
print("backend after ctx:", after)
assert after == 'module://aardvark', "backend was reset by rc_context"
print("OK: backend change preserved")
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib__matplotlib-23299: rc_context must not revert rcParams['backend']. Gold patch: orig = dict(rcParams.copy()); del orig['backend'] before the try, so the backend is excluded from the restore snapshot on BOTH normal and exception paths.

Probe results (patched / base / weak-candidate):
- probe_1 (Req1 ac2, POSITIVE CONTROL): backend changed to module://aardvark inside block is preserved after exit. HOLDS patched / VIOLATED base (AssertionError: backend was reset) / HOLDS weak. Discriminates base -> prepatch_reproduced=true.
- probe_2 (Req2 ac1/ac2): non-backend value lines.linewidth reverted on normal exit. HOLDS patched / HOLDS base / HOLDS weak. (regression 'SHALL keep' criterion)
- probe_3 (Req1 ac3): backend untouched inside block retains its pre-set value. HOLDS all trees.
- probe_4 (Req1 ac4 + Req2 ac3 + Req3 ac1/ac2): exception path — non-backend reverted, backend preserved, exception propagates. HOLDS patched / VIOLATED base / VIOLATED weak. This is the discriminating regression against the naive partial fix.
- probe_5 (Req4 ac1/ac2/ac3): figure created inside rc_context stays in Gcf across get_backend() and is closable. HOLDS all trees.

Note: probe_2/probe_3/probe_5 hold at base as well (the original bug in this env's rcParams representation does not manifest through get_backend the way the upstream issue described for probe_5's raw path; the real observable discriminator is the backend-reset on rc_context restore, captured by probe_1 and probe_4). The suite discriminates: positive control fails at base, and the weak requirements-plausible patch is rejected by probe_4. All 5 probes hold on the gold-patched tree.

Environment: used python; all runs completed cleanly (no timeouts/INCONCLUSIVE).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
The weak candidate patch only deletes orig['backend'] on the NORMAL exit path (after yield), so when the rc_context block exits via an exception, the snapshotted backend value is still written back by dict.update(rcParams, orig). probe_4 (Req1 ac4 / Req3) catches this: it changes backend to 'module://zzz' inside a block that raises, and observes rcParams['backend'] reverted to 'module://aardvark' under the weak patch (VIOLATED) but correctly kept as 'module://zzz' under the gold patch (HOLDS).
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1 ac2 (positive control): backend changed inside rc_context is preserved after exit.
import matplotlib as mpl
from matplotlib import rc_context

assert mpl.rcParams['backend'] != 'module://aardvark'
with rc_context():
    mpl.rcParams['backend'] = 'module://aardvark'
after = mpl.rcParams['backend']
print("backend after ctx:", after)
assert after == 'module://aardvark', "backend was reset by rc_context"
print("OK: backend change preserved")
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib__matplotlib-23299: rc_context must not revert rcParams['backend']. Gold patch: orig = dict(rcParams.copy()); del orig['backend'] before the try, so the backend is excluded from the restore snapshot on BOTH normal and exception paths.

Probe results (patched / base / weak-candidate):
- probe_1 (Req1 ac2, POSITIVE CONTROL): backend changed to module://aardvark inside block is preserved after exit. HOLDS patched / VIOLATED base (AssertionError: backend was reset) / HOLDS weak. Discriminates base -> prepatch_reproduced=true.
- probe_2 (Req2 ac1/ac2): non-backend value lines.linewidth reverted on normal exit. HOLDS patched / HOLDS base / HOLDS weak. (regression 'SHALL keep' criterion)
- probe_3 (Req1 ac3): backend untouched inside block retains its pre-set value. HOLDS all trees.
- probe_4 (Req1 ac4 + Req2 ac3 + Req3 ac1/ac2): exception path — non-backend reverted, backend preserved, exception propagates. HOLDS patched / VIOLATED base / VIOLATED weak. This is the discriminating regression against the naive partial fix.
- probe_5 (Req4 ac1/ac2/ac3): figure created inside rc_context stays in Gcf across get_backend() and is closable. HOLDS all trees.

Note: probe_2/probe_3/probe_5 hold at base as well (the original bug in this env's rcParams representation does not manifest through get_backend the way the upstream issue described for probe_5's raw path; the real observable discriminator is the backend-reset on rc_context restore, captured by probe_1 and probe_4). The suite discriminates: positive control fails at base, and the weak requirements-plausible patch is rejected by probe_4. All 5 probes hold on the gold-patched tree.

Environment: used python; all runs completed cleanly (no timeouts/INCONCLUSIVE).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: `orig = dict(rcParams.copy()); del orig['backend']` — the backend key is dropped from the snapshot that is restored, so on exit backend is never re-assigned while all other keys revert. Requirements pin exactly this observable boundary (backend excluded from restore; everything else reverted, including on exception), not a narrow helper/branch. Probe results — patched: R1.2=True('module://foo'), R2=True, R3=True, R4=True(1==1); base: R1.2=False('agg'), R2/R3/R4=True. R4's Gcf-clearing bug does not reproduce in the headless agg env (requires QtAgg/first-figure ordering) but R4 states the correct patched behavior and contradicts nothing; no invented/forbidden behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes rc_context behavior (preserve backend across restore, revert all other rcParams incl. exception path, keep Gcf figure registry intact when get_backend() is queried) entirely in behavioral EARS terms. All of this is derivable from the public problem_statement, which explicitly shows get_backend() clearing Gcf.figs for a figure created under rc_context and the plt.close consequence. Naming rc_context, rcParams, get_backend, _pylab_helpers.Gcf, and __init__.py is legitimate localization. No hidden-test artifacts leak: the sentinel value 'module://aardvark', the test names (test_no_backend_reset_rccontext, test_rcparams_reset_after_fail), FAIL_TO_PASS/PASS_TO_PASS ids, and the gold edit ('orig = dict(rcParams.copy()); del orig[\'backend\']') appear nowhere. Requirement enumerations reflect behavior, not the test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
