# P2 adversarial audit — django__django-16454

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# POSITIVE CONTROL. Requirement 1 criteria 2+3:
# A sub-parser built from a CommandParser with called_from_command_line=True
# must report an argument error via argparse's error path (SystemExit),
# NOT raise CommandError. At base the flag is lost (None) -> CommandError.
import django
from django.core.management.base import CommandParser, CommandError

parser = CommandParser(called_from_command_line=True, prog="manage.py cheeses")
sub = parser.add_subparsers()
create = sub.add_parser("create")
create.add_argument("name")  # required positional

raised = None
try:
    # missing required 'name' inside the sub-command
    parser.parse_args(["create"])
except SystemExit as e:
    raised = ("SystemExit", e.code)
except CommandError as e:
    raised = ("CommandError", str(e))
except BaseException as e:
    raised = (type(e).__name__, str(e))

print("observed:", raised)
if raised is not None and raised[0] == "SystemExit":
    print("PASS: sub-parser argument error surfaced via argparse error (SystemExit)")
    raise SystemExit(0)
print("FAIL: expected SystemExit, got", raised)
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 1 criterion 2: the constructed sub-parser must carry
# called_from_command_line equal to the parent's value.
from django.core.management.base import CommandParser

for flag in (True, False):
    parent = CommandParser(called_from_command_line=flag)
    sub = parent.add_subparsers()
    child = sub.add_parser("x")
    print(f"parent flag={flag!r} -> child.called_from_command_line={getattr(child,'called_from_command_line','MISSING')!r}, type={type(child).__name__}")
    assert isinstance(child, CommandParser), "child must be a CommandParser"
    assert child.called_from_command_line == flag, f"expected {flag!r}, got {child.called_from_command_line!r}"
print("PASS: sub-parser called_from_command_line propagated for True and False")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 1 criterion 4: sub-parser from a CommandParser whose flag is
# falsy/unset must raise CommandError (not SystemExit) on an argument error.
from django.core.management.base import CommandParser, CommandError

# unset (defaults to None) -> falsy
parser = CommandParser(prog="manage.py cheeses")
sub = parser.add_subparsers()
create = sub.add_parser("create")
create.add_argument("name")

raised = None
try:
    parser.parse_args(["create"])
except CommandError as e:
    raised = ("CommandError", str(e))
except SystemExit as e:
    raised = ("SystemExit", e.code)
except BaseException as e:
    raised = (type(e).__name__, str(e))

print("observed:", raised)
if raised is not None and raised[0] == "CommandError":
    print("PASS: falsy flag sub-parser raised CommandError")
    raise SystemExit(0)
