# P2 adversarial audit — django__django-12155

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: Req 1.1/1.2/1.3 — docstring with text on first line + indented body.
# The body's shared leading indentation must be removed so body is NOT left indented.
import sys
from django.contrib.admindocs.utils import parse_docstring
doc = "firstline\n\n    second line"
title, body, meta = parse_docstring(doc)
print("title=%r body=%r meta=%r" % (title, body, meta))
ok = (title == "firstline" and body == "second line" and meta == {})
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.4: title and body of a first-line-text docstring each render as ordinary
# reST paragraph content WITHOUT emitting any warning/error to stderr.
import sys, io
import sys, types
import django
from django.conf import settings
_u = types.ModuleType("dummyurls")
from django.urls import path, include
_u.urlpatterns = [path("admindocs/", include("django.contrib.admindocs.urls"))]
sys.modules["dummyurls"] = _u
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, ROOT_URLCONF="dummyurls",
        INSTALLED_APPS=["django.contrib.admindocs","django.contrib.admin",
            "django.contrib.auth","django.contrib.contenttypes"], USE_TZ=True)
    django.setup()
from django.contrib.admindocs.utils import parse_docstring, parse_rst
doc = "firstline\n\n    second line"
title, body, meta = parse_docstring(doc)
buf = io.StringIO(); old = sys.stderr; sys.stderr = buf
try:
    rt = parse_rst(title, 'view'); rb = parse_rst(body, 'view')
finally:
    sys.stderr = old
err = buf.getvalue()
print("rendered_title=%r" % rt); print("rendered_body=%r" % rb); print("stderr=%r" % err)
ok = ("<p>firstline</p>" in rt and "<p>second line</p>" in rb and err.strip() == "")
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.5: no non-blank line after the first — parse_docstring SHALL NOT fail
# (min() over empty sequence) and leaves lines after first unchanged.
import sys
from django.contrib.admindocs.utils import parse_docstring
try:
    t, b, m = parse_docstring("onlyoneline")
except Exception as e:
    print("RAISED:", type(e).__name__, e); sys.exit(1)
print("single -> title=%r body=%r meta=%r" % (t, b, m))
# also a first line of text followed only by blank lines
try:
    t2, b2, m2 = parse_docstring("firstline\n\n\n")
except Exception as e:
    print("RAISED2:", type(e).__name__, e); sys.exit(1)
