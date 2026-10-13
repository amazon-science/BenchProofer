# P2 adversarial audit — sphinx-doc__sphinx-8035

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_control.py`, `probe_2_omit.py`, `probe_3_allnoarg.py`, `probe_4_nonmatch.py`, `probe_5_named.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_control.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_control.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, shutil
root = os.getcwd()
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
from sphinx.util.docutils import LoggingReporter
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from unittest.mock import Mock

testroot = os.path.join(root, 'tests', 'roots', 'test-ext-autodoc')
srcdir = os.path.join(tempfile.mkdtemp(), 'ext-autodoc')
shutil.copytree(testroot, srcdir)
app = SphinxTestApp('html', srcdir=sphinx_path(srcdir))

def do_autodoc(app, objtype, name, options=None):
    options = options or {}
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    doccls(bridge, name).generate()
    return bridge.result

app.config.autoclass_content = 'class'
actual = list(do_autodoc(app, 'module', 'target.private',
              {"members": None, "private-members": "_public_function"}))
print("ACTUAL", actual)
expected = [
    '',
    '.. py:module:: target.private',
    '',
    '',
    '.. py:function:: _public_function(name)',
    '   :module: target.private',
    '',
    '   public_function is a docstring().',
    '',
    '   :meta public:',
    '',
]
assert actual == expected, "output mismatch"
print("Req1.2/1.3/1.5 OK: only named private member documented, full block")
sys.exit(0)
```

Attack 2 — `probe_2_omit.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, shutil
root = os.getcwd()
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
from sphinx.util.docutils import LoggingReporter
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from unittest.mock import Mock
srcdir = os.path.join(tempfile.mkdtemp(), "ext-autodoc")
shutil.copytree(os.path.join(root,"tests","roots","test-ext-autodoc"), srcdir)
app = SphinxTestApp("html", srcdir=sphinx_path(srcdir))
def do_autodoc(app, objtype, name, options=None):
    options = options or {}
    app.env.temp_data.setdefault("docname","index")
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(""), docoptions, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)
app.config.autoclass_content = "class"

actual = do_autodoc(app, "module", "target.private", {"members": None})
print("ACTUAL", actual)
expected = [
    '',
    '.. py:module:: target.private',
    '',
    '',
    '.. py:function:: _public_function(name)',
    '   :module: target.private',
    '',
    '   public_function is a docstring().',
    '',
    '   :meta public:',
    '',
]
assert actual == expected, "Req2 mismatch"
print("Req2.1/2.2/2.3 OK: omit private-members -> meta-public kept, meta-private omitted")
sys.exit(0)
```

Attack 3 — `probe_3_allnoarg.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, shutil
root = os.getcwd()
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
from sphinx.util.docutils import LoggingReporter
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from unittest.mock import Mock
srcdir = os.path.join(tempfile.mkdtemp(), "ext-autodoc")
shutil.copytree(os.path.join(root,"tests","roots","test-ext-autodoc"), srcdir)
app = SphinxTestApp("html", srcdir=sphinx_path(srcdir))
def do_autodoc(app, objtype, name, options=None):
    options = options or {}
    app.env.temp_data.setdefault("docname","index")
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(""), docoptions, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)
app.config.autoclass_content = "class"

actual = do_autodoc(app, "module", "target.private", {"members": None, "private-members": None})
print("ACTUAL", actual)
expected = [
    '',
    '.. py:module:: target.private',
    '',
    '',
    '.. py:function:: _public_function(name)',
    '   :module: target.private',
    '',
    '   public_function is a docstring().',
    '',
    '   :meta public:',
    '',
    '',
    '.. py:function:: private_function(name)',
    '   :module: target.private',
    '',
    '   private_function is a docstring().',
    '',
    '   :meta private:',
    '',
]
assert actual == expected, "Req3 mismatch"
print("Req3.1/3.2/3.3 OK: no-arg private-members -> all private documented")
sys.exit(0)
```

Attack 4 — `probe_4_nonmatch.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, shutil
root = os.getcwd()
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
from sphinx.util.docutils import LoggingReporter
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from unittest.mock import Mock
srcdir = os.path.join(tempfile.mkdtemp(), "ext-autodoc")
shutil.copytree(os.path.join(root,"tests","roots","test-ext-autodoc"), srcdir)
app = SphinxTestApp("html", srcdir=sphinx_path(srcdir))
def do_autodoc(app, objtype, name, options=None):
    options = options or {}
    app.env.temp_data.setdefault("docname","index")
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(""), docoptions, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)
app.config.autoclass_content = "class"

