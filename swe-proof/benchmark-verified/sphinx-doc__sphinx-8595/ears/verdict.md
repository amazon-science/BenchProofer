# P2 adversarial audit — sphinx-doc__sphinx-8595

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, textwrap, shutil
srcdir = tempfile.mkdtemp()
pkgdir = os.path.join(srcdir, "pkgmod")
os.makedirs(pkgdir)
# a module with docstring, __all__=[], and members
open(os.path.join(srcdir,"target.py"),"w").write(textwrap.dedent('''
    """MODULE_DOCSTRING_MARKER."""
    __all__ = []
    def foo():
        """foo doc"""
    def bar():
        """bar doc"""
'''))
open(os.path.join(srcdir,"conf.py"),"w").write("extensions=['sphinx.ext.autodoc']\nmaster_doc='index'\n")
open(os.path.join(srcdir,"index.rst"),"w").write(".. automodule:: target\n   :members:\n")
sys.path.insert(0, srcdir)

from sphinx.application import Sphinx
outdir=os.path.join(srcdir,"_build"); doctree=os.path.join(srcdir,"_dt")
app=Sphinx(srcdir, srcdir, outdir, doctree, "text", status=None, warning=sys.stderr)
app.build()
out=open(os.path.join(outdir,"index.txt")).read()
print("OUTPUT>>>")
print(out)
print("<<<")
has_doc = "MODULE_DOCSTRING_MARKER" in out
has_foo = "foo" in out
has_bar = "bar" in out
print("has_docstring=",has_doc,"has_foo=",has_foo,"has_bar=",has_bar)
ok = has_doc and (not has_foo) and (not has_bar)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys

from sphinx.ext.autodoc import ModuleDocumenter, ObjectMember
def _obj(n):
    f=lambda:0
    f.__name__=n
    return f
class _Stub: pass
def call(all_, member_names, want_all=True, opt_members=None):
    s=_Stub()
    mm={n:ObjectMember(n,_obj(n)) for n in member_names}
    s.get_module_members=lambda: mm
    s.__all__=all_
    s.object=_obj("themodule")
    class O: pass
    o=O(); o.members=opt_members
    s.options=o
    check_module, ret = ModuleDocumenter.get_object_members(s, want_all)
    return check_module, ret, mm

check_module, ret, mm = call([], ["a","b","c"], want_all=True)
names=[r.__name__ for r in ret]
skipped=[getattr(r,'skipped',False) for r in ret]
print("empty __all__: check_module=",check_module," returned=",names," skipped=",skipped)
ok = (check_module is False) and set(names)=={"a","b","c"} and all(skipped)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys

from sphinx.ext.autodoc import ModuleDocumenter, ObjectMember
def _obj(n):
    f=lambda:0
    f.__name__=n
    return f
class _Stub: pass
def call(all_, member_names, want_all=True, opt_members=None):
    s=_Stub()
    mm={n:ObjectMember(n,_obj(n)) for n in member_names}
    s.get_module_members=lambda: mm
    s.__all__=all_
    s.object=_obj("themodule")
    class O: pass
    o=O(); o.members=opt_members
    s.options=o
    check_module, ret = ModuleDocumenter.get_object_members(s, want_all)
    return check_module, ret, mm

check_module, ret, mm = call(None, ["a","b"], want_all=True)
names=[r.__name__ for r in ret]
skipped=[getattr(r,'skipped',False) for r in ret]
print("None __all__: check_module=",check_module," returned=",names," skipped=",skipped)
ok = (check_module is True) and set(names)=={"a","b"} and not any(skipped)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys

from sphinx.ext.autodoc import ModuleDocumenter, ObjectMember
def _obj(n):
    f=lambda:0
    f.__name__=n
    return f
class _Stub: pass
def call(all_, member_names, want_all=True, opt_members=None):
    s=_Stub()
    mm={n:ObjectMember(n,_obj(n)) for n in member_names}
    s.get_module_members=lambda: mm
    s.__all__=all_
    s.object=_obj("themodule")
    class O: pass
    o=O(); o.members=opt_members
    s.options=o
    check_module, ret = ModuleDocumenter.get_object_members(s, want_all)
    return check_module, ret, mm

check_module, ret, mm = call(["a"], ["a","b"], want_all=True)
byname={r.__name__:getattr(r,'skipped',False) for r in ret}
print("__all__=['a']: check_module=",check_module," returned=",list(byname.keys())," skipped_map=",byname)
ok = (check_module is False) and set(byname)=={"a","b"} and byname["a"]==False and byname["b"]==True
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys

from sphinx.ext.autodoc import ModuleDocumenter, ObjectMember
def _obj(n):
    f=lambda:0
    f.__name__=n
    return f
