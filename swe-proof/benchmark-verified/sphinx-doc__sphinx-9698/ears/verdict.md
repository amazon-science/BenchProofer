# P2 adversarial audit — sphinx-doc__sphinx-9698

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.1/1.2/1.3 (POSITIVE CONTROL): property-flagged py:method index label omits ()
import sphinx.util.nodes  # force full init to avoid circular import
import types, sys
from sphinx.domains.python import PyMethod
class Fake:  # plain object; PyMethod.env is a read-only property, so don't instantiate it
    pass
def fake(options, add_module_names=False):
    f = Fake(); f.options = options
    f.env = types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=add_module_names))
    return f
label = PyMethod.get_index_text(fake({'property': True}), 'mod', ('Class.meth5', 'Class'))
print("property label:", repr(label))
ok_form = label == 'meth5 (Class property)'
ok_paren = ('meth5 (' in label) and ('()' not in label)   # Req1.2
ok_qual = '(Class property)' in label                       # Req1.3
print("ok_form", ok_form, "ok_paren", ok_paren, "ok_qual", ok_qual)
sys.exit(0 if (ok_form and ok_paren and ok_qual) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req2.1: classmethod keeps ()
import sphinx.util.nodes
import types, sys
from sphinx.domains.python import PyMethod
class Fake: pass
def fake(o):
    f=Fake(); f.options=o
    f.env=types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=False)); return f
label = PyMethod.get_index_text(fake({'classmethod': True}), 'mod', ('Class.meth', 'Class'))
print("classmethod label:", repr(label))
sys.exit(0 if label == 'meth() (Class class method)' else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.2/2.3: staticmethod and plain method keep ()
import sphinx.util.nodes
import types, sys
from sphinx.domains.python import PyMethod
class Fake: pass
def fake(o):
    f=Fake(); f.options=o
    f.env=types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=False)); return f
lstatic = PyMethod.get_index_text(fake({'staticmethod': True}), 'mod', ('Class.meth', 'Class'))
lplain  = PyMethod.get_index_text(fake({}), 'mod', ('Class.meth', 'Class'))
print("static:", repr(lstatic), "plain:", repr(lplain))
ok = lstatic == 'meth() (Class static method)' and lplain == 'meth() (Class method)'
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2.4: classmethod+property -> class-method form (with ())
import sphinx.util.nodes
import types, sys
from sphinx.domains.python import PyMethod
class Fake: pass
def fake(o):
    f=Fake(); f.options=o
    f.env=types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=False)); return f
label = PyMethod.get_index_text(fake({'classmethod': True, 'property': True}), 'mod', ('Class.meth', 'Class'))
print("cls+prop label:", repr(label))
sys.exit(0 if label == 'meth() (Class class method)' else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2.5: no-dot fallback keeps () regardless of property option
import sphinx.util.nodes
import types, sys
from sphinx.domains.python import PyMethod
class Fake: pass
def fake(o):
    f=Fake(); f.options=o
    f.env=types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=False)); return f
with_mod = PyMethod.get_index_text(fake({'property': True}), 'mod', ('func', 'func'))
no_mod   = PyMethod.get_index_text(fake({'property': True}), '', ('func', 'func'))
print("with_mod:", repr(with_mod), "no_mod:", repr(no_mod))
ok = with_mod == 'func() (in module mod)' and no_mod == 'func()'
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req4.1/4.2: py:attribute and py:property labels unchanged (no ())
import sphinx.util.nodes
import types, sys
from sphinx.domains.python import PyProperty, PyAttribute
class Fake: pass
def fake(o):
    f=Fake(); f.options=o
    f.env=types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=False)); return f
lprop = PyProperty.get_index_text(fake({}), 'mod', ('Class.prop', 'Class'))
lattr = PyAttribute.get_index_text(fake({}), 'mod', ('Class.attr', 'Class'))
print("py:property:", repr(lprop), "py:attribute:", repr(lattr))
ok = lprop == 'prop (Class property)' and lattr == 'attr (Class attribute)'
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.1/1.2/1.3 (POSITIVE CONTROL): property-flagged py:method index label omits ()
import sphinx.util.nodes  # force full init to avoid circular import
import types, sys
from sphinx.domains.python import PyMethod
class Fake:  # plain object; PyMethod.env is a read-only property, so don't instantiate it
    pass
