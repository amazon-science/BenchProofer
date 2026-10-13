# P2 adversarial audit — django__django-14765

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1: supplying a non-set (list) real_apps raises AssertionError.
Positive control: HOLDS patched, FAILS at base (base coerces list->set)."""
import sys
from django.db.migrations.state import ProjectState

try:
    ps = ProjectState(real_apps=["myapp"])
    print("NO AssertionError raised; real_apps=", getattr(ps, "real_apps", "<unset>"))
    sys.exit(1)
except AssertionError:
    print("AssertionError raised for list real_apps -> OK")
    sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1 (tuple variant): supplying a non-set tuple raises AssertionError."""
import sys
from django.db.migrations.state import ProjectState

try:
    ProjectState(real_apps=("a", "b"))
    print("NO AssertionError for tuple real_apps")
    sys.exit(1)
except AssertionError:
    print("AssertionError raised for tuple real_apps -> OK")
    sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.2: rejection happens BEFORE storing real_apps (construction incomplete).
After a failed construction with a non-set, no valid real_apps set should be stored."""
import sys
from django.db.migrations.state import ProjectState

ps = ProjectState.__new__(ProjectState)  # bare instance, no __init__ yet
try:
    ps.__init__(real_apps=["x"])
    print("construction completed unexpectedly")
    sys.exit(1)
except AssertionError:
    # real_apps must NOT have been assigned as the coerced list-derived set
    ra = getattr(ps, "real_apps", "<unset>")
    print("AssertionError; real_apps attr =", ra)
    if ra == "<unset>":
        print("no real_apps stored before assertion -> OK")
        sys.exit(0)
    print("real_apps was stored before/despite assertion -> FAIL")
    sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2: no argument / None -> real_apps defaults to an empty set, no AssertionError."""
import sys
from django.db.migrations.state import ProjectState

ps_omitted = ProjectState()
ps_none = ProjectState(real_apps=None)
ok = True
for label, ps in [("omitted", ps_omitted), ("None", ps_none)]:
    ra = ps.real_apps
    print(label, "-> real_apps =", repr(ra), "type=", type(ra).__name__)
    if not (isinstance(ra, set) and len(ra) == 0):
        ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3: a supplied set is stored unchanged (same contents, is a set),
for both empty and non-empty sets."""
import sys
from django.db.migrations.state import ProjectState

ok = True
for supplied in [set(), {"app1", "app2"}]:
    ps = ProjectState(real_apps=supplied)
    ra = ps.real_apps
    print("supplied", supplied, "-> stored", repr(ra), "type=", type(ra).__name__)
    if not isinstance(ra, set) or ra != supplied:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.3: equality holds iff models and real_apps collections are equal.
Two states with same (empty) models but differing real_apps must be unequal;
identical real_apps must be equal. Uses only supported (set) inputs."""
import sys
from django.db.migrations.state import ProjectState

a = ProjectState(real_apps={"foo"})
b = ProjectState(real_apps={"foo"})
c = ProjectState(real_apps={"bar"})
d = ProjectState()  # empty set

print("a==b (same real_apps):", a == b)
print("a==c (diff real_apps):", a == c)
print("a==d (foo vs empty):", a == d)

ok = (a == b) and (a != c) and (a != d)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R4.4: the stored real_apps set is used to exempt relations from dangling-ref
errors. Building a ProjectState from an app registry that references a 'real'
(unmigrated) app should resolve when that app label is in real_apps.
We test the mechanism at the API surface: real_apps flows into StateApps as the
set of real app labels used to skip dangling-reference checks."""
import sys
from django.db.migrations.state import ProjectState

# Construct with a real_apps set; render and confirm real_apps propagates and
# that a set is accepted end-to-end (no coercion path needed).
ps = ProjectState(real_apps={"contenttypes"})
print("real_apps stored:", ps.real_apps, type(ps.real_apps).__name__)
# clone() must preserve real_apps as a set of the same contents
clone = ps.clone()
print("clone real_apps:", clone.real_apps, type(clone.real_apps).__name__)
ok = (isinstance(clone.real_apps, set) and clone.real_apps == {"contenttypes"})
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1: supplying a non-set (list) real_apps raises AssertionError.
Positive control: HOLDS patched, FAILS at base (base coerces list->set)."""
import sys
from django.db.migrations.state import ProjectState

try:
    ps = ProjectState(real_apps=["myapp"])
    print("NO AssertionError raised; real_apps=", getattr(ps, "real_apps", "<unset>"))
    sys.exit(1)
except AssertionError:
    print("AssertionError raised for list real_apps -> OK")
    sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14765: ProjectState.__init__ should assert isinstance(real_apps, set) for a supplied non-None value; None/omitted -> empty set; supplied set stored unchanged.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1): list real_apps -> AssertionError. HOLDS patched, FAILS base (base coerces list->set). POSITIVE CONTROL.
