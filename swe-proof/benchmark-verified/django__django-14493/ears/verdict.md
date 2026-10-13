# P2 adversarial audit — django__django-14493

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
At base, post_process with max_post_process_passes=0 raises UnboundLocalError: local variable 'substitutions' referenced before assignment (probe_1 --base, exit 1). The weak_true candidate (initializing substitutions=True instead of False) is rejected by probe_1: with passes=0 it wrongly yields RuntimeError('Max post-process passes exceeded.'), violating R1.2/R2.3.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.1/R1.2/R2.3 positive control: max_post_process_passes=0 completes,
no UnboundLocalError, no 'Max post-process passes exceeded' RuntimeError.
HOLDS on patched, FAILS at base (UnboundLocalError)."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self, passes, initial, pass_substs):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = passes
        self._initial = initial
        self._pass_substs = pass_substs
        self.calls = 0

    def _post_process(self, paths, adjustable_paths, hashed_files):
        idx = self.calls
        self.calls += 1
        if idx == 0:
            for item in self._initial:
                yield item
        else:
            subst = self._pass_substs[idx - 1]
            yield ('a.css', 'a.deadbeef.css', True, subst)


s = Fake(passes=0, initial=[('a.css', 'a.deadbeef.css', True, False)], pass_substs=[])
try:
    results = list(s.post_process({}))
except UnboundLocalError as e:
    print("FAIL: UnboundLocalError raised:", e)
    sys.exit(1)
except Exception as e:
    print("FAIL: unexpected error:", type(e).__name__, e)
    sys.exit(1)

print("results:", results)
runtime_errs = [r for r in results if r[0] == 'All' and isinstance(r[2], RuntimeError)]
if runtime_errs:
    print("FAIL: RuntimeError('Max post-process passes exceeded') yielded with passes=0")
    sys.exit(1)
print("OK: passes=0 completed cleanly, no max-passes RuntimeError")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.4: with passes=0, the initial single pass still runs and every
adjustable file is yielded under its final hashed name."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = 0
        self.calls = 0

    def _post_process(self, paths, adjustable_paths, hashed_files):
        self.calls += 1
        # simulate the single initial pass output
        hashed_files['x'] = 'style.abc123.css'
        yield ('style.css', 'style.abc123.css', True, False)


s = Fake()
results = list(s.post_process({'style.css': (None, 'style.css')}))
print("calls:", s.calls, "results:", results)
if s.calls < 1:
    print("FAIL: initial pass not performed")
    sys.exit(1)
names = {r[0]: r[1] for r in results if not isinstance(r[2], Exception)}
if names.get('style.css') != 'style.abc123.css':
    print("FAIL: adjustable file not yielded under hashed name")
    sys.exit(1)
print("OK: initial pass ran and file yielded under hashed name")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R3.2/R3.4: a refinement pass producing no substitutions stops the loop
immediately (before exhausting passes) and does NOT yield max-passes error."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = 5
        self.calls = 0

    def _post_process(self, paths, adjustable_paths, hashed_files):
        idx = self.calls
        self.calls += 1
        if idx == 0:
            yield ('a.css', 'a.h.css', True, False)  # initial
        else:
            # first refinement pass reports NO substitution -> should stop
            yield ('a.css', 'a.h.css', True, False)


s = Fake()
results = list(s.post_process({}))
print("calls:", s.calls, "results:", results)
# initial(1) + exactly one refinement pass then break = 2
if s.calls != 2:
    print("FAIL: loop did not stop early; calls=", s.calls)
    sys.exit(1)
if any(r[0] == 'All' and isinstance(r[2], RuntimeError) for r in results):
    print("FAIL: max-passes error yielded despite convergence")
    sys.exit(1)
print("OK: early-stop on no substitutions, no error")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.3: if the loop runs the full max_post_process_passes and the final
executed pass still produced substitutions, post_process yields
'All', None, RuntimeError('Max post-process passes exceeded.')."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = 2
        self.calls = 0

    def _post_process(self, paths, adjustable_paths, hashed_files):
        idx = self.calls
        self.calls += 1
        if idx == 0:
            yield ('a.css', 'a.h.css', True, True)  # initial
        else:
            yield ('a.css', 'a.h.css', True, True)  # always substituting


s = Fake()
results = list(s.post_process({}))
print("calls:", s.calls, "results:", results)
# initial + 2 passes = 3
if s.calls != 3:
    print("FAIL: expected full 2 passes (calls=3), got", s.calls)
    sys.exit(1)
errs = [r for r in results if r[0] == 'All' and r[1] is None and isinstance(r[2], RuntimeError)]
if not errs:
    print("FAIL: max-passes RuntimeError not yielded")
    sys.exit(1)
