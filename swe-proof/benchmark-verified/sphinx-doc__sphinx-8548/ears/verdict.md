# P2 adversarial audit — sphinx-doc__sphinx-8548

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)

def norm(s): return s.strip() if s else s
members = call_members(M.Bar, ["Bar"])
print("member names:", sorted(members))
ok = "attr1" in members
if ok:
    ca = members["attr1"]
    print("attr1 docstring:", repr(ca.docstring), "class_:", ca.class_)
    ok = (norm(ca.docstring) == "docstring foo") and (ca.class_ is M.Foo)
print("R1.2 holds:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)

def norm(s): return s.strip() if s else s
members = call_members(M.Bar, ["Bar"])
got = {n: norm(members[n].docstring) for n in members if n in ("attr1","attr2","attr3")}
print("got:", got)
expect = {"attr1":"docstring foo","attr2":"docstring bar","attr3":"docstring bar"}
ok = got == expect
print("R1.1/1.3 positive-control holds:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)

def norm(s): return s.strip() if s else s
members = call_members(M.Bar, ["Bar"])
ca = members.get("attr2")
print("attr2 docstring:", repr(ca.docstring) if ca else None)
ok = ca is not None and norm(ca.docstring) == "docstring bar" and norm(ca.docstring) != "docstring foo"
print("R2 shadow-precedence holds:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)

def norm(s): return s.strip() if s else s
members = call_members(M.Foo, ["Foo"])
names = set(n for n in members if n.startswith("attr"))
print("Foo attr members:", {n: norm(members[n].docstring) for n in names})
ok = names == {"attr1","attr2"} and norm(members["attr1"].docstring)=="docstring foo" and norm(members["attr2"].docstring)=="docstring foo"
print("R3.1 own-attrs holds:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)
import enum
# annotation-only + slots class
class Ann:
    x: int
    __slots__ = ("s1",)

m1 = call_members(Ann, ["Ann"])
print("Ann members:", sorted(m1))
ok_ann = "x" in m1 and "s1" in m1

class Color(enum.Enum):
    RED = 1
    GREEN = 2
m2 = call_members(Color, ["Color"])
print("Color members:", sorted(m2))
ok_enum = "RED" in m2 and "GREEN" in m2

ok = ok_ann and ok_enum
print("R3.2 slots/enum/annotation holds:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)
# Build a class whose base is defined via exec (no locatable source module for analysis)
ns = {}
exec("class Dyn:\n    def __init__(self):\n        self.dynattr = None  #: dyn doc\n", ns)
Dyn = ns["Dyn"]
Dyn.__module__ = "sbu_no_such_module_xyz"  # module that cannot be analyzed

class Child(Dyn, M.Bar):
    def __init__(self):
        self.childattr = None  #: docstring child

try:
    members = call_members(Child, ["Child"])
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("members:", sorted(members))
# must not raise, must return a dict, and must still pick up analyzable Bar/Foo attrs
ok = isinstance(members, dict) and "attr3" in members and "attr1" in members
print("R4 robustness holds:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)

def norm(s): return s.strip() if s else s
members = call_members(M.Bar, ["Bar"])
got = {n: norm(members[n].docstring) for n in members if n in ("attr1","attr2","attr3")}
print("got:", got)
expect = {"attr1":"docstring foo","attr2":"docstring bar","attr3":"docstring bar"}
ok = got == expect
print("R1.1/1.3 positive-control holds:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8548: get_class_members must walk the MRO and match each class's own __qualname__ against ModuleAnalyzer.attr_docs so base-only documented instance attributes are collected for a derived class under inherited-members. All probes call get_class_members reproducing the real caller on either tree (base signature takes an analyzer; patched derives per-class analyzers).

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.2): documenting Bar(Foo) includes attr1, associated with class_ is Foo and carrying base docstring 'docstring foo'. HOLDS patched / VIOLATED base (positive control leg).
- probe_2 (R1.1/1.3, POSITIVE CONTROL): full inherited set {attr1:foo, attr2:bar, attr3:bar}. HOLDS patched, VIOLATED at base (base only yields attr2,attr3) -> prepatch_reproduced=true.
- probe_3 (R2 shadow precedence): attr2 retains Bar's docstring 'docstring bar', not Foo's. HOLDS patched.
- probe_4 (R3.1 own attrs): documenting Foo alone yields exactly attr1,attr2 with foo docstrings, no attr3. HOLDS patched.
- probe_5 (R3.2 regression): __slots__ member s1, annotation-only x, and enum members RED/GREEN still collected. HOLDS patched.
- probe_6 (R4 robustness): a base whose __module__ is unanalyzable (set to a nonexistent module) does not raise; returned table still accumulates analyzable Foo/Bar attrs. HOLDS patched.

Candidate wrong patches (both REJECTED by the suite -> discrimination shown):
- weak_A: walks MRO and derives per-class analyzers but matches recorded namespace against the TARGET objpath ('.'.join(objpath)) instead of each class's own qualname (the lazy partial fix). REJECTED by probe_1, probe_2, probe_6 (base-only attr1 dropped).
- weak_B: correct namespace matching but processes MRO base-first (reversed getmro), so a base docstring overwrites the derived one. REJECTED by probe_2 and probe_3 (attr2 gets 'docstring foo').

All six probes hold on the patched tree; positive control (probe_2) fails at base and holds patched; every candidate patch is rejected by >=1 probe. No requirements violation and no probe-conforming weak patch found. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import os, sys, tempfile, inspect
WORK = tempfile.mkdtemp(prefix="sbu_probe_mod_")
MODSRC = ('class Foo:\n'
          '    def __init__(self):\n'
          '        self.attr1 = None  #: docstring foo\n'
          '        self.attr2 = None  #: docstring foo\n\n\n'
          'class Bar(Foo):\n'
          '    def __init__(self):\n'
          '        self.attr2 = None  #: docstring bar\n'
          '        self.attr3 = None  #: docstring bar\n')
open(os.path.join(WORK, "sbu_probe_mod.py"), "w").write(MODSRC)
sys.path.insert(0, WORK)
import sbu_probe_mod as M
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

def call_members(subject, objpath):
    sig = inspect.signature(get_class_members)
    if "analyzer" in sig.parameters:
        an = ModuleAnalyzer.for_module(subject.__module__)
        an.analyze()
        return get_class_members(subject, objpath, safe_getattr, an)
    return get_class_members(subject, objpath, safe_getattr)

def norm(s): return s.strip() if s else s
members = call_members(M.Bar, ["Bar"])
got = {n: norm(members[n].docstring) for n in members if n in ("attr1","attr2","attr3")}
print("got:", got)
expect = {"attr1":"docstring foo","attr2":"docstring bar","attr3":"docstring bar"}
ok = got == expect
print("R1.1/1.3 positive-control holds:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8548: get_class_members must walk the MRO and match each class's own __qualname__ against ModuleAnalyzer.attr_docs so base-only documented instance attributes are collected for a derived class under inherited-members. All probes call get_class_members reproducing the real caller on either tree (base signature takes an analyzer; patched derives per-class analyzers).

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.2): documenting Bar(Foo) includes attr1, associated with class_ is Foo and carrying base docstring 'docstring foo'. HOLDS patched / VIOLATED base (positive control leg).
- probe_2 (R1.1/1.3, POSITIVE CONTROL): full inherited set {attr1:foo, attr2:bar, attr3:bar}. HOLDS patched, VIOLATED at base (base only yields attr2,attr3) -> prepatch_reproduced=true.
- probe_3 (R2 shadow precedence): attr2 retains Bar's docstring 'docstring bar', not Foo's. HOLDS patched.
- probe_4 (R3.1 own attrs): documenting Foo alone yields exactly attr1,attr2 with foo docstrings, no attr3. HOLDS patched.
- probe_5 (R3.2 regression): __slots__ member s1, annotation-only x, and enum members RED/GREEN still collected. HOLDS patched.
- probe_6 (R4 robustness): a base whose __module__ is unanalyzable (set to a nonexistent module) does not raise; returned table still accumulates analyzable Foo/Bar attrs. HOLDS patched.

Candidate wrong patches (both REJECTED by the suite -> discrimination shown):
- weak_A: walks MRO and derives per-class analyzers but matches recorded namespace against the TARGET objpath ('.'.join(objpath)) instead of each class's own qualname (the lazy partial fix). REJECTED by probe_1, probe_2, probe_6 (base-only attr1 dropped).
- weak_B: correct namespace matching but processes MRO base-first (reversed getmro), so a base docstring overwrites the derived one. REJECTED by probe_2 and probe_3 (attr2 gets 'docstring foo').

All six probes hold on the patched tree; positive control (probe_2) fails at base and holds patched; every candidate patch is rejected by >=1 probe. No requirements violation and no probe-conforming weak patch found. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes: (a) get_object_members drops the self.analyzer argument -> Req5 AC1 exact; (b) get_class_members signature drops analyzer param and instead loops `for cls in getmro(subject)`, per-class computes modname/qualname via safe_getattr, ModuleAnalyzer.for_module(modname).analyze(), and matches `ns == qualname` -> Req1 AC1/AC4 and Req5 AC2 exact (pins the full MRO walk + per-class own-module analysis, not a narrow slice); (c) getmro is most-derived-first with `name not in members` guard -> Req2 AC1-AC3 (probe: attr2 retains Bar docstring); (d) annotation-only collection moved inside the MRO loop keeping the `not in members` guard, other passes (slots/enum/directly-defined) untouched -> Req3 AC2/AC3 (test_instance_variable, non-inherited, yields only Bar's attr2/attr3); (e) per-class `except (AttributeError, PycodeError): pass` plus outer `except AttributeError` and safe_getattr -> Req4 AC1-AC3. Req3 AC1/AC4 and Req1 AC3 describe the rendered autodoc directive output, matching the test_ext_autodoc_autoclass F2P tests. No requirement mandates behavior the code lacks, forbids behavior it has, invents behavior, or pins the wrong boundary. Base-vs-patched probe cleanly separates (base VIOLATED on attr1, patched HOLDS).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the gold fix into behavioral EARS requirements at an appropriate abstraction: MRO-wide attribute-docstring collection, matching entries whose namespace equals each class's qualified name (the __qualname__ vs objpath change), first-occurrence-wins precedence for shadowed names, PycodeError/AttributeError robustness for unanalyzable base classes, and the caller dropping the single analyzer argument. Naming get_class_members, ClassDocumenter.get_object_members, sphinx.ext.autodoc.importer, and sphinx.pycode.ModuleAnalyzer is legitimate localization — these are the modules/functions the gold patch edits, and the public problem_statement already frames the issue as autodoc's (namespace, attrname) search-key not checking base-class namespaces. No hidden-test content is transmitted: the fixture class names (Foo/Bar), attribute names (attr1/attr2/attr3), docstring literals ('docstring foo'/'docstring bar'), test function names (test_instance_variable, test_inherited_instance_variable), test file paths (tests/test_ext_autodoc_autoclass.py, tests/roots/.../instance_variable.py), and the exact rST directive output lines appear NOWHERE in requirements.md. The generic examples used (self.attr = None #: docstring, attr: int) are standard Sphinx comment-docstring/annotation syntax and are consistent with the public problem_statement and hints, not reconstructions of the parametrized test cases.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