print("trailing-blank -> title=%r body=%r meta=%r" % (t2, b2, m2))
ok = (t == "onlyoneline" and b == "" and m == {} and t2 == "firstline")
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.1: None or empty string short-circuits to ('', '', {}).
import sys
from django.contrib.admindocs.utils import parse_docstring
r_none = parse_docstring(None)
r_empty = parse_docstring("")
print("None ->", r_none)
print("'' ->", r_empty)
ok = (r_none == ('', '', {}) and r_empty == ('', '', {}))
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.1 (regression): empty-first-line docstring (Django's own style) parses
# identically to the historical trim_docstring-based behavior.
import sys
from django.contrib.admindocs.utils import parse_docstring
# Reference: historical algorithm computed inline.
def old_trim(docstring):
    if not docstring or not docstring.strip():
        return ''
    lines = docstring.expandtabs().splitlines()
    indent = min(len(l) - len(l.lstrip()) for l in lines if l.lstrip())
    trimmed = [lines[0].lstrip()] + [l[indent:].rstrip() for l in lines[1:]]
    return "\n".join(trimmed).strip()
import re
def old_parse(docstring):
    docstring = old_trim(docstring)
    if not docstring:
        return '', '', {}
    parts = re.split(r'\n{2,}', docstring)
    title = parts[0]
    if len(parts) == 1:
        body = ''
        metadata = {}
    else:
        from email.parser import HeaderParser
        from email.errors import HeaderParseError
        parser = HeaderParser()
        try:
            metadata = parser.parsestr(parts[-1]).items()
            metadata = dict(metadata)
        except HeaderParseError:
            metadata = {}
            body = "\n\n".join(parts[1:])
        else:
            if metadata:
                body = "\n\n".join(parts[1:-1])
            else:
                body = "\n\n".join(parts[1:])
    return title, body, dict(metadata)
docs = [
    "\nTitle line.\n\n    Body paragraph one.\n\n    Body two.\n",
    "\nDoes something useful.\n",
    "\nSummary.\n\n    param: value\n    other: thing\n",
]
allok = True
for d in docs:
    got = parse_docstring(d)
    exp = old_parse(d)
    same = got == exp
    print("same=%s got=%r exp=%r" % (same, got, exp))
    allok = allok and same
print("OK" if allok else "FAIL")
sys.exit(0 if allok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.3: final paragraph of RFC-822 key:value lines returned as metadata and
# excluded from body; a non-metadata final paragraph stays in the body.
import sys
from django.contrib.admindocs.utils import parse_docstring
d_meta = "Title.\n\nSome body text here.\n\nauthor: jane\nversion: 2"
t, b, m = parse_docstring(d_meta)
print("meta-case: title=%r body=%r meta=%r" % (t, b, m))
ok_meta = (m.get('author') == 'jane' and m.get('version') == '2'
           and 'author' not in b and b == "Some body text here.")
d_nometa = "Title.\n\nJust a normal closing paragraph."
t2, b2, m2 = parse_docstring(d_nometa)
print("no-meta-case: title=%r body=%r meta=%r" % (t2, b2, m2))
ok_nometa = (m2 == {} and "Just a normal closing paragraph." in b2)
ok = ok_meta and ok_nometa
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: model-detail view path renders a first-line-text method docstring
# cleanly (no residual indentation, no stderr) via the same cleandoc trim.
import sys, io
import sys, types
import django
from django.conf import settings
_u = types.ModuleType("dummyurls")
from django.urls import path, include
_u.urlpatterns = [path("admindocs/", include("django.contrib.admindocs.urls"))]
sys.modules["dummyurls"] = _u
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, ROOT_URLCONF="dummyurls",
        INSTALLED_APPS=["django.contrib.admindocs","django.contrib.admin",
            "django.contrib.auth","django.contrib.contenttypes"], USE_TZ=True)
    django.setup()
from inspect import cleandoc
from django.contrib.admindocs.utils import parse_rst
class M:
    def meth(self):
        """methodfirst line.

        Indented detail line.
        """
        pass
verbose = M.meth.__doc__
buf = io.StringIO(); old = sys.stderr; sys.stderr = buf
try:
    rendered = parse_rst(cleandoc(verbose), 'model', 'model:m')
finally:
    sys.stderr = old
err = buf.getvalue()
print("rendered=%r" % rendered); print("stderr=%r" % err)
ok = ("<p>methodfirst line." in rendered and "Indented detail line." in rendered and err.strip() == "")
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Req 2.2: a whitespace-only (but non-empty) multiline docstring must NOT take
# the None/'' short-circuit; it is normalized per PEP257 instead. For '\n   \n'
# the gold normalization (inspect.cleandoc) yields a non-empty title, proving the
# empty triple was NOT assumed for whitespace.
import sys
from django.contrib.admindocs.utils import parse_docstring
r = parse_docstring("\n   \n")
print("'\\n   \\n' ->", r)
# Must NOT be the empty short-circuit result; normalization produced a title.
ok = (r != ('', '', {}) and r[0] == '   ')
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.1/1.2/1.3 — docstring with text on first line + indented body.
# The body's shared leading indentation must be removed so body is NOT left indented.
import sys
from django.contrib.admindocs.utils import parse_docstring
doc = "firstline\n\n    second line"
title, body, meta = parse_docstring(doc)
print("title=%r body=%r meta=%r" % (title, body, meta))
ok = (title == "firstline" and body == "second line" and meta == {})
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) HOLDS patched and is VIOLATED at base (firstline/'    second line' -> indented body not dedented), so it discriminates. probe_2 also discriminates (base emits the 'default-role' directive error to the rendered output; patched renders clean <p> paragraphs with empty stderr).

Coverage: probe_1 = Req 1.1/1.2/1.3 (dedent body by common indent of lines-after-first); probe_2 = Req 1.4 (title+body render as ordinary paragraphs, no stderr warning); probe_3 = Req 1.5 (no non-blank line after first -> no min()-empty crash; single line + trailing-blank cases); probe_4 = Req 2.1 (None/'' short-circuit to ('','',{})); probe_5 = Req 3.1 (empty-first-line docstrings parse identically to historical trim_docstring algorithm, 3 cases); probe_6 = Req 3.3 (RFC-822 metadata paragraph extracted vs non-metadata paragraph stays in body); probe_7 = Req 4.1/4.2 (view path cleandoc-trims method docstring, renders clean, no stderr); probe_8 = Req 2.2 (whitespace-only multiline docstring is NOT assumed empty -> '\n   \n' normalizes to title='   ', not the empty short-circuit).

CANDIDATE PATCH (required floor): weak_A = the naive 'lines[1:]' fix of the original trim_docstring WITHOUT an empty-sequence guard (a weak reading of Req 1.1 that ignores Req 1.5). It is REJECTED by the suite: probe_3 fails arg is an empty sequence on a single-line docstring, violating Req 1.5) and probe_8 fails (collapses '\n   \n' to ('','',{}), violating Req 2.2). probes 1,2,4,5,6 still hold under it. This demonstrates the suite discriminates plausibly-wrong implementations.

IMPORTANT re prior stamp: the recorded G-EQ/G-PANEL-1 VIOLATION (prior probe_7) asserted whitespace-only docstrings SHALL return ('','',{}) — that is BACKWARDS. Requirement 2.2 explicitly states the empty result 'SHALL NOT be assumed for a docstring that merely contains whitespace'. The gold (inspect.cleandoc) yields title='   ' for '\n   \n', which is exactly what Req 2.2 mandates and what my probe_8 confirms. The prior VIOLATION was a bogus probe encoding the negation of the requirement; there is no real spec-too-strong defect here. Similarly the prior G-PANEL-2 note is self-refuting (it observes cleandoc gives '   ' then mislabels that as unfaithful).