actual = do_autodoc(app, "module", "target.private", {"members": None, "private-members": "does_not_exist"})
print("ACTUAL", actual)
joined = "\n".join(actual)
assert "private_function" not in joined, "Req1.3 violated: unnamed private member documented"
assert "_public_function" in joined, "meta-public member should still be documented"
print("Req1.3/4.4 OK: private member absent from list is NOT documented")
sys.exit(0)
```

Attack 5 — `probe_5_named.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, shutil
root = os.getcwd()
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
from sphinx.util.docutils import LoggingReporter
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from unittest.mock import Mock
srcdir = os.path.join(tempfile.mkdtemp(), "ext-autodoc")
shutil.copytree(os.path.join(root,"tests","roots","test-ext-autodoc"), srcdir)
app = SphinxTestApp("html", srcdir=sphinx_path(srcdir))
def do_autodoc(app, objtype, name, options=None):
    options = options or {}
    app.env.temp_data.setdefault("docname","index")
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(""), docoptions, 1, state)
    doccls(bridge, name).generate()
    return list(bridge.result)
app.config.autoclass_content = "class"

actual = do_autodoc(app, "module", "target.private", {"members": None, "private-members": "private_function"})
print("ACTUAL", actual)
joined = "\n".join(actual)
assert "py:function:: private_function(name)" in joined, "Req1.2 violated: named private member not documented"
assert "private_function is a docstring()." in joined, "Req1.5 violated: docstring missing"
print("Req1.2/1.5 OK: named private member documented with full block")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_control.py`

```python
import os, sys, tempfile, shutil
root = os.getcwd()
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
from sphinx.util.docutils import LoggingReporter
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from unittest.mock import Mock

testroot = os.path.join(root, 'tests', 'roots', 'test-ext-autodoc')
srcdir = os.path.join(tempfile.mkdtemp(), 'ext-autodoc')
shutil.copytree(testroot, srcdir)
app = SphinxTestApp('html', srcdir=sphinx_path(srcdir))

def do_autodoc(app, objtype, name, options=None):
    options = options or {}
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    doccls(bridge, name).generate()
    return bridge.result

app.config.autoclass_content = 'class'
actual = list(do_autodoc(app, 'module', 'target.private',
              {"members": None, "private-members": "_public_function"}))
print("ACTUAL", actual)
expected = [
    '',
    '.. py:module:: target.private',
    '',
    '',
    '.. py:function:: _public_function(name)',
    '   :module: target.private',
    '',
    '   public_function is a docstring().',
    '',
    '   :meta public:',
    '',
]
assert actual == expected, "output mismatch"
print("Req1.2/1.3/1.5 OK: only named private member documented, full block")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: sphinx :private-members: gains explicit name-list support (issue 8035). Gold patch: change option parser bool_option->members_option for both ModuleDocumenter and ClassDocumenter, add merge_members_option, and rewrite the filter_members keep-logic to branch on private_members being None / ALL / a name-list (plus is_filtered_inherited_member for the list case).