class _Stub: pass
def call(all_, member_names, want_all=True, opt_members=None):
    s=_Stub()
    mm={n:ObjectMember(n,_obj(n)) for n in member_names}
    s.get_module_members=lambda: mm
    s.__all__=all_
    s.object=_obj("themodule")
    class O: pass
    o=O(); o.members=opt_members
    s.options=o
    check_module, ret = ModuleDocumenter.get_object_members(s, want_all)
    return check_module, ret, mm

check_module, ret, mm = call(None, ["a","b","c"], want_all=False, opt_members=["c","missing","a"])
names=[r.__name__ for r in ret]
print("requested-by-name: check_module=",check_module," returned_in_order=",names)
ok = (check_module is False) and names==["c","a"]
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import os, sys, tempfile, textwrap, shutil
srcdir = tempfile.mkdtemp()
pkgdir = os.path.join(srcdir, "pkgmod")
os.makedirs(pkgdir)
# a module with docstring, __all__=[], and members
open(os.path.join(srcdir,"target.py"),"w").write(textwrap.dedent('''
    """MODULE_DOCSTRING_MARKER."""
    __all__ = []
    def foo():
        """foo doc"""
    def bar():
        """bar doc"""
'''))
open(os.path.join(srcdir,"conf.py"),"w").write("extensions=['sphinx.ext.autodoc']\nmaster_doc='index'\n")
open(os.path.join(srcdir,"index.rst"),"w").write(".. automodule:: target\n   :members:\n")
sys.path.insert(0, srcdir)

from sphinx.application import Sphinx
outdir=os.path.join(srcdir,"_build"); doctree=os.path.join(srcdir,"_dt")
app=Sphinx(srcdir, srcdir, outdir, doctree, "text", status=None, warning=sys.stderr)
app.build()
out=open(os.path.join(outdir,"index.txt")).read()
print("OUTPUT>>>")
print(out)
print("<<<")
has_doc = "MODULE_DOCSTRING_MARKER" in out
has_foo = "foo" in out
has_bar = "bar" in out
print("has_docstring=",has_doc,"has_foo=",has_foo,"has_bar=",has_bar)
ok = has_doc and (not has_foo) and (not has_bar)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-8595: automodule must honor an empty __all__. Gold patch changes `if not self.__all__:` to `if self.__all__ is None:` in ModuleDocumenter.get_object_members.

Probes (all standalone python, repo package only):
- probe_1 (POSITIVE CONTROL, end-to-end): builds a real Sphinx text app for a module with docstring, __all__=[], and members foo/bar under `.. automodule:: :members:`. Encodes Req 2.1 (no member entries) + Req 2.2 (module docstring still present). PATCHED: HOLDS (only MODULE_DOCSTRING_MARKER, no foo/bar). BASE: VIOLATED (foo+bar documented). => discriminates.
- probe_2 (Req 1.1/1.2/1.3 + 2.3): empty __all__ via unit call to get_object_members => check_module==False AND all 3 discovered members returned-and-marked-skipped. PATCHED HOLDS; BASE VIOLATED (base returns check_module=True, none skipped). Second discriminating probe.
- probe_3 (Req 3.1/3.2 regression): __all__ absent (None) => check_module==True, all members kept, none skipped. HOLDS on both trees (regression preserved).
- probe_4 (Req 4.1/4.3 regression): __all__=['a'], members a,b => check_module==False, both kept, b marked skipped, a not. HOLDS on both.
- probe_5 (Req 5.1/5.2 regression): want_all=False, options.members=['c','missing','a'], discovered a,b,c => returns ['c','a'] in requested order, missing omitted, check_module==False. HOLDS on both.

