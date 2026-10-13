# P2 adversarial audit — sphinx-doc__sphinx-10323

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_control.py`, `probe_2_prepend_verbatim.py`, `probe_3_append_verbatim.py`, `probe_4_no_warning.py`, `probe_5_dedent_only.py`, `probe_6_prepend_only.py`, `probe_7_empty_and_selection.py`, `probe_8_gold_test.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_control.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (dedent moved between prepend_filter and append_filter, so dedent still sees the prepended line): with dedent=4, prepend='  PRE', append='  POST', source lines with 8/10 leading spaces, it yields '  PRE\n    selected_a\n      selected_b\n      POST\n' — the prepend line's leading whitespace is stripped from '  PRE'(2 sp)->''(0), while append survives. Rejected by probes 1,2,4,8; only probe 3 (append-only) passes.
```

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_control.py` → holds on the patched tree (good)

```python
# Positive control / Req1.1,1.2,1.3: dedent applies ONLY to selected source
# content; prepend & append lines keep their original leading whitespace.
# HOLDS on patched, must FAIL at base (base dedents last, stripping prepend/append).
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src = "        selected_a\n" "          selected_b\n"   # 8 & 10 leading spaces
f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
f.write(src); f.close()
opts = {'dedent': 4, 'prepend': '      PRE', 'append': '      POST'}
content, _ = LiteralIncludeReader(f.name, opts, CFG).read()
expected = ("      PRE\n"          # prepend verbatim (6 spaces)
            "    selected_a\n"     # 8-4=4 spaces
            "      selected_b\n"   # 10-4=6 spaces
            "      POST\n")        # append verbatim (6 spaces)
print("OBSERVED:", repr(content))
print("EXPECTED:", repr(expected))
os.unlink(f.name)
raise SystemExit(0 if content == expected else 1)
```

Attack 2 — `probe_2_prepend_verbatim.py` → holds on the patched tree (good)

```python
# Req1.2: prepend line placed verbatim (with trailing newline) at FRONT of the
# already-dedented content; its leading whitespace preserved.
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src = "        A\n" "        B\n"
f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
f.write(src); f.close()
prep = '    PREPEND_LINE'   # 4 leading spaces, non-ws after
opts = {'dedent': 4, 'prepend': prep}
content, _ = LiteralIncludeReader(f.name, opts, CFG).read()
os.unlink(f.name)
print("OBSERVED:", repr(content))
ok = content.startswith(prep + '\n')
print("startswith prepend+newline:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3_append_verbatim.py` → holds on the patched tree (good)

```python
# Req1.3: append line placed verbatim (with trailing newline) at END of the
# already-dedented content; its leading whitespace preserved.
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src = "        A\n" "        B\n"
f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
f.write(src); f.close()
app = '    APPEND_LINE'   # 4 leading spaces, non-ws after
opts = {'dedent': 4, 'append': app}
content, _ = LiteralIncludeReader(f.name, opts, CFG).read()
os.unlink(f.name)
print("OBSERVED:", repr(content))
ok = content.endswith(app + '\n')
print("endswith append+newline:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4_no_warning.py` → holds on the patched tree (good)

```python
# Req1.5: with dedent + prepend/append whose leading whitespace is less than the
# dedent count, the reader SHALL NOT emit "non-whitespace stripped by dedent"
# (the added lines are never subjected to dedent).
import tempfile, os, logging
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
recs=[]
class H(logging.Handler):
    def emit(self, r): recs.append(r.getMessage())
h=H(); logging.getLogger().addHandler(h); logging.getLogger().setLevel(logging.DEBUG)
for n in list(logging.Logger.manager.loggerDict):
    logging.getLogger(n).addHandler(h)
src="        A\n        B\n"   # 8 leading spaces, dedents cleanly by 4
f=tempfile.NamedTemporaryFile("w",suffix=".txt",delete=False); f.write(src); f.close()
opts={'dedent':4,'prepend':'PRE','append':'POST'}  # PRE/POST have no leading ws
content,_=LiteralIncludeReader(f.name,opts,CFG).read()
os.unlink(f.name)
warned=any('non-whitespace stripped by dedent' in m for m in recs)
print("CONTENT",repr(content))
print("WARNINGS",recs)
print("warned:",warned)
raise SystemExit(1 if warned else 0)
```

Attack 5 — `probe_5_dedent_only.py` → holds on the patched tree (good)

