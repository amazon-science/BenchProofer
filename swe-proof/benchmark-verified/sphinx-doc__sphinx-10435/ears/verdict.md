# P2 adversarial audit — sphinx-doc__sphinx-10435

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
# Requirement 1 (criteria 1 & 2) + POSITIVE CONTROL.
# The inline highlighted-code opening group SHALL be emitted as
#   \sphinxcode{\sphinxupquote{
# immediately followed by a `%` comment character, and the newline the
# highlighter emits right after the opening delimiter SHALL be commented out.
# Exit 0 iff the emitted .tex contains  \sphinxcode{\sphinxupquote{%\n
# (i.e. `{%` then a newline, no space/blank line).  Holds patched, fails base.
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    ".. role:: python(code)\n   :language: python\n\n"
    'Inline :python:`def foo(1 + 2 + None + "abc"): pass` code block\n')
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

needle = r'\sphinxcode{\sphinxupquote{%' + '\n'
ok = needle in content
i = content.find(r'\sphinxcode{\sphinxupquote{')
print("context:", repr(content[i:i+60]) if i >= 0 else "NOT FOUND")
print("opening-group-with-pct-and-suppressed-newline:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 1 criterion 3: the first highlighted token appears on the line
# immediately following the %-terminated opening, with nothing but the
# comment-suppressed newline between the opening group and the first token.
# The highlighted body begins with \PYG (first token). Exit 0 iff the text
# right after `\sphinxcode{\sphinxupquote{%\n` starts with \PYG (no blank line,
# no leading spaces).
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    ".. role:: python(code)\n   :language: python\n\n"
    'Inline :python:`def foo(1 + 2 + None + "abc"): pass` code block\n')
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

marker = r'\sphinxcode{\sphinxupquote{%' + '\n'
idx = content.find(marker)
ok = False
if idx >= 0:
    after = content[idx + len(marker):]
    print("first 30 chars after opening:", repr(after[:30]))
    ok = after.startswith(r'\PYG')
else:
    print("opening marker not found")
print("first-token-immediately-after-suppressed-newline:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 2 (criteria 1,2,3): trailing whitespace suppression. The closing
# sequence SHALL be: last highlighted token, then `%`, a single newline, then
# `}}`. i.e. the body ends `...<lasttoken>%\n}}` — no trailing newline before
# the closing, and the newline before }} is comment-suppressed.
# Exit 0 iff `%\n}}` appears AND the char just before that `%` is `}` (end of a
# \PYG{...}{...} token group, i.e. a real token, not a leftover newline/space).
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    ".. role:: python(code)\n   :language: python\n\n"
    'Inline :python:`def foo(1 + 2 + None + "abc"): pass` code block\n')
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

close = '%' + '\n' + '}}'
idx = content.find(close)
ok = False
if idx >= 0:
    before = content[max(0, idx-40):idx]
    print("40 chars before closing %\\n}}:", repr(before))
    # char immediately before the % must be a closing brace of the last token
    ok = idx > 0 and content[idx-1] == '}'
    # and there must be no bare newline immediately before the % (no trailing
    # newline left in the body)
    ok = ok and content[idx-1] != '\n'
else:
    print("closing sequence %\\n}} not found")
print("trailing-suppressed-close-flush-against-last-token:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 3 criterion 2 (SHALL keep): a plain inline literal (not classed
# `code`, no language) SHALL emit  \sphinxcode{\sphinxupquote{  with NO added
# comment char and close with }}  — unchanged from prior behavior.
# We render a plain ``literal`` and require the exact byte sequence
#   \sphinxcode{\sphinxupquote{plainliteral}}
# with NO `%` inserted after the opening brace.
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    "A plain ``plainliteral`` here\n")
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