Probe suite (all run in the instance docker image; harness reconstructs the test's do_autodoc via SphinxTestApp on the test-ext-autodoc root with target.private = {_public_function (:meta public:), private_function (:meta private:)}):
- probe_1_control (POSITIVE CONTROL, Req1.2/1.3/1.5): members=None + private-members='_public_function' -> exactly the named private member's full block. HOLDS patched, VIOLATED at base (base treats private-members as truthy bool -> documents ALL private -> mismatch). Discriminates.
- probe_2_omit (Req2.1/2.2/2.3): members=None, no private-members -> meta-public _public_function kept, meta-private private_function omitted. HOLDS patched.
- probe_3_allnoarg (Req3.1/3.2/3.3): private-members=None (no arg = ALL) -> both members documented. HOLDS patched.
- probe_4_nonmatch (Req1.3/4.4): private-members='does_not_exist' -> private_function NOT documented, _public_function still documented. HOLDS patched.
- probe_5_named (Req1.2/1.5): private-members='private_function' -> that meta-private member documented with full block. HOLDS patched.

Candidate wrong-fix: weak_partial.diff swaps only the option parser (bool_option->members_option) on both documenters but LEAVES the base filter_members keep-logic (keep = self.options.private_members and (has_doc or undoc)) untouched. With a non-empty list, the truthiness test keeps every private member regardless of the list. Applies at base_commit; runner-checked: REJECTED by probe_1_control (documents all private, not just named) and probe_4_nonmatch (documents private_function though not named); probes 2/3/5 still HOLD. This demonstrates the suite discriminates a plausible partial implementation. No requirements-conforming alternative patch was found that would fail the hidden tests, so no TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes cover Req1-4 including the SHALL-keep regressions (omit, no-arg all), all hold on the patched tree, the positive control fails at base and holds patched, and at least one wrong-fix candidate is exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_control.py`, `probe_2_omit.py`, `probe_3_allnoarg.py`, `probe_4_nonmatch.py`, `probe_5_named.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_control.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_control.py` → holds on the patched tree (good)

Attack 2 — `probe_2_omit.py` → holds on the patched tree (good)

Attack 3 — `probe_3_allnoarg.py` → holds on the patched tree (good)

Attack 4 — `probe_4_nonmatch.py` → holds on the patched tree (good)

Attack 5 — `probe_5_named.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_control.py`

```python
import os, sys, tempfile, shutil
root = os.getcwd()
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path as sphinx_path
from sphinx.util.docutils import LoggingReporter
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from unittest.mock import Mock

testroot = os.path.join(root, 'tests', 'roots', 'test-ext-autodoc')
srcdir = os.path.join(tempfile.mkdtemp(), 'ext-autodoc')
shutil.copytree(testroot, srcdir)
app = SphinxTestApp('html', srcdir=sphinx_path(srcdir))

def do_autodoc(app, objtype, name, options=None):
    options = options or {}
    app.env.temp_data.setdefault('docname', 'index')
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock(); state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    doccls(bridge, name).generate()
    return bridge.result

app.config.autoclass_content = 'class'
actual = list(do_autodoc(app, 'module', 'target.private',
              {"members": None, "private-members": "_public_function"}))
print("ACTUAL", actual)
expected = [
    '',
    '.. py:module:: target.private',
    '',
    '',
    '.. py:function:: _public_function(name)',
    '   :module: target.private',
    '',
    '   public_function is a docstring().',
    '',
    '   :meta public:',
    '',
]
assert actual == expected, "output mismatch"
print("Req1.2/1.3/1.5 OK: only named private member documented, full block")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: sphinx :private-members: gains explicit name-list support (issue 8035). Gold patch: change option parser bool_option->members_option for both ModuleDocumenter and ClassDocumenter, add merge_members_option, and rewrite the filter_members keep-logic to branch on private_members being None / ALL / a name-list (plus is_filtered_inherited_member for the list case).

Probe suite (all run in the instance docker image; harness reconstructs the test's do_autodoc via SphinxTestApp on the test-ext-autodoc root with target.private = {_public_function (:meta public:), private_function (:meta private:)}):
- probe_1_control (POSITIVE CONTROL, Req1.2/1.3/1.5): members=None + private-members='_public_function' -> exactly the named private member's full block. HOLDS patched, VIOLATED at base (base treats private-members as truthy bool -> documents ALL private -> mismatch). Discriminates.
- probe_2_omit (Req2.1/2.2/2.3): members=None, no private-members -> meta-public _public_function kept, meta-private private_function omitted. HOLDS patched.
- probe_3_allnoarg (Req3.1/3.2/3.3): private-members=None (no arg = ALL) -> both members documented. HOLDS patched.
- probe_4_nonmatch (Req1.3/4.4): private-members='does_not_exist' -> private_function NOT documented, _public_function still documented. HOLDS patched.
- probe_5_named (Req1.2/1.5): private-members='private_function' -> that meta-private member documented with full block. HOLDS patched.

Candidate wrong-fix: weak_partial.diff swaps only the option parser (bool_option->members_option) on both documenters but LEAVES the base filter_members keep-logic (keep = self.options.private_members and (has_doc or undoc)) untouched. With a non-empty list, the truthiness test keeps every private member regardless of the list. Applies at base_commit; runner-checked: REJECTED by probe_1_control (documents all private, not just named) and probe_4_nonmatch (documents private_function though not named); probes 2/3/5 still HOLD. This demonstrates the suite discriminates a plausible partial implementation. No requirements-conforming alternative patch was found that would fail the hidden tests, so no TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes cover Req1-4 including the SHALL-keep regressions (omit, no-arg all), all hold on the patched tree, the positive control fails at base and holds patched, and at least one wrong-fix candidate is exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patched logic confirmed: (non-attr private branch) private_members is None->drop, is ALL->keep, is_filtered_inherited_member->drop, else membername in private_members; undocumented & no undoc-members->drop. (attr_docs private branch) None->drop, ALL->keep, else membername in list. Metadata: ':meta private:'->isprivate=True, ':meta public:'->isprivate=False. Observable checks all HOLD on gold tree: R1 explicit list '_public_function' documents only that member (signature/module/docstring block emitted), unnamed omitted; a meta-private member ('private_function', no leading underscore) IS kept when named in the list, and unnamed public dropped — matches R1.2/R1.3/R1.5. R2 omitted: meta-public underscore member shown, meta-private/underscore member omitted — matches R2.1-2.3. R3 no-arg: all private members documented alongside public — matches R3.1-3.3. R4.1/4.2/4.3 hold by the branch structure. G-DIFF/G-RESOLVE etc. all pass; F2P test test_private_members reproduced.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the :private-members: three-shape behavior (omitted / no-arg / name-list) which is directly derivable from the public problem_statement (feature request to make :private-members: take arguments like :members:). It does NOT transmit any hidden-test artifacts: no test path/name (tests/test_ext_autodoc_private_members.py::test_private_members), no fixture id (target.private), no member name (_public_function), no verbatim docstring ('public_function is a docstring().'), and no gold-invented identifier (merge_members_option / merge_special_members_option). Mentions of :meta public: / :meta private: are pre-existing, publicly-documented Sphinx metadata behavior exercised by the PASS_TO_PASS tests, described behaviorally rather than quoted. 'signature/definition line, owning-module line, docstring' is a generic description of any autodoc output block, not the test's specific expected-output strings. Inherited-member filtering (Req 4) mirrors the gold's is_filtered_inherited_member branch but as behavioral prose — legitimate localization of the change. All content is behavioral translation, which is the intended purpose.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
