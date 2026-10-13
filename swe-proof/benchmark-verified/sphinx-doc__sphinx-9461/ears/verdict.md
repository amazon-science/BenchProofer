# P2 adversarial audit — sphinx-doc__sphinx-9461

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_prefix_class.py`, `probe_prefix_variants.py`, `probe_option_spec.py`, `probe_domain_index.py`, `probe_autodoc.py`, `probe_isclassmethod.py`, `probe_getdoc.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_prefix_class.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_prefix_class.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): classmethod flag -> prefix "class property "
from sphinx.domains.python import PyProperty
inst = PyProperty.__new__(PyProperty)
inst.options = {'classmethod': True}
p = inst.get_signature_prefix("")
print("classmethod-only prefix:", repr(p))
assert p == "class property ", p
print("OK")
```

Attack 2 — `probe_prefix_variants.py` → holds on the patched tree (good)

```python
# Req 1.3/1.4/1.5: prefix variants
from sphinx.domains.python import PyProperty
def prefix(opts):
    inst = PyProperty.__new__(PyProperty)
    inst.options = opts
    return inst.get_signature_prefix("")
none = prefix({})
abstract = prefix({'abstractmethod': True})
both = prefix({'abstractmethod': True, 'classmethod': True})
print("none:", repr(none), "abstract:", repr(abstract), "both:", repr(both))
assert none == "property ", none            # 1.5
assert abstract == "abstract property ", abstract  # 1.3
assert both == "abstract class property ", both    # 1.4
print("OK")
```

Attack 3 — `probe_option_spec.py` → holds on the patched tree (good)

```python
# Req 1.1: classmethod flag option accepted alongside abstractmethod & type
from docutils.parsers.rst import directives
from sphinx.domains.python import PyProperty
spec = PyProperty.option_spec
print("keys:", sorted(spec.keys()))
assert 'classmethod' in spec, "classmethod option missing"
assert 'abstractmethod' in spec
assert 'type' in spec
assert spec['classmethod'] is directives.flag, spec['classmethod']
print("OK")
```

Attack 4 — `probe_domain_index.py` → holds on the patched tree (good)

```python
# Req 2: index entry + domain object registration for a class-level property.
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.restructuredtext import parse
from sphinx.testing.path import path as sphinx_path
import tempfile, os
_sd=tempfile.mkdtemp()
open(os.path.join(_sd,'conf.py'),'w').write('')
open(os.path.join(_sd,'index.rst'),'w').write('')
from sphinx.addnodes import index as index_node

app = SphinxTestApp('dummy', srcdir=sphinx_path(_sd))
try:
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:property:: prop1\n"
            "      :abstractmethod:\n"
            "      :type: str\n"
            "\n"
            "   .. py:property:: prop2\n"
            "      :classmethod:\n"
            "      :type: str\n")
    doctree = parse(app, text)
    domain = app.env.get_domain('py')
    # Req 2.2: object registration
    print("objects:", {k: v for k,v in domain.objects.items() if k.startswith('Class.')})
    assert 'Class.prop2' in domain.objects, "prop2 not registered (Req 2.2)"
    assert domain.objects['Class.prop2'] == ('index', 'Class.prop2', 'property', False), domain.objects['Class.prop2']
    # Req 2.3: ordinary prop still registered unchanged
    assert 'Class.prop1' in domain.objects
    assert domain.objects['Class.prop1'] == ('index', 'Class.prop1', 'property', False)
    # Req 2.1: index text form "prop2 (Class property)"
    entries = []
    for node in doctree.traverse(index_node):
        entries.extend(node['entries'])
    print("index entries:", entries)
    got = [e[1] for e in entries]
    assert 'prop2 (Class property)' in got, "no class-level index entry (Req 2.1)"
    assert 'prop1 (Class property)' in got, "no ordinary index entry (Req 2.1/2.3)"
    print("OK")
finally:
    app.cleanup()
```

Attack 5 — `probe_autodoc.py` → holds on the patched tree (good)

```python
# Req 3 & 4: autodoc discovers a classmethod-property member, marks it
# :classmethod:, emits :type: int and docstring; ordinary property has no
# :classmethod:. Self-contained module (test_patch not applied to the tree).
import os, sys, textwrap
from unittest.mock import Mock

