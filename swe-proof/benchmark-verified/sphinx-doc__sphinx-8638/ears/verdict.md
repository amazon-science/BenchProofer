# P2 adversarial audit — sphinx-doc__sphinx-8638

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
#!/usr/bin/env python
"""Probe R1.1 / R1.3 (positive control): a :var: field's NAME is rendered as a
plain literal_strong text node and is NOT wrapped in a pending_xref.

Fails at base (name auto-linked via rolename='obj' -> pending_xref), holds
patched (rolename removed -> plain literal_strong)."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    with open(os.path.join(srcdir, "conf.py"), "w") as f:
        f.write("")
    with open(os.path.join(srcdir, "index.rst"), "w") as f:
        f.write("")
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        # older/newer signature: path-like required
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    text = (".. py:class:: Class\n"
            "\n"
            "   :var int attr: blah blah\n")
    doctree = render(text)

    # Locate the field_body paragraph for the Variables field.
    strongs = list(doctree.findall(addnodes.literal_strong))
    # find the literal_strong holding "attr"
    attr_strongs = [n for n in strongs if n.astext() == "attr"]
    print("literal_strong 'attr' count:", len(attr_strongs))
    if not attr_strongs:
        print("FAIL: no literal_strong node with text 'attr' found")
        sys.exit(1)

    node = attr_strongs[0]
    # its parent must be a paragraph (field_body content), NOT inside a pending_xref
    parent = node.parent
    print("parent of attr literal_strong:", type(parent).__name__)

    # Ensure the attr name is not wrapped in a pending_xref anywhere up the chain
    anc = node
    while anc is not None:
        if isinstance(anc, addnodes.pending_xref):
            print("FAIL: 'attr' literal_strong is inside a pending_xref (auto-linked)")
            sys.exit(1)
        anc = anc.parent

    # Also: there must be NO pending_xref whose text is 'attr' anywhere.
    for xr in doctree.findall(addnodes.pending_xref):
        if xr.astext() == "attr":
            print("FAIL: found a pending_xref with text 'attr'")
            sys.exit(1)

    print("PASS: variable name rendered as plain literal_strong, no pending_xref")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
"""Probe R2.1 / R2.3 / R3.3(vartype): the TYPE annotation of a documented
variable stays a pending_xref to a class-role object (reftype=class,
reftarget=int), wrapping literal_emphasis holding 'int'. Also confirms name+type
coexist: name plain, type xref, in the same rendered item."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    open(os.path.join(srcdir, "conf.py"), "w").close()
    open(os.path.join(srcdir, "index.rst"), "w").close()
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    text = (".. py:class:: Class\n"
            "\n"
            "   :var int attr: blah blah\n")
    doctree = render(text)

    # find pending_xref that targets the type 'int'
    type_xrefs = []
    for xr in doctree.findall(addnodes.pending_xref):
        if xr.astext() == "int":
            type_xrefs.append(xr)
    print("pending_xref 'int' count:", len(type_xrefs))
    if not type_xrefs:
        print("FAIL: no pending_xref for the type 'int'")
        sys.exit(1)

    xr = type_xrefs[0]
    reftype = xr.get("reftype")
    reftarget = xr.get("reftarget")
    refdomain = xr.get("refdomain")
    print("reftype=%r reftarget=%r refdomain=%r" % (reftype, reftarget, refdomain))
    if reftype != "class":
        print("FAIL: type xref reftype is not 'class'")
        sys.exit(1)
    if reftarget != "int":
        print("FAIL: type xref reftarget is not 'int'")
        sys.exit(1)
    if refdomain != "py":
        print("FAIL: type xref refdomain is not 'py'")
        sys.exit(1)

    # inner node must be literal_emphasis holding 'int'
    emph = list(xr.findall(addnodes.literal_emphasis))
    print("inner literal_emphasis count:", len(emph), "text:",
          emph[0].astext() if emph else None)
    if not emph or emph[0].astext() != "int":
        print("FAIL: type xref does not wrap literal_emphasis 'int'")
        sys.exit(1)

    # coexistence: name still plain literal_strong 'attr'
    attr = [n for n in doctree.findall(addnodes.literal_strong) if n.astext() == "attr"]
    if not attr:
        print("FAIL: variable name literal_strong 'attr' missing")
        sys.exit(1)

    print("PASS: type stays class xref wrapping literal_emphasis; name coexists plain")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
