# P2 adversarial audit — scikit-learn__scikit-learn-10908

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

# Req1.1/1.2/1.3 + positive control: get_feature_names on unfitted vectorizer
# constructed with a provided vocabulary returns terms in feature-index order,
# and vocabulary_ maps each name to its position.
import sys
from sklearn.feature_extraction.text import CountVectorizer

vocab = ["pizza", "beer", "salad", "wine"]
cv = CountVectorizer(vocabulary=vocab)

# must NOT be fitted yet
if hasattr(cv, "vocabulary_"):
    print("FAIL: vocabulary_ present before any access")
    sys.exit(1)

try:
    names = cv.get_feature_names()
except Exception as e:
    print("FAIL: get_feature_names raised on provided-but-unfitted vocab: %r" % e)
    sys.exit(1)

print("names =", names)
if list(names) != vocab:
    print("FAIL: names not in provided list order")
    sys.exit(1)

# vocabulary_ maps each name to its position in returned list
for idx, name in enumerate(names):
    if cv.vocabulary_.get(name) != idx:
        print("FAIL: vocabulary_[%r]=%r != %d" % (name, cv.vocabulary_.get(name), idx))
        sys.exit(1)

print("PASS: names in order and mapping consistent")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python

# Req2.1: after get_feature_names establishes vocab from provided vocabulary,
# fixed_vocabulary_ SHALL be True.
import sys
from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(vocabulary=["a", "b", "c"])
cv.get_feature_names()
print("fixed_vocabulary_ =", getattr(cv, "fixed_vocabulary_", "MISSING"))
if getattr(cv, "fixed_vocabulary_", None) is not True:
    print("FAIL: fixed_vocabulary_ not True after establishing provided vocab")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python

# Req2.3/2.4/2.5: validation errors on establishing provided vocabulary via
# get_feature_names (duplicate term, bad mapping indices, empty vocab).
import sys
from sklearn.feature_extraction.text import CountVectorizer

ok = True

# duplicate term
cv = CountVectorizer(vocabulary=["a", "b", "a"])
try:
    cv.get_feature_names()
    print("FAIL: no error on duplicate term"); ok = False
except ValueError as e:
    print("duplicate ->", e)

# mapping with repeated/non-covering indices
cv = CountVectorizer(vocabulary={"a": 0, "b": 2})  # missing index 1
try:
    cv.get_feature_names()
    print("FAIL: no error on bad mapping indices"); ok = False
except ValueError as e:
    print("bad mapping ->", e)

# empty vocabulary
cv = CountVectorizer(vocabulary=[])
try:
    cv.get_feature_names()
    print("FAIL: no error on empty vocab"); ok = False
except ValueError as e:
    print("empty ->", e)

if ok:
    print("PASS")
    sys.exit(0)
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python

# Req3: no vocabulary provided + not fitted -> get_feature_names raises
# (not-fitted ValueError); and it must NOT establish a vocabulary_.
import sys
from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer()
raised = False
try:
    cv.get_feature_names()
except ValueError as e:
    raised = True
    print("raised ->", e)
except Exception as e:
    print("FAIL: wrong exception type %r" % e)
    sys.exit(1)

if not raised:
    print("FAIL: no error when unfitted and no vocabulary provided")
    sys.exit(1)

# Req3.3: must not have established a learned vocabulary_
if hasattr(cv, "vocabulary_"):
    print("FAIL: vocabulary_ established when none provided:", cv.vocabulary_)
    sys.exit(1)

print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python

# Req4: after fitting on a corpus, get_feature_names returns learned terms in
# ascending feature-index order; count == len(vocabulary_); mapping name->idx.
# Also Req1.4 consistency after transform on provided-vocab vectorizer, and
# Req3.2 fixed_vocabulary_ False after a no-vocab fit.
import sys
from sklearn.feature_extraction.text import CountVectorizer

corpus = ["the quick brown fox", "the lazy dog", "quick brown dog"]
cv = CountVectorizer()
cv.fit(corpus)
names = cv.get_feature_names()
print("names =", names)

if sorted(names) != list(names):
    print("FAIL: names not in ascending order")
    sys.exit(1)
if len(names) != len(cv.vocabulary_):
    print("FAIL: len mismatch")
    sys.exit(1)
for idx, name in enumerate(names):
    if cv.vocabulary_[name] != idx:
        print("FAIL: vocabulary_[%r]=%d != %d" % (name, cv.vocabulary_[name], idx))
        sys.exit(1)
if getattr(cv, "fixed_vocabulary_", None) is not False:
    print("FAIL: fixed_vocabulary_ should be False for learned vocab")
    sys.exit(1)

# Req1.4 / Req4.4: provided-vocab vectorizer, transform then get_feature_names consistent
vocab = ["dog", "cat", "fox"]
cv2 = CountVectorizer(vocabulary=vocab)
X = cv2.transform(["dog cat fox"])  # succeeds without fit
names2 = cv2.get_feature_names()
print("names2 =", names2)
if list(names2) != vocab:
    print("FAIL: provided-vocab names not consistent after transform")
    sys.exit(1)
for idx, name in enumerate(names2):
    if cv2.vocabulary_[name] != idx:
        print("FAIL: mapping inconsistent after transform")
        sys.exit(1)

print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python

# Req1.1/1.2/1.3 + positive control: get_feature_names on unfitted vectorizer
# constructed with a provided vocabulary returns terms in feature-index order,
# and vocabulary_ maps each name to its position.
import sys
from sklearn.feature_extraction.text import CountVectorizer

vocab = ["pizza", "beer", "salad", "wine"]
cv = CountVectorizer(vocabulary=vocab)

