# P2 adversarial audit — sphinx-doc__sphinx-11445

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
"""Positive control: role-prefixed heading preserved (Req 1.2, 1.3, 2.3).

A document that opens with an interpreted-text role heading (:mod:`mypackage2`)
followed by its underline. prepend_prolog must NOT count the heading as a field
line, so the prolog lands BEFORE the heading and the heading text and its
underline stay consecutive.
"""
from docutils.statemachine import StringList
from sphinx.util.rst import prepend_prolog

lines = [":mod:`mypackage2`", "=================", "", "Some content."]
content = StringList(lines, "dummy.rst")
prolog = "this is prolog"
prepend_prolog(content, prolog)
result = list(content)
print("RESULT:", result)

# Heading text and underline must remain consecutive with nothing between them.
hi = result.index(":mod:`mypackage2`")
ok_consecutive = result[hi + 1] == "================="
# prolog must appear before the heading
ok_prolog_before = result.index("this is prolog") < hi
print("consecutive:", ok_consecutive, "prolog_before_heading:", ok_prolog_before)
if ok_consecutive and ok_prolog_before:
    print("HOLDS")
    raise SystemExit(0)
print("VIOLATED")
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 2.1 / 2.2: genuine bibliographic fields counted; prolog after them
with exactly one blank-line separator."""
from docutils.statemachine import StringList
from sphinx.util.rst import prepend_prolog

lines = [":title: My Doc", ":author: Me", "", "Body text."]
content = StringList(lines, "dummy.rst")
prepend_prolog(content, "PROLOG")
result = list(content)
print("RESULT:", result)

# First two lines preserved as the header block.
ok_header = result[0] == ":title: My Doc" and result[1] == ":author: Me"
# Exactly one blank line, then PROLOG.
ok_sep = result[2] == "" and result[3] == "PROLOG"
print("header:", ok_header, "sep+prolog:", ok_sep)
if ok_header and ok_sep:
    print("HOLDS"); raise SystemExit(0)
print("VIOLATED"); raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.3 / 3.2: plain heading document (k=0) -> prolog at very top, NO blank
line before prolog, then blank after prolog before original content."""
from docutils.statemachine import StringList
from sphinx.util.rst import prepend_prolog

lines = ["Hello world", "===========", "", "Content."]
content = StringList(lines, "dummy.rst")
prepend_prolog(content, "PROLOG")
result = list(content)
print("RESULT:", result)

# k=0: prolog begins at very top.
ok_top = result[0] == "PROLOG"
# one blank line after prolog then original first line
ok_after = result[1] == "" and result[2] == "Hello world" and result[3] == "==========="
print("top:", ok_top, "after:", ok_after)
if ok_top and ok_after:
    print("HOLDS"); raise SystemExit(0)
print("VIOLATED"); raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.4: role-prefixed heading NOT immediately followed by an underline but
separated by a blank line -> still must NOT be counted as a field line (prolog
at top, k=0)."""
from docutils.statemachine import StringList
from sphinx.util.rst import prepend_prolog

lines = [":mod:`mypackage2`", "", "Some content."]
content = StringList(lines, "dummy.rst")
prepend_prolog(content, "PROLOG")
result = list(content)
print("RESULT:", result)

# k must be 0: prolog at the very top, heading not counted.
ok = result[0] == "PROLOG" and result.index(":mod:`mypackage2`") > result.index("PROLOG")
print("k0_heading_preserved:", ok)
if ok:
    print("HOLDS"); raise SystemExit(0)
print("VIOLATED"); raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.6: empty prolog leaves content unchanged; and Req 3.4: append_epilog
unchanged (non-empty epilog after a single blank separator)."""
from docutils.statemachine import StringList
from sphinx.util.rst import prepend_prolog, append_epilog

lines = [":mod:`mypackage2`", "=================", "", "Content."]
content = StringList(lines, "dummy.rst")
prepend_prolog(content, "")
r1 = list(content)
print("empty-prolog RESULT:", r1)
ok_empty = r1 == lines

