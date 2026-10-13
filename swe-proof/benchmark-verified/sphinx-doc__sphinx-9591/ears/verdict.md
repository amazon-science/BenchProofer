# P2 adversarial audit — sphinx-doc__sphinx-9591

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_xref.py`, `probe_2_separator.py`, `probe_3_notype.py`, `probe_4_prefix.py`, `probe_5_data_attr.py`, `probe_6_union.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_xref.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_xref.py` → holds on the patched tree (good)

```python
# Requirement 1.2 (POSITIVE CONTROL): a documented property's declared type is
# parsed into a cross-reference node (pending_xref), not inert plain text.
import tempfile, sys
from io import StringIO
from docutils import nodes
from sphinx import addnodes

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text)
    finally:
        app.cleanup()

def prop_signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

text = (".. py:class:: Class\n\n"
        "   .. py:property:: prop1\n"
        "      :type: str\n")
doc = render(text)
sig = prop_signode(doc, "prop1")
assert sig is not None, "property signode not found"
# the type annotation is the desc_annotation that carries the ': ' separator
xrefs = list(sig.traverse(addnodes.pending_xref))
targets = [x.get("reftarget") for x in xrefs]
print("pending_xref targets in prop1 signature:", targets)
ok = any(t == "str" for t in targets)
print("has cross-reference for type 'str':", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_separator.py` → holds on the patched tree (good)

```python
# Requirement 1.1 & 1.3: the type-annotation node's children begin with a
# plain-text node holding exactly ": " followed by the parsed type nodes.
import tempfile, sys
from io import StringIO
from docutils import nodes
from sphinx import addnodes

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text)
    finally:
        app.cleanup()

def prop_signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

text = (".. py:class:: Class\n\n"
        "   .. py:property:: prop1\n"
        "      :type: str\n")
doc = render(text)
sig = prop_signode(doc, "prop1")
assert sig is not None
# Identify the type-annotation desc_annotation: the one containing a pending_xref
# or whose text starts with ': '. The name is prop1; the prefix annotation is
# 'property '. So find desc_annotation whose astext starts with ':'.
ann = None
for a in sig.traverse(addnodes.desc_annotation):
    if a.astext().startswith(":"):
        ann = a
        break
assert ann is not None, "no type annotation found"
kids = list(ann.children)
print("type annotation children types:", [type(k).__name__ for k in kids])
first = kids[0]
print("first child is Text:", isinstance(first, nodes.Text), "value=%r" % first.astext())
# first child must be a plain Text node == ": "
cond_first = isinstance(first, nodes.Text) and first.astext() == ": "
# there must be a pending_xref among the remaining (parsed) nodes
has_xref = any(isinstance(k, addnodes.pending_xref) or list(k.traverse(addnodes.pending_xref)) for k in kids[1:])
print("first is exactly ': ':", cond_first, " parsed nodes contain xref:", bool(has_xref))
sys.exit(0 if (cond_first and has_xref) else 1)
```

Attack 3 — `probe_3_notype.py` → holds on the patched tree (good)

```python
# Requirement 1.4: no type option -> NO type-annotation node appended.
import tempfile, sys
from io import StringIO
from docutils import nodes
from sphinx import addnodes

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text)
    finally:
        app.cleanup()

def prop_signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

text = (".. py:class:: Class\n\n"
        "   .. py:property:: prop_notype\n")
doc = render(text)
sig = prop_signode(doc, "prop_notype")
assert sig is not None
type_anns = [a for a in sig.traverse(addnodes.desc_annotation) if a.astext().startswith(":")]
print("type-annotation nodes (should be 0):", len(type_anns))
# also ensure the prefix annotation 'property ' is still there
prefix_anns = [a for a in sig.traverse(addnodes.desc_annotation) if "property" in a.astext()]
print("prefix annotation present:", len(prefix_anns) > 0)
sys.exit(0 if (len(type_anns) == 0 and prefix_anns) else 1)
```

Attack 4 — `probe_4_prefix.py` → holds on the patched tree (good)

```python
# Requirement 2.1 & 2.3: property signature prefix. abstractmethod->'abstract property ',
# classmethod->'class property '. And type annotation still rendered per Req1.
import tempfile, sys
from io import StringIO
from docutils import nodes
from sphinx import addnodes

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text)
    finally:
        app.cleanup()

