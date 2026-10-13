# P2 adversarial audit — sphinx-doc__sphinx-11510

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_poscontrol.py`, `probe_2_docname_and_list.py`, `probe_3_literal_no_event.py`, `probe_4_no_handler_regression.py`, `probe_5_structure_preserved.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_poscontrol.py` → holds on the patched tree (good)

```python
# Positive control + R1.1/R1.3/R4: with a source-read handler registered, a
# rewrite of INCLUDED (here nested: index -> baz/baz.rst -> foo.rst) rst content
# must reach the final doctree. HOLDS patched, VIOLATED at base.
import tempfile, io, sys
from pathlib import Path
from sphinx.testing.util import SphinxTestApp
from sphinx.testing import restructuredtext

srcdir = Path(tempfile.mkdtemp())
(srcdir / "conf.py").write_text("project='t'\nexclude_patterns=['_build']\n")
(srcdir / "foo.rst").write_text("The #magical foo.\n")
b = srcdir / "baz"; b.mkdir()
(b / "baz.rst").write_text("Baz\n===\n\n.. include:: foo.rst\n\nBaz was here.")
app = SphinxTestApp(srcdir=srcdir, status=io.StringIO(), warning=io.StringIO())

def h(app, doc, source):
    source[0] = source[0].replace("#magical", "amazing")
app.connect("source-read", h)

text = ".. include:: baz/baz.rst\n"
app.env.find_files(app.config, app.builder)
doctree = restructuredtext.parse(app, text, 'index')
alltext = doctree.astext()
app.cleanup()

print("doctree text:", repr(alltext))
has_rewritten = "amazing foo" in alltext
has_original = "#magical" in alltext
print("has_rewritten=", has_rewritten, "has_original=", has_original)
sys.exit(0 if (has_rewritten and not has_original) else 1)
```

Attack 2 — `probe_2_docname_and_list.py` → holds on the patched tree (good)

```python
# R1.2 + R1.3 + R2.1/R2.2: when source-read fires for an included rst file the
# docname passed must be the path2doc-derived docname (e.g. "baz/baz", not the
# raw path or absolute path), the source arg must be a single-element mutable
# list, and the offered text must be the file's own content WITHOUT internal
# marker/bookkeeping lines (here baz/baz sliced by :start-line: 4 == "\nBaz was here.").
import tempfile, io, sys
from pathlib import Path
from sphinx.testing.util import SphinxTestApp
from sphinx.testing import restructuredtext

srcdir = Path(tempfile.mkdtemp())
(srcdir / "conf.py").write_text("project='t'\nexclude_patterns=['_build']\n")
(srcdir / "foo.rst").write_text("The #magical foo.\n")
b = srcdir / "baz"; b.mkdir()
(b / "baz.rst").write_text("Baz\n===\n\n.. include:: foo.rst\n\nBaz was here.")
app = SphinxTestApp(srcdir=srcdir, status=io.StringIO(), warning=io.StringIO())

records = []
def h(app, doc, source):
    # record docname, that source is a list, its len, and the text
    records.append((doc, isinstance(source, list), len(source), source[0]))
app.connect("source-read", h)

text = ".. include:: baz/baz.rst\n   :start-line: 4\n"
app.env.find_files(app.config, app.builder)
restructuredtext.parse(app, text, 'index')
app.cleanup()

print("records:", records)
# find the record for the included file (docname baz/baz)
inc = [r for r in records if r[0] == "baz/baz"]
if not inc:
    print("FAIL: no source-read event with docname 'baz/baz'")
    sys.exit(1)
doc, is_list, ln, txt = inc[0]
print("docname ok:", doc == "baz/baz")
print("is_list:", is_list, "len:", ln)
print("offered text:", repr(txt))
ok = (doc == "baz/baz") and is_list and ln == 1 and txt == "\nBaz was here."
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_literal_no_event.py` → holds on the patched tree (good)

```python
# R3.1/R3.2: a :literal: include must NOT emit a source-read event for its
# content, and the literal content must be unchanged even with a handler that
# would otherwise rewrite it. Top-level 'index' still fires.
import tempfile, io, sys
from pathlib import Path
from sphinx.testing.util import SphinxTestApp
from sphinx.testing import restructuredtext

