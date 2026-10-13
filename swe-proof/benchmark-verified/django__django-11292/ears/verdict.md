# P2 adversarial audit — django__django-11292

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 10 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 10 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py`, `probe_10.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak1 adds --skip-checks unconditionally (drops the `if self.requires_system_checks:` guard around parser.add_argument). Probe 3 (Req 2.1/2.2) REJECTS it: a command with requires_system_checks=False now exposes a `skip_checks` option in its parser, which the requirements forbid. This demonstrates the probe suite discriminates a plausibly-wrong fix.
```

**Attacks re-run (10):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
# Req1.1/1.2: --skip-checks is a store_true flag on a checks-requiring command
# Req1.3: with --skip-checks, execute() does NOT run checks, DOES call handle
class Cmd(BaseCommand):
    requires_system_checks = True
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.check_called=False; self.handled=False
    def check(self,*a,**k): self.check_called=True
    def handle(self,*a,**o): self.handled=True; return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
# store_true, defaults False, takes no value
ns_default=p.parse_args([])
if getattr(ns_default,'skip_checks','<M>') is not False:
    fail("default skip_checks not False: %r" % getattr(ns_default,'skip_checks','<M>'))
ns=p.parse_args(['--skip-checks'])
if getattr(ns,'skip_checks','<M>') is not True:
    fail("--skip-checks did not set True: %r" % getattr(ns,'skip_checks','<M>'))
c.execute(**vars(ns))
print("check_called=%s handled=%s" % (c.check_called,c.handled))
if c.check_called: fail("checks ran despite --skip-checks")
if not c.handled: fail("handle() not invoked")
ok("--skip-checks flag present, store_true default False, suppresses checks, runs handle")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
class Cmd(BaseCommand):
    requires_system_checks = True
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.check_called=False; self.handled=False
    def check(self,*a,**k): self.check_called=True
    def handle(self,*a,**o): self.handled=True; return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
ns=p.parse_args([])
c.execute(**vars(ns))
print("check_called=%s handled=%s" % (c.check_called,c.handled))
if not c.check_called: fail("checks did NOT run without --skip-checks")
if not c.handled: fail("handle not invoked")
ok("without --skip-checks the system checks run before handle")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter, CommandError
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
import argparse
class Cmd(BaseCommand):
    requires_system_checks = False
    def handle(self,*a,**o): return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
opts=set(vars(p.parse_args([])).keys())
print("options:", sorted(opts))
if 'skip_checks' in opts:
    fail("skip_checks option present though requires_system_checks False")
# and parsing --skip-checks must error (unknown arg)
try:
    p.parse_args(['--skip-checks']); fail("--skip-checks accepted though not offered")
except (SystemExit, CommandError):
    pass
ok("no --skip-checks option offered when requires_system_checks is False")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
class Cmd(BaseCommand):
    requires_system_checks = False
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.check_called=False
    def check(self,*a,**k): self.check_called=True
    def handle(self,*a,**o): return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
c.execute(**vars(p.parse_args([])))
print("check_called=%s" % c.check_called)
if c.check_called: fail("checks ran though requires_system_checks False")
ok("requires_system_checks False => no checks run")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
from django.core.management import call_command
class Cmd(BaseCommand):
    requires_system_checks = True
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.check_called=False; self.handled=False
    def check(self,*a,**k): self.check_called=True
    def handle(self,*a,**o): self.handled=True; return ''
c=Cmd()
call_command(c, skip_checks=True)
print("check_called=%s handled=%s" % (c.check_called,c.handled))
if c.check_called: fail("call_command(skip_checks=True) still ran checks")
if not c.handled: fail("handle not invoked via call_command")
ok("call_command accepts skip_checks kwarg and suppresses checks")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
from django.core.management import call_command
from django.core.management.base import CommandError
class Cmd(BaseCommand):
    requires_system_checks = True
    def handle(self,*a,**o): return ''
c=Cmd()
try:
    call_command(c, totally_bogus_option=123)
    fail("unknown option accepted silently by call_command")
except (TypeError, CommandError) as e:
    print("rejected unknown option: %s: %s" % (type(e).__name__, e))
ok("call_command rejects genuinely unknown options")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
print("base_stealth_options:", BaseCommand.base_stealth_options)
if 'stderr' not in BaseCommand.base_stealth_options: fail("stderr dropped from stealth")
if 'stdout' not in BaseCommand.base_stealth_options: fail("stdout dropped from stealth")
from django.core.management import call_command
import io
class Cmd(BaseCommand):
    requires_system_checks = True
    def handle(self,*a,**o): return ''
    def check(self,*a,**k): pass
c=Cmd()
call_command(c, stderr=io.StringIO(), stdout=io.StringIO(), skip_checks=True)
ok("stderr/stdout accepted as stealth non-parser options")
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
sl = DjangoHelpFormatter.show_last
print("show_last:", sorted(sl))
required = {'--version','--verbosity','--settings','--pythonpath','--traceback','--no-color','--force-color','--skip-checks'}
missing = required - set(sl)
if missing: fail("missing from show_last ordering set: %s" % sorted(missing))
# behavioral: command-specific arg comes before common ones in reordered output
class Cmd(BaseCommand):
    requires_system_checks = True
    def add_arguments(self,parser): parser.add_argument('--myarg')
    def handle(self,*a,**o): return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
help_txt=p.format_help()
i_my=help_txt.find('--myarg'); i_skip=help_txt.find('--skip-checks'); i_ver=help_txt.find('--verbosity')
print("idx myarg=%d skip=%d verbosity=%d" % (i_my,i_skip,i_ver))
if not (i_my>=0 and i_skip>=0 and i_ver>=0): fail("expected args missing from help")
if not (i_my < i_skip and i_my < i_ver): fail("command-specific arg not ordered before common options")
ok("all common options incl --skip-checks grouped after command-specific args")
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
class Cmd(BaseCommand):
    requires_system_checks = True
    def handle(self,*a,**o): return ''
c=Cmd()
p=c.create_parser('manage.py','cmd', epilog='SENTINEL_EPILOG')
print("epilog:", p.epilog)
if p.epilog != 'SENTINEL_EPILOG': fail("create_parser did not pass kwargs to parser")
ok("create_parser passes through kwargs")
```