def prop_signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

text = (".. py:class:: Class\n\n"
        "   .. py:property:: prop1\n"
        "      :abstractmethod:\n"
        "      :type: str\n\n"
        "   .. py:property:: prop2\n"
        "      :classmethod:\n"
        "      :type: str\n")
doc = render(text)
ok = True
for name, expected_prefix in (("prop1", "abstract property"), ("prop2", "class property")):
    sig = prop_signode(doc, name)
    assert sig is not None, name
    prefix_ann = None
    for a in sig.traverse(addnodes.desc_annotation):
        t = a.astext()
        if not t.startswith(":"):
            prefix_ann = a
            break
    ptext = prefix_ann.astext() if prefix_ann is not None else "<none>"
    # normalize whitespace
    norm = " ".join(ptext.split())
    print(f"{name}: prefix={norm!r}")
    if norm != expected_prefix:
        ok = False
    # and type annotation with xref still present
    xrefs = [x.get("reftarget") for x in sig.traverse(addnodes.pending_xref)]
    print(f"{name}: type xrefs={xrefs}")
    if "str" not in xrefs:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_data_attr.py` → holds on the patched tree (good)

```python
# Requirement 3.1 & 3.2: data and attribute annotations still render ': ' + parsed
# cross-reference-aware nodes (regression). attribute value option unchanged.
import tempfile, sys
from io import StringIO
from docutils import nodes
from sphinx import addnodes

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text)
    finally:
        app.cleanup()

def signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

# data object
text_data = (".. py:data:: dvar\n"
             "   :type: int\n")
doc = render(text_data)
sig = signode(doc, "dvar")
assert sig is not None
xrefs = [x.get("reftarget") for x in sig.traverse(addnodes.pending_xref)]
has_colon = any(a.astext().startswith(":") for a in sig.traverse(addnodes.desc_annotation))
print("data dvar: xrefs=", xrefs, "colon-annotation=", has_colon)
ok = ("int" in xrefs) and has_colon

# attribute object with type + value
text_attr = (".. py:class:: C\n\n"
             "   .. py:attribute:: attr\n"
             "      :type: int\n"
             "      :value: 5\n")
doc2 = render(text_attr)
sig2 = signode(doc2, "attr")
assert sig2 is not None
xrefs2 = [x.get("reftarget") for x in sig2.traverse(addnodes.pending_xref)]
full = sig2.astext()
print("attr: xrefs=", xrefs2, "text=", repr(full))
ok = ok and ("int" in xrefs2) and ("= 5" in full)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_union.py` → holds on the patched tree (good)

```python
# Requirement 1.2 + 3.3: a compound/union type on a property is fully parsed
# (each type name -> its own xref), matching _parse_annotation behavior.
import tempfile, sys
from io import StringIO
from sphinx import addnodes
from sphinx.domains.python import _parse_annotation

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text), app
    finally:
        pass

def prop_signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

text = (".. py:class:: Class\n\n"
        "   .. py:property:: prop1\n"
        "      :type: str | int\n")
doc, app = render(text)
try:
    sig = prop_signode(doc, "prop1")
    assert sig is not None
    xrefs = sorted(x.get("reftarget") for x in sig.traverse(addnodes.pending_xref))
    print("property union xref targets:", xrefs)
    # Compare against what _parse_annotation itself yields for the same type
    nodes_list = _parse_annotation("str | int", app.env)
    from docutils import nodes as dn
    direct = sorted(x.get("reftarget")
                    for n in nodes_list
                    for x in ([n] if isinstance(n, addnodes.pending_xref) else n.traverse(addnodes.pending_xref)))
    print("_parse_annotation direct targets:", direct)
    ok = xrefs == ["int", "str"] and direct == ["int", "str"]
finally:
    app.cleanup()
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_xref.py`

```python
# Requirement 1.2 (POSITIVE CONTROL): a documented property's declared type is
# parsed into a cross-reference node (pending_xref), not inert plain text.
import tempfile, sys
from io import StringIO
from docutils import nodes
from sphinx import addnodes

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text)
    finally:
        app.cleanup()

def prop_signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