"""Probe R2.2 / R3.4: the rendered field_body paragraph sequence for
:var int attr: blah blah is EXACTLY the expected structure with unchanged
punctuation/separators:
    [literal_strong 'attr', ' (', pending_xref>literal_emphasis 'int', ')',
     ' -- ', 'blah blah'].
This mirrors the hidden test's assert_node and pins ordering/labels/text."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    open(os.path.join(srcdir, "conf.py"), "w").close()
    open(os.path.join(srcdir, "index.rst"), "w").close()
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    text = (".. py:class:: Class\n"
            "\n"
            "   :var int attr: blah blah\n")
    doctree = render(text)

    # Field label must be "Variables"
    fnames = [n.astext() for n in doctree.findall(nodes.field_name)]
    print("field_name(s):", fnames)
    if "Variables" not in fnames:
        print("FAIL: 'Variables' field label missing")
        sys.exit(1)

    # Find the field_body paragraph
    para = None
    for fb in doctree.findall(nodes.field_body):
        for p in fb.findall(nodes.paragraph):
            para = p
            break
        if para is not None:
            break
    if para is None:
        print("FAIL: no field_body paragraph")
        sys.exit(1)

    children = list(para.children)
    print("num children:", len(children))
    for i, c in enumerate(children):
        print("  [%d] %s = %r" % (i, type(c).__name__, c.astext()))

    if len(children) != 6:
        print("FAIL: expected 6 children in the rendered item")
        sys.exit(1)

    c = children
    ok = (
        isinstance(c[0], addnodes.literal_strong) and c[0].astext() == "attr" and
        isinstance(c[1], nodes.Text) and c[1].astext() == " (" and
        isinstance(c[2], addnodes.pending_xref) and c[2].astext() == "int" and
        isinstance(c[3], nodes.Text) and c[3].astext() == ")" and
        isinstance(c[4], nodes.Text) and c[4].astext() == " -- " and
        isinstance(c[5], nodes.Text) and c[5].astext() == "blah blah"
    )
    if not ok:
        print("FAIL: rendered item structure/punctuation does not match expected")
        sys.exit(1)

    print("PASS: exact rendered item structure with unchanged punctuation/separators")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
"""Probe R3.1 / R3.3(paramtype): parameter info fields keep their configured
argument-role rendering. In the Python domain the parameter field group has no
'obj'-style rolename, so a parameter NAME renders as a plain literal_strong
(exactly as before the change), and its type renders as a class cross-reference.
This 'SHALL keep' probe pins the parameter rendered item to its pre-change
structure so a fix that leaks into the parameter group is caught."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    open(os.path.join(srcdir, "conf.py"), "w").close()
    open(os.path.join(srcdir, "index.rst"), "w").close()
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    text = (".. py:function:: f(name)\n"
            "\n"
            "   :param str name: the name\n")
    doctree = render(text)

    # Field label
    fnames = [n.astext() for n in doctree.findall(nodes.field_name)]
    print("field_name(s):", fnames)
    if "Parameters" not in fnames:
        print("FAIL: 'Parameters' field label missing")
        sys.exit(1)

    # Find the parameter field_body paragraph
    para = None
    for fb in doctree.findall(nodes.field_body):
        for p in fb.findall(nodes.paragraph):
            para = p
            break
        if para is not None:
            break
    if para is None:
        print("FAIL: no field_body paragraph for parameters")
        sys.exit(1)

    children = list(para.children)
    for i, c in enumerate(children):
        print("  [%d] %s = %r" % (i, type(c).__name__, c.astext()))

    # Expected pre-change structure (same as gold): name plain literal_strong,
    # ' (', class pending_xref 'str' wrapping literal_emphasis, ')', ' -- ',
    # 'the name'.
    if len(children) != 6:
        print("FAIL: expected 6 children in the parameter rendered item")
        sys.exit(1)
    c = children
    ok = (
        isinstance(c[0], addnodes.literal_strong) and c[0].astext() == "name" and
        isinstance(c[1], nodes.Text) and c[1].astext() == " (" and
        isinstance(c[2], addnodes.pending_xref) and c[2].astext() == "str" and
        c[2].get("reftype") == "class" and c[2].get("reftarget") == "str" and
        isinstance(c[3], nodes.Text) and c[3].astext() == ")" and
        isinstance(c[4], nodes.Text) and c[4].astext() == " -- " and
        isinstance(c[5], nodes.Text) and c[5].astext() == "the name"
    )
    if not ok:
        print("FAIL: parameter rendered item does not match pre-change structure")
        sys.exit(1)

    # The param name literal_strong must NOT be wrapped in a pending_xref.
    name_strong = [n for n in doctree.findall(addnodes.literal_strong)
                   if n.astext() == "name"][0]
    anc = name_strong
    while anc is not None:
        if isinstance(anc, addnodes.pending_xref):
            print("FAIL: param name unexpectedly inside pending_xref")
            sys.exit(1)
        anc = anc.parent

    print("PASS: parameter field renders name plain + type class-xref, as before")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
