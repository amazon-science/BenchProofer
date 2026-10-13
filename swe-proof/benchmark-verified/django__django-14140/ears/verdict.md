# P2 adversarial audit — django__django-14140

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
import sys
from django.db.models import Q

# Req 1.3: single key/value lookup child -> length-2 tuple in args, empty kwargs
path, args, kwargs = Q(x=1).deconstruct()
print("path=", path)
print("args=", args)
print("kwargs=", kwargs)

ok = (
    path == 'django.db.models.Q'
    and args == (('x', 1),)
    and kwargs == {}
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from django.db.models import Q

# Req 1.4: two+ kv children -> all length-2 tuples in args, stored order
path, args, kwargs = Q(x=1, y=2).deconstruct()
print("args=", args, "kwargs=", kwargs)
ok = (
    set(args) == {('x', 1), ('y', 2)}
    and len(args) == 2
    and kwargs == {}
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
    django.setup()

from django.db.models import Q, Exists
from django.contrib.auth.models import User

qs = User.objects.filter(username='jim')
exists = Exists(qs)

# Req 2.1/2.2: single Exists child -> no TypeError, expression itself sole element of args, empty kwargs
try:
    path, args, kwargs = Q(exists).deconstruct()
except TypeError as e:
    print("TypeError raised:", e)
    print("FAIL")
    sys.exit(1)

print("args=", args, "kwargs=", kwargs)
ok = (
    len(args) == 1
    and args[0] is exists
    and kwargs == {}
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from django.db.models import Q

# Req 2.3: single nested Q child -> nested Q sole element of args, empty kwargs
inner = Q(x=1)
path, args, kwargs = Q(inner).deconstruct()
print("args=", args, "kwargs=", kwargs)
ok = (
    len(args) == 1
    and args[0] is inner
    and kwargs == {}
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from django.db.models import Q

# Req 3 & 4: connector and negation reporting
# AND default -> no _connector
_, a1, k1 = Q(x=1, y=2).deconstruct()
# OR -> _connector present
_, a2, k2 = (Q(x=1) | Q(y=2)).deconstruct()
# negated single kv child -> length-2 tuple in args plus _negated=True
_, a3, k3 = (~Q(x=1)).deconstruct()

print("AND kwargs=", k1)
print("OR kwargs=", k2, "args=", a2)
print("NEG args=", a3, "kwargs=", k3)

ok = (
    '_connector' not in k1
    and k2.get('_connector') == 'OR'
    and '_negated' not in k1
    and a3 == (('x', 1),)
    and k3.get('_negated') is True
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from django.db.models import Q

# Req 5.1: roundtrip equality for AND, OR, negation
cases = [Q(x=1), Q(x=1, y=2), Q(x=1) | Q(y=2), ~Q(x=1), ~(Q(x=1) | Q(y=2))]
ok = True
for q in cases:
    path, args, kwargs = q.deconstruct()
    rebuilt = Q(*args, **kwargs)
    eq = rebuilt == q
    print(repr(q), "->", args, kwargs, "rebuilt==orig:", eq)
    ok = ok and eq
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
    django.setup()

from django.db.models import Q, Exists
from django.contrib.auth.models import User

# Req 5.2: combining a Q wrapping a conditional expression with an empty Q via
# & and | in either order must not raise.
exists = Exists(User.objects.filter(username='jim'))
q = Q(exists)
ok = True
for expr, label in [
    (lambda: q & Q(), "q & Q()"),
    (lambda: Q() & q, "Q() & q"),
    (lambda: q | Q(), "q | Q()"),
    (lambda: Q() | q, "Q() | q"),
]:
    try:
        res = expr()
        print(label, "->", repr(res))
    except Exception as e:
        print(label, "RAISED", type(e).__name__, e)
        ok = False
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from django.db.models import Q

# Req 1.3: single key/value lookup child -> length-2 tuple in args, empty kwargs
path, args, kwargs = Q(x=1).deconstruct()
print("path=", path)
print("args=", args)
print("kwargs=", kwargs)

ok = (
    path == 'django.db.models.Q'
    and args == (('x', 1),)
    and kwargs == {}
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14140: Q.deconstruct must place all children positionally into args, reserving kwargs for connector/negation only. 7 probes cover the requirements:
- probe_1 (Req 1.3): Q(x=1).deconstruct() -> args==(('x',1),), kwargs=={}. HOLDS patched; FAILS base (base returns args=(), kwargs={'x':1}). POSITIVE CONTROL.
- probe_2 (Req 1.4): Q(x=1,y=2) -> two length-2 tuples in args, empty kwargs. HOLDS.
- probe_3 (Req 2.1/2.2): Q(Exists(...)) -> no TypeError, Exists object itself sole element of args, empty kwargs. HOLDS patched; FAILS base with 'Exists' object is not subscriptable. (also discriminates)
- probe_4 (Req 2.3): Q(nested Q) -> nested Q sole element of args, empty kwargs. HOLDS.
- probe_5 (Req 3 & 4): AND emits no _connector; OR emits _connector='OR'; negated single kv child stays length-2 tuple in args plus _negated=True. HOLDS.
- probe_6 (Req 5.1): roundtrip equality Q(*args,**kwargs)==orig for AND/OR/negation cases. HOLDS.
- probe_7 (Req 5.2): combining Q(Exists) with empty Q via &/| in either order does not raise. HOLDS patched; FAILS base. (also discriminates)

All 7 HOLD on the gold-patched tree. Positive control (probe_1) HOLDS patched and FAILS at base -> prepatch reproduced.

WEAK CANDIDATE (weak.diff): replaces the special-case guard `len==1 and not isinstance(child,Q)` with `len==1 and isinstance(child,(tuple,list))`. This fixes the crash (Exists no longer subscripted) but STILL inlines a single kv child into kwargs. REJECTED by probe_1 (single kv child inlined into kwargs instead of args) and probe_5 (negated single kv child inlined). This demonstrates the suite discriminates the lazy 'just stop the crash' fix that leaves the historical kv-inlining behavior in place — i.e. the requirements are not too weak. 1/1 weak candidate rejected.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base vs patched, and a requirements-violating alternative patch is rejected by the probe suite.

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
import sys
from django.db.models import Q

# Req 1.3: single key/value lookup child -> length-2 tuple in args, empty kwargs
path, args, kwargs = Q(x=1).deconstruct()
print("path=", path)
print("args=", args)
print("kwargs=", kwargs)

ok = (
    path == 'django.db.models.Q'
    and args == (('x', 1),)
    and kwargs == {}
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14140: Q.deconstruct must place all children positionally into args, reserving kwargs for connector/negation only. 7 probes cover the requirements:
- probe_1 (Req 1.3): Q(x=1).deconstruct() -> args==(('x',1),), kwargs=={}. HOLDS patched; FAILS base (base returns args=(), kwargs={'x':1}). POSITIVE CONTROL.
- probe_2 (Req 1.4): Q(x=1,y=2) -> two length-2 tuples in args, empty kwargs. HOLDS.
- probe_3 (Req 2.1/2.2): Q(Exists(...)) -> no TypeError, Exists object itself sole element of args, empty kwargs. HOLDS patched; FAILS base with 'Exists' object is not subscriptable. (also discriminates)
- probe_4 (Req 2.3): Q(nested Q) -> nested Q sole element of args, empty kwargs. HOLDS.
- probe_5 (Req 3 & 4): AND emits no _connector; OR emits _connector='OR'; negated single kv child stays length-2 tuple in args plus _negated=True. HOLDS.
- probe_6 (Req 5.1): roundtrip equality Q(*args,**kwargs)==orig for AND/OR/negation cases. HOLDS.
- probe_7 (Req 5.2): combining Q(Exists) with empty Q via &/| in either order does not raise. HOLDS patched; FAILS base. (also discriminates)

All 7 HOLD on the gold-patched tree. Positive control (probe_1) HOLDS patched and FAILS at base -> prepatch reproduced.

WEAK CANDIDATE (weak.diff): replaces the special-case guard `len==1 and not isinstance(child,Q)` with `len==1 and isinstance(child,(tuple,list))`. This fixes the crash (Exists no longer subscripted) but STILL inlines a single kv child into kwargs. REJECTED by probe_1 (single kv child inlined into kwargs instead of args) and probe_5 (negated single kv child inlined). This demonstrates the suite discriminates the lazy 'just stop the crash' fix that leaves the historical kv-inlining behavior in place — i.e. the requirements are not too weak. 1/1 weak candidate rejected.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base vs patched, and a requirements-violating alternative patch is rejected by the probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch removes the len==1 special case so all children go positionally into args; kwargs reserved for _connector/_negated. Requirements pin exactly this changed observable behavior, including the key single-child-lookup boundary (Req 1.3) that was the crux of the change. Modeling boundary is the full deconstruct behavior, not a narrow branch. Verified via nl_attack probe (exit 0) on patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the deconstruct fix behaviorally. All concrete examples (Q(x=1), Q(x=1,y=2), Q(Exists(queryset)), the TypeError 'Exists' object is not subscriptable) are already in the public problem_statement. Identifiers named (query_utils.py, Q, deconstruct, _combine, _connector, _negated, connector, negated, conditional) are pre-existing/gold code being localized, not fix-invented names. Behavioral requirements that map onto hidden tests (single-child→args, nested Q→args, combine-with-empty-Q both orders via &/|, pickle round-trip) are stated as general behavior/round-trip/commutativity properties rather than reproducing test cases. No test names, file paths, node ids, parametrization ids, quoted test/gold code, or test-only fixture identifiers (is_poc, tagged, Tag, gmbh, Employee, Group, Event) appear. This is legitimate test-behavior→requirement translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