# create our own module with prop1 (ordinary) and prop2 (classmethod-property)
moddir = '$SCRATCH'
os.makedirs(moddir, exist_ok=True)
open(os.path.join(moddir, 'myprops.py'), 'w').write(textwrap.dedent('''
    class Foo:
        """docstring"""
        @property
        def prop1(self) -> int:
            """docstring"""
        @classmethod
        @property
        def prop2(cls) -> int:
            """docstring"""
'''))
sys.path.insert(0, moddir)

from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
root=None
for r, dirs, files in os.walk('/testbed/tests'):
    if r.endswith('roots/test-ext-autodoc') and os.path.isdir(os.path.join(r,'target')):
        root=r; break
assert root
app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
try:
    from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
    from sphinx.util.docutils import LoggingReporter
    app.setup_extension('sphinx.ext.autodoc')
    doccls = app.registry.documenters['class']
    docoptions = process_documenter_options(doccls, app.config, {'members': None})
    state = Mock(); state.document.settings.tab_width = 8
    app.env.temp_data['docname']='index'
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    d = doccls(bridge, 'myprops.Foo')
    d.generate()
    lines = list(bridge.result)
    text = '\n'.join(lines)
    print("=== GENERATED ===")
    print(text)
    print("=== END ===")

    assert 'py:property:: Foo.prop2' in text, "prop2 not documented (Req 3.1/3.2)"
    i2 = next(k for k,l in enumerate(lines) if 'Foo.prop2' in l)
    block2 = '\n'.join(lines[i2:i2+7])
    assert ':classmethod:' in block2, "no :classmethod: for prop2 (Req 4.1)"
    assert ':type: int' in block2, "no :type: int for prop2 (Req 4.3)"
    assert 'docstring' in block2, "no docstring for prop2 (Req 4.4)"

    i1 = next(k for k,l in enumerate(lines) if 'Foo.prop1' in l)
    block1 = '\n'.join(lines[i1:i2])
    assert 'py:property:: Foo.prop1' in text, "prop1 not documented (Req 3.4)"
    assert ':classmethod:' not in block1, "prop1 wrongly marked classmethod (Req 4.2)"
    assert ':type: int' in block1, "prop1 missing type (Req 4.3)"
    assert 'docstring' in block1, "prop1 missing docstring (Req 4.4)"
    print("OK")
finally:
    app.cleanup()
```

Attack 6 — `probe_isclassmethod.py` → holds on the patched tree (good)

```python
# Req 5.1 & 5.2: isclassmethod recognizes classmethod objs & cls/name path
from sphinx.util.inspect import isclassmethod
class A:
    @classmethod
    @property
    def cp(cls):
        "cp doc"
        return 1
    @classmethod
    def cm(cls): return 2
    @property
    def p(self): return 3
# 5.1: a classmethod object
print("cm dict entry classmethod?", isclassmethod(A.__dict__['cm']))
assert isclassmethod(A.__dict__['cm']) is True
# 5.1: bound method bound to a class
print("A.cm bound?", isclassmethod(A.cm))
assert isclassmethod(A.cm) is True
# 5.2: cls/name path - the classmethod-wrapped property. A.cp resolves to the
# property object (not a classmethod obj), but via cls/name it's a classmethod.
obj = A.__dict__['cp']  # classmethod object
print("cp via cls/name:", isclassmethod(A.cp, A, 'cp'))
assert isclassmethod(A.cp, A, 'cp') is True
# plain property should NOT be a classmethod
print("plain prop:", isclassmethod(A.__dict__['p'], A, 'p'))
assert isclassmethod(A.__dict__['p'], A, 'p') is False
print("OK")
```

Attack 7 — `probe_getdoc.py` → holds on the patched tree (good)

```python
# Req 5.3 & 5.4: getdoc with cls/name returns wrapped-function docstring for
# classmethod-property; preserves ordinary behavior otherwise.
from sphinx.util.inspect import getdoc
class A:
    @classmethod
    @property
    def cp(cls):
        "cp docstring here"
        return 1
    @property
    def p(self):
        "plain prop doc"
        return 2
# 5.3: classmethod-wrapped property -> underlying function docstring
d = getdoc(A.cp, cls=A, name='cp')
print("cp getdoc:", repr(d))
assert d == "cp docstring here", d
# 5.4: ordinary object docstring resolution still works
def f():
    "func doc"
    return 0