CANDIDATE PATCH exercised — cand_lazy.diff: the naive 'return False, []' fix for empty __all__ (documents no members, would pass the F2P test and probe_1's e2e output check) but does NOT return-and-mark-skip the discovered members. Result: probe_2 REJECTS it (returned=[], skipped=[]), probes 1/3/4/5 HOLD. This proves the suite discriminates a plausibly-wrong implementation on the Req 2.3 boundary; it is NOT a too-weak finding (rejected, not passing).

Verdict SOUND: 5 distinct probes all hold on the patched tree; positive control discriminates (base VIOLATED, patched HOLDS, prepatch reproduced); the requirements-plausible lazy candidate is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import os, sys, tempfile, textwrap, shutil
srcdir = tempfile.mkdtemp()
pkgdir = os.path.join(srcdir, "pkgmod")
os.makedirs(pkgdir)
# a module with docstring, __all__=[], and members
open(os.path.join(srcdir,"target.py"),"w").write(textwrap.dedent('''
    """MODULE_DOCSTRING_MARKER."""
    __all__ = []
    def foo():
        """foo doc"""
    def bar():
        """bar doc"""
'''))
open(os.path.join(srcdir,"conf.py"),"w").write("extensions=['sphinx.ext.autodoc']\nmaster_doc='index'\n")
open(os.path.join(srcdir,"index.rst"),"w").write(".. automodule:: target\n   :members:\n")
sys.path.insert(0, srcdir)

from sphinx.application import Sphinx
outdir=os.path.join(srcdir,"_build"); doctree=os.path.join(srcdir,"_dt")
app=Sphinx(srcdir, srcdir, outdir, doctree, "text", status=None, warning=sys.stderr)
app.build()
out=open(os.path.join(outdir,"index.txt")).read()
print("OUTPUT>>>")
print(out)
print("<<<")
has_doc = "MODULE_DOCSTRING_MARKER" in out
has_foo = "foo" in out
has_bar = "bar" in out
print("has_docstring=",has_doc,"has_foo=",has_foo,"has_bar=",has_bar)
ok = has_doc and (not has_foo) and (not has_bar)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-8595: automodule must honor an empty __all__. Gold patch changes `if not self.__all__:` to `if self.__all__ is None:` in ModuleDocumenter.get_object_members.

Probes (all standalone python, repo package only):
- probe_1 (POSITIVE CONTROL, end-to-end): builds a real Sphinx text app for a module with docstring, __all__=[], and members foo/bar under `.. automodule:: :members:`. Encodes Req 2.1 (no member entries) + Req 2.2 (module docstring still present). PATCHED: HOLDS (only MODULE_DOCSTRING_MARKER, no foo/bar). BASE: VIOLATED (foo+bar documented). => discriminates.
- probe_2 (Req 1.1/1.2/1.3 + 2.3): empty __all__ via unit call to get_object_members => check_module==False AND all 3 discovered members returned-and-marked-skipped. PATCHED HOLDS; BASE VIOLATED (base returns check_module=True, none skipped). Second discriminating probe.
- probe_3 (Req 3.1/3.2 regression): __all__ absent (None) => check_module==True, all members kept, none skipped. HOLDS on both trees (regression preserved).
- probe_4 (Req 4.1/4.3 regression): __all__=['a'], members a,b => check_module==False, both kept, b marked skipped, a not. HOLDS on both.
- probe_5 (Req 5.1/5.2 regression): want_all=False, options.members=['c','missing','a'], discovered a,b,c => returns ['c','a'] in requested order, missing omitted, check_module==False. HOLDS on both.

CANDIDATE PATCH exercised — cand_lazy.diff: the naive 'return False, []' fix for empty __all__ (documents no members, would pass the F2P test and probe_1's e2e output check) but does NOT return-and-mark-skip the discovered members. Result: probe_2 REJECTS it (returned=[], skipped=[]), probes 1/3/4/5 HOLD. This proves the suite discriminates a plausibly-wrong implementation on the Req 2.3 boundary; it is NOT a too-weak finding (rejected, not passing).

Verdict SOUND: 5 distinct probes all hold on the patched tree; positive control discriminates (base VIOLATED, patched HOLDS, prepatch reproduced); the requirements-plausible lazy candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified in the instance image: base_commit has buggy `if not self.__all__:` (empty __all__ conflated with absent -> all members documented, the reported bug); patched tree has `if self.__all__ is None:`. Requirements model the full changed observable behavior biconditionally (absent/empty/named/by-name), not a narrow single-branch slice — the modeling boundary is correct. No invented, forbidden-but-present, or mandated-but-absent behavior found. Note: harness stdout mangles newlines to CR; recovered full source via cat -v | tr '\r' '\n'.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the None-vs-empty __all__ distinction, which is the public bug (problem_statement: 'empty __all__ attribute is ignored') restated behaviorally, matching the gold edit's intent without quoting it. All named entities (sphinx/ext/autodoc/__init__.py, ModuleDocumenter.get_object_members, import_object, __all__, the __module__/check_module 'implicit origin-based check') are legitimate localization derivable from the public source, not from hidden tests. Req 2.2's 'directive header and module's own docstring' parallels the test's asserted output but is stated generically — no verbatim strings, no 'target.empty_all' module name, no 'docsting of empty_all module.' text, no test name (test_empty_all) or path. Reqs 4/5 (populated __all__, by-name requests) describe pre-existing get_object_members behavior visible in source, not any hidden test (only one FAIL_TO_PASS case exists), so no parametrization mirroring. No test-shaped enumeration, no fix-invented identifiers.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
