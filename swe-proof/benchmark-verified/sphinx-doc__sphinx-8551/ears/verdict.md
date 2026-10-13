# P2 adversarial audit — sphinx-doc__sphinx-8551

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
"""Positive control. Req 1.1/1.2/1.5 + Req 2: an info-field type xref built
inside a module+class carries py:module and py:class of the surrounding scope.
Must HOLD patched, FAIL at base."""
import os, sys, tempfile

def build():
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param str name: blah blah\n"
            "   :param age: blah blah\n"
            "   :type age: int\n")
    return restructuredtext.parse(app, text)

def main():
    from sphinx import addnodes
    doctree = build()
    xrefs = list(doctree.traverse(addnodes.pending_xref))
    print("found %d pending_xref" % len(xrefs))
    targets = {}
    for x in xrefs:
        targets[x.get('reftarget')] = x
    print("targets:", sorted(targets))
    ok = True
    for tname in ("str", "int"):
        if tname not in targets:
            print("MISSING xref for", tname); ok = False; continue
        x = targets[tname]
        m = x.get('py:module'); c = x.get('py:class')
        print("%s -> py:module=%r py:class=%r reftype=%r refdomain=%r"
              % (tname, m, c, x.get('reftype'), x.get('refdomain')))
        if m != "example" or c != "Class":
            print("  FAIL scope not recorded for", tname); ok = False
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3 & 1.4: with NO surrounding module and NO class, the xref's
py:module and py:class entries are null/absent (mirror missing context),
not a fabricated name."""
import os, sys, tempfile

def build(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    return restructuredtext.parse(app, text)

def main():
    from sphinx import addnodes
    # A function with a param type, no module, no class in scope.
    text = (".. py:function:: foo(name)\n"
            "\n"
            "   :param str name: blah\n")
    doctree = build(text)
    xrefs = [x for x in doctree.traverse(addnodes.pending_xref)
             if x.get('reftarget') == 'str']
    print("found %d str xref" % len(xrefs))
    if not xrefs:
        print("MISSING"); sys.exit(1)
    x = xrefs[0]
    m = x.get('py:module'); c = x.get('py:class')
    print("py:module=%r py:class=%r" % (m, c))
    # null/absent, NOT fabricated. Accept None (absent-ish).
    ok = (m in (None,)) and (c in (None,))
    if not ok:
        print("FAIL: fabricated scope name where context was empty")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1, 3.5, 3.6: xref remains refspecific, is a py-domain pending_xref
with class-style reftype, and a fully qualified name is kept verbatim as
reftarget (already-correct qualified refs unaffected)."""
import os, sys, tempfile

