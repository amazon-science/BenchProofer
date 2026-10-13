# P2 adversarial audit — sphinx-doc__sphinx-7440

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
# Req 1 (AC1,2,3): glossary terms registered under case-preserving key;
# case-distinct terms both registered, no duplicate warning.
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.testing import restructuredtext

srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
warning = StringIO()
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=warning)

text = (".. glossary::\n\n"
        "   MySQL\n"
        "       a database\n\n"
        "   mysql\n"
        "       a command\n")
restructuredtext.parse(app, text)

objects = list(app.env.get_domain("std").get_objects())
names = [o[0] for o in objects if o[2] == "term"]
print("term names:", names)
warn = warning.getvalue()
print("warnings:", repr(warn))

ok = ("MySQL" in names and "mysql" in names
      and "duplicate" not in warn.lower())
# also ensure no lowercased-only collapse: exactly two distinct term objs
distinct = set(names)
ok = ok and {"MySQL", "mysql"} <= distinct
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2 (AC1,2): index entry text equals original case-preserved term text,
# and equals the registered object name.
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.testing import restructuredtext
from sphinx import addnodes

srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=StringIO())

text = (".. glossary::\n\n"
        "   MySQL\n"
        "       a database\n")
doctree = restructuredtext.parse(app, text)

# find index nodes
idx_entries = []
for node in doctree.traverse(addnodes.index):
    idx_entries.extend(node['entries'])
print("index entries:", idx_entries)
# entries tuples: (type, entry_text, target, main, key)
texts = [e[1] for e in idx_entries]
targets = [e[2] for e in idx_entries]
print("index texts:", texts, "targets:", targets)

objects = list(app.env.get_domain("std").get_objects())
term_names = [o[0] for o in objects if o[2] == "term"]

ok = ("MySQL" in texts                         # AC1: case preserved in index
      and "mysql" not in texts                 # no case-folded variant
      and "MySQL" in term_names                 # AC2: object name matches
      and any(t == "term-MySQL" for t in targets))  # target uses preserved text
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3 (AC1,2): term xref resolves case-sensitively — a reference to "MySQL"
# resolves to the MySQL term, and does NOT collapse "mysql"->"MySQL".
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.domains.std import StandardDomain
from sphinx.roles import XRefRole

# 1. structural: the 'term' role must NOT be lowercase-folding.
role = StandardDomain.roles['term']
print("term role:", role, "lowercase=", getattr(role, "lowercase", None))
role_ok = getattr(role, "lowercase", False) is False

# 2. behavioral: register two case-distinct terms; resolve_xref for "MySQL"
srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
from sphinx.testing import restructuredtext
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=StringIO())
text = (".. glossary::\n\n"
        "   MySQL\n"
        "       a database\n\n"
        "   mysql\n"
        "       a command\n")
restructuredtext.parse(app, text)
std = app.env.get_domain("std")

# std.objects keyed by (objtype, name); ensure case-distinct keys exist
objs = {(o[2], o[0]) for o in std.get_objects()}
print("has ('term','MySQL'):", ('term','MySQL') in objs,
      " ('term','mysql'):", ('term','mysql') in objs)
behav_ok = ('term','MySQL') in objs and ('term','mysql') in objs

ok = role_ok and behav_ok
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4 AC1: exact same term text defined twice -> duplicate-term warning.
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.testing import restructuredtext

srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
warning = StringIO()
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=warning)

text = (".. glossary::\n\n"
        "   dup\n"
        "       first\n\n"
        "   dup\n"
        "       second\n")
restructuredtext.parse(app, text)
warn = warning.getvalue()
print("warnings:", repr(warn))
ok = "duplicate" in warn.lower() and "dup" in warn
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4 AC3 & AC5: classifier ' : classifier' produces term from term part only;
# multiple term lines share one definition.
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.testing import restructuredtext
from docutils import nodes

srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=StringIO())

text = (".. glossary::\n\n"
        "   termA : classifierX\n"
        "       shared def\n\n"
        "   multi1\n"
        "   multi2\n"
        "       one def\n")
doctree = restructuredtext.parse(app, text)

term_texts = [t.astext() for t in doctree.traverse(nodes.term)]
print("term texts:", term_texts)

objects = list(app.env.get_domain("std").get_objects())
names = sorted(o[0] for o in objects if o[2] == "term")
print("registered term names:", names)

# classifier stripped: term node text is 'termA', not 'termA : classifierX'
classifier_ok = ("termA" in term_texts
                 and not any(":" in t for t in term_texts))
# multiple term lines both registered
multi_ok = "multi1" in names and "multi2" in names
ok = classifier_ok and multi_ok
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4 AC4: comments ignored; sorted option preserves ordering/grouping.
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.testing import restructuredtext
from docutils import nodes

srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
warning = StringIO()
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=warning)

text = (".. glossary::\n   :sorted:\n\n"
        "   .. a comment\n\n"
        "   Zebra\n"
        "       z\n\n"
        "   apple\n"
        "       a\n")
