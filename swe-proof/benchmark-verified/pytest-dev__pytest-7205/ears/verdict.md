# P2 adversarial audit — pytest-dev__pytest-7205

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
"""Positive control / Req 1.1,1.2,1.3: a string param 'foo' is rendered as its
repr ('foo' in quotes) inside trailing [ ] at end of the SETUP line.
HOLDS on patched (saferepr -> 'foo'), FAILS at base (plain str -> foo)."""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(textwrap.dedent("""
    import pytest
    @pytest.fixture(params=['foo'])
    def arg_same(request):
        return request.param
    def test_x(arg_same):
        pass
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--setup-show",
                    "-p", "no:cacheprovider", tf],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("RET", r.returncode)
print(out)
# Must contain the quoted repr form, and must NOT contain the bare form.
ok_quoted = "arg_same['foo']" in out
bare = "arg_same[foo]" in out
print("quoted_repr_present=", ok_quoted, " bare_present=", bare)
sys.exit(0 if (ok_quoted and not bare) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.2: under python -bb (byte warnings -> errors), --setup-show with a
bytes parameter completes with success exit status and does NOT error."""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(textwrap.dedent("""
    import pytest
    @pytest.mark.parametrize('data', [b'Hello World'])
    def test_data(data):
        pass
"""))
r = subprocess.run([sys.executable, "-bb", "-m", "pytest", "--setup-show",
                    "-p", "no:cacheprovider", tf],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("RET", r.returncode)
print(out[-2000:])
bw = "BytesWarning" in out
print("BytesWarning_present=", bw)
sys.exit(0 if (r.returncode == 0 and not bw) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2: length is bounded (maxsize small enough to truncate a huge
value) yet a short value is shown in full & unmodified.
- A long string param must be TRUNCATED (rendered shorter than full repr and
  contain saferepr's '...' elision marker).
- A short string 'ab' must appear as full repr 'ab'.
Also Req 3.2 lower bound: budget must be >= a few chars (short value in full)."""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
tf = os.path.join(d, "test_probe.py")
big = "A" * 500
open(tf, "w").write(textwrap.dedent(f"""
    import pytest
    @pytest.fixture(params=[{big!r}, 'ab'])
    def arg_same(request):
        return request.param
    def test_x(arg_same):
        pass
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--setup-show",
                    "-p", "no:cacheprovider", tf],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("RET", r.returncode)
# Find the bracketed segment for the big value line.
import re
brackets = re.findall(r"arg_same\[(.*?)\]", out)
print("brackets found:", [b[:60] + ('...' if len(b) > 60 else '') for b in brackets])
# The full repr of the 500-A string is 502 chars; truncated must be far shorter.
long_seg = [b for b in brackets if b.startswith("'A") or "A" in b[:5]]
short_ok = "arg_same['ab']" in out
truncated = any(len(b) <= 60 and "..." in b for b in long_seg)
full_len_present = any(len(b) >= 400 for b in brackets)
print("short_ok=", short_ok, "truncated=", truncated, "full_untruncated_present=", full_len_present)
sys.exit(0 if (short_ok and truncated and not full_len_present) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 4.3 + 1.4 + 4.1: same param shown on both SETUP and TEARDOWN lines;
an unparametrized fixture gets NO trailing bracket; step label/scope/name
format preserved. Uses --setup-show so teardown lines are emitted."""
import subprocess, sys, tempfile, os, textwrap, re

d = tempfile.mkdtemp()
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(textwrap.dedent("""
    import pytest
    @pytest.fixture(params=['foo'])
    def arg_same(request):
        return request.param
    @pytest.fixture
    def plain(request):
        return 1
    def test_x(arg_same, plain):
        pass
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--setup-show",
                    "-p", "no:cacheprovider", tf],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("RET", r.returncode)
print(out)
setup_ok = "SETUP    F arg_same['foo']" in out
teardown_ok = "TEARDOWN F arg_same['foo']" in out
# plain fixture: line has name with no trailing [ ]
plain_lines = [ln for ln in out.splitlines() if re.search(r"\b(SETUP|TEARDOWN)\b.*\bplain\b", ln)]
print("plain_lines:", plain_lines)
plain_no_bracket = bool(plain_lines) and all("[" not in ln.split("plain",1)[1] for ln in plain_lines)
print("setup_ok=", setup_ok, "teardown_ok=", teardown_ok, "plain_no_bracket=", plain_no_bracket)
sys.exit(0 if (setup_ok and teardown_ok and plain_no_bracket) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.2 + 4.4: (a) SETUP line for a fixture that depends on others still
appends the sorted '(fixtures used: ...)' list excluding request; (b) explicit
id list is used to SELECT the value, and only final rendering goes through
saferepr. With ids=['spam','ham'], the selected id string 'spam' must render as
repr 'spam' (quoted)."""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(textwrap.dedent("""
    import pytest
    @pytest.fixture(params=[1, 2], ids=['spam', 'ham'])
    def arg_same(request):
        return request.param
    @pytest.fixture
    def arg_other(arg_same):
        return arg_same
    def test_x(arg_other):
        pass
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--setup-show",
                    "-p", "no:cacheprovider", tf],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("RET", r.returncode)
print(out)
# id selected then repr'd -> quoted
id_repr = ("arg_same['spam']" in out) and ("arg_same['ham']" in out)
# dependent fixture lists used fixtures, sorted, excluding request
deps_ok = "(fixtures used: arg_same)" in out
print("id_repr=", id_repr, "deps_ok=", deps_ok)
sys.exit(0 if (id_repr and deps_ok) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.1,1.2,1.3: a string param 'foo' is rendered as its
repr ('foo' in quotes) inside trailing [ ] at end of the SETUP line.
HOLDS on patched (saferepr -> 'foo'), FAILS at base (plain str -> foo)."""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(textwrap.dedent("""
    import pytest
    @pytest.fixture(params=['foo'])
    def arg_same(request):
        return request.param
    def test_x(arg_same):
        pass
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--setup-show",
                    "-p", "no:cacheprovider", tf],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("RET", r.returncode)
print(out)
# Must contain the quoted repr form, and must NOT contain the bare form.
ok_quoted = "arg_same['foo']" in out
bare = "arg_same[foo]" in out
print("quoted_repr_present=", ok_quoted, " bare_present=", bare)
sys.exit(0 if (ok_quoted and not bare) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: _show_fixture_action renders fixturedef.cached_param via saferepr(..., maxsize=42) instead of plain str .format().

Probes (all HOLD on gold-patched tree; run with conda env python python):
- probe_1 (Req 1.1/1.2/1.3, POSITIVE CONTROL): string param 'foo' rendered as quoted repr 'foo' inside trailing [] at end of SETUP line, NOT bare foo. HOLDS patched; FAILS at base (base emits arg_same[foo], patched emits arg_same['foo']) -> discriminates.
- probe_2 (Req 2.2): under python -bb with a bytes param b'Hello World' and --setup-show, run exits 0 and emits no BytesWarning. HOLDS patched.
- probe_3 (Req 3.1/3.2): a 500-char string param is truncated (contains saferepr '...' elision, <=60 chars, no >=400-char untruncated segment) while short 'ab' is shown in full as 'ab'. HOLDS patched.
- probe_4 (Req 1.4/4.1/4.3): same param 'foo' appears on both SETUP and TEARDOWN lines; an unparametrized fixture 'plain' gets no trailing bracket. HOLDS patched.
- probe_5 (Req 4.2/4.4): explicit ids=['spam','ham'] select the id, then only final rendering goes through saferepr so id renders quoted ('spam'/'ham'); dependent fixture still shows sorted (fixtures used: arg_same) excluding request. HOLDS patched.

CANDIDATE (wrong fix, REQUIRED floor): weak_repr_nobound.diff = naive repr() with NO size bound. It satisfies Req 1 (quoted repr) and Req 2 (no bytes coercion) -> probe_1 HOLDS under it, but VIOLATES Req 3 -> probe_3 REJECTS it (VIOLATED: the 500-char value is emitted untruncated). This demonstrates the suite discriminates a requirements-plausible-but-wrong (unbounded) implementation, and this naive fix would fail the hidden test test_show_fixtures_with_parameters-family expectations for truncation.

Result: >=5 distinct probes all HOLD on patched; positive control FAILS at base (prepatch_reproduced=true); >=1 candidate exercised and REJECTED by the probe suite. No requirement is unfaithful/too-strong (no probe fails on patched) and the encoded suite rejects the too-weak unbounded-repr alternative. Verdict SOUND.

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
"""Positive control / Req 1.1,1.2,1.3: a string param 'foo' is rendered as its
repr ('foo' in quotes) inside trailing [ ] at end of the SETUP line.
HOLDS on patched (saferepr -> 'foo'), FAILS at base (plain str -> foo)."""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(textwrap.dedent("""
    import pytest
    @pytest.fixture(params=['foo'])
    def arg_same(request):
        return request.param
    def test_x(arg_same):
        pass
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--setup-show",
                    "-p", "no:cacheprovider", tf],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("RET", r.returncode)
print(out)
# Must contain the quoted repr form, and must NOT contain the bare form.
ok_quoted = "arg_same['foo']" in out
bare = "arg_same[foo]" in out
print("quoted_repr_present=", ok_quoted, " bare_present=", bare)
sys.exit(0 if (ok_quoted and not bare) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: _show_fixture_action renders fixturedef.cached_param via saferepr(..., maxsize=42) instead of plain str .format().

Probes (all HOLD on gold-patched tree; run with conda env python python):
- probe_1 (Req 1.1/1.2/1.3, POSITIVE CONTROL): string param 'foo' rendered as quoted repr 'foo' inside trailing [] at end of SETUP line, NOT bare foo. HOLDS patched; FAILS at base (base emits arg_same[foo], patched emits arg_same['foo']) -> discriminates.
- probe_2 (Req 2.2): under python -bb with a bytes param b'Hello World' and --setup-show, run exits 0 and emits no BytesWarning. HOLDS patched.
- probe_3 (Req 3.1/3.2): a 500-char string param is truncated (contains saferepr '...' elision, <=60 chars, no >=400-char untruncated segment) while short 'ab' is shown in full as 'ab'. HOLDS patched.
- probe_4 (Req 1.4/4.1/4.3): same param 'foo' appears on both SETUP and TEARDOWN lines; an unparametrized fixture 'plain' gets no trailing bracket. HOLDS patched.
- probe_5 (Req 4.2/4.4): explicit ids=['spam','ham'] select the id, then only final rendering goes through saferepr so id renders quoted ('spam'/'ham'); dependent fixture still shows sorted (fixtures used: arg_same) excluding request. HOLDS patched.

CANDIDATE (wrong fix, REQUIRED floor): weak_repr_nobound.diff = naive repr() with NO size bound. It satisfies Req 1 (quoted repr) and Req 2 (no bytes coercion) -> probe_1 HOLDS under it, but VIOLATES Req 3 -> probe_3 REJECTS it (VIOLATED: the 500-char value is emitted untruncated). This demonstrates the suite discriminates a requirements-plausible-but-wrong (unbounded) implementation, and this naive fix would fail the hidden test test_show_fixtures_with_parameters-family expectations for truncation.

Result: >=5 distinct probes all HOLD on patched; positive control FAILS at base (prepatch_reproduced=true); >=1 candidate exercised and REJECTED by the probe suite. No requirement is unfaithful/too-strong (no probe fails on patched) and the encoded suite rejects the too-weak unbounded-repr alternative. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes run in the instance image. Gold-patched: test_bytes exits 0, saferepr('abc',42)=="'abc'", saferepr(200-char)==len 42. Base VIOLATED both the string-repr and bytes-crash expectations, confirming the requirements pin the actual changed observable behavior (value rendered via saferepr) rather than a narrow slice or invented behavior. Modeling boundary correct.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to _show_fixture_action in src/_pytest/setuponly.py and the pytest_fixture_setup/post_finalizer hooks — legitimate localization. The gold edit's only invented value, maxsize=42, is deliberately abstracted ('size budget', 'small enough to bound a single line yet large enough that typical short values are shown in full') and never disclosed. The 'abc' -> 'abc' illustration is an invented example, not a test parameter value (tests use foo/bar/spam/ham/FOO/BAR). The bytes/-bb/BytesWarning scenario in Requirement 2 is drawn entirely from the PUBLIC problem_statement (which includes the exact repro file and traceback). Requirement 4.4's mention of 'a static id list or an id-generating callable' describes real pre-existing pytest id-selection behavior (params vs ids= list vs ids= callable) rather than reconstructing the three test variants (test_show_fixtures_with_parameters / _with_parameter_ids / _with_parameter_ids_function). No test names, file paths, parametrization ids, or verbatim test/gold code lines are transmitted. Requirements are behavioral translations of what the tests check (repr rendering, quoting of strings, no BytesWarning, truncation), which is the intended purpose.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
