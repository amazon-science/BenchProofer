# P2 adversarial audit — sphinx-doc__sphinx-7748

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_poscontrol.py`, `probe_2_content_class.py`, `probe_3_single.py`, `probe_4_strip.py`, `probe_5_disabled.py`, `probe_6_nostop.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_poscontrol.py` → holds on the patched tree (good)

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
# Req 1.2/1.3/1.4/2.1/2.2: THREE overloaded sigs collected, each own line, ORDER preserved,
# args+retann preserved exactly. Positive control: HOLDS patched, FAILS at base.
TARGET = ('class E:\n'
          '    def __init__(self):\n'
          '        """E(foo: int, bar: int) -> int \\\\\n'
          '        E(foo: str, bar: str) -> str \\\\\n'
          '        E(foo: float, bar: float) -> float"""\n')
app = build_app({'autoclass_content':'init','autodoc_docstring_signature':True}, TARGET)
res = do_autodoc(app, 'class', 'target.docstring_signature.E')
print("RESULT:")
for l in res: print(repr(l))
want = [
    '.. py:class:: E(foo: int, bar: int) -> int',
    '              E(foo: str, bar: str) -> str',
    '              E(foo: float, bar: float) -> float',
]
# strict subsequence in this exact order
try:
    idxs = [res.index(w) for w in want]
    ordered = idxs == sorted(idxs) and len(set(idxs))==3
except ValueError:
    ordered = False
ok = all(w in res for w in want) and ordered
print("all three sigs, each own line, exact order+annotations:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_content_class.py` → holds on the patched tree (good)

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
TARGET = 'class E:\n    def __init__(self):\n        """E(foo: int, bar: int, baz: int) -> None \\\\\n        E(foo: str, bar: str, baz: str) -> None"""\n'
app = build_app({'autoclass_content':'class','autodoc_docstring_signature':True}, TARGET)
res = do_autodoc(app, 'class', 'target.docstring_signature.E')
print("RESULT:")
for l in res: print(repr(l))
# content mode 'class' excludes constructor -> empty arg list, no overload lines
ok = ('.. py:class:: E()' in res) and not any('foo: int' in l for l in res)
print("empty arg list, no ctor sigs leaked:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_single.py` → holds on the patched tree (good)

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
# D already exists in the target root with single-signature ctor docstring "D(foo, bar, baz)"
app = build_app({'autoclass_content':'init','autodoc_docstring_signature':True}, '')
res = do_autodoc(app, 'class', 'target.docstring_signature.D')
print("RESULT:")
for l in res: print(repr(l))
ok = ('.. py:class:: D(foo, bar, baz)' in res)
# and no extra continuation line
n = sum(1 for l in res if l.strip().startswith('.. py:class:: D'))
print("single sig adopted:", ok, "class-directive-lines:", n)
sys.exit(0 if ok and n==1 else 1)
```

Attack 4 — `probe_4_strip.py` → holds on the patched tree (good)

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
TARGET = 'class F:\n    def __init__(self):\n        """F(a) -> int \\\\\n        F(b) -> str\n\n        Real description here.\n        """\n'
app = build_app({'autoclass_content':'init','autodoc_docstring_signature':True}, TARGET)
res = do_autodoc(app, 'class', 'target.docstring_signature.F')
print("RESULT:")
for l in res: print(repr(l))
body = "\n".join(res)
# description must survive; raw signature text must NOT appear in body region
has_desc = 'Real description here.' in body
# after the module line, no leftover 'F(a) -> int' as body text
directive_ok = '.. py:class:: F(a) -> int' in res and '              F(b) -> str' in res
# The signature lines should not ALSO appear as body prose (i.e., not duplicated below module line)
mod_idx = next(i for i,l in enumerate(res) if ':module:' in l)
body_after = res[mod_idx+1:]
leaked = any(('F(a) -> int' in l or 'F(b) -> str' in l) for l in body_after)
ok = has_desc and directive_ok and not leaked
print("desc kept:", has_desc, "dir_ok:", directive_ok, "leaked_below:", leaked)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_disabled.py` → holds on the patched tree (good)

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
TARGET = 'class E:\n    def __init__(self):\n        """E(foo: int, bar: int, baz: int) -> None \\\\\n        E(foo: str, bar: str, baz: str) -> None"""\n'
app = build_app({'autoclass_content':'init','autodoc_docstring_signature':False}, TARGET)
res = do_autodoc(app, 'class', 'target.docstring_signature.E')
print("RESULT:")
for l in res: print(repr(l))
# feature off: class rendered with empty () and the raw docstring appears as body
directive_empty = '.. py:class:: E()' in res
body = "\n".join(res)
raw_in_body = 'E(foo: int, bar: int, baz: int)' in body  # not stripped
ok = directive_empty and raw_in_body
print("empty directive:", directive_empty, "raw docstring kept in body:", raw_in_body)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_nostop.py` → holds on the patched tree (good)

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
# G has no continuation marker on first sig -> only first adopted, second stays as body
TARGET = 'class G:\n    def __init__(self):\n        """G(a) -> int\n        G(b) -> str"""\n'
app = build_app({'autoclass_content':'init','autodoc_docstring_signature':True}, TARGET)
res = do_autodoc(app, 'class', 'target.docstring_signature.G')
print("RESULT:")
for l in res: print(repr(l))
# only first signature adopted in header, no continuation line
adopted = '.. py:class:: G(a) -> int' in res
no_second_in_header = not any(l.strip().startswith('G(b)') and l.startswith(' ' ) and ':: ' not in l for l in res)
# second sig must appear as body text (not consumed)
mod_idx = next(i for i,l in enumerate(res) if ':module:' in l)
second_in_body = any('G(b) -> str' in l for l in res[mod_idx+1:])
ok = adopted and second_in_body
print("first adopted:", adopted, "second left in body (not collected):", second_in_body)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_poscontrol.py`

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
# Req 1.2/1.3/1.4/2.1/2.2: THREE overloaded sigs collected, each own line, ORDER preserved,
# args+retann preserved exactly. Positive control: HOLDS patched, FAILS at base.
TARGET = ('class E:\n'
          '    def __init__(self):\n'
          '        """E(foo: int, bar: int) -> int \\\\\n'
          '        E(foo: str, bar: str) -> str \\\\\n'
          '        E(foo: float, bar: float) -> float"""\n')
app = build_app({'autoclass_content':'init','autodoc_docstring_signature':True}, TARGET)
res = do_autodoc(app, 'class', 'target.docstring_signature.E')
print("RESULT:")
for l in res: print(repr(l))
want = [
    '.. py:class:: E(foo: int, bar: int) -> int',
    '              E(foo: str, bar: str) -> str',
    '              E(foo: float, bar: float) -> float',
]
# strict subsequence in this exact order
try:
    idxs = [res.index(w) for w in want]
    ordered = idxs == sorted(idxs) and len(set(idxs))==3
except ValueError:
    ordered = False
ok = all(w in res for w in want) and ordered
print("all three sigs, each own line, exact order+annotations:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: collect EVERY leading signature from a docstring for overloaded callables (autodoc_docstring_signature). Gold edits sphinx/ext/autodoc/__init__.py DocstringSignatureMixin._find_signature/get_doc/format_signature and ClassDocumenter, plus ModuleDocumenter objpath=[None] guard.

Probes run in the official image via nl_attack. Each builds a SphinxTestApp over tests/roots/test-ext-autodoc (target module appended in a temp copy) and runs the real ClassDocumenter through do_autodoc (same harness the hidden F2P tests use). Results on gold-PATCHED tree unless noted.

Probe 1 (POSITIVE CONTROL) — Req 1.2/1.3/1.4/2.1/2.2: three backslash-continued overloads for class E collected, rendered each on its own line, EXACT order, args+retann preserved. HOLDS patched; VIOLATED at base (base keeps trailing '\\' and emits only first sig in header, rest dumped to body) => prepatch reproduced, discriminating power confirmed.
Probe 2 — Req 6.4: autoclass_content='class' excludes constructor => '.. py:class:: E()' with NO ctor signatures leaked. HOLDS.
Probe 3 — Req 6.1: single-signature class D unchanged => exactly one 'D(foo, bar, baz)' directive line. HOLDS.
Probe 4 — Req 5.1/5.2: continued sigs consumed and STRIPPED from body while description text ('Real description here.') survives; no raw sig text below :module:. HOLDS.
Probe 5 — Req 6.3: autodoc_docstring_signature disabled => empty 'E()' directive and raw docstring left in body (nothing read/stripped). HOLDS.
Probe 6 — Req 2.3/2.4/3: first sig line WITHOUT trailing backslash => scan stops, only first adopted, second line left as body text (not collected). HOLDS.

TOO-WEAK candidates (must apply at base_commit; both derived from gold with one line changed):
- weak_B (space-join instead of newline-join of collected sigs): probe_1 REJECTS (all sigs mashed onto one header line, violates Req 3 'each on its own line'). Suite discriminates.
- weak_C (render subsequent sigs in reversed order): probe_1 REJECTS (order violated, Req 1.2/2.1). Suite discriminates.

>=5 distinct probes all HOLD on patched tree; positive control HOLDS patched & FAILS at base; >=1 candidate exercised and REJECTED. No probe fails on the patched tree; no probe-conforming alternative found. Req 7 (module-level objpath guard) not directly probed — it is a regression guard on the gold's own added code and requires a singledispatch fixture; Reqs 1-6 fully covered including the 'SHALL keep' regression criteria (Req 6.1/6.3/6.4). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_poscontrol.py`, `probe_2_content_class.py`, `probe_3_single.py`, `probe_4_strip.py`, `probe_5_disabled.py`, `probe_6_nostop.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_poscontrol.py` → holds on the patched tree (good)

Attack 2 — `probe_2_content_class.py` → holds on the patched tree (good)

Attack 3 — `probe_3_single.py` → holds on the patched tree (good)

Attack 4 — `probe_4_strip.py` → holds on the patched tree (good)

Attack 5 — `probe_5_disabled.py` → holds on the patched tree (good)

Attack 6 — `probe_6_nostop.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_poscontrol.py`

```python
import os, tempfile, shutil
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as spath
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter
from unittest.mock import Mock
from io import StringIO

def build_app(confoverrides, extra_target):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp,"src")
    shutil.copytree("tests/roots/test-ext-autodoc", dst)
    tgt = os.path.join(dst,"target","docstring_signature.py")
    with open(tgt,"a") as f:
        f.write("\n"+extra_target+"\n")
    st=StringIO(); wr=StringIO()
    app = SphinxTestApp('dummy', srcdir=spath(dst), confoverrides=confoverrides, status=st, warning=wr)
    app._sbu_warn = wr
    return app

def do_autodoc(app, objtype, name, options=None):
    if options is None: options={}
    app.env.temp_data['docname']='index'
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return list(bridge.result)
import sys
# Req 1.2/1.3/1.4/2.1/2.2: THREE overloaded sigs collected, each own line, ORDER preserved,
# args+retann preserved exactly. Positive control: HOLDS patched, FAILS at base.
TARGET = ('class E:\n'
          '    def __init__(self):\n'
          '        """E(foo: int, bar: int) -> int \\\\\n'
          '        E(foo: str, bar: str) -> str \\\\\n'
          '        E(foo: float, bar: float) -> float"""\n')
app = build_app({'autoclass_content':'init','autodoc_docstring_signature':True}, TARGET)
res = do_autodoc(app, 'class', 'target.docstring_signature.E')
print("RESULT:")
for l in res: print(repr(l))
want = [
    '.. py:class:: E(foo: int, bar: int) -> int',
    '              E(foo: str, bar: str) -> str',
    '              E(foo: float, bar: float) -> float',
]
# strict subsequence in this exact order
try:
    idxs = [res.index(w) for w in want]
    ordered = idxs == sorted(idxs) and len(set(idxs))==3
except ValueError:
    ordered = False
ok = all(w in res for w in want) and ordered
print("all three sigs, each own line, exact order+annotations:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: collect EVERY leading signature from a docstring for overloaded callables (autodoc_docstring_signature). Gold edits sphinx/ext/autodoc/__init__.py DocstringSignatureMixin._find_signature/get_doc/format_signature and ClassDocumenter, plus ModuleDocumenter objpath=[None] guard.

Probes run in the official image via nl_attack. Each builds a SphinxTestApp over tests/roots/test-ext-autodoc (target module appended in a temp copy) and runs the real ClassDocumenter through do_autodoc (same harness the hidden F2P tests use). Results on gold-PATCHED tree unless noted.

Probe 1 (POSITIVE CONTROL) — Req 1.2/1.3/1.4/2.1/2.2: three backslash-continued overloads for class E collected, rendered each on its own line, EXACT order, args+retann preserved. HOLDS patched; VIOLATED at base (base keeps trailing '\\' and emits only first sig in header, rest dumped to body) => prepatch reproduced, discriminating power confirmed.
Probe 2 — Req 6.4: autoclass_content='class' excludes constructor => '.. py:class:: E()' with NO ctor signatures leaked. HOLDS.
Probe 3 — Req 6.1: single-signature class D unchanged => exactly one 'D(foo, bar, baz)' directive line. HOLDS.
Probe 4 — Req 5.1/5.2: continued sigs consumed and STRIPPED from body while description text ('Real description here.') survives; no raw sig text below :module:. HOLDS.
Probe 5 — Req 6.3: autodoc_docstring_signature disabled => empty 'E()' directive and raw docstring left in body (nothing read/stripped). HOLDS.
Probe 6 — Req 2.3/2.4/3: first sig line WITHOUT trailing backslash => scan stops, only first adopted, second line left as body text (not collected). HOLDS.

TOO-WEAK candidates (must apply at base_commit; both derived from gold with one line changed):
- weak_B (space-join instead of newline-join of collected sigs): probe_1 REJECTS (all sigs mashed onto one header line, violates Req 3 'each on its own line'). Suite discriminates.
- weak_C (render subsequent sigs in reversed order): probe_1 REJECTS (order violated, Req 1.2/2.1). Suite discriminates.

>=5 distinct probes all HOLD on patched tree; positive control HOLDS patched & FAILS at base; >=1 candidate exercised and REJECTED. No probe fails on the patched tree; no probe-conforming alternative found. Req 7 (module-level objpath guard) not directly probed — it is a regression guard on the gold's own added code and requires a singledispatch fixture; Reqs 1-6 fully covered including the 'SHALL keep' regression criteria (Req 6.1/6.3/6.4). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed gold-patched tree in instance image. _find_signature/format_signature source matches patch exactly. Multi-overload extraction, ordering (primary first, additional as '(%s) -> %s' joined by newline in format_signature), backslash-continuation stripping, empty-line boundary, name-candidate filtering, single-block sourcing, docstring stripping, and the ClassDocumenter/ModuleDocumenter objpath=[None] fix are all present and behave as the requirements state. Modeling boundary is the changed observable behavior (whole DocstringSignatureMixin signature-collection), not a narrow helper slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the multi-signature docstring feature as behavioral requirements. It goes beyond the public problem_statement in naming the gold's mechanisms (backslash-continuation marker with whitespace stripping = Req 2; candidate names objpath[-1]/__init__/MRO = Req 3.4; module-grouped-function objpath fix = Req 7), but each is a translation of the fix's BEHAVIOR into a requirement — the legitimate localization/behavioral-spec purpose — not transmission of the tests. No leakage of hidden-test artifacts: the specific test signatures (E(foo: int,...) -> None / str,str,str) are NOT enumerated, no test file paths (tests/test_ext_autodoc_configs.py, target/docstring_signature.py), no test function names (test_autoclass_content_and_docstring_signature_init/both/class), no class names E/D, no FAIL_TO_PASS ids, and no quoted test or gold source. The int/str overload parametrization from the test data is absent, so the prose does not reconstruct the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
