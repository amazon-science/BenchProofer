# P2 adversarial audit — sphinx-doc__sphinx-9320

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
"""Positive control — Requirement 1 criteria 1 & 2.
An empty entry at the 'new root path (or just Enter to exit)' re-prompt SHALL
be accepted (no ValidationError) and cause ask_user to raise SystemExit(1).

Patched: first empty entry -> is_path_or_empty returns '' -> SystemExit(1).
Base:    '' rejected by is_path ('valid path name') -> loops, never exits.
We cap term_input at a few calls: if it's called more than once we conclude
the empty entry was NOT accepted (base behaviour) -> FAIL.
"""
import os, sys, tempfile
import sphinx.cmd.quickstart as qs

class Stop(Exception):
    pass

tmp = tempfile.mkdtemp()
open(os.path.join(tmp, "conf.py"), "w").close()  # existing sphinx project

calls = {"n": 0}
def fake_input(prompt):
    calls["n"] += 1
    if calls["n"] > 3:
        raise Stop("term_input called >3 times without exiting")
    return ""  # user just presses Enter

qs.term_input = fake_input

d = {"path": tmp}
raised = None
try:
    qs.ask_user(d)
except SystemExit as e:
    raised = e
except Stop as s:
    print("OBSERVED: no exit;", s)
    sys.exit(1)

print("term_input calls:", calls["n"])
print("SystemExit raised:", raised is not None, "code:", getattr(raised, "code", None))
if raised is None:
    print("FAIL: ask_user returned without SystemExit")
    sys.exit(1)
if calls["n"] != 1:
    print("FAIL: empty entry not accepted on first try")
    sys.exit(1)
if raised.code != 1:
    print("FAIL: exit code is not 1")
    sys.exit(1)
print("HOLD: empty entry accepted, SystemExit(1) raised after one prompt")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1 criterion 4 — non-empty entry at the re-prompt still gets the
existing-directory validation: a non-existent dir is REJECTED (re-prompt),
an existing dir with no conf.py is ACCEPTED and flow leaves the loop.

Reply 1 = bogus non-existent path (must be rejected -> re-prompt, same prompt);
reply 2 = a fresh existing dir with no conf.py (must be accepted -> loop exits).
We detect loop-exit when ask_user asks a prompt that is NOT the root-path
re-prompt (it proceeds to 'sep'/etc.), and stop there.
"""
import os, sys, tempfile
import sphinx.cmd.quickstart as qs

class LoopExited(Exception):
    pass
class Stop(Exception):
    pass

bad = tempfile.mkdtemp()
open(os.path.join(bad, "conf.py"), "w").close()
good = tempfile.mkdtemp()
nonexist = os.path.join(bad, "does_not_exist_xyz")
assert not os.path.isdir(nonexist)

replies = [nonexist, good]
seen = []
def fake_input(prompt):
    if "root path" not in prompt:
        # proceeded past the conf.py loop -> success point
        raise LoopExited(prompt)
    if not replies:
        raise Stop("ran out of root-path replies")
    r = replies.pop(0); seen.append(r); return r
qs.term_input = fake_input

d = {"path": bad}
exited = False
try:
    qs.ask_user(d)
except LoopExited:
    exited = True
except SystemExit as e:
    print("FAIL: SystemExit raised for a non-empty valid dir:", e.code); sys.exit(1)
except Stop as s:
    print("FAIL:", s); sys.exit(1)

print("root-path replies consumed:", seen)
print("final d['path']:", d.get("path"))
if len(seen) != 2:
    print("FAIL: bogus non-existent path was not rejected (only %d prompt)" % len(seen)); sys.exit(1)
if not exited:
    print("FAIL: loop did not exit after valid dir"); sys.exit(1)
if d.get("path") != good:
    print("FAIL: valid existing dir not accepted as new path"); sys.exit(1)
print("HOLD: bogus path rejected, valid existing dir accepted, loop exited")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 1 criterion 3 — WHILE an existing conf.py remains detectable and
the user has NOT supplied an empty entry, ask_user keeps re-prompting rather
than proceeding. Give it two non-empty answers that both still point at dirs
containing conf.py: it must re-prompt (2+ prompts) and NOT proceed to later
questions. Then an empty entry exits.
"""
import os, sys, tempfile
import sphinx.cmd.quickstart as qs

