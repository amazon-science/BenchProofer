# P2 adversarial audit — sphinx-doc__sphinx-9658

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
"""Positive control. Req 2 + Req 3: restify of a mock stand-in reached by
multi-level access yields a complete dotted reference (module joined to the
short name), not one truncated at a trailing dot with the final component
missing. HOLDS patched, FAILS at base."""
import sys
from sphinx.ext.autodoc.mock import mock
from sphinx.util.typing import restify

with mock(['unknown']):
    import unknown
    r = restify(unknown.secret.Class)

print("restify:", repr(r))
ok = (r == ':py:class:`unknown.secret.Class`')
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2 + Req 1.1: a stand-in created via subclass factory reports
__qualname__ equal to its __name__, which equals the accessed short name."""
import sys
from sphinx.ext.autodoc.mock import mock

with mock(['unknown']):
    import unknown
    obj = unknown.secret.Class      # multi-level access -> stand-in for 'Class'

name = getattr(obj, '__name__', '<none>')
qn = getattr(obj, '__qualname__', '<none>')
print("__name__:", repr(name))
print("__qualname__:", repr(qn))

# short name must be the final component 'Class' (not full path, not empty),
# and qualname must equal it.
ok = (name == 'Class' and qn == 'Class')
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2 + Req 2.3: base mock object class defines __name__ == '' and a
directly instantiated base mock reports __qualname__ == '' (empty)."""
import sys
from sphinx.ext.autodoc.mock import _MockObject

cls_name = getattr(_MockObject, '__name__', '<none>')
# The class attribute default; type object's own __name__ is '_MockObject',
# so read from the class __dict__ to get the mock's declared default.
declared = _MockObject.__dict__.get('__name__', '<missing>')

inst = _MockObject()
qn = getattr(inst, '__qualname__', '<none>')
print("declared class __name__ default:", repr(declared))
print("instance __qualname__:", repr(qn))

ok = (declared == '' and qn == '')
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.3 + 2.4: chained attribute AND item access each yield a stand-in
whose __name__/__qualname__ is exactly the single accessed component (not the
full dotted path, not empty, no module prefix). Item access is on a mock
_MockObject (unknown.foo[...])."""
import sys
from sphinx.ext.autodoc.mock import mock

ok = True
with mock(['unknown']):
    import unknown
    a = unknown.foo            # attr
    b = a.bar                  # deeper attr
    d = unknown.foo['Item']    # item access on a _MockObject

for obj, expect in [(a, 'foo'), (b, 'bar'), (d, 'Item')]:
    n = getattr(obj, '__name__', '<none>')
    q = getattr(obj, '__qualname__', '<none>')
    print(f"expect {expect!r}: __name__={n!r} __qualname__={q!r}")
    if n != expect or q != expect:
        ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1 (regression): restify of ordinary/non-mock hints is unchanged
from base behavior. Covers builtin, typing container, Optional, ordinary
class. (Sphinx 4.3.0 restify is single-arg.)"""
import sys
from typing import List, Optional
from sphinx.util.typing import restify

checks = [
    ("int", restify(int), ':py:class:`int`'),
    ("List[int]", restify(List[int]),
     ':py:class:`~typing.List`\\ [:py:class:`int`]'),
    ("Optional[int]", restify(Optional[int]),
     ':py:obj:`~typing.Optional`\\ [:py:class:`int`]'),
]

class Foo:
    pass
checks.append(("Foo", restify(Foo), ':py:class:`__main__.Foo`'))

