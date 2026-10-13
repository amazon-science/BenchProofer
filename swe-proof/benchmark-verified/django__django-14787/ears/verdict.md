# P2 adversarial audit — django__django-14787

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
"""Positive control: Req1.3 — the callable passed into the wrapped decorator
exposes __name__ equal to the original method's name (no AttributeError).
On base, partial has no __name__ -> AttributeError -> decorator crashes."""
import sys
from django.utils.decorators import method_decorator

seen = {}

def logging_dec(func):
    # user decorator that reads func.__name__ (crashes on partial at base)
    seen["name"] = func.__name__
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner

class C:
    @method_decorator(logging_dec)
    def hello(self):
        "docstring"
        return 42

try:
    r = C().hello()
except AttributeError as e:
    print("FAIL: AttributeError reading __name__:", e)
    sys.exit(1)

print("return:", r, "seen __name__:", seen.get("name"))
if r == 42 and seen.get("name") == "hello":
    print("HOLDS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 — the callable the wrapped decorator receives exposes __name__,
__module__, __qualname__, __doc__, __annotations__ each equal to the original
method's corresponding attribute."""
import sys
from django.utils.decorators import method_decorator

captured = {}

def capture_dec(func):
    for a in ("__name__", "__module__", "__qualname__", "__doc__", "__annotations__"):
        captured[a] = getattr(func, a, "<<MISSING>>")
    def inner(*a, **k):
        return func(*a, **k)
    return inner

class C:
    @method_decorator(capture_dec)
    def target(self, x: int) -> int:
        "the doc"
        return x

# reference metadata from the original underlying function
orig = C.__dict__  # not the wrapper; get original via a fresh undecorated copy
def target(self, x: int) -> int:
    "the doc"
    return x

C().target(1)
expected = {
    "__name__": "target",
    "__qualname__": "C.target",
    "__doc__": "the doc",
    "__annotations__": {"x": int, "return": int},
}
ok = True
print("captured:", captured)
for k, v in expected.items():
    if captured.get(k) != v:
        print(f"MISMATCH {k}: got {captured.get(k)!r} want {v!r}")
        ok = False
if captured.get("__module__") in (None, "<<MISSING>>"):
    print("MISSING __module__")
    ok = False
if ok:
    print("HOLDS")
    sys.exit(0)
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.5 / Req2.2 — attributes previously attached to the method (its __dict__)
are reflected on the callable handed to the decorator (update_wrapper WRAPPER_UPDATES
copies __dict__)."""
import sys
from django.utils.decorators import method_decorator

captured = {}

def capture_dec(func):
    captured["extra"] = getattr(func, "custom_attr", "<<MISSING>>")
    captured["dict_has"] = "custom_attr" in getattr(func, "__dict__", {})
    def inner(*a, **k):
        return func(*a, **k)
    return inner

def attach(func):
    func.custom_attr = "hello-attr"
    return func

class C:
    @method_decorator(capture_dec)
    @attach
    def target(self):
        return 1

C().target()
print("captured:", captured)
if captured.get("extra") == "hello-attr" and captured.get("dict_has"):
    print("HOLDS")
    sys.exit(0)
print("FAIL: method __dict__ not reflected on callable")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1 — the FINAL wrapper returned by method_decorator still exposes the
original method's identity attributes (name/qualname/doc). Regression."""
import sys
from django.utils.decorators import method_decorator

def dec(func):
    def inner(*a, **k):
        return func(*a, **k)
    return inner

class C:
    @method_decorator(dec)
    def target(self):
        "docs here"
        return 7

w = C.target  # the wrapper (function, unbound)
print("name", w.__name__, "qual", w.__qualname__, "doc", w.__doc__)
ok = (w.__name__ == "target" and w.__qualname__ == "C.target"
      and w.__doc__ == "docs here" and C().target() == 7)
if ok:
    print("HOLDS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.3 — tuple of decorators: applied in order they appear; all added
attributes preserved on the resulting wrapper; and Req2.7/2.8 return value intact."""
import sys
from django.utils.decorators import method_decorator

order = []

def make(tag):
    def dec(func):
        order.append(("apply", tag))
        def inner(*a, **k):
            order.append(("call", tag))
            return func(*a, **k)
        inner.__dict__[f"attr_{tag}"] = tag
        return inner
    return dec

class C:
    @method_decorator((make("a"), make("b")))
    def target(self):
        return "R"

r = C().target()
w = C.target
print("order:", order, "ret:", r)
# call order: outermost first. In _multi_decorate decorators applied in reversed()
# so that they run in listed order at call time: a before b.
call_seq = [t for kind, t in order if kind == "call"]
print("call_seq:", call_seq)
attrs_ok = getattr(w, "attr_a", None) == "a" and getattr(w, "attr_b", None) == "b"
if r == "R" and call_seq == ["a", "b"] and attrs_ok:
    print("HOLDS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.5 / Req2.6 — name-based errors: ValueError for non-existent/non-method
name; TypeError for a non-callable attribute. Regression preservation."""
import sys
from django.utils.decorators import method_decorator

def dec(func):
    def inner(*a, **k):
        return func(*a, **k)
    return inner

ok = True

# Non-existent name -> ValueError
try:
    @method_decorator(dec, name="nope")
    class A:
        def real(self):
            return 1
    print("FAIL: no ValueError for missing name")
    ok = False
except ValueError as e:
    print("ValueError ok:", e)

# Non-callable attribute -> TypeError
try:
    @method_decorator(dec, name="attr")
    class B:
        attr = 5
    print("FAIL: no TypeError for non-callable")
    ok = False
except TypeError as e:
    print("TypeError ok:", e)

if ok:
    print("HOLDS")
    sys.exit(0)
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.3 — the callable passed into the wrapped decorator
exposes __name__ equal to the original method's name (no AttributeError).
On base, partial has no __name__ -> AttributeError -> decorator crashes."""
import sys
from django.utils.decorators import method_decorator

seen = {}

def logging_dec(func):
    # user decorator that reads func.__name__ (crashes on partial at base)
    seen["name"] = func.__name__
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner

class C:
    @method_decorator(logging_dec)
    def hello(self):
        "docstring"
        return 42

try:
    r = C().hello()
except AttributeError as e:
    print("FAIL: AttributeError reading __name__:", e)
    sys.exit(1)

print("return:", r, "seen __name__:", seen.get("name"))
if r == 42 and seen.get("name") == "hello":
    print("HOLDS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14787: method_decorator/_multi_decorate must wrap the bound partial with functools.wraps(method) so the callable handed to the wrapped decorator carries the original method's identity metadata. Gold: bound_method = wraps(method)(partial(method.__get__(self, type(self)))).

6 probes, all HOLD on gold-patched tree (exit 0):
- probe_1 (POSITIVE CONTROL, Req1.3): user decorator reads func.__name__. PATCHED: name='hello', ret=42, HOLDS. BASE: AttributeError 'functools.partial' has no attribute '__name__' -> VIOLATED (exit 1). Discriminates => prepatch_reproduced=true.
- probe_2 (Req1.2): callable exposes __name__/__module__/__qualname__/__doc__/__annotations__ equal to original method. PATCHED HOLDS; BASE all missing/wrong.
- probe_3 (Req1.5/2.2): method __dict__ attribute (custom_attr) reflected on callable. PATCHED HOLDS; BASE missing.
- probe_4 (Req2.1): final wrapper still exposes name/qualname/doc; return intact. HOLDS.
- probe_5 (Req2.3/2.7/2.8): tuple of decorators applied in listed call order (a,b), added attrs preserved on wrapper, return unchanged. HOLDS.
- probe_6 (Req2.5/2.6): ValueError for nonexistent name, TypeError for non-callable attribute. HOLDS.

CANDIDATE PATCH (weak_name_module_only): a lazy reading of Req1.3/1.4 that only manually sets bound_method.__name__ and __module__ on the bare partial (no functools.wraps). This satisfies the narrow FAIL_TO_PASS reading (checks only __name__ and __module__ is not None) but is REJECTED by the probe suite: probe_2 fails (__doc__ still the partial's docstring, __annotations__ MISSING) and probe_3 fails (method __dict__ not copied). This demonstrates the suite discriminates a plausibly-wrong partial fix and requires true update_wrapper semantics (Req1.6). No requirements-conforming patch was found that fails the hidden tests.

Verdict SOUND: >=5 distinct probes all hold on patched; positive control holds patched and fails at base; >=1 candidate patch exercised and REJECTED by the suite.

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
"""Positive control: Req1.3 — the callable passed into the wrapped decorator
exposes __name__ equal to the original method's name (no AttributeError).
On base, partial has no __name__ -> AttributeError -> decorator crashes."""
import sys
from django.utils.decorators import method_decorator

seen = {}

def logging_dec(func):
    # user decorator that reads func.__name__ (crashes on partial at base)
    seen["name"] = func.__name__
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner

class C:
    @method_decorator(logging_dec)
    def hello(self):
        "docstring"
        return 42

try:
    r = C().hello()
except AttributeError as e:
    print("FAIL: AttributeError reading __name__:", e)
    sys.exit(1)

print("return:", r, "seen __name__:", seen.get("name"))
if r == 42 and seen.get("name") == "hello":
    print("HOLDS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14787: method_decorator/_multi_decorate must wrap the bound partial with functools.wraps(method) so the callable handed to the wrapped decorator carries the original method's identity metadata. Gold: bound_method = wraps(method)(partial(method.__get__(self, type(self)))).

6 probes, all HOLD on gold-patched tree (exit 0):
- probe_1 (POSITIVE CONTROL, Req1.3): user decorator reads func.__name__. PATCHED: name='hello', ret=42, HOLDS. BASE: AttributeError 'functools.partial' has no attribute '__name__' -> VIOLATED (exit 1). Discriminates => prepatch_reproduced=true.
- probe_2 (Req1.2): callable exposes __name__/__module__/__qualname__/__doc__/__annotations__ equal to original method. PATCHED HOLDS; BASE all missing/wrong.
- probe_3 (Req1.5/2.2): method __dict__ attribute (custom_attr) reflected on callable. PATCHED HOLDS; BASE missing.
- probe_4 (Req2.1): final wrapper still exposes name/qualname/doc; return intact. HOLDS.
- probe_5 (Req2.3/2.7/2.8): tuple of decorators applied in listed call order (a,b), added attrs preserved on wrapper, return unchanged. HOLDS.
- probe_6 (Req2.5/2.6): ValueError for nonexistent name, TypeError for non-callable attribute. HOLDS.

CANDIDATE PATCH (weak_name_module_only): a lazy reading of Req1.3/1.4 that only manually sets bound_method.__name__ and __module__ on the bare partial (no functools.wraps). This satisfies the narrow FAIL_TO_PASS reading (checks only __name__ and __module__ is not None) but is REJECTED by the probe suite: probe_2 fails (__doc__ still the partial's docstring, __annotations__ MISSING) and probe_3 fails (method __dict__ not copied). This demonstrates the suite discriminates a plausibly-wrong partial fix and requires true update_wrapper semantics (Req1.6). No requirements-conforming patch was found that fails the hidden tests.

Verdict SOUND: >=5 distinct probes all hold on patched; positive control holds patched and fails at base; >=1 candidate patch exercised and REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (patched): captured name='hello_world', module non-None, qualname endswith hello_world, doc='docstring here', annotations={'return': str}, __dict__ includes __wrapped__. Probe (base): AttributeError at func.__name__ inside decorator via _wrapper. Error messages: ValueError 'The keyword argument `name` must be the name of a method of...'; TypeError "Cannot decorate 'x' as it isn't a callable attribute...". Requirement 2.6's phrasing ('not a callable attribute') is a faithful paraphrase of the real 'isn't a callable attribute' message, not a mismatch. Boundary is correctly pinned to the changed callable-metadata behavior rather than a narrow helper slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally and stays within public knowledge. The attribute enumeration in Req 1.2 (__name__/__module__/__qualname__/__doc__/__annotations__) is functools.WRAPPER_ASSIGNMENTS (public stdlib) and does not mirror the hidden test, which only asserts __name__=='method' and __module__ is not None. functools.wraps is named in the public problem_statement. Symbols named (_multi_decorate, _wrapper, functools.partial) are pre-existing source identifiers used for legitimate localization; the gold-patch local 'bound_method' is NOT surfaced ('bound callable' is used instead). Req 2's preserved-behavior list (tuple/argumented/descriptors/ValueError-for-bad-name/TypeError-for-non-callable) reflects source-visible existing behavior of method_decorator (the raises are in the code), not the hidden PASS_TO_PASS test suite. No test names, file paths, ids, quoted test/gold code, or fix-invented identifiers present.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
