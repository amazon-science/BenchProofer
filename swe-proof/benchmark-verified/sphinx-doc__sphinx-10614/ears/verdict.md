# P2 adversarial audit — sphinx-doc__sphinx-10614

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
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 1.1 + 1.2 : a resolved destination URI (refuri) is recorded VERBATIM,
# no leading "../", and identically for SVG and raster.
# POSITIVE CONTROL: at base the SVG branch prepends "../", so this FAILS at base.
uri = "foo/bar.html#test.Foo"
child = xref(refuri=uri, reftitle="test.Foo")
svg = run_case([child], fmt="svg")
child2 = xref(refuri=uri, reftitle="test.Foo")
png = run_case([child2], fmt="png")
print("SVG urls:", svg)
print("PNG urls:", png)
ok = True
if svg.get("test.Foo") != uri:
    print("FAIL: SVG did not record refuri verbatim; got", svg.get("test.Foo")); ok = False
if png.get("test.Foo") != uri:
    print("FAIL: PNG did not record refuri verbatim; got", png.get("test.Foo")); ok = False
if svg != png:
    print("FAIL: SVG and PNG url maps differ"); ok = False
# explicit: no "../" prefix
for v in list(svg.values()) + list(png.values()):
    if v.startswith("../"):
        print("FAIL: url has forbidden '../' prefix:", v); ok = False
import sys
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 1.3 : absolute URL (contains "://") left unmodified for SVG (and PNG).
uri = "https://example.org/foo.html#subdir.other.Bob"
# external -> internal False, keyed by trailing component (Req 2.2)
c = xref(refuri=uri, reftitle="subdir.other.Bob", internal=False)
svg = run_case([c], fmt="svg")
print("SVG urls:", svg)
ok = True
vals = list(svg.values())
if uri not in vals:
    print("FAIL: absolute URI not recorded verbatim; got", vals); ok = False
for v in vals:
    if v.startswith("../"):
        print("FAIL: absolute URI got '../' prefix:", v); ok = False
    if "://" in v and not v.startswith("https://example.org/"):
        print("FAIL: absolute URI mangled:", v); ok = False
import sys
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 2 : keying of destination-URI references.
# 2.1 internal (or default) -> keyed by reftitle
# 2.2 external (internal=False) -> keyed by trailing component after final '#'
# 2.3 external, no '#' -> key is the whole URI
# 2.4 same for SVG and raster
ok = True
# internal by default (no 'internal' key)
c_def = xref(refuri="doc.html#test.Foo", reftitle="test.Foo")
u = run_case([c_def], fmt="svg")
if "test.Foo" not in u:
    print("FAIL 2.1 default: not keyed by reftitle:", u); ok = False
# explicitly internal True
c_int = xref(refuri="doc.html#test.Bar", reftitle="test.Bar", internal=True)
u = run_case([c_int], fmt="png")
if "test.Bar" not in u:
    print("FAIL 2.1 internal: not keyed by reftitle:", u); ok = False
# external with fragment -> key = trailing component
c_ext = xref(refuri="https://ex.org/foo.html#subdir.other.Bob", reftitle="Bob", internal=False)
for fmt in ("svg", "png"):
    u = run_case([c_ext], fmt=fmt)
    if "subdir.other.Bob" not in u:
        print("FAIL 2.2/2.4 ext frag key (%s):" % fmt, u); ok = False
    if "Bob" in u and "subdir.other.Bob" not in u:
        print("FAIL 2.2 keyed by reftitle not trailing comp"); ok = False
# external no fragment -> key = whole uri
c_nofrag = xref(refuri="https://ex.org/whole", reftitle="T", internal=False)
u = run_case([c_nofrag], fmt="svg")
if "https://ex.org/whole" not in u:
    print("FAIL 2.3 no-fragment whole-uri key:", u); ok = False
import sys
print("keys observed OK") if ok else None
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 3 : SVG in-page anchor (refid, no refuri) -> current_filename + '#' + refid,
#         no '../' prefix, keyed by reftitle.
# Req 4 : non-SVG -> '#' + refid, keyed by reftitle, no docname/leading segment.
ok = True
c = xref(refid="test.Foo", reftitle="test.Foo")
svg = run_case([c], fmt="svg", docname="subdir/index", suffix=".html")
print("SVG anchor urls:", svg)
expect_svg = "subdir/index.html#test.Foo"
if svg.get("test.Foo") != expect_svg:
    print("FAIL 3: expected %r got %r" % (expect_svg, svg.get("test.Foo"))); ok = False
if any(v.startswith("../") for v in svg.values()):
    print("FAIL 3.2: '../' prefix present:", svg); ok = False

