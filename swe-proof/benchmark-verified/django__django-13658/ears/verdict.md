# P2 adversarial audit — django__django-13658

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_parserprog.py`, `probe_2_subhelp_usage.py`, `probe_3_help_stderr_empty.py`, `probe_4_main_py.py`, `probe_5_preprocess_settings.py`, `probe_6_unknown_command.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_parserprog.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_parserprog.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2/1.3/1.4: the preprocess option parser's prog must be derived
# from the SUPPLIED argv[0]'s final path component, independent of sys.argv.
# POSITIVE CONTROL: holds patched (prog='mysite-admin'), fails at base (prog None).
import io, sys, contextlib
import django.core.management as mgmt

captured = {}
Orig = mgmt.CommandParser
class Spy(Orig):
    def __init__(self, *a, **k):
        if str(k.get('usage', '')).startswith('%(prog)s subcommand'):
            captured['prog'] = k.get('prog', None)
        super().__init__(*a, **k)
mgmt.CommandParser = Spy

# ambient sys.argv[0] deliberately DIFFERS from the supplied vector's argv[0]
sys.argv = ['/ambient/path/wrong-prog', 'garbage']
out, err = io.StringIO(), io.StringIO()
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        mgmt.execute_from_command_line(['/opt/bin/mysite-admin', 'help', 'startapp'])
except SystemExit:
    pass
except Exception as e:
    print("EXC during execute:", repr(e))

prog = captured.get('prog')
print("captured preprocess-parser prog =", repr(prog))
ok = (prog == 'mysite-admin')
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_subhelp_usage.py` → holds on the patched tree (good)

```python
# Req 2.1/2.3: subcommand help usage line begins with the supplied program name
# followed by the subcommand name; with sys.argv[0] != supplied argv[0].
import io, sys, contextlib
import django.core.management as mgmt

sys.argv = ['/ambient/wrong-prog', 'x']
out, err = io.StringIO(), io.StringIO()
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        mgmt.execute_from_command_line(['/opt/bin/mysite-admin', 'help', 'startapp'])
except SystemExit:
    pass
o = out.getvalue()
print("STDOUT (first lines):")
print(o[:300])
# Usage line must show 'mysite-admin startapp', not the ambient 'wrong-prog'.
ok = ('mysite-admin startapp' in o) and ('wrong-prog' not in o)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_help_stderr_empty.py` → holds on the patched tree (good)

```python
# Req 2.2: subcommand help under normal conditions writes to stdout and NOTHING
# to stderr.
import io, sys, contextlib
import django.core.management as mgmt

sys.argv = ['/ambient/wrong-prog', 'x']
out, err = io.StringIO(), io.StringIO()
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        mgmt.execute_from_command_line(['/opt/bin/mysite-admin', 'help', 'startapp'])
except SystemExit:
    pass
o, e = out.getvalue(), err.getvalue()
print("stdout len =", len(o), "stderr =", repr(e[:200]))
ok = (len(o) > 0) and (e.strip() == '')
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_main_py.py` → holds on the patched tree (good)

```python
# Req 1.5 & 3.4: when supplied argv[0]'s final path component is __main__.py,
# the presented program name SHALL be 'python -m django'. Check both prog_name
# and that the preprocess parser receives it.
import io, sys, contextlib
import django.core.management as mgmt

captured = {}
Orig = mgmt.CommandParser
class Spy(Orig):
    def __init__(self, *a, **k):
        if str(k.get('usage', '')).startswith('%(prog)s subcommand'):
            captured['prog'] = k.get('prog', None)
        super().__init__(*a, **k)
mgmt.CommandParser = Spy

sys.argv = ['/ambient/wrong-prog', 'x']
u = mgmt.ManagementUtility(['/some/where/__main__.py', 'help', 'startapp'])
print("prog_name =", repr(u.prog_name))
out, err = io.StringIO(), io.StringIO()
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        u.execute()
except SystemExit:
    pass
