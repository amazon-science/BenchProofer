# P2 adversarial audit — sphinx-doc__sphinx-9229

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
# Probe 1 (POSITIVE CONTROL) — Req 2.1 / Req 3.2:
# When a module-level alias HAS an author doc comment, autodoc SHALL show that
# comment instead of the 'alias of ...' placeholder.
# HOLDS iff the comment text appears AND no 'alias of' placeholder line appears.
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Foo:\n    """Foo doc"""\n    def meth(self):\n        pass\n\n'
    '#: my comment line\n'
    'Commented = Foo\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def do_autodoc(app, objtype, name):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters[objtype]
    opts = process_documenter_options(doccls, app.config, {})
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)

out = do_autodoc(app, 'class', 'mypkg.mod.Commented')
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)
print("OUTPUT:", out)
has_comment = any('my comment line' in l for l in out)
has_alias = any('alias of' in l for l in out)
print("has_comment=", has_comment, "has_alias_placeholder=", has_alias)
sys.exit(0 if (has_comment and not has_alias) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Probe 2 — Req 4.2 / Req 3.1 (regression / "SHALL keep"):
# An alias WITHOUT a doc comment SHALL still render exactly the 'alias of <target>'
# placeholder and no class docstring.
# HOLDS iff output equals the expected attribute+placeholder block with the
# 'alias of' line and no leaked class docstring ("Foo doc").
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Foo:\n    """Foo doc"""\n    pass\n\n'
    'Plain = Foo\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def do_autodoc(app, objtype, name):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters[objtype]
    opts = process_documenter_options(doccls, app.config, {})
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)

out = do_autodoc(app, 'class', 'mypkg.mod.Plain')
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)
print("OUTPUT:", out)
expected = [
    '',
    '.. py:attribute:: Plain',
    '   :module: mypkg.mod',
    '',
    '   alias of :class:`mypkg.mod.Foo`',
]
ok = (out == expected) and not any('Foo doc' in l for l in out)
print("matches_expected=", out == expected, "no_class_docstring=", not any('Foo doc' in l for l in out))
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Probe 3 — Req 2.1 & 2.2 (get_doc return semantics):
# For an alias WITH a comment, get_doc SHALL return an empty block ([] -> a
# present-but-empty result, NOT None). For an alias WITHOUT a comment, get_doc
# SHALL return None ("no documentation").
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Foo:\n    """Foo doc"""\n    pass\n\n'
    'Plain = Foo\n\n'
    '#: cmt\nCommented = Foo\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def make_documenter(name):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters['class']
    opts = process_documenter_options(doccls, app.config, {})
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    d = doccls(bridge, name)
    d.parse_name()
    d.import_object()
    # Replicate Documenter.generate(): populate self.analyzer for the real module
    from sphinx.pycode import ModuleAnalyzer
    try:
        d.analyzer = ModuleAnalyzer.for_module(d.get_real_modname())
        d.analyzer.analyze()
    except Exception:
        d.analyzer = None
    return d

d_plain = make_documenter('mypkg.mod.Plain')
d_cmt = make_documenter('mypkg.mod.Commented')
print("Plain doc_as_attr=", d_plain.doc_as_attr, "Commented doc_as_attr=", d_cmt.doc_as_attr)
doc_plain = d_plain.get_doc()
doc_cmt = d_cmt.get_doc()
print("get_doc(Plain)=", doc_plain)
print("get_doc(Commented)=", doc_cmt)
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)

ok = (d_plain.doc_as_attr and d_cmt.doc_as_attr
      and doc_plain is None
      and doc_cmt == [])
print("plain_is_None=", doc_plain is None, "commented_is_empty_list=", doc_cmt == [])
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Probe 4 — Req 1 (get_variable_comment lookup semantics):
# The class documenter SHALL provide a means to retrieve the doc comment for the
# object by dotted path in its module namespace (empty class-namespace key).
#  - returns the comment lines for a commented alias (Req 1.4)
#  - returns an empty/absent result for an uncommented alias (Req 1.5)
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Foo:\n    """Foo doc"""\n    pass\n\n'
    'Plain = Foo\n\n'
    '#: cmt line one\nCommented = Foo\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def make_documenter(name):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters['class']
    opts = process_documenter_options(doccls, app.config, {})
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    d = doccls(bridge, name)
    d.parse_name(); d.import_object()
    from sphinx.pycode import ModuleAnalyzer
    try:
        d.analyzer = ModuleAnalyzer.for_module(d.get_real_modname())
        d.analyzer.analyze()
    except Exception:
        d.analyzer = None
    return d

