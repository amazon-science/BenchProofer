# P2 adversarial audit — pytest-dev__pytest-7982

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_symlink_recurse.py`, `probe_2_ordering.py`, `probe_3_recurse_predicate.py`, `probe_4_yield_once.py`, `probe_5_e2e_collect_both.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_symlink_recurse.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_symlink_recurse.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL / Requirement 1.1 & 1.4:
visit() SHALL descend into an entry that resolves to a directory even when the
entry is a symbolic link. Encoded directly against _pytest.pathlib.visit so it
discriminates: base has follow_symlinks=False (won't descend), patched descends.
"""
import os
import sys
import tempfile
from _pytest.pathlib import visit


def main() -> int:
    root = tempfile.mkdtemp(prefix="sbu_p1_")
    real = os.path.join(root, "realdir")
    os.mkdir(real)
    with open(os.path.join(real, "inside.txt"), "w") as f:
        f.write("x")
    link = os.path.join(root, "linkdir")
    os.symlink(real, link)

    yielded = [e.path for e in visit(root, recurse=lambda e: True)]
    # The file reached ONLY through the symlink dir:
    target = os.path.join(link, "inside.txt")
    print("yielded paths:", yielded)
    descended = target in yielded
    print("descended into symlinked dir:", descended)
    if not descended:
        print("FAIL: visit did not follow the symlinked directory")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 2 — `probe_2_ordering.py` → holds on the patched tree (good)

```python
"""Requirement 2.1 & 2.2:
visit() SHALL yield each directory level's entries sorted ascending by name
BEFORE the contents of any subdirectory (breadth-first, per level).
"""
import os
import sys
import tempfile
from _pytest.pathlib import visit


def main() -> int:
    root = tempfile.mkdtemp(prefix="sbu_p2_")
    # top-level entries out of order
    for name in ["b_file.txt", "a_dir", "c_file.txt"]:
        p = os.path.join(root, name)
        if name.endswith("_dir"):
            os.mkdir(p)
            with open(os.path.join(p, "z_child.txt"), "w") as f:
                f.write("x")
        else:
            with open(p, "w") as f:
                f.write("x")

    names = [os.path.basename(e.path) for e in visit(root, recurse=lambda e: True)]
    print("emission order:", names)

    # First three emitted must be the top level sorted ascending
    top = names[:3]
    if top != ["a_dir", "b_file.txt", "c_file.txt"]:
        print("FAIL: top level not sorted ascending / not emitted first:", top)
        return 1
    # Child must appear AFTER all three top-level entries (breadth-first).
    if "z_child.txt" not in names:
        print("FAIL: child not emitted at all")
        return 1
    if names.index("z_child.txt") < 3:
        print("FAIL: subdir contents emitted before top level finished")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 3 — `probe_3_recurse_predicate.py` → holds on the patched tree (good)

```python
"""Requirement 2.3 & 2.4:
- When recurse() does not select a directory entry, visit SHALL NOT descend.
- A non-directory entry SHALL be yielded but NOT descended into.
"""
import os
import sys
import tempfile
from _pytest.pathlib import visit


def main() -> int:
    root = tempfile.mkdtemp(prefix="sbu_p3_")
    skip = os.path.join(root, "skipdir")
    os.mkdir(skip)
    with open(os.path.join(skip, "hidden.txt"), "w") as f:
        f.write("x")
    keep = os.path.join(root, "keepdir")
    os.mkdir(keep)
    with open(os.path.join(keep, "shown.txt"), "w") as f:
        f.write("x")
    with open(os.path.join(root, "top.txt"), "w") as f:
        f.write("x")

    # recurse selects everything except skipdir
    def recurse(entry):
        return os.path.basename(entry.path) != "skipdir"

    paths = [e.path for e in visit(root, recurse=recurse)]
    names = [os.path.basename(p) for p in paths]
    print("yielded:", names)

    # skipdir itself is yielded (as an entry) but its content is NOT
    if "skipdir" not in names:
        print("FAIL: skipdir entry not yielded")
        return 1
    if "hidden.txt" in names:
        print("FAIL: descended into non-selected dir")
        return 1
    # keepdir content IS present
    if "shown.txt" not in names:
        print("FAIL: did not descend into selected dir")
        return 1
    # top-level file yielded, obviously not descended (it's a file)
    if "top.txt" not in names:
        print("FAIL: top-level file not yielded")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 4 — `probe_4_yield_once.py` → holds on the patched tree (good)

```python
"""Requirement 2.5:
visit SHALL yield every entry of the starting directory level exactly once,
preserving the set of non-symlinked directories and files.
"""
import os
import sys
import tempfile
from _pytest.pathlib import visit


def main() -> int:
    root = tempfile.mkdtemp(prefix="sbu_p4_")
    names_expected = {"f1.txt", "f2.txt", "d1", "d2"}
    for n in names_expected:
        p = os.path.join(root, n)
        if n.startswith("d"):
            os.mkdir(p)
        else:
            open(p, "w").close()

    entries = list(visit(root, recurse=lambda e: False))  # no descent
    top_names = [os.path.basename(e.path) for e in entries]
    print("top level entries:", top_names)

    if sorted(top_names) != sorted(names_expected):
        print("FAIL: top-level set mismatch")
        return 1
    if len(top_names) != len(set(top_names)):
        print("FAIL: some entry yielded more than once")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 5 — `probe_5_e2e_collect_both.py` → holds on the patched tree (good)

```python
"""Requirement 1.2 & 1.3:
End-to-end. A tree with a real top-level test file AND a symlinked directory
containing a test file: pytest SHALL collect and run BOTH tests.
Uses the repo's own pytest via `python -m pytest` in a subprocess (the repo
package), parsing the summary line — the probe itself is not a pytest test.
"""
import os
import subprocess
import sys
import tempfile


def main() -> int:
    root = tempfile.mkdtemp(prefix="sbu_p5_")
    # real top-level test
    with open(os.path.join(root, "test_top.py"), "w") as f:
        f.write("def test_top():\n    assert True\n")
    # real dir (placed outside collection root so only the symlink reaches it)
    realbox = tempfile.mkdtemp(prefix="sbu_p5real_")
    with open(os.path.join(realbox, "test_inside.py"), "w") as f:
        f.write("def test_inside():\n    assert True\n")
    os.symlink(realbox, os.path.join(root, "symlink_dir"))

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", root, "-p", "no:cacheprovider", "-q",
         "--no-header", "-o", "addopts="],
        capture_output=True, text=True, cwd=root, env=env,
    )
    out = r.stdout + "\n" + r.stderr
    print(out[-1500:])
    # Expect both tests collected and passed.
    if "2 passed" not in out:
        print("FAIL: expected '2 passed' (both real and symlinked tests)")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_symlink_recurse.py`

```python
"""POSITIVE CONTROL / Requirement 1.1 & 1.4:
visit() SHALL descend into an entry that resolves to a directory even when the
entry is a symbolic link. Encoded directly against _pytest.pathlib.visit so it
discriminates: base has follow_symlinks=False (won't descend), patched descends.
"""
import os
import sys
import tempfile
from _pytest.pathlib import visit


def main() -> int:
    root = tempfile.mkdtemp(prefix="sbu_p1_")
    real = os.path.join(root, "realdir")
    os.mkdir(real)
    with open(os.path.join(real, "inside.txt"), "w") as f:
        f.write("x")
    link = os.path.join(root, "linkdir")
    os.symlink(real, link)

    yielded = [e.path for e in visit(root, recurse=lambda e: True)]
    # The file reached ONLY through the symlink dir:
    target = os.path.join(link, "inside.txt")
    print("yielded paths:", yielded)
    descended = target in yielded
    print("descended into symlinked dir:", descended)
    if not descended:
        print("FAIL: visit did not follow the symlinked directory")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: restore pre-6.1.0 behavior so visit() in src/_pytest/pathlib.py descends into symlinked directories (remove follow_symlinks=False). Gold patch changes entry.is_dir(follow_symlinks=False) -> entry.is_dir().

Probe suite (all run in the official image via nl_attack probe):
- probe_1_symlink_recurse (Req 1.1/1.4, POSITIVE CONTROL): calls visit() directly on a tree with a symlinked dir; asserts a file reachable only through the symlink is yielded. VIOLATED at base (descended=False), HOLDS gold-patched (descended=True). Discriminates.
- probe_2_ordering (Req 2.1/2.2): top level emitted sorted ascending and before subdir contents (breadth-first). HOLDS patched.
- probe_3_recurse_predicate (Req 2.3/2.4): non-selected dir not descended; non-dir yielded not descended; selected dir descended. HOLDS patched.
- probe_4_yield_once (Req 2.5): every starting-level entry yielded exactly once, set preserved. HOLDS patched.
- probe_5_e2e_collect_both (Req 1.2/1.3): end-to-end `python -m pytest` over a tree with a real top test + symlinked dir test; expects '2 passed'. HOLDS patched (2 passed).

Candidate wrong-fix: weak_noop.diff — a comment-only no-op that leaves follow_symlinks=False. Applies cleanly at base. REJECTED by probe_1 (descended=False) and probe_5 (only 1 passed), while probe_2 still HOLDS. This demonstrates the suite discriminates a non-fixing implementation; the required FAIL_TO_PASS test (test_collect_symlink_dir) would not resolve under it.

All 5 probes hold on the patched tree; positive control fails at base and holds patched; a probe-conforming-but-wrong candidate is rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_symlink_recurse.py`, `probe_2_ordering.py`, `probe_3_recurse_predicate.py`, `probe_4_yield_once.py`, `probe_5_e2e_collect_both.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_symlink_recurse.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_symlink_recurse.py` → holds on the patched tree (good)

Attack 2 — `probe_2_ordering.py` → holds on the patched tree (good)

Attack 3 — `probe_3_recurse_predicate.py` → holds on the patched tree (good)

Attack 4 — `probe_4_yield_once.py` → holds on the patched tree (good)

Attack 5 — `probe_5_e2e_collect_both.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_symlink_recurse.py`

```python
"""POSITIVE CONTROL / Requirement 1.1 & 1.4:
visit() SHALL descend into an entry that resolves to a directory even when the
entry is a symbolic link. Encoded directly against _pytest.pathlib.visit so it
discriminates: base has follow_symlinks=False (won't descend), patched descends.
"""
import os
import sys
import tempfile
from _pytest.pathlib import visit


def main() -> int:
    root = tempfile.mkdtemp(prefix="sbu_p1_")
    real = os.path.join(root, "realdir")
    os.mkdir(real)
    with open(os.path.join(real, "inside.txt"), "w") as f:
        f.write("x")
    link = os.path.join(root, "linkdir")
    os.symlink(real, link)

    yielded = [e.path for e in visit(root, recurse=lambda e: True)]
    # The file reached ONLY through the symlink dir:
    target = os.path.join(link, "inside.txt")
    print("yielded paths:", yielded)
    descended = target in yielded
    print("descended into symlinked dir:", descended)
    if not descended:
        print("FAIL: visit did not follow the symlinked directory")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: restore pre-6.1.0 behavior so visit() in src/_pytest/pathlib.py descends into symlinked directories (remove follow_symlinks=False). Gold patch changes entry.is_dir(follow_symlinks=False) -> entry.is_dir().

Probe suite (all run in the official image via nl_attack probe):
- probe_1_symlink_recurse (Req 1.1/1.4, POSITIVE CONTROL): calls visit() directly on a tree with a symlinked dir; asserts a file reachable only through the symlink is yielded. VIOLATED at base (descended=False), HOLDS gold-patched (descended=True). Discriminates.
- probe_2_ordering (Req 2.1/2.2): top level emitted sorted ascending and before subdir contents (breadth-first). HOLDS patched.
- probe_3_recurse_predicate (Req 2.3/2.4): non-selected dir not descended; non-dir yielded not descended; selected dir descended. HOLDS patched.
- probe_4_yield_once (Req 2.5): every starting-level entry yielded exactly once, set preserved. HOLDS patched.
- probe_5_e2e_collect_both (Req 1.2/1.3): end-to-end `python -m pytest` over a tree with a real top test + symlinked dir test; expects '2 passed'. HOLDS patched (2 passed).

Candidate wrong-fix: weak_noop.diff — a comment-only no-op that leaves follow_symlinks=False. Applies cleanly at base. REJECTED by probe_1 (descended=False) and probe_5 (only 1 passed), while probe_2 still HOLDS. This demonstrates the suite discriminates a non-fixing implementation; the required FAIL_TO_PASS test (test_collect_symlink_dir) would not resolve under it.

All 5 probes hold on the patched tree; positive control fails at base and holds patched; a probe-conforming-but-wrong candidate is rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Req 2 (sort ascending per level, breadth-first per level, recurse filter honored, non-dir yielded-not-descended, each entry once) describes the unchanged surrounding code and is preserved by the one-line diff — verified by probe. Req 3 (CLI symlink arg, out-of-tree link target, norecursedirs/venv/collect_ignore, nested real subdirs) covers unrelated safeguards genuinely untouched by the change; the diff does not modify any of those code paths. Modeling boundary is correct: requirements target the changed observable traversal behavior of visit() (the F2P test_collect_symlink_dir), not a helper or single branch.

Counterexample / evidence:

```
N/A — no divergence found. Patched probe: visit over {realdir/a.txt, linkdir->{b.txt}, top.txt} yields ['a.txt','b.txt','linkdir','realdir','top.txt']; base fails to include b.txt. recurse=False and symlink-to-file edges (Req 2.3/2.4) confirmed: recurse-false yields ['f.txt','linkfile','sub'] (no descent), symlink-to-file yielded not descended.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes only public/behavioral content. The fix location and nature (remove follow_symlinks=False in visit) is already in the public problem_statement. Named identifiers (visit, recurse, pathlib.py, Package.collect, Session, norecursedirs, collect_ignore/collect_ignore_glob, virtualenv detection) are legitimate localization and public pytest concepts, not fix-invented. No test file paths, test function/class names (e.g. test_collect_symlink_dir), parametrization ids, quoted test/gold code, or the passed=2 outcome appear. Req 1.3 is a generalized scenario that does not match the actual test's structure. Req 3's enumeration maps to PASS_TO_PASS *behaviors* (symlink file-arg, out-of-tree symlink, nested real subdirs) but transmits behavioral preservation properties rather than the tests themselves — the intended translation, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