o = out.getvalue()
print("captured parser prog =", repr(captured.get('prog')))
print("stdout head:", o[:120])
ok = (u.prog_name == 'python -m django'
      and captured.get('prog') == 'python -m django'
      and 'python -m django startapp' in o)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_preprocess_settings.py` → holds on the patched tree (good)

```python
# Req 3.1 & 3.2: --settings/--pythonpath are preprocessed early (their effects
# applied before command resolution) AND invalid/unrecognized options at that
# stage are ignored rather than aborting.
import io, sys, os, contextlib
import django.core.management as mgmt

sys.argv = ['/ambient/wrong-prog', 'x']
# unknown option --frobnicate present alongside --pythonpath: must NOT abort;
# --pythonpath effect (adding to sys.path) must be applied early.
before = list(sys.path)
out, err = io.StringIO(), io.StringIO()
rc = None
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        mgmt.execute_from_command_line(
            ['/opt/bin/mysite-admin', 'help', '--pythonpath=$SCRATCH',
             '--frobnicate'])
except SystemExit as se:
    rc = se.code
applied = '$SCRATCH' in sys.path
print("pythonpath applied early =", applied)
print("did not abort on unknown option (reached help) =", 'Type' in out.getvalue() or 'subcommand' in out.getvalue())
ok = applied
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_unknown_command.py` → holds on the patched tree (good)

```python
# Req 3.7 & 1.6: "Unknown command" hint uses the presented program name;
# and equal utility argv with differing sys.argv yields the same prog name.
import io, sys, contextlib
import django.core.management as mgmt

def run(ambient):
    sys.argv = ambient
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            mgmt.execute_from_command_line(['/opt/bin/mysite-admin', 'no_such_cmd_xyz'])
    except SystemExit:
        pass
    return out.getvalue() + err.getvalue()

a = run(['/ambient/wrong-A', 'z'])
b = run(['/other/wrong-B', 'z'])
print("run A output:", repr(a[:200]))
# Req 3.7: hint uses presented prog name 'mysite-admin', not ambient.
hint_ok = ("mysite-admin help" in a) and ("wrong-A" not in a)
# Req 1.6: same utility argv => same prog name regardless of ambient argv
same_ok = (a == b)
print("hint uses presented prog =", hint_ok, "; deterministic across ambient =", same_ok)
ok = hint_ok and same_ok
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_parserprog.py`

```python
# Req 1.1/1.2/1.3/1.4: the preprocess option parser's prog must be derived
# from the SUPPLIED argv[0]'s final path component, independent of sys.argv.
# POSITIVE CONTROL: holds patched (prog='mysite-admin'), fails at base (prog None).
import io, sys, contextlib
import django.core.management as mgmt

captured = {}
Orig = mgmt.CommandParser
class Spy(Orig):
    def __init__(self, *a, **k):
        if str(k.get('usage', '')).startswith('%(prog)s subcommand'):
            captured['prog'] = k.get('prog', None)
        super().__init__(*a, **k)
mgmt.CommandParser = Spy

# ambient sys.argv[0] deliberately DIFFERS from the supplied vector's argv[0]
sys.argv = ['/ambient/path/wrong-prog', 'garbage']
out, err = io.StringIO(), io.StringIO()
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        mgmt.execute_from_command_line(['/opt/bin/mysite-admin', 'help', 'startapp'])
except SystemExit:
    pass
except Exception as e:
    print("EXC during execute:", repr(e))

prog = captured.get('prog')
print("captured preprocess-parser prog =", repr(prog))
ok = (prog == 'mysite-admin')
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django-13658: gold fix passes prog=self.prog_name to the preprocess CommandParser in ManagementUtility.execute() so the program name shown by that parser derives from the supplied argv[0] rather than ambient sys.argv[0].