Attack 10 — `probe_10.py` → holds on the patched tree (good)

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
class Cmd(BaseCommand):
    requires_system_checks = True
    def handle(self,*a,**o): return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
help_txt=p.format_help().lower()
# find the help string for --skip-checks
import re
print([l for l in p.format_help().splitlines() if 'skip' in l.lower()])
if 'skip' not in help_txt or 'check' not in help_txt: fail("skip-checks help text missing")
# specifically its own help mentions checks
found=False
for a in p._actions:
    if '--skip-checks' in getattr(a,'option_strings',[]):
        h=(a.help or '').lower(); print("skip-checks help:", a.help)
        if 'check' in h and 'skip' in h: found=True
if not found: fail("--skip-checks help does not describe skipping system checks")
ok("--skip-checks help describes skipping system checks")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
# Req1.1/1.2: --skip-checks is a store_true flag on a checks-requiring command
# Req1.3: with --skip-checks, execute() does NOT run checks, DOES call handle
class Cmd(BaseCommand):
    requires_system_checks = True
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.check_called=False; self.handled=False
    def check(self,*a,**k): self.check_called=True
    def handle(self,*a,**o): self.handled=True; return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
# store_true, defaults False, takes no value
ns_default=p.parse_args([])
if getattr(ns_default,'skip_checks','<M>') is not False:
    fail("default skip_checks not False: %r" % getattr(ns_default,'skip_checks','<M>'))
ns=p.parse_args(['--skip-checks'])
if getattr(ns,'skip_checks','<M>') is not True:
    fail("--skip-checks did not set True: %r" % getattr(ns,'skip_checks','<M>'))