doctree = restructuredtext.parse(app, text)
term_texts = [t.astext() for t in doctree.traverse(nodes.term)]
print("term texts:", term_texts)
warn = warning.getvalue()
print("warnings:", repr(warn))

# comment must not appear as a term
no_comment = not any("comment" in t for t in term_texts)
# sorted: case-insensitive sort -> apple before Zebra
sorted_ok = term_texts == sorted(term_texts, key=lambda x: x.lower())
# both preserved-case terms present
present = "Zebra" in term_texts and "apple" in term_texts
# ignore unrelated env warnings (e.g. 'meta' node already registered);
# require no glossary/term-structure warnings.
bad = [ln for ln in warn.splitlines()
       if ("glossary" in ln.lower() or "comment" in ln.lower()
           or "duplicate term" in ln.lower())]
print("glossary-relevant warnings:", bad)
ok = no_comment and sorted_ok and present and not bad
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1 (AC1,2,3): glossary terms registered under case-preserving key;
# case-distinct terms both registered, no duplicate warning.
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.testing import restructuredtext

srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
warning = StringIO()
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=warning)

text = (".. glossary::\n\n"
        "   MySQL\n"
        "       a database\n\n"
        "   mysql\n"
        "       a command\n")
restructuredtext.parse(app, text)

objects = list(app.env.get_domain("std").get_objects())
names = [o[0] for o in objects if o[2] == "term"]
print("term names:", names)
warn = warning.getvalue()
print("warnings:", repr(warn))

ok = ("MySQL" in names and "mysql" in names
      and "duplicate" not in warn.lower())
# also ensure no lowercased-only collapse: exactly two distinct term objs
distinct = set(names)
ok = ok and {"MySQL", "mysql"} <= distinct
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7440: make glossary terms case-sensitive end to end. Gold changes two things in sphinx/domains/std.py: (a) note_object('term', termtext.lower(), ...) -> note_object('term', termtext, ...); (b) term XRefRole drops lowercase=True.

Probes (all run in the official docker image, sphinx 3.0.1):
- probe_1 (Req1 AC1/2/3): register 'MySQL' and 'mysql' in a glossary; both must appear as distinct 'term' objects with case-preserved names and NO duplicate-term warning. Patched HOLDS (names ['MySQL','mysql']); BASE VIOLATED (only ['mysql'], 'duplicate term description of mysql' warning). POSITIVE CONTROL.
- probe_2 (Req2 AC1/2): index entry text and target for 'MySQL' must be case-preserved ('MySQL'/'term-MySQL') and equal the registered object name; 'mysql' must not appear. Patched HOLDS; BASE VIOLATED (object registered as lowercased 'mysql' so object-name match fails while index text stays 'MySQL' — the exact registered/index disagreement the spec describes).
- probe_3 (Req3 AC1/2): structural — term role's lowercase attr must be False; behavioral — both ('term','MySQL') and ('term','mysql') keys registered. Patched HOLDS (lowercase=False, both keys); BASE VIOLATED (lowercase=True, only mysql key).
- probe_4 (Req4 AC1, regression): exact duplicate term text emits duplicate-term warning naming the term. HOLDS on both trees.
- probe_5 (Req4 AC3/5, regression): classifier 'termA : classifierX' yields term node 'termA' only (no ':'); multiple term lines (multi1/multi2) both registered on shared def. HOLDS on both trees.
- probe_6 (Req4 AC4, regression): :sorted: glossary with a comment line and case-distinct terms — comment not emitted as a term, case-insensitive sort preserved (apple before Zebra), no glossary/term structure warnings. HOLDS on both trees (env-only 'meta already registered' warning filtered out).

Candidate wrong patches (must apply at base_commit):
- weak_partial (note_object case-fold removed but role still lowercase=True): REJECTED by probe_3 (role lowercase=True). Demonstrates the suite catches a partial fix that omits the role change (xref resolution would still case-fold, matching neither hidden-test intent nor Req3).
- weak_role_only (role lowercase removed but note_object still termtext.lower()): REJECTED by probes 1,2,3 (term still registered under lowercased key -> MySQL/mysql collapse, duplicate warning, object-name mismatch).

Both wrong-fix candidates are rejected; the positive control discriminates (fails at base, holds patched); all 6 probes hold on the patched tree. Verdict SOUND — requirements are faithful and the suite discriminates weak implementations. (No requirements-conforming candidate was found that fails hidden tests, so no TOO-WEAK finding.)

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
# Req 1 (AC1,2,3): glossary terms registered under case-preserving key;
# case-distinct terms both registered, no duplicate warning.
import os, sys, tempfile
from io import StringIO
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.path import path
from sphinx.testing import restructuredtext

srcdir = tempfile.mkdtemp(prefix="sbu_src_")
open(os.path.join(srcdir, "conf.py"), "w").write("")
open(os.path.join(srcdir, "index.rst"), "w").write("")
warning = StringIO()
app = SphinxTestApp(srcdir=path(srcdir), status=StringIO(), warning=warning)