print("FAIL: expected CommandError, got", raised)
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 2 criteria 1+2: a foreign parser_class (NOT a CommandParser
# subclass) must be used to build sub-parsers WITHOUT injecting
# called_from_command_line, and other kwargs forwarded. The vanilla parser
# must handle its own errors via argparse (SystemExit), not get a surprise
# called_from_command_line kwarg (which would raise TypeError).
import argparse
from django.core.management.base import CommandParser

parent = CommandParser(called_from_command_line=True)
# explicit foreign parser_class
sub = parent.add_subparsers(parser_class=argparse.ArgumentParser)
child = sub.add_parser("foo")
child.add_argument("bar", type=int)
print("child type:", type(child).__name__)
assert type(child) is argparse.ArgumentParser, "foreign class must be used verbatim"
assert not hasattr(child, "called_from_command_line"), "must NOT inject called_from_command_line"

# invalid int -> vanilla argparse errors via SystemExit
raised = None
try:
    parent.parse_args(["foo", "seven"])
except SystemExit as e:
    raised = ("SystemExit", e.code)
except BaseException as e:
    raised = (type(e).__name__, str(e))
print("observed:", raised)
assert raised is not None and raised[0] == "SystemExit", f"expected SystemExit, got {raised}"
print("PASS: foreign parser_class untouched and errors normally")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 3 criteria 1+2: normal sub-command dispatch and parsing still
# works — required positional supplied parses successfully and exposes values.
# Also criterion 5 (top-level behavior preserved) via missing_args_message.
from django.core.management.base import CommandParser, CommandError

parser = CommandParser(called_from_command_line=True)
sub = parser.add_subparsers(dest="subcommand", required=True)
create = sub.add_parser("create")
create.add_argument("name")

ns = parser.parse_args(["create", "wensleydale"])
print("parsed:", vars(ns))
assert ns.subcommand == "create"
assert ns.name == "wensleydale"

# top-level required subparser missing -> error path honored (flag True -> SystemExit)
raised = None
try:
    parser.parse_args([])
except SystemExit as e:
    raised = "SystemExit"
except CommandError as e:
    raised = "CommandError"
print("missing top-level subcommand raised:", raised)
assert raised == "SystemExit", raised
print("PASS: normal dispatch works and top-level required-subparser error honored")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 3 criterion 3 (programmatic invalid option) + Req1 crit5:
# with falsy flag, an unrecognized option to the sub-command must go through
# CommandParser's normal error path -> CommandError (not a raw argparse crash).
from django.core.management.base import CommandParser, CommandError

parser = CommandParser(called_from_command_line=False)
sub = parser.add_subparsers()
create = sub.add_parser("create")
create.add_argument("name")

raised = None
try:
    parser.parse_args(["create", "n", "--nope"])
except CommandError as e:
    raised = ("CommandError", str(e))
except SystemExit as e:
    raised = ("SystemExit", e.code)
except BaseException as e:
    raised = (type(e).__name__, str(e))
print("observed:", raised)
assert raised is not None and raised[0] == "CommandError", f"expected CommandError, got {raised}"
print("PASS: invalid option in sub-command raised CommandError via normal path")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# POSITIVE CONTROL. Requirement 1 criteria 2+3:
# A sub-parser built from a CommandParser with called_from_command_line=True
# must report an argument error via argparse's error path (SystemExit),
# NOT raise CommandError. At base the flag is lost (None) -> CommandError.
import django
from django.core.management.base import CommandParser, CommandError

parser = CommandParser(called_from_command_line=True, prog="manage.py cheeses")
sub = parser.add_subparsers()
create = sub.add_parser("create")
create.add_argument("name")  # required positional

raised = None
try:
    # missing required 'name' inside the sub-command
    parser.parse_args(["create"])
except SystemExit as e:
    raised = ("SystemExit", e.code)
except CommandError as e:
    raised = ("CommandError", str(e))
except BaseException as e:
    raised = (type(e).__name__, str(e))

print("observed:", raised)
if raised is not None and raised[0] == "SystemExit":
    print("PASS: sub-parser argument error surfaced via argparse error (SystemExit)")
    raise SystemExit(0)
print("FAIL: expected SystemExit, got", raised)
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16454: CommandParser.add_subparsers() must propagate called_from_command_line to same-family sub-parsers so sub-command argument errors are formatted like top-level ones.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1 c2+c3, POSITIVE CONTROL): sub-parser from flag=True parser -> missing required arg raises SystemExit (argparse error path). PATCHED: HOLDS (SystemExit 2). BASE: VIOLATED (raises CommandError) => discriminates, prepatch reproduced.
- probe_2 (Req1 c2): child.called_from_command_line == parent's, for both True and False, child is CommandParser. HOLDS.
- probe_3 (Req1 c4): flag unset/falsy -> sub-parser argument error raises CommandError. HOLDS.
- probe_4 (Req2 c1+c2): explicit foreign parser_class (argparse.ArgumentParser) used verbatim, NO called_from_command_line injected, errors via SystemExit. HOLDS.
- probe_5 (Req3 c1+c2, Req1 c5): normal dispatch parses required positional, top-level required-subparser error honored (SystemExit under flag=True). HOLDS.
- probe_6 (Req3 c3, Req1 c5): invalid option under flag=False -> CommandError via normal path. HOLDS.

Candidate wrong-fix patches (REQUIRED floor met: 2 exercised, 2 REJECTED):
- weak_A (drops the issubclass(CommandParser) guard from Req2 c1 — always wraps parser_class in partial(called_from_command_line=...)): REJECTED by probe_4 — injecting called_from_command_line into argparse.ArgumentParser raises TypeError, violating Req2. Passes probes 1,2,3,5,6.
- weak_B (hardcodes called_from_command_line=True instead of self.called_from_command_line): REJECTED by probe_2 (flag=False parent yields child flag=True) and probe_3 (falsy parent no longer raises CommandError, gets SystemExit) — violates Req1 c2/c4. Passes probes 1,4,5,6.

Suite discriminates wrong implementations on both attack axes (missing foreign-class guard; wrong flag source). No requirements-conforming patch found that fails hidden tests. Positive control fails at base and holds patched. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# POSITIVE CONTROL. Requirement 1 criteria 2+3:
# A sub-parser built from a CommandParser with called_from_command_line=True
# must report an argument error via argparse's error path (SystemExit),
# NOT raise CommandError. At base the flag is lost (None) -> CommandError.
import django
from django.core.management.base import CommandParser, CommandError