c2 = xref(refid="test.Foo", reftitle="test.Foo")
png = run_case([c2], fmt="png", docname="subdir/index", suffix=".html")
print("PNG anchor urls:", png)
if png.get("test.Foo") != "#test.Foo":
    print("FAIL 4: expected '#test.Foo' got %r" % png.get("test.Foo")); ok = False
for v in png.values():
    if v != "#test.Foo":
        print("FAIL 4.2: raster anchor not pure '#id':", v); ok = False
import sys
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 5 & 6 : references with neither refuri nor refid contribute NO entry;
#   refuri+refid together -> treated under URI rules only;
#   one entry per resolvable ref, in given order.
ok = True
# 5.1 neither -> skipped
c_none = xref(reftitle="test.Nada")
u = run_case([c_none], fmt="svg")
if "test.Nada" in u or u:
    print("FAIL 5.1: empty ref produced entry:", u); ok = False
# 5.2 both refuri and refid -> URI rules (verbatim uri), NOT anchor
c_both = xref(refuri="doc.html#test.Foo", refid="test.Foo", reftitle="test.Foo")
u = run_case([c_both], fmt="svg")
print("both:", u)
if u.get("test.Foo") != "doc.html#test.Foo":
    print("FAIL 5.2: both-case did not use URI rule:", u); ok = False
# 6: multiple refs, count + only resolvable ones
children = [
    xref(refuri="a.html#A", reftitle="A"),          # entry
    xref(reftitle="B"),                              # skipped (neither)
    xref(refid="C", reftitle="C"),                   # entry (svg anchor)
    xref(refuri="https://x.org/p#D", reftitle="Dt", internal=False),  # entry ext
]
u = run_case(children, fmt="svg", docname="index", suffix=".html")
print("multi:", u)
if set(u.keys()) != {"A", "C", "D"}:
    print("FAIL 6: unexpected key set:", set(u.keys())); ok = False
if u.get("A") != "a.html#A":
    print("FAIL 6: A url wrong:", u.get("A")); ok = False
if u.get("C") != "index.html#C":
    print("FAIL 6: C anchor url wrong:", u.get("C")); ok = False
if u.get("D") != "https://x.org/p#D":
    print("FAIL 6: D ext url wrong:", u.get("D")); ok = False
import sys
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 7.2 / 7.3 : class collection for a diagram is unchanged — each class contributes
# (name, fully-qualified name, list of base names, optional tooltip); import + alias handling.
from sphinx.ext.inheritance_diagram import InheritanceGraph, import_classes
ok = True
classes = import_classes("logging.StreamHandler", None)
print("import_classes(logging.StreamHandler):", classes)
if not classes:
    print("FAIL 7.3: import_classes returned nothing"); ok = False

# Build a graph and check class_info tuple shape + base relationship (non-builtin base).
g = InheritanceGraph(["logging.StreamHandler"], currmodule="logging")
ci = g.class_info
print("class_info entries:", len(ci))
shape_ok = all(isinstance(t, tuple) and len(t) == 4 for t in ci)
if not shape_ok:
    print("FAIL 7.2: class_info tuple shape not 4-elem:", ci); ok = False
sh = [t for t in ci if t[1] == "logging.StreamHandler"]
if not sh:
    print("FAIL 7.2: StreamHandler node missing:", ci); ok = False
else:
    name, fq, bases, tooltip = sh[0]
    print("node:", sh[0])
    if not (isinstance(name, str) and isinstance(fq, str) and isinstance(bases, list)):
        print("FAIL 7.2: tuple field types wrong"); ok = False
    if "logging.Handler" not in bases:
        print("FAIL 7.2: expected non-builtin base logging.Handler not collected:", bases); ok = False
    # Handler node also present
    if not any(t[1] == "logging.Handler" for t in ci):
        print("FAIL 7.2: Handler node missing from graph:", [t[1] for t in ci]); ok = False
import sys
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 1.1 + 1.2 : a resolved destination URI (refuri) is recorded VERBATIM,
# no leading "../", and identically for SVG and raster.
# POSITIVE CONTROL: at base the SVG branch prepends "../", so this FAILS at base.
uri = "foo/bar.html#test.Foo"
child = xref(refuri=uri, reftitle="test.Foo")
svg = run_case([child], fmt="svg")
child2 = xref(refuri=uri, reftitle="test.Foo")
png = run_case([child2], fmt="png")
print("SVG urls:", svg)
print("PNG urls:", png)
ok = True
if svg.get("test.Foo") != uri:
    print("FAIL: SVG did not record refuri verbatim; got", svg.get("test.Foo")); ok = False
if png.get("test.Foo") != uri:
    print("FAIL: PNG did not record refuri verbatim; got", png.get("test.Foo")); ok = False
if svg != png:
    print("FAIL: SVG and PNG url maps differ"); ok = False
