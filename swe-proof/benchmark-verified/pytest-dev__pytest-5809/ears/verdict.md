# P2 adversarial audit — pytest-dev__pytest-5809

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control. R1.1/R1.3: the encoded request body sets the highlighter
language parameter to `text` and declares NO python-specific highlighter.
Holds on patched tree, must FAIL at base (base uses lexer=python3)."""
import sys
import urllib.parse
import urllib.request
from _pytest import pastebin

captured = {}
def mocked(url, data):
    captured["url"] = url
    captured["data"] = data
    class DF:
        def read(self):
            return b'View <a href="/raw/3c0c6750bd">raw</a>.'
    return DF()
urllib.request.urlopen = mocked

pastebin.create_new_paste(b"full-paste-contents")
data = captured["data"]
body = data.decode() if isinstance(data, (bytes, bytearray)) else data
params = dict(urllib.parse.parse_qsl(body))
print("body:", body)
print("lexer:", params.get("lexer"))

ok = params.get("lexer") == "text"
# must NOT declare any python-specific highlighter
py_lexer = params.get("lexer", "").lower().startswith("python")
if not ok:
    print("FAIL: lexer is not 'text'")
    sys.exit(1)
if py_lexer:
    print("FAIL: python-specific lexer declared")
    sys.exit(1)
print("PASS: lexer=text, no python-specific highlighter")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2: the language parameter SHALL NOT depend on the running Python major
version. We inspect create_new_paste's source and require that the value bound
to the 'lexer' key is a single constant not selected via sys.version_info.
Approach: parse the AST, find the dict literal built for the request, locate the
'lexer' entry, and assert its value is a constant string 'text' (not an
IfExp/conditional referencing version_info)."""
import ast
import inspect
import sys
from _pytest import pastebin

src = inspect.getsource(pastebin.create_new_paste)
mod = ast.parse(src)
lexer_values = []
for node in ast.walk(mod):
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "lexer":
                lexer_values.append(v)

print("found %d lexer dict-entries" % len(lexer_values))
if not lexer_values:
    print("FAIL: no lexer parameter found in dict literal")
    sys.exit(1)