exact = r'\sphinxcode{\sphinxupquote{plainliteral}}'
has_exact = exact in content
# must NOT have the code-role percent form for this plain literal
bad = r'\sphinxcode{\sphinxupquote{%'  # only appears for highlighted code
i = content.find(r'\sphinxcode{\sphinxupquote{')
print("context:", repr(content[i:i+60]) if i >= 0 else "NOT FOUND")
print("plain-literal exact form present:", has_exact)
print("no percent-open in this doc:", bad not in content)
ok = has_exact and (bad not in content)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 3 criterion 1 (SHALL keep): a block-level highlighted code
# listing SHALL still be emitted inside a sphinxVerbatim environment whose body
# is preceded by a single newline after the opening line and followed by a
# single newline before \end{sphinxVerbatim} — exactly as before. NO `%`
# suppression there.
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    ".. code-block:: python\n\n"
    '   def foo(1 + 2 + None + "abc"): pass\n')
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

begin = r'\begin{sphinxVerbatim}[commandchars=\\\{\}]'
bi = content.find(begin)
ok = False
if bi >= 0:
    after = content[bi + len(begin):]
    ei = after.find(r'\end{sphinxVerbatim}')
    body = after[:ei]
    print("body starts:", repr(body[:15]))
    print("body ends:", repr(body[-15:]))
    # single newline right after opening line, single newline before \end
    starts_nl = body.startswith('\n') and not body.startswith('\n\n')
    ends_nl = body.endswith('\n') and not body.endswith('\n\n')
    # no percent-suppression injected in the block path
    no_pct = '%\n\\end{sphinxVerbatim}' not in content
    ok = starts_nl and ends_nl and no_pct
    print("single-nl-open:", starts_nl, "single-nl-close:", ends_nl, "no-pct:", no_pct)
else:
    print("sphinxVerbatim environment not found")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 3 criterion 5: the highlighted body content (the sequence of
# \PYG tokens between the opening and closing delimiters) SHALL be byte-for-byte
# identical to what the highlighter produced; only the surrounding delimiters
# change. We check that the inline body equals the exact expected \PYG token
# stream for `def foo(1 + 2 + None + "abc"): pass` — the same token stream the
# hidden test pins as common_content.
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    ".. role:: python(code)\n   :language: python\n\n"
    'Inline :python:`def foo(1 + 2 + None + "abc"): pass` code block\n')
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

open_m = r'\sphinxcode{\sphinxupquote{%' + '\n'
close_m = '%' + '\n' + '}}'
oi = content.find(open_m)
ci = content.find(close_m, oi + 1) if oi >= 0 else -1
ok = False
if oi >= 0 and ci >= 0:
    body = content[oi + len(open_m):ci]
    # every non-empty content is a run of \PYG tokens on one line
    print("inline body:", repr(body[:80]), "...len", len(body))
    tokens_only = body.startswith(r'\PYG') and '\n' not in body and body.count(r'\PYG') >= 5
    # spot-check the exact head and tail the highlighter produces
    head_ok = body.startswith(r'\PYG{k}{def}')
    tail_ok = body.endswith(r'\PYG{k}{pass}')
    ok = tokens_only and head_ok and tail_ok
    print("tokens-only-single-line:", tokens_only, "head:", head_ok, "tail:", tail_ok)
else:
    print("could not locate inline body between delimiters")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1 (criteria 1 & 2) + POSITIVE CONTROL.
# The inline highlighted-code opening group SHALL be emitted as
#   \sphinxcode{\sphinxupquote{
# immediately followed by a `%` comment character, and the newline the
# highlighter emits right after the opening delimiter SHALL be commented out.
# Exit 0 iff the emitted .tex contains  \sphinxcode{\sphinxupquote{%\n
# (i.e. `{%` then a newline, no space/blank line).  Holds patched, fails base.
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    ".. role:: python(code)\n   :language: python\n\n"
    'Inline :python:`def foo(1 + 2 + None + "abc"): pass` code block\n')
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

