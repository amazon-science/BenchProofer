# P2 adversarial audit — sphinx-doc__sphinx-7910

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
"""POSITIVE CONTROL / Req1 AC1,AC3,AC4: a decorated __init__ that preserves
its docstring, owned by its class, with the init toggle ON, MUST be INCLUDED
(_skip_member returns False = do not skip). At base, ownership resolves from
the decorated object's own __globals__ (which does NOT contain the owning
class), so ownership fails and the decision is deferred (None) -> NOT included.
Holds iff _skip_member(...) == False (explicit inclusion)."""
import sys, types, functools
from sphinx.ext.napoleon import _skip_member


class Cfg:
    napoleon_include_init_with_doc = True
    napoleon_include_special_with_doc = False
    napoleon_include_private_with_doc = False


class App:
    config = Cfg()


# Build a decorator living in a SEPARATE module so the wrapper's __globals__
# does not contain the owning class -- exactly the real functools.wraps bug.
decmod = types.ModuleType("decmod_probe")
decmod_src = (
    "import functools\n"
    "def wrap(f):\n"
    "    @functools.wraps(f)\n"
    "    def inner(*a, **k):\n"
    "        return f(*a, **k)\n"
    "    return inner\n"
)
exec(decmod_src, decmod.__dict__)
sys.modules["decmod_probe"] = decmod


class Owner:
    @decmod.wrap
    def __init__(self):
        """A documented decorated __init__."""
        pass


