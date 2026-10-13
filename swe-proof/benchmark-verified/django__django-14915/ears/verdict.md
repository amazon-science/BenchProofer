# P2 adversarial audit — django__django-14915

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
import sys
from django.forms.models import ModelChoiceIteratorValue

# Req 1.1 / positive control: instance is hashable at all
v = ModelChoiceIteratorValue(1, object())
try:
    h = hash(v)
except TypeError as e:
    print("FAIL: hash raised TypeError:", e)
    sys.exit(1)
print("OK: hash succeeded ->", h)
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from django.forms.models import ModelChoiceIteratorValue

# Req 2.1/2.5: hash equals hash of wrapped underlying value
ok = True
for underlying in [1, "abc", 42, (1, 2)]:
    v = ModelChoiceIteratorValue(underlying, object())
    if hash(v) != hash(underlying):
        print("FAIL: hash(v)=%r != hash(%r)=%r" % (hash(v), underlying, hash(underlying)))
        ok = False
    else:
        print("OK: hash matches for", underlying)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from django.forms.models import ModelChoiceIteratorValue

# Req 2.2/2.3: hash depends only on wrapped value, not on model object.
# Two wrappers with equal underlying value but different model -> equal hash.
v1 = ModelChoiceIteratorValue(7, "modelA")
v2 = ModelChoiceIteratorValue(7, "modelB")
v3 = ModelChoiceIteratorValue(7, None)
ok = hash(v1) == hash(v2) == hash(v3)
print("hashes:", hash(v1), hash(v2), hash(v3))
if not ok:
    print("FAIL: hashes differ despite equal underlying value")
    sys.exit(1)
# distinct underlying values should generally differ (as test asserts pk1!=pk2)
va = ModelChoiceIteratorValue(1, None)
vb = ModelChoiceIteratorValue(2, None)
if hash(va) == hash(vb):
    print("FAIL: hash(1) == hash(2) unexpectedly")
    sys.exit(1)
print("OK: hash independent of model; distinct values differ")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from django.forms.models import ModelChoiceIteratorValue

# Req 1.2/1.3/1.4 + 2.5: membership in dict/set keyed by plain value; insertion
v = ModelChoiceIteratorValue(1, object())
show_fields = {1: ['first_name', 'last_name']}
try:
    r_dict = v in show_fields
    r_set = v in {1, 2}
    d = {}
    d[v] = 'x'
    s = set()
    s.add(v)
except TypeError as e:
    print("FAIL: TypeError during membership/insert:", e)
    sys.exit(1)
# 2.5: wrapper equal to plain value probes mapping keyed by plain value
if not r_dict:
    print("FAIL: wrapper not found in dict keyed by plain value")
    sys.exit(1)
if not r_set:
    print("FAIL: wrapper not found in set of plain values")
    sys.exit(1)
# lookup returns the value stored under plain key
if show_fields[v] != ['first_name', 'last_name']:
    print("FAIL: dict lookup with wrapper key did not return plain-key value")
    sys.exit(1)
print("OK: dict/set membership, insertion, and lookup all work")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from django.forms.models import ModelChoiceIteratorValue

# Req 3: preserved behavior - value/instance exposed, str, equality
m = object()
v = ModelChoiceIteratorValue(5, m)
ok = True
if v.value != 5:
    print("FAIL: .value not exposed"); ok = False
if v.instance is not m:
    print("FAIL: .instance not exposed"); ok = False
if str(v) != "5":
    print("FAIL: str(v)=%r != '5'" % str(v)); ok = False
# eq with plain value
if not (v == 5):
    print("FAIL: v == 5 should hold"); ok = False
if v == 6:
    print("FAIL: v == 6 should not hold"); ok = False
# eq with another wrapper
if not (v == ModelChoiceIteratorValue(5, None)):
    print("FAIL: wrapper eq wrapper same value"); ok = False
if v == ModelChoiceIteratorValue(6, None):
    print("FAIL: wrapper eq wrapper diff value"); ok = False