if 'Max post-process passes exceeded.' not in str(errs[0][2]):
    print("FAIL: wrong error message:", errs[0][2])
    sys.exit(1)
print("OK: max-passes RuntimeError yielded correctly")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R2.2/R3.4: loop executes multiple passes; final pass has no substitution
-> converges, no error. Distinguishes 'always error' wrong fixes."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = 5
        self.calls = 0
        self.pass_substs = [True, True, False]

    def _post_process(self, paths, adjustable_paths, hashed_files):
        idx = self.calls
        self.calls += 1
        if idx == 0:
            yield ('a.css', 'a.h.css', True, True)
        else:
            yield ('a.css', 'a.h.css', True, self.pass_substs[idx - 1])


s = Fake()
results = list(s.post_process({}))
print("calls:", s.calls, "results:", results)
# initial + 3 passes (True,True,False->break) = 4
if s.calls != 4:
    print("FAIL: expected calls=4, got", s.calls)
    sys.exit(1)
if any(r[0] == 'All' and isinstance(r[2], RuntimeError) for r in results):
    print("FAIL: error yielded despite eventual convergence")
    sys.exit(1)
print("OK: converged after final no-subst pass, no error")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.5: non-adjustable files and per-file exceptions from the initial pass
are yielded, and self.hashed_files is updated with the mapping. Checked with
passes=0 to ensure these outputs are preserved even without refinement."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = 0
        self.calls = 0

    def _post_process(self, paths, adjustable_paths, hashed_files):
        self.calls += 1
        hashed_files['k'] = 'img.deadbeef.png'
        yield ('img.png', 'img.deadbeef.png', True, False)      # non-adjustable
        yield ('bad.css', None, ValueError('boom'), False)      # per-file exc


s = Fake()
results = list(s.post_process({}))
print("results:", results, "hashed_files:", s.hashed_files)
got_nonadj = any(r[0] == 'img.png' and r[1] == 'img.deadbeef.png' for r in results)
got_exc = any(r[0] == 'bad.css' and isinstance(r[2], ValueError) for r in results)
if not got_nonadj:
    print("FAIL: non-adjustable file not yielded")
    sys.exit(1)
if not got_exc:
    print("FAIL: per-file exception not yielded")
    sys.exit(1)
if s.hashed_files.get('k') != 'img.deadbeef.png':
    print("FAIL: hashed_files mapping not updated")
    sys.exit(1)
print("OK: non-adjustable + exception yielded and mapping updated")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.2/R2.3 positive control: max_post_process_passes=0 completes,
no UnboundLocalError, no 'Max post-process passes exceeded' RuntimeError.
HOLDS on patched, FAILS at base (UnboundLocalError)."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self, passes, initial, pass_substs):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = passes
        self._initial = initial
        self._pass_substs = pass_substs
        self.calls = 0

    def _post_process(self, paths, adjustable_paths, hashed_files):
        idx = self.calls
        self.calls += 1
        if idx == 0:
            for item in self._initial:
                yield item
        else:
            subst = self._pass_substs[idx - 1]
            yield ('a.css', 'a.deadbeef.css', True, subst)


s = Fake(passes=0, initial=[('a.css', 'a.deadbeef.css', True, False)], pass_substs=[])
try:
    results = list(s.post_process({}))
except UnboundLocalError as e:
    print("FAIL: UnboundLocalError raised:", e)
    sys.exit(1)
except Exception as e:
    print("FAIL: unexpected error:", type(e).__name__, e)
    sys.exit(1)

print("results:", results)
runtime_errs = [r for r in results if r[0] == 'All' and isinstance(r[2], RuntimeError)]
if runtime_errs:
    print("FAIL: RuntimeError('Max post-process passes exceeded') yielded with passes=0")
    sys.exit(1)