srcdir = Path(tempfile.mkdtemp())
(srcdir / "conf.py").write_text("project='t'\nexclude_patterns=['_build']\n")
(srcdir / "text.txt").write_text("This is #magical plain text.\n")
app = SphinxTestApp(srcdir=srcdir, status=io.StringIO(), warning=io.StringIO())

seen = []
def h(app, doc, source):
    seen.append(doc)
    source[0] = source[0].replace("#magical", "amazing")
app.connect("source-read", h)

text = ".. include:: text.txt\n   :literal:\n"
app.env.find_files(app.config, app.builder)
doctree = restructuredtext.parse(app, text, 'index')
alltext = doctree.astext()
app.cleanup()

print("seen docnames:", seen)
print("doctree text:", repr(alltext))
# no event for text.txt (as literal); literal content preserved verbatim
no_literal_event = ("text.txt" not in seen) and ("text" not in seen)
literal_preserved = "#magical plain text" in alltext
print("no_literal_event:", no_literal_event, "literal_preserved:", literal_preserved)
sys.exit(0 if (no_literal_event and literal_preserved) else 1)
```

Attack 4 — `probe_4_no_handler_regression.py` → holds on the patched tree (good)

```python
# R5.1 + R1.5 + R2.3(structure): when NO source-read handler is registered, the
# include directive must NOT emit source-read for included files, and multi-line
# / list structure of the included content must be preserved intact. We verify
# structure by comparing the doctree of an included multi-item list to a direct
# parse of the same content.
import tempfile, io, sys
from pathlib import Path
from sphinx.testing.util import SphinxTestApp
from sphinx.testing import restructuredtext
from docutils import nodes

srcdir = Path(tempfile.mkdtemp())
(srcdir / "conf.py").write_text("project='t'\nexclude_patterns=['_build']\n")
(srcdir / "multi.rst").write_text("- alpha\n- beta\n- gamma\n")
app = SphinxTestApp(srcdir=srcdir, status=io.StringIO(), warning=io.StringIO())

# No handler connected. But instrument events to be sure nothing fires.
fired = []
orig_emit = app.events.emit
def spy_emit(name, *a, **k):
    if name == "source-read":
        fired.append(a[0] if a else None)  # docname
    return orig_emit(name, *a, **k)
app.events.emit = spy_emit

text = ".. include:: multi.rst\n"
app.env.find_files(app.config, app.builder)
doctree = restructuredtext.parse(app, text, 'index')

# count bullet list items
items = len(doctree.traverse(nodes.list_item))
listtxt = doctree.astext()
app.cleanup()

# restructuredtext.parse always emits source-read for the top-level docname
# ('index'); R5.1 forbids emitting it for the INCLUDED file (docname 'multi').
included_events = [d for d in fired if d not in ("index", None)]
print("all source-read docnames:", fired)
print("included-file source-read events (must be empty):", included_events)
print("list_item count:", items)
print("text:", repr(listtxt))
ok = (len(included_events) == 0) and (items == 3) and all(w in listtxt for w in ("alpha", "beta", "gamma"))
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_structure_preserved.py` → holds on the patched tree (good)

```python
# R2.3: when a handler rewrites included content, the rewritten content must be
# parsed with the SAME physical-line and block boundaries the original produced
# (no lines merged/dropped/shifted). Included file is a 3-item bullet list; a
# handler rewrites a token in each line. Result must still be a 3-item list with
# the rewritten tokens (proves splitlines/rejoin preserves line structure).
import tempfile, io, sys
from pathlib import Path
from sphinx.testing.util import SphinxTestApp
from sphinx.testing import restructuredtext
from docutils import nodes