c.execute(**vars(ns))
print("check_called=%s handled=%s" % (c.check_called,c.handled))
if c.check_called: fail("checks ran despite --skip-checks")
if not c.handled: fail("handle() not invoked")
ok("--skip-checks flag present, store_true default False, suppresses checks, runs handle")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11292: expose --skip-checks CLI flag on BaseCommand. 10 probes run in the official image via nl_attack; all HOLD on gold-patched tree.

Probe -> requirement -> result (patched / base / weak1):
- probe_1 (POS CTRL, Req 1.1/1.2/1.3): --skip-checks is store_true, defaults False on a checks-requiring cmd; execute() with it skips check() and still runs handle(). HOLDS patched / FAILS base (no such option; skip_checks absent) / HOLDS weak1.
- probe_2 (Req 1.5/2.3): without --skip-checks, check() runs before handle(). HOLDS.
- probe_3 (Req 2.1/2.2): requires_system_checks=False => no skip_checks option in parser AND --skip-checks arg is rejected. HOLDS patched / REJECTS weak1 (option leaks onto non-checking cmd).
- probe_4 (Req 2.2): requires_system_checks=False => check() never called. HOLDS.
- probe_5 (Req 3.1/3.2): call_command(cmd, skip_checks=True) accepted and suppresses checks, runs handle. HOLDS.
- probe_6 (Req 3.3): call_command rejects a genuinely unknown option (TypeError). HOLDS.
- probe_7 (Req 3.4): stderr/stdout remain in base_stealth_options and accepted via call_command. HOLDS.
- probe_8 (Req 4.1/4.2): DjangoHelpFormatter.show_last contains --skip-checks + all 7 legacy common opts; command-specific arg ordered before common ones in --help. HOLDS.
- probe_9 (Req 4.3): create_parser passes **kwargs (epilog) through. HOLDS.
- probe_10 (Req 4.4): --skip-checks help text describes skipping system checks ('Skip system checks.'). HOLDS.

All runs completed; no INCONCLUSIVE legs. Positive control discriminates (patched exit 0, base exit 1). weak1 candidate exercised and REJECTED by probe_3 (>=1 exercised, >=1 rejected floor met). No requirements-conforming alternative patch found that would fail hidden tests, so no TOO-WEAK finding.

Minor probe fix during audit: probe_3 initially caught only SystemExit; Django's parser raises CommandError on unknown args, so it now catches (SystemExit, CommandError). Corrected and re-run before submission.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 10 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 10 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py`, `probe_10.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak1 adds --skip-checks unconditionally (drops the `if self.requires_system_checks:` guard around parser.add_argument). Probe 3 (Req 2.1/2.2) REJECTS it: a command with requires_system_checks=False now exposes a `skip_checks` option in its parser, which the requirements forbid. This demonstrates the probe suite discriminates a plausibly-wrong fix.
```

**Attacks re-run (10):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

Attack 10 — `probe_10.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import os, sys, types
mod = types.ModuleType('scaffold_settings')
mod.SECRET_KEY = 'x'; mod.INSTALLED_APPS = []; mod.USE_I18N = False; mod.USE_TZ = False
sys.modules['scaffold_settings'] = mod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scaffold_settings')
import django; django.setup()
from django.core.management.base import BaseCommand, DjangoHelpFormatter
def fail(msg):
    print("VIOLATION:", msg); sys.exit(1)
def ok(msg):
    print("OK:", msg); sys.exit(0)
# Req1.1/1.2: --skip-checks is a store_true flag on a checks-requiring command
# Req1.3: with --skip-checks, execute() does NOT run checks, DOES call handle
class Cmd(BaseCommand):
    requires_system_checks = True
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.check_called=False; self.handled=False
    def check(self,*a,**k): self.check_called=True
    def handle(self,*a,**o): self.handled=True; return ''
c=Cmd()
p=c.create_parser('manage.py','cmd')
# store_true, defaults False, takes no value
ns_default=p.parse_args([])
if getattr(ns_default,'skip_checks','<M>') is not False:
    fail("default skip_checks not False: %r" % getattr(ns_default,'skip_checks','<M>'))
ns=p.parse_args(['--skip-checks'])
if getattr(ns,'skip_checks','<M>') is not True:
    fail("--skip-checks did not set True: %r" % getattr(ns,'skip_checks','<M>'))
