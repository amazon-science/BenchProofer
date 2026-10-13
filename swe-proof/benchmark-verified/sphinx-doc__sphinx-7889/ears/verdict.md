# P2 adversarial audit — sphinx-doc__sphinx-7889

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
"""Req1.1 / Req1.4 (POSITIVE CONTROL): subscription with a non-string key
(a TypeVar) returns a _MockObject rather than raising. FAILS at base."""
import sys
from typing import TypeVar
from sphinx.ext.autodoc.mock import _MockObject

m = _MockObject()
T = TypeVar('T')
try:
    result = m[T]
except Exception as e:
    print("subscription raised:", type(e).__name__, e)
    sys.exit(1)
print("result:", repr(result), "type:", type(result).__name__)
if not isinstance(result, _MockObject):
    print("FAIL: result not a _MockObject")
    sys.exit(1)
# Req1.4: must be further indexable/attr-accessible/callable without error
_ = result[T]
_ = result.some_attr
_ = result()
print("PASS: non-string subscription returns usable _MockObject")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2: identity of returned object derived from textual representation of
the key (str(key)). The display name of a subscript result must incorporate
str(key). We check that subscripting with an object whose str() is distinctive
yields a mock whose __display_name__ contains that text."""
import sys
from sphinx.ext.autodoc.mock import _MockObject

class Weird:
    def __str__(self):
        return "WEIRDKEY"
    def __repr__(self):
        return "<Weird repr should not be used>"

m = _MockObject()
# give the base a known display name
try:
    dn_base = m.__display_name__
except Exception as e:
    print("no __display_name__:", e); sys.exit(1)
res = m[Weird()]
dn = res.__display_name__
print("base display:", dn_base, "| result display:", dn)
if "WEIRDKEY" not in dn:
    print("FAIL: str(key) 'WEIRDKEY' not reflected in display name:", dn)
    sys.exit(1)
print("PASS: display name derived from str(key)")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3: string key behaves exactly as before — returns a _MockObject
identified by that string key (display name reflects the string)."""
import sys
from sphinx.ext.autodoc.mock import _MockObject

m = _MockObject()
res = m["Foo"]
print("type:", type(res).__name__, "display:", res.__display_name__)
if not isinstance(res, _MockObject):
    print("FAIL: not a _MockObject"); sys.exit(1)
if "Foo" not in res.__display_name__:
    print("FAIL: string key 'Foo' not in display name"); sys.exit(1)
print("PASS: string subscription unchanged")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2: a class may subclass a parametrized mocked base. Mirrors the hidden
test: class SubClass2(mock.SomeClass[T]) completes without TypeError, doc
preserved, instance is genuine."""
import sys
from typing import TypeVar
from sphinx.ext.autodoc.mock import _MockObject

mock = _MockObject()
T = TypeVar('T')
try:
    class SubClass2(mock.SomeClass[T]):
        """docstring of SubClass"""
except TypeError as e:
    print("FAIL: subclassing parametrized mock raised TypeError:", e)
    sys.exit(1)

obj2 = SubClass2()
print("doc:", repr(SubClass2.__doc__))
if SubClass2.__doc__ != "docstring of SubClass":
    print("FAIL: docstring not preserved"); sys.exit(1)
if not isinstance(obj2, SubClass2):
    print("FAIL: obj2 not instance of SubClass2"); sys.exit(1)
print("PASS: parametrized mock subclass works")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.3: preserve existing behaviors — attribute chains stay mocks,
call returns mock, decorator-with-callable returns arg unchanged, direct
subclass real methods execute and doc preserved."""
import sys
from sphinx.ext.autodoc.mock import _MockObject

mock = _MockObject()
# 3.1 attribute chains
assert isinstance(mock.attr1, _MockObject)
assert isinstance(mock.attr1.attr2, _MockObject)
assert isinstance(mock.attr1.attr2.meth(), _MockObject)
# 3.2 call returns mock
assert isinstance(mock(), _MockObject)
# 3.2 decorator with a function returns it unchanged
def realfunc():
    return 42
assert mock(realfunc) is realfunc, "decorator with function should return it unchanged"
# decorator with a class returns it unchanged
class C: pass
assert mock(C) is C, "decorator with class should return it unchanged"

# 3.3 direct subclass
class SubClass(mock.SomeClass):
    """docstring of SubClass"""
    def method(self):
        return "string"
    def other_method(self):
        return SubClass()

obj = SubClass()
assert SubClass.__doc__ == "docstring of SubClass"
assert obj.method() == "string", "real method must return real result"
assert isinstance(obj.other_method(), SubClass)
print("PASS: existing mock behaviors preserved")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.4/3.6: module mocking works within context and cleans up after."""
import sys
from importlib import import_module
from sphinx.ext.autodoc.mock import mock, _MockObject

modname = 'sphinx.unknown'
submod = modname + '.submodule'
with mock([modname]):
    mod = import_module(modname)
    print("module:", mod)
    # attribute access yields a mock object
    assert isinstance(mod.some_attr, _MockObject), "module attr not a mock"
    # descendant import succeeds
    sub = import_module(submod)
    assert sub is not None
# after context: import hooks removed, modules invalidated
try:
    import_module(modname)
    print("FAIL: module still importable after context exit")
    sys.exit(1)
except ImportError:
    pass
print("PASS: module mocking active in context and cleaned up")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 / Req1.4 (POSITIVE CONTROL): subscription with a non-string key
(a TypeVar) returns a _MockObject rather than raising. FAILS at base."""
import sys
from typing import TypeVar
from sphinx.ext.autodoc.mock import _MockObject

