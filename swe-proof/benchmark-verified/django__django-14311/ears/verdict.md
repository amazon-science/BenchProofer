# P2 adversarial audit — django__django-14311

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
"""Positive control / Requirement 1.3: dotted non-package module.
`python -m foo.bar.baz` (baz is a plain module) => spec.name='foo.bar.baz',
parent='foo.bar'. The reconstructed -m target MUST be the full 'foo.bar.baz'
(NOT reduced to 'foo.bar'). HOLDS on patched, FAILS at base (base uses parent).
"""
import sys, __main__


class FakeSpec:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


def run():
    sys.argv = ['/nowhere/does_not_exist_dir/foo.py', 'runserver', '--noreload=0']
    __main__.__spec__ = FakeSpec('foo.bar.baz', 'foo.bar')
    from django.utils import autoreload
    args = autoreload.get_child_arguments()
    print("args =", args)
    assert '-m' in args, "no -m emitted"
    target = args[args.index('-m') + 1]
    print("m-target =", target)
    assert target == 'foo.bar.baz', f"expected full dotted name, got {target!r}"
    # forwarded args must follow (Req 1.1)
    assert args[-2:] == ['runserver', '--noreload=0'], f"forwarded args wrong: {args[-2:]}"
    print("OK: full dotted module name preserved and argv forwarded")


run()
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.4 / 4: single top-level module `python -m foo` where foo.py
is a module => spec.name='foo', parent=''. MUST still emit -m foo, and must
NOT fall through to no--m / script-path handling. At base this is skipped
(parent empty) => falls through.
"""
import sys, __main__


class FakeSpec:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


def run():
    sys.argv = ['$SCRATCH/some_existing_placeholder.py', 'check']
    __main__.__spec__ = FakeSpec('foo', '')
    from django.utils import autoreload
    args = autoreload.get_child_arguments()
    print("args =", args)
    assert '-m' in args, "no -m emitted for single top-level module"
    target = args[args.index('-m') + 1]
    print("m-target =", target)
    assert target == 'foo', f"expected 'foo', got {target!r}"
    # must NOT be the script-path fallthrough: sys.argv[0] must not be appended raw
    assert args[-1] == 'check' and args.count('$SCRATCH/some_existing_placeholder.py') == 0, \
        f"fell through to script path: {args}"
    print("OK: -m foo emitted for single top-level module, no fallthrough")


run()
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 1.2 / 2.1: package launch `python -m pkg` runs pkg/__main__.py
=> spec.name='pkg.__main__', parent='pkg'. Reconstructed -m target MUST be the
parent 'pkg' (existing behavior preserved). This HOLDS at base and patched.
Also checks the exact '__main__' name form.
"""
import sys, __main__


class FakeSpec:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


def run():
    from django.utils import autoreload

    # case A: 'pkg.__main__' with parent 'pkg'
    sys.argv = ['/nowhere/xyz.py', 'runserver']
    __main__.__spec__ = FakeSpec('pkg.__main__', 'pkg')
    args = autoreload.get_child_arguments()
    print("A args =", args)
    assert '-m' in args and args[args.index('-m') + 1] == 'pkg', f"A: got {args}"

    # case B: name exactly '__main__' with parent 'pkg' (deeper: pkg.sub run as -m pkg.sub)
    __main__.__spec__ = FakeSpec('__main__', 'pkg.sub')
    args = autoreload.get_child_arguments()
    print("B args =", args)
    assert '-m' in args and args[args.index('-m') + 1] == 'pkg.sub', f"B: got {args}"

    print("OK: package launch reconstructs to parent package name")


run()
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 3.1 / 3.2: no __spec__ => no -m emitted; when sys.argv[0]
exists on disk, run interpreter against original sys.argv (script path path).
"""
import sys, os, tempfile, __main__


def run():
    # ensure no usable spec
    if hasattr(__main__, '__spec__'):
        __main__.__spec__ = None
    from django.utils import autoreload

    fd, script = tempfile.mkstemp(suffix='_manage.py')
    os.close(fd)
    sys.argv = [script, 'runserver', '0:8000']
    args = autoreload.get_child_arguments()
    print("args =", args)
    assert '-m' not in args, f"unexpected -m emitted: {args}"
    # script path path: original argv appended
    assert script in args, f"script path not present: {args}"
    assert args[-1] == '0:8000', f"argv not forwarded in order: {args}"
    print("OK: no spec => no -m, runs against original sys.argv")


run()
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2.2 / 1.5: warning options (-W) preserved and positioned before
the -m target; executable prefix is sys.executable. Uses the dotted-module case.
"""
import sys, __main__


class FakeSpec:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