ok = True
for label, got, want in checks:
    print(f"{label}: got={got!r} want={want!r}")
    if got != want:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.3 + Req 5.1: stringify of a mock stand-in is unchanged (module.name
display), and core mock protocols still hold (len 0, empty iter, membership
false, attr access yields stand-in, __display_name__/__module__ intact)."""
import sys
from sphinx.ext.autodoc.mock import mock, _MockObject
from sphinx.util.typing import stringify

ok = True
with mock(['unknown']):
    import unknown
    C = unknown.secret.Class
    s = stringify(C)
    print("stringify:", repr(s))
    if s != 'unknown.secret.Class':
        ok = False
    print("display_name:", repr(C.__display_name__), "module:", repr(C.__module__))
    if C.__display_name__ != 'unknown.secret.Class' or C.__module__ != 'unknown.secret':
        ok = False

m = _MockObject()
print("len:", len(m), "iter:", list(m), "'x' in m:", ('x' in m))
if len(m) != 0 or list(m) != [] or ('x' in m):
    ok = False
if not isinstance(m.anything, _MockObject):
    ok = False
if m.__sphinx_mock__ is not True:
    ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 2 + Req 3: restify of a mock stand-in reached by
multi-level access yields a complete dotted reference (module joined to the
short name), not one truncated at a trailing dot with the final component
missing. HOLDS patched, FAILS at base."""
import sys
from sphinx.ext.autodoc.mock import mock
from sphinx.util.typing import restify

with mock(['unknown']):
    import unknown
    r = restify(unknown.secret.Class)

print("restify:", repr(r))
ok = (r == ':py:class:`unknown.secret.Class`')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance image is Sphinx 4.3.0 (py3.9): restify is single-arg (no 'mode'), the string renderer is 'stringify' (not 'stringify_annotation'), and item access is on _MockObject not _MockModule; probes adapted accordingly.

Probe map (all HOLD on gold-patched tree):
- probe_1 (Req 2/3, POSITIVE CONTROL): restify(unknown.secret.Class) == ':py:class:`unknown.secret.Class`'. HOLDS patched; FAILS at base (base gives ':py:class:`unknown.secret.`' — truncated at trailing dot). Discriminates.
- probe_2 (Req 1.1/2.1/2.2): multi-level stand-in reports __name__=='Class' and __qualname__=='Class'. HOLDS patched; base has no __name__ instance attr and __qualname__==''.
- probe_3 (Req 1.2/2.3): _MockObject class declares __name__=='' default and a bare instance reports __qualname__==''. HOLDS patched; base has no declared __name__ default.
- probe_4 (Req 1.3/2.4): chained attr access (foo, foo.bar) and item access (foo['Item']) each yield stand-in with __name__/__qualname__ == the single accessed component. HOLDS patched; base __qualname__==''.
- probe_5 (Req 4.1 regression): restify of int/List[int]/Optional[int]/ordinary class unchanged. HOLDS on BOTH base and patched (unchanged) — regression guard.
- probe_6 (Req 4.3/5.1 regression): stringify(mock)=='unknown.secret.Class' unchanged, plus mock protocols (len 0, empty iter, membership false, attr yields stand-in, __display_name__/__module__/__sphinx_mock__ intact). HOLDS on both base and patched.

Candidate wrong-fix (weak.diff): adds only '__name__ = \'\'' to the base _MockObject class (the partial fix a weak reading of Req 1.2/2.3 permits) but omits both the __init__ change (self.__qualname__ = self.__name__, which at base is hardcoded '') and the '__name__: name' entry in _make_subclass. Applies cleanly at base_commit. REJECTED by probe_1 (still ':py:class:`unknown.secret.`'), probe_2 (__name__==''), and probe_4 — demonstrating the suite discriminates a partial implementation that would not resolve the hidden tests. Probes 3/5/6 accept it (as expected for a regression/base-default guard).

All 6 probes hold on the patched tree; positive control fails at base and holds patched (prepatch_reproduced=true); >=1 candidate exercised and REJECTED. No requirement mandates behavior the gold patch lacks, and no probe-conforming alternative was found that would pass the suite yet fail resolution. Verdict SOUND.

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
"""Positive control. Req 2 + Req 3: restify of a mock stand-in reached by
multi-level access yields a complete dotted reference (module joined to the
short name), not one truncated at a trailing dot with the final component
missing. HOLDS patched, FAILS at base."""
import sys
from sphinx.ext.autodoc.mock import mock
from sphinx.util.typing import restify

with mock(['unknown']):
    import unknown
    r = restify(unknown.secret.Class)

