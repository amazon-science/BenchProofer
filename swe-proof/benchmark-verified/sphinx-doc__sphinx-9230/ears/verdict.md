# P2 adversarial audit — sphinx-doc__sphinx-9230

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_poscontrol.py`, `probe_2_sametype.py`, `probe_3_xrefs.py`, `probe_4_singletoken.py`, `probe_5_notype.py`, `probe_6_septype.py`, `probe_7_whitespace.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_poscontrol.py` → holds on the patched tree (good)

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 1.1/1.2/1.4 + positive control: multi-word type must split at LAST token.
# name == opc_meta, type == "dict(str, str)" reconstructed intact.
if __name__ == "__main__":
    app = build_app()
    dt, paras = render(app, ":param dict(str, str) opc_meta: blah blah")
    d = find_param(paras, "opc_meta")
    print("observed:", d)
    ok = (d is not None and d["name"] == "opc_meta" and d["has_type"]
          and d["type_text"] == "dict(str, str)")
    if not ok:
        print("FAIL: expected name=opc_meta type='dict(str, str)'"); sys.exit(1)
    print("HOLD: name/type split correctly for multi-word type"); sys.exit(0)
```

Attack 2 — `probe_2_sametype.py` → holds on the patched tree (good)

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 1.3: type from inline "<type> <name>" is cross-referenced/rendered
# IDENTICALLY to the same type supplied via a separate :type: field.
if __name__ == "__main__":
    app = build_app()
    _, pin = render(app, ":param Dict[str, str] params: blah blah")
    inline = find_param(pin, "params")
    _, psep = render(app, ":param params: blah blah",
                          ":type params: Dict[str, str]")
    sep = find_param(psep, "params")
    print("inline:", inline)
    print("separate:", sep)
    if inline is None or sep is None:
        print("FAIL: param not found"); sys.exit(1)
    if inline["type_children"] != sep["type_children"]:
        print("FAIL: inline type rendering != separate-field rendering"); sys.exit(1)
    if inline["xref_targets"] != sep["xref_targets"]:
        print("FAIL: xref targets differ"); sys.exit(1)
    print("HOLD: inline type identical to separate :type: field"); sys.exit(0)
```

Attack 3 — `probe_3_xrefs.py` → holds on the patched tree (good)

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 1.3/1.4: each component of a bracketed type is individually
# cross-referenced (pending_xref for Dict, str, str) and brackets/commas kept.
if __name__ == "__main__":
    app = build_app()
    _, paras = render(app, ":param Dict[str, str] params: blah blah")
    d = find_param(paras, "params")
    print("observed:", d)
    if d is None or not d["has_type"]:
        print("FAIL: no type"); sys.exit(1)
    if d["name"] != "params":
        print("FAIL: name wrong"); sys.exit(1)
    if d["type_text"] != "Dict[str, str]":
        print("FAIL: type_text != 'Dict[str, str]'"); sys.exit(1)
    if d["xref_targets"] != ["Dict", "str", "str"]:
        print("FAIL: xref targets != [Dict,str,str]:", d["xref_targets"]); sys.exit(1)
    print("HOLD: bracketed type components individually xref'd"); sys.exit(0)
```

Attack 4 — `probe_4_singletoken.py` → holds on the patched tree (good)

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 2.1 (regression): "int age" -> first token type, second token name.
if __name__ == "__main__":
    app = build_app()
    _, paras = render(app, ":param int age: blah blah")
    d = find_param(paras, "age")
    print("observed:", d)
    if d is None or not d["has_type"]:
        print("FAIL: no type"); sys.exit(1)
    if d["name"] != "age" or d["type_text"] != "int":
        print("FAIL: expected name=age type=int"); sys.exit(1)
    if d["xref_targets"] != ["int"]:
        print("FAIL: xref != [int]:", d["xref_targets"]); sys.exit(1)
    print("HOLD: single type/name split unchanged"); sys.exit(0)
```

Attack 5 — `probe_5_notype.py` → holds on the patched tree (good)

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 2.2 (regression): a lone token ":param items:" records NO type.
# We compare vs ":param age:"+":type age:int" only to confirm no type slot.
if __name__ == "__main__":
    app = build_app()
    _, paras = render(app, ":param foo: blah blah")
    d = find_param(paras, "foo")
    print("observed:", d)
    if d is None:
        print("FAIL: param foo missing"); sys.exit(1)
    if d["name"] != "foo":
        print("FAIL: name wrong:", d["name"]); sys.exit(1)
    if d["has_type"] or d["xref_targets"]:
        print("FAIL: unexpected type recorded for typeless param"); sys.exit(1)
    print("HOLD: lone-token param has no type"); sys.exit(0)
```

