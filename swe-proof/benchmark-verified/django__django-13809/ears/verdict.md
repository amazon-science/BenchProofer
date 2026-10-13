# P2 adversarial audit — django__django-13809

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
# Positive control: Req2.1 + Req2.2 — skip_checks enabled => no announcement, check() NOT called
import io
from unittest import mock
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'])
django.setup()
from django.core.management import call_command

out = io.StringIO()
with mock.patch('django.core.management.commands.runserver.run'), \
     mock.patch('django.core.management.base.BaseCommand.check_migrations'), \
     mock.patch('django.core.management.base.BaseCommand.check') as mocked_check:
    call_command('runserver', use_reloader=False, skip_checks=True, stdout=out)
    val = out.getvalue()
    print("stdout was:\n", repr(val))
    print("check called:", mocked_check.called)
    ok = ('Performing system checks...' not in val) and (not mocked_check.called)
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req3.1 + 3.2 — skip_checks disabled => announcement written AND check() called
import io
from unittest import mock
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'])
django.setup()
from django.core.management import call_command

out = io.StringIO()
with mock.patch('django.core.management.commands.runserver.run'), \
     mock.patch('django.core.management.base.BaseCommand.check_migrations'), \
     mock.patch('django.core.management.base.BaseCommand.check') as mocked_check:
    call_command('runserver', use_reloader=False, skip_checks=False, stdout=out)
    val = out.getvalue()
    print("stdout was:\n", repr(val))
    print("check called:", mocked_check.called)
    print("check call kwargs:", mocked_check.call_args)
    ok = ('Performing system checks...' in val) and mocked_check.called
    # Req3.2: display_num_errors=True
    if mocked_check.called:
        ok = ok and (mocked_check.call_args.kwargs.get('display_num_errors') is True)
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.1 + 1.4 — --skip-checks is a registered boolean store_true flag, documented as skipping system checks; default disabled (Req1.2)
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.management.commands.runserver import Command

cmd = Command()
parser = cmd.create_parser('manage.py', 'runserver')
# find the skip-checks action
act = None
for a in parser._actions:
    if '--skip-checks' in a.option_strings:
        act = a
        break
print("action:", act)
ok = act is not None
if act is not None:
    print("dest:", act.dest, "nargs:", act.nargs, "const:", getattr(act,'const',None), "default:", act.default)
    print("help:", act.help)
    # boolean flag taking no value: store_true => nargs==0
    ok = ok and (act.nargs == 0)
    # default disabled/false
    ok = ok and (not act.default)
    # documented as skipping system checks
    ok = ok and (act.help is not None and 'check' in act.help.lower())
# Req1.2 default: parse with no args
ns = parser.parse_args([])
print("default skip_checks:", getattr(ns, 'skip_checks', 'MISSING'))
ok = ok and (getattr(ns, 'skip_checks', None) is False)
# Req1.3 supplied => True
ns2 = parser.parse_args(['--skip-checks'])
print("supplied skip_checks:", ns2.skip_checks)
ok = ok and (ns2.skip_checks is True)
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req4.1 — check_migrations runs on EVERY startup regardless of skip_checks (both True and False)
import io
from unittest import mock
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'])
django.setup()
from django.core.management import call_command

def run(skip):
    out = io.StringIO()
    with mock.patch('django.core.management.commands.runserver.run'), \
         mock.patch('django.core.management.base.BaseCommand.check'), \
         mock.patch('django.core.management.base.BaseCommand.check_migrations') as mm:
        call_command('runserver', use_reloader=False, skip_checks=skip, stdout=out)
        return mm.called

c_true = run(True)
c_false = run(False)
print("check_migrations called when skip=True:", c_true)
print("check_migrations called when skip=False:", c_false)
ok = c_true and c_false
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req4.2 + Req2.3/3.3 — banner (version/settings/address) written AND server started (run called)
# on every startup regardless of skip_checks; and the ONLY difference between skip=True/False
# is the system-check announcement line.
import io
from unittest import mock
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'])
django.setup()
from django.core.management import call_command

