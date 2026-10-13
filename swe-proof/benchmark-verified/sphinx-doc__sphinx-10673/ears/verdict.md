# P2 adversarial audit — sphinx-doc__sphinx-10673

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_posctrl.py`, `probe_2_order_titles.py`, `probe_3_explicit_title.py`, `probe_4_glob_exclude.py`, `probe_5_regression_warn.py`, `probe_6_fignum.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_posctrl.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_posctrl.py` → holds on the patched tree (good)

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n   :maxdepth: 1\n   :caption: Indices and tables\n\n"
 "   genindex\n   modindex\n   search\n")
warn=io.StringIO()
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=warn,status=None,freshenv=True)
app.build()
w=warn.getvalue(); print("WARNINGS:",repr(w))
bad=[l for l in w.splitlines() if "nonexisting document" in l and any(n in l for n in ("genindex","modindex","search"))]
if bad: print("FAIL bad warnings",bad); raise SystemExit(1)
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
ok=('genindex.html' in wrap) and ('search.html' in wrap) and ('py-modindex.html' in wrap)
print("wrapper links genindex/modindex/search present:",ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2_order_titles.py` → holds on the patched tree (good)

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n\n   genindex\n   modindex\n   search\n")
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=io.StringIO(),status=None,freshenv=True)
app.build()
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
order=re.findall(r'href="(genindex\.html|py-modindex\.html|search\.html)"',wrap)
print("wrapper href order:",order)
titles_ok=all(t in wrap for t in ("Index","Module Index","Search Page"))
print("default titles present:",titles_ok)
exp=["genindex.html","py-modindex.html","search.html"]
order_ok=order==exp
print("order_ok:",order_ok)
raise SystemExit(0 if (titles_ok and order_ok) else 1)
```

Attack 3 — `probe_3_explicit_title.py` → holds on the patched tree (good)

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n\n   MyIndexLink <genindex>\n")
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=io.StringIO(),status=None,freshenv=True)
app.build()
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
present=('MyIndexLink' in wrap) and ('genindex.html' in wrap)
# default section title 'Index' must NOT be the link text here
default_used='>Index<' in wrap
print("wrapper explicit-title link present:",present,"| default 'Index' used:",default_used)
raise SystemExit(0 if (present and not default_used) else 1)
```

Attack 4 — `probe_4_glob_exclude.py` → holds on the patched tree (good)

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n   :glob:\n\n   *\n")
open(os.path.join(src,"foo.rst"),"w").write("Foo\n===\n\ncontent\n")
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=io.StringIO(),status=None,freshenv=True)
app.build()
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
foo_linked='foo.html' in wrap
gen_linked=any(x in wrap for x in ('genindex.html','search.html','py-modindex.html'))
print("wrapper foo linked:",foo_linked,"| generated auto-included:",gen_linked)
raise SystemExit(0 if (foo_linked and not gen_linked) else 1)
```

Attack 5 — `probe_5_regression_warn.py` → holds on the patched tree (good)

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n\n   foo\n   nope_missing\n")
open(os.path.join(src,"foo.rst"),"w").write("Foo\n===\n\ncontent\n")
warn=io.StringIO()
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=warn,status=None,freshenv=True)
app.build()
w=warn.getvalue(); print("WARNINGS:",repr(w))
warned=any("nonexisting document" in l and "nope_missing" in l for l in w.splitlines())
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
foo_ok='foo.html' in wrap
print("bogus warned:",warned,"| real doc foo linked:",foo_ok)
raise SystemExit(0 if (warned and foo_ok) else 1)
```