Attack 6 — `probe_6_septype.py` → holds on the patched tree (good)

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 2.3 (regression): type via separate :type: field associates + renders.
if __name__ == "__main__":
    app = build_app()
    _, paras = render(app, ":param age: blah blah", ":type age: int")
    d = find_param(paras, "age")
    print("observed:", d)
    if d is None or not d["has_type"]:
        print("FAIL: no type"); sys.exit(1)
    if d["name"] != "age" or d["type_text"] != "int":
        print("FAIL: expected name=age type=int"); sys.exit(1)
    if d["xref_targets"] != ["int"]:
        print("FAIL: xref != [int]"); sys.exit(1)
    print("HOLD: separate :type: field unchanged"); sys.exit(0)
```

Attack 7 — `probe_7_whitespace.py` → holds on the patched tree (good)

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 2.5 (regression): repeated interior whitespace between type and name
# collapses; name/type carry no spurious leading/trailing whitespace.
if __name__ == "__main__":
    app = build_app()
    _, paras = render(app, ":param int    age: blah blah")
    d = find_param(paras, "age")
    print("observed:", d)
    if d is None or not d["has_type"]:
        print("FAIL: no type"); sys.exit(1)
    if d["name"] != "age":
        print("FAIL: name has spurious ws:", repr(d["name"])); sys.exit(1)
    if d["type_text"] != "int":
        print("FAIL: type has spurious ws:", repr(d["type_text"])); sys.exit(1)
    print("HOLD: whitespace collapsed at boundaries"); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_poscontrol.py`

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 1.1/1.2/1.4 + positive control: multi-word type must split at LAST token.
# name == opc_meta, type == "dict(str, str)" reconstructed intact.
if __name__ == "__main__":
    app = build_app()
    dt, paras = render(app, ":param dict(str, str) opc_meta: blah blah")
    d = find_param(paras, "opc_meta")
    print("observed:", d)
    ok = (d is not None and d["name"] == "opc_meta" and d["has_type"]
          and d["type_text"] == "dict(str, str)")
    if not ok:
        print("FAIL: expected name=opc_meta type='dict(str, str)'"); sys.exit(1)
    print("HOLD: name/type split correctly for multi-word type"); sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9230: gold fix is one char, split(None,1)->rsplit(None,1) in DocFieldTransformer.transform, so ':param <type> <name>:' splits at the LAST whitespace, letting multi-word types (dict(str, str)) render intact.

Probes render real doctrees via sphinx.testing.restructuredtext.parse against a dummy-builder SphinxTestApp inside the instance image; each dissects the Parameters bullet paragraph (literal_strong name; type nodes between ' (' and closing ')'; pending_xref targets).

Results on the gold-PATCHED tree (all HOLD):
- probe_1_poscontrol (Req1.1/1.2/1.4): ':param dict(str, str) opc_meta:' -> name=opc_meta, type='dict(str, str)'. HOLD.
- probe_2_sametype (Req1.3): inline 'Dict[str, str] params' renders type nodes+xrefs IDENTICALLY to a separate ':type params: Dict[str, str]' field. HOLD.
- probe_3_xrefs (Req1.3/1.4): 'Dict[str, str]' -> xref targets [Dict,str,str], brackets/commas preserved. HOLD.
- probe_4_singletoken (Req2.1): ':param int age:' -> type=int name=age. HOLD.
- probe_5_notype (Req2.2): lone ':param foo:' records no type. HOLD.
- probe_6_septype (Req2.3): separate ':type age: int' associates+renders. HOLD.
- probe_7_whitespace (Req2.5): ':param int    age:' collapses interior whitespace, name/type unstripped-spurious-free. HOLD.

Positive control (probe_1) at BASE: VIOLATED (opc_meta param not found / mis-split) -> discriminates base vs patched. Probes 2,3 also fail at base; probes 4,5,6,7 hold at base (they are regression guards, as intended).

Wrong-fix candidates (both REJECTED by the suite; both apply at base_commit):
- weak_swap.diff: 'argname, argtype = fieldarg.rsplit(None,1)' (last token taken as the TYPE, reversed). Rejected by probes 1,2,3,4,7 (name/type swapped, e.g. type='opc_meta').
- weak_strip.diff: rsplit then argtype.replace(' ','') (fixes the split but mangles the type by collapsing internal whitespace -> 'dict(str,str)'). Rejected by probes 1,2,3 on Req1.2 whitespace-preservation (literal_emphasis ',' vs required ', ').