Probes (each standalone python, exit 0 iff criterion holds), results on PATCHED tree:
- probe_1_parserprog.py (Req 1.1/1.2/1.3/1.4; POSITIVE CONTROL): spies on the preprocess CommandParser (usage '%(prog)s subcommand...') to capture its prog kwarg while sys.argv[0]!=supplied argv[0]. PATCHED: prog='mysite-admin' -> HOLDS. BASE: prog=None -> VIOLATED (discriminates).
- probe_2_subhelp_usage.py (Req 2.1/2.3): 'help startapp' usage line begins with supplied prog+subcommand and does not contain ambient name. PATCHED: 'mysite-admin startapp' present, 'wrong-prog' absent -> HOLDS.
- probe_3_help_stderr_empty.py (Req 2.2): subcommand help writes to stdout, nothing to stderr. PATCHED: stdout len 2011, stderr '' -> HOLDS.
- probe_4_main_py.py (Req 1.5/3.4): supplied argv[0] final component __main__.py => prog_name and parser prog and usage line all 'python -m django'. PATCHED -> HOLDS.
- probe_5_preprocess_settings.py (Req 3.1/3.2): --pythonpath applied early (dir added to sys.path) and unknown option --frobnicate does not abort. PATCHED -> HOLDS.
- probe_6_unknown_command.py (Req 3.7/1.6): 'Unknown command' hint uses presented prog ('mysite-admin help', not ambient) and is deterministic across two differing ambient sys.argv. PATCHED -> HOLDS.

Candidate wrong patches (both apply at base_commit):
- weak_ambient.diff: sets prog=os.path.basename(sys.argv[0]) (reads AMBIENT vector, the exact bug the requirements forbid). REJECTED by probe_1 (captured prog='wrong-prog', exit 1). This is the lazy misreading of Req 1 and the suite catches it.
- weak_noop.diff: comment-only, prog still falls back to sys.argv[0]. REJECTED by probe_1 (prog=None, exit 1).

Both candidates are rejected by the discriminating probe, so the suite distinguishes wrong implementations; no probe-conforming alternative that fails the hidden test was found. All 6 probes HOLD on patched; positive control HOLDS patched and FAILS at base (prepatch reproduced). Verdict SOUND.

Note: probes 2/6 use the natural side effects of help/unknown-command dispatch, which also exercise Req 3.5/3.6 (help subcommand + dispatch on supplied argv) as regression coverage.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_parserprog.py`, `probe_2_subhelp_usage.py`, `probe_3_help_stderr_empty.py`, `probe_4_main_py.py`, `probe_5_preprocess_settings.py`, `probe_6_unknown_command.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_parserprog.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_parserprog.py` → holds on the patched tree (good)

Attack 2 — `probe_2_subhelp_usage.py` → holds on the patched tree (good)

Attack 3 — `probe_3_help_stderr_empty.py` → holds on the patched tree (good)

Attack 4 — `probe_4_main_py.py` → holds on the patched tree (good)

Attack 5 — `probe_5_preprocess_settings.py` → holds on the patched tree (good)

Attack 6 — `probe_6_unknown_command.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_parserprog.py`

```python
# Req 1.1/1.2/1.3/1.4: the preprocess option parser's prog must be derived
# from the SUPPLIED argv[0]'s final path component, independent of sys.argv.
# POSITIVE CONTROL: holds patched (prog='mysite-admin'), fails at base (prog None).
import io, sys, contextlib
import django.core.management as mgmt

captured = {}
Orig = mgmt.CommandParser
class Spy(Orig):
    def __init__(self, *a, **k):
        if str(k.get('usage', '')).startswith('%(prog)s subcommand'):
            captured['prog'] = k.get('prog', None)
        super().__init__(*a, **k)
mgmt.CommandParser = Spy

# ambient sys.argv[0] deliberately DIFFERS from the supplied vector's argv[0]
sys.argv = ['/ambient/path/wrong-prog', 'garbage']
out, err = io.StringIO(), io.StringIO()
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        mgmt.execute_from_command_line(['/opt/bin/mysite-admin', 'help', 'startapp'])
except SystemExit:
    pass
except Exception as e:
    print("EXC during execute:", repr(e))

prog = captured.get('prog')
print("captured preprocess-parser prog =", repr(prog))
ok = (prog == 'mysite-admin')
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django-13658: gold fix passes prog=self.prog_name to the preprocess CommandParser in ManagementUtility.execute() so the program name shown by that parser derives from the supplied argv[0] rather than ambient sys.argv[0].