# explicit: no "../" prefix
for v in list(svg.values()) + list(png.values()):
    if v.startswith("../"):
        print("FAIL: url has forbidden '../' prefix:", v); ok = False
import sys
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes unit-test html_visit_inheritance_diagram directly by capturing the urls dict handed to generate_dot (via a fake graph/translator; get_graph_hash and render_dot_html neutralized). Coverage:
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): refuri recorded verbatim, no '../', identical for SVG and PNG. HOLDS patched; FAILS at base (base SVG branch prepends '../', so SVG!=PNG and has forbidden '../').
- probe_2 (Req 1.3): absolute https:// URI left unmodified, no '../' prefix. HOLDS patched.
- probe_3 (Req 2.1/2.2/2.3/2.4): internal (and default) keyed by reftitle; external (internal=False) keyed by trailing component after final '#'; external no-fragment keyed by whole URI; same for SVG/PNG. HOLDS patched.
- probe_4 (Req 3 + Req 4): SVG in-page anchor -> current_filename+'#'+refid, no '../', keyed by reftitle; raster -> pure '#'+refid. HOLDS patched; FAILS at base (SVG anchor prepended '../').
- probe_5 (Req 5.1/5.2 + Req 6): ref with neither refuri nor refid contributes no entry; ref with both uses URI rules only; multi-ref ordering/completeness with correct keys {A,C,D}. HOLDS patched.
- probe_6 (Req 7.2/7.3): import_classes + InheritanceGraph.class_info tuple shape (name, fqname, base list, tooltip) and non-builtin base collection unchanged (logging.StreamHandler -> logging.Handler). HOLDS patched.

Discrimination: positive control probe_1 (and probe_4) FAIL at base and HOLD on patched. Candidate weak patch 'naive_drop_dotdot_no_intersphinx_keying' removes the erroneous '../' prefixes (fixing the reported SVG-embedding bug) but keeps keying every refuri by child['reftitle'] — omitting the intersphinx trailing-component keying (Req 2.2/2.3). It is REJECTED by probe_3 (wrong keys 'Bob'/'T' instead of 'subdir.other.Bob'/whole-URI) and probe_5 (key set {A,Dt,C} instead of {A,C,D}), demonstrating the suite discriminates a partial/wrong fix. It applies cleanly at base_commit. No requirements-conforming patch was found that fails the hidden tests. Verdict SOUND: >=5 distinct probes all hold on the patched tree, the positive control discriminates base vs patched, and >=1 candidate patch was exercised and rejected.

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
import sphinx.ext.inheritance_diagram as mod
from docutils import nodes


class FakeNode(list):
    def __init__(self, children, attrs):
        super().__init__(children)
        self.attrs = dict(attrs)
    def __getitem__(self, k):
        if isinstance(k, str):
            return self.attrs[k]
        return list.__getitem__(self, k)
    def get(self, k, default=None):
        return self.attrs.get(k, default)


class Xref(dict):
    """emulate a pending_xref: dict semantics + .get already provided."""
    pass


class FakeGraph:
    def __init__(self, sink):
        self.sink = sink
    def generate_dot(self, name, urls, env=None):
        self.sink['urls'] = dict(urls)
        return "digraph{}"


class _Cfg:
    def __init__(self, fmt): self.graphviz_output_format = fmt
class _Env:
    def __init__(self, fmt): self.config = _Cfg(fmt)
class _Builder:
    def __init__(self, fmt, docname, suffix):
        self.env = _Env(fmt); self.current_docname = docname; self.out_suffix = suffix
class _Tr:
    def __init__(self, fmt, docname, suffix): self.builder = _Builder(fmt, docname, suffix)


def run_case(children, fmt="svg", docname="index", suffix=".html"):
    sink = {}
    graph = FakeGraph(sink)
    node = FakeNode(children, {'graph': graph, 'content': 'X'})
    oh, orr = mod.get_graph_hash, mod.render_dot_html
    mod.get_graph_hash = lambda n: "deadbeef"
    mod.render_dot_html = lambda *a, **k: None
    try:
        try:
            mod.html_visit_inheritance_diagram(_Tr(fmt, docname, suffix), node)
        except nodes.SkipNode:
            pass
    finally:
        mod.get_graph_hash = oh; mod.render_dot_html = orr
    return sink.get('urls', None)


def xref(**kw):
    x = Xref()
    x.update(kw)
    return x

# Req 1.1 + 1.2 : a resolved destination URI (refuri) is recorded VERBATIM,
# no leading "../", and identically for SVG and raster.
# POSITIVE CONTROL: at base the SVG branch prepends "../", so this FAILS at base.
uri = "foo/bar.html#test.Foo"
child = xref(refuri=uri, reftitle="test.Foo")
svg = run_case([child], fmt="svg")
child2 = xref(refuri=uri, reftitle="test.Foo")
png = run_case([child2], fmt="png")
print("SVG urls:", svg)
print("PNG urls:", png)
ok = True
if svg.get("test.Foo") != uri:
    print("FAIL: SVG did not record refuri verbatim; got", svg.get("test.Foo")); ok = False