- probe_2 (R1.1 tuple): tuple real_apps -> AssertionError. HOLDS patched, FAILS base.
- probe_3 (R1.2): AssertionError raised before real_apps stored (bare __new__ instance has no real_apps attr after failed __init__). HOLDS patched, FAILS base.
- probe_4 (R2.1/2.2/2.3): omitted and None -> real_apps == empty set, no AssertionError. HOLDS patched.
- probe_5 (R3.1/3.2): empty and non-empty supplied set stored unchanged as a set. HOLDS patched.
- probe_6 (R4.3): equality iff models+real_apps equal; differing real_apps -> unequal (supported set inputs). HOLDS patched.
- probe_7 (R4.4/4.5): real_apps set propagates through clone unchanged. HOLDS patched.

Positive control discrimination confirmed: probes 1-3 all VIOLATED at base (exit 1), HOLD patched (exit 0).

Candidate wrong-fix (weak.diff): retains isinstance-coercion instead of asserting. REJECTED by probes 1,2,3 (no AssertionError raised; still coerces list/tuple). This proves the suite discriminates the lazy fix a weak reading of Req1 permits. probes 4-7 pass under it (as expected — it preserves default/set behavior).

No TOO-WEAK finding: no requirements-conforming alternative patch found that passes all probes yet fails the hidden tests. No VIOLATION: every mandated behavior holds on the patched tree. VERDICT SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""R1: supplying a non-set (list) real_apps raises AssertionError.
Positive control: HOLDS patched, FAILS at base (base coerces list->set)."""
import sys
from django.db.migrations.state import ProjectState

try:
    ps = ProjectState(real_apps=["myapp"])
    print("NO AssertionError raised; real_apps=", getattr(ps, "real_apps", "<unset>"))
    sys.exit(1)
except AssertionError:
    print("AssertionError raised for list real_apps -> OK")
    sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14765: ProjectState.__init__ should assert isinstance(real_apps, set) for a supplied non-None value; None/omitted -> empty set; supplied set stored unchanged.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1): list real_apps -> AssertionError. HOLDS patched, FAILS base (base coerces list->set). POSITIVE CONTROL.
- probe_2 (R1.1 tuple): tuple real_apps -> AssertionError. HOLDS patched, FAILS base.
- probe_3 (R1.2): AssertionError raised before real_apps stored (bare __new__ instance has no real_apps attr after failed __init__). HOLDS patched, FAILS base.
- probe_4 (R2.1/2.2/2.3): omitted and None -> real_apps == empty set, no AssertionError. HOLDS patched.
- probe_5 (R3.1/3.2): empty and non-empty supplied set stored unchanged as a set. HOLDS patched.
- probe_6 (R4.3): equality iff models+real_apps equal; differing real_apps -> unequal (supported set inputs). HOLDS patched.
- probe_7 (R4.4/4.5): real_apps set propagates through clone unchanged. HOLDS patched.

Positive control discrimination confirmed: probes 1-3 all VIOLATED at base (exit 1), HOLD patched (exit 0).

Candidate wrong-fix (weak.diff): retains isinstance-coercion instead of asserting. REJECTED by probes 1,2,3 (no AssertionError raised; still coerces list/tuple). This proves the suite discriminates the lazy fix a weak reading of Req1 permits. probes 4-7 pass under it (as expected — it preserves default/set behavior).

No TOO-WEAK finding: no requirements-conforming alternative patch found that passes all probes yet fails the hidden tests. No VIOLATION: every mandated behavior holds on the patched tree. VERDICT SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces defensive isinstance-coercion with: real_apps None -> set(); else assert isinstance(real_apps, set); self.real_apps = real_apps. Req 1 (assert on non-set), Req 2 (None default), Req 3 (set stored unchanged) exactly describe this. Req 4 (preservation of rendering/equality/relation behavior) is a no-behavior-change umbrella consistent with the patch touching only __init__ assignment. Note Req 1 example includes 'list, tuple, or other iterable' and empty list [] now raises (base tolerated it) — both verified. Faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The core behavioral requirement (assert real_apps is a set when non-None, default empty set on None/absent, store supplied set unchanged, raise AssertionError otherwise) is derivable verbatim from the PUBLIC problem_statement, which literally states 'it can just assert that it's a set when non-None.' The hidden test test_real_apps_non_set passes real_apps=['contenttypes'] and checks AssertionError; the requirements mention 'a list, tuple, or other iterable' only as generic non-set examples — no 'contenttypes' string, no test name/path/id, no assertRaises structure. Requirement 4's enumeration (swappable models, unused-models-with-custom-managers, mixed-case labels, dangling references, rendering/equality/relations) overlaps with PASS_TO_PASS regression test names, but those are pre-existing tests describing general ProjectState behavior, and the clause reads as a legitimate 'no regressions' behavioral description rather than a reconstruction of the hidden FAIL_TO_PASS test. Module/attribute names (ProjectState, state.py, real_apps) are legitimate localization, not fix-invented identifiers. No quoted test/gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