def references_version(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and n.attr == "version_info":
            return True
        if isinstance(n, ast.Name) and n.id == "version_info":
            return True
    return False

for v in lexer_values:
    if isinstance(v, ast.IfExp) or references_version(v):
        print("FAIL: lexer value is conditional / depends on version")
        sys.exit(1)
    if not (isinstance(v, ast.Constant) and v.value == "text"):
        print("FAIL: lexer value is not the constant 'text':", ast.dump(v))
        sys.exit(1)

print("PASS: lexer is constant 'text', independent of python version")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2: complete & correct request contents.
- R2.1 code == contents unchanged
- R2.2 expiry == 1week
- R2.3 target url == https://bpaste.net
- R2.4 data passed to opener is bytes
- R2.5 exactly {code, lexer, expiry}, nothing more/less"""
import sys
import urllib.parse
import urllib.request
from _pytest import pastebin

captured = {}
def mocked(url, data):
    captured["url"] = url
    captured["data"] = data
    class DF:
        def read(self):
            return b'View <a href="/raw/3c0c6750bd">raw</a>.'
    return DF()
urllib.request.urlopen = mocked

pastebin.create_new_paste(b"full-paste-contents")
url = captured["url"]
data = captured["data"]
print("url:", url)
print("data type:", type(data).__name__)

# R2.4 bytes
if not isinstance(data, (bytes, bytearray)):
    print("FAIL: data is not bytes")
    sys.exit(1)
body = data.decode()
params = dict(urllib.parse.parse_qsl(body))
print("params keys:", sorted(params))

# R2.3
if url != "https://bpaste.net":
    print("FAIL: url != https://bpaste.net")
    sys.exit(1)
# R2.1
if params.get("code") != "full-paste-contents":
    print("FAIL: code param not equal to contents")
    sys.exit(1)
# R2.2
if params.get("expiry") != "1week":
    print("FAIL: expiry != 1week")
    sys.exit(1)
# R2.5 exactly these three keys
if set(params) != {"code", "lexer", "expiry"}:
    print("FAIL: param set is not exactly {code,lexer,expiry}:", set(params))
    sys.exit(1)
print("PASS: request contents complete and correct")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1: when the response contains a raw-paste reference, create_new_paste
returns the show-URL https://bpaste.net/show/<id> with the extracted id."""
import sys
import urllib.request
from _pytest import pastebin

def mocked(url, data):
    class DF:
        def read(self):
            return b'View <a href="/raw/3c0c6750bd">raw</a>.'
    return DF()
urllib.request.urlopen = mocked

result = pastebin.create_new_paste(b"full-paste-contents")
print("result:", repr(result))
if result == "https://bpaste.net/show/3c0c6750bd":
    print("PASS: show-URL derived from raw reference")
    sys.exit(0)
print("FAIL: unexpected return value")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.2: IF the response contains NO recognizable raw-paste reference, THEN
create_new_paste SHALL NOT return a show-URL of the form
https://bpaste.net/show/<id>. The requirement mandates only that no such
show-URL is *returned* — it does NOT mandate a graceful non-raising return.
So the criterion holds iff either (a) the call raises, or (b) it returns a
value that does not match the show-URL pattern."""
import re
import sys
import urllib.request
from _pytest import pastebin

def mocked(url, data):
    class DF:
        def read(self):
            # a response WITHOUT any href="/raw/..." reference
            return b'Totally unrelated HTML with no raw paste reference.'
    return DF()
urllib.request.urlopen = mocked

showurl = re.compile(r"^https://bpaste\.net/show/\w+$")
try:
    result = pastebin.create_new_paste(b"full-paste-contents")
    print("returned:", repr(result))
    if isinstance(result, str) and showurl.match(result):
        print("FAIL: returned a show-URL for a non-matching response")
        sys.exit(1)
    print("PASS: no show-URL returned for non-matching response (returned non-show value)")
    sys.exit(0)
except Exception as e:
    print("raised (no show-URL returned):", repr(e))
    print("PASS: no show-URL returned for non-matching response (raised)")
    sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R5.1 (tee) + R6.1 (utf-8 encode): with --pastebin=all, pytest_configure
installs a tee on the terminal reporter's write that encodes text as utf-8
bytes into a buffer; pytest_unconfigure reads that buffer and uploads it once
via create_new_paste. We drive this with lightweight fakes (no pytest runner)."""
import sys
import types
import urllib.request
from _pytest import pastebin


class FakeTW:
    def __init__(self):
        self.written = []
    def write(self, s, **kwargs):
        self.written.append(s)
    def line(self, s="", **kwargs):
        self.written.append(s + "\n")


class FakeTR:
    def __init__(self, tw):
        self._tw = tw
        self.lines = []
    def write_sep(self, sep, title, **kw):
        self.lines.append("SEP %s %s" % (sep, title))
    def write_line(self, s, **kw):
        self.lines.append(s)


class FakeOption:
    pastebin = "all"


class FakePM:
    def __init__(self, tr):
        self._tr = tr
    def getplugin(self, name):
        if name == "terminalreporter":
            return self._tr
        return None


class FakeConfig:
    def __init__(self, tr):
        self.option = FakeOption()
        self.pluginmanager = FakePM(tr)


tw = FakeTW()
tr = FakeTR(tw)
config = FakeConfig(tr)

# install tee
pastebin.pytest_configure(config)

# terminal reporter now writes through tee; feed non-ascii text
tr._tw.write("hello ☺ world\n")
tr._tw.write("1 failed, 1 passed, 1 skipped\n")

# capture the upload
uploaded = {}
calls = []
def mocked(url, data):
    calls.append(1)
    uploaded["data"] = data
    class DF:
        def read(self):
            return b'View <a href="/raw/abc123">raw</a>.'
    return DF()
urllib.request.urlopen = mocked

# pytest_unconfigure reads the buffer and uploads once
pastebin.pytest_unconfigure(config)

sessionlog = pastebin.create_new_paste  # sanity
print("upload calls during unconfigure:", len(calls))
print("uploaded data type:", type(uploaded.get("data")).__name__)

# The buffered content passed to create_new_paste should have been the utf-8
# bytes of what we wrote. create_new_paste got called with those bytes; verify
# the buffer contained utf-8-encoded non-ascii.
data = uploaded.get("data")
if len(calls) != 1:
    print("FAIL: create_new_paste not invoked exactly once")
    sys.exit(1)
# data is the urlencoded bytes body; the code param should carry utf-8 bytes of ☺
body = data.decode() if isinstance(data, (bytes, bytearray)) else data
utf8_snowman = "☺".encode("utf-8")
# percent-encoded utf-8 of ☺ is %E2%98%BA
if "%E2%98%BA" not in body.upper():
    print("FAIL: utf-8 encoded non-ascii not present in uploaded body")
    print("body:", body)
    sys.exit(1)
if "SEP" not in " ".join(tr.lines) or not any("pastebin session-log" in l for l in tr.lines):
    print("FAIL: separator/paste URL line not emitted")
    print("lines:", tr.lines)
    sys.exit(1)
print("PASS: tee encodes utf-8, uploads once, emits sep + url line")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R4: failed-only pastebin mode.
- R4.3: if --pastebin is not 'failed', the failed-only terminal-summary path
  SHALL NOT upload any paste.
- R4.1/4.2: with pastebin=failed and one failing rep present, the helper is
  invoked (once per failure) and the uploaded content includes the failing
  test's representation.
Driven with fakes; create_new_paste is monkeypatched to record calls."""
import sys
import urllib.request
from _pytest import pastebin


class FakeOption:
    def __init__(self, mode):
        self.pastebin = mode
        self.color = "no"


class FakeConfig:
    def __init__(self, mode):
        self.option = FakeOption(mode)


class FakeTR:
    def __init__(self, mode, stats):
        self.config = FakeConfig(mode)
        self.stats = stats
        self.lines = []
        self._tw = None
    def write_sep(self, sep, title, **kw):
        self.lines.append("SEP")
    def write_line(self, s, **kw):
        self.lines.append(s)
    def _getfailureheadline(self, rep):
        return "test_fail headline"


class FakeRep:
    def __init__(self, text):
        self._text = text
        self.longrepr = None  # force AttributeError -> use _getfailureheadline
    def toterminal(self, tw):
        tw.stringio.write(self._text)


# Record helper invocations
calls = []
def fake_create_new_paste(contents):
    calls.append(contents)
    return "https://bpaste.net/show/deadbeef"
pastebin.create_new_paste = fake_create_new_paste

# --- R4.3: mode != failed -> no upload ---
calls.clear()
tr_all = FakeTR("all", {"failed": [FakeRep("def test_fail")]})
pastebin.pytest_terminal_summary(tr_all)
if len(calls) != 0:
    print("FAIL(R4.3): upload happened when pastebin != failed:", len(calls))
    sys.exit(1)
print("R4.3 ok: no upload when mode != failed")

# --- R4.1/4.2: mode == failed, one failing rep -> exactly one upload ---
calls.clear()
tr_failed = FakeTR("failed", {"failed": [FakeRep("def test_fail with assert 0")]})
pastebin.pytest_terminal_summary(tr_failed)
print("upload calls in failed-mode:", len(calls))
if len(calls) != 1:
    print("FAIL(R4.2): expected exactly one upload, got", len(calls))
    sys.exit(1)
content = calls[0]
if "def test_fail" not in content:
    print("FAIL(R4.2): uploaded content lacks failing test representation:", repr(content))
    sys.exit(1)
print("PASS: failed-only mode uploads once with failing representation; no upload otherwise")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. R1.1/R1.3: the encoded request body sets the highlighter
language parameter to `text` and declares NO python-specific highlighter.
Holds on patched tree, must FAIL at base (base uses lexer=python3)."""
import sys
import urllib.parse
import urllib.request
from _pytest import pastebin

captured = {}
def mocked(url, data):
    captured["url"] = url
    captured["data"] = data
    class DF:
        def read(self):
            return b'View <a href="/raw/3c0c6750bd">raw</a>.'
    return DF()
urllib.request.urlopen = mocked

pastebin.create_new_paste(b"full-paste-contents")
data = captured["data"]
body = data.decode() if isinstance(data, (bytes, bytearray)) else data
params = dict(urllib.parse.parse_qsl(body))
print("body:", body)
print("lexer:", params.get("lexer"))

ok = params.get("lexer") == "text"
# must NOT declare any python-specific highlighter
py_lexer = params.get("lexer", "").lower().startswith("python")
if not ok:
    print("FAIL: lexer is not 'text'")
    sys.exit(1)
if py_lexer:
    print("FAIL: python-specific lexer declared")
    sys.exit(1)
print("PASS: lexer=text, no python-specific highlighter")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5809: gold patch changes create_new_paste's lexer from 'python3'/'python' (version-dependent) to the constant 'text'. Hidden F2P: testing/test_pastebin.py::TestPaste::test_create_new_paste, which asserts lexer=='text' plus the full request contents/return value.

7 probes, each standalone (stdlib + _pytest package, no pytest):
- probe_1 (R1.1/R1.3, POSITIVE CONTROL): encodes request body sets lexer=text and no python-specific highlighter. HOLDS patched (lexer=text), FAILS at base (lexer=python3), FAILS under weak candidate (lexer=plaintext). Discriminates.
- probe_2 (R1.2): AST-inspects create_new_paste; lexer value must be constant 'text' not conditional on sys.version_info. HOLDS patched; FAILS at base (IfExp on version_info); FAILS under weak candidate (constant 'plaintext').
- probe_3 (R2.1-2.5): code==contents, expiry=1week, url=https://bpaste.net, data is bytes, params exactly {code,lexer,expiry}. HOLDS patched.
- probe_4 (R3.1): returns https://bpaste.net/show/3c0c6750bd from raw href. HOLDS patched.
- probe_5 (R3.2): on a response with NO raw reference, create_new_paste must NOT return a show-URL. Faithful reading: a raise also satisfies 'shall not return a show-URL'. HOLDS patched (raises TypeError on 'bad response: '+bytes). NOTE: the prior recorded G-EQ VIOLATION used a probe that demanded a graceful non-raising return here — that is an OVER-STRONG reading; R3.2 only forbids returning a show-URL, which the raise honors. So the prior fail was an audit-protocol artifact, not a real requirements defect.
- probe_6 (R5.1/R5.2/R5.3/R6.1): drives pytest_configure/pytest_unconfigure with fakes; tee encodes utf-8 (percent-encoded %E2%98%BA present), uploads exactly once, emits separator + 'pastebin session-log' URL line. HOLDS patched.
- probe_7 (R4.1/R4.2/R4.3): pytest_terminal_summary uploads nothing when mode!=failed; uploads exactly once in failed mode with failing test representation. HOLDS patched.

All 7 HOLD on the gold-patched tree. Positive control probe_1 HOLDS patched and FAILS at base (prepatch reproduced). 

Wrong-fix candidate weak.diff sets lexer='plaintext' (a plausible but wrong 'neutral' lexer a weak reading permits). Probes 1 and 2 REJECT it — exactly mirroring the hidden test's lexer=='text' assertion, so that candidate would NOT resolve. This demonstrates the suite discriminates wrong implementations on the load-bearing behavior. No requirements-conforming alternative found that fails the hidden test. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. R1.1/R1.3: the encoded request body sets the highlighter
language parameter to `text` and declares NO python-specific highlighter.
Holds on patched tree, must FAIL at base (base uses lexer=python3)."""
import sys
import urllib.parse
import urllib.request
from _pytest import pastebin

captured = {}
def mocked(url, data):
    captured["url"] = url
    captured["data"] = data
    class DF:
        def read(self):
            return b'View <a href="/raw/3c0c6750bd">raw</a>.'
    return DF()
urllib.request.urlopen = mocked

pastebin.create_new_paste(b"full-paste-contents")
data = captured["data"]
body = data.decode() if isinstance(data, (bytes, bytearray)) else data
params = dict(urllib.parse.parse_qsl(body))
print("body:", body)
print("lexer:", params.get("lexer"))

ok = params.get("lexer") == "text"
# must NOT declare any python-specific highlighter
py_lexer = params.get("lexer", "").lower().startswith("python")
if not ok:
    print("FAIL: lexer is not 'text'")
    sys.exit(1)
if py_lexer:
    print("FAIL: python-specific lexer declared")
    sys.exit(1)
print("PASS: lexer=text, no python-specific highlighter")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5809: gold patch changes create_new_paste's lexer from 'python3'/'python' (version-dependent) to the constant 'text'. Hidden F2P: testing/test_pastebin.py::TestPaste::test_create_new_paste, which asserts lexer=='text' plus the full request contents/return value.

7 probes, each standalone (stdlib + _pytest package, no pytest):
- probe_1 (R1.1/R1.3, POSITIVE CONTROL): encodes request body sets lexer=text and no python-specific highlighter. HOLDS patched (lexer=text), FAILS at base (lexer=python3), FAILS under weak candidate (lexer=plaintext). Discriminates.
- probe_2 (R1.2): AST-inspects create_new_paste; lexer value must be constant 'text' not conditional on sys.version_info. HOLDS patched; FAILS at base (IfExp on version_info); FAILS under weak candidate (constant 'plaintext').
- probe_3 (R2.1-2.5): code==contents, expiry=1week, url=https://bpaste.net, data is bytes, params exactly {code,lexer,expiry}. HOLDS patched.
- probe_4 (R3.1): returns https://bpaste.net/show/3c0c6750bd from raw href. HOLDS patched.
- probe_5 (R3.2): on a response with NO raw reference, create_new_paste must NOT return a show-URL. Faithful reading: a raise also satisfies 'shall not return a show-URL'. HOLDS patched (raises TypeError on 'bad response: '+bytes). NOTE: the prior recorded G-EQ VIOLATION used a probe that demanded a graceful non-raising return here — that is an OVER-STRONG reading; R3.2 only forbids returning a show-URL, which the raise honors. So the prior fail was an audit-protocol artifact, not a real requirements defect.
- probe_6 (R5.1/R5.2/R5.3/R6.1): drives pytest_configure/pytest_unconfigure with fakes; tee encodes utf-8 (percent-encoded %E2%98%BA present), uploads exactly once, emits separator + 'pastebin session-log' URL line. HOLDS patched.
- probe_7 (R4.1/R4.2/R4.3): pytest_terminal_summary uploads nothing when mode!=failed; uploads exactly once in failed mode with failing test representation. HOLDS patched.

All 7 HOLD on the gold-patched tree. Positive control probe_1 HOLDS patched and FAILS at base (prepatch reproduced). 

Wrong-fix candidate weak.diff sets lexer='plaintext' (a plausible but wrong 'neutral' lexer a weak reading permits). Probes 1 and 2 REJECT it — exactly mirroring the hidden test's lexer=='text' assertion, so that candidate would NOT resolve. This demonstrates the suite discriminates wrong implementations on the load-bearing behavior. No requirements-conforming alternative found that fails the hidden test. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: R1-R3 pin the changed helper's full observable output (not merely the single lexer line), and R4-R6 fence the unchanged surrounding plugin (failed-only / all-output / non-ASCII) as preservation constraints matching the three PASS_TO_PASS tests. The G-EQ / G-PANEL-1 fail is a separate spec-too-weak concern: a probe expected create_new_paste to *return* gracefully on a non-matching response, but the patched code raises TypeError there (a pre-existing bug the gold patch did not touch). That is a weakness/coverage issue in a different lane, not a faithfulness divergence — no requirement mandates behavior the patched code lacks, forbids behavior it has, pins a wrong boundary, or invents behavior. Verified via nl_attack probes on the gold-patched tree in the instance image; issue explicitly requests lexer python3->text; FAIL_TO_PASS test asserts lexer='text', bytes, url, code=.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The central change (lexer python3->text, create_new_paste in src/_pytest/pastebin.py, bpaste.net target, 'not Python code but arbitrary text') is entirely disclosed in the public problem_statement, including the exact 'text' value. Non-public specifics in the doc — expiry=1week, code=contents, the https://bpaste.net/show/<id> return form, the raw-paste reference, ASCII-encoded bytes payload, UTF-8 non-ASCII handling — are all pre-existing behavior of pastebin.py readable from the module source, not derived from the hidden tests or gold edit; describing them is legitimate localization. No test file path (testing/test_pastebin.py), class/function names (TestPaste::test_create_new_paste, TestPasteCapture::test_failed/test_all/test_non_ascii_paste_text), parametrization ids, or verbatim test literals (e.g. 'code=full-paste-contents', 'lexer=%s') are transmitted. Req 4/5/6 translate the PASS_TO_PASS scenarios into behavioral requirements (failed-only mode, all-output tee, non-ASCII) rather than reproducing the test code; the pass/fail/skip enumeration describes observable behavior, not the test parametrization. The fix invents no new identifiers.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