d_plain = make_documenter('mypkg.mod.Plain')
d_cmt = make_documenter('mypkg.mod.Commented')

# Requirement 1.1: there must be a retrieval means on the documenter.
if not hasattr(d_cmt, 'get_variable_comment'):
    print("NO get_variable_comment method"); sys.path.remove(work); shutil.rmtree(work, ignore_errors=True); sys.exit(1)

cmt = d_cmt.get_variable_comment()
plain = d_plain.get_variable_comment()
print("Commented comment=", cmt)
print("Plain comment=", plain)
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)

# 1.4: commented -> non-empty sequence of lines containing the comment text
# 1.5: uncommented -> absent (falsy / empty)
ok = (cmt and any('cmt line one' in l for l in cmt)) and (not plain)
print("commented_nonempty=", bool(cmt and any('cmt line one' in l for l in cmt)),
      "plain_absent=", not plain)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Probe 5 — Req 4.1 / 4.3 (regression: ordinary class untouched):
# For an object NOT documented as an alias (a real class), autodoc SHALL render
# its docstring and its members exactly as before. HOLDS iff the class docstring
# line and the member method appear, and NO 'alias of' placeholder is emitted.
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Real:\n'
    '    """Real class docstring here"""\n'
    '    def meth(self):\n'
    '        """method doc"""\n'
    '        pass\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def do_autodoc(app, name, options):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters['class']
    opts = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    doccls(bridge, name).generate(more_content=None)
    return list(bridge.result)

out = do_autodoc(app, 'mypkg.mod.Real', {'members': None})
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)
print("OUTPUT:", out)
has_docstring = any('Real class docstring here' in l for l in out)
has_member = any('.. py:method:: Real.meth' in l for l in out)
has_alias = any('alias of' in l for l in out)
print("has_docstring=", has_docstring, "has_member=", has_member, "has_alias=", has_alias)
sys.exit(0 if (has_docstring and has_member and not has_alias) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Probe 6 — Req 4.3 (alias skips documenting members, whether or not commented):
# A commented alias must still NOT document the target class's members. HOLDS iff
# the commented alias output contains the comment but NONE of Foo's members
# (e.g. 'Foo.meth' / py:method) are emitted.
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Foo:\n'
    '    """Foo doc"""\n'
    '    def meth(self):\n'
    '        """member method"""\n'
    '        pass\n\n'
    '#: alias comment\nCommented = Foo\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def do_autodoc(app, name, options):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters['class']
    opts = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    doccls(bridge, name).generate(more_content=None)
    return list(bridge.result)

# even asking for members, an alias must not document them
out = do_autodoc(app, 'mypkg.mod.Commented', {'members': None})
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)
print("OUTPUT:", out)
has_comment = any('alias comment' in l for l in out)
has_member = any('meth' in l for l in out) or any('member method' in l for l in out)
has_alias_placeholder = any('alias of' in l for l in out)
print("has_comment=", has_comment, "has_member=", has_member,
      "has_alias_placeholder=", has_alias_placeholder)
sys.exit(0 if (has_comment and not has_member and not has_alias_placeholder) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Probe 1 (POSITIVE CONTROL) — Req 2.1 / Req 3.2:
# When a module-level alias HAS an author doc comment, autodoc SHALL show that
# comment instead of the 'alias of ...' placeholder.
# HOLDS iff the comment text appears AND no 'alias of' placeholder line appears.
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Foo:\n    """Foo doc"""\n    def meth(self):\n        pass\n\n'
    '#: my comment line\n'
    'Commented = Foo\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def do_autodoc(app, objtype, name):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters[objtype]
    opts = process_documenter_options(doccls, app.config, {})
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)