if png.get("test.Foo") != uri:
    print("FAIL: PNG did not record refuri verbatim; got", png.get("test.Foo")); ok = False
if svg != png:
    print("FAIL: SVG and PNG url maps differ"); ok = False
# explicit: no "../" prefix
for v in list(svg.values()) + list(png.values()):
    if v.startswith("../"):
        print("FAIL: url has forbidden '../' prefix:", v); ok = False
import sys
print("RESULT", "HOLD" if ok else "VIOLATION")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes unit-test html_visit_inheritance_diagram directly by capturing the urls dict handed to generate_dot (via a fake graph/translator; get_graph_hash and render_dot_html neutralized). Coverage:
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): refuri recorded verbatim, no '../', identical for SVG and PNG. HOLDS patched; FAILS at base (base SVG branch prepends '../', so SVG!=PNG and has forbidden '../').
- probe_2 (Req 1.3): absolute https:// URI left unmodified, no '../' prefix. HOLDS patched.
- probe_3 (Req 2.1/2.2/2.3/2.4): internal (and default) keyed by reftitle; external (internal=False) keyed by trailing component after final '#'; external no-fragment keyed by whole URI; same for SVG/PNG. HOLDS patched.
- probe_4 (Req 3 + Req 4): SVG in-page anchor -> current_filename+'#'+refid, no '../', keyed by reftitle; raster -> pure '#'+refid. HOLDS patched; FAILS at base (SVG anchor prepended '../').
- probe_5 (Req 5.1/5.2 + Req 6): ref with neither refuri nor refid contributes no entry; ref with both uses URI rules only; multi-ref ordering/completeness with correct keys {A,C,D}. HOLDS patched.
- probe_6 (Req 7.2/7.3): import_classes + InheritanceGraph.class_info tuple shape (name, fqname, base list, tooltip) and non-builtin base collection unchanged (logging.StreamHandler -> logging.Handler). HOLDS patched.

Discrimination: positive control probe_1 (and probe_4) FAIL at base and HOLD on patched. Candidate weak patch 'naive_drop_dotdot_no_intersphinx_keying' removes the erroneous '../' prefixes (fixing the reported SVG-embedding bug) but keeps keying every refuri by child['reftitle'] — omitting the intersphinx trailing-component keying (Req 2.2/2.3). It is REJECTED by probe_3 (wrong keys 'Bob'/'T' instead of 'subdir.other.Bob'/whole-URI) and probe_5 (key set {A,Dt,C} instead of {A,C,D}), demonstrating the suite discriminates a partial/wrong fix. It applies cleanly at base_commit. No requirements-conforming patch was found that fails the hidden tests. Verdict SOUND: >=5 distinct probes all hold on the patched tree, the positive control discriminates base vs patched, and >=1 candidate patch was exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The fix's essence is (a) removing the SVG-only `'../'` prepend on both refuri and refid branches, and (b) adding internal/external keying via `child.get('internal', True)` and `refuri.rsplit('#',1)[-1]`. Requirements 1-3 pin exactly these two changes; R1.3 (absolute URLs left unmodified) is an accurate consequence of recording refuri verbatim. Modeling boundary is the whole changed loop, not a narrow slice. Probe stdout truncation was a harness display artifact; patch-apply-clean confirms gold matches the code inspected.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes behavior generically and legitimately localizes the change to html_visit_inheritance_diagram in sphinx/ext/inheritance_diagram.py. No test names/paths (e.g. test_inheritance_diagram_svg_html), no parametrization ids, no fixture identifiers (subdir.other.Bob, example.org, DocLowerLevel/DocHere, the zlib inventory), and no quoted test or gold code appear. The gold patch introduces no new public identifiers to leak (the only new symbol is a local var `refname`, which is NOT mentioned). Requirement 2 (external/intersphinx keying: internal->key by reftitle; external->key by refuri.rsplit('#',1)[-1] i.e. trailing component after last '#') is content beyond the public problem_statement — it derives from the gold edit — but it is expressed as a behavioral rule describing what the fix must do, which is the sanctioned translation of gold behavior into requirements, not transmission of the hidden tests. Requirements 1/3/4/5/7 (verbatim URI recording, SVG anchor = filename#refid vs raster #refid, absolute-URL untouched, drop refs with neither) map to the public bug report (the blanket '../' prefix). No case enumeration mirrors the test parametrization; the doc describes the field-driven branch logic rather than the specific fixture cases.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
