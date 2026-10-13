# P2 adversarial audit — django__django-14089

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

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control: R1.1 + R1.3/R1.4 — reversed() works and yields reverse order.
HOLDS on patched, FAILS at base (base raises TypeError)."""
import sys
from django.utils.datastructures import OrderedSet

s = OrderedSet([1, 2, 3, 4])
try:
    r = list(reversed(s))
except Exception as e:
    print("reversed() raised:", repr(e))
    sys.exit(1)
fwd = list(s)
print("forward:", fwd, "reversed:", r)
if r != fwd[::-1]:
    print("NOT reverse of forward")
    sys.exit(1)
if r != [4, 3, 2, 1]:
    print("unexpected reverse order")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2 — reversed yields exactly the contained elements, each once, none added/omitted.
Uses distinct + duplicate-collapsing input."""
import sys
from collections import Counter
from django.utils.datastructures import OrderedSet

s = OrderedSet(['a', 'b', 'c', 'b', 'a', 'd'])  # distinct: a,b,c,d
r = list(reversed(s))
print("reversed:", r)
if Counter(r) != Counter(list(s)):
    print("multiset mismatch vs forward")
    sys.exit(1)
if any(v != 1 for v in Counter(r).values()):
    print("an element repeated")
    sys.exit(1)
if set(r) != {'a', 'b', 'c', 'd'}:
    print("element set mismatch")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.5 — empty OrderedSet: reversed() yields no elements."""
import sys
from django.utils.datastructures import OrderedSet

s = OrderedSet()
r = list(reversed(s))
print("empty reversed:", r)
if r != []:
    print("expected empty")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.1 + R2.2 — returned object is a collections.abc.Iterator and is one-shot (exhausts).
R2.3 — consuming does not modify the set (contents/order/len unchanged)."""
import sys
from collections.abc import Iterator
from django.utils.datastructures import OrderedSet

s = OrderedSet([10, 20, 30])
before_fwd = list(s)
before_len = len(s)

it = reversed(s)
if not isinstance(it, Iterator):
    print("not an Iterator:", type(it))
    sys.exit(1)

first = list(it)
second = list(it)  # same object, must be exhausted
print("first:", first, "second:", second)
if first != [30, 20, 10]:
    print("wrong reverse order")
    sys.exit(1)
if second != []:
    print("iterator re-yielded (not one-shot)")
    sys.exit(1)

# set unchanged
if list(s) != before_fwd or len(s) != before_len:
    print("set was modified by reversed consumption")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3 — preserve existing OrderedSet behavior: forward order, distinct first-insertion,
membership, len, bool, add/remove/discard. And reversed reflects post-mutation state."""
import sys
from django.utils.datastructures import OrderedSet

# R3.1/R3.2 forward + distinct first-insertion
s = OrderedSet([3, 1, 2, 1, 3])
if list(s) != [3, 1, 2]:
    print("forward/distinct wrong:", list(s)); sys.exit(1)
# R3.3 membership
if 2 not in s or 99 in s:
    print("membership wrong"); sys.exit(1)
# R3.4 len + bool
if len(s) != 3 or not s:
    print("len/bool wrong"); sys.exit(1)
if OrderedSet():
    print("empty should be falsy"); sys.exit(1)
# R3.5 add/remove/discard
s.add(5)
if list(s) != [3, 1, 2, 5]:
    print("add wrong:", list(s)); sys.exit(1)
s.remove(1)
if list(s) != [3, 2, 5]:
    print("remove wrong:", list(s)); sys.exit(1)
s.discard(999)  # no error
try:
    s.remove(999)
    print("remove missing should KeyError"); sys.exit(1)
except KeyError:
    pass
# reversed reflects current state
if list(reversed(s)) != [5, 2, 3]:
    print("reversed after mutation wrong:", list(reversed(s))); sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4 — surrounding data structures preserved: MultiValueDict, CaseInsensitiveMapping,
ImmutableList, DictWrapper still behave (construction/access/update/copy/repr/errors)."""
import sys
import copy
from django.utils.datastructures import (
    MultiValueDict, MultiValueDictKeyError, CaseInsensitiveMapping,
    ImmutableList, DictWrapper,
)

