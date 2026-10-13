# P2 adversarial audit — scikit-learn__scikit-learn-13124

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control -- Requirement 1.1 / 1.3:
# With shuffle=True, two different integer seeds must in general produce
# different collections of test folds. The discriminating case (from the PR)
# is n_splits == class_size, where the base bug (identical per-class shuffle)
# collapses the test-fold collection to a seed-independent value.
import numpy as np
from sklearn.model_selection import StratifiedKFold

X = np.arange(10)
y = [0] * 5 + [1] * 5
kf1 = StratifiedKFold(5, shuffle=True, random_state=0)
kf2 = StratifiedKFold(5, shuffle=True, random_state=1)
ts1 = sorted(tuple(sorted(s[1].tolist())) for s in kf1.split(X, y))
ts2 = sorted(tuple(sorted(s[1].tolist())) for s in kf2.split(X, y))
print("seed0 test folds:", ts1)
print("seed1 test folds:", ts2)
differ = ts1 != ts2
print("collections differ across seeds:", differ)
raise SystemExit(0 if differ else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 1.3: with shuffle=True and >1 class, distinct classes are
# generally arranged DIFFERENTLY (single generator threaded across classes),
# rather than every class receiving an identical arrangement (the base bug).
import numpy as np
from sklearn.model_selection import StratifiedKFold

y = np.array([0]*20 + [1]*20)
X = np.zeros((len(y), 1))
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=7)
tf = skf._make_test_folds(X, y)
c0 = tf[y == 0]
c1 = tf[y == 1]
print("class0 arrangement:", c0.tolist())
print("class1 arrangement:", c1.tolist())
identical = np.array_equal(c0, c1)
print("classes have identical arrangement:", identical)
# Criterion holds iff arrangements are NOT forced identical.
raise SystemExit(1 if identical else 0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 3.1 & 3.2: fixed integer seed reproduces identical splits
# on every invocation and across independently-built instances.
import numpy as np
from sklearn.model_selection import StratifiedKFold

X = np.arange(10)
y = [0]*5 + [1]*5

def splits(seed):
    kf = StratifiedKFold(5, shuffle=True, random_state=seed)
    return [(tuple(tr.tolist()), tuple(te.tolist())) for tr, te in kf.split(X, y)]

a = splits(0)
b = splits(0)                      # same instance-config, re-called
kf_again = StratifiedKFold(5, shuffle=True, random_state=0)
c = [(tuple(tr.tolist()), tuple(te.tolist())) for tr, te in kf_again.split(X, y)]

print("call1:", a)
print("call2:", b)
print("fresh instance:", c)
ok = (a == b) and (a == c)
print("reproducible:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 4.1 & 4.2: with shuffle=False, splits are seed-independent and
# each class stays in natural ascending order (contiguous blocks per class).
import numpy as np
from sklearn.model_selection import StratifiedKFold

y = np.array([0]*20 + [1]*20)
X = np.zeros((len(y), 1))

def folds(seed):
    kf = StratifiedKFold(5, shuffle=False, random_state=seed)
    return [tuple(sorted(te.tolist())) for te in kf._iter_test_masks() ] if False else \
           [tuple(sorted(te.tolist())) for _, te in kf.split(X, y)]

f_none = folds(None)
f0 = folds(0)
f1 = folds(1)
print("shuffle=False seed=None:", f_none)
print("shuffle=False seed=0:   ", f0)
print("shuffle=False seed=1:   ", f1)
seed_indep = (f_none == f0 == f1)

# natural ascending order: class0 (idx 0..19) dealt round-robin into folds ->
# first fold should get the smallest indices of each class contiguously.
tf = StratifiedKFold(5, shuffle=False).split(X, y)
first_test = sorted(next(iter(tf))[1].tolist())
print("first fold test indices:", first_test)
# For 20 per class over 5 folds, fold0 must be [0,1,2,3, 20,21,22,23]
natural = first_test == [0, 1, 2, 3, 20, 21, 22, 23]
print("natural ascending order preserved:", natural)

ok = seed_indep and natural
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 5.1/5.2/5.3: n_splits preserved, class proportions ~equal per
# fold, test indices cover every sample exactly once, train = complement.
import numpy as np
from sklearn.model_selection import StratifiedKFold

def check(shuffle, seed):
    y = np.array([0]*30 + [1]*15)   # 2:1 imbalance
    X = np.zeros((len(y), 1))
    n = 5
    kf = StratifiedKFold(n, shuffle=shuffle, random_state=seed)
    splits = list(kf.split(X, y))
    assert len(splits) == n, "n_splits mismatch"
    all_test = []
    for tr, te in splits:
        all_test.extend(te.tolist())
        # train is complement of test
        assert sorted(np.concatenate([tr, te]).tolist()) == list(range(len(y))), "train != complement"
        assert set(tr).isdisjoint(set(te)), "train/test overlap"
        # class proportion in this fold ~ global (1/3 class1)
        frac1 = np.mean(y[te] == 1)
        assert abs(frac1 - 1/3) <= 0.15, f"proportion off: {frac1}"
    # cover every sample exactly once
    assert sorted(all_test) == list(range(len(y))), "coverage broken"
    return True

check(True, 0)
check(True, 5)
check(False, 0)
print("n_splits, proportions, coverage, complement all OK for shuffle T/F")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 2.1/2.3/2.4 (+5.5): random_state interpretation.
#  - int seed: treated as seed for a fresh RNG (reproducible; equals a
#    RandomState(seed) instance passed directly, consumed once).
#  - RandomState instance: used directly.
#  - invalid form: ValueError.
#  - unsupported target type (continuous): ValueError.
import numpy as np
from sklearn.model_selection import StratifiedKFold

X = np.arange(10)
y = [0]*5 + [1]*5

def folds(rs):
    kf = StratifiedKFold(5, shuffle=True, random_state=rs)
    return [tuple(sorted(te.tolist())) for _, te in kf.split(X, y)]

# int seed == RandomState(seed) instance used directly
by_int = folds(0)
by_inst = folds(np.random.RandomState(0))
print("by int seed:  ", by_int)
print("by instance:  ", by_inst)
assert by_int == by_inst, "int seed not equivalent to RandomState(seed)"

# invalid random_state form -> ValueError
try:
    folds("not-a-valid-rng")
    raise SystemExit("no ValueError for invalid random_state")
except ValueError:
    print("invalid random_state -> ValueError OK")

# unsupported target type (continuous) -> ValueError
try:
    kf = StratifiedKFold(3, shuffle=True, random_state=0)
    list(kf.split(np.arange(9), np.linspace(0, 1, 9)))
    raise SystemExit("no ValueError for continuous target")
except ValueError:
    print("continuous target -> ValueError OK")

print("random_state interpretation criteria OK")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control -- Requirement 1.1 / 1.3:
# With shuffle=True, two different integer seeds must in general produce
# different collections of test folds. The discriminating case (from the PR)
# is n_splits == class_size, where the base bug (identical per-class shuffle)
# collapses the test-fold collection to a seed-independent value.
import numpy as np
from sklearn.model_selection import StratifiedKFold

X = np.arange(10)
y = [0] * 5 + [1] * 5
kf1 = StratifiedKFold(5, shuffle=True, random_state=0)
kf2 = StratifiedKFold(5, shuffle=True, random_state=1)
ts1 = sorted(tuple(sorted(s[1].tolist())) for s in kf1.split(X, y))
ts2 = sorted(tuple(sorted(s[1].tolist())) for s in kf2.split(X, y))
print("seed0 test folds:", ts1)
print("seed1 test folds:", ts2)
differ = ts1 != ts2
print("collections differ across seeds:", differ)
raise SystemExit(0 if differ else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: StratifiedKFold shuffle must genuinely depend on random_state. Gold patch changes _make_test_folds to `rng = check_random_state(self.random_state)` so a SINGLE seeded generator is threaded across the per-class KFold splitters (each class advances rng state -> distinct arrangements). Base bug: `rng = self.random_state` passed the raw int to each per-class KFold, which internally re-derived an IDENTICAL RandomState(seed), so every class was shuffled identically and different seeds gave the same test-fold collections (only fold emission order differed).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): PR's discriminating case n_splits==class_size (X=arange(10), y=[0]*5+[1]*5); seed0 vs seed1 test-fold collections must differ. FAILS at base (collections identical) => prepatch reproduced; HOLDS patched.
- probe_2 (Req1.3): with shuffle=True and 2 classes, per-class fold arrangements must NOT be forced identical. FAILS at base (class0==class1 arrangement); HOLDS patched.
- probe_3 (Req3.1/3.2): fixed int seed reproduces identical splits across re-calls and across fresh instances. HOLDS.
- probe_4 (Req4.1/4.2): shuffle=False seed-independent (None/0/1 identical) and natural ascending per-class order (fold0=[0..3,20..23]). HOLDS.
- probe_5 (Req5.1/5.2/5.3): n_splits preserved, per-fold class proportions ~global (2:1 imbalance), test indices cover every sample exactly once, train=complement, for shuffle T/F. HOLDS.
- probe_6 (Req2.1/2.3/2.4/5.5): int seed == RandomState(seed) instance used directly; invalid random_state -> ValueError; continuous target -> ValueError. HOLDS.

Candidate wrong-fixes (both REJECTED by suite; demonstrates discrimination):
- weakA (lazy fix): docstring-only change, leaves `rng = self.random_state`. Rejected by probe_1 (collections identical across seeds), probe_2 (identical per-class arrangement), probe_6 (int seed != RandomState instance). == base behavior.
- weakB (partial/weak reading): converts to check_random_state at top BUT re-derives a fresh check_random_state(self.random_state) INSIDE the per-class comprehension, so each class gets an independent identically-seeded RNG. Rejected by probe_1 and probe_2 (classes still arranged identically -> seed-independent collections) and probe_6. This is exactly the trap a shallow reading of Req2 permits; suite catches it via Req1.3.

Conclusion: >=5 distinct probes all hold on patched; positive control discriminates (fails base, holds patched); >=1 candidate exercised and REJECTED (both). Suite discriminates wrong implementations; no requirement-conforming alternative found that fails the hidden test. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
# Positive control -- Requirement 1.1 / 1.3:
# With shuffle=True, two different integer seeds must in general produce
# different collections of test folds. The discriminating case (from the PR)
# is n_splits == class_size, where the base bug (identical per-class shuffle)
# collapses the test-fold collection to a seed-independent value.
import numpy as np
from sklearn.model_selection import StratifiedKFold

X = np.arange(10)
y = [0] * 5 + [1] * 5
kf1 = StratifiedKFold(5, shuffle=True, random_state=0)
kf2 = StratifiedKFold(5, shuffle=True, random_state=1)
ts1 = sorted(tuple(sorted(s[1].tolist())) for s in kf1.split(X, y))
ts2 = sorted(tuple(sorted(s[1].tolist())) for s in kf2.split(X, y))
print("seed0 test folds:", ts1)
print("seed1 test folds:", ts2)
differ = ts1 != ts2
print("collections differ across seeds:", differ)
raise SystemExit(0 if differ else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: StratifiedKFold shuffle must genuinely depend on random_state. Gold patch changes _make_test_folds to `rng = check_random_state(self.random_state)` so a SINGLE seeded generator is threaded across the per-class KFold splitters (each class advances rng state -> distinct arrangements). Base bug: `rng = self.random_state` passed the raw int to each per-class KFold, which internally re-derived an IDENTICAL RandomState(seed), so every class was shuffled identically and different seeds gave the same test-fold collections (only fold emission order differed).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): PR's discriminating case n_splits==class_size (X=arange(10), y=[0]*5+[1]*5); seed0 vs seed1 test-fold collections must differ. FAILS at base (collections identical) => prepatch reproduced; HOLDS patched.
- probe_2 (Req1.3): with shuffle=True and 2 classes, per-class fold arrangements must NOT be forced identical. FAILS at base (class0==class1 arrangement); HOLDS patched.
- probe_3 (Req3.1/3.2): fixed int seed reproduces identical splits across re-calls and across fresh instances. HOLDS.
- probe_4 (Req4.1/4.2): shuffle=False seed-independent (None/0/1 identical) and natural ascending per-class order (fold0=[0..3,20..23]). HOLDS.
- probe_5 (Req5.1/5.2/5.3): n_splits preserved, per-fold class proportions ~global (2:1 imbalance), test indices cover every sample exactly once, train=complement, for shuffle T/F. HOLDS.
- probe_6 (Req2.1/2.3/2.4/5.5): int seed == RandomState(seed) instance used directly; invalid random_state -> ValueError; continuous target -> ValueError. HOLDS.

Candidate wrong-fixes (both REJECTED by suite; demonstrates discrimination):
- weakA (lazy fix): docstring-only change, leaves `rng = self.random_state`. Rejected by probe_1 (collections identical across seeds), probe_2 (identical per-class arrangement), probe_6 (int seed != RandomState instance). == base behavior.
- weakB (partial/weak reading): converts to check_random_state at top BUT re-derives a fresh check_random_state(self.random_state) INSIDE the per-class comprehension, so each class gets an independent identically-seeded RNG. Rejected by probe_1 and probe_2 (classes still arranged identically -> seed-independent collections) and probe_6. This is exactly the trap a shallow reading of Req2 permits; suite catches it via Req1.3.

Conclusion: >=5 distinct probes all hold on patched; positive control discriminates (fails base, holds patched); >=1 candidate exercised and REJECTED (both). Suite discriminates wrong implementations; no requirement-conforming alternative found that fails the hidden test. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the observable seed-dependent + per-class-distinct shuffling (the changed behavior), not a narrow slice. Probe outputs — base: 'classes identically arranged (BUG present): True', 'n=10 sets equal across seeds: True'; patched: those flip to False. All 5 requirements verified via probe on the gold-patched image.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior, not the hidden test. Naming StratifiedKFold._make_test_folds, check_random_state, and KFold is legitimate localization — check_random_state is the literal gold edit target and naming modules/functions is permitted. Requirement 1 states that two different integer random_state values SHALL generally produce different test folds; this is a behavioral translation of the public problem_statement's core complaint ('I expect batches to be different when Shuffle is turned on for different random_state seeds'), NOT a transcription of the hidden test (test_shuffle_stratifiedkfold: X=np.arange(10), y=[0]*5+[1]*5, seeds 0 and 1, assert test_set1 != test_set2). No specific seed values, dataset shapes, or parametrization ids from the test appear. Requirement 2's int/None/instance/ValueError enumeration mirrors the public/standard semantics of check_random_state, not any test case (no such test exists in FAIL_TO_PASS/PASS_TO_PASS for these paths). The single-generator-threaded-across-classes description restates the hints/gold mechanism as a behavioral requirement rather than quoting gold code. No test file path, test function name, quoted test/gold code lines, or case enumerations mirroring test parametrization. No fix-invented identifiers (none are invented; check_random_state pre-exists).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