class Reached(Exception):
    pass

d1 = tempfile.mkdtemp(); open(os.path.join(d1, "conf.py"), "w").close()
d2 = tempfile.mkdtemp(); open(os.path.join(d2, "conf.py"), "w").close()

replies = [d2, ""]   # first: another existing sphinx proj; then Enter -> exit
seen = []
def fake_input(prompt):
    # If we reach any prompt that is not the root-path re-prompt, the loop was
    # wrongly exited.
    if "root path" not in prompt:
        raise Reached("proceeded to a non-rootpath prompt: %r" % prompt)
    if not replies:
        raise Reached("ran out of replies")
    r = replies.pop(0); seen.append(r); return r
qs.term_input = fake_input

d = {"path": d1}
try:
    qs.ask_user(d)
except SystemExit as e:
    print("SystemExit code:", e.code, "prompts seen:", len(seen))
    if len(seen) != 2:
        print("FAIL: did not re-prompt for the still-conf.py dir")
        sys.exit(1)
    print("HOLD: re-prompted while conf.py present, then exited on empty")
    sys.exit(0)
except Reached as r:
    print("FAIL:", r)
    sys.exit(1)
print("FAIL: no SystemExit")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2 — initial root-path prompt stays strict.
2.1: is_path rejects a non-existent path with the 'valid path name' error.
2.2: a bare Enter at the initial root-path prompt selects the default ('.'),
     NOT treated as empty/exit. We verify via do_prompt with default '.'.
Also verify is_path_or_empty is NOT what the initial prompt uses: an empty
answer with default '.' must yield '.', and is_path itself must reject ''.
"""
import os, sys, tempfile
import sphinx.cmd.quickstart as qs
from sphinx.cmd.quickstart import is_path, ValidationError, do_prompt

ok = True

# 2.1 non-existent path rejected by the strict validator
nonexist = os.path.join(tempfile.mkdtemp(), "nope")
try:
    is_path(nonexist)
    print("FAIL 2.1: is_path accepted a non-existent path"); ok = False
except ValidationError as e:
    print("2.1 rejected non-existent path:", str(e))

# is_path must reject '' too (strict prompt cannot exit on empty)
try:
    is_path("")
    print("FAIL 2.1b: is_path accepted empty string"); ok = False
except ValidationError:
    print("2.1b is_path rejects empty string (good)")

# 2.2 bare Enter -> default '.' at the initial prompt
qs.term_input = lambda prompt: ""    # user presses Enter
val = do_prompt("Root path for the documentation", ".", is_path)
print("2.2 do_prompt returned:", repr(val))
if val != ".":
    print("FAIL 2.2: bare Enter did not select default '.'"); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 3 — do_prompt keeps its behavior.
3.1 strips surrounding whitespace before validating.
3.2 empty/whitespace-only response with a default substitutes the default.
3.3 on ValidationError, reports and re-prompts (does not return).
3.4 returns the validated value; non-ASCII handled correctly.
"""
import sys
import sphinx.cmd.quickstart as qs
from sphinx.cmd.quickstart import do_prompt, nonempty, ValidationError

ok = True

# 3.1 whitespace stripped before validation
qs.term_input = lambda p: "   hello   "
v = do_prompt("q", None, nonempty)
print("3.1 stripped ->", repr(v))
if v != "hello":
    print("FAIL 3.1"); ok = False

# 3.2 whitespace-only w/ default -> default
qs.term_input = lambda p: "    "
v = do_prompt("q", "mydefault", nonempty)
print("3.2 default-substituted ->", repr(v))
if v != "mydefault":
    print("FAIL 3.2"); ok = False