srcdir = Path(tempfile.mkdtemp())
(srcdir / "conf.py").write_text("project='t'\nexclude_patterns=['_build']\n")
(srcdir / "multi.rst").write_text("- alpha #x\n- beta #x\n- gamma #x\n")
app = SphinxTestApp(srcdir=srcdir, status=io.StringIO(), warning=io.StringIO())

def h(app, doc, source):
    source[0] = source[0].replace("#x", "DONE")
app.connect("source-read", h)

text = ".. include:: multi.rst\n"
app.env.find_files(app.config, app.builder)
doctree = restructuredtext.parse(app, text, 'index')
items = doctree.traverse(nodes.list_item)
alltext = doctree.astext()
app.cleanup()

print("list_item count:", len(items))
print("text:", repr(alltext))
ok = (len(items) == 3) and ("DONE" in alltext) and ("#x" not in alltext) \
     and all(w in alltext for w in ("alpha", "beta", "gamma"))
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_poscontrol.py`

```python
# Positive control + R1.1/R1.3/R4: with a source-read handler registered, a
# rewrite of INCLUDED (here nested: index -> baz/baz.rst -> foo.rst) rst content
# must reach the final doctree. HOLDS patched, VIOLATED at base.
import tempfile, io, sys
from pathlib import Path
from sphinx.testing.util import SphinxTestApp
from sphinx.testing import restructuredtext

srcdir = Path(tempfile.mkdtemp())
(srcdir / "conf.py").write_text("project='t'\nexclude_patterns=['_build']\n")
(srcdir / "foo.rst").write_text("The #magical foo.\n")
b = srcdir / "baz"; b.mkdir()
(b / "baz.rst").write_text("Baz\n===\n\n.. include:: foo.rst\n\nBaz was here.")
app = SphinxTestApp(srcdir=srcdir, status=io.StringIO(), warning=io.StringIO())

def h(app, doc, source):
    source[0] = source[0].replace("#magical", "amazing")
app.connect("source-read", h)

text = ".. include:: baz/baz.rst\n"
app.env.find_files(app.config, app.builder)
doctree = restructuredtext.parse(app, text, 'index')
alltext = doctree.astext()
app.cleanup()