lines2 = ["Body line 1", "Body line 2"]
c2 = StringList(lines2, "dummy.rst")
append_epilog(c2, "EPILOG")
r2 = list(c2)
print("epilog RESULT:", r2)
# last original line, one blank, then epilog
ok_epilog = r2[0] == "Body line 1" and r2[1] == "Body line 2" and r2[2] == "" and r2[3] == "EPILOG"

print("empty_unchanged:", ok_empty, "epilog_ok:", ok_epilog)
if ok_empty and ok_epilog:
    print("HOLDS"); raise SystemExit(0)
print("VIOLATED"); raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4: unrelated helpers unchanged (escape leading dot, textwidth wide chars,
heading adornment width)."""
from sphinx.util.rst import escape, textwidth, heading

e = escape(".hidden")
print("escape:", repr(e))
ok_escape = e == "\\.hidden"

tw = textwidth("あ")  # full-width -> 2
print("textwidth:", tw)
ok_tw = tw == 2

class FakeEnv:
    language = "en"
out = heading(FakeEnv(), "Title", 1)
print("heading:", repr(out))
lines = out.split("\n")
ok_heading = lines[0] == "Title" and len(lines[1]) == textwidth("Title") and len(set(lines[1])) == 1

print("escape:", ok_escape, "tw:", ok_tw, "heading:", ok_heading)
if ok_escape and ok_tw and ok_heading:
    print("HOLDS"); raise SystemExit(0)
print("VIOLATED"); raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: role-prefixed heading preserved (Req 1.2, 1.3, 2.3).

A document that opens with an interpreted-text role heading (:mod:`mypackage2`)
followed by its underline. prepend_prolog must NOT count the heading as a field
line, so the prolog lands BEFORE the heading and the heading text and its
underline stay consecutive.
"""
from docutils.statemachine import StringList
from sphinx.util.rst import prepend_prolog

lines = [":mod:`mypackage2`", "=================", "", "Some content."]
content = StringList(lines, "dummy.rst")
prolog = "this is prolog"
prepend_prolog(content, prolog)
result = list(content)
print("RESULT:", result)

# Heading text and underline must remain consecutive with nothing between them.
hi = result.index(":mod:`mypackage2`")
ok_consecutive = result[hi + 1] == "================="
# prolog must appear before the heading
ok_prolog_before = result.index("this is prolog") < hi
print("consecutive:", ok_consecutive, "prolog_before_heading:", ok_prolog_before)
if ok_consecutive and ok_prolog_before:
    print("HOLDS")
    raise SystemExit(0)
print("VIOLATED")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements encoded as 6 standalone probes, all HOLD on gold-patched tree; positive control (probe_1: role-prefixed heading :mod:`mypackage2` + underline) FAILS at base (prolog spliced inside title -> ['...:mod:`mypackage2`','','this is prolog','','=================',...]) and HOLDS patched. Coverage: probe_1 Req1.2/1.3/2.3 (role heading preserved, prolog before, underline consecutive); probe_2 Req3.1/2.1/2.2 (genuine docinfo fields counted, prolog after with one blank sep); probe_3 Req2.3/3.2 (plain heading k=0, prolog at top no leading blank, blank after); probe_4 Req1.4 (role heading separated by blank line still k=0); probe_5 Req2.6/3.4 (empty prolog unchanged; append_epilog unchanged); probe_6 Req4 (escape leading dot, textwidth wide char=2, heading adornment width). CANDIDATE PATCH weak.diff replaces docinfo_re with r':\w+:' (a naive tightening a weak reading permits): it still MATCHES the leading ':mod:' token of the role heading, so probes 1 and 4 REJECT it (VIOLATED) -> suite discriminates wrong implementations; probes 2,3,5,6 still hold under it. No requirements-conforming alternative found that would fail the hidden tests. All runs completed in the official image.

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
"""Positive control: role-prefixed heading preserved (Req 1.2, 1.3, 2.3).

A document that opens with an interpreted-text role heading (:mod:`mypackage2`)
followed by its underline. prepend_prolog must NOT count the heading as a field
line, so the prolog lands BEFORE the heading and the heading text and its
underline stay consecutive.
"""
from docutils.statemachine import StringList
from sphinx.util.rst import prepend_prolog