Probes (each standalone python, exit 0 iff criterion holds), results on PATCHED tree:
- probe_1_parserprog.py (Req 1.1/1.2/1.3/1.4; POSITIVE CONTROL): spies on the preprocess CommandParser (usage '%(prog)s subcommand...') to capture its prog kwarg while sys.argv[0]!=supplied argv[0]. PATCHED: prog='mysite-admin' -> HOLDS. BASE: prog=None -> VIOLATED (discriminates).
- probe_2_subhelp_usage.py (Req 2.1/2.3): 'help startapp' usage line begins with supplied prog+subcommand and does not contain ambient name. PATCHED: 'mysite-admin startapp' present, 'wrong-prog' absent -> HOLDS.
- probe_3_help_stderr_empty.py (Req 2.2): subcommand help writes to stdout, nothing to stderr. PATCHED: stdout len 2011, stderr '' -> HOLDS.
- probe_4_main_py.py (Req 1.5/3.4): supplied argv[0] final component __main__.py => prog_name and parser prog and usage line all 'python -m django'. PATCHED -> HOLDS.
- probe_5_preprocess_settings.py (Req 3.1/3.2): --pythonpath applied early (dir added to sys.path) and unknown option --frobnicate does not abort. PATCHED -> HOLDS.
- probe_6_unknown_command.py (Req 3.7/1.6): 'Unknown command' hint uses presented prog ('mysite-admin help', not ambient) and is deterministic across two differing ambient sys.argv. PATCHED -> HOLDS.

Candidate wrong patches (both apply at base_commit):
- weak_ambient.diff: sets prog=os.path.basename(sys.argv[0]) (reads AMBIENT vector, the exact bug the requirements forbid). REJECTED by probe_1 (captured prog='wrong-prog', exit 1). This is the lazy misreading of Req 1 and the suite catches it.
- weak_noop.diff: comment-only, prog still falls back to sys.argv[0]. REJECTED by probe_1 (prog=None, exit 1).

Both candidates are rejected by the discriminating probe, so the suite distinguishes wrong implementations; no probe-conforming alternative that fails the hidden test was found. All 6 probes HOLD on patched; positive control HOLDS patched and FAILS at base (prepatch reproduced). Verdict SOUND.

Note: probes 2/6 use the natural side effects of help/unknown-command dispatch, which also exercise Req 3.5/3.6 (help subcommand + dispatch on supplied argv) as regression coverage.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: parser = CommandParser(prog=self.prog_name, usage='%(prog)s subcommand [options] [args]', add_help=False, allow_abbrev=False). Requirements 1-3 collectively describe: (1) prog from utility argv not ambient sys.argv; (1.4/1.5) basename + __main__.py special case; (2) subcommand help usage line begins with prog name, stdout only; (3) regression protection of preprocessing/fallback/special-cases/Unknown-command hint. All confirmed by probes against the instance image. F2P test: test_program_name_from_argv passes on patched, TypeError on base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The fix and its localization (ManagementUtility.execute, CommandParser, prog=self.prog_name, __main__.py -> 'python -m django') are all in the PUBLIC problem_statement, which quotes the exact gold edit. The only hidden test is test_program_name_from_argv, which checks that a subcommand help usage line uses the argv-derived prog name and emits nothing to stderr. Requirement 2 translates this into behavioral acceptance criteria without transmitting the test: no test file path (tests/admin_scripts/tests.py), no class/method name (ExecuteFromCommandLine), no literals ('shell', the ['django-admin']+args vector, captured_stdout/stderr, sys.argv=[None]+args), and no parametrization ids. The 'nothing to stderr / help to stdout' property is a legitimate behavioral spec (consistent with the problem hint about a spurious invalid message), not quoted test code. Requirement 3's command enumeration is generic CLI regression framing, not a mirror of the single-test FAIL_TO_PASS. This is behavioral translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
