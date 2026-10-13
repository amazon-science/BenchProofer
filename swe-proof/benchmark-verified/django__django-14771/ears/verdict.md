# P2 adversarial audit — django__django-14771

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# R1.1 + R1.2 (POSITIVE CONTROL): flag-style -X option rendered as -Xutf8
import sys, os, tempfile, __main__
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'manage.py'); open(script,'w').write('#\n')
with mock.patch.object(sys, 'argv', [script, 'runserver']), \
     mock.patch.object(sys, 'warnoptions', []), \
     mock.patch.object(sys, '_xoptions', {'utf8': True}), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', None):
    args = autoreload.get_child_arguments()
print("args =", args)
ok = '-Xutf8' in args and not any(a.startswith('-Xutf8=') for a in args)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.3: value-style -X option rendered as -Xkey=value with single '='
import sys, os, tempfile, __main__
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'manage.py'); open(script,'w').write('#\n')
with mock.patch.object(sys, 'argv', [script, 'runserver']), \
     mock.patch.object(sys, 'warnoptions', []), \
     mock.patch.object(sys, '_xoptions', {'dev': 'a=b'}), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', None):
    args = autoreload.get_child_arguments()
print("args =", args)
ok = '-Xdev=a=b' in args
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.4 + R1.6 order: multiple -X in _xoptions order, after -W, before program args
import sys, os, tempfile, __main__, collections
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'manage.py'); open(script,'w').write('#\n')
xopts = collections.OrderedDict([('utf8', True), ('dev', True), ('foo', 'bar')])
with mock.patch.object(sys, 'argv', [script, 'runserver', '--noreload']), \
     mock.patch.object(sys, 'warnoptions', ['error']), \
     mock.patch.object(sys, '_xoptions', xopts), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', None):
    args = autoreload.get_child_arguments()
print("args =", args)
# expected: [exe, -Werror, -Xutf8, -Xdev, -Xfoo=bar, script, runserver, --noreload]
xs = [a for a in args if a.startswith('-X')]
w_i = args.index('-Werror')
first_x = min(args.index(x) for x in xs)
prog_i = args.index(script)
ok = (xs == ['-Xutf8', '-Xdev', '-Xfoo=bar']
      and w_i < first_x < prog_i
      and all(args.index(x) > w_i and args.index(x) < prog_i for x in xs))
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R1.5: no active -X options => no -X tokens added
import sys, os, tempfile, __main__
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'manage.py'); open(script,'w').write('#\n')
with mock.patch.object(sys, 'argv', [script, 'runserver']), \
     mock.patch.object(sys, 'warnoptions', []), \
     mock.patch.object(sys, '_xoptions', {}), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', None):
    args = autoreload.get_child_arguments()
print("args =", args)
ok = not any(a.startswith('-X') for a in args)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R2.1 + R2.2: non-CPython => no -X tokens, command line identical to no-forwarding
import sys, os, tempfile, __main__
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'manage.py'); open(script,'w').write('#\n')
with mock.patch.object(sys, 'argv', [script, 'runserver']), \
     mock.patch.object(sys, 'warnoptions', ['error']), \
     mock.patch.object(sys, '_xoptions', {'utf8': True, 'foo': 'bar'}), \
     mock.patch.object(sys.implementation, 'name', 'pypy'), \
     mock.patch.object(__main__, '__spec__', None):
    args = autoreload.get_child_arguments()
print("args =", args)
expected = [sys.executable, '-Werror', script, 'runserver']
ok = (not any(a.startswith('-X') for a in args)) and args == expected
print("HOLDS" if ok else "VIOLATED", "expected", expected)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R3.1 + R3.2 + R3.3: -m module reconstruction, executable first, -W kept before -X
import sys, __main__
from types import SimpleNamespace
from unittest import mock
from django.utils import autoreload

fake_spec = SimpleNamespace(name='__main__', parent='django')
with mock.patch.object(sys, 'argv', ['-m', 'runserver', '--noreload']), \
     mock.patch.object(sys, 'warnoptions', ['error']), \
     mock.patch.object(sys, '_xoptions', {'utf8': True}), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', fake_spec):
    args = autoreload.get_child_arguments()