def fake(options, add_module_names=False):
    f = Fake(); f.options = options
    f.env = types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=add_module_names))
    return f
label = PyMethod.get_index_text(fake({'property': True}), 'mod', ('Class.meth5', 'Class'))
print("property label:", repr(label))
ok_form = label == 'meth5 (Class property)'
ok_paren = ('meth5 (' in label) and ('()' not in label)   # Req1.2
ok_qual = '(Class property)' in label                       # Req1.3
print("ok_form", ok_form, "ok_paren", ok_paren, "ok_qual", ok_qual)
sys.exit(0 if (ok_form and ok_paren and ok_qual) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9698. Gold patch is a one-line string edit in PyMethod.get_index_text: the property branch changes '%s() (%s property)' -> '%s (%s property)' (drop trailing () on property-flagged py:method index label).

Probe harness note: importing sphinx.domains.python directly in this image hits a circular-import AttributeError (addnodes.versionmodified); importing sphinx.util.nodes first fully initializes the module and avoids it. Also PyMethod.env is a read-only property, so probes construct a plain stub object (not an instance) and call get_index_text as an unbound function with a stub carrying .options and .env.config.add_module_names.

Probes (all HOLD on patched tree):
- probe_1 (POSITIVE CONTROL) Req1.1/1.2/1.3: property-flagged method label == 'meth5 (Class property)', member immediately followed by ' (', no '()' after member, qualifier '(Class property)' retained. PATCHED: HOLDS ('meth5 (Class property)'); BASE: FAILS ('meth5() (Class property)') -> discriminates.
- probe_2 Req2.1: classmethod keeps () -> 'meth() (Class class method)'. HOLDS.
- probe_3 Req2.2/2.3: staticmethod 'meth() (Class static method)' and plain 'meth() (Class method)' keep (). HOLDS.
- probe_4 Req2.4: classmethod+property together select class-method form with () -> 'meth() (Class class method)'. HOLDS.
- probe_5 Req2.5: no-dot ValueError fallback keeps () regardless of property option -> 'func() (in module mod)' and 'func()'. HOLDS.
- probe_6 Req4.1/4.2: py:attribute -> 'attr (Class attribute)' and py:property -> 'prop (Class property)' unchanged (no ()). HOLDS.

Candidate wrong patches (floor: >=1 exercised, >=1 rejected — both REJECTED):
- weak_noop: adds only a comment, leaves property branch with (). REJECTED by probe_1 (VIOLATED: 'meth5() (Class property)'); probes 2-6 hold. Demonstrates suite catches the do-nothing/partial fix.
- weak_stripall: over-broad — strips () from ALL four method-kind branches (classmethod/property/static/plain). REJECTED by probe_2, probe_3, probe_4 (Req2 regression guards fire on classmethod/static/plain losing ()); probe_1/5/6 hold. Demonstrates suite catches the too-aggressive fix.

No requirement-conforming alternative patch survived the suite: the only single-branch edit that passes all 6 probes is exactly the gold edit (property branch only), so no TOO-WEAK finding. Requirements are faithful and discriminating. (Note: meta.json records G-PANEL-3=fail = solution leakage of the meth5/Class fixture identifiers into requirements prose; that is a leakage concern, orthogonal to G-EQ spec fidelity, which is SOUND.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req1.1/1.2/1.3 (POSITIVE CONTROL): property-flagged py:method index label omits ()
import sphinx.util.nodes  # force full init to avoid circular import
import types, sys
from sphinx.domains.python import PyMethod
class Fake:  # plain object; PyMethod.env is a read-only property, so don't instantiate it
    pass
def fake(options, add_module_names=False):
    f = Fake(); f.options = options
    f.env = types.SimpleNamespace(config=types.SimpleNamespace(add_module_names=add_module_names))
    return f
label = PyMethod.get_index_text(fake({'property': True}), 'mod', ('Class.meth5', 'Class'))
print("property label:", repr(label))
ok_form = label == 'meth5 (Class property)'
ok_paren = ('meth5 (' in label) and ('()' not in label)   # Req1.2
ok_qual = '(Class property)' in label                       # Req1.3
print("ok_form", ok_form, "ok_paren", ok_paren, "ok_qual", ok_qual)
sys.exit(0 if (ok_form and ok_paren and ok_qual) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9698. Gold patch is a one-line string edit in PyMethod.get_index_text: the property branch changes '%s() (%s property)' -> '%s (%s property)' (drop trailing () on property-flagged py:method index label).

Probe harness note: importing sphinx.domains.python directly in this image hits a circular-import AttributeError (addnodes.versionmodified); importing sphinx.util.nodes first fully initializes the module and avoids it. Also PyMethod.env is a read-only property, so probes construct a plain stub object (not an instance) and call get_index_text as an unbound function with a stub carrying .options and .env.config.add_module_names.

Probes (all HOLD on patched tree):
- probe_1 (POSITIVE CONTROL) Req1.1/1.2/1.3: property-flagged method label == 'meth5 (Class property)', member immediately followed by ' (', no '()' after member, qualifier '(Class property)' retained. PATCHED: HOLDS ('meth5 (Class property)'); BASE: FAILS ('meth5() (Class property)') -> discriminates.
- probe_2 Req2.1: classmethod keeps () -> 'meth() (Class class method)'. HOLDS.
- probe_3 Req2.2/2.3: staticmethod 'meth() (Class static method)' and plain 'meth() (Class method)' keep (). HOLDS.
- probe_4 Req2.4: classmethod+property together select class-method form with () -> 'meth() (Class class method)'. HOLDS.
- probe_5 Req2.5: no-dot ValueError fallback keeps () regardless of property option -> 'func() (in module mod)' and 'func()'. HOLDS.
- probe_6 Req4.1/4.2: py:attribute -> 'attr (Class attribute)' and py:property -> 'prop (Class property)' unchanged (no ()). HOLDS.

Candidate wrong patches (floor: >=1 exercised, >=1 rejected — both REJECTED):
- weak_noop: adds only a comment, leaves property branch with (). REJECTED by probe_1 (VIOLATED: 'meth5() (Class property)'); probes 2-6 hold. Demonstrates suite catches the do-nothing/partial fix.
- weak_stripall: over-broad — strips () from ALL four method-kind branches (classmethod/property/static/plain). REJECTED by probe_2, probe_3, probe_4 (Req2 regression guards fire on classmethod/static/plain losing ()); probe_1/5/6 hold. Demonstrates suite catches the too-aggressive fix.

No requirement-conforming alternative patch survived the suite: the only single-branch edit that passes all 6 probes is exactly the gold edit (property branch only), so no TOO-WEAK finding. Requirements are faithful and discriminating. (Note: meta.json records G-PANEL-3=fail = solution leakage of the meth5/Class fixture identifiers into requirements prose; that is a leakage concern, orthogonal to G-EQ spec fidelity, which is SOUND.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling BOUNDARY is correct: requirements pin the full observable changed behavior (property branch flips to no-parens) AND bound it biconditionally by asserting every non-property branch and the no-dot fallback keep '()'. This distinguishes a faithful twin from a prepatch twin (the property case is the sole discriminator) and forbids over-broad edits (e.g. stripping '()' from static/class/plain methods). Req 2.4 correctly captures the elif precedence (classmethod checked before property). Confirmed on the instance image via nl_attack probe on both patched and base trees.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior abstractly using placeholders (<member>, <class>) and never surface any hidden-test artifact: the test path/function (tests/test_domain_py.py::test_pymethod_options), the concrete identifiers used by the test (meth5, Class), the node index (doctree[1][1][8]), or the parametrization/assert_node structure are all absent. The gold edit changes exactly one format string ('%s() (%s property)' -> '%s (%s property)') in PyMethod.get_index_text; the doc translates this into a behavioral requirement (property label omits trailing ()), which is the legitimate purpose of the spec, not a leak. Named symbols — sphinx/domains/python.py, PyMethod.get_index_text, PyProperty.get_index_text, py:method/py:property/py:attribute, and the option names classmethod/staticmethod/property — are all public Sphinx API and source-module localization; the problem_statement itself names py:method, :property:, py:property. The Req 2 enumeration of the classmethod/staticmethod/method/precedence/fallback label forms is derivable from the public source function's own branch structure (which the fix does not touch) and does NOT mirror the hidden test, which only asserts the single property case. No fix-invented identifiers exist (the fix invents nothing). No leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