d2 = getdoc(f)
print("func getdoc:", repr(d2))
assert d2 == "func doc", d2
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_prefix_class.py`

```python
# Req 1.2 (POSITIVE CONTROL): classmethod flag -> prefix "class property "
from sphinx.domains.python import PyProperty
inst = PyProperty.__new__(PyProperty)
inst.options = {'classmethod': True}
p = inst.get_signature_prefix("")
print("classmethod-only prefix:", repr(p))
assert p == "class property ", p
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9461: support @classmethod @property attributes. 7 probes, each stdlib+sphinx only, all HOLD on gold-patched tree.

Positive control: probe_prefix_class (Req 1.2) -> PyProperty.get_signature_prefix with {'classmethod'} yields 'class property '. HOLDS patched, FAILS at base (base returns 'property'). Discriminates.

Probe coverage vs criteria:
- probe_prefix_class: Req 1.2 (class-only prefix). patched HOLDS, base FAILS.
- probe_prefix_variants: Req 1.3/1.4/1.5 (none->'property ', abstract->'abstract property ', both->'abstract class property '). patched HOLDS.
- probe_option_spec: Req 1.1 (option_spec has 'classmethod' flag alongside abstractmethod & type). patched HOLDS.
- probe_domain_index: Req 2.1/2.2/2.3 (index entries 'prop2 (Class property)'; domain.objects['Class.prop2']==('index','Class.prop2','property',False); ordinary prop1 unchanged). patched HOLDS.
- probe_autodoc: Req 3.1/3.2/3.4 + 4.1/4.2/4.3/4.4 (autodoc discovers classmethod-property Foo.prop2, emits :classmethod:, :type: int, docstring; ordinary prop1 has NO :classmethod:). Self-contained module written to /tmp since test_patch not applied to tree. patched HOLDS, base FAILS (prop2 not documented at base).
- probe_isclassmethod: Req 5.1/5.2 (isclassmethod recognizes classmethod obj, class-bound method, and cls/name MRO path for classmethod-property; plain property is not). patched HOLDS.
- probe_getdoc: Req 5.3/5.4 (getdoc(obj, cls, name) returns wrapped-function docstring for classmethod-property; ordinary object docstring preserved). patched HOLDS.

Candidate patch (weak_partial.diff): applies ONLY the sphinx/domains/python.py directive change (classmethod option + prefix), omitting the autodoc PropertyDocumenter and util/inspect changes -- the lazy partial fix a weak reading of Req 1 alone permits. Under it: probe_prefix_class, probe_prefix_variants, probe_option_spec, probe_domain_index all HOLD (directive-level), but probe_autodoc, probe_isclassmethod, probe_getdoc are all REJECTED (VIOLATED). This demonstrates the suite discriminates wrong/partial implementations across Req 3/4/5. This candidate would NOT resolve the hidden tests (test_ext_autodoc_autoclass::test_properties, test_ext_autodoc_autoproperty::test_class_properties both need the autodoc discovery). So it is a rejected candidate, not a too-weak finding.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control discriminates (base fails), and a probe-conforming-only-of-Req1 partial patch is rejected. No requirement mandates behavior the gold patch lacks; no probe-conforming alternative found. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_prefix_class.py`, `probe_prefix_variants.py`, `probe_option_spec.py`, `probe_domain_index.py`, `probe_autodoc.py`, `probe_isclassmethod.py`, `probe_getdoc.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_prefix_class.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_prefix_class.py` → holds on the patched tree (good)

Attack 2 — `probe_prefix_variants.py` → holds on the patched tree (good)

Attack 3 — `probe_option_spec.py` → holds on the patched tree (good)

Attack 4 — `probe_domain_index.py` → holds on the patched tree (good)

Attack 5 — `probe_autodoc.py` → holds on the patched tree (good)

Attack 6 — `probe_isclassmethod.py` → holds on the patched tree (good)

Attack 7 — `probe_getdoc.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_prefix_class.py`

```python
# Req 1.2 (POSITIVE CONTROL): classmethod flag -> prefix "class property "
from sphinx.domains.python import PyProperty
inst = PyProperty.__new__(PyProperty)
inst.options = {'classmethod': True}
p = inst.get_signature_prefix("")
print("classmethod-only prefix:", repr(p))
assert p == "class property ", p
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9461: support @classmethod @property attributes. 7 probes, each stdlib+sphinx only, all HOLD on gold-patched tree.

Positive control: probe_prefix_class (Req 1.2) -> PyProperty.get_signature_prefix with {'classmethod'} yields 'class property '. HOLDS patched, FAILS at base (base returns 'property'). Discriminates.