"""Probe R3.2: exception fields (:raises:) keep cross-referencing to the
'exc' role. A :raises TypeError: ... must render 'TypeError' as a pending_xref
with reftype='exc'. Regression 'SHALL keep' criterion."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    open(os.path.join(srcdir, "conf.py"), "w").close()
    open(os.path.join(srcdir, "index.rst"), "w").close()
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    text = (".. py:function:: f()\n"
            "\n"
            "   :raises TypeError: if wrong\n")
    doctree = render(text)

    exc_xrefs = [xr for xr in doctree.findall(addnodes.pending_xref)
                 if xr.astext() == "TypeError"]
    print("pending_xref 'TypeError' count:", len(exc_xrefs))
    for xr in exc_xrefs:
        print("  reftype=%r reftarget=%r refdomain=%r" %
              (xr.get("reftype"), xr.get("reftarget"), xr.get("refdomain")))
    exc_ok = [xr for xr in exc_xrefs if xr.get("reftype") == "exc"]
    if not exc_ok:
        print("FAIL: :raises: TypeError is not an 'exc' cross-reference")
        sys.exit(1)

    # Label 'Raises' present
    fnames = [n.astext() for n in doctree.findall(nodes.field_name)]
    print("field_name(s):", fnames)
    if "Raises" not in fnames:
        print("FAIL: 'Raises' field label missing")
        sys.exit(1)

    print("PASS: exception field still cross-references the 'exc' role")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
"""Probe R4.1: even when another object with the SAME name exists in the
project, a documented variable's name is rendered plain and NOT linked to it.
We document a class 'attr' (an object) and, in the same doc, a class 'Class'
with :var int attr:. The variable name 'attr' must still be a plain
literal_strong not wrapped in a pending_xref."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    open(os.path.join(srcdir, "conf.py"), "w").close()
    open(os.path.join(srcdir, "index.rst"), "w").close()
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    # Define an object named 'attr' AND a variable named 'attr'.
    text = (".. py:function:: attr()\n"
            "\n"
            "   an unrelated object named attr\n"
            "\n"
            ".. py:class:: Class\n"
            "\n"
            "   :var int attr: blah blah\n")
    doctree = render(text)

    # Find the variable-name literal_strong (text 'attr') and verify none of
    # them is inside a pending_xref.
    attr_strongs = [n for n in doctree.findall(addnodes.literal_strong)
                    if n.astext() == "attr"]
    print("literal_strong 'attr' count:", len(attr_strongs))
    if not attr_strongs:
        print("FAIL: variable name literal_strong 'attr' missing")
        sys.exit(1)

    for n in attr_strongs:
        anc = n
        while anc is not None:
            if isinstance(anc, addnodes.pending_xref):
                print("FAIL: variable name 'attr' linked despite same-named object")
                sys.exit(1)
            anc = anc.parent

    # And no pending_xref references target 'attr'
    for xr in doctree.findall(addnodes.pending_xref):
        if xr.get("reftarget") == "attr":
            print("FAIL: a pending_xref targets 'attr'")
            sys.exit(1)

    print("PASS: variable name stays plain even with a same-named object present")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
