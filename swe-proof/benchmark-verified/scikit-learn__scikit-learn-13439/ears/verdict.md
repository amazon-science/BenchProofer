# P2 adversarial audit — scikit-learn__scikit-learn-13439

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate patch defines __len__ as sum(1 for _ in self._iter()), counting only non-None/non-'passthrough' steps. On a 5-step pipeline containing a None and a 'passthrough' entry it returns 3 instead of 5 — probe_2 REJECTS it (VIOLATED: len=3 expected 5). This confirms the probe suite discriminates the requirement R1.2/R1.3 mandate that len counts EVERY entry.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1: len(pipe) == len(pipe.steps), returns int, no TypeError. Positive control."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA()), ('clf', LogisticRegression())])
try:
    n = len(pipe)
except TypeError as e:
    print("FAIL: len() raised TypeError:", e)
    sys.exit(1)
print("len(pipe) =", n, "len(pipe.steps) =", len(pipe.steps), "type =", type(n).__name__)
if not isinstance(n, int):
    print("FAIL: not int")
    sys.exit(1)
if n != len(pipe.steps) or n != 3:
    print("FAIL: mismatch")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2/1.3: counts every entry incl None and 'passthrough', no dedup/drop."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

# entries with None and 'passthrough' estimators
steps = [('a', StandardScaler()), ('b', None), ('c', 'passthrough'),
         ('d', PCA()), ('e', LogisticRegression())]
pipe = Pipeline(steps)
n = len(pipe)
print("len =", n, "expected 5; steps len =", len(pipe.steps))
if n != 5 or n != len(pipe.steps):
    print("FAIL")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2: pipe[:len(pipe)] returns Pipeline with all original steps; length-derived slice."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

steps = [('scaler', StandardScaler()), ('pca', PCA()), ('clf', LogisticRegression())]
pipe = Pipeline(steps)
full = pipe[:len(pipe)]
if not isinstance(full, Pipeline):
    print("FAIL: not Pipeline"); sys.exit(1)
if full.steps != pipe.steps:
    print("FAIL: steps differ", full.steps); sys.exit(1)
# a length-derived sub-slice
half = pipe[:len(pipe)-1]
if not isinstance(half, Pipeline) or half.steps != pipe.steps[:2]:
    print("FAIL: sub-slice", getattr(half,'steps',half)); sys.exit(1)
print("OK: full.steps==pipe.steps, half==first2")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1/3.2/3.3: int index -> estimator; name -> estimator; slice -> Pipeline."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

sc, pca, clf = StandardScaler(), PCA(), LogisticRegression()
pipe = Pipeline([('scaler', sc), ('pca', pca), ('clf', clf)])

# integer positive
assert pipe[0] is sc, "int0"
# integer negative
assert pipe[-1] is clf, "int neg"
# name lookup
assert pipe['pca'] is pca, "name"
# slice -> Pipeline
s = pipe[1:3]
assert isinstance(s, Pipeline) and s.steps == pipe.steps[1:3], "slice"
print("OK: int/neg/name/slice all correct")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.4/3.5/3.6: error behavior preserved — step!=1 slice ValueError, OOR IndexError, bad name KeyError."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA()), ('clf', LogisticRegression())])

def expect(exc, fn, label):
    try:
        fn()
    except exc:
        print("OK:", label, "raised", exc.__name__)
        return True
    except Exception as e:
        print("FAIL:", label, "raised", type(e).__name__, "not", exc.__name__)
        return False
    print("FAIL:", label, "did not raise")
    return False

ok = True
ok &= expect(ValueError, lambda: pipe[::-1], "reversed slice")
ok &= expect(ValueError, lambda: pipe[::2], "step-2 slice")
ok &= expect(IndexError, lambda: pipe[10], "out-of-range int")
ok &= expect(KeyError, lambda: pipe['nope'], "missing name")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.7: named_steps unchanged — count of accessible named steps equals steps count."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA()), ('clf', LogisticRegression())])
names = list(pipe.named_steps.keys())
print("named_steps:", names)
if set(names) != {'scaler', 'pca', 'clf'}:
    print("FAIL: names"); sys.exit(1)
if len(names) != 3:
    print("FAIL: count"); sys.exit(1)
# named_steps returns the right objects
if pipe.named_steps['pca'] is not pipe['pca']:
    print("FAIL: named_steps object mismatch"); sys.exit(1)
print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1: len(pipe) == len(pipe.steps), returns int, no TypeError. Positive control."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA()), ('clf', LogisticRegression())])
try:
    n = len(pipe)
except TypeError as e:
    print("FAIL: len() raised TypeError:", e)
    sys.exit(1)
print("len(pipe) =", n, "len(pipe.steps) =", len(pipe.steps), "type =", type(n).__name__)
if not isinstance(n, int):
    print("FAIL: not int")
    sys.exit(1)