Probe coverage vs criteria:
- probe_prefix_class: Req 1.2 (class-only prefix). patched HOLDS, base FAILS.
- probe_prefix_variants: Req 1.3/1.4/1.5 (none->'property ', abstract->'abstract property ', both->'abstract class property '). patched HOLDS.
- probe_option_spec: Req 1.1 (option_spec has 'classmethod' flag alongside abstractmethod & type). patched HOLDS.
- probe_domain_index: Req 2.1/2.2/2.3 (index entries 'prop2 (Class property)'; domain.objects['Class.prop2']==('index','Class.prop2','property',False); ordinary prop1 unchanged). patched HOLDS.
- probe_autodoc: Req 3.1/3.2/3.4 + 4.1/4.2/4.3/4.4 (autodoc discovers classmethod-property Foo.prop2, emits :classmethod:, :type: int, docstring; ordinary prop1 has NO :classmethod:). Self-contained module written to /tmp since test_patch not applied to tree. patched HOLDS, base FAILS (prop2 not documented at base).
- probe_isclassmethod: Req 5.1/5.2 (isclassmethod recognizes classmethod obj, class-bound method, and cls/name MRO path for classmethod-property; plain property is not). patched HOLDS.
- probe_getdoc: Req 5.3/5.4 (getdoc(obj, cls, name) returns wrapped-function docstring for classmethod-property; ordinary object docstring preserved). patched HOLDS.

Candidate patch (weak_partial.diff): applies ONLY the sphinx/domains/python.py directive change (classmethod option + prefix), omitting the autodoc PropertyDocumenter and util/inspect changes -- the lazy partial fix a weak reading of Req 1 alone permits. Under it: probe_prefix_class, probe_prefix_variants, probe_option_spec, probe_domain_index all HOLD (directive-level), but probe_autodoc, probe_isclassmethod, probe_getdoc are all REJECTED (VIOLATED). This demonstrates the suite discriminates wrong/partial implementations across Req 3/4/5. This candidate would NOT resolve the hidden tests (test_ext_autodoc_autoclass::test_properties, test_ext_autodoc_autoproperty::test_class_properties both need the autodoc discovery). So it is a rejected candidate, not a too-weak finding.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control discriminates (base fails), and a probe-conforming-only-of-Req1 partial patch is rejected. No requirement mandates behavior the gold patch lacks; no probe-conforming alternative found. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch touches three files: sphinx/domains/python.py (PyProperty option + prefix), sphinx/ext/autodoc/__init__.py (can_document_member, import_object resolving wrapped property, add_directive_header emitting :classmethod:, getdoc call args), sphinx/util/inspect.py (isclassmethod cls/name path, getdoc cls/name path). All five requirements map onto the actual changed observable behavior with no narrow-slice boundary, no invented behavior, and no forbidden behavior. FAIL_TO_PASS tests (test_pyproperty, test_properties, test_class_properties) align with the specified prefix/discovery/docstring behavior. Verified via nl_attack probe (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md translates hidden-test-checked behavior into behavioral EARS requirements without transmitting the tests themselves. Checks performed: (1) No test names, paths, or ids leaked — no mention of test_pyproperty / test_class_properties / test_properties, tests/test_domain_py.py, tests/test_ext_autodoc_autoproperty.py, or the fixture path tests/roots/test-ext-autodoc/target/properties.py. (2) No test-fixture identifiers leaked — the doc never names prop1/prop2/Foo/Class/target.properties or the literal domain-object tuples ('index','Class.prop2','property',False). (3) Named modules/functions (PyProperty, PropertyDocumenter, isclassmethod, getdoc in sphinx/domains/python.py, sphinx/ext/autodoc/__init__.py, sphinx/util/inspect.py) are legitimate localization of the change; isclassmethod/getdoc are pre-existing helpers, not fix-invented identifiers. (4) The signature-prefix output strings ('property ', 'class property ', 'abstract class property ') are behavioral outputs; notably Req 1.4's 'abstract class property ' combination is NOT exercised by any hidden test (tests only assert 'abstract property ' and 'class property '), so this is genuine behavioral generalization, the opposite of mirroring the parametrization. (5) The @classmethod/@property demo snippet in the Introduction is already present verbatim in the public problem_statement. (6) Index/inventory requirements (Req 2) describe get_index_text and domain-object registration semantics generically rather than reproducing the test's literal assertion data. Naming the :classmethod:/:abstractmethod:/:type: directive options is describing the public directive surface, not the hidden tests. This is behavior-describing, not test-reconstructing.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