def build(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    return restructuredtext.parse(app, text)

def main():
    from sphinx import addnodes
    text = (".. py:module:: mod.submod\n"
            ".. py:function:: foo(name)\n"
            "\n"
            "   :param mod.submod.A name: blah\n")
    doctree = build(text)
    xrefs = list(doctree.traverse(addnodes.pending_xref))
    print("targets:", [x.get('reftarget') for x in xrefs])
    match = [x for x in xrefs if x.get('reftarget') == 'mod.submod.A']
    if not match:
        print("FAIL: qualified name not kept verbatim as reftarget")
        sys.exit(1)
    x = match[0]
    print("refdomain=%r reftype=%r refspecific=%r"
          % (x.get('refdomain'), x.get('reftype'), x.get('refspecific')))
    ok = (x.get('refdomain') == 'py' and x.get('reftype') == 'class'
          and x.get('refspecific') is True)
    if not ok:
        print("FAIL: domain/reftype/refspecific not as required")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.2 & 3.3: prefix handling. '.'-prefixed target -> leading '.' stripped
from reftarget, full name shown. '~'-prefixed target -> stripped from reftarget
AND only final dotted component is the visible link text."""
import os, sys, tempfile

def build(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    return restructuredtext.parse(app, text)

def main():
    from sphinx import addnodes
    text = (".. py:function:: foo(a, b)\n"
            "\n"
            "   :param .mod.sub.A a: x\n"
            "   :param ~mod.sub.B b: y\n")
    doctree = build(text)
    xrefs = list(doctree.traverse(addnodes.pending_xref))
    info = {x.get('reftarget'): x.astext() for x in xrefs}
    print("reftarget -> visible text:", info)
    ok = True
    # dot-prefixed: reftarget stripped to 'mod.sub.A', text full 'mod.sub.A'
    if 'mod.sub.A' not in info:
        print("FAIL: dot prefix not stripped to mod.sub.A"); ok = False
    elif info['mod.sub.A'] != 'mod.sub.A':
        print("FAIL: dot prefix text wrong:", info['mod.sub.A']); ok = False
    # tilde-prefixed: reftarget 'mod.sub.B', visible text only 'B'
    if 'mod.sub.B' not in info:
        print("FAIL: tilde prefix not stripped to mod.sub.B"); ok = False
    elif info['mod.sub.B'] != 'B':
        print("FAIL: tilde visible text should be 'B':", info['mod.sub.B']); ok = False
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.4: a type target that is the literal None is built as a generic
object reference (reftype 'obj'), not a class reference. Uses :rtype: None."""
import os, sys, tempfile

def build(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    return restructuredtext.parse(app, text)

def main():
    from sphinx import addnodes
    text = (".. py:function:: foo()\n"
            "\n"
            "   :rtype: None\n")
    doctree = build(text)
    xrefs = [x for x in doctree.traverse(addnodes.pending_xref)
             if x.get('reftarget') == 'None']
    print("found %d None xref" % len(xrefs))
    if not xrefs:
        print("FAIL: no None xref"); sys.exit(1)
    x = xrefs[0]
    print("reftype=%r refdomain=%r" % (x.get('reftype'), x.get('refdomain')))
    ok = x.get('reftype') == 'obj'
    if not ok:
        print("FAIL: None should be built as obj reference, not class")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.7 (regression): overall field rendering intact. :param str name:
renders name (literal_strong), parenthesized type as xref, and description
text together in the parameters list; and :param age: + :type age: combine."""
import os, sys, tempfile

def build(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    return restructuredtext.parse(app, text)

def main():
    from docutils import nodes
    from sphinx import addnodes
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param str name: blah blah\n"
            "   :param age: blah blah\n"
            "   :type age: int\n")
    doctree = build(text)
    # Expect a parameters field with a bullet list of 2 list_items.
    items = list(doctree.traverse(nodes.list_item))
    print("list_items:", len(items))
    full = doctree.astext()
    ok = True
    if len(items) < 2:
        print("FAIL: expected >=2 parameter list items"); ok = False
    # each item paragraph must contain the strong name, the type xref, desc.
    def item_ok(li, name, typ):
        para = li[0]
        strongs = [n.astext() for n in para.traverse(addnodes.literal_strong)]
        xr = [x.get('reftarget') for x in para.traverse(addnodes.pending_xref)]
        txt = para.astext()
        print("  item name=%r strong=%s xref=%s text=%r" % (name, strongs, xr, txt))
        return (name in strongs and typ in xr and 'blah blah' in txt)
    if len(items) >= 2:
        if not item_ok(items[0], 'name', 'str'):
            print("FAIL: name/str item malformed"); ok = False
        if not item_ok(items[1], 'age', 'int'):
            print("FAIL: age/int item malformed"); ok = False
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 1.1/1.2/1.5 + Req 2: an info-field type xref built
inside a module+class carries py:module and py:class of the surrounding scope.
Must HOLD patched, FAIL at base."""
import os, sys, tempfile

def build():
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param str name: blah blah\n"
            "   :param age: blah blah\n"
            "   :type age: int\n")
    return restructuredtext.parse(app, text)

def main():
    from sphinx import addnodes
    doctree = build()
    xrefs = list(doctree.traverse(addnodes.pending_xref))
    print("found %d pending_xref" % len(xrefs))
    targets = {}
    for x in xrefs:
        targets[x.get('reftarget')] = x
    print("targets:", sorted(targets))
    ok = True
    for tname in ("str", "int"):
        if tname not in targets:
            print("MISSING xref for", tname); ok = False; continue
        x = targets[tname]
        m = x.get('py:module'); c = x.get('py:class')
        print("%s -> py:module=%r py:class=%r reftype=%r refdomain=%r"
              % (tname, m, c, x.get('reftype'), x.get('refdomain')))
        if m != "example" or c != "Class":
            print("  FAIL scope not recorded for", tname); ok = False
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Prepatch bug re-encoded as an attack: `True`.

Instance: give info-field type cross-references (:param <type>, :type, :rtype) the same namespace context (py:module + py:class) an explicit role node carries, so unqualified type names resolve within the enclosing scope. Gold patch: python.py make_xref records result['py:module']/['py:class'] from env.ref_context; docfields.py Field.transform passes env=... into make_xrefs.

Probes (all standalone; parse rST via sphinx.testing.restructuredtext, inspect pending_xref nodes):
- probe_1 (POSITIVE CONTROL) — Req 1.1/1.2/1.5 + Req 2: inside module 'example' + class 'Class', both :param str name: and :param age:/:type age: int produce xrefs carrying py:module='example', py:class='Class'. HOLDS patched (exit0); VIOLATED at base (py:module=None, py:class=None) — discriminates.
- probe_2 — Req 1.3/1.4: function with no module/class in scope -> py:module and py:class are None (not fabricated). HOLDS patched.
- probe_3 — Req 3.1/3.5/3.6: fully-qualified 'mod.submod.A' kept verbatim as reftarget; node is py-domain, reftype='class', refspecific=True. HOLDS patched.
- probe_4 — Req 3.2/3.3: '.mod.sub.A' -> reftarget 'mod.sub.A' with full visible text; '~mod.sub.B' -> reftarget 'mod.sub.B' with visible text only 'B'. HOLDS patched.
- probe_5 — Req 3.4: :rtype: None built as reftype='obj' (generic object), not class. HOLDS patched.
- probe_6 — Req 3.7 regression: parameters list renders name (literal_strong), parenthesized type xref, and description together for both the :param str name: form and the :param age: + :type age: form. HOLDS patched.

Candidate wrong-fixes, both REJECTED by probe_1 (suite discriminates partial fixes):
- weak_docfields_only: only passes env into make_xrefs, never records scope in make_xref -> py:module=None, py:class=None. REJECTED.
- weak_module_only: records py:module but omits py:class -> py:class=None for str/int. REJECTED (this is exactly the Req 1.2/1.5 leg a weak reading would drop).

No requirements-conforming candidate found that evades the suite; no TOO-WEAK finding. All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched. Verdict SOUND.

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
"""Positive control. Req 1.1/1.2/1.5 + Req 2: an info-field type xref built
inside a module+class carries py:module and py:class of the surrounding scope.
Must HOLD patched, FAIL at base."""
import os, sys, tempfile

def build():
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as spath
    from sphinx.testing import restructuredtext
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'conf.py'), 'w').write("project='t'\nextensions=[]\n")
    open(os.path.join(tmp, 'index.rst'), 'w').write("hi\n")
    app = SphinxTestApp(srcdir=spath(tmp))
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param str name: blah blah\n"
            "   :param age: blah blah\n"
            "   :type age: int\n")
    return restructuredtext.parse(app, text)