def run(skip):
    out = io.StringIO()
    with mock.patch('django.core.management.commands.runserver.run') as mocked_run, \
         mock.patch('django.core.management.base.BaseCommand.check_migrations'), \
         mock.patch('django.core.management.base.BaseCommand.check'):
        call_command('runserver', use_reloader=False, skip_checks=skip, addrport='127.0.0.1:8000', stdout=out)
        return out.getvalue(), mocked_run.called

v_true, run_true = run(True)
v_false, run_false = run(False)
print("skip=True stdout:\n", repr(v_true))
print("skip=False stdout:\n", repr(v_false))
print("run called true/false:", run_true, run_false)

ok = run_true and run_false
# banner content present in both
for v in (v_true, v_false):
    ok = ok and (django.get_version() in v)
    ok = ok and ('127.0.0.1' in v and '8000' in v)
    ok = ok and ('settings' in v.lower())

# Req2.3/3.3: the ONLY difference is the "Performing system checks..." block.
# Remove that block from the disabled output and compare to enabled output.
import re
stripped = v_false.replace('Performing system checks...\n\n', '')
# System check identified... line may also appear only via check() which is mocked, so none here.
print("stripped(false) == true ?", stripped == v_true)
ok = ok and (stripped == v_true)
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req2.1 + Req2.2 — skip_checks enabled => no announcement, check() NOT called
import io
from unittest import mock
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'])
django.setup()
from django.core.management import call_command

out = io.StringIO()
with mock.patch('django.core.management.commands.runserver.run'), \
     mock.patch('django.core.management.base.BaseCommand.check_migrations'), \
     mock.patch('django.core.management.base.BaseCommand.check') as mocked_check:
    call_command('runserver', use_reloader=False, skip_checks=True, stdout=out)
    val = out.getvalue()
    print("stdout was:\n", repr(val))
    print("check called:", mocked_check.called)
    ok = ('Performing system checks...' not in val) and (not mocked_check.called)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: add --skip-checks to runserver that omits the system-check announcement + Command.check() call when enabled, leaving all other startup behavior unchanged.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req2.1+2.2, POSITIVE CONTROL): skip_checks=True => 'Performing system checks...' NOT in stdout AND BaseCommand.check() not called. HOLDS patched; VIOLATED at base (skip_checks is an unknown option pre-patch). Discriminates.
- probe_2 (Req3.1+3.2): skip_checks=False => announcement written AND check() called with display_num_errors=True. HOLDS patched.
- probe_3 (Req1.1/1.2/1.3/1.4): --skip-checks registered as store_true (nargs=0), default False, parses to True when supplied, help mentions 'check'. HOLDS patched.
- probe_4 (Req4.1): check_migrations called on every startup for both skip=True and skip=False. HOLDS patched.
- probe_5 (Req4.2 + Req2.3/3.3): run() (serving) called and banner (version, 127.0.0.1:8000, settings) written for both modes; the ONLY textual difference between disabled and enabled output is the 'Performing system checks...\n\n' block (stripped(false)==true). HOLDS patched.

Discriminating power (candidate wrong-fix):
- weak_register_only.diff: registers the --skip-checks flag in add_arguments but does NOT guard the check block in inner_run. REJECTED by probe_1 (announcement/check still fire when skip=True) and probe_5 (extra block => outputs differ beyond the check block). Probes 2/3/4 correctly still hold. This proves the suite discriminates the lazy 'flag but no behavior' fix that a weak reading permits.

No requirement-conforming alternative patch was found: any patch satisfying probe_1 (no announcement + no check() call under skip=True) and probe_2 (both present under skip=False) and probe_5 (only difference is the check block) must implement exactly the gold behavior — guarding the announcement+check pair on the skip_checks option. Hidden test test_skip_checks asserts precisely these facts, so the encoded requirements match the F2P test.