obj = Owner.__init__
print("obj.__qualname__ =", getattr(obj, "__qualname__", None))
print("owner in decorated globals?", "Owner" in getattr(obj, "__globals__", {}))
res = _skip_member(App(), "class", "__init__", obj, True, object())
print("_skip_member returned:", res)
# Behavior mandated: explicit inclusion (False).
sys.exit(0 if res is False else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2 AC1: NON-decorated member ownership resolves identically as before.
An undocumented... no -- a documented undecorated private member owned by its
class, with the private toggle ON, MUST be INCLUDED, both patched and base
(this branch is unchanged). Holds iff _skip_member == False."""
import sys
from sphinx.ext.napoleon import _skip_member


class Cfg:
    napoleon_include_init_with_doc = False
    napoleon_include_special_with_doc = False
    napoleon_include_private_with_doc = True


class App:
    config = Cfg()


class Owner:
    def _helper(self):
        """documented private undecorated method."""
        pass


obj = Owner._helper
print("qualname:", obj.__qualname__, "globals has Owner:",
      "Owner" in obj.__globals__)
res = _skip_member(App(), "class", "_helper", obj, True, object())
print("_skip_member returned:", res)
sys.exit(0 if res is False else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2 AC2 & AC3 & AC8: deferral cases the handler must NOT force-include.
(a) __weakref__ -> defer (None) even with a docstring.
(b) member with no docstring -> defer (None) regardless of toggles.
And it must NEVER return True (only False or None). Holds iff both cases
return None. Unchanged across trees; guards against a fix that over-includes."""
import sys
from sphinx.ext.napoleon import _skip_member


class Cfg:
    napoleon_include_init_with_doc = True
    napoleon_include_special_with_doc = True
    napoleon_include_private_with_doc = True


class App:
    config = Cfg()


class Owner:
    def _nodoc(self):
        pass  # no docstring


# (a) __weakref__ with a docstring. A normal class exposes a __weakref__
# getset_descriptor (which carries a __doc__).
class WithWeakref:
    pass


wk = WithWeakref.__weakref__
print("wk has doc?", bool(getattr(wk, "__doc__", None)))
res_wk = _skip_member(App(), "class", "__weakref__", wk, True, object())
print("__weakref__ ->", res_wk)

# (b) no docstring member with all toggles on -> still defer.
obj = Owner._nodoc
obj.__doc__ = None
res_nodoc = _skip_member(App(), "class", "_nodoc", obj, True, object())
print("no-doc private ->", res_nodoc)

ok = (res_wk is None) and (res_nodoc is None)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2 AC4 & AC6: (AC4) a class member NOT owned by its resolved class ->
defer (None). (AC6) toggle OFF -> defer even for a documented owned member.
Holds iff: unowned special member returns None AND owned special member with
special toggle OFF returns None. Guards against a too-weak fix that includes
regardless of ownership or toggle state."""
import sys
from sphinx.ext.napoleon import _skip_member


class OwnerA:
    def __special__(self):
        """doc"""
        pass


# AC4: fabricate a member whose qualname points at a class that does NOT
# declare it. Use a function whose __qualname__ says 'Ghost.__special__' but
# no Ghost class exists in its globals -> ownership fails -> defer.
def orphan(self):
    """doc"""
    pass


orphan.__qualname__ = "Ghost.__special__"

# ensure toggle ON so the ONLY reason to defer is lack of ownership
class CfgOn:
    napoleon_include_init_with_doc = True
    napoleon_include_special_with_doc = True
    napoleon_include_private_with_doc = True


class AppOn:
    config = CfgOn()


res_unowned = _skip_member(AppOn(), "class", "__special__", orphan, True, object())
print("unowned special (toggle on) ->", res_unowned)

# AC6: owned special member but special toggle OFF -> defer.
class CfgOff:
    napoleon_include_init_with_doc = True
    napoleon_include_special_with_doc = False
    napoleon_include_private_with_doc = True


class AppOff:
    config = CfgOff()


res_toggleoff = _skip_member(AppOff(), "class", "__special__",
                             OwnerA.__special__, True, object())
print("owned special (toggle off) ->", res_toggleoff)

ok = (res_unowned is None) and (res_toggleoff is None)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2 AC5 & AC7: MODULE members are decided by category+toggle WITHOUT any
owning-class resolution. A documented module-level private function with the
private toggle ON MUST be INCLUDED (False), and its qualname has no dot so no
ownership branch runs. Holds iff res == False. Unchanged across trees."""
import sys
from sphinx.ext.napoleon import _skip_member


class Cfg:
    napoleon_include_init_with_doc = False
    napoleon_include_special_with_doc = False
    napoleon_include_private_with_doc = True


class App:
    config = Cfg()


def _module_priv():
    """documented private module-level function."""
    pass


print("qualname:", _module_priv.__qualname__)
res = _skip_member(App(), "module", "_module_priv", _module_priv, True, object())
print("module private ->", res)
sys.exit(0 if res is False else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2 AC9: namedtuple-derived classes follow the same ownership+category
rules and keep their inclusion/skip decisions. A documented private method
defined on a namedtuple subclass, owned by that class, private toggle ON, MUST
be INCLUDED (False). Also a documented decorated __init__ on the SAME
namedtuple-derived class must be included on the patched tree (AC9 + Req1).
Holds iff the private member is included (unchanged behavior). The decorated
init leg is reported but not gated here (covered by probe_1) so this probe
stays a pure regression check."""
import sys, types, functools
from collections import namedtuple
from sphinx.ext.napoleon import _skip_member


class Cfg:
    napoleon_include_init_with_doc = True
    napoleon_include_special_with_doc = False
    napoleon_include_private_with_doc = True


class App:
    config = Cfg()


Base = namedtuple("Base", ["x", "y"])


class Point(Base):
    def _extra(self):
        """documented private method on a namedtuple subclass."""
        return self.x


obj = Point._extra
print("qualname:", obj.__qualname__, "globals has Point:",
      "Point" in obj.__globals__)
res = _skip_member(App(), "class", "_extra", obj, True, object())
print("namedtuple-subclass private ->", res)
sys.exit(0 if res is False else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL / Req1 AC1,AC3,AC4: a decorated __init__ that preserves
its docstring, owned by its class, with the init toggle ON, MUST be INCLUDED
(_skip_member returns False = do not skip). At base, ownership resolves from
the decorated object's own __globals__ (which does NOT contain the owning
class), so ownership fails and the decision is deferred (None) -> NOT included.
Holds iff _skip_member(...) == False (explicit inclusion)."""
import sys, types, functools
from sphinx.ext.napoleon import _skip_member


class Cfg:
    napoleon_include_init_with_doc = True
    napoleon_include_special_with_doc = False
    napoleon_include_private_with_doc = False


class App:
    config = Cfg()


# Build a decorator living in a SEPARATE module so the wrapper's __globals__
# does not contain the owning class -- exactly the real functools.wraps bug.
decmod = types.ModuleType("decmod_probe")
decmod_src = (
    "import functools\n"
    "def wrap(f):\n"
    "    @functools.wraps(f)\n"
    "    def inner(*a, **k):\n"
    "        return f(*a, **k)\n"
    "    return inner\n"
)
exec(decmod_src, decmod.__dict__)
sys.modules["decmod_probe"] = decmod


class Owner:
    @decmod.wrap
    def __init__(self):
        """A documented decorated __init__."""
        pass


obj = Owner.__init__
print("obj.__qualname__ =", getattr(obj, "__qualname__", None))
print("owner in decorated globals?", "Owner" in getattr(obj, "__globals__", {}))
res = _skip_member(App(), "class", "__init__", obj, True, object())
print("_skip_member returned:", res)
# Behavior mandated: explicit inclusion (False).
sys.exit(0 if res is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7910 (Napoleon _skip_member). Gold patch: obj.__globals__[cls_path] -> inspect.unwrap(obj).__globals__[cls_path], resolving the owning class from the UNDERLYING (undecorated) object.

### PROBES (all run in the official image; PATCHED results):
- probe_1 (Req1 AC1/AC3/AC4, POSITIVE CONTROL): decorated __init__ (functools.wraps, decorator in a separate module so the wrapper's __globals__ lacks the owning class), docstring preserved, init toggle ON -> must be INCLUDED. PATCHED: _skip_member=False (HOLDS). BASE: _skip_member=None (VIOLATED) => discriminates. prepatch_reproduced=true.
- probe_2 (Req2 AC1): undecorated documented private member, owned, private toggle ON -> INCLUDED. PATCHED: False (HOLDS).
- probe_3 (Req2 AC2/AC3/AC8): __weakref__ with a docstring -> defer (None); no-docstring member with all toggles ON -> defer (None). PATCHED: both None (HOLDS).
- probe_4 (Req2 AC4/AC6): unowned member (qualname points at a class not present, toggle ON) -> defer; owned special member with special toggle OFF -> defer. PATCHED: both None (HOLDS).
- probe_5 (Req2 AC5/AC7): module-level documented private, private toggle ON, no ownership resolution -> INCLUDED. PATCHED: False (HOLDS).
- probe_6 (Req2 AC9): namedtuple-derived subclass documented private method, owned, private toggle ON -> INCLUDED. PATCHED: False (HOLDS).

All 6 hold patched; positive control fails at base and holds patched.

CANDIDATE WRONG-FIX (weak.diff): replaces obj.__globals__ with obj.__wrapped__.__globals__ (a naive reading that unwraps unconditionally instead of via inspect.unwrap). REJECTED by the suite: probe_2 VIOLATED (undecorated Owner._helper has no __wrapped__ -> AttributeError -> ownership fails -> deferred instead of included) and probe_6 VIOLATED (same for the namedtuple subclass method). This is the Req2-AC1 regression that inspect.unwrap (which returns the object itself when there is no wrapper chain) avoids. Demonstrates the probe suite discriminates plausibly-wrong implementations.

VERDICT SOUND: >=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and a wrong-fix candidate is rejected by two probes.

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
"""POSITIVE CONTROL / Req1 AC1,AC3,AC4: a decorated __init__ that preserves
its docstring, owned by its class, with the init toggle ON, MUST be INCLUDED
(_skip_member returns False = do not skip). At base, ownership resolves from
the decorated object's own __globals__ (which does NOT contain the owning
class), so ownership fails and the decision is deferred (None) -> NOT included.
Holds iff _skip_member(...) == False (explicit inclusion)."""
import sys, types, functools
from sphinx.ext.napoleon import _skip_member


class Cfg:
    napoleon_include_init_with_doc = True
    napoleon_include_special_with_doc = False
    napoleon_include_private_with_doc = False


class App:
    config = Cfg()


# Build a decorator living in a SEPARATE module so the wrapper's __globals__
# does not contain the owning class -- exactly the real functools.wraps bug.
decmod = types.ModuleType("decmod_probe")
decmod_src = (
    "import functools\n"
    "def wrap(f):\n"
    "    @functools.wraps(f)\n"
    "    def inner(*a, **k):\n"
    "        return f(*a, **k)\n"
    "    return inner\n"
)
exec(decmod_src, decmod.__dict__)
sys.modules["decmod_probe"] = decmod


class Owner:
    @decmod.wrap
    def __init__(self):
        """A documented decorated __init__."""
        pass


obj = Owner.__init__
print("obj.__qualname__ =", getattr(obj, "__qualname__", None))
print("owner in decorated globals?", "Owner" in getattr(obj, "__globals__", {}))
res = _skip_member(App(), "class", "__init__", obj, True, object())
print("_skip_member returned:", res)
# Behavior mandated: explicit inclusion (False).
sys.exit(0 if res is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7910 (Napoleon _skip_member). Gold patch: obj.__globals__[cls_path] -> inspect.unwrap(obj).__globals__[cls_path], resolving the owning class from the UNDERLYING (undecorated) object.

### PROBES (all run in the official image; PATCHED results):
- probe_1 (Req1 AC1/AC3/AC4, POSITIVE CONTROL): decorated __init__ (functools.wraps, decorator in a separate module so the wrapper's __globals__ lacks the owning class), docstring preserved, init toggle ON -> must be INCLUDED. PATCHED: _skip_member=False (HOLDS). BASE: _skip_member=None (VIOLATED) => discriminates. prepatch_reproduced=true.
- probe_2 (Req2 AC1): undecorated documented private member, owned, private toggle ON -> INCLUDED. PATCHED: False (HOLDS).
- probe_3 (Req2 AC2/AC3/AC8): __weakref__ with a docstring -> defer (None); no-docstring member with all toggles ON -> defer (None). PATCHED: both None (HOLDS).
- probe_4 (Req2 AC4/AC6): unowned member (qualname points at a class not present, toggle ON) -> defer; owned special member with special toggle OFF -> defer. PATCHED: both None (HOLDS).
- probe_5 (Req2 AC5/AC7): module-level documented private, private toggle ON, no ownership resolution -> INCLUDED. PATCHED: False (HOLDS).
- probe_6 (Req2 AC9): namedtuple-derived subclass documented private method, owned, private toggle ON -> INCLUDED. PATCHED: False (HOLDS).

All 6 hold patched; positive control fails at base and holds patched.

CANDIDATE WRONG-FIX (weak.diff): replaces obj.__globals__ with obj.__wrapped__.__globals__ (a naive reading that unwraps unconditionally instead of via inspect.unwrap). REJECTED by the suite: probe_2 VIOLATED (undecorated Owner._helper has no __wrapped__ -> AttributeError -> ownership fails -> deferred instead of included) and probe_6 VIOLATED (same for the namedtuple subclass method). This is the Req2-AC1 regression that inspect.unwrap (which returns the object itself when there is no wrapper chain) avoids. Demonstrates the probe suite discriminates plausibly-wrong implementations.

VERDICT SOUND: >=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and a wrong-fix candidate is rejected by two probes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirement<->code verification (all run in the instance image):
- 1.1 unwrap for owning-class resolution: code uses `inspect.unwrap(obj).__globals__[cls_path]`; confirmed unwrapped globals contain SampleClass while wrapper globals do not.
- 1.2 ownership test: `cls and hasattr(cls,name) and name in cls.__dict__` — matches.
- 1.3/1.4/2.7 include when owned+doc+toggle: returns False; probed True for decorated __special__ case; __init__ path identical (is_init/inc_init).
- 1.5 boundary: dotted cls_path -> module attribute traversal (functools.reduce(getattr)); dotless -> unwrap().__globals__. The change touches ONLY the dotless branch, exactly as required; nested names explicitly out of scope and code leaves them unchanged.
- 1.6 error handling: `except Exception: cls_is_owner=False` — matches 'treat as not owned, do not propagate'.
- 2.1 undecorated identity: inspect.unwrap returns obj itself when not wrapped, so decision is identical to pre-change; verified base==patched for non-decorated members.
- 2.2 __weakref__ deferral: `name != '__weakref__'` guard; probed None.
- 2.3 no-doc deferral: `has_doc` guard.
- 2.4 not-owned deferral: cls_is_owner False -> None.
- 2.5 module member: condition `what=='module' or cls_is_owner` bypasses owning-class resolution for modules; probed 'module' returns False without resolution.
- 2.6 toggle-off deferral: probed None with napoleon_include_special_with_doc=False.
- 2.8 never forces skip: only return values are False or None.
- 2.9 namedtuple unchanged: test_namedtuple is PASS_TO_PASS; patch does not alter that path.
The requirements pin the CHANGED observable behavior biconditionally (decorated-member inclusion via unwrap) and preserve all other decisions; boundary is correct, not a narrow slice or invented behavior.

Counterexample / evidence:

```
The FAIL_TO_PASS discriminator confirms the modeling boundary is correct rather than a narrow slice: for a `class` member decorated by a wrapper whose __globals__ lacks the owning class (functools.wraps does NOT copy __globals__), with a docstring and napoleon_include_special_with_doc=True, `_skip_member('class','__decorated_func__',obj,True,...)` returns None at base_commit (member wrongly dropped) but False (include) on the gold-patched tree. Probed both trees: base=None, patched=False.
```

- 1.1 unwrap for owning-class resolution: code uses `inspect.unwrap(obj).__globals__[cls_path]`; confirmed unwrapped globals contain SampleClass while wrapper globals do not.
- 1.2 ownership test: `cls and hasattr(cls,name) and name in cls.__dict__` — matches.
- 1.3/1.4/2.7 include when owned+doc+toggle: returns False; probed True for decorated __special__ case; __init__ path identical (is_init/inc_init).
- 1.5 boundary: dotted cls_path -> module attribute traversal (functools.reduce(getattr)); dotless -> unwrap().__globals__. The change touches ONLY the dotless branch, exactly as required; nested names explicitly out of scope and code leaves them unchanged.
- 1.6 error handling: `except Exception: cls_is_owner=False` — matches 'treat as not owned, do not propagate'.
- 2.1 undecorated identity: inspect.unwrap returns obj itself when not wrapped, so decision is identical to pre-change; verified base==patched for non-decorated members.
- 2.2 __weakref__ deferral: `name != '__weakref__'` guard; probed None.
- 2.3 no-doc deferral: `has_doc` guard.
- 2.4 not-owned deferral: cls_is_owner False -> None.
- 2.5 module member: condition `what=='module' or cls_is_owner` bypasses owning-class resolution for modules; probed 'module' returns False without resolution.
- 2.6 toggle-off deferral: probed None with napoleon_include_special_with_doc=False.
- 2.8 never forces skip: only return values are False or None.
- 2.9 namedtuple unchanged: test_namedtuple is PASS_TO_PASS; patch does not alter that path.
The requirements pin the CHANGED observable behavior biconditionally (decorated-member inclusion via unwrap) and preserve all other decisions; boundary is correct, not a narrow slice or invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change (_skip_member in sphinx/ext/napoleon/__init__.py; unwrap helper in sphinx/util/inspect.py) and translate the FAIL_TO_PASS behavior into requirements — all derivable from the PUBLIC problem_statement, which itself names functools.wraps, napoleon_include_init_with_doc, obj.__globals__[cls_path], and cls_is_owner. The gold edit (inspect.unwrap(obj).__globals__[cls_path]) is described behaviorally as 'following the decorator link chain to the end,' not quoted. No test name/path/id, no quoted test code, and none of the test-only identifiers (simple_decorator helper, __decorated_func__ sample member) are leaked. Borderline but acceptable: (1) Req 2.2's __weakref__ appears verbatim in the function source being modified, so it describes existing behavior, not a hidden test; (2) Req 2.9's 'namedtuple-derived class' corresponds to the PASS_TO_PASS test_namedtuple and is not in the problem_statement, a mild over-specification, but it is stated behaviorally (preserve prior decisions), transmits no test name/code/id, and namedtuple is a generic construct — it does not reconstruct the hidden test. The Req 2 enumeration of module/class/exception × private/special/init × doc/undoc mirrors the SkipMemberTest matrix but equally describes the actual branch logic of _skip_member (verified against source), which is legitimate behavioral description.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