print("doctree text:", repr(alltext))
has_rewritten = "amazing foo" in alltext
has_original = "#magical" in alltext
print("has_rewritten=", has_rewritten, "has_original=", has_original)
sys.exit(0 if (has_rewritten and not has_original) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-11510: Include directive must route included RST text through the source-read event. Gold patch monkeypatches StateMachine.insert_input (instance-level), guarded by a source-read listener check.

PROBE SUITE (all standalone, sphinx.testing.util.SphinxTestApp + restructuredtext.parse, no pytest). Results on gold-patched tree unless noted:
- probe_1_poscontrol (R1.1/R1.3/R4, POSITIVE CONTROL): nested include index->baz/baz.rst->foo.rst with a handler rewriting '#magical'->'amazing'; doctree must contain rewritten nested text and not the original. HOLDS patched ('The amazing foo.'), VIOLATED at base ('The #magical foo.' unchanged) -> discriminates.
- probe_2_docname_and_list (R1.2/R1.3/R2.1/R2.2): source-read fires for the included file with docname 'baz/baz' (path2doc/os_path derived), source is a single-element mutable list, and offered text is exactly the file's own content sliced by :start-line: 4 == '\nBaz was here.' with NO leading/trailing marker/bookkeeping lines. HOLDS patched; VIOLATED at base (no baz/baz event at all).
- probe_3_literal_no_event (R3.1/R3.2): a :literal: include emits NO source-read event for its content and the literal text is preserved verbatim even with a rewriting handler. HOLDS.
- probe_4_no_handler_regression (R5.1): with NO handler, no source-read event is emitted for the INCLUDED file (only the top-level 'index' fires from restructuredtext.parse), and list structure is preserved. HOLDS patched.
- probe_5_structure_preserved (R2.3): included 3-item bullet list rewritten per-line by a handler still parses as 3 list_items with rewritten tokens (splitlines/rejoin preserves physical-line/block boundaries). HOLDS.

### WRONG-FIX CANDIDATES (both apply at base_commit; both REJECTED by the suite -> suite discriminates wrong implementations):
- cand_no_marker.diff: naive community monkeypatch that joins ALL include_lines (no [:-2] marker exclusion) and does splitlines() without re-attaching the two docutils marker lines. REJECTED by probe_2: the offered text leaks the internal '.. end of inclusion from "..."' bookkeeping line (violates R2.1/R2.2). (Other probes still pass, confirming the marker-exclusion pin catches exactly this.)
- cand_no_guard.diff: drops the `if listeners.get('source-read')` guard (always monkeypatches). REJECTED by probe_4: emits a source-read event for the included 'multi' file even when no handler is registered (violates R5.1).

BASE reproduction: probe_1 (positive control) FAILS at base and HOLDS patched; probe_2 also fails at base (no included-file event). prepatch_reproduced=true.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and >=2 plausibly-wrong requirement-permissive candidates are rejected by the probe suite (no too-weak finding). NB: meta.json records G-PANEL-3=LEAKAGE (Requirement 2 transcribes the internal marker/splitlines/join algorithm) — that is a separate leakage concern, not a spec-fidelity/too-weak defect; the G-EQ spec-fidelity judgment is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_poscontrol.py`, `probe_2_docname_and_list.py`, `probe_3_literal_no_event.py`, `probe_4_no_handler_regression.py`, `probe_5_structure_preserved.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_poscontrol.py` → holds on the patched tree (good)

Attack 2 — `probe_2_docname_and_list.py` → holds on the patched tree (good)

Attack 3 — `probe_3_literal_no_event.py` → holds on the patched tree (good)

Attack 4 — `probe_4_no_handler_regression.py` → holds on the patched tree (good)

Attack 5 — `probe_5_structure_preserved.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_poscontrol.py`

```python
# Positive control + R1.1/R1.3/R4: with a source-read handler registered, a
# rewrite of INCLUDED (here nested: index -> baz/baz.rst -> foo.rst) rst content
# must reach the final doctree. HOLDS patched, VIOLATED at base.
import tempfile, io, sys
from pathlib import Path
from sphinx.testing.util import SphinxTestApp
from sphinx.testing import restructuredtext

srcdir = Path(tempfile.mkdtemp())
(srcdir / "conf.py").write_text("project='t'\nexclude_patterns=['_build']\n")
(srcdir / "foo.rst").write_text("The #magical foo.\n")
b = srcdir / "baz"; b.mkdir()
(b / "baz.rst").write_text("Baz\n===\n\n.. include:: foo.rst\n\nBaz was here.")
app = SphinxTestApp(srcdir=srcdir, status=io.StringIO(), warning=io.StringIO())

def h(app, doc, source):
    source[0] = source[0].replace("#magical", "amazing")
app.connect("source-read", h)

text = ".. include:: baz/baz.rst\n"
app.env.find_files(app.config, app.builder)
doctree = restructuredtext.parse(app, text, 'index')
alltext = doctree.astext()
app.cleanup()

print("doctree text:", repr(alltext))
has_rewritten = "amazing foo" in alltext
has_original = "#magical" in alltext
print("has_rewritten=", has_rewritten, "has_original=", has_original)
sys.exit(0 if (has_rewritten and not has_original) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-11510: Include directive must route included RST text through the source-read event. Gold patch monkeypatches StateMachine.insert_input (instance-level), guarded by a source-read listener check.

PROBE SUITE (all standalone, sphinx.testing.util.SphinxTestApp + restructuredtext.parse, no pytest). Results on gold-patched tree unless noted:
- probe_1_poscontrol (R1.1/R1.3/R4, POSITIVE CONTROL): nested include index->baz/baz.rst->foo.rst with a handler rewriting '#magical'->'amazing'; doctree must contain rewritten nested text and not the original. HOLDS patched ('The amazing foo.'), VIOLATED at base ('The #magical foo.' unchanged) -> discriminates.
- probe_2_docname_and_list (R1.2/R1.3/R2.1/R2.2): source-read fires for the included file with docname 'baz/baz' (path2doc/os_path derived), source is a single-element mutable list, and offered text is exactly the file's own content sliced by :start-line: 4 == '\nBaz was here.' with NO leading/trailing marker/bookkeeping lines. HOLDS patched; VIOLATED at base (no baz/baz event at all).
- probe_3_literal_no_event (R3.1/R3.2): a :literal: include emits NO source-read event for its content and the literal text is preserved verbatim even with a rewriting handler. HOLDS.
- probe_4_no_handler_regression (R5.1): with NO handler, no source-read event is emitted for the INCLUDED file (only the top-level 'index' fires from restructuredtext.parse), and list structure is preserved. HOLDS patched.
- probe_5_structure_preserved (R2.3): included 3-item bullet list rewritten per-line by a handler still parses as 3 list_items with rewritten tokens (splitlines/rejoin preserves physical-line/block boundaries). HOLDS.

### WRONG-FIX CANDIDATES (both apply at base_commit; both REJECTED by the suite -> suite discriminates wrong implementations):
- cand_no_marker.diff: naive community monkeypatch that joins ALL include_lines (no [:-2] marker exclusion) and does splitlines() without re-attaching the two docutils marker lines. REJECTED by probe_2: the offered text leaks the internal '.. end of inclusion from "..."' bookkeeping line (violates R2.1/R2.2). (Other probes still pass, confirming the marker-exclusion pin catches exactly this.)
- cand_no_guard.diff: drops the `if listeners.get('source-read')` guard (always monkeypatches). REJECTED by probe_4: emits a source-read event for the included 'multi' file even when no handler is registered (violates R5.1).

BASE reproduction: probe_1 (positive control) FAILS at base and HOLDS patched; probe_2 also fails at base (no included-file event). prepatch_reproduced=true.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and >=2 plausibly-wrong requirement-permissive candidates are rejected by the probe suite (no too-weak finding). NB: meta.json records G-PANEL-3=LEAKAGE (Requirement 2 transcribes the internal marker/splitlines/join algorithm) — that is a separate leakage concern, not a spec-fidelity/too-weak defect; the G-EQ spec-fidelity judgment is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch monkey-patches StateMachine.insert_input on the instance so RST-parsed includes route through source-read; the requirements' modeling boundary (RST-only, marker-line stripping, docname derivation, listener guard, nested includes) matches the F2P tests test_include_source_read_event and test_include_source_read_event_nested_includes and my independent probes. probe.py PASS on patched (keys=['baz/baz','index'], text.txt absent, baz repr '\nBaz was here.'); probe_base.py VIOLATED at base (baz/baz not offered) — confirms discrimination.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md contains no hidden-test artifacts: no test function names (test_include_source_read_event / _nested_includes), no fixture filenames (baz/baz.rst, foo.rst, text.txt), no literal test strings ('#magical'->'amazing', 'The amazing foo.', '\nBaz was here.', ':start-line: 4', doctree.children==3), and no gold-invented identifiers (StateMachine.insert_input monkey-patch, include_lines[:-2] markers, env.path2doc/os_path). The document localizes to the Include directive in sphinx/directives/other.py and the source-read event — both fully public in the problem_statement/hints. The three non-obvious behaviors it pins (literal includes not emitted, nested includes covered, marker-line/provenance bookkeeping excluded from the offered text) are expressed as behavioral requirements, not as verbatim tests or case enumerations mirroring parametrization; they are legitimate translations of expected behavior derivable from the bug report (include directive, nested content, only RST parsed). No line reconstructs the hidden tests or gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