text = (".. py:class:: Class\n\n"
        "   .. py:property:: prop1\n"
        "      :type: str\n")
doc = render(text)
sig = prop_signode(doc, "prop1")
assert sig is not None, "property signode not found"
# the type annotation is the desc_annotation that carries the ': ' separator
xrefs = list(sig.traverse(addnodes.pending_xref))
targets = [x.get("reftarget") for x in xrefs]
print("pending_xref targets in prop1 signature:", targets)
ok = any(t == "str" for t in targets)
print("has cross-reference for type 'str':", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-9591: PyProperty.handle_signature must parse a property's declared :type: through the shared _parse_annotation helper so type names become pending_xref cross-references, instead of emitting inert ': '+typ plain text. Gold patch: `signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *_parse_annotation(typ, self.env))`. Hidden test tests/test_domain_py.py::test_pyproperty (after test_patch) requires the type annotation to be [desc_annotation, (': ', [pending_xref, 'str'])].

Probe suite (all HOLD on gold-patched tree; ran in the official Docker image; docutils uses .traverse not .findall in this py3.9 image):
- probe_1_xref (Req 1.2, POSITIVE CONTROL): property type 'str' produces a pending_xref with reftarget 'str'. HOLDS patched, FAILS at base (base emits only inert text). Discriminates.
- probe_2_separator (Req 1.1/1.3): type annotation children begin with a distinct plain Text node exactly ': ' followed by parsed nodes containing an xref. HOLDS patched, FAILS at base (base child is single Text ': str').
- probe_3_notype (Req 1.4): property with no :type: appends NO type-annotation node (prefix 'property ' still present). HOLDS on both (regression guard).
- probe_4_prefix (Req 2.1/2.3): abstractmethod->'abstract property ', classmethod->'class property ' prefixes preserved AND type still rendered as xref. HOLDS patched.
- probe_5_data_attr (Req 3.1/3.2): data and attribute :type: still render ': '+parsed xref nodes; attribute :value: 5 still rendered ('attr: int = 5'). HOLDS on both (unchanged directives regression).
- probe_6_union (Req 1.2/3.3): compound type 'str | int' on a property yields per-name xrefs {int,str}, matching _parse_annotation's own output. HOLDS patched, FAILS at base.

Candidate wrong-fix EXERCISED and REJECTED: weak_plain.diff restructures the desc_annotation into two separate Text nodes (': ', typ) WITHOUT calling _parse_annotation — the lazy fix a weak reading permits. Probes 1,2,4,6 REJECT it (no pending_xref produced), and it would fail the hidden test_pyproperty which requires [pending_xref, 'str']. This proves the suite discriminates the correct parse-based fix from a cosmetic non-fix. No requirements-conforming alternative that fails the harness was found.

Verdict SOUND: 6 distinct probes all hold on the patched tree, positive control discriminates (holds patched, fails at base), and a plausible wrong fix is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_xref.py`, `probe_2_separator.py`, `probe_3_notype.py`, `probe_4_prefix.py`, `probe_5_data_attr.py`, `probe_6_union.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_xref.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_xref.py` → holds on the patched tree (good)

Attack 2 — `probe_2_separator.py` → holds on the patched tree (good)

Attack 3 — `probe_3_notype.py` → holds on the patched tree (good)

Attack 4 — `probe_4_prefix.py` → holds on the patched tree (good)

Attack 5 — `probe_5_data_attr.py` → holds on the patched tree (good)

Attack 6 — `probe_6_union.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_xref.py`

```python
# Requirement 1.2 (POSITIVE CONTROL): a documented property's declared type is
# parsed into a cross-reference node (pending_xref), not inert plain text.
import tempfile, sys
from io import StringIO
from docutils import nodes
from sphinx import addnodes

def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path
    from sphinx.testing import restructuredtext
    srcdir = path(tempfile.mkdtemp())
    (srcdir / "conf.py").write_text("", encoding="utf8")
    (srcdir / "index.rst").write_text("", encoding="utf8")
    app = SphinxTestApp(srcdir=srcdir, status=StringIO(), warning=StringIO())
    try:
        return restructuredtext.parse(app, text)
    finally:
        app.cleanup()

def prop_signode(doc, name):
    for sig in doc.traverse(addnodes.desc_signature):
        for nm in sig.traverse(addnodes.desc_name):
            if nm.astext() == name:
                return sig
    return None

text = (".. py:class:: Class\n\n"
        "   .. py:property:: prop1\n"
        "      :type: str\n")
doc = render(text)
sig = prop_signode(doc, "prop1")
assert sig is not None, "property signode not found"
# the type annotation is the desc_annotation that carries the ': ' separator
xrefs = list(sig.traverse(addnodes.pending_xref))
targets = [x.get("reftarget") for x in xrefs]
print("pending_xref targets in prop1 signature:", targets)
ok = any(t == "str" for t in targets)
print("has cross-reference for type 'str':", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-9591: PyProperty.handle_signature must parse a property's declared :type: through the shared _parse_annotation helper so type names become pending_xref cross-references, instead of emitting inert ': '+typ plain text. Gold patch: `signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *_parse_annotation(typ, self.env))`. Hidden test tests/test_domain_py.py::test_pyproperty (after test_patch) requires the type annotation to be [desc_annotation, (': ', [pending_xref, 'str'])].

Probe suite (all HOLD on gold-patched tree; ran in the official Docker image; docutils uses .traverse not .findall in this py3.9 image):
- probe_1_xref (Req 1.2, POSITIVE CONTROL): property type 'str' produces a pending_xref with reftarget 'str'. HOLDS patched, FAILS at base (base emits only inert text). Discriminates.
- probe_2_separator (Req 1.1/1.3): type annotation children begin with a distinct plain Text node exactly ': ' followed by parsed nodes containing an xref. HOLDS patched, FAILS at base (base child is single Text ': str').
- probe_3_notype (Req 1.4): property with no :type: appends NO type-annotation node (prefix 'property ' still present). HOLDS on both (regression guard).
- probe_4_prefix (Req 2.1/2.3): abstractmethod->'abstract property ', classmethod->'class property ' prefixes preserved AND type still rendered as xref. HOLDS patched.
- probe_5_data_attr (Req 3.1/3.2): data and attribute :type: still render ': '+parsed xref nodes; attribute :value: 5 still rendered ('attr: int = 5'). HOLDS on both (unchanged directives regression).
- probe_6_union (Req 1.2/3.3): compound type 'str | int' on a property yields per-name xrefs {int,str}, matching _parse_annotation's own output. HOLDS patched, FAILS at base.

Candidate wrong-fix EXERCISED and REJECTED: weak_plain.diff restructures the desc_annotation into two separate Text nodes (': ', typ) WITHOUT calling _parse_annotation — the lazy fix a weak reading permits. Probes 1,2,4,6 REJECT it (no pending_xref produced), and it would fail the hidden test_pyproperty which requires [pending_xref, 'str']. This proves the suite discriminates the correct parse-based fix from a cosmetic non-fix. No requirements-conforming alternative that fails the harness was found.

Verdict SOUND: 6 distinct probes all hold on the patched tree, positive control discriminates (holds patched, fails at base), and a plausible wrong fix is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a 2-line change confined to PyProperty.handle_signature (`': ' + typ` inert desc_annotation replaced by parsed annotation with a leading ': ' Text node). Requirements pin precisely the changed observable behavior at the correct boundary; no over/under-specification, no invented behavior. Verified via nl_attack probes on patched tree (source inspection + functional xref/separator check).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the behavioral change (render a property's declared type via the shared _parse_annotation helper, emitting a ': ' Text node followed by cross-reference-aware inline nodes) and localizes it to PyProperty.handle_signature. All specifics are public or legitimate: (1) the cross-reference goal and ': '+type prior behavior are stated in problem_statement; (2) _parse_annotation is a pre-existing codebase symbol, not a fix-invented identifier (the gold patch calls the same existing function); (3) the 'property '/'abstract '/'class ' prefixes are documented directive options, not test-derived; (4) mentioning data/attribute parity is behavioral context. No test names (test_pyproperty), file paths (tests/test_domain_py.py), node-structure assertions ([pending_xref, 'str'], desc_annotation), parametrization ids, or verbatim gold lines (nodes.Text(': '), addnodes.desc_annotation(...)) are reproduced. The doc translates test intent into requirements rather than transmitting the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