# MultiValueDict
d = MultiValueDict({'name': ['Adrian', 'Simon'], 'pos': ['Dev']})
if d['name'] != 'Simon' or d.getlist('name') != ['Adrian', 'Simon']:
    print("MVD access wrong"); sys.exit(1)
if d.getlist('nope') != []:
    print("MVD getlist default wrong"); sys.exit(1)
try:
    MultiValueDict()['x']
    print("MVD should raise"); sys.exit(1)
except MultiValueDictKeyError:
    pass
d2 = copy.deepcopy(d)
if d2.getlist('name') != ['Adrian', 'Simon']:
    print("MVD deepcopy wrong"); sys.exit(1)

# CaseInsensitiveMapping
ci = CaseInsensitiveMapping({'Accept': 'text'})
if ci['accept'] != 'text' or 'ACCEPT' not in ci:
    print("CI mapping wrong"); sys.exit(1)

# ImmutableList
il = ImmutableList([1, 2, 3])
try:
    il[0] = 9
    print("ImmutableList should be immutable"); sys.exit(1)
except AttributeError:
    pass

# DictWrapper
dw = DictWrapper({'a': 'val'}, lambda x: x.upper(), 'p_')
if dw['a'] != 'val' or dw['p_a'] != 'VAL':
    print("DictWrapper wrong:", dw['p_a']); sys.exit(1)

print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: R1.1 + R1.3/R1.4 — reversed() works and yields reverse order.
HOLDS on patched, FAILS at base (base raises TypeError)."""
import sys
from django.utils.datastructures import OrderedSet

s = OrderedSet([1, 2, 3, 4])
try:
    r = list(reversed(s))
except Exception as e:
    print("reversed() raised:", repr(e))
    sys.exit(1)
fwd = list(s)
print("forward:", fwd, "reversed:", r)
if r != fwd[::-1]:
    print("NOT reverse of forward")
    sys.exit(1)
if r != [4, 3, 2, 1]:
    print("unexpected reverse order")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance adds __reversed__ to OrderedSet so reversed() works. 6 probes all HOLD on gold-patched tree.

Probe->requirement mapping (all HOLD patched):
- probe_1 (POSITIVE CONTROL): R1.1/R1.3/R1.4 reversed() works + exact reverse of forward. HOLDS patched (reversed [4,3,2,1]), FAILS base (TypeError: 'OrderedSet' object is not reversible). Discriminates.
- probe_2: R1.2 exactly the contained distinct elements, each once (dup-collapsing input). HOLDS.
- probe_3: R1.5 empty set -> reversed yields nothing. HOLDS.
- probe_4: R2.1 result isinstance collections.abc.Iterator, R2.2 one-shot (second traversal empty), R2.3 set unchanged. HOLDS patched.
- probe_5: R3.1-3.5 forward order/distinct first-insertion/membership/len/bool/add/remove/discard + reversed reflects post-mutation state. HOLDS.
- probe_6: R4 surrounding structures (MultiValueDict access/getlist/KeyError/deepcopy, CaseInsensitiveMapping, ImmutableList immutability, DictWrapper prefix transform). HOLDS.

CANDIDATE PATCH: weak.diff implements __reversed__ as `return list(self.dict)[::-1]` (returns a list, not an iterator). This is the lazy fix a weak reading permits (R1.1-1.5 order/content criteria all pass). Ran all probes under --patch weak.diff: probe_1,2,3,5 HOLD but probe_4 is REJECTED (VIOLATED: 'not an Iterator: <class list>'). So the suite discriminates this wrong implementation via R2.1/R2.2. The gold real test asserts iterator/one-shot semantics, so this weak patch would also fail the official harness -> not a too-weak finding; it confirms discriminating power.

All needed runs completed. Positive control failed at base (prepatch_reproduced=true) and holds patched.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control: R1.1 + R1.3/R1.4 — reversed() works and yields reverse order.
HOLDS on patched, FAILS at base (base raises TypeError)."""
import sys
from django.utils.datastructures import OrderedSet