if n != len(pipe.steps) or n != 3:
    print("FAIL: mismatch")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; all applied cleanly. Coverage: probe_1 R1.1/1.4/1.5 (len==len(steps), int, no TypeError) — also POSITIVE CONTROL, FAILS at base with 'object of type Pipeline has no len()'. probe_2 R1.2/1.3 (counts None + 'passthrough' entries, no dedup/drop => 5). probe_3 R2.1/2.2 (pipe[:len(pipe)] returns Pipeline with all steps; length-derived sub-slice). probe_4 R3.1/3.2/3.3 (int pos/neg -> estimator, name -> estimator, slice -> Pipeline). probe_5 R3.4/3.5/3.6 (step!=1 & reversed slice -> ValueError, OOR int -> IndexError, bad name -> KeyError). probe_6 R3.7 (named_steps unchanged, count matches). Positive control discriminates (patched exit 0, base exit 1 => prepatch_reproduced true). Candidate patch weak_iter_count is a plausible-wrong reading (count 'active' steps); REJECTED by probe_2. No probe-conforming alternative found that would leave hidden tests unresolved. Requirements are faithful to the gold patch (return len(self.steps)).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate patch defines __len__ as sum(1 for _ in self._iter()), counting only non-None/non-'passthrough' steps. On a 5-step pipeline containing a None and a 'passthrough' entry it returns 3 instead of 5 — probe_2 REJECTS it (VIOLATED: len=3 expected 5). This confirms the probe suite discriminates the requirement R1.2/R1.3 mandate that len counts EVERY entry.
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
"""R1: len(pipe) == len(pipe.steps), returns int, no TypeError. Positive control."""
import sys
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA()), ('clf', LogisticRegression())])
try:
    n = len(pipe)
except TypeError as e:
    print("FAIL: len() raised TypeError:", e)
    sys.exit(1)
print("len(pipe) =", n, "len(pipe.steps) =", len(pipe.steps), "type =", type(n).__name__)
if not isinstance(n, int):
    print("FAIL: not int")
    sys.exit(1)
if n != len(pipe.steps) or n != 3:
    print("FAIL: mismatch")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; all applied cleanly. Coverage: probe_1 R1.1/1.4/1.5 (len==len(steps), int, no TypeError) — also POSITIVE CONTROL, FAILS at base with 'object of type Pipeline has no len()'. probe_2 R1.2/1.3 (counts None + 'passthrough' entries, no dedup/drop => 5). probe_3 R2.1/2.2 (pipe[:len(pipe)] returns Pipeline with all steps; length-derived sub-slice). probe_4 R3.1/3.2/3.3 (int pos/neg -> estimator, name -> estimator, slice -> Pipeline). probe_5 R3.4/3.5/3.6 (step!=1 & reversed slice -> ValueError, OOR int -> IndexError, bad name -> KeyError). probe_6 R3.7 (named_steps unchanged, count matches). Positive control discriminates (patched exit 0, base exit 1 => prepatch_reproduced true). Candidate patch weak_iter_count is a plausible-wrong reading (count 'active' steps); REJECTED by probe_2. No probe-conforming alternative found that would leave hidden tests unresolved. Requirements are faithful to the gold patch (return len(self.steps)).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (patched, exit 0 ALL OK): len(pipe)==3==len(pipe.steps); Pipeline with a 'passthrough' entry still len 3 (Req1.2); pipe[:len(pipe)] returns a Pipeline with identical .steps (Req2.1/2.2); pipe[0]/pipe[-1] return stored estimators (Req3.1), pipe['svc'] name lookup (Req3.2), pipe[:2] returns Pipeline with sliced steps (Req3.3), pipe[::-1] raises ValueError (Req3.4), pipe[10] IndexError (Req3.5), pipe['nope'] KeyError (Req3.6). Base probe (--base, exit 0): len(pipe) raises TypeError, confirming the modeling boundary is the newly-added __len__, which Req 1 targets. Requirement scope matches the observable change; the __getitem__ criteria (Reg 3) are pre-existing behavior correctly asserted as preserved.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The hidden test is a one-line `assert len(pipeline) == 2` appended to test_make_pipeline_memory; the gold edit is `def __len__(self): return len(self.steps)`. requirements.md never names the test function/path/id (test_make_pipeline_memory, sklearn/tests/test_pipeline.py), never quotes test or gold code, and invents no identifiers — `__len__`, `steps`, `__getitem__`, `sklearn.pipeline` are legitimate localization of the change surface (and `pipe[:len(pipe)]`, len() raising TypeError are verbatim from the PUBLIC problem_statement). The None/'passthrough' clause and the ValueError/IndexError/KeyError slicing cases (Req 3) translate pre-existing, documented Pipeline __getitem__ semantics into behavioral requirements rather than mirroring the FAIL_TO_PASS test; those parametrized [None]/[passthrough] cases are PASS_TO_PASS regressions, not the added test. Behavioral description, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