```python
# Req2.4: dedent WITHOUT prepend/append -> selected content dedented exactly as
# before (matches prior implementation).  Also Req2.7 (auto common-prefix).
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src = "        A\n" "          B\n"   # 8 and 10 leading spaces
f=tempfile.NamedTemporaryFile("w",suffix=".txt",delete=False); f.write(src); f.close()
# explicit dedent 4
c4,_=LiteralIncludeReader(f.name, {'dedent':4}, CFG).read()
# auto dedent (no count) -> remove common leading whitespace (8)
cauto,_=LiteralIncludeReader(f.name, {'dedent':None}, CFG).read()
os.unlink(f.name)
exp4 = "    A\n      B\n"
expauto = "A\n  B\n"
print("dedent4 OBS",repr(c4),"EXP",repr(exp4))
print("auto   OBS",repr(cauto),"EXP",repr(expauto))
raise SystemExit(0 if (c4==exp4 and cauto==expauto) else 1)
```

Attack 6 — `probe_6_prepend_only.py` → holds on the patched tree (good)

```python
# Req2.2 & 2.3: prepend/append with NO dedent -> insert line+newline at
# front/end of selected content, unchanged from prior behavior (leading ws kept).
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src="    X\n    Y\n"
f=tempfile.NamedTemporaryFile("w",suffix=".txt",delete=False); f.write(src); f.close()
cp,_=LiteralIncludeReader(f.name, {'prepend':'   HEAD'}, CFG).read()
ca,_=LiteralIncludeReader(f.name, {'append':'   TAIL'}, CFG).read()
os.unlink(f.name)
exp_p="   HEAD\n    X\n    Y\n"
exp_a="    X\n    Y\n   TAIL\n"
print("prepend OBS",repr(cp),"EXP",repr(exp_p))
print("append  OBS",repr(ca),"EXP",repr(exp_a))
raise SystemExit(0 if (cp==exp_p and ca==exp_a) else 1)
```

Attack 7 — `probe_7_empty_and_selection.py` → holds on the patched tree (good)

```python
# Req2.5: empty prepend/append value -> no line inserted.
# Req2.1: selection filters (lines) applied first, before dedent/prepend/append.
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src="".join("line%d\n"%i for i in range(1,6))  # line1..line5
f=tempfile.NamedTemporaryFile("w",suffix=".txt",delete=False); f.write(src); f.close()
# empty values -> nothing inserted
ce,_=LiteralIncludeReader(f.name, {'prepend':'', 'append':''}, CFG).read()
# selection with lines 2-3 then prepend
cs,_=LiteralIncludeReader(f.name, {'lines':'2-3','prepend':'P'}, CFG).read()
os.unlink(f.name)
exp_e=src
exp_s="P\nline2\nline3\n"
print("empty OBS",repr(ce),"EXP",repr(exp_e))
print("sel   OBS",repr(cs),"EXP",repr(exp_s))
raise SystemExit(0 if (ce==exp_e and cs==exp_s) else 1)
```

Attack 8 — `probe_8_gold_test.py` → holds on the patched tree (good)

```python
# Req1.1: exact scenario/expected output from the FAIL_TO_PASS test
# (test_LiteralIncludeReader_dedent_and_append_and_prepend).
# lines 9-11 are 'class Bar'-style body: '    def baz():','        pass','' (blank).
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
lines = [
 "# header line 1\n",   # 1
 "# header line 2\n",   # 2
 "\n",                  # 3
 "foo = 1\n",           # 4
 "\n",                  # 5
 "class Foo:\n",        # 6
 "    pass\n",          # 7
 "\n",                  # 8
 "    def baz():\n",    # 9
 "        pass\n",      # 10
 "\n",                  # 11
 "def bar(): pass\n",   # 12
]
f=tempfile.NamedTemporaryFile("w",suffix=".inc",delete=False); f.write("".join(lines)); f.close()
opts={'lines':'9-11','dedent':2,'prepend':'class Foo:','append':'# comment'}
content,_=LiteralIncludeReader(f.name, opts, CFG).read()
os.unlink(f.name)
expected=("class Foo:\n"
          "  def baz():\n"
          "      pass\n"
          "\n"
          "# comment\n")
print("OBSERVED",repr(content))
print("EXPECTED",repr(expected))
raise SystemExit(0 if content==expected else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_control.py`