text = (".. glossary::\n\n"
        "   MySQL\n"
        "       a database\n\n"
        "   mysql\n"
        "       a command\n")
restructuredtext.parse(app, text)

objects = list(app.env.get_domain("std").get_objects())
names = [o[0] for o in objects if o[2] == "term"]
print("term names:", names)
warn = warning.getvalue()
print("warnings:", repr(warn))

ok = ("MySQL" in names and "mysql" in names
      and "duplicate" not in warn.lower())
# also ensure no lowercased-only collapse: exactly two distinct term objs
distinct = set(names)
ok = ok and {"MySQL", "mysql"} <= distinct
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7440: make glossary terms case-sensitive end to end. Gold changes two things in sphinx/domains/std.py: (a) note_object('term', termtext.lower(), ...) -> note_object('term', termtext, ...); (b) term XRefRole drops lowercase=True.

Probes (all run in the official docker image, sphinx 3.0.1):
- probe_1 (Req1 AC1/2/3): register 'MySQL' and 'mysql' in a glossary; both must appear as distinct 'term' objects with case-preserved names and NO duplicate-term warning. Patched HOLDS (names ['MySQL','mysql']); BASE VIOLATED (only ['mysql'], 'duplicate term description of mysql' warning). POSITIVE CONTROL.
- probe_2 (Req2 AC1/2): index entry text and target for 'MySQL' must be case-preserved ('MySQL'/'term-MySQL') and equal the registered object name; 'mysql' must not appear. Patched HOLDS; BASE VIOLATED (object registered as lowercased 'mysql' so object-name match fails while index text stays 'MySQL' — the exact registered/index disagreement the spec describes).
- probe_3 (Req3 AC1/2): structural — term role's lowercase attr must be False; behavioral — both ('term','MySQL') and ('term','mysql') keys registered. Patched HOLDS (lowercase=False, both keys); BASE VIOLATED (lowercase=True, only mysql key).
- probe_4 (Req4 AC1, regression): exact duplicate term text emits duplicate-term warning naming the term. HOLDS on both trees.
- probe_5 (Req4 AC3/5, regression): classifier 'termA : classifierX' yields term node 'termA' only (no ':'); multiple term lines (multi1/multi2) both registered on shared def. HOLDS on both trees.
- probe_6 (Req4 AC4, regression): :sorted: glossary with a comment line and case-distinct terms — comment not emitted as a term, case-insensitive sort preserved (apple before Zebra), no glossary/term structure warnings. HOLDS on both trees (env-only 'meta already registered' warning filtered out).

Candidate wrong patches (must apply at base_commit):
- weak_partial (note_object case-fold removed but role still lowercase=True): REJECTED by probe_3 (role lowercase=True). Demonstrates the suite catches a partial fix that omits the role change (xref resolution would still case-fold, matching neither hidden-test intent nor Req3).
- weak_role_only (role lowercase removed but note_object still termtext.lower()): REJECTED by probes 1,2,3 (term still registered under lowercased key -> MySQL/mysql collapse, duplicate warning, object-name mismatch).

Both wrong-fix candidates are rejected; the positive control discriminates (fails at base, holds patched); all 6 probes hold on the patched tree. Verdict SOUND — requirements are faithful and the suite discriminates weak implementations. (No requirements-conforming candidate was found that fails hidden tests, so no TOO-WEAK finding.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the changed observable behavior (both patch hunks — registration key AND xref role case-folding) plus the index-entry/object-name agreement that motivated the issue, and explicitly preserve unchanged diagnostics. No over-claim, no forbidden-behavior mandate, no invented behavior. F2P test is test_glossary; the patch is exactly the two edits in patch.diff and probes confirm patched vs base divergence.

Counterexample / evidence:

```
N/A — no diverging input exists. Concretely, at input (MySQL, mysql): base registers both under key 'mysql' → second warned as duplicate (bug); patched registers under 'MySQL' and 'mysql' → distinct, no warning, matching Req 1.2. At exact-repeat input (mysql, mysql): patched still warns (Req 4.1). Term xref target 'MySQL' is not lowercased before lookup (Req 3), lowercase=False confirmed.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change to legitimate pre-existing symbols (sphinx/domains/std.py, make_glossary_term, note_object, the 'term' XRefRole) — all present in the gold patch but naming the change site is legitimate, not leakage. The MySQL/mysql example is drawn verbatim from the PUBLIC problem_statement, not from the hidden test (which uses term2->TERM2). No test file path, test function names, node-ids (term-term2), get_objects() tuple shapes, or parametrization ids appear. Requirement 4's enumeration of preserved behaviors (duplicate warning, empty-line separation, classifier ' : classifier', comment ignoring, sorted output, multiple term lines) loosely parallels the PASS_TO_PASS set but describes public, documented glossary-directive behaviors as behavior rather than transmitting test identifiers or the specific parametrized cases. The doc translates test-checked behavior (case-sensitive registration/index/xref) into requirements without reconstructing the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