# 3.3 ValidationError -> re-prompt (not return). First reply invalid, then ok.
seq = iter(["", "good"])   # nonempty rejects '' -> must re-prompt
def fi(p): return next(seq)
qs.term_input = fi
v = do_prompt("q", None, nonempty)
print("3.3 re-prompted then returned ->", repr(v))
if v != "good":
    print("FAIL 3.3"); ok = False

# 3.4 non-ASCII round-trips through the validated value
qs.term_input = lambda p: "café—naïve"
v = do_prompt("q", None, nonempty)
print("3.4 non-ascii ->", repr(v))
if v != "café—naïve":
    print("FAIL 3.4"); ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 4 — unrelated quickstart behavior preserved.
Run generate() with default answers into a fresh dir and confirm the expected
project files exist, plus the preserved settings: suffix '.rst', master/root
document 'index', and generated files use the correct line-ending convention.
"""
import os, sys, tempfile
import sphinx.cmd.quickstart as qs

d = {
    "path": tempfile.mkdtemp(),
    "sep": False,
    "dot": "_",
    "project": "Proj",
    "author": "Auth",
    "version": "1.0",
    "release": "1.0",
    "language": "en",
    "suffix": ".rst",
    "master": "index",
    "makefile": True,
    "batchfile": True,
}
qs.generate(d, overwrite=True)

root = d["path"]
conf = os.path.join(root, "conf.py")
index = os.path.join(root, "index.rst")
ok = True
for f in (conf, index):
    print("exists", f, os.path.isfile(f))
    if not os.path.isfile(f):
        print("FAIL missing", f); ok = False

# master/root document name preserved
if d.get("root_doc") != "index" or d.get("master") != "index":
    print("FAIL master/root_doc not 'index':", d.get("master"), d.get("root_doc")); ok = False
else:
    print("master/root_doc == index")

# suffix preserved -> index file uses .rst
if not os.path.isfile(index):
    print("FAIL suffix: index.rst not produced"); ok = False

# line-ending convention: generated conf.py written in text mode (no CRLF on posix)
with open(conf, "rb") as fh:
    data = fh.read()
print("conf.py has CRLF:", b"\r\n" in data)
if b"\r\n" in data:
    print("FAIL: unexpected CRLF line endings in generated conf.py"); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Requirement 1 criteria 1 & 2.
An empty entry at the 'new root path (or just Enter to exit)' re-prompt SHALL
be accepted (no ValidationError) and cause ask_user to raise SystemExit(1).

Patched: first empty entry -> is_path_or_empty returns '' -> SystemExit(1).
Base:    '' rejected by is_path ('valid path name') -> loops, never exits.
We cap term_input at a few calls: if it's called more than once we conclude
the empty entry was NOT accepted (base behaviour) -> FAIL.
"""
import os, sys, tempfile
import sphinx.cmd.quickstart as qs

class Stop(Exception):
    pass

tmp = tempfile.mkdtemp()
open(os.path.join(tmp, "conf.py"), "w").close()  # existing sphinx project

calls = {"n": 0}
def fake_input(prompt):
    calls["n"] += 1
    if calls["n"] > 3:
        raise Stop("term_input called >3 times without exiting")
    return ""  # user just presses Enter

qs.term_input = fake_input

d = {"path": tmp}
raised = None
try:
    qs.ask_user(d)
except SystemExit as e:
    raised = e
except Stop as s:
    print("OBSERVED: no exit;", s)
    sys.exit(1)

print("term_input calls:", calls["n"])
print("SystemExit raised:", raised is not None, "code:", getattr(raised, "code", None))
if raised is None:
    print("FAIL: ask_user returned without SystemExit")
    sys.exit(1)
if calls["n"] != 1:
    print("FAIL: empty entry not accepted on first try")
    sys.exit(1)
if raised.code != 1:
    print("FAIL: exit code is not 1")
    sys.exit(1)