out = do_autodoc(app, 'class', 'mypkg.mod.Commented')
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)
print("OUTPUT:", out)
has_comment = any('my comment line' in l for l in out)
has_alias = any('alias of' in l for l in out)
print("has_comment=", has_comment, "has_alias_placeholder=", has_alias)
sys.exit(0 if (has_comment and not has_alias) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9229: autodoc must honour a variable/attribute doc-comment on a module-level class alias, showing the comment instead of the 'alias of <target>' placeholder; behaviour for an uncommented alias and for ordinary (non-alias) objects must be unchanged.

HARNESS: The prior auditor (G-PANEL-2 note in meta.json) reported that isolated do_autodoc probes returned an empty list even for the known-passing base test, and fell back to trusting the G-RESOLVE stamp. I found the real cause and built a working harness: the class documenter reads self.analyzer.attr_docs (populated by Documenter.generate), so probes that call get_doc/get_variable_comment directly must first set d.analyzer = ModuleAnalyzer.for_module(...).analyze(). Full generate()-based probes work as-is. I therefore have genuine machine checks, not a stamp deferral.

### PROBES (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req 2.1/3.2): commented alias output contains the comment text AND no 'alias of' placeholder. HOLDS patched, VIOLATED at base (base emits BOTH the comment and the placeholder line) -> discriminates.
- probe_2 (Req 4.2/3.1 regression): uncommented alias renders EXACTLY ['', '.. py:attribute:: Plain', '   :module: mypkg.mod', '', '   alias of :class:`mypkg.mod.Foo`'] with no class docstring.
- probe_3 (Req 2.1/2.2): get_doc returns [] for commented alias and None for uncommented alias (both doc_as_attr True). Base returns None for both -> discriminates.
- probe_4 (Req 1.1/1.4/1.5): get_variable_comment method exists, returns the comment lines for a commented alias and a falsy/empty result for an uncommented one. Method absent at base -> discriminates.
- probe_5 (Req 4.1/4.3 regression): an ordinary class still renders its docstring + members and no 'alias of'.
- probe_6 (Req 4.3): a commented alias still does NOT document the target class's members (even with members option), shows the comment and no placeholder.

### CANDIDATE WRONG-FIXES (both REJECTED by the suite -> suite discriminates):
- candA (partial fix: applies only the get_doc branch, leaves add_content always substituting the 'alias of' placeholder). Probe suite REJECTS: probe_1 VIOLATED (placeholder still shown for commented alias) and probe_6 VIOLATED. Encodes a weak reading of Req 2 without Req 3.2.
- candB (naive: get_doc always returns [] for aliases and add_content never substitutes the placeholder). Probe suite REJECTS: probe_2 VIOLATED (uncommented alias loses its 'alias of' placeholder), probe_3 & probe_4 VIOLATED. This is exactly the Req-4.2/2.2 regression the requirements forbid.

VERDICT: SOUND. 6 distinct probes covering Req 1-4 (including the 'SHALL keep' regressions Req 4.1/4.2/4.3) all hold on the patched tree; the positive control discriminates base vs patched (prepatch reproduced); >=1 candidate exercised and 2/2 wrong-fix candidates rejected. No requirements violation found and no requirements-conforming alternative patch that fails to resolve was found.

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
# Probe 1 (POSITIVE CONTROL) — Req 2.1 / Req 3.2:
# When a module-level alias HAS an author doc comment, autodoc SHALL show that
# comment instead of the 'alias of ...' placeholder.
# HOLDS iff the comment text appears AND no 'alias of' placeholder line appears.
import os, sys, tempfile, shutil
from unittest.mock import Mock

work = tempfile.mkdtemp()
pkg = os.path.join(work, 'mypkg'); os.makedirs(pkg)
open(os.path.join(pkg, '__init__.py'), 'w').write('')
open(os.path.join(pkg, 'mod.py'), 'w').write(
    'class Foo:\n    """Foo doc"""\n    def meth(self):\n        pass\n\n'
    '#: my comment line\n'
    'Commented = Foo\n'
)
sys.path.insert(0, work)
src = os.path.join(work, 'src'); os.makedirs(src)
open(os.path.join(src, 'conf.py'), 'w').write("extensions=['sphinx.ext.autodoc']\n")
open(os.path.join(src, 'index.rst'), 'w').write("x\n")

from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.util.docutils import LoggingReporter

app = Sphinx(src, src, os.path.join(work, 'out'), os.path.join(work, 'dt'),
             'html', status=None, warning=sys.stderr, freshenv=True)

def do_autodoc(app, objtype, name):
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters[objtype]
    opts = process_documenter_options(doccls, app.config, {})
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), opts, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)