print("args =", args)
# expected: [exe, -Werror, -Xutf8, -m, django, runserver, --noreload]  (sys.argv[1:])
ok = (args[0] == sys.executable
      and args[1] == '-Werror'
      and args[2] == '-Xutf8'
      and args[3:5] == ['-m', 'django']
      and args[5:] == ['runserver', '--noreload'])
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# R3.7: nonexistent script and no .exe/-script.py entry point => RuntimeError
import sys, os, tempfile, __main__
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'nope_manage.py')  # does not exist
raised = False
with mock.patch.object(sys, 'argv', [script, 'runserver']), \
     mock.patch.object(sys, 'warnoptions', []), \
     mock.patch.object(sys, '_xoptions', {}), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', None):
    try:
        args = autoreload.get_child_arguments()
        print("returned", args)
    except RuntimeError as e:
        raised = True
        print("RuntimeError:", e)
print("HOLDS" if raised else "VIOLATED")
sys.exit(0 if raised else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 + R1.2 (POSITIVE CONTROL): flag-style -X option rendered as -Xutf8
import sys, os, tempfile, __main__
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'manage.py'); open(script,'w').write('#\n')
with mock.patch.object(sys, 'argv', [script, 'runserver']), \
     mock.patch.object(sys, 'warnoptions', []), \
     mock.patch.object(sys, '_xoptions', {'utf8': True}), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', None):
    args = autoreload.get_child_arguments()
print("args =", args)
ok = '-Xutf8' in args and not any(a.startswith('-Xutf8=') for a in args)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: forward active `-X` interpreter options across auto-reload restarts in get_child_arguments(), CPython-only, after -W and before program args, preserving all prior reconstruction behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1+R1.2, POSITIVE CONTROL): flag-style -X {'utf8':True} rendered as single token '-Xutf8'. HOLDS patched, VIOLATED at base (base emits no -X). prepatch_reproduced=true.
- probe_2 (R1.3): value-style {'dev':'a=b'} rendered '-Xdev=a=b' (single leading '='). HOLDS.
- probe_3 (R1.4+R1.6): ordered {utf8:True,dev:True,foo:'bar'} => ['-Xutf8','-Xdev','-Xfoo=bar'] in _xoptions order, positioned after -Werror and before the script/program args. HOLDS.
- probe_4 (R1.5): empty _xoptions => no -X tokens. HOLDS.
- probe_5 (R2.1+R2.2): implementation.name='pypy' => no -X tokens; command line byte-identical to no-forwarding ([exe,-Werror,script,runserver]). HOLDS.
- probe_6 (R3.1+R3.2+R3.3): -m module path (__spec__ name='__main__', parent='django') => [exe,-Werror,-Xutf8,-m,django, *sys.argv[1:]]; executable first, -W kept before -X. HOLDS. (initial version had a wrong expected slice; corrected to sys.argv[1:] and re-verified.)
- probe_7 (R3.7): nonexistent script, no .exe/-script.py sibling => RuntimeError raised. HOLDS.

Candidate wrong patches (both apply at base_commit; both REJECTED by the suite -> suite discriminates):
- weak_noguard.diff: forwards -X but omits the `sys.implementation.name == 'cpython'` guard. REJECTED by probe_5 (emits -X tokens under pypy, violating R2.1/R2.2).
- weak_dropvalue.diff: guarded, but renders only '-X{key}' dropping the value. REJECTED by probe_2 (produces '-Xdev' instead of '-Xdev=a=b', violating R1.3).

All runs completed in the official image via nl_attack probe. Env: SBU_PYTHON conda swebench-lean. No probe failed on the patched tree; positive control discriminates base vs patched; >=1 candidate exercised and rejected. Verdict SOUND (advisory).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# R1.1 + R1.2 (POSITIVE CONTROL): flag-style -X option rendered as -Xutf8
import sys, os, tempfile, __main__
from unittest import mock
from django.utils import autoreload