needle = r'\sphinxcode{\sphinxupquote{%' + '\n'
ok = needle in content
i = content.find(r'\sphinxcode{\sphinxupquote{')
print("context:", repr(content[i:i+60]) if i >= 0 else "NOT FOUND")
print("opening-group-with-pct-and-suppressed-newline:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-10435: LaTeX writer visit_literal for inline highlighted code must suppress leading+trailing whitespace by rewriting the Verbatim delimiters into %-suppressed groups. Gold patch: open '\sphinxcode{\sphinxupquote{%', strip '\n\end{Verbatim}' ([:-15]), append '%'+CR+'}}'.

Probe suite (all run in the official docker image; sphinx 5.0, base f1061c01):
- probe_1 (R1 c1&c2, POSITIVE CONTROL): opening group == '\sphinxcode{\sphinxupquote{%\n'. PATCHED: holds. BASE: fails (opening is '{\n' with no '%'). WEAK: holds.
- probe_2 (R1 c3): first token '\PYG' immediately follows the %-suppressed opening newline. PATCHED holds, BASE fails.
- probe_3 (R2 c1-3): closing is '<lasttoken>}%\n}}' — '%\n}}' present and char before '%' is a token-closing '}' (not a stray newline). PATCHED holds, BASE fails, WEAK REJECTED (no '%\n}}' — trailing newline not stripped, closing still '}}').
- probe_4 (R3 c2, regression): plain ``literal`` emits exact '\sphinxcode{\sphinxupquote{plainliteral}}' with NO '%'. Holds on PATCHED and BASE.
- probe_5 (R3 c1, regression): block code-block still uses sphinxVerbatim env with single newline after open line and before \end, no '%'. Holds on PATCHED and BASE.
- probe_6 (R3 c5): inline body between delimiters is byte-identical highlighter output — single-line \PYG token run starting '\PYG{k}{def}' ending '\PYG{k}{pass}', >=5 tokens. PATCHED holds; BASE fails (no %-delimited region); WEAK REJECTED (no closing '%\n}}' so region unlocatable).

Discrimination confirmed: positive control (probe_1) HOLDS patched and FAILS base (prepatch reproduced). Candidate 'partial_leading_only' (adds only the leading '%', omits trailing strip [:-15] and '%'+CR) satisfies probes 1,2 but is REJECTED by probes 3 and 6 — matching the hidden test which pins BOTH '{%' opening and '%\n}}' closing. No requirements VIOLATION found on the patched tree; no requirements-conforming alternative patch found. Verdict SOUND.

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
# Requirement 1 (criteria 1 & 2) + POSITIVE CONTROL.
# The inline highlighted-code opening group SHALL be emitted as
#   \sphinxcode{\sphinxupquote{
# immediately followed by a `%` comment character, and the newline the
# highlighter emits right after the opening delimiter SHALL be commented out.
# Exit 0 iff the emitted .tex contains  \sphinxcode{\sphinxupquote{%\n
# (i.e. `{%` then a newline, no space/blank line).  Holds patched, fails base.
import os, tempfile, sys

src = tempfile.mkdtemp(prefix="sxsrc_"); out = tempfile.mkdtemp(prefix="sxout_")
open(os.path.join(src, "conf.py"), "w").write(
    "project='p'\nextensions=[]\nmaster_doc='index'\n")
open(os.path.join(src, "index.rst"), "w").write(
    ".. role:: python(code)\n   :language: python\n\n"
    'Inline :python:`def foo(1 + 2 + None + "abc"): pass` code block\n')
from sphinx.application import Sphinx
Sphinx(src, src, out, out, "latex", freshenv=True, status=None,
       warning=sys.stderr).build()
tex = [f for f in os.listdir(out) if f.endswith(".tex")][0]
content = open(os.path.join(out, tex)).read()

needle = r'\sphinxcode{\sphinxupquote{%' + '\n'
ok = needle in content
i = content.find(r'\sphinxcode{\sphinxupquote{')
print("context:", repr(content[i:i+60]) if i >= 0 else "NOT FOUND")
print("opening-group-with-pct-and-suppressed-newline:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-10435: LaTeX writer visit_literal for inline highlighted code must suppress leading+trailing whitespace by rewriting the Verbatim delimiters into %-suppressed groups. Gold patch: open '\sphinxcode{\sphinxupquote{%', strip '\n\end{Verbatim}' ([:-15]), append '%'+CR+'}}'.

Probe suite (all run in the official docker image; sphinx 5.0, base f1061c01):
- probe_1 (R1 c1&c2, POSITIVE CONTROL): opening group == '\sphinxcode{\sphinxupquote{%\n'. PATCHED: holds. BASE: fails (opening is '{\n' with no '%'). WEAK: holds.
- probe_2 (R1 c3): first token '\PYG' immediately follows the %-suppressed opening newline. PATCHED holds, BASE fails.
- probe_3 (R2 c1-3): closing is '<lasttoken>}%\n}}' — '%\n}}' present and char before '%' is a token-closing '}' (not a stray newline). PATCHED holds, BASE fails, WEAK REJECTED (no '%\n}}' — trailing newline not stripped, closing still '}}').
- probe_4 (R3 c2, regression): plain ``literal`` emits exact '\sphinxcode{\sphinxupquote{plainliteral}}' with NO '%'. Holds on PATCHED and BASE.
- probe_5 (R3 c1, regression): block code-block still uses sphinxVerbatim env with single newline after open line and before \end, no '%'. Holds on PATCHED and BASE.
- probe_6 (R3 c5): inline body between delimiters is byte-identical highlighter output — single-line \PYG token run starting '\PYG{k}{def}' ending '\PYG{k}{pass}', >=5 tokens. PATCHED holds; BASE fails (no %-delimited region); WEAK REJECTED (no closing '%\n}}' so region unlocatable).

Discrimination confirmed: positive control (probe_1) HOLDS patched and FAILS base (prepatch reproduced). Candidate 'partial_leading_only' (adds only the leading '%', omits trailing strip [:-15] and '%'+CR) satisfies probes 1,2 but is REJECTED by probes 3 and 6 — matching the hidden test which pins BOTH '{%' opening and '%\n}}' closing. No requirements VIOLATION found on the patched tree; no requirements-conforming alternative patch found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is 3 lines in visit_literal (sphinx/writers/latex.py). Probed patched tree source: opening replace target is r'\sphinxcode{\sphinxupquote{%' (adds trailing '%'), trailer strip is rstrip()[:-15] (was [:-14]; now removes the '\n' + '\end{Verbatim}' = 15 chars), and the closing append is '%' + CR + '}}' (was '}}'), followed by raise nodes.SkipNode. Requirement mapping: R1.1/1.2/1.3 = the '%' appended after the opening group comments the post-delimiter newline -> matches the .replace to '...upquote{%'. R2.1 = strip \n before \end{Verbatim} via [:-15] (exactly matches, old was [:-14] stripping only the 14-char delimiter). R2.2/2.3 = append '%'+newline+'}}' (matches '%' + CR + '}}'). R2.4 = raise nodes.SkipNode (children not descended) matches. R3.1 (block sphinxVerbatim path), R3.2 (plain literal '\sphinxcode{\sphinxupquote{' with depart appending '}}'), R3.3 (title \sphinxstyleliteralintitle), R3.4 (kbd \sphinxkeyboard), R3.5 (body bytes unchanged) all correspond to code paths the patch does not touch. The requirements pin the changed observable behavior (leading/trailing whitespace suppression via delimiter rewriting), not a narrow slice, and invent nothing. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is unusually explicit: it displays both the buggy LaTeX markup and the desired output verbatim, including the `%` comment inserted after `\sphinxcode{\sphinxupquote{` and before `}}`. Every behavioral claim in Requirements 1 and 2 (comment-suppressed leading/trailing newlines) is directly derivable from that public example, not from the hidden test. Req 3 names pre-existing LaTeX writer macros (\sphinxstyleliteralintitle, \sphinxkeyboard, sphinxVerbatim) to localize the change — these are legitimate module/behavior descriptions, not fix-invented identifiers (the gold patch invents nothing; it only edits string literals). No test names/paths/ids, no \PYG token strings from the test's common_content, no gold magic offsets ([:-15]/[:-14]) transmitted as code, and no case enumeration mirroring test parametrization (single F2P test). Requirements translate desired behavior into obligations rather than reconstructing the hidden test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