parser = CommandParser(called_from_command_line=True, prog="manage.py cheeses")
sub = parser.add_subparsers()
create = sub.add_parser("create")
create.add_argument("name")  # required positional

raised = None
try:
    # missing required 'name' inside the sub-command
    parser.parse_args(["create"])
except SystemExit as e:
    raised = ("SystemExit", e.code)
except CommandError as e:
    raised = ("CommandError", str(e))
except BaseException as e:
    raised = (type(e).__name__, str(e))

print("observed:", raised)
if raised is not None and raised[0] == "SystemExit":
    print("PASS: sub-parser argument error surfaced via argparse error (SystemExit)")
    raise SystemExit(0)
print("FAIL: expected SystemExit, got", raised)
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16454: CommandParser.add_subparsers() must propagate called_from_command_line to same-family sub-parsers so sub-command argument errors are formatted like top-level ones.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1 c2+c3, POSITIVE CONTROL): sub-parser from flag=True parser -> missing required arg raises SystemExit (argparse error path). PATCHED: HOLDS (SystemExit 2). BASE: VIOLATED (raises CommandError) => discriminates, prepatch reproduced.
- probe_2 (Req1 c2): child.called_from_command_line == parent's, for both True and False, child is CommandParser. HOLDS.
- probe_3 (Req1 c4): flag unset/falsy -> sub-parser argument error raises CommandError. HOLDS.
- probe_4 (Req2 c1+c2): explicit foreign parser_class (argparse.ArgumentParser) used verbatim, NO called_from_command_line injected, errors via SystemExit. HOLDS.
- probe_5 (Req3 c1+c2, Req1 c5): normal dispatch parses required positional, top-level required-subparser error honored (SystemExit under flag=True). HOLDS.
- probe_6 (Req3 c3, Req1 c5): invalid option under flag=False -> CommandError via normal path. HOLDS.

Candidate wrong-fix patches (REQUIRED floor met: 2 exercised, 2 REJECTED):
- weak_A (drops the issubclass(CommandParser) guard from Req2 c1 — always wraps parser_class in partial(called_from_command_line=...)): REJECTED by probe_4 — injecting called_from_command_line into argparse.ArgumentParser raises TypeError, violating Req2. Passes probes 1,2,3,5,6.
- weak_B (hardcodes called_from_command_line=True instead of self.called_from_command_line): REJECTED by probe_2 (flag=False parent yields child flag=True) and probe_3 (falsy parent no longer raises CommandError, gets SystemExit) — violates Req1 c2/c4. Passes probes 1,4,5,6.

Suite discriminates wrong implementations on both attack axes (missing foreign-class guard; wrong flag source). No requirements-conforming patch found that fails hidden tests. Positive control fails at base and holds patched. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch overrides CommandParser.add_subparsers to wrap parser_class in functools.partial(parser_class, called_from_command_line=self.called_from_command_line) only when parser_class subclasses CommandParser (defaulting parser_class to type(self)). Requirement 1 (define add_subparsers), Req 2 (foreign class untouched, parser_class kwarg forwarded, default = own class), Req 3 (preserve existing behavior) all correspond to the code and the FAIL_TO_PASS test test_subparser_error_formatting. Modeling boundary is correct: requirements target the observable error-reporting behavior of constructed sub-parsers, matching the gold patch and issue. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the fix behaviorally using only pre-existing identifiers (CommandParser, add_subparsers, called_from_command_line, parser_class from base.py/argparse) — legitimate localization, no fix-invented names. The FAIL_TO_PASS exact error strings ('manage.py subparser foo: error: argument bar: invalid int value: twelve') are NOT quoted; requirements say only 'concise usage/error message on the error output stream.' Test file path (subparser_vanilla.py), test function names, and test-specific literals (type=int, 'twelve'/'seven') are all absent. Requirement 2 (foreign parser classes) exceeds the problem_statement but is derivable from the gold issubclass branch (describing the code's behavior, legitimate). Requirement 3.4's enumeration (mutually exclusive groups, required options, etc.) loosely echoes PASS_TO_PASS categories but reads as generic argparse no-regression scope, not a reconstruction of parametrized ids/cases. No quoted test/gold code, no paths/names/ids transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