d = tempfile.mkdtemp(); script = os.path.join(d, 'manage.py'); open(script,'w').write('#\n')
with mock.patch.object(sys, 'argv', [script, 'runserver']), \
     mock.patch.object(sys, 'warnoptions', []), \
     mock.patch.object(sys, '_xoptions', {'utf8': True}), \
     mock.patch.object(sys.implementation, 'name', 'cpython'), \
     mock.patch.object(__main__, '__spec__', None):
    args = autoreload.get_child_arguments()
print("args =", args)
ok = '-Xutf8' in args and not any(a.startswith('-Xutf8=') for a in args)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: forward active `-X` interpreter options across auto-reload restarts in get_child_arguments(), CPython-only, after -W and before program args, preserving all prior reconstruction behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1+R1.2, POSITIVE CONTROL): flag-style -X {'utf8':True} rendered as single token '-Xutf8'. HOLDS patched, VIOLATED at base (base emits no -X). prepatch_reproduced=true.
- probe_2 (R1.3): value-style {'dev':'a=b'} rendered '-Xdev=a=b' (single leading '='). HOLDS.
- probe_3 (R1.4+R1.6): ordered {utf8:True,dev:True,foo:'bar'} => ['-Xutf8','-Xdev','-Xfoo=bar'] in _xoptions order, positioned after -Werror and before the script/program args. HOLDS.
- probe_4 (R1.5): empty _xoptions => no -X tokens. HOLDS.
- probe_5 (R2.1+R2.2): implementation.name='pypy' => no -X tokens; command line byte-identical to no-forwarding ([exe,-Werror,script,runserver]). HOLDS.
- probe_6 (R3.1+R3.2+R3.3): -m module path (__spec__ name='__main__', parent='django') => [exe,-Werror,-Xutf8,-m,django, *sys.argv[1:]]; executable first, -W kept before -X. HOLDS. (initial version had a wrong expected slice; corrected to sys.argv[1:] and re-verified.)
- probe_7 (R3.7): nonexistent script, no .exe/-script.py sibling => RuntimeError raised. HOLDS.

Candidate wrong patches (both apply at base_commit; both REJECTED by the suite -> suite discriminates):
- weak_noguard.diff: forwards -X but omits the `sys.implementation.name == 'cpython'` guard. REJECTED by probe_5 (emits -X tokens under pypy, violating R2.1/R2.2).
- weak_dropvalue.diff: guarded, but renders only '-X{key}' dropping the value. REJECTED by probe_2 (produces '-Xdev' instead of '-Xdev=a=b', violating R1.3).

All runs completed in the official image via nl_attack probe. Env: SBU_PYTHON conda swebench-lean. No probe failed on the patched tree; positive control discriminates base vs patched; >=1 candidate exercised and rejected. Verdict SOUND (advisory).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified full function source on the patched image; exe_fallback branch (Req3.5) returns [exe_entrypoint, *sys.argv[1:]] without interpreter-option tokens and Req3.5 correctly omits them, while script_entrypoint branch (Req3.6) returns [*args, script_entrypoint, *sys.argv[1:]] including the interpreter-option tokens and Req3.6 correctly includes them. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the -X forwarding behavior generically in terms of sys._xoptions and sys.implementation.name, localizing the change to get_child_arguments() in django/utils/autoreload.py (both legitimate). The `-X utf8` example is drawn directly from the public problem_statement. The flag(True)->'-Xkey' vs value->'-Xkey=value' distinction is genuine CPython/sys._xoptions semantics, not a reproduction of the hidden test fixture {'utf8': True, 'a': 'b'}; the arbitrary test identifiers ('a','b'), the concrete assertion vector [sys.executable, '-Xutf8', '-Xa=b', __file__, 'runserver'], the mock.patch scaffolding, and the test names (test_xoptions, TestChildArguments) are absent. Ordering/placement requirements (after -W, before program args) describe behavior rather than transmitting test code. No test names/paths/ids, no quoted test or gold code, no fix-invented identifiers.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