All needed runs completed. 5 probes hold on patched, positive control fails at base, and a wrong-fix candidate is rejected => SOUND.

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
# Positive control: Req2.1 + Req2.2 — skip_checks enabled => no announcement, check() NOT called
import io
from unittest import mock
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'])
django.setup()
from django.core.management import call_command

out = io.StringIO()
with mock.patch('django.core.management.commands.runserver.run'), \
     mock.patch('django.core.management.base.BaseCommand.check_migrations'), \
     mock.patch('django.core.management.base.BaseCommand.check') as mocked_check:
    call_command('runserver', use_reloader=False, skip_checks=True, stdout=out)
    val = out.getvalue()
    print("stdout was:\n", repr(val))
    print("check called:", mocked_check.called)
    ok = ('Performing system checks...' not in val) and (not mocked_check.called)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: add --skip-checks to runserver that omits the system-check announcement + Command.check() call when enabled, leaving all other startup behavior unchanged.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req2.1+2.2, POSITIVE CONTROL): skip_checks=True => 'Performing system checks...' NOT in stdout AND BaseCommand.check() not called. HOLDS patched; VIOLATED at base (skip_checks is an unknown option pre-patch). Discriminates.
- probe_2 (Req3.1+3.2): skip_checks=False => announcement written AND check() called with display_num_errors=True. HOLDS patched.
- probe_3 (Req1.1/1.2/1.3/1.4): --skip-checks registered as store_true (nargs=0), default False, parses to True when supplied, help mentions 'check'. HOLDS patched.
- probe_4 (Req4.1): check_migrations called on every startup for both skip=True and skip=False. HOLDS patched.
- probe_5 (Req4.2 + Req2.3/3.3): run() (serving) called and banner (version, 127.0.0.1:8000, settings) written for both modes; the ONLY textual difference between disabled and enabled output is the 'Performing system checks...\n\n' block (stripped(false)==true). HOLDS patched.

Discriminating power (candidate wrong-fix):
- weak_register_only.diff: registers the --skip-checks flag in add_arguments but does NOT guard the check block in inner_run. REJECTED by probe_1 (announcement/check still fire when skip=True) and probe_5 (extra block => outputs differ beyond the check block). Probes 2/3/4 correctly still hold. This proves the suite discriminates the lazy 'flag but no behavior' fix that a weak reading permits.

No requirement-conforming alternative patch was found: any patch satisfying probe_1 (no announcement + no check() call under skip=True) and probe_2 (both present under skip=False) and probe_5 (only difference is the check block) must implement exactly the gold behavior — guarding the announcement+check pair on the skip_checks option. Hidden test test_skip_checks asserts precisely these facts, so the encoded requirements match the F2P test.

All needed runs completed. 5 probes hold on patched, positive control fails at base, and a wrong-fix candidate is rejected => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds parser.add_argument('--skip-checks', action='store_true', help='Skip system checks.') and wraps the announcement + self.check(display_num_errors=True) in `if not options['skip_checks']:`. The requirements pin exactly this observable behavior — the skip-checks branch controlling BOTH the announcement and the check call together, while migration check/banner/serving are preserved. Requirements correctly model the full changed behavior, not a narrow slice. Probe run inside instance image: HOLDS (gold-patched) exit=0; VIOLATED (base) — flag unrecognized.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All identifiers in requirements.md are public via problem_statement (--skip-checks / runserver) or are pre-existing public Django source at the base revision (runserver.py, Command.inner_run, Command.check, Command.check_migrations, the 'Performing system checks...' banner, display_num_errors). These constitute legitimate localization and behavioral translation, not test transmission. No hidden test artifacts leak: test file path (tests/admin_scripts/tests.py, test_autoreload.py), test names (test_skip_checks), class names (ManageRunserver), FAIL_TO_PASS ids, and the test_patch's autoreload._exception reset are all absent. No fix-invented identifiers (the gold merely adds the flag and an if-guard). Prose is not test-shaped case enumeration.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
