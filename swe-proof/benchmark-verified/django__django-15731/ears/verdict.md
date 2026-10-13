# P2 adversarial audit — django__django-15731

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
"""R1.1/R1.2 + positive control: manager proxy signature equals QuerySet method's, not (*args, **kwargs)."""
import inspect
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

m_sig = inspect.signature(Manager.bulk_create)
q_sig = inspect.signature(QuerySet.bulk_create)
print("manager bulk_create:", m_sig)
print("queryset bulk_create:", q_sig)

params = list(m_sig.parameters)
is_generic = params == ["args", "kwargs"] and \
    m_sig.parameters["args"].kind == inspect.Parameter.VAR_POSITIONAL
print("is_generic variadic:", is_generic)

ok = (str(m_sig) == str(q_sig)) and not is_generic
print("MATCH:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.3: underlying QuerySet method discoverable via __wrapped__ chain."""
import inspect
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

wrapped = getattr(Manager.bulk_create, "__wrapped__", None)
print("__wrapped__:", wrapped)
# inspect.unwrap should reach the QuerySet function
unwrapped = inspect.unwrap(Manager.bulk_create)
qs_func = QuerySet.bulk_create
print("unwrapped:", unwrapped)
print("qs func:", qs_func)
ok = wrapped is not None and unwrapped is qs_func
print("OK:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1/R2.2/R2.3/R2.4: identity/doc/qualname/module/annotations match underlying QuerySet method."""
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

failures = []
# use a method with a docstring; get has one, bulk_create has one
for name in ["bulk_create", "get", "count", "filter"]:
    mm = getattr(Manager, name)
    qm = getattr(QuerySet, name)
    for attr in ["__name__", "__doc__", "__qualname__", "__module__", "__annotations__"]:
        mv = getattr(mm, attr, "<MISSING>")
        qv = getattr(qm, attr, "<MISSING>")
        if mv != qv:
            failures.append((name, attr, mv, qv))

for f in failures:
    print("MISMATCH", f)
print("num failures:", len(failures))
raise SystemExit(0 if not failures else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.5: full __dict__ metadata propagated, incl. custom attrs on the QuerySet method.
We synthesize a fresh queryset with a custom-attributed method and regenerate proxies."""
from django.db.models.query import QuerySet
from django.db.models.manager import BaseManager

# Build a subclass method carrying a custom attribute; ensure it propagates.
class MyQS(QuerySet):
    def frobnicate(self, x, y=3):
        "frob docs"
        return (x, y)
    frobnicate.custom_marker = "PROPAGATE_ME"

methods = BaseManager._get_queryset_methods(MyQS)
proxy = methods.get("frobnicate")
print("proxy:", proxy)
if proxy is None:
    print("frobnicate not proxied")
    raise SystemExit(1)
marker = getattr(proxy, "custom_marker", None)
print("custom_marker:", marker)
# also __dict__ propagation
print("proxy __dict__ keys:", sorted(proxy.__dict__.keys()))
ok = marker == "PROPAGATE_ME"
print("OK:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.1/R3.3: forwarding behavior preserved — proxy delegates to get_queryset()."""
from django.db.models.manager import BaseManager

calls = []

class FakeQS:
    def get(self, *args, **kwargs):
        calls.append(("get", args, kwargs))
        return "RESULT"
    get.queryset_only = False

# generate methods from a QuerySet-like class
from django.db.models.query import QuerySet

class MyQS(QuerySet):
    def echo(self, a, b=2, *rest, **kw):
        return ("echo", a, b, rest, kw)

methods = BaseManager._get_queryset_methods(MyQS)
proxy = methods["echo"]

class FakeManager:
    def get_queryset(self):
        return MyQS.__new__(MyQS)  # instance; echo doesn't touch state

# bind proxy as a method
import types
mgr = FakeManager()
bound = types.MethodType(proxy, mgr)
res = bound(10, 20, 30, k=99)
print("result:", res)
ok = res == ("echo", 10, 20, (30,), {"k": 99})
print("OK:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.2: set of proxied methods unchanged — queryset_only skipped, underscore skipped, public copied."""
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet

class MyQS(QuerySet):
    def public_method(self):
        return 1
    def _private(self):
        return 2
    def only_qs(self):
        return 3
    only_qs.queryset_only = True
    def _allowed(self):
        return 4
    _allowed.queryset_only = False

methods = BaseManager._get_queryset_methods(MyQS)
print("public_method proxied:", "public_method" in methods)
print("_private proxied:", "_private" in methods)
print("only_qs proxied:", "only_qs" in methods)
print("_allowed proxied:", "_allowed" in methods)
# standard public ones still there
for n in ["get", "count", "filter", "bulk_create"]:
    print(n, "in methods:", n in methods)

ok = ("public_method" in methods and
      "_private" not in methods and
      "only_qs" not in methods and
      "_allowed" in methods and
      all(n in methods for n in ["get", "count", "filter", "bulk_create"]))
print("OK:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.2 + positive control: manager proxy signature equals QuerySet method's, not (*args, **kwargs)."""
import inspect
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

m_sig = inspect.signature(Manager.bulk_create)
q_sig = inspect.signature(QuerySet.bulk_create)
print("manager bulk_create:", m_sig)
print("queryset bulk_create:", q_sig)

params = list(m_sig.parameters)
is_generic = params == ["args", "kwargs"] and \
    m_sig.parameters["args"].kind == inspect.Parameter.VAR_POSITIONAL
print("is_generic variadic:", is_generic)

ok = (str(m_sig) == str(q_sig)) and not is_generic
print("MATCH:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15731: gold patch wraps the dynamically-generated manager proxy (manager_method) with functools.wraps(method), replacing the old hand-copy of __name__/__doc__ only, so proxy methods now carry the wrapped QuerySet method's full introspection metadata (signature, __wrapped__, __qualname__, __module__, __annotations__, __dict__).

Probes (all standalone, stdlib + django only), results PATCHED / BASE / WEAK:
- probe_1 (R1.1/R1.2, POSITIVE CONTROL): inspect.signature(Manager.bulk_create) equals QuerySet.bulk_create's full param list and is not (*args,**kwargs). HOLDS patched / FAILS base (base shows (self,*args,**kwargs)) / FAILS weak. Discriminates.
- probe_2 (R1.3): __wrapped__ set and inspect.unwrap resolves to QuerySet.bulk_create. HOLDS patched / FAILS base / FAILS weak.
- probe_3 (R2.1-R2.4): __name__/__doc__/__qualname__/__module__/__annotations__ match underlying QuerySet method for bulk_create,get,count,filter. HOLDS patched / (base fails - not run separately but weak covers qualname/module; base fails on annotations/qualname) / HOLDS weak (weak also copies qualname+module, and these methods have no annotations, so probe_3 doesn't discriminate weak — intentional; probes 1/2/4 do).
- probe_4 (R2.5): custom attribute on a QuerySet method propagates to proxy __dict__ (functools.wraps copies __dict__). HOLDS patched / FAILS base / FAILS weak.
- probe_5 (R3.1/R3.3): proxy still delegates to get_queryset() forwarding all args and returning result. HOLDS patched / HOLDS weak (regression preserved).
- probe_6 (R3.2): proxied-method selection rules unchanged (public copied, _private skipped, queryset_only skipped, _allowed with queryset_only=False copied, standard get/count/filter/bulk_create present). HOLDS patched / HOLDS weak.

Candidate wrong-fix (weak.diff): the pre-fix approach extended to also copy __qualname__ and __module__ but NOT the signature/__wrapped__/__dict__. It is a requirements-conforming-looking lazy fix but is REJECTED by probes 1, 2, and 4 — demonstrating the suite discriminates the signature requirement (R1) and full-metadata propagation requirement (R2.5) that the naive copy cannot satisfy. No probe-conforming alternative found that would leave hidden tests unresolved.

Conclusion: 6/6 probes hold on the gold-patched tree; positive control (probe_1) fails at base (prepatch reproduced); the plausible weak patch is rejected. Requirements are faithful and adequately tight.

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
"""R1.1/R1.2 + positive control: manager proxy signature equals QuerySet method's, not (*args, **kwargs)."""
import inspect
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

m_sig = inspect.signature(Manager.bulk_create)
q_sig = inspect.signature(QuerySet.bulk_create)
print("manager bulk_create:", m_sig)
print("queryset bulk_create:", q_sig)

params = list(m_sig.parameters)
is_generic = params == ["args", "kwargs"] and \
    m_sig.parameters["args"].kind == inspect.Parameter.VAR_POSITIONAL
print("is_generic variadic:", is_generic)

ok = (str(m_sig) == str(q_sig)) and not is_generic
print("MATCH:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15731: gold patch wraps the dynamically-generated manager proxy (manager_method) with functools.wraps(method), replacing the old hand-copy of __name__/__doc__ only, so proxy methods now carry the wrapped QuerySet method's full introspection metadata (signature, __wrapped__, __qualname__, __module__, __annotations__, __dict__).

Probes (all standalone, stdlib + django only), results PATCHED / BASE / WEAK:
- probe_1 (R1.1/R1.2, POSITIVE CONTROL): inspect.signature(Manager.bulk_create) equals QuerySet.bulk_create's full param list and is not (*args,**kwargs). HOLDS patched / FAILS base (base shows (self,*args,**kwargs)) / FAILS weak. Discriminates.
- probe_2 (R1.3): __wrapped__ set and inspect.unwrap resolves to QuerySet.bulk_create. HOLDS patched / FAILS base / FAILS weak.
- probe_3 (R2.1-R2.4): __name__/__doc__/__qualname__/__module__/__annotations__ match underlying QuerySet method for bulk_create,get,count,filter. HOLDS patched / (base fails - not run separately but weak covers qualname/module; base fails on annotations/qualname) / HOLDS weak (weak also copies qualname+module, and these methods have no annotations, so probe_3 doesn't discriminate weak — intentional; probes 1/2/4 do).
- probe_4 (R2.5): custom attribute on a QuerySet method propagates to proxy __dict__ (functools.wraps copies __dict__). HOLDS patched / FAILS base / FAILS weak.
- probe_5 (R3.1/R3.3): proxy still delegates to get_queryset() forwarding all args and returning result. HOLDS patched / HOLDS weak (regression preserved).
- probe_6 (R3.2): proxied-method selection rules unchanged (public copied, _private skipped, queryset_only skipped, _allowed with queryset_only=False copied, standard get/count/filter/bulk_create present). HOLDS patched / HOLDS weak.

Candidate wrong-fix (weak.diff): the pre-fix approach extended to also copy __qualname__ and __module__ but NOT the signature/__wrapped__/__dict__. It is a requirements-conforming-looking lazy fix but is REJECTED by probes 1, 2, and 4 — demonstrating the suite discriminates the signature requirement (R1) and full-metadata propagation requirement (R2.5) that the naive copy cannot satisfy. No probe-conforming alternative found that would leave hidden tests unresolved.

Conclusion: 6/6 probes hold on the gold-patched tree; positive control (probe_1) fails at base (prepatch reproduced); the plausible weak patch is rejected. Requirements are faithful and adequately tight.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** R2.4 (annotations equal underlying) holds vacuously here since QuerySet.bulk_create has no annotations ({}), but @wraps copies __annotations__ so it would hold generally. R2.5's 'whole attribute dict' claim is faithful: wraps runs manager_method.__dict__.update(method.__dict__). No requirement pins a narrower boundary than the actual change; boundary is correct.

Counterexample / evidence:

```
N/A — probe HOLDS on patched tree, VIOLATED on base, matching every acceptance criterion.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes behavior at the level of the public problem_statement plus standard consequences of functools.wraps (which the problem_statement explicitly names as the fix). Named identifiers — BaseManager._get_queryset_methods, manager.py, bulk_create, get_queryset, queryset_only, from_queryset — are legitimate localization; queryset_only/from_queryset are real public Django API, not fix-invented. Req 1.2 enumerates parameters objs, batch_size, ignore_conflicts, all of which appear verbatim in the public problem_statement ('expected: (objs, batch_size=None, ignore_conflicts=False)'), and it deliberately stops at 'and further keyword parameters' rather than reproducing the hidden test's exact signature string (which additionally includes update_conflicts, update_fields, unique_fields). No test names (test_manager_method_signature/test_manager_method_attributes), no test file path (tests/basic/tests.py), no Article.objects, no quoted test/gold code, and no test-shaped case enumeration. The __wrapped__/wrapped-chain and metadata-attribute requirements are the documented effect of functools.wraps, not reconstruction of gold or tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