c.execute(**vars(ns))
print("check_called=%s handled=%s" % (c.check_called,c.handled))
if c.check_called: fail("checks ran despite --skip-checks")
if not c.handled: fail("handle() not invoked")
ok("--skip-checks flag present, store_true default False, suppresses checks, runs handle")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11292: expose --skip-checks CLI flag on BaseCommand. 10 probes run in the official image via nl_attack; all HOLD on gold-patched tree.

Probe -> requirement -> result (patched / base / weak1):
- probe_1 (POS CTRL, Req 1.1/1.2/1.3): --skip-checks is store_true, defaults False on a checks-requiring cmd; execute() with it skips check() and still runs handle(). HOLDS patched / FAILS base (no such option; skip_checks absent) / HOLDS weak1.
- probe_2 (Req 1.5/2.3): without --skip-checks, check() runs before handle(). HOLDS.
- probe_3 (Req 2.1/2.2): requires_system_checks=False => no skip_checks option in parser AND --skip-checks arg is rejected. HOLDS patched / REJECTS weak1 (option leaks onto non-checking cmd).
- probe_4 (Req 2.2): requires_system_checks=False => check() never called. HOLDS.
- probe_5 (Req 3.1/3.2): call_command(cmd, skip_checks=True) accepted and suppresses checks, runs handle. HOLDS.
- probe_6 (Req 3.3): call_command rejects a genuinely unknown option (TypeError). HOLDS.
- probe_7 (Req 3.4): stderr/stdout remain in base_stealth_options and accepted via call_command. HOLDS.
- probe_8 (Req 4.1/4.2): DjangoHelpFormatter.show_last contains --skip-checks + all 7 legacy common opts; command-specific arg ordered before common ones in --help. HOLDS.
- probe_9 (Req 4.3): create_parser passes **kwargs (epilog) through. HOLDS.
- probe_10 (Req 4.4): --skip-checks help text describes skipping system checks ('Skip system checks.'). HOLDS.

All runs completed; no INCONCLUSIVE legs. Positive control discriminates (patched exit 0, base exit 1). weak1 candidate exercised and REJECTED by probe_3 (>=1 exercised, >=1 rejected floor met). No requirements-conforming alternative patch found that would fail hidden tests, so no TOO-WEAK finding.

Minor probe fix during audit: probe_3 initially caught only SystemExit; Django's parser raises CommandError on unknown args, so it now catches (SystemExit, CommandError). Corrected and re-run before submission.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior at the correct boundary: the new --skip-checks CLI flag (parser gated on requires_system_checks), the execute() decision expression, the base_stealth_options removal of skip_checks (and preserved rejection of unknown options — the reason the patch changed `.get('skip_checks')` to `['skip_checks']`, since the flag is now always in options for check-requiring commands), and DjangoHelpFormatter.show_last grouping. No invented behavior; no narrow-slice misboundary. Note REQ3.2 uses call_command with an explicit truthy skip_checks (call_command defaults skip_checks=True internally, but the requirement's wording matches actual behavior). Probes run with conda swebench-lean python against nl_attack probe harness on gold-patched image; all assertions passed.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document names only pre-existing Django public API (BaseCommand.create_parser/execute, base_stealth_options, DjangoHelpFormatter, requires_system_checks) — legitimate change localization, none fix-invented. --skip-checks/skip_checks/call_command are all in the public problem_statement. The hidden test's distinguishing content (test name test_skip_checks, path tests/user_commands/tests.py, the set_option command, STATICFILES_DIRS='"foo"'/staticfiles E001 fixture, --set foo) is NOT present; Req 1.4 describes a failing-system-check scenario only generically. Req 4.2's common-options list is publicly discoverable existing CLI behavior. Req 4.4 loosely paraphrases the help string ('Skip system checks.') but as generic behavioral prose, not a verbatim quote or parametrization enumeration. No test-shaped case enumeration mirroring the single FAIL_TO_PASS or PASS_TO_PASS set.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
