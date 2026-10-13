# P2 adversarial audit — astropy__astropy-7166

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.1 & R1.5 positive control: a property with no docstring inherits the
exact docstring of the overridden base-class property."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    @property
    def bar(self):
        "BAR"
        return 1


class Sub(Base):
    @property
    def bar(self):
        return 42


got = Sub.bar.__doc__
print("Sub.bar.__doc__ =", repr(got))
if got == "BAR":
    sys.exit(0)
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2: docstring for an overriding property is resolved through the MRO,
using the FIRST base class that defines a correspondingly named member."""
import sys
from astropy.utils.misc import InheritDocstrings


class A(metaclass=InheritDocstrings):
    @property
    def bar(self):
        "A-DOC"
        return 1


class B(A):
    @property
    def bar(self):
        "B-DOC"
        return 2


class C(B):
    @property
    def bar(self):
        return 3


# MRO of C is C, B, A -> first base defining bar is B
got = C.bar.__doc__
print("C.__mro__ =", [k.__name__ for k in C.__mro__])
print("C.bar.__doc__ =", repr(got))
if got == "B-DOC":
    sys.exit(0)
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.3: a property that already has its own docstring is left unchanged."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    @property
    def bar(self):
        "BASE-DOC"
        return 1


class Sub(Base):
    @property
    def bar(self):
        "OWN-DOC"
        return 42


got = Sub.bar.__doc__
print("Sub.bar.__doc__ =", repr(got))
if got == "OWN-DOC":
    sys.exit(0)
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.4: if no base class defines a correspondingly named member, the
property's docstring is left absent (None)."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    pass


class Sub(Base):
    @property
    def brandnew(self):
        return 42


got = Sub.brandnew.__doc__
print("Sub.brandnew.__doc__ =", repr(got))
if got is None:
    sys.exit(0)
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R2.1 & R2.2: method/special-method docstring inheritance still works
(the __call__ regression case)."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    def __call__(self, *args):
        "FOO"
        pass

    def method(self):
        "METH"
        pass


class Sub(Base):
    def __call__(self, *args):
        pass

    def method(self):
        pass


print("Sub.__call__.__doc__ =", repr(Sub.__call__.__doc__))
print("Sub.method.__doc__ =", repr(Sub.method.__doc__))
if Sub.__call__.__doc__ == "FOO" and Sub.method.__doc__ == "METH":
    sys.exit(0)
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.1 & R3.2: private members (single leading underscore) are NOT modified;
public members (incl. dunder) ARE. Here a private property must stay None even
though a base defines a docstring for it."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    @property
    def _secret(self):
        "SECRET-DOC"
        return 1


class Sub(Base):
    @property
    def _secret(self):
        return 42


got = Sub._secret.__doc__
print("Sub._secret.__doc__ =", repr(got))
# non-public -> must NOT be modified -> stays None
if got is None:
    sys.exit(0)
sys.exit(1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R2.3: a method that already has its own docstring is left unchanged."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    def method(self):
        "BASE-METH"
        pass


class Sub(Base):
    def method(self):
        "OWN-METH"
        pass


got = Sub.method.__doc__
print("Sub.method.__doc__ =", repr(got))
if got == "OWN-METH":
    sys.exit(0)
sys.exit(1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
"""R3.3: a member that is neither a function/method nor a property/data
descriptor SHALL NOT have its docstring modified. Use a non-data-descriptor
callable-free value: a plain class attribute set to an object whose __doc__ we
can observe. We use a custom class instance (not a data descriptor) that carries
its own __doc__ = None; the metaclass must leave it None even though the base
defines a same-named property with a docstring."""
import sys
from astropy.utils.misc import InheritDocstrings


class Marker:
    __doc__ = None  # instance-level doc slot, observable


class Base(metaclass=InheritDocstrings):
    @property
    def thing(self):
        "THING-DOC"
        return 1


class Sub(Base):
    thing = Marker()  # not a function, not a data descriptor


import inspect
print("isdatadescriptor(Marker()) =", inspect.isdatadescriptor(Sub.__dict__['thing']))
print("isfunction =", inspect.isfunction(Sub.__dict__['thing']))
got = Sub.__dict__['thing'].__doc__
print("Sub.thing.__doc__ =", repr(got))
# Marker instance is neither function nor data descriptor -> must not be touched
if got is None:
    sys.exit(0)
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 & R1.5 positive control: a property with no docstring inherits the
exact docstring of the overridden base-class property."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    @property
    def bar(self):
        "BAR"
        return 1


class Sub(Base):
    @property
    def bar(self):
        return 42


got = Sub.bar.__doc__
print("Sub.bar.__doc__ =", repr(got))
if got == "BAR":
    sys.exit(0)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

InheritDocstrings metaclass: gold patch widens eligibility from inspect.isfunction(val) to (inspect.isfunction(val) or inspect.isdatadescriptor(val)) so overriding properties inherit docstrings.

8 probes, all HOLD on gold-patched tree:
- probe_1 (R1.1/R1.5, POSITIVE CONTROL): property w/o docstring inherits exact base docstring 'BAR'. HOLDS patched, VIOLATED at base (Sub.bar.__doc__=None). Discriminates.
- probe_2 (R1.2): 3-level MRO C(B(A)); C.bar inherits from FIRST base defining it (B -> 'B-DOC'). HOLDS patched, VIOLATED at base.
- probe_3 (R1.3): property with own docstring left unchanged ('OWN-DOC').
- probe_4 (R1.4): no base defines member -> stays None.
- probe_5 (R2.1/R2.2): method + __call__ docstring inheritance still works ('FOO','METH'). HOLDS at base too (regression leg).
- probe_6 (R3.1/R3.2): private property _secret NOT modified (stays None).
- probe_7 (R2.3): method with own docstring unchanged ('OWN-METH').
- probe_8 (R3.3): non-function/non-datadescriptor member (plain instance) not modified.

Candidate patch 'data_descriptor_only' (weak.diff): replaces isfunction with isdatadescriptor only (drops functions). A weak reading of R1 (only properties). REJECTED by probe_5: Sub.__call__.__doc__=None, Sub.method.__doc__=None -> breaks R2 method inheritance, and would fail hidden test (test_inherit_docstrings asserts Subclass.__call__.__doc__=='FOO'). This proves the suite discriminates wrong implementations.

Verdict SOUND: 8 distinct probes covering all criteria hold on patched tree; positive control discriminates base vs patched; requirements-conforming-only-for-R1 weak candidate is rejected by the R2 regression probe.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 & R1.5 positive control: a property with no docstring inherits the
exact docstring of the overridden base-class property."""
import sys
from astropy.utils.misc import InheritDocstrings


