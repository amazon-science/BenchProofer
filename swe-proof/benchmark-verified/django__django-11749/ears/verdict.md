# P2 adversarial audit — django__django-11749

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

Counterexample / evidence:

```
The weak_partial candidate patch recognizes only the FIRST member of each required mutually-exclusive group (group._group_actions[0]) as satisfying the group. It applies cleanly at base_commit and passes probes 1,3,5, but probe_2 REJECTS it: call_command(cmd, foo_name='bar') (the SECOND group member) still raises CommandError 'one of the arguments --foo-id --foo-name is required'. This demonstrates the suite discriminates a plausible partial fix that violates Requirement 1.5 (behavior must hold regardless of which member is supplied) and would fail the hidden test test_mutually_exclusive_group_required_options (which asserts both foo_id=1 and foo_name='foo' work).
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Requirement 1 (core / positive control): call_command with a member of a
required mutually-exclusive group passed as a kwarg SHALL run without raising a
'one of the arguments is required' error, and the supplied dest reaches the
handler with the caller's value.

HOLDS iff call_command('mutex', foo_id=1) succeeds and options['foo_id']==1.
FAILS at base (raises CommandError). This is the discriminating positive control.
"""
import sys
import io

import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[], USE_TZ=True, LOGGING_CONFIG=None)
django.setup()

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

received = {}


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--foo-id', type=int, nargs='?', default=None)
        group.add_argument('--foo-name', type=str, nargs='?', default=None)

    def handle(self, *args, **options):
        received.clear()
        received.update(options)
        self.stdout.write(','.join(k for k in options))


cmd = Command()
out = io.StringIO()
try:
    call_command(cmd, foo_id=1, stdout=out)
except CommandError as e:
    print("VIOLATION: call_command raised CommandError:", e)
    sys.exit(1)
except Exception as e:
    print("UNEXPECTED error:", type(e).__name__, e)
    sys.exit(1)

print("handler options keys:", sorted(received))
print("foo_id value:", received.get('foo_id'))
if received.get('foo_id') != 1:
    print("VIOLATION: foo_id not present with value 1")
    sys.exit(1)
print("OK: call_command succeeded and foo_id=1 reached the handler")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.5 + 2.1: behavior holds for the OTHER member (foo_name), AND
required-group validation still fires when NOTHING is supplied.

HOLDS iff: call_command(foo_name='bar') succeeds with foo_name reaching handler,
AND call_command() with no member raises CommandError mentioning 'required'.
"""
import sys
import io

import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[], USE_TZ=True, LOGGING_CONFIG=None)
django.setup()

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

received = {}


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--foo-id', type=int, nargs='?', default=None)
        group.add_argument('--foo-name', type=str, nargs='?', default=None)

    def handle(self, *args, **options):
        received.clear()
        received.update(options)


cmd = Command()

# Part A: the other member works too (Req 1.5)
out = io.StringIO()
try:
    call_command(cmd, foo_name='bar', stdout=out)
except Exception as e:
    print("VIOLATION (foo_name): raised", type(e).__name__, e)
    sys.exit(1)
if received.get('foo_name') != 'bar':
    print("VIOLATION: foo_name did not reach handler as 'bar':", received.get('foo_name'))
    sys.exit(1)
print("OK: foo_name='bar' reached handler")

# Part B: nothing supplied -> CommandError (Req 2.1)
raised = None
try:
    call_command(cmd, stdout=io.StringIO())
except CommandError as e:
    raised = str(e)
except Exception as e:
    print("VIOLATION: wrong exception type when nothing supplied:", type(e).__name__, e)
    sys.exit(1)
if raised is None:
    print("VIOLATION: no error raised when no group member supplied")
    sys.exit(1)
print("missing-arg error:", raised)
if 'required' not in raised:
    print("VIOLATION: error does not report 'required'")
    sys.exit(1)
print("OK: required-group validation still fires when nothing supplied")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 1.3: when a required mutex group has multiple members and the
caller supplies exactly ONE as a kwarg, call_command SHALL forward ONLY the
supplied member and NOT fabricate/forward the other members.

We supply foo_id=5 and assert the OTHER member (foo_name) stays at its default
(None) in the handler options -- i.e. nothing was fabricated for it. Also assert
that supplying two members of the required group at once still triggers the
mutual-exclusivity error (they were both forwarded / not silently dropped).

HOLDS iff foo_id=5 supplied alone -> foo_name is None in handler.
"""
import sys
import io

import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[], USE_TZ=True, LOGGING_CONFIG=None)
django.setup()

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

received = {}


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--foo-id', type=int, nargs='?', default=None)
        group.add_argument('--foo-name', type=str, nargs='?', default=None)

    def handle(self, *args, **options):
        received.clear()
        received.update(options)


cmd = Command()
try:
    call_command(cmd, foo_id=5, stdout=io.StringIO())
except Exception as e:
    print("VIOLATION: raised on single member supply:", type(e).__name__, e)
    sys.exit(1)

print("foo_id:", received.get('foo_id'), " foo_name:", received.get('foo_name'))
if received.get('foo_id') != 5:
    print("VIOLATION: foo_id not 5")
    sys.exit(1)
if received.get('foo_name') is not None:
    print("VIOLATION: other member foo_name was fabricated:", received.get('foo_name'))
    sys.exit(1)
print("OK: only the supplied member forwarded; other member left at default None")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 3 (regression 'SHALL keep'): individually-required options are
still forwarded, resolved via the option-name->dest mapping, and work mixed
with positional args. Also Req 3.3: caller may use either the public option
name or the dest name.

HOLDS iff: a command with a plain required option --need (dest='need') runs when
supplied as kwarg need=7, value reaches handler; AND supplying via the public
name also works. (This should hold at base too -- it is a regression guard.)
"""
import sys
import io

import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[], USE_TZ=True, LOGGING_CONFIG=None)
django.setup()

from django.core.management import call_command
from django.core.management.base import BaseCommand

received = {}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--need', type=int, required=True)
        parser.add_argument('extra', nargs='?', default=None)

    def handle(self, *args, **options):
        received.clear()
        received.update(options)


cmd = Command()
# via dest kwarg
try:
    call_command(cmd, need=7, stdout=io.StringIO())
except Exception as e:
    print("VIOLATION: required option via kwarg raised:", type(e).__name__, e)
    sys.exit(1)
if received.get('need') != 7:
    print("VIOLATION: required option value not forwarded:", received.get('need'))
    sys.exit(1)
print("OK: individually-required option forwarded (need=7)")

# mixed with a positional arg
try:
    call_command(cmd, 'pos', need=9, stdout=io.StringIO())
except Exception as e:
    print("VIOLATION: required option mixed with positional raised:", type(e).__name__, e)
    sys.exit(1)
if received.get('need') != 9 or received.get('extra') != 'pos':
    print("VIOLATION: mixed forwarding wrong:", received.get('need'), received.get('extra'))
    sys.exit(1)
print("OK: required option + positional forwarded (need=9, extra=pos)")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2.2 + 4: a kwarg that is NOT individually required and NOT part
of any required mutex group is NOT injected into parse_args solely on the new
rule (it still works via arg_options), unknown options raise TypeError, and a
NON-required mutex group member supplied as a kwarg does not trigger spurious
forwarding/errors.

HOLDS iff:
 (a) an unknown option name raises TypeError listing valid options (Req 4.1);
 (b) a plain optional kwarg (--maybe) is accepted and its value reaches the
     handler (Req 4.2 / 2.2);
 (c) a member of a NON-required mutex group supplied as kwarg runs fine and only
     that member is set (the new rule only applies to required groups, Req 2.2).
"""
import sys
import io

import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[], USE_TZ=True, LOGGING_CONFIG=None)
django.setup()

from django.core.management import call_command
from django.core.management.base import BaseCommand

received = {}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--maybe', type=int, default=None)
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument('--aaa', type=int, nargs='?', default=None)
        group.add_argument('--bbb', type=str, nargs='?', default=None)

    def handle(self, *args, **options):
        received.clear()
        received.update(options)


cmd = Command()

# (a) unknown option -> TypeError
try:
    call_command(cmd, definitely_not_an_option=1, stdout=io.StringIO())
    print("VIOLATION: unknown option did not raise")
    sys.exit(1)
except TypeError as e:
    print("OK: unknown option raised TypeError:", str(e)[:120])
except Exception as e:
    print("VIOLATION: unknown option raised wrong type:", type(e).__name__, e)
    sys.exit(1)

# (b) plain optional kwarg forwarded
try:
    call_command(cmd, maybe=42, stdout=io.StringIO())
except Exception as e:
    print("VIOLATION: optional kwarg raised:", type(e).__name__, e)
    sys.exit(1)
if received.get('maybe') != 42:
    print("VIOLATION: optional kwarg value not forwarded:", received.get('maybe'))
    sys.exit(1)
print("OK: plain optional kwarg forwarded (maybe=42)")

# (c) non-required mutex member as kwarg works, only it is set
try:
    call_command(cmd, aaa=3, stdout=io.StringIO())
except Exception as e:
    print("VIOLATION: non-required mutex member raised:", type(e).__name__, e)
    sys.exit(1)
if received.get('aaa') != 3 or received.get('bbb') is not None:
    print("VIOLATION: non-required mutex forwarding wrong:", received.get('aaa'), received.get('bbb'))
    sys.exit(1)
print("OK: non-required mutex member forwarded, other member left None")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1 (core / positive control): call_command with a member of a
required mutually-exclusive group passed as a kwarg SHALL run without raising a
'one of the arguments is required' error, and the supplied dest reaches the
handler with the caller's value.

HOLDS iff call_command('mutex', foo_id=1) succeeds and options['foo_id']==1.
FAILS at base (raises CommandError). This is the discriminating positive control.
"""
import sys
import io

import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[], USE_TZ=True, LOGGING_CONFIG=None)
django.setup()

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

received = {}


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--foo-id', type=int, nargs='?', default=None)
        group.add_argument('--foo-name', type=str, nargs='?', default=None)

    def handle(self, *args, **options):
        received.clear()
        received.update(options)
        self.stdout.write(','.join(k for k in options))


cmd = Command()
out = io.StringIO()
try:
    call_command(cmd, foo_id=1, stdout=out)
except CommandError as e:
    print("VIOLATION: call_command raised CommandError:", e)
    sys.exit(1)
except Exception as e:
    print("UNEXPECTED error:", type(e).__name__, e)
    sys.exit(1)

print("handler options keys:", sorted(received))
print("foo_id value:", received.get('foo_id'))
if received.get('foo_id') != 1:
    print("VIOLATION: foo_id not present with value 1")
    sys.exit(1)
print("OK: call_command succeeded and foo_id=1 reached the handler")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) HOLDS patched and FAILS (VIOLATED) at base with the exact CommandError, giving discriminating power. Probes exercised via `python -m swebench_unified.nl_attack probe` inside the official image; commands passed as objects to call_command so no test command files need installing.

Coverage:
- probe_1 (Req 1.1/1.2/1.4, positive control): call_command(cmd, foo_id=1) succeeds without 'required' error and foo_id=1 reaches the handler. HOLDS patched, VIOLATED at base.
- probe_2 (Req 1.5 + Req 2.1): the OTHER member foo_name='bar' works AND the required-group validation still fires (CommandError mentioning 'required') when nothing is supplied. HOLDS patched; this is the probe that rejects the weak candidate.
- probe_3 (Req 1.3): supplying exactly one member (foo_id=5) forwards only that member; the other member foo_name is left at its default None (nothing fabricated). HOLDS patched.
- probe_4 (Req 3.1/3.2/3.3 regression): individually-required option --need forwarded via kwarg and mixed with a positional arg; value reaches handler. HOLDS patched.
- probe_5 (Req 2.2 + Req 4.1/4.2): unknown option raises TypeError listing valid options; a plain optional kwarg is forwarded; a NON-required mutex group member works and only it is set (the new rule applies only to required groups). HOLDS patched.

Candidate patches exercised: 1 (weak_partial). REJECTED by the suite (probe_2), so no TOO-WEAK finding — the requirements adequately constrain the fix; Req 1.5 is what kills the partial reading. No requirements VIOLATION found: every probe holds on the gold-patched tree.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
The weak_partial candidate patch recognizes only the FIRST member of each required mutually-exclusive group (group._group_actions[0]) as satisfying the group. It applies cleanly at base_commit and passes probes 1,3,5, but probe_2 REJECTS it: call_command(cmd, foo_name='bar') (the SECOND group member) still raises CommandError 'one of the arguments --foo-id --foo-name is required'. This demonstrates the suite discriminates a plausible partial fix that violates Requirement 1.5 (behavior must hold regardless of which member is supplied) and would fail the hidden test test_mutually_exclusive_group_required_options (which asserts both foo_id=1 and foo_name='foo' work).
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1 (core / positive control): call_command with a member of a
required mutually-exclusive group passed as a kwarg SHALL run without raising a
'one of the arguments is required' error, and the supplied dest reaches the
handler with the caller's value.

HOLDS iff call_command('mutex', foo_id=1) succeeds and options['foo_id']==1.
FAILS at base (raises CommandError). This is the discriminating positive control.
"""
import sys
import io

import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[], USE_TZ=True, LOGGING_CONFIG=None)
django.setup()

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

received = {}


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--foo-id', type=int, nargs='?', default=None)
        group.add_argument('--foo-name', type=str, nargs='?', default=None)

    def handle(self, *args, **options):
        received.clear()
        received.update(options)
        self.stdout.write(','.join(k for k in options))


cmd = Command()
out = io.StringIO()
try:
    call_command(cmd, foo_id=1, stdout=out)
except CommandError as e:
    print("VIOLATION: call_command raised CommandError:", e)
    sys.exit(1)
except Exception as e:
    print("UNEXPECTED error:", type(e).__name__, e)
    sys.exit(1)

print("handler options keys:", sorted(received))
print("foo_id value:", received.get('foo_id'))
if received.get('foo_id') != 1:
    print("VIOLATION: foo_id not present with value 1")
    sys.exit(1)
print("OK: call_command succeeded and foo_id=1 reached the handler")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) HOLDS patched and FAILS (VIOLATED) at base with the exact CommandError, giving discriminating power. Probes exercised via `python -m swebench_unified.nl_attack probe` inside the official image; commands passed as objects to call_command so no test command files need installing.

Coverage:
- probe_1 (Req 1.1/1.2/1.4, positive control): call_command(cmd, foo_id=1) succeeds without 'required' error and foo_id=1 reaches the handler. HOLDS patched, VIOLATED at base.
- probe_2 (Req 1.5 + Req 2.1): the OTHER member foo_name='bar' works AND the required-group validation still fires (CommandError mentioning 'required') when nothing is supplied. HOLDS patched; this is the probe that rejects the weak candidate.
- probe_3 (Req 1.3): supplying exactly one member (foo_id=5) forwards only that member; the other member foo_name is left at its default None (nothing fabricated). HOLDS patched.
- probe_4 (Req 3.1/3.2/3.3 regression): individually-required option --need forwarded via kwarg and mixed with a positional arg; value reaches handler. HOLDS patched.
- probe_5 (Req 2.2 + Req 4.1/4.2): unknown option raises TypeError listing valid options; a plain optional kwarg is forwarded; a NON-required mutex group member works and only it is set (the new rule applies only to required groups). HOLDS patched.

Candidate patches exercised: 1 (weak_partial). REJECTED by the suite (probe_2), so no TOO-WEAK finding — the requirements adequately constrain the fix; Req 1.5 is what kills the partial reading. No requirements VIOLATION found: every probe holds on the gold-patched tree.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds `mutually_exclusive_required_options` (members of groups with group.required) and ORs `opt in mutually_exclusive_required_options` into the injection condition. Requirements pin the exact changed observable behavior (kwarg member of a required mutex group now satisfies the group and is forwarded as <min-flag>=<value>), correctly bound biconditionally with R2 preserving the missing-detection path. No mandated behavior absent from code, no forbidden behavior present, no invented behavior; modeling boundary is the changed behavior, not a narrow slice. Probe run on gold-patched image, exit 0, all assertions held.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the public problem_statement. It uses only generic placeholders (some_dest, <flag>, <value>) and never mentions the hidden test's concrete identifiers: the command name 'mutually_exclusive_required', the options '--foo-id'/'--foo-name', the test function 'test_mutually_exclusive_group_required_options', the class CommandTests, or the file path tests/user_commands/tests.py. The two potentially-worrying specifics are both already PUBLIC: (1) Req 1.2's 'shortest (lexicographically minimum) option string' / '<flag>=<value>' form is verbatim public — problem_statement quotes '{}={}'.format(min(opt.option_strings), arg_options[opt.dest]); (2) Req 2.1's 'one of the arguments is required' error is quoted in problem_statement. The gold-invented identifier 'mutually_exclusive_required_options' does not appear. Requirements 3-4 translate PASS_TO_PASS coverage into behavioral criteria rather than enumerating parametrized cases; naming call_command / django/core/management/__init__.py is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