Env note: probe_2/probe_7 configure minimal Django settings with ROOT_URLCONF including django.contrib.admindocs.urls so parse_rst's default-role reverse('django-admindocs-docroot') resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.1/1.2/1.3 — docstring with text on first line + indented body.
# The body's shared leading indentation must be removed so body is NOT left indented.
import sys
from django.contrib.admindocs.utils import parse_docstring
doc = "firstline\n\n    second line"
title, body, meta = parse_docstring(doc)
print("title=%r body=%r meta=%r" % (title, body, meta))
ok = (title == "firstline" and body == "second line" and meta == {})
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) HOLDS patched and is VIOLATED at base (firstline/'    second line' -> indented body not dedented), so it discriminates. probe_2 also discriminates (base emits the 'default-role' directive error to the rendered output; patched renders clean <p> paragraphs with empty stderr).

Coverage: probe_1 = Req 1.1/1.2/1.3 (dedent body by common indent of lines-after-first); probe_2 = Req 1.4 (title+body render as ordinary paragraphs, no stderr warning); probe_3 = Req 1.5 (no non-blank line after first -> no min()-empty crash; single line + trailing-blank cases); probe_4 = Req 2.1 (None/'' short-circuit to ('','',{})); probe_5 = Req 3.1 (empty-first-line docstrings parse identically to historical trim_docstring algorithm, 3 cases); probe_6 = Req 3.3 (RFC-822 metadata paragraph extracted vs non-metadata paragraph stays in body); probe_7 = Req 4.1/4.2 (view path cleandoc-trims method docstring, renders clean, no stderr); probe_8 = Req 2.2 (whitespace-only multiline docstring is NOT assumed empty -> '\n   \n' normalizes to title='   ', not the empty short-circuit).

CANDIDATE PATCH (required floor): weak_A = the naive 'lines[1:]' fix of the original trim_docstring WITHOUT an empty-sequence guard (a weak reading of Req 1.1 that ignores Req 1.5). It is REJECTED by the suite: probe_3 fails arg is an empty sequence on a single-line docstring, violating Req 1.5) and probe_8 fails (collapses '\n   \n' to ('','',{}), violating Req 2.2). probes 1,2,4,5,6 still hold under it. This demonstrates the suite discriminates plausibly-wrong implementations.

IMPORTANT re prior stamp: the recorded G-EQ/G-PANEL-1 VIOLATION (prior probe_7) asserted whitespace-only docstrings SHALL return ('','',{}) — that is BACKWARDS. Requirement 2.2 explicitly states the empty result 'SHALL NOT be assumed for a docstring that merely contains whitespace'. The gold (inspect.cleandoc) yields title='   ' for '\n   \n', which is exactly what Req 2.2 mandates and what my probe_8 confirms. The prior VIOLATION was a bogus probe encoding the negation of the requirement; there is no real spec-too-strong defect here. Similarly the prior G-PANEL-2 note is self-refuting (it observes cleandoc gives '   ' then mislabels that as unfaithful).

Env note: probe_2/probe_7 configure minimal Django settings with ROOT_URLCONF including django.contrib.admindocs.urls so parse_rst's default-role reverse('django-admindocs-docroot') resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces trim_docstring with inspect.cleandoc in both utils.parse_docstring and views.ModelDetailView.get_context_data, plus a falsy-only early return. Probes on patched tree: first-line-text 'test tests something.\n    ' -> title kept ('test tests something.\n    ',...) ; body case dedents indented body (Req 1.2/1.3); single line no failure (Req 1.5); metadata trailing paragraph parsed to mapping and excluded from body (Req 3.3); None/'' -> ('','',{}) (Req 2.1); whitespace-only normalized not short-circuited (Req 2.2). Base-vs-patched contrast confirms the changed observable is dedenting bodies of first-line-text docstrings and no longer collapsing whitespace-only to empty. FAIL_TO_PASS test_parse_rst_with_docstring_no_leading_line_feed covers the changed behavior. Requirements pin the changed observable behavior (PEP257/cleandoc trimming), not a narrow slice; boundary is correct and covers both call sites (Req 4).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior derivable from the PUBLIC problem_statement (which already names trim_docstring, the culprit min() line, the first-line-indent-0 bug, the default-role directive error, and a docstring example) plus legitimate localization of the changed code. All identifiers cited (parse_docstring, parse_rst, trim_docstring, ModelDetailView.get_context_data, verbose) pre-exist in the target modules or the problem statement — none are fix-invented; cleandoc is NOT named (its algorithm is paraphrased as PEP 257 behavior, the legitimate fix-as-requirement translation). The hidden test (test_parse_rst_with_docstring_no_leading_line_feed) is a single case: no test name/path/id, no quoted test/gold code, and Req 1.3's structural example (text / blank line / indented body) is generic prose that supplies none of the test's literal strings ('firstline', 'second line'); Req 1.4's 'renders as paragraph, no stderr' is the test's assertion translated to a behavioral obligation, which is the spec's proper job, not leakage. No case enumeration mirroring parametrization (there is only one F2P case).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