print("restify:", repr(r))
ok = (r == ':py:class:`unknown.secret.Class`')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance image is Sphinx 4.3.0 (py3.9): restify is single-arg (no 'mode'), the string renderer is 'stringify' (not 'stringify_annotation'), and item access is on _MockObject not _MockModule; probes adapted accordingly.

Probe map (all HOLD on gold-patched tree):
- probe_1 (Req 2/3, POSITIVE CONTROL): restify(unknown.secret.Class) == ':py:class:`unknown.secret.Class`'. HOLDS patched; FAILS at base (base gives ':py:class:`unknown.secret.`' — truncated at trailing dot). Discriminates.
- probe_2 (Req 1.1/2.1/2.2): multi-level stand-in reports __name__=='Class' and __qualname__=='Class'. HOLDS patched; base has no __name__ instance attr and __qualname__==''.
- probe_3 (Req 1.2/2.3): _MockObject class declares __name__=='' default and a bare instance reports __qualname__==''. HOLDS patched; base has no declared __name__ default.
- probe_4 (Req 1.3/2.4): chained attr access (foo, foo.bar) and item access (foo['Item']) each yield stand-in with __name__/__qualname__ == the single accessed component. HOLDS patched; base __qualname__==''.
- probe_5 (Req 4.1 regression): restify of int/List[int]/Optional[int]/ordinary class unchanged. HOLDS on BOTH base and patched (unchanged) — regression guard.
- probe_6 (Req 4.3/5.1 regression): stringify(mock)=='unknown.secret.Class' unchanged, plus mock protocols (len 0, empty iter, membership false, attr yields stand-in, __display_name__/__module__/__sphinx_mock__ intact). HOLDS on both base and patched.

Candidate wrong-fix (weak.diff): adds only '__name__ = \'\'' to the base _MockObject class (the partial fix a weak reading of Req 1.2/2.3 permits) but omits both the __init__ change (self.__qualname__ = self.__name__, which at base is hardcoded '') and the '__name__: name' entry in _make_subclass. Applies cleanly at base_commit. REJECTED by probe_1 (still ':py:class:`unknown.secret.`'), probe_2 (__name__==''), and probe_4 — demonstrating the suite discriminates a partial implementation that would not resolve the hidden tests. Probes 3/5/6 accept it (as expected for a regression/base-default guard).

All 6 probes hold on the patched tree; positive control fails at base and holds patched (prepatch_reproduced=true); >=1 candidate exercised and REJECTED. No requirement mandates behavior the gold patch lacks, and no probe-conforming alternative was found that would pass the suite yet fail resolution. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: adds __name__='' to _MockObject, __name__=name to _make_subclass attrs, and changes __init__ from self.__qualname__='' to self.__qualname__=self.__name__. restify (sphinx/util/typing.py _restify_py37) uses cls.__qualname__ joined to cls.__module__, which is exactly the modeling boundary the requirements pin. Requirements correctly model the changed OBSERVABLE (complete reST reference for mocked bases) rather than a narrow slice, and correctly scope preservation to non-mock rendering + mock stringify. Probed both base and gold-patched trees; behavior matches every criterion.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements name only pre-existing source identifiers (_MockObject, _make_subclass, restify, stringify, __name__, __qualname__, __display_name__, __module__, __sphinx_mock__, __sphinx_decorator_args__, mock.py, util/typing.py) — legitimate localization; the gold edit invents NO new identifiers. Reqs 1-3 translate the gold's behavior (short name stored as __name__, __qualname__=__name__, empty default) into behavioral requirements, which is the intended job, not a leak. No test names/paths (test_restify_mock, test_stringify_mock), no parametrization strings (unknown, secret, unknown.secret.Class), no quoted test/gold code appear. Req 4's enumeration of non-mock annotation kinds (containers, Callable, Union, typevars, aliases, ForwardRef, Literal, PEP 585, broken hints, Annotated) tracks the PASS_TO_PASS family but these are exactly the branches restify/stringify handle in the source — discoverable from the changed functions — and are stated as a scope-preservation constraint, not as test cases or expected assertion values. No reconstruction of hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