print("HOLD: empty entry accepted, SystemExit(1) raised after one prompt")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9320: the re-prompt 'Please enter a new root path (or just Enter to exit)' must accept an empty entry (return unchanged) so ask_user can SystemExit(1), while still applying is_path existing-dir validation to non-empty entries. Gold patch adds is_path_or_empty and wires it in.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): empty entry accepted on the first prompt and ask_user raises SystemExit(1). Runs term_input returning '' with a >3-call tripwire. PATCHED: exit0 (1 prompt, SystemExit code 1). BASE: exit1 — base uses is_path, which rejects '' and loops forever ('term_input called >3 times without exiting'). Discriminates.
- probe_2 (Req 1.4): non-empty entry still gets existing-dir validation — a non-existent path is REJECTED (re-prompt) and a valid existing dir is ACCEPTED (loop exits). PATCHED: HOLD. BASE: HOLD (base already validated non-empty via is_path).
- probe_3 (Req 1.3): while conf.py remains detectable and no empty entry supplied, keeps re-prompting (2 prompts for two conf.py dirs) rather than proceeding; then empty exits. PATCHED: HOLD.
- probe_4 (Req 2.1/2.2): is_path rejects non-existent path and '' with 'valid path name'; bare Enter at initial prompt selects default '.' (not exit). PATCHED: HOLD.
- probe_5 (Req 3.1-3.4): do_prompt strips whitespace, substitutes default on empty, re-prompts on ValidationError, returns validated value, handles non-ASCII. PATCHED: HOLD.
- probe_6 (Req 4): generate() with default answers produces conf.py + index.rst, preserves suffix '.rst', master/root_doc 'index', and no CRLF line endings. PATCHED: HOLD.

Wrong-fix candidate weak.diff: wires the re-prompt to allow_empty instead of is_path_or_empty. It satisfies Req 1.1/1.2 (empty exits) but DROPS the existing-dir validation Req 1.4 mandates. Probe suite REJECTS it: probe_2 VIOLATED (a bogus non-existent path is wrongly accepted, only 1 prompt, loop exits without re-prompting). Demonstrates the suite discriminates a plausible weak reading. probes 1,3,4,5,6 HOLD under it (expected).

Conclusion: >=5 probes hold on the patched tree, positive control fails at base and holds patched (prepatch reproduced), and a requirements-relaxing alternative is caught by the suite. Requirements are faithful and discriminating: SOUND.

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
"""Positive control — Requirement 1 criteria 1 & 2.
An empty entry at the 'new root path (or just Enter to exit)' re-prompt SHALL
be accepted (no ValidationError) and cause ask_user to raise SystemExit(1).

Patched: first empty entry -> is_path_or_empty returns '' -> SystemExit(1).
Base:    '' rejected by is_path ('valid path name') -> loops, never exits.
We cap term_input at a few calls: if it's called more than once we conclude
the empty entry was NOT accepted (base behaviour) -> FAIL.
"""
import os, sys, tempfile
import sphinx.cmd.quickstart as qs

class Stop(Exception):
    pass

tmp = tempfile.mkdtemp()
open(os.path.join(tmp, "conf.py"), "w").close()  # existing sphinx project

calls = {"n": 0}
def fake_input(prompt):
    calls["n"] += 1
    if calls["n"] > 3:
        raise Stop("term_input called >3 times without exiting")
    return ""  # user just presses Enter

qs.term_input = fake_input

d = {"path": tmp}
raised = None
try:
    qs.ask_user(d)
except SystemExit as e:
    raised = e
except Stop as s:
    print("OBSERVED: no exit;", s)
    sys.exit(1)

print("term_input calls:", calls["n"])
print("SystemExit raised:", raised is not None, "code:", getattr(raised, "code", None))
if raised is None:
    print("FAIL: ask_user returned without SystemExit")
    sys.exit(1)
if calls["n"] != 1:
    print("FAIL: empty entry not accepted on first try")
    sys.exit(1)
if raised.code != 1:
    print("FAIL: exit code is not 1")
    sys.exit(1)