```python
# Positive control / Req1.1,1.2,1.3: dedent applies ONLY to selected source
# content; prepend & append lines keep their original leading whitespace.
# HOLDS on patched, must FAIL at base (base dedents last, stripping prepend/append).
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src = "        selected_a\n" "          selected_b\n"   # 8 & 10 leading spaces
f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
f.write(src); f.close()
opts = {'dedent': 4, 'prepend': '      PRE', 'append': '      POST'}
content, _ = LiteralIncludeReader(f.name, opts, CFG).read()
expected = ("      PRE\n"          # prepend verbatim (6 spaces)
            "    selected_a\n"     # 8-4=4 spaces
            "      selected_b\n"   # 10-4=6 spaces
            "      POST\n")        # append verbatim (6 spaces)
print("OBSERVED:", repr(content))
print("EXPECTED:", repr(expected))
os.unlink(f.name)
raise SystemExit(0 if content == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Target: sphinx/directives/code.py LiteralIncludeReader.read filter ordering. Gold patch moves dedent_filter BEFORE prepend_filter/append_filter so dedent applies only to selected source content.

8 probes, all HOLD on gold-patched tree:
- probe_1_control (POSITIVE CONTROL; Req1.1/1.2/1.3): dedent applies only to source; prepend '      PRE' & append '      POST' keep 6 leading spaces while source dedents. HOLDS patched, FAILS at base (base gives '  PRE...  POST', dedent stripped 4 from added lines).
- probe_2_prepend_verbatim (Req1.2): prepend line placed verbatim at front, leading ws preserved. FAILS at base.
- probe_3_append_verbatim (Req1.3): append line verbatim at end. FAILS at base.
- probe_4_no_warning (Req1.5): no 'non-whitespace stripped by dedent' warning emitted (captured via logging handler). At base 5 such warnings fired. FAILS at base.
- probe_5_dedent_only (Req2.4/2.7): dedent w/o prepend/append — explicit count 4 and auto common-prefix removal both exact. Regression (holds base+patched).
- probe_6_prepend_only (Req2.2/2.3): prepend/append w/o dedent unchanged, leading ws kept. Regression.
- probe_7_empty_and_selection (Req2.5/2.1): empty prepend/append inserts nothing; :lines: selection applied before prepend. Regression.
- probe_8_gold_test (Req1.1): exact FAIL_TO_PASS input (lines 9-11, dedent 2, prepend 'class Foo:', append '# comment') -> exact expected output. HOLDS patched, FAILS at base.

Discriminating power confirmed: probes 1,2,3,4,8 all FAIL at base (prepatch_reproduced=true). WEAK candidate (dedent between prepend and append) rejected by probes 1,2,4,8 — suite discriminates wrong implementations. No requirements-conforming alternative patch found that would fail the hidden test: the requirements pin the ordering biconditionally (dedent before both prepend AND append) which is exactly the gold behavior. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_control.py`, `probe_2_prepend_verbatim.py`, `probe_3_append_verbatim.py`, `probe_4_no_warning.py`, `probe_5_dedent_only.py`, `probe_6_prepend_only.py`, `probe_7_empty_and_selection.py`, `probe_8_gold_test.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_control.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (dedent moved between prepend_filter and append_filter, so dedent still sees the prepended line): with dedent=4, prepend='  PRE', append='  POST', source lines with 8/10 leading spaces, it yields '  PRE\n    selected_a\n      selected_b\n      POST\n' — the prepend line's leading whitespace is stripped from '  PRE'(2 sp)->''(0), while append survives. Rejected by probes 1,2,4,8; only probe 3 (append-only) passes.
```

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_control.py` → holds on the patched tree (good)

Attack 2 — `probe_2_prepend_verbatim.py` → holds on the patched tree (good)

Attack 3 — `probe_3_append_verbatim.py` → holds on the patched tree (good)

Attack 4 — `probe_4_no_warning.py` → holds on the patched tree (good)

Attack 5 — `probe_5_dedent_only.py` → holds on the patched tree (good)

Attack 6 — `probe_6_prepend_only.py` → holds on the patched tree (good)

Attack 7 — `probe_7_empty_and_selection.py` → holds on the patched tree (good)

Attack 8 — `probe_8_gold_test.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_control.py`

```python
# Positive control / Req1.1,1.2,1.3: dedent applies ONLY to selected source
# content; prepend & append lines keep their original leading whitespace.
# HOLDS on patched, must FAIL at base (base dedents last, stripping prepend/append).
import tempfile, os
from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
CFG = Config({}, {})
src = "        selected_a\n" "          selected_b\n"   # 8 & 10 leading spaces
f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
f.write(src); f.close()
opts = {'dedent': 4, 'prepend': '      PRE', 'append': '      POST'}
content, _ = LiteralIncludeReader(f.name, opts, CFG).read()
expected = ("      PRE\n"          # prepend verbatim (6 spaces)
            "    selected_a\n"     # 8-4=4 spaces
            "      selected_b\n"   # 10-4=6 spaces
            "      POST\n")        # append verbatim (6 spaces)