s = OrderedSet([1, 2, 3, 4])
try:
    r = list(reversed(s))
except Exception as e:
    print("reversed() raised:", repr(e))
    sys.exit(1)
fwd = list(s)
print("forward:", fwd, "reversed:", r)
if r != fwd[::-1]:
    print("NOT reverse of forward")
    sys.exit(1)
if r != [4, 3, 2, 1]:
    print("unexpected reverse order")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance adds __reversed__ to OrderedSet so reversed() works. 6 probes all HOLD on gold-patched tree.

Probe->requirement mapping (all HOLD patched):
- probe_1 (POSITIVE CONTROL): R1.1/R1.3/R1.4 reversed() works + exact reverse of forward. HOLDS patched (reversed [4,3,2,1]), FAILS base (TypeError: 'OrderedSet' object is not reversible). Discriminates.
- probe_2: R1.2 exactly the contained distinct elements, each once (dup-collapsing input). HOLDS.
- probe_3: R1.5 empty set -> reversed yields nothing. HOLDS.
- probe_4: R2.1 result isinstance collections.abc.Iterator, R2.2 one-shot (second traversal empty), R2.3 set unchanged. HOLDS patched.
- probe_5: R3.1-3.5 forward order/distinct first-insertion/membership/len/bool/add/remove/discard + reversed reflects post-mutation state. HOLDS.
- probe_6: R4 surrounding structures (MultiValueDict access/getlist/KeyError/deepcopy, CaseInsensitiveMapping, ImmutableList immutability, DictWrapper prefix transform). HOLDS.

CANDIDATE PATCH: weak.diff implements __reversed__ as `return list(self.dict)[::-1]` (returns a list, not an iterator). This is the lazy fix a weak reading permits (R1.1-1.5 order/content criteria all pass). Ran all probes under --patch weak.diff: probe_1,2,3,5 HOLD but probe_4 is REJECTED (VIOLATED: 'not an Iterator: <class list>'). So the suite discriminates this wrong implementation via R2.1/R2.2. The gold real test asserts iterator/one-shot semantics, so this weak patch would also fail the official harness -> not a too-weak finding; it confirms discriminating power.

All needed runs completed. Positive control failed at base (prepatch_reproduced=true) and holds patched.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a single method addition; nl_attack probes on both patched and base trees confirm behavior. No unfaithful mandate, prohibition, boundary error, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize to django/utils/datastructures.py and OrderedSet, and name reversed()/__reversed__ — all public in the problem_statement (which explicitly says 'adding a __reversed__() method to OrderedSet'). No test file path, test/class names ('test_reversed', 'OrderedSetTests', 'utils_tests.test_datastructures'), no gold-patch lines, and no fix-invented identifiers appear (the gold adds only __reversed__, already public). The specific test literals ([1,2,3] -> [3,2,1]) are NOT reproduced; the doc describes the reverse-order behavior generically (k-th element = forward position n-1-k). The closest match is Req 2.1's mention of 'collections.abc.Iterator', which parallels the hidden test's assertIsInstance(s, collections.abc.Iterator); however, returning a standard iterator from reversed() is the ordinary Python iterator-protocol behavior and is a legitimate behavioral specification, not a transcription of a test-only artifact. Requirements about empty-set behavior, one-shot exhaustion, and non-mutation go beyond the single hidden test — evidence of behavior-first specification rather than test reconstruction. No case enumeration mirrors any parametrization (the F2P is a single non-parametrized test).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