"""Probe R1.1 / R1.3 (positive control): a :var: field's NAME is rendered as a
plain literal_strong text node and is NOT wrapped in a pending_xref.

Fails at base (name auto-linked via rolename='obj' -> pending_xref), holds
patched (rolename removed -> plain literal_strong)."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    with open(os.path.join(srcdir, "conf.py"), "w") as f:
        f.write("")
    with open(os.path.join(srcdir, "index.rst"), "w") as f:
        f.write("")
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        # older/newer signature: path-like required
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    text = (".. py:class:: Class\n"
            "\n"
            "   :var int attr: blah blah\n")
    doctree = render(text)

    # Locate the field_body paragraph for the Variables field.
    strongs = list(doctree.findall(addnodes.literal_strong))
    # find the literal_strong holding "attr"
    attr_strongs = [n for n in strongs if n.astext() == "attr"]
    print("literal_strong 'attr' count:", len(attr_strongs))
    if not attr_strongs:
        print("FAIL: no literal_strong node with text 'attr' found")
        sys.exit(1)

    node = attr_strongs[0]
    # its parent must be a paragraph (field_body content), NOT inside a pending_xref
    parent = node.parent
    print("parent of attr literal_strong:", type(parent).__name__)

    # Ensure the attr name is not wrapped in a pending_xref anywhere up the chain
    anc = node
    while anc is not None:
        if isinstance(anc, addnodes.pending_xref):
            print("FAIL: 'attr' literal_strong is inside a pending_xref (auto-linked)")
            sys.exit(1)
        anc = anc.parent

    # Also: there must be NO pending_xref whose text is 'attr' anywhere.
    for xr in doctree.findall(addnodes.pending_xref):
        if xr.astext() == "attr":
            print("FAIL: found a pending_xref with text 'attr'")
            sys.exit(1)

    print("PASS: variable name rendered as plain literal_strong, no pending_xref")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8638. Gold fix removes rolename='obj' from the PyTypedField('variable', ...) entry in PyObject.doc_field_types so :var/:ivar/:cvar names render as plain literal_strong rather than a pending_xref. Six standalone probes render minimal RST via sphinx.testing.restructuredtext.parse inside the instance image and inspect the doctree.

Probe results (patched / base):
- probe_1 (R1.1,R1.3; POSITIVE CONTROL): var name 'attr' is a plain literal_strong not inside any pending_xref, and no pending_xref has text 'attr'. HOLDS patched; FAILS at base (base wraps 'attr' in a pending_xref -> discriminating power confirmed).
- probe_2 (R2.1,R2.3,R3.3): type 'int' stays pending_xref reftype=class reftarget=int refdomain=py wrapping literal_emphasis 'int'; name coexists plain. HOLDS patched.
- probe_3 (R2.2,R3.4): exact rendered item = [literal_strong 'attr', ' (', pending_xref 'int', ')', ' -- ', 'blah blah'] with 'Variables' label. HOLDS patched.
- probe_4 (R3.1,R3.3): parameter field regression - :param str name: renders name plain literal_strong (no xref, as before) + type 'str' class xref; exact 6-child structure. HOLDS patched. (Initial version wrongly assumed param names were xref'd; corrected to the true pre-change structure: param group also has no rolename, so plain name is the unchanged baseline.)
- probe_5 (R3.2): :raises TypeError: stays pending_xref reftype=exc; 'Raises' label present. HOLDS patched.
- probe_6 (R4.1): even with an unrelated object also named 'attr' documented in the same doc, the var name stays plain and no pending_xref targets 'attr'. HOLDS patched.

Candidate wrong patches (both REQUIRED floor met - both REJECTED by the suite, demonstrating discrimination):
- weak_class.diff: changes rolename='obj' -> rolename='class' (still cross-references the name, wrong reading of R1). REJECTED: probe_1, probe_3, probe_6 all fail (name becomes a pending_xref).
- weak_notype.diff: removes name rolename correctly BUT also changes typerolename 'class' -> 'obj' (over-broad edit violating R2/R3.3). REJECTED: probe_2 fails (type xref reftype becomes 'obj' not 'class'); probe_1 still passes, so the suite catches the type regression the name-only probe misses.

All 6 probes hold on the gold-patched tree; positive control fails at base; no probe-conforming alternative patch was found. Requirements are faithful and adequately tight.

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
#!/usr/bin/env python
"""Probe R1.1 / R1.3 (positive control): a :var: field's NAME is rendered as a
plain literal_strong text node and is NOT wrapped in a pending_xref.