def main():
    from sphinx import addnodes
    doctree = build()
    xrefs = list(doctree.traverse(addnodes.pending_xref))
    print("found %d pending_xref" % len(xrefs))
    targets = {}
    for x in xrefs:
        targets[x.get('reftarget')] = x
    print("targets:", sorted(targets))
    ok = True
    for tname in ("str", "int"):
        if tname not in targets:
            print("MISSING xref for", tname); ok = False; continue
        x = targets[tname]
        m = x.get('py:module'); c = x.get('py:class')
        print("%s -> py:module=%r py:class=%r reftype=%r refdomain=%r"
              % (tname, m, c, x.get('reftype'), x.get('refdomain')))
        if m != "example" or c != "Class":
            print("  FAIL scope not recorded for", tname); ok = False
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

Prepatch bug re-encoded as an attack: `True`.

Instance: give info-field type cross-references (:param <type>, :type, :rtype) the same namespace context (py:module + py:class) an explicit role node carries, so unqualified type names resolve within the enclosing scope. Gold patch: python.py make_xref records result['py:module']/['py:class'] from env.ref_context; docfields.py Field.transform passes env=... into make_xrefs.

Probes (all standalone; parse rST via sphinx.testing.restructuredtext, inspect pending_xref nodes):
- probe_1 (POSITIVE CONTROL) — Req 1.1/1.2/1.5 + Req 2: inside module 'example' + class 'Class', both :param str name: and :param age:/:type age: int produce xrefs carrying py:module='example', py:class='Class'. HOLDS patched (exit0); VIOLATED at base (py:module=None, py:class=None) — discriminates.
- probe_2 — Req 1.3/1.4: function with no module/class in scope -> py:module and py:class are None (not fabricated). HOLDS patched.
- probe_3 — Req 3.1/3.5/3.6: fully-qualified 'mod.submod.A' kept verbatim as reftarget; node is py-domain, reftype='class', refspecific=True. HOLDS patched.
- probe_4 — Req 3.2/3.3: '.mod.sub.A' -> reftarget 'mod.sub.A' with full visible text; '~mod.sub.B' -> reftarget 'mod.sub.B' with visible text only 'B'. HOLDS patched.
- probe_5 — Req 3.4: :rtype: None built as reftype='obj' (generic object), not class. HOLDS patched.
- probe_6 — Req 3.7 regression: parameters list renders name (literal_strong), parenthesized type xref, and description together for both the :param str name: form and the :param age: + :type age: form. HOLDS patched.