# must NOT be fitted yet
if hasattr(cv, "vocabulary_"):
    print("FAIL: vocabulary_ present before any access")
    sys.exit(1)

try:
    names = cv.get_feature_names()
except Exception as e:
    print("FAIL: get_feature_names raised on provided-but-unfitted vocab: %r" % e)
    sys.exit(1)

print("names =", names)
if list(names) != vocab:
    print("FAIL: names not in provided list order")
    sys.exit(1)

# vocabulary_ maps each name to its position in returned list
for idx, name in enumerate(names):
    if cv.vocabulary_.get(name) != idx:
        print("FAIL: vocabulary_[%r]=%r != %d" % (name, cv.vocabulary_.get(name), idx))
        sys.exit(1)

print("PASS: names in order and mapping consistent")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1 (return provided-vocab names in index order + vocabulary_ mapping consistency), Req2 (fixed_vocabulary_=True after establishing; duplicate/bad-mapping/empty ValueErrors), Req3 (no-vocab unfitted -> ValueError, no vocabulary_ established), Req4 (fitted names ascending, count==len, mapping; transform-then-get consistency). All 5 HOLD on gold-patched tree. Positive control probe_1 HOLDS patched, VIOLATED at base (raised NotFittedError) -> discriminating. Candidate weak.diff (sets vocabulary_ directly from self.vocabulary, skipping _validate_vocabulary) is a requirements-conforming-looking naive fix but REJECTED by probe_2 (fixed_vocabulary_ not set True), probe_3 (empty/mapping validation missing), and probe_4 (TypeError instead of ValueError when no vocab). Suite discriminates wrong implementations; no too-weak candidate passed. Ran with swebench-lean conda python via nl_attack; all runs completed.

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

# Req1.1/1.2/1.3 + positive control: get_feature_names on unfitted vectorizer
# constructed with a provided vocabulary returns terms in feature-index order,
# and vocabulary_ maps each name to its position.
import sys
from sklearn.feature_extraction.text import CountVectorizer

vocab = ["pizza", "beer", "salad", "wine"]
cv = CountVectorizer(vocabulary=vocab)

# must NOT be fitted yet
if hasattr(cv, "vocabulary_"):
    print("FAIL: vocabulary_ present before any access")
    sys.exit(1)

try:
    names = cv.get_feature_names()
except Exception as e:
    print("FAIL: get_feature_names raised on provided-but-unfitted vocab: %r" % e)
    sys.exit(1)

print("names =", names)
if list(names) != vocab:
    print("FAIL: names not in provided list order")
    sys.exit(1)

# vocabulary_ maps each name to its position in returned list
for idx, name in enumerate(names):
    if cv.vocabulary_.get(name) != idx:
        print("FAIL: vocabulary_[%r]=%r != %d" % (name, cv.vocabulary_.get(name), idx))
        sys.exit(1)

print("PASS: names in order and mapping consistent")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1 (return provided-vocab names in index order + vocabulary_ mapping consistency), Req2 (fixed_vocabulary_=True after establishing; duplicate/bad-mapping/empty ValueErrors), Req3 (no-vocab unfitted -> ValueError, no vocabulary_ established), Req4 (fitted names ascending, count==len, mapping; transform-then-get consistency). All 5 HOLD on gold-patched tree. Positive control probe_1 HOLDS patched, VIOLATED at base (raised NotFittedError) -> discriminating. Candidate weak.diff (sets vocabulary_ directly from self.vocabulary, skipping _validate_vocabulary) is a requirements-conforming-looking naive fix but REJECTED by probe_2 (fixed_vocabulary_ not set True), probe_3 (empty/mapping validation missing), and probe_4 (TypeError instead of ValueError when no vocab). Suite discriminates wrong implementations; no too-weak candidate passed. Ran with swebench-lean conda python via nl_attack; all runs completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds `if not hasattr(self,'vocabulary_'): self._validate_vocabulary()` before `self._check_vocabulary()` in get_feature_names. This exactly re-uses transform/fit's vocabulary establishment path (_validate_vocabulary), so all sub-behaviors (duplicate/gap/empty validation, fixed_vocabulary_ semantics) are inherited — the requirements pin the changed observable behavior (feature-name access on a provided-but-unfitted vocabulary) at the right boundary, not a narrow slice. The FAIL_TO_PASS test test_feature_names checks exactly R1/R2.1 (list vocab -> names in order, fixed_vocabulary_ True, mapping) and R3.2 (fixed_vocabulary_ False when unfitted no-vocab). Requirement wording for R2.5 ('indicating an empty vocabulary') is a faithful characterization of the actual message 'empty vocabulary passed to fit'.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change using only public/pre-existing API identifiers (get_feature_names, _validate_vocabulary, _check_vocabulary, vocabulary_, fixed_vocabulary_ — all present in text.py, none invented by the gold patch, which merely inserts `if not hasattr(self,'vocabulary_'): self._validate_vocabulary()`). No hidden-test content is transmitted: no test names/paths/ids, no quoted test code. The concrete vocabulary example in the doc-worthy sense is NOT present — the hidden test's food vocabulary (['beer','burger','celeri','coke','pizza','salad','sparkling','tomato','water']) is never reproduced; the doc stays abstract ('an ordered list of terms', 'position equal to its 0-based index'). Requirements 2.3/2.4/2.5 (duplicate term, gap/repeated indices, empty vocabulary raise ValueError) describe pre-existing _validate_vocabulary validation behavior that corresponds to PASS_TO_PASS tests, expressed as genuine behavioral requirements rather than as an enumeration mirroring test parametrization. The fixed_vocabulary_ True/False assertions are public-attribute behavior. This is behavior translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