print("OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from django.forms.models import ModelChoiceIteratorValue

# Req 1.1 / positive control: instance is hashable at all
v = ModelChoiceIteratorValue(1, object())
try:
    h = hash(v)
except TypeError as e:
    print("FAIL: hash raised TypeError:", e)
    sys.exit(1)
print("OK: hash succeeded ->", h)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-14915: gold patch adds __hash__ returning hash(self.value) to ModelChoiceIteratorValue.

Probes (all HOLD on patched tree, verified):
- probe_1 (Req 1.1, POSITIVE CONTROL): hash(instance) succeeds. HOLDS patched, VIOLATED at base (TypeError: unhashable type 'ModelChoiceIteratorValue'). Discriminates.
- probe_2 (Req 2.1/2.5): hash(v) == hash(wrapped underlying value) for several value types.
- probe_3 (Req 2.2/2.3): hash independent of model object (equal underlying -> equal hash across different/None models); distinct underlying values differ.
- probe_4 (Req 1.2/1.3/1.4/2.5): dict/set membership, insertion, and dict lookup with wrapper key against a plain-value-keyed mapping all work.
- probe_5 (Req 3.1-3.4): .value/.instance exposed, str form preserved, equality with plain value and with another wrapper preserved.

Candidate wrong-fix (constant_hash / weak.diff): __hash__ returns 0. Satisfies a naive reading of 'SHALL be hashable' (probe_1 and probe_5 pass) but REJECTED by probe_2 (hash != hash(value)), probe_3 (hash(1)==hash(2)), and probe_4 (wrapper not found in dict keyed by plain value). This also fails the official test_choice_value_hash assertNotEqual(hash(value_1), hash(value_2)). Suite discriminates wrong implementations.

Conclusion: >=5 distinct probes all hold on patched tree, positive control discriminates (fails at base), and a plausibly-wrong candidate is rejected by the suite. Requirements are faithful and not too weak. SOUND.

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
import sys
from django.forms.models import ModelChoiceIteratorValue

# Req 1.1 / positive control: instance is hashable at all
v = ModelChoiceIteratorValue(1, object())
try:
    h = hash(v)
except TypeError as e:
    print("FAIL: hash raised TypeError:", e)
    sys.exit(1)
print("OK: hash succeeded ->", h)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-14915: gold patch adds __hash__ returning hash(self.value) to ModelChoiceIteratorValue.

Probes (all HOLD on patched tree, verified):
- probe_1 (Req 1.1, POSITIVE CONTROL): hash(instance) succeeds. HOLDS patched, VIOLATED at base (TypeError: unhashable type 'ModelChoiceIteratorValue'). Discriminates.
- probe_2 (Req 2.1/2.5): hash(v) == hash(wrapped underlying value) for several value types.
- probe_3 (Req 2.2/2.3): hash independent of model object (equal underlying -> equal hash across different/None models); distinct underlying values differ.
- probe_4 (Req 1.2/1.3/1.4/2.5): dict/set membership, insertion, and dict lookup with wrapper key against a plain-value-keyed mapping all work.
- probe_5 (Req 3.1-3.4): .value/.instance exposed, str form preserved, equality with plain value and with another wrapper preserved.

Candidate wrong-fix (constant_hash / weak.diff): __hash__ returns 0. Satisfies a naive reading of 'SHALL be hashable' (probe_1 and probe_5 pass) but REJECTED by probe_2 (hash != hash(value)), probe_3 (hash(1)==hash(2)), and probe_4 (wrapper not found in dict keyed by plain value). This also fails the official test_choice_value_hash assertNotEqual(hash(value_1), hash(value_2)). Suite discriminates wrong implementations.

Conclusion: >=5 distinct probes all hold on patched tree, positive control discriminates (fails at base), and a plausibly-wrong candidate is rejected by the suite. Requirements are faithful and not too weak. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds exactly `def __hash__(self): return hash(self.value)`. Requirements pin the changed observable behavior (hashability derived from wrapped value alone, consistent with __eq__) without over-narrowing to a single branch/helper and without inventing behavior. Boundary is correct: they cover both directions of equality, both dict and set membership, key/member insertion, determinism, model-independence, and preservation of str/eq/wrapping. Base-vs-patched discriminator confirmed via probe (VIOLATED base / HOLDS patched).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already exposes: the class name ModelChoiceIteratorValue, the exact TypeError ('unhashable type: ModelChoiceIteratorValue'), the dict-membership use case ({1: ['first_name','last_name']}), and set/array contrast. requirements.md stays within this plus behavioral modeling. Requirement 2 ('hash depends only on the wrapped underlying value and not on the model object', 'two instances wrapping equal values hash equal regardless of model') is the behavioral consequence of the one-line gold fix `def __hash__(self): return hash(self.value)` — a legitimate translation, not a transcription. The hidden test (test_choice_value_hash) constructs a wrapper with a None model and asserts equal hash, and asserts distinct values hash unequal; these are covered by describing hash-consistency-with-equality behavior rather than by enumerating the test's specific cases, ids, or code. No test file path (tests/model_forms/test_modelchoicefield.py), no test/class/function names, no parametrization ids, no quoted test or gold lines, no fix-invented identifiers (the only names used — ModelChoiceIteratorValue, __eq__, __str__, value, model object — are pre-existing/public API and needed to localize the change). No case enumeration mirroring the test structure.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