Candidate wrong-fixes, both REJECTED by probe_1 (suite discriminates partial fixes):
- weak_docfields_only: only passes env into make_xrefs, never records scope in make_xref -> py:module=None, py:class=None. REJECTED.
- weak_module_only: records py:module but omits py:class -> py:class=None for str/int. REJECTED (this is exactly the Req 1.2/1.5 leg a weak reading would drop).

No requirements-conforming candidate found that evades the suite; no TOO-WEAK finding. All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is exactly two hunks: (1) sphinx/domains/python.py PyXrefMixin.make_xref adds the py:module/py:class carry from env.ref_context; (2) sphinx/util/docfields.py Field.transform threads env into the make_xref call. Requirements pin precisely the changed observable behavior (namespace context now recorded on the info-field type node + env made reachable at the link site) and correctly bucket the pre-existing prefix/None/refspecific behavior under a 'preserve' requirement. Modeling boundary is the changed behavior, not a narrow slice. Probes run in the instance image on the gold-patched tree confirm all cited code shapes. No requirement mandates absent behavior, forbids present behavior, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to the genuine public API (PyXrefMixin.make_xref, Field.transform, sphinx/domains/python.py, sphinx/util/docfields.py) and the pre-existing domain context keys py:module / py:class — all legitimate. None of the hidden-test specifics leak: no test function name (test_info_field_list), no path (tests/test_domain_py.py), no quoted test/gold code, and none of the test literals (module 'example', class 'Class', types 'str'/'int', param 'age', the assert_node doctree structure). The class-in-module scenario in Req 1.5 and the two param-field forms describe the gold edit's behavior (recording both py:module and py:class from ref_context) rather than reproducing the test — a faithful behavioral translation, which is the intended purpose. The prefix (./~) and None handling in Req 3 describe the visible make_xref code, not test parametrization. No semantic gold-reconstruction leak found.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