print("OBSERVED:", repr(content))
print("EXPECTED:", repr(expected))
os.unlink(f.name)
raise SystemExit(0 if content == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Target: sphinx/directives/code.py LiteralIncludeReader.read filter ordering. Gold patch moves dedent_filter BEFORE prepend_filter/append_filter so dedent applies only to selected source content.

8 probes, all HOLD on gold-patched tree:
- probe_1_control (POSITIVE CONTROL; Req1.1/1.2/1.3): dedent applies only to source; prepend '      PRE' & append '      POST' keep 6 leading spaces while source dedents. HOLDS patched, FAILS at base (base gives '  PRE...  POST', dedent stripped 4 from added lines).
- probe_2_prepend_verbatim (Req1.2): prepend line placed verbatim at front, leading ws preserved. FAILS at base.
- probe_3_append_verbatim (Req1.3): append line verbatim at end. FAILS at base.
- probe_4_no_warning (Req1.5): no 'non-whitespace stripped by dedent' warning emitted (captured via logging handler). At base 5 such warnings fired. FAILS at base.
- probe_5_dedent_only (Req2.4/2.7): dedent w/o prepend/append — explicit count 4 and auto common-prefix removal both exact. Regression (holds base+patched).
- probe_6_prepend_only (Req2.2/2.3): prepend/append w/o dedent unchanged, leading ws kept. Regression.
- probe_7_empty_and_selection (Req2.5/2.1): empty prepend/append inserts nothing; :lines: selection applied before prepend. Regression.
- probe_8_gold_test (Req1.1): exact FAIL_TO_PASS input (lines 9-11, dedent 2, prepend 'class Foo:', append '# comment') -> exact expected output. HOLDS patched, FAILS at base.

Discriminating power confirmed: probes 1,2,3,4,8 all FAIL at base (prepatch_reproduced=true). WEAK candidate (dedent between prepend and append) rejected by probes 1,2,4,8 — suite discriminates wrong implementations. No requirements-conforming alternative patch found that would fail the hidden test: the requirements pin the ordering biconditionally (dedent before both prepend AND append) which is exactly the gold behavior. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified against sphinx/directives/code.py: filter order is pyobject,start,end,lines,dedent,prepend,append (patched). prepend_filter/append_filter only insert for truthy values (Req 2.5 ok), and only 'dedent' in options triggers dedent (Req 2.4 ok). Modeling boundary is the changed behavior itself, not a narrow helper slice. Both patched (exit 0) and base (exit 1) probes confirm the biconditional.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes the fix behaviorally (de-indent must apply only to selected source content, before prepend/append) — this direction is explicitly public in the problem_statement, which says the ideal solution is 'if dedent was applied only to the literalinclude and not to the prepend and append content'. Filter method names (pyobject_filter, start_filter, end_filter, lines_filter, prepend_filter, append_filter, dedent_filter) and LiteralIncludeReader.read are genuine pre-existing identifiers in sphinx/directives/code.py, used for legitimate localization — none are fix-invented. The hidden test (tests/test_directive_code.py::test_LiteralIncludeReader_dedent_and_append_and_prepend) and its specifics are NOT transmitted: no test name/path, no parametrization values (lines '9-11', dedent 2, prepend 'class Foo:', append '# comment'), and no quoted expected output ('def baz()', 'pass'). The acceptance criteria are generic behavioral statements, not an enumeration mirroring the single parametrized test case. Requirement 2's list of preserved behaviors (pyobject/start/end/lines selection, tab-width, empty-value handling, lineno-match rejection) reflects the public directive API, not the hidden test set (which contains only one F2P case).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