Attack 6 — `probe_6_fignum.py` → holds on the patched tree (good)

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\nnumfig=True\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n   :numbered:\n\n   genindex\n   search\n   foo\n")
open(os.path.join(src,"foo.rst"),"w").write("Foo\n===\n\ncontent\n")
warn=io.StringIO()
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=warn,status=None,freshenv=True)
app.build()   # must not raise
w=warn.getvalue(); print("WARNINGS:",repr(w))
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
ok=('genindex.html' in wrap) and ('foo.html' in wrap)
bad=[l for l in w.splitlines() if "nonexisting document" in l and any(n in l for n in ("genindex","search"))]
print("wrapper links ok:",ok,"| bad warns:",bad)
raise SystemExit(0 if (ok and not bad) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_posctrl.py`

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n   :maxdepth: 1\n   :caption: Indices and tables\n\n"
 "   genindex\n   modindex\n   search\n")
warn=io.StringIO()
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=warn,status=None,freshenv=True)
app.build()
w=warn.getvalue(); print("WARNINGS:",repr(w))
bad=[l for l in w.splitlines() if "nonexisting document" in l and any(n in l for n in ("genindex","modindex","search"))]
if bad: print("FAIL bad warnings",bad); raise SystemExit(1)
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
ok=('genindex.html' in wrap) and ('search.html' in wrap) and ('py-modindex.html' in wrap)
print("wrapper links genindex/modindex/search present:",ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all built via a real Sphinx HTML build inside the instance image (sphinx 5.2.0 / py3.9), each scoping HTML checks to the <div class=toctree-wrapper> region to avoid theme relbar contamination (genindex/search links appear in every page's navbar otherwise — an early un-scoped draft produced false failures).

Probe → criterion → result (PATCHED / BASE / weak_partial):
- probe_1_posctrl (Req 1.1 no 'nonexisting document' warning for genindex/modindex/search + Req 3.1 links rendered in wrapper): HOLDS / VIOLATED / VIOLATED. This is the positive control — discriminates base vs patched.
- probe_2_order_titles (Req 1.2/1.4 one entry per name in listed order + Req 3.2 default section titles Index/Module Index/Search Page): HOLDS / VIOLATED / VIOLATED.
- probe_3_explicit_title (Req 3.3 explicit 'MyIndexLink <genindex>' title used, default 'Index' NOT used): HOLDS / VIOLATED / VIOLATED.
- probe_4_glob_exclude (Req 2.1 glob '*' includes foo but NOT generated names): HOLDS / HOLDS(base) / HOLDS. Not discriminating on its own (base also excludes generated names since they aren't in found_docs) but pins the anti-regression that the fix must not start auto-globbing them.
- probe_5_regression_warn (Req 5.1/5.2 real doc appended, bogus 'nope_missing' still warns nonexisting): HOLDS / HOLDS / HOLDS. Regression guard.
- probe_6_fignum (Req 4 numbered toctree linking genindex/search builds without error and still links them; no nonexisting warns): HOLDS / VIOLATED / VIOLATED(raises during emit).

Wrong-fix candidate weak_partial.diff = gold patch to sphinx/directives/other.py ONLY (accept names + warning suppression + glob exclusion), omitting the adapters/toctree.py and collectors/toctree.py hunks. The probe suite REJECTS it: probe_1/2/3 fail (names accepted so no warning, but no reference node is rendered → no links) and probe_6 fails (figure-numbering walk recurses into genindex/search as if source docs and crashes). This demonstrates the suite discriminates a plausible partial reading of Req 1 that ignores Reqs 3 and 4.

All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and rejected. Floor met.

Caveat (out of G-EQ scope, informational): meta.json records a G-PANEL-2 (faithfulness) fail regarding Req 2.3 vs the code's warning guard when a glob matches only generated names (`if not docnames`, where docnames now includes generated names). That is a spec-faithfulness nuance, not a too-weak/too-strong equivalence defect, and does not affect the G-EQ verdict; I did not probe it here since it concerns wording of the 'didn't match' warning condition rather than a behavior the requirements mandate the gold code lacks.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_posctrl.py`, `probe_2_order_titles.py`, `probe_3_explicit_title.py`, `probe_4_glob_exclude.py`, `probe_5_regression_warn.py`, `probe_6_fignum.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_posctrl.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_posctrl.py` → holds on the patched tree (good)

Attack 2 — `probe_2_order_titles.py` → holds on the patched tree (good)

Attack 3 — `probe_3_explicit_title.py` → holds on the patched tree (good)

Attack 4 — `probe_4_glob_exclude.py` → holds on the patched tree (good)

Attack 5 — `probe_5_regression_warn.py` → holds on the patched tree (good)

Attack 6 — `probe_6_fignum.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_posctrl.py`

```python
import os, tempfile, io, re
from sphinx.application import Sphinx
src=tempfile.mkdtemp(); out=tempfile.mkdtemp()
open(os.path.join(src,"conf.py"),"w").write("project='t'\nextensions=[]\n")
open(os.path.join(src,"index.rst"),"w").write(
 "Title\n=====\n\n.. toctree::\n   :maxdepth: 1\n   :caption: Indices and tables\n\n"
 "   genindex\n   modindex\n   search\n")
warn=io.StringIO()
app=Sphinx(src,src,out,os.path.join(out,".doctree"),"html",warning=warn,status=None,freshenv=True)
app.build()
w=warn.getvalue(); print("WARNINGS:",repr(w))
bad=[l for l in w.splitlines() if "nonexisting document" in l and any(n in l for n in ("genindex","modindex","search"))]
if bad: print("FAIL bad warnings",bad); raise SystemExit(1)
html=open(os.path.join(out,"index.html")).read()
m=re.search(r'<div class="toctree-wrapper.*?</div>',html,re.S); wrap=m.group(0) if m else ""
ok=('genindex.html' in wrap) and ('search.html' in wrap) and ('py-modindex.html' in wrap)
print("wrapper links genindex/modindex/search present:",ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all built via a real Sphinx HTML build inside the instance image (sphinx 5.2.0 / py3.9), each scoping HTML checks to the <div class=toctree-wrapper> region to avoid theme relbar contamination (genindex/search links appear in every page's navbar otherwise — an early un-scoped draft produced false failures).

Probe → criterion → result (PATCHED / BASE / weak_partial):
- probe_1_posctrl (Req 1.1 no 'nonexisting document' warning for genindex/modindex/search + Req 3.1 links rendered in wrapper): HOLDS / VIOLATED / VIOLATED. This is the positive control — discriminates base vs patched.
- probe_2_order_titles (Req 1.2/1.4 one entry per name in listed order + Req 3.2 default section titles Index/Module Index/Search Page): HOLDS / VIOLATED / VIOLATED.
- probe_3_explicit_title (Req 3.3 explicit 'MyIndexLink <genindex>' title used, default 'Index' NOT used): HOLDS / VIOLATED / VIOLATED.
- probe_4_glob_exclude (Req 2.1 glob '*' includes foo but NOT generated names): HOLDS / HOLDS(base) / HOLDS. Not discriminating on its own (base also excludes generated names since they aren't in found_docs) but pins the anti-regression that the fix must not start auto-globbing them.
- probe_5_regression_warn (Req 5.1/5.2 real doc appended, bogus 'nope_missing' still warns nonexisting): HOLDS / HOLDS / HOLDS. Regression guard.
- probe_6_fignum (Req 4 numbered toctree linking genindex/search builds without error and still links them; no nonexisting warns): HOLDS / VIOLATED / VIOLATED(raises during emit).

Wrong-fix candidate weak_partial.diff = gold patch to sphinx/directives/other.py ONLY (accept names + warning suppression + glob exclusion), omitting the adapters/toctree.py and collectors/toctree.py hunks. The probe suite REJECTS it: probe_1/2/3 fail (names accepted so no warning, but no reference node is rendered → no links) and probe_6 fails (figure-numbering walk recurses into genindex/search as if source docs and crashes). This demonstrates the suite discriminates a plausible partial reading of Req 1 that ignores Reqs 3 and 4.

All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and rejected. Floor met.

Caveat (out of G-EQ scope, informational): meta.json records a G-PANEL-2 (faithfulness) fail regarding Req 2.3 vs the code's warning guard when a glob matches only generated names (`if not docnames`, where docnames now includes generated names). That is a spec-faithfulness nuance, not a too-weak/too-strong equivalence defect, and does not affect the G-EQ verdict; I did not probe it here since it concerns wording of the 'didn't match' warning condition rather than a behavior the requirements mandate the gold code lacks.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified against gold-patched tree in instance image via nl_attack probe (RESULT: PASS): labels sourced from std domain initial_data['labels'].keys(); all_docnames = found_docs.copy() | generated_docnames; glob loop `if docname in generated_docnames: continue`; explicit-entry check uses `found_docs | generated_docnames`; warning guarded by `if not docnames:`. std.py initial label table confirmed: genindex->('genindex','',Index), modindex->('py-modindex','',Module Index), search->('search','',Search Page). Req 1 (explicit accept, order, null-title (None,docname) tuples, label-table sourcing), Req 3 (adapter refuri=registered docname, sectionname title fallback, no subitems), Req 4 (assign_figure_numbers skips generated), and Req 5 (preserved ordinary/self/URL/dup behavior) all match the gold patch's changed observable behavior with correct biconditional modeling boundaries. The earlier UNFAITHFUL verdict was resolved by the subsequent requirements edit.

Counterexample / evidence:

```
Glob pattern `sea*` in a non-glob-matched project: gold code computes docnames=['search'] (truthy, since all_docnames includes 'search'), loop skips it (no entry), and `if not docnames:` is False so NO warning fires. Req 2.4 mandates exactly this (no entry, no warning); Req 2.3's warning applies only when docnames is empty. No divergence.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements name the three modified source functions/files (parse_content in directives/other.py, TocTreeAdapter.resolve inner helper in adapters/toctree.py, assign_figure_numbers in collectors/toctree.py) and the std-domain label table — all legitimate localization drawn from public sphinx source, not from the hidden test. The three page names (genindex/modindex/search), the caption 'Indices and tables', the ordering, and the 'nonexisting document' warning all come from the PUBLIC problem_statement. The (null-title, name) entry model in Req 1.3/1.4 mirrors the problem_statement's own example, not the test's assertion; the fix-invented identifier `generated_docnames` never appears. No test file path/name (tests/test_environment_toctree.py::test_toctree_index), no testroot name (toctree-index), no XML-builder detail, no assert_node structure, and no verbatim gold-patch code are reproduced. Reqs 2 (glob exclusion) and 4 (figure-numbering skip) describe gold-edit behavior NOT even exercised by the single FAIL_TO_PASS test, so they are behavioral description rather than test reconstruction. The document translates behavior; it does not transmit the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