Conclusion: >=5 distinct probes all hold patched; positive control discriminates (prepatch reproduced); 2/2 requirement-plausible wrong fixes rejected -> the requirement suite has discriminating power and admits no wrong fix it accepts. SOUND. (Note: G-PANEL-3 separately flags leakage of the hidden-test fieldarg 'Dict[str, str] params' into the prose; that is a leakage concern, out of scope for G-EQ spec-fidelity, and does not affect faithfulness/strength which are sound.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_poscontrol.py`, `probe_2_sametype.py`, `probe_3_xrefs.py`, `probe_4_singletoken.py`, `probe_5_notype.py`, `probe_6_septype.py`, `probe_7_whitespace.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_poscontrol.py` → holds on the patched tree (good)

Attack 2 — `probe_2_sametype.py` → holds on the patched tree (good)

Attack 3 — `probe_3_xrefs.py` → holds on the patched tree (good)

Attack 4 — `probe_4_singletoken.py` → holds on the patched tree (good)

Attack 5 — `probe_5_notype.py` → holds on the patched tree (good)

Attack 6 — `probe_6_septype.py` → holds on the patched tree (good)

Attack 7 — `probe_7_whitespace.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_poscontrol.py`

```python
import sys, tempfile
from docutils import nodes
from sphinx import addnodes

def build_app():
    import warnings; warnings.simplefilter("ignore")
    from sphinx.testing.util import SphinxTestApp
    try:
        from sphinx.testing.path import path as spath
    except Exception:
        spath = None
    base = tempfile.mkdtemp(prefix="sbu_src_")
    srcdir = spath(base) if spath else __import__("pathlib").Path(base)
    (srcdir / "conf.py").write_text("extensions = []\n")
    (srcdir / "index.rst").write_text("t\n=\n")
    return SphinxTestApp(buildername="dummy", srcdir=srcdir)

def parse(app, text):
    from sphinx.testing import restructuredtext
    return restructuredtext.parse(app, text)

def render(app, *param_lines):
    """Parse a class with the given :param/:type lines; return list of the
    rendered Parameters bullet paragraphs (one per param)."""
    body = "".join("   " + l + "\n" for l in param_lines)
    text = ".. py:module:: example\n.. py:class:: Class\n\n" + body
    dt = parse(app, text)
    paras = [ls.parent for ls in dt.traverse(addnodes.literal_strong)]
    return dt, paras

def dissect(para):
    """Return dict: name, type_text (joined type-node text between ' (' and
    the closing ')'), has_type (bool), xref_targets (list), type_children
    (list of (classname, text))."""
    kids = list(para.children)
    name = kids[0].astext()
    open_i = close_i = None
    for i,ch in enumerate(kids):
        if isinstance(ch, nodes.Text) and ch.astext() == " (":
            open_i = i; break
    if open_i is not None:
        for i in range(len(kids)-1, open_i, -1):
            if isinstance(kids[i], nodes.Text) and kids[i].astext() == ")":
                close_i = i; break
    if open_i is None or close_i is None:
        return dict(name=name, type_text=None, has_type=False,
                    xref_targets=[], type_children=[])
    tnodes = kids[open_i+1:close_i]
    type_text = "".join(n.astext() for n in tnodes)
    xrefs = [n.astext() for n in para.traverse(addnodes.pending_xref)]
    tchildren = [(type(n).__name__, n.astext()) for n in tnodes]
    return dict(name=name, type_text=type_text, has_type=True,
                xref_targets=xrefs, type_children=tchildren)

def find_param(paras, name):
    for p in paras:
        if list(p.children) and p.children[0].astext() == name:
            return dissect(p)
    return None

# Req 1.1/1.2/1.4 + positive control: multi-word type must split at LAST token.
# name == opc_meta, type == "dict(str, str)" reconstructed intact.
if __name__ == "__main__":
    app = build_app()
    dt, paras = render(app, ":param dict(str, str) opc_meta: blah blah")
    d = find_param(paras, "opc_meta")
    print("observed:", d)
    ok = (d is not None and d["name"] == "opc_meta" and d["has_type"]
          and d["type_text"] == "dict(str, str)")
    if not ok:
        print("FAIL: expected name=opc_meta type='dict(str, str)'"); sys.exit(1)
    print("HOLD: name/type split correctly for multi-word type"); sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9230: gold fix is one char, split(None,1)->rsplit(None,1) in DocFieldTransformer.transform, so ':param <type> <name>:' splits at the LAST whitespace, letting multi-word types (dict(str, str)) render intact.

Probes render real doctrees via sphinx.testing.restructuredtext.parse against a dummy-builder SphinxTestApp inside the instance image; each dissects the Parameters bullet paragraph (literal_strong name; type nodes between ' (' and closing ')'; pending_xref targets).

Results on the gold-PATCHED tree (all HOLD):
- probe_1_poscontrol (Req1.1/1.2/1.4): ':param dict(str, str) opc_meta:' -> name=opc_meta, type='dict(str, str)'. HOLD.
- probe_2_sametype (Req1.3): inline 'Dict[str, str] params' renders type nodes+xrefs IDENTICALLY to a separate ':type params: Dict[str, str]' field. HOLD.
- probe_3_xrefs (Req1.3/1.4): 'Dict[str, str]' -> xref targets [Dict,str,str], brackets/commas preserved. HOLD.
- probe_4_singletoken (Req2.1): ':param int age:' -> type=int name=age. HOLD.
- probe_5_notype (Req2.2): lone ':param foo:' records no type. HOLD.
- probe_6_septype (Req2.3): separate ':type age: int' associates+renders. HOLD.
- probe_7_whitespace (Req2.5): ':param int    age:' collapses interior whitespace, name/type unstripped-spurious-free. HOLD.

Positive control (probe_1) at BASE: VIOLATED (opc_meta param not found / mis-split) -> discriminates base vs patched. Probes 2,3 also fail at base; probes 4,5,6,7 hold at base (they are regression guards, as intended).

Wrong-fix candidates (both REJECTED by the suite; both apply at base_commit):
- weak_swap.diff: 'argname, argtype = fieldarg.rsplit(None,1)' (last token taken as the TYPE, reversed). Rejected by probes 1,2,3,4,7 (name/type swapped, e.g. type='opc_meta').
- weak_strip.diff: rsplit then argtype.replace(' ','') (fixes the split but mangles the type by collapsing internal whitespace -> 'dict(str,str)'). Rejected by probes 1,2,3 on Req1.2 whitespace-preservation (literal_emphasis ',' vs required ', ').

Conclusion: >=5 distinct probes all hold patched; positive control discriminates (prepatch reproduced); 2/2 requirement-plausible wrong fixes rejected -> the requirement suite has discriminating power and admits no wrong fix it accepts. SOUND. (Note: G-PANEL-3 separately flags leakage of the hidden-test fieldarg 'Dict[str, str] params' into the prose; that is a leakage concern, out of scope for G-EQ spec-fidelity, and does not affect faithfulness/strength which are sound.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified via nl_attack probe on the gold-patched instance image: patched transform contains `fieldarg.rsplit(None, 1)` and not `split(None, 1)`. Base commit 567ff227 uses split(None,1) (confirmed from repo git). One probe assertion initially failed on a pure-leading-whitespace input `'   int   age  '` expecting (`int`,`age`) but rsplit gives (`   int`,`age`); this is a probe artifact, not an unfaithfulness: `fieldarg` is produced upstream via `field_name.astext().split(None,1)[1]`, which strips leading whitespace, so such an input never reaches the rsplit. R2.5 says whitespace is collapsed/stripped 'in the same manner as the prior single-token handling' — which is exactly true (both rely on whitespace-splitting semantics). Modeling boundary is correct: requirements pin the changed decomposition behavior, not one branch/helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to DocFieldTransformer.transform in sphinx/util/docfields.py (legitimate localization) and describes the split-at-last-whitespace behavior in prose. The only concrete example used (`:param dict(str, str) opc_meta:` and the garbled `str) opc_meta (dict(str,)` vs correct `opc_meta (dict(str, str))` rendering) is taken verbatim from the PUBLIC problem_statement. The hidden test's distinct case (`:param Dict[str, str] params:`), the test function name (test_info_field_list / tests/test_domain_py.py), the assert_node node-index paths, the pending_xref/literal_emphasis node structure, and the gold's fix-invented change (split->rsplit) are NOT present. `int age` is a generic single-token illustration, not the hidden test's data (age appears in the test only via separate :param/:type fields). No case enumeration mirroring the test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