m = _MockObject()
T = TypeVar('T')
try:
    result = m[T]
except Exception as e:
    print("subscription raised:", type(e).__name__, e)
    sys.exit(1)
print("result:", repr(result), "type:", type(result).__name__)
if not isinstance(result, _MockObject):
    print("FAIL: result not a _MockObject")
    sys.exit(1)
# Req1.4: must be further indexable/attr-accessible/callable without error
_ = result[T]
_ = result.some_attr
_ = result()
print("PASS: non-string subscription returns usable _MockObject")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: __getitem__ must accept non-string keys by using str(key) in _make_subclass. 6 probes cover Req1.1/1.4 (non-string subscription returns usable _MockObject), Req1.2 (identity derived from str(key)), Req1.3 (string key unchanged), Req2 (subclassing parametrized mock base: no TypeError, doc preserved, genuine instance), Req3.1/3.2/3.3 (attr chains, call/decorator-passthrough, direct subclass real methods), Req3.4/3.6 (module mock active in context + cleanup). All 6 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (TypeError: can only concatenate str (not TypeVar) to str) and HOLDS patched — discriminating. Candidate weak patch (try _make_subclass(key,...) except TypeError: return self) satisfies probe_1/4 crash-avoidance but is REJECTED by probe_2: Req1.2 mandates the returned identity derive from str(key); the weak fix drops the key text (display name stays '_MockObject', not '_MockObject.WEIRDKEY'). Suite thus discriminates wrong implementations; no requirement-conforming alternative found. Note: the weak patch would also likely diverge from gold hidden-test display-name expectations, but probe_2 already rejects it on requirement grounds.

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
"""Req1.1 / Req1.4 (POSITIVE CONTROL): subscription with a non-string key
(a TypeVar) returns a _MockObject rather than raising. FAILS at base."""
import sys
from typing import TypeVar
from sphinx.ext.autodoc.mock import _MockObject

m = _MockObject()
T = TypeVar('T')
try:
    result = m[T]
except Exception as e:
    print("subscription raised:", type(e).__name__, e)
    sys.exit(1)
print("result:", repr(result), "type:", type(result).__name__)
if not isinstance(result, _MockObject):
    print("FAIL: result not a _MockObject")
    sys.exit(1)
# Req1.4: must be further indexable/attr-accessible/callable without error
_ = result[T]
_ = result.some_attr
_ = result()
print("PASS: non-string subscription returns usable _MockObject")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: __getitem__ must accept non-string keys by using str(key) in _make_subclass. 6 probes cover Req1.1/1.4 (non-string subscription returns usable _MockObject), Req1.2 (identity derived from str(key)), Req1.3 (string key unchanged), Req2 (subclassing parametrized mock base: no TypeError, doc preserved, genuine instance), Req3.1/3.2/3.3 (attr chains, call/decorator-passthrough, direct subclass real methods), Req3.4/3.6 (module mock active in context + cleanup). All 6 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (TypeError: can only concatenate str (not TypeVar) to str) and HOLDS patched — discriminating. Candidate weak patch (try _make_subclass(key,...) except TypeError: return self) satisfies probe_1/4 crash-avoidance but is REJECTED by probe_2: Req1.2 mandates the returned identity derive from str(key); the weak fix drops the key text (display name stays '_MockObject', not '_MockObject.WEIRDKEY'). Suite thus discriminates wrong implementations; no requirement-conforming alternative found. Note: the weak patch would also likely diverge from gold hidden-test display-name expectations, but probe_2 already rejects it on requirement grounds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched image: R1.1 mo[TypeVar] returns a _MockObject (no exception); R1.2 the returned object's __display_name__ contains str(T) (identity derived from textual repr); R1.3 string keys still work ('Foo' in display name); R1.4 result is a _MockObject. R2: `class Sub(Base[T])` completes, __doc__ preserved verbatim ('docstring here'), Sub() is a real instance. R3.2 decorator: mo(func) is func, mo(class) is class, mo(1,2)/mo() return mocks. R3.3 direct subclass of _MockObject preserves __doc__ and runs own methods (g()==7). Base (unpatched) raises 'can only concatenate str (not "TypeVar") to str' on mo[T], confirming the modeling boundary (subscription with non-string keys) matches the actual changed observable behavior — not a narrow branch or helper. R3.4/R3.5/R3.6 (module mocking, ABC checks, context-manager teardown) are unchanged by the patch and remain true; requirements correctly describe them as preserved behavior. No requirement mandates behavior absent from the patch, forbids present behavior, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior only. Named symbols (_MockObject, _make_subclass, __getitem__, __getattr__, __doc__) are pre-existing codebase identifiers used for legitimate localization, not fix-invented. Req 1.2 ('textual representation of the key') is a behavioral translation of the gold fix (str(key)), not a quote. Req 2 translates the FAIL_TO_PASS TypeVar-parametrized-subclass assertions into behavior without reproducing the test's identifiers (SubClass2, T), the literal docstring string, test names, or file path (tests/test_ext_autodoc_mock.py::test_MockObject). Req 3's enumeration topically parallels the PASS_TO_PASS suite (test_mock, test_MockModule, test_mock_decorator, test_abc_MockObject, test_mock_does_not_follow_upper_modules) but each clause states the mock module's existing public contract, all derivable from mock.py source rather than from hidden tests. Generic-typing/TypeVar/TypeError-concatenation framing is already in the public problem_statement. No test ids, no quoted test/gold code, no parametrization enumeration.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