print("HOLD: empty entry accepted, SystemExit(1) raised after one prompt")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9320: the re-prompt 'Please enter a new root path (or just Enter to exit)' must accept an empty entry (return unchanged) so ask_user can SystemExit(1), while still applying is_path existing-dir validation to non-empty entries. Gold patch adds is_path_or_empty and wires it in.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): empty entry accepted on the first prompt and ask_user raises SystemExit(1). Runs term_input returning '' with a >3-call tripwire. PATCHED: exit0 (1 prompt, SystemExit code 1). BASE: exit1 — base uses is_path, which rejects '' and loops forever ('term_input called >3 times without exiting'). Discriminates.
- probe_2 (Req 1.4): non-empty entry still gets existing-dir validation — a non-existent path is REJECTED (re-prompt) and a valid existing dir is ACCEPTED (loop exits). PATCHED: HOLD. BASE: HOLD (base already validated non-empty via is_path).
- probe_3 (Req 1.3): while conf.py remains detectable and no empty entry supplied, keeps re-prompting (2 prompts for two conf.py dirs) rather than proceeding; then empty exits. PATCHED: HOLD.
- probe_4 (Req 2.1/2.2): is_path rejects non-existent path and '' with 'valid path name'; bare Enter at initial prompt selects default '.' (not exit). PATCHED: HOLD.
- probe_5 (Req 3.1-3.4): do_prompt strips whitespace, substitutes default on empty, re-prompts on ValidationError, returns validated value, handles non-ASCII. PATCHED: HOLD.
- probe_6 (Req 4): generate() with default answers produces conf.py + index.rst, preserves suffix '.rst', master/root_doc 'index', and no CRLF line endings. PATCHED: HOLD.

Wrong-fix candidate weak.diff: wires the re-prompt to allow_empty instead of is_path_or_empty. It satisfies Req 1.1/1.2 (empty exits) but DROPS the existing-dir validation Req 1.4 mandates. Probe suite REJECTS it: probe_2 VIOLATED (a bogus non-existent path is wrongly accepted, only 1 prompt, loop exits without re-prompting). Demonstrates the suite discriminates a plausible weak reading. probes 1,3,4,5,6 HOLD under it (expected).

Conclusion: >=5 probes hold on the patched tree, positive control fails at base and holds patched (prepatch reproduced), and a requirements-relaxing alternative is caught by the suite. Requirements are faithful and discriminating: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is two hunks: adds is_path_or_empty(x) (empty passthrough, else is_path(x)) and changes only the 'Please enter a new root path (or just Enter to exit)' do_prompt call from is_path to is_path_or_empty; the subsequent `if not d['path']: sys.exit(1)` supplies the exit. The requirements pin exactly this changed observable behavior (empty accepted -> exit 1) rather than a narrow slice, and correctly scope the initial-root-path prompt (Req2) as unchanged (still is_path, default = current dir). Base-commit probe confirms is_path_or_empty does not exist pre-patch (AttributeError), matching the described bug. Modeling boundary is correct and biconditional-ish (empty<->exit, non-empty<->is_path validation). Probe tool truncates stdout source dumps, so behaviors were confirmed via assertion-style probes.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold-invented identifier `is_path_or_empty` is NOT disclosed; the document describes its behavior ("accept an empty entry and return it unchanged") and names only legitimate localization targets `ask_user`, `do_prompt`, `is_path`. No test names, file paths, parametrization ids, or quoted test/gold code appear. The SystemExit status-1 detail (Req 1.2) derives from `sys.exit(1)`, which is UNCHANGED context in the gold patch (pre-existing code), not gold-invented, and matches only the public 'exits' expectation. Req 3/4 translate PASS_TO_PASS behaviors (do_prompt strip/default/nonascii, quickstart defaults/all-answers/eol/extensions) into behavioral preservation requirements rather than reproducing the tests' structure or parametrization. This is behavior description, the intended function of the spec.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