print("OK: passes=0 completed cleanly, no max-passes RuntimeError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover: R1.1/R1.2/R2.3 (probe_1, positive control) passes=0 completes with no UnboundLocalError and no max-passes RuntimeError; R1.4 (probe_2) initial pass still runs and adjustable file yielded under hashed name at passes=0; R3.2/R3.4 (probe_3) early-stop on no-subst pass, no error; R3.3 (probe_4) full passes with final subst -> yields 'All',None,RuntimeError; R2.2/R3.4 (probe_5) multi-pass eventual convergence -> no error; R3.5 (probe_6) non-adjustable files + per-file exceptions yielded and hashed_files mapping updated. All 6 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (UnboundLocalError) and HOLDS patched => discriminating. Candidate weak_true (substitutions=True init) is REJECTED by probe_1 => suite discriminates a plausible wrong reading. Candidate weak_try (wrapping the final check in try/except NameError) passes all probes, but UnboundLocalError IS a NameError subclass so this is a genuinely correct alternative fix, not a too-weak-spec finding; it too resolves the bug. No requirements-conforming patch found that fails the hidden behavior. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
At base, post_process with max_post_process_passes=0 raises UnboundLocalError: local variable 'substitutions' referenced before assignment (probe_1 --base, exit 1). The weak_true candidate (initializing substitutions=True instead of False) is rejected by probe_1: with passes=0 it wrongly yields RuntimeError('Max post-process passes exceeded.'), violating R1.2/R2.3.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.2/R2.3 positive control: max_post_process_passes=0 completes,
no UnboundLocalError, no 'Max post-process passes exceeded' RuntimeError.
HOLDS on patched, FAILS at base (UnboundLocalError)."""
import sys
from django.contrib.staticfiles.storage import HashedFilesMixin


class Fake(HashedFilesMixin):
    def __init__(self, passes, initial, pass_substs):
        self.hashed_files = {}
        self._patterns = {}
        self.max_post_process_passes = passes
        self._initial = initial
        self._pass_substs = pass_substs
        self.calls = 0

    def _post_process(self, paths, adjustable_paths, hashed_files):
        idx = self.calls
        self.calls += 1
        if idx == 0:
            for item in self._initial:
                yield item
        else:
            subst = self._pass_substs[idx - 1]
            yield ('a.css', 'a.deadbeef.css', True, subst)


s = Fake(passes=0, initial=[('a.css', 'a.deadbeef.css', True, False)], pass_substs=[])
try:
    results = list(s.post_process({}))
except UnboundLocalError as e:
    print("FAIL: UnboundLocalError raised:", e)
    sys.exit(1)
except Exception as e:
    print("FAIL: unexpected error:", type(e).__name__, e)
    sys.exit(1)

print("results:", results)
runtime_errs = [r for r in results if r[0] == 'All' and isinstance(r[2], RuntimeError)]
if runtime_errs:
    print("FAIL: RuntimeError('Max post-process passes exceeded') yielded with passes=0")
    sys.exit(1)
print("OK: passes=0 completed cleanly, no max-passes RuntimeError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover: R1.1/R1.2/R2.3 (probe_1, positive control) passes=0 completes with no UnboundLocalError and no max-passes RuntimeError; R1.4 (probe_2) initial pass still runs and adjustable file yielded under hashed name at passes=0; R3.2/R3.4 (probe_3) early-stop on no-subst pass, no error; R3.3 (probe_4) full passes with final subst -> yields 'All',None,RuntimeError; R2.2/R3.4 (probe_5) multi-pass eventual convergence -> no error; R3.5 (probe_6) non-adjustable files + per-file exceptions yielded and hashed_files mapping updated. All 6 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (UnboundLocalError) and HOLDS patched => discriminating. Candidate weak_true (substitutions=True init) is REJECTED by probe_1 => suite discriminates a plausible wrong reading. Candidate weak_try (wrapping the final check in try/except NameError) passes all probes, but UnboundLocalError IS a NameError subclass so this is a genuinely correct alternative fix, not a too-weak-spec finding; it too resolves the bug. No requirements-conforming patch found that fails the hidden behavior. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is exactly one line: `substitutions = False` inserted immediately before the refinement `for` loop (source L39). Probe of HashedFilesMixin.post_process source confirms L39 addition; loop body still contains `substitutions = False` re-init (L~40) and `substitutions = substitutions or subst` (L46), early break at L48-49, and the post-loop `if substitutions` RuntimeError at L51-52 all intact. Base-commit probe with max_post_process_passes=0 raises UnboundLocalError; patched returns normally — the modeling boundary (behavior at passes=0 plus preservation for positive limits) is exactly the changed observable behavior, not a narrow slice. Requirements neither mandate absent behavior nor forbid present behavior nor invent behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable entirely from the PUBLIC problem_statement. The problem_statement already contains: the crash (UnboundLocalError on `substitutions`), the traceback showing `if substitutions:` at storage.py, the fact that `substitutions` is only set inside the loop, `max_post_process_passes = 0`, `ManifestStaticFilesStorage`/`post_process`, and the reproduction via a subclass. The gold edit merely adds `substitutions = False` before the loop — an identifier already public in the traceback; the doc invents no new identifier. No test file paths, test class/function names (e.g. NoPostProcessReplacedPathStorage / test_collectstatistic_no_post_process_replaced_paths), or parametrization ids appear. Req 1.3's phrase that the command's output 'SHALL report that files were post-processed' loosely parallels the hidden test assertion (`assertIn('post-processed', stdout.getvalue())`), but 'post-processed' is the natural, user-visible collectstatic output term and this is a behavioral description, not transmission of the test. Localizing the change to storage.py/HashedFilesMixin.post_process and naming the pre-existing `substitutions`/`max_post_process_passes` is legitimate. No reconstruction of the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