Fails at base (name auto-linked via rolename='obj' -> pending_xref), holds
patched (rolename removed -> plain literal_strong)."""
import sys
import tempfile
import os


def render(text):
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.restructuredtext import parse
    srcdir = tempfile.mkdtemp()
    with open(os.path.join(srcdir, "conf.py"), "w") as f:
        f.write("")
    with open(os.path.join(srcdir, "index.rst"), "w") as f:
        f.write("")
    try:
        app = SphinxTestApp(srcdir=srcdir)
    except TypeError:
        # older/newer signature: path-like required
        from sphinx.testing.path import path as spath
        app = SphinxTestApp(srcdir=spath(srcdir))
    try:
        return parse(app, text)
    finally:
        app.cleanup()


def main():
    from docutils import nodes
    from sphinx import addnodes

    text = (".. py:class:: Class\n"
            "\n"
            "   :var int attr: blah blah\n")
    doctree = render(text)

    # Locate the field_body paragraph for the Variables field.
    strongs = list(doctree.findall(addnodes.literal_strong))
    # find the literal_strong holding "attr"
    attr_strongs = [n for n in strongs if n.astext() == "attr"]
    print("literal_strong 'attr' count:", len(attr_strongs))
    if not attr_strongs:
        print("FAIL: no literal_strong node with text 'attr' found")
        sys.exit(1)

    node = attr_strongs[0]
    # its parent must be a paragraph (field_body content), NOT inside a pending_xref
    parent = node.parent
    print("parent of attr literal_strong:", type(parent).__name__)

    # Ensure the attr name is not wrapped in a pending_xref anywhere up the chain
    anc = node
    while anc is not None:
        if isinstance(anc, addnodes.pending_xref):
            print("FAIL: 'attr' literal_strong is inside a pending_xref (auto-linked)")
            sys.exit(1)
        anc = anc.parent

    # Also: there must be NO pending_xref whose text is 'attr' anywhere.
    for xr in doctree.findall(addnodes.pending_xref):
        if xr.astext() == "attr":
            print("FAIL: found a pending_xref with text 'attr'")
            sys.exit(1)

    print("PASS: variable name rendered as plain literal_strong, no pending_xref")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8638. Gold fix removes rolename='obj' from the PyTypedField('variable', ...) entry in PyObject.doc_field_types so :var/:ivar/:cvar names render as plain literal_strong rather than a pending_xref. Six standalone probes render minimal RST via sphinx.testing.restructuredtext.parse inside the instance image and inspect the doctree.

Probe results (patched / base):
- probe_1 (R1.1,R1.3; POSITIVE CONTROL): var name 'attr' is a plain literal_strong not inside any pending_xref, and no pending_xref has text 'attr'. HOLDS patched; FAILS at base (base wraps 'attr' in a pending_xref -> discriminating power confirmed).
- probe_2 (R2.1,R2.3,R3.3): type 'int' stays pending_xref reftype=class reftarget=int refdomain=py wrapping literal_emphasis 'int'; name coexists plain. HOLDS patched.
- probe_3 (R2.2,R3.4): exact rendered item = [literal_strong 'attr', ' (', pending_xref 'int', ')', ' -- ', 'blah blah'] with 'Variables' label. HOLDS patched.
- probe_4 (R3.1,R3.3): parameter field regression - :param str name: renders name plain literal_strong (no xref, as before) + type 'str' class xref; exact 6-child structure. HOLDS patched. (Initial version wrongly assumed param names were xref'd; corrected to the true pre-change structure: param group also has no rolename, so plain name is the unchanged baseline.)
- probe_5 (R3.2): :raises TypeError: stays pending_xref reftype=exc; 'Raises' label present. HOLDS patched.
- probe_6 (R4.1): even with an unrelated object also named 'attr' documented in the same doc, the var name stays plain and no pending_xref targets 'attr'. HOLDS patched.

Candidate wrong patches (both REQUIRED floor met - both REJECTED by the suite, demonstrating discrimination):
- weak_class.diff: changes rolename='obj' -> rolename='class' (still cross-references the name, wrong reading of R1). REJECTED: probe_1, probe_3, probe_6 all fail (name becomes a pending_xref).
- weak_notype.diff: removes name rolename correctly BUT also changes typerolename 'class' -> 'obj' (over-broad edit violating R2/R3.3). REJECTED: probe_2 fails (type xref reftype becomes 'obj' not 'class'); probe_1 still passes, so the suite catches the type regression the name-only probe misses.

All 6 probes hold on the gold-patched tree; positive control fails at base; no probe-conforming alternative patch was found. Requirements are faithful and adequately tight.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: PyTypedField('variable', ...) drops rolename='obj'. Behavioral probe on patched tree: NAME node type=strong (literal_strong), pending_xref=False; TYPE node=pending_xref reftype='class'; keeps typerolename='class'. Requirements 1-4 all match. Requirement 1's claim of 'strong-inline text node' is accurate: literal_strong subclasses nodes.strong, and make_field passes addnodes.literal_strong as innernode for the name. The scoping claims (Requirement 3) are consistent with the one-line diff.

Counterexample / evidence:

```
N/A — no requirement diverges from patched behavior. Confirmed base (rolename='obj', auto-links) vs patched (rolename=None, plain strong node) so the requirements correctly capture the changed observable behavior and pin it biconditionally at the right boundary (the var/ivar/cvar field group name-rendering), not a narrow slice or invented behavior.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a one-line change: removing rolename='obj' from the PyTypedField('variable', ...) entry in sphinx/domains/python.py so :var:/:ivar:/:cvar: names stop auto-cross-referencing. Hidden test test_info_field_list_var renders ':var int attr:' and asserts the node tree: literal_strong 'attr', ' (', pending_xref/literal_emphasis 'int', ')', ' -- ', 'blah blah', with reftype='class' reftarget='int'.

The requirements.md legitimately (a) localizes the change to PyObject.doc_field_types in python.py and the docfields.py helpers (naming modules is permitted), and (b) translates the behavior: variable name -> plain strong-inline text with no pending_xref; type -> class-role cross-reference wrapping emphasized inline text; other fields (param/raises/type) unchanged. These node-type names (literal_strong, pending_xref, emphasized/class-role) are pre-existing Sphinx docutils concepts describing observable rendering, not fix-invented identifiers.

No leakage found: no test name/path/id, no quoted test or gold code, no parametrization-mirroring enumeration (single F2P test, no parametrization). The 'limit' example in the intro comes verbatim from the PUBLIC problem_statement. The test's literals ('int', 'attr', 'blah blah') never appear in the document. Req 2.1's 'single simple name' phrasing describes general TypedField behavior, not the test's specific input. This is exactly the intended behavioral translation, not transmission of the hidden test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