class Base(metaclass=InheritDocstrings):
    @property
    def bar(self):
        "BAR"
        return 1


class Sub(Base):
    @property
    def bar(self):
        return 42


got = Sub.bar.__doc__
print("Sub.bar.__doc__ =", repr(got))
if got == "BAR":
    sys.exit(0)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

InheritDocstrings metaclass: gold patch widens eligibility from inspect.isfunction(val) to (inspect.isfunction(val) or inspect.isdatadescriptor(val)) so overriding properties inherit docstrings.

8 probes, all HOLD on gold-patched tree:
- probe_1 (R1.1/R1.5, POSITIVE CONTROL): property w/o docstring inherits exact base docstring 'BAR'. HOLDS patched, VIOLATED at base (Sub.bar.__doc__=None). Discriminates.
- probe_2 (R1.2): 3-level MRO C(B(A)); C.bar inherits from FIRST base defining it (B -> 'B-DOC'). HOLDS patched, VIOLATED at base.
- probe_3 (R1.3): property with own docstring left unchanged ('OWN-DOC').
- probe_4 (R1.4): no base defines member -> stays None.
- probe_5 (R2.1/R2.2): method + __call__ docstring inheritance still works ('FOO','METH'). HOLDS at base too (regression leg).
- probe_6 (R3.1/R3.2): private property _secret NOT modified (stays None).
- probe_7 (R2.3): method with own docstring unchanged ('OWN-METH').
- probe_8 (R3.3): non-function/non-datadescriptor member (plain instance) not modified.

Candidate patch 'data_descriptor_only' (weak.diff): replaces isfunction with isdatadescriptor only (drops functions). A weak reading of R1 (only properties). REJECTED by probe_5: Sub.__call__.__doc__=None, Sub.method.__doc__=None -> breaks R2 method inheritance, and would fail hidden test (test_inherit_docstrings asserts Subclass.__call__.__doc__=='FOO'). This proves the suite discriminates wrong implementations.

Verdict SOUND: 8 distinct probes covering all criteria hold on patched tree; positive control discriminates base vs patched; requirements-conforming-only-for-R1 weak candidate is rejected by the R2 regression probe.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base-commit probe confirms the pre-patch bug (Sub.bar.__doc__ == None) and patched fixes it. Requirements pin the changed observable boundary (property/data-descriptor inheritance) rather than a narrow slice or invented behavior. R3.1's dunder rule ('longer than four characters') matches is_public_member. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior, not the hidden tests. The public problem_statement already says the InheritDocstrings metaclass fails for properties because it uses inspect.isfunction. The doc's mention of 'properties (and, more generally, data descriptors)' maps to the gold fix's `inspect.isdatadescriptor` but 'data descriptor' is the standard Python concept defining what a property IS — it is a behavioral generalization, not quoted gold code or a fix-invented identifier. Module/function localization (astropy/utils/misc.py, InheritDocstrings) is explicitly legitimate and already public. Req 3.1's public/dunder rule reflects the pre-existing is_public_member source (unchanged patch context), not the gold edit or hidden test. The __call__ example (Req 2.2) is a canonical special-method illustration; though the hidden test exercises __call__, the doc does not reproduce the test's specifics (Base/Subclass shape, 'FOO'/'BAR' docstrings, `return 42`, the assert, or the test name/path test_misc.py::test_inherit_docstrings). No test names/paths/ids, no quoted test or gold code, no parametrization enumeration. This is legitimate behavior-to-requirements translation.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