def run():
    from django.utils import autoreload
    saved = list(sys.warnoptions)
    try:
        # inject a warning option
        sys.warnoptions[:] = ['ignore', 'error::DeprecationWarning']
        sys.argv = ['/nowhere/foo.py', 'runserver']
        __main__.__spec__ = FakeSpec('foo.bar.baz', 'foo.bar')
        args = autoreload.get_child_arguments()
        print("args =", args)
        assert args[0] == sys.executable, f"prefix not sys.executable: {args[0]!r}"
        wopts = ['-Wignore', '-Werror::DeprecationWarning']
        for w in wopts:
            assert w in args, f"missing warning option {w}: {args}"
        m_idx = args.index('-m')
        for w in wopts:
            assert args.index(w) < m_idx, f"warning option {w} not before -m: {args}"
        assert args[m_idx + 1] == 'foo.bar.baz', f"target wrong: {args}"
        print("OK: -W options preserved before -m target; sys.executable prefix")
    finally:
        sys.warnoptions[:] = saved


run()
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Requirement 1.3: dotted non-package module.
`python -m foo.bar.baz` (baz is a plain module) => spec.name='foo.bar.baz',
parent='foo.bar'. The reconstructed -m target MUST be the full 'foo.bar.baz'
(NOT reduced to 'foo.bar'). HOLDS on patched, FAILS at base (base uses parent).
"""
import sys, __main__


class FakeSpec:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


def run():
    sys.argv = ['/nowhere/does_not_exist_dir/foo.py', 'runserver', '--noreload=0']
    __main__.__spec__ = FakeSpec('foo.bar.baz', 'foo.bar')
    from django.utils import autoreload
    args = autoreload.get_child_arguments()
    print("args =", args)
    assert '-m' in args, "no -m emitted"
    target = args[args.index('-m') + 1]
    print("m-target =", target)
    assert target == 'foo.bar.baz', f"expected full dotted name, got {target!r}"
    # forwarded args must follow (Req 1.1)
    assert args[-2:] == ['runserver', '--noreload=0'], f"forwarded args wrong: {args[-2:]}"
    print("OK: full dotted module name preserved and argv forwarded")


run()
```

Prepatch bug re-encoded as an attack: `True`.

Target: get_child_arguments() in django/utils/autoreload.py reconstructs -m target from __main__.__spec__. Probes exercise all mandated behaviors by injecting a fake __main__.__spec__ (FakeSpec name/parent) and sys.argv, then calling get_child_arguments() in the official image.

Probe results (patched / base / weak-candidate):
- probe_1 (Req 1.3, 1.1; POSITIVE CONTROL): dotted non-package `python -m foo.bar.baz` (name='foo.bar.baz', parent='foo.bar') => -m target must be full 'foo.bar.baz' and argv[1:] forwarded. HOLDS patched; VIOLATED at base (base gives 'foo.bar' — drops final component); HOLDS weak.
- probe_2 (Req 1.4/4): single top-level module `python -m foo` (name='foo', parent=''). Must still emit -m foo, no fallthrough. HOLDS patched; VIOLATED at base (base skips -m because parent empty => RuntimeError script-not-exist); HOLDS weak.
- probe_3 (Req 1.2/2.1): package launch name='pkg.__main__' parent='pkg' AND name=='__main__' parent='pkg.sub' => target must be parent. HOLDS patched; HOLDS at base (unchanged behavior); VIOLATED under weak candidate (weak emits -m pkg.__main__ instead of -m pkg). This is the discriminating probe against the wrong fix.
- probe_4 (Req 3.1/3.2): no __spec__ + sys.argv[0] exists => no -m, run interpreter against original argv. HOLDS patched/base/weak.
- probe_5 (Req 2.2/1.5): -W warning options preserved and positioned before -m target; prefix is sys.executable. HOLDS patched/weak.

Positive control discriminates (fails at base, holds patched) => prepatch reproduced.

Candidate patch 'weak_use_full_name_always' replaces the whole condition with `-m __main__.__spec__.name` unconditionally — a lazy reading that satisfies the dotted/top-level SHALLs but breaks the package case (Req 1.2/2.1). The suite REJECTS it via probe_3, demonstrating discriminating power against a requirements-plausible wrong fix. No probe-conforming alternative patch was found that would fail the hidden tests.

All 5 probes hold on the gold-patched tree; positive control discriminates; wrong-fix candidate rejected. Verdict SOUND.

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
"""Positive control / Requirement 1.3: dotted non-package module.
`python -m foo.bar.baz` (baz is a plain module) => spec.name='foo.bar.baz',
parent='foo.bar'. The reconstructed -m target MUST be the full 'foo.bar.baz'
(NOT reduced to 'foo.bar'). HOLDS on patched, FAILS at base (base uses parent).
"""
import sys, __main__


class FakeSpec:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


def run():
    sys.argv = ['/nowhere/does_not_exist_dir/foo.py', 'runserver', '--noreload=0']
    __main__.__spec__ = FakeSpec('foo.bar.baz', 'foo.bar')
    from django.utils import autoreload
    args = autoreload.get_child_arguments()
    print("args =", args)
    assert '-m' in args, "no -m emitted"
    target = args[args.index('-m') + 1]
    print("m-target =", target)
    assert target == 'foo.bar.baz', f"expected full dotted name, got {target!r}"
    # forwarded args must follow (Req 1.1)
    assert args[-2:] == ['runserver', '--noreload=0'], f"forwarded args wrong: {args[-2:]}"
    print("OK: full dotted module name preserved and argv forwarded")


run()
```

Prepatch bug re-encoded as an attack: `True`.

Target: get_child_arguments() in django/utils/autoreload.py reconstructs -m target from __main__.__spec__. Probes exercise all mandated behaviors by injecting a fake __main__.__spec__ (FakeSpec name/parent) and sys.argv, then calling get_child_arguments() in the official image.

Probe results (patched / base / weak-candidate):
- probe_1 (Req 1.3, 1.1; POSITIVE CONTROL): dotted non-package `python -m foo.bar.baz` (name='foo.bar.baz', parent='foo.bar') => -m target must be full 'foo.bar.baz' and argv[1:] forwarded. HOLDS patched; VIOLATED at base (base gives 'foo.bar' — drops final component); HOLDS weak.
- probe_2 (Req 1.4/4): single top-level module `python -m foo` (name='foo', parent=''). Must still emit -m foo, no fallthrough. HOLDS patched; VIOLATED at base (base skips -m because parent empty => RuntimeError script-not-exist); HOLDS weak.
- probe_3 (Req 1.2/2.1): package launch name='pkg.__main__' parent='pkg' AND name=='__main__' parent='pkg.sub' => target must be parent. HOLDS patched; HOLDS at base (unchanged behavior); VIOLATED under weak candidate (weak emits -m pkg.__main__ instead of -m pkg). This is the discriminating probe against the wrong fix.
- probe_4 (Req 3.1/3.2): no __spec__ + sys.argv[0] exists => no -m, run interpreter against original argv. HOLDS patched/base/weak.
- probe_5 (Req 2.2/1.5): -W warning options preserved and positioned before -m target; prefix is sys.executable. HOLDS patched/weak.

Positive control discriminates (fails at base, holds patched) => prepatch reproduced.

Candidate patch 'weak_use_full_name_always' replaces the whole condition with `-m __main__.__spec__.name` unconditionally — a lazy reading that satisfies the dotted/top-level SHALLs but breaks the package case (Req 1.2/2.1). The suite REJECTS it via probe_3, demonstrating discriminating power against a requirements-plausible wrong fix. No probe-conforming alternative patch was found that would fail the hidden tests.

All 5 probes hold on the gold-patched tree; positive control discriminates; wrong-fix candidate rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: `if getattr(__main__,'__spec__',None) is not None:` then `name = spec.parent` iff (spec.name=='__main__' or endswith('.__main__')) and spec.parent, else `name = spec.name`; args += ['-m', name] + sys.argv[1:]. Probe HOLDS on patched (pkg->pkg, foo.bar.baz->foo.bar.baz, foo->foo, __main__->pkg), VIOLATED on base (foo.bar.baz->foo.bar). The endswith('.__main__') boundary detection and the always-emit-when-spec-present semantics (R1.4 no fall-through) are exactly as coded. R2 (package/warning preservation) and R3 (no-spec fallbacks unchanged) are outside the touched lines and correctly described as preserved.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the -m reconstruction behavior using the example foo.bar.baz taken directly from the public problem_statement. The detection rule ('__main__' or ends with '.__main__') mirrors the gold patch condition, but these are standard Python import-system identifiers, not fix-invented names, and stating the distinguishing rule is the legitimate act of localizing/describing the changed behavior. No hidden-test artifacts leak: the test name (test_run_as_non_django_module_non_package), test file path (tests/utils_tests/test_autoreload.py, test_module/main_module.py), and the specific test module identifier (utils_tests.test_module.main_module) never appear. The document uses foo.bar.baz, not the test's main_module fixture value. The three-case enumeration (package / dotted non-package / top-level single module) is behavioral — the top-level single-module case isn't even exercised by the shown test_patch, so it reflects code understanding rather than test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