out = do_autodoc(app, 'class', 'mypkg.mod.Commented')
sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)
print("OUTPUT:", out)
has_comment = any('my comment line' in l for l in out)
has_alias = any('alias of' in l for l in out)
print("has_comment=", has_comment, "has_alias_placeholder=", has_alias)
sys.exit(0 if (has_comment and not has_alias) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9229: autodoc must honour a variable/attribute doc-comment on a module-level class alias, showing the comment instead of the 'alias of <target>' placeholder; behaviour for an uncommented alias and for ordinary (non-alias) objects must be unchanged.

HARNESS: The prior auditor (G-PANEL-2 note in meta.json) reported that isolated do_autodoc probes returned an empty list even for the known-passing base test, and fell back to trusting the G-RESOLVE stamp. I found the real cause and built a working harness: the class documenter reads self.analyzer.attr_docs (populated by Documenter.generate), so probes that call get_doc/get_variable_comment directly must first set d.analyzer = ModuleAnalyzer.for_module(...).analyze(). Full generate()-based probes work as-is. I therefore have genuine machine checks, not a stamp deferral.

### PROBES (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req 2.1/3.2): commented alias output contains the comment text AND no 'alias of' placeholder. HOLDS patched, VIOLATED at base (base emits BOTH the comment and the placeholder line) -> discriminates.
- probe_2 (Req 4.2/3.1 regression): uncommented alias renders EXACTLY ['', '.. py:attribute:: Plain', '   :module: mypkg.mod', '', '   alias of :class:`mypkg.mod.Foo`'] with no class docstring.
- probe_3 (Req 2.1/2.2): get_doc returns [] for commented alias and None for uncommented alias (both doc_as_attr True). Base returns None for both -> discriminates.
- probe_4 (Req 1.1/1.4/1.5): get_variable_comment method exists, returns the comment lines for a commented alias and a falsy/empty result for an uncommented one. Method absent at base -> discriminates.
- probe_5 (Req 4.1/4.3 regression): an ordinary class still renders its docstring + members and no 'alias of'.
- probe_6 (Req 4.3): a commented alias still does NOT document the target class's members (even with members option), shows the comment and no placeholder.

### CANDIDATE WRONG-FIXES (both REJECTED by the suite -> suite discriminates):
- candA (partial fix: applies only the get_doc branch, leaves add_content always substituting the 'alias of' placeholder). Probe suite REJECTS: probe_1 VIOLATED (placeholder still shown for commented alias) and probe_6 VIOLATED. Encodes a weak reading of Req 2 without Req 3.2.
- candB (naive: get_doc always returns [] for aliases and add_content never substitutes the placeholder). Probe suite REJECTS: probe_2 VIOLATED (uncommented alias loses its 'alias of' placeholder), probe_3 & probe_4 VIOLATED. This is exactly the Req-4.2/2.2 regression the requirements forbid.

VERDICT: SOUND. 6 distinct probes covering Req 1-4 (including the 'SHALL keep' regressions Req 4.1/4.2/4.3) all hold on the patched tree; the positive control discriminates base vs patched (prepatch reproduced); >=1 candidate exercised and 2/2 wrong-fix candidates rejected. No requirements violation found and no requirements-conforming alternative patch that fails to resolve was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Grounded via nl_attack probe (exit 0) constructing an alias-with-comment and an alias-without-comment module and reading ModuleAnalyzer.attr_docs; plus F2P/test_patch expected output. Minor code quirk (get_variable_comment builds a local `analyzer` from get_real_modname but returns self.analyzer.attr_docs) does not create an observable divergence for the modeled behavior and requirements describe intended semantics faithfully. Note: this bundle's G-PANEL-3 (leakage) fail cites a Req-4 sub-criteria list (class/init/both docstrings, Bases-of-generic, decorators) that does NOT appear in the current requirements.md — a stale detail, irrelevant to faithfulness.

Counterexample / evidence:

```
None found. Probe HOLDS on gold-patched tree; alias+comment yields comment lines, alias without comment yields no attr_docs entry, exactly as the four requirements describe.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md contains no hidden-test artifacts: no test function name (test_class_alias_having_doccomment), no test file path, no fixture identifiers (OtherAlias, Bar, '#: docstring'), and no expected-output lines ('.. py:attribute:: OtherAlias', ':module: target.classes'). The fix-invented method get_variable_comment is described behaviorally, never named. Named symbols (ClassDocumenter, get_doc, add_content, doc_as_attr, ModuleAnalyzer, attr_docs) are pre-existing Sphinx internals = legitimate localization. Req 1.2 ('empty class-namespace component together with the object's dotted path as the lookup key') and the []-vs-None/PycodeError prose closely track the gold implementation, but this is the intended translation of the fix into behavioral requirements, not transmission of the tests — it describes the standard attr_docs key convention and does not reconstruct the single F2P test. No parametrization exists to mirror. The bug scenario (aliases showing only 'alias of ...' despite author docstrings) is fully public via problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