lines = [":mod:`mypackage2`", "=================", "", "Some content."]
content = StringList(lines, "dummy.rst")
prolog = "this is prolog"
prepend_prolog(content, prolog)
result = list(content)
print("RESULT:", result)

# Heading text and underline must remain consecutive with nothing between them.
hi = result.index(":mod:`mypackage2`")
ok_consecutive = result[hi + 1] == "================="
# prolog must appear before the heading
ok_prolog_before = result.index("this is prolog") < hi
print("consecutive:", ok_consecutive, "prolog_before_heading:", ok_prolog_before)
if ok_consecutive and ok_prolog_before:
    print("HOLDS")
    raise SystemExit(0)
print("VIOLATED")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements encoded as 6 standalone probes, all HOLD on gold-patched tree; positive control (probe_1: role-prefixed heading :mod:`mypackage2` + underline) FAILS at base (prolog spliced inside title -> ['...:mod:`mypackage2`','','this is prolog','','=================',...]) and HOLDS patched. Coverage: probe_1 Req1.2/1.3/2.3 (role heading preserved, prolog before, underline consecutive); probe_2 Req3.1/2.1/2.2 (genuine docinfo fields counted, prolog after with one blank sep); probe_3 Req2.3/3.2 (plain heading k=0, prolog at top no leading blank, blank after); probe_4 Req1.4 (role heading separated by blank line still k=0); probe_5 Req2.6/3.4 (empty prolog unchanged; append_epilog unchanged); probe_6 Req4 (escape leading dot, textwidth wide char=2, heading adornment width). CANDIDATE PATCH weak.diff replaces docinfo_re with r':\w+:' (a naive tightening a weak reading permits): it still MATCHES the leading ':mod:' token of the role heading, so probes 1 and 4 REJECT it (VIOLATED) -> suite discriminates wrong implementations; probes 2,3,5,6 still hold under it. No requirements-conforming alternative found that would fail the hidden tests. All runs completed in the official image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces docinfo_re=re.compile(':\\w+:.*?') with FIELD_NAME_RE=re.compile(Body.patterns['field_marker']) in prepend_prolog's leading-line loop, plus a `lineno=0` init guarding the empty-prolog-splitlines edge. Requirements pin the changed observable behavior (which leading lines count + preamble placement), not a narrow slice — the modeling boundary is correct. Verified via nl_attack probes on the patched tree: regex classification, full prepend_prolog output for k>0/k=0, and the exact hidden-test line/source tuples all reproduce.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior, not the hidden tests. The public problem_statement already exposes rst_prolog, the :mod: domain directive, the :mod:`mypackage2` heading example, and the dropped-heading/toctree symptom. The gold patch's fix-invented identifiers (FIELD_NAME_RE, Body.patterns['field_marker'], docinfo_re, the lineno=0 init) appear NOWHERE in requirements.md; Req 1.1 instead translates the field-marker grammar into prose (colon, non-empty field name, closing colon not preceded by a space, followed by space/EOL) — a legitimate behavioral description, not a transcription of the regex. Naming prepend_prolog/append_epilog/escape/textwidth/heading in sphinx/util/rst.py is legitimate localization. Hidden test content is NOT leaked: no test names/paths/ids (test_prepend_prolog_with_roles_in_sections*), no fixture strings (:title:/:author:/SphinxFileInput, :mod:`foo`), no quoted xitems() assertion tuples with <generated>/<rst_prolog> markers. The with-newline/without-newline distinction in Req 3.3 and the blank-line placement rules describe genuine trailing-newline behavior of the function rather than mirroring the two FAIL_TO_PASS parametrizations verbatim. Req 4 restates pre-existing source-visible helper behavior (PASS_TO_PASS regression coverage), which is legitimate no-regression scoping, not test-derived. No semantic reconstruction of the hidden tests beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
