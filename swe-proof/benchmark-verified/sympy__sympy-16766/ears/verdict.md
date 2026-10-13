# P2 adversarial audit — sympy__sympy-16766

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
# Positive control (Req1.1/1.2/1.5): Indexed p[0] prints as "p[0]" with no unsupported warning.
from sympy import IndexedBase, symbols
from sympy.printing.pycode import pycode
p = IndexedBase("p")
s = pycode(p[0])
print("pycode(p[0]) =", repr(s))
assert s == "p[0]", s
assert "not supported" not in s.lower(), s
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.3: two indices -> comma+space inside one bracket pair "p[0, 1]".
from sympy import IndexedBase
from sympy.printing.pycode import pycode
p = IndexedBase("p")
s = pycode(p[0, 1])
print("pycode(p[0,1]) =", repr(s))
assert s == "p[0, 1]", s
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.4: non-trivial index printed with normal per-expr printing.
from sympy import IndexedBase, symbols
from sympy.printing.pycode import pycode
p = IndexedBase("p")
i, j = symbols("i j")
s = pycode(p[i + 1])
print("pycode(p[i+1]) =", repr(s))
# normal pycode of (i+1) is "i + 1"
assert s == "p[i + 1]", s
s2 = pycode(p[i, j])
print("pycode(p[i,j]) =", repr(s2))
assert s2 == "p[i, j]", s2
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req1.5: no "Not supported in Python" comment block for indexed expr.
from sympy import IndexedBase, symbols
from sympy.printing.pycode import pycode
p = IndexedBase("p")
s = pycode(p[0])
print("pycode(p[0]) =", repr(s))
assert "Not supported" not in s, s
assert "# Indexed" not in s, s
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2 regression: non-indexed expressions unchanged (values verified in-image).
import sys
from sympy import symbols, sign, sin, Abs
from sympy.printing.pycode import pycode
x = symbols("x")
checks = {
    "sin(x)": (pycode(sin(x)), "math.sin(x)"),
    "sign(x)": (pycode(sign(x)), "(0.0 if x == 0 else math.copysign(1, x))"),
    "Abs(x)": (pycode(Abs(x)), "abs(x)"),
    "x**2+1": (pycode(x**2 + 1), "x**2 + 1"),
}
for k,(got,exp) in checks.items():
    print(k, "=", repr(got), file=sys.stderr)
    assert got == exp, (k, got, exp)
print("OK", file=sys.stderr)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req1 via lambdify path: NumPy printer also renders subscription, no warning.
from sympy import IndexedBase
from sympy.printing.pycode import pycode, NumPyPrinter
p = IndexedBase("p")
s = pycode(p[0, 1])
print("pycode p[0,1]:", repr(s))
assert s == "p[0, 1]", s
n = NumPyPrinter().doprint(p[0, 1])
print("NumPyPrinter p[0,1]:", repr(n))
assert n == "p[0, 1]", n
assert "Not supported" not in n, n
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control (Req1.1/1.2/1.5): Indexed p[0] prints as "p[0]" with no unsupported warning.
from sympy import IndexedBase, symbols
from sympy.printing.pycode import pycode
p = IndexedBase("p")
s = pycode(p[0])
print("pycode(p[0]) =", repr(s))
assert s == "p[0]", s
assert "not supported" not in s.lower(), s
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1.1-1.5 and Req2 regression. Results (exit 0=holds): PATCHED all pass (1,2,3,4,5,6=0). BASE: probe_1..4,6 fail (exit1), probe_5 (regression, non-indexed unchanged) holds at base as expected. Positive control probe_1 (pycode(p[0])=='p[0]', no 'not supported') HOLDS patched, FAILS base -> discriminates. Two wrong-fix candidates BOTH REJECTED by the suite: weak_a (comma without space -> 'p[0,1]') and weak_b (only first index printed -> 'p[0]') each fail probe_2 (single-bracket 'p[0, 1]'), probe_3 (multi-index order+space), and probe_6 (NumPyPrinter path). So the suite discriminates wrong single/multi-index implementations. Probe values (sqrt->'sqrt(x)', sign, Abs->'abs(x)') empirically confirmed in-image. Note: meta.json records G-PANEL-3=fail (leakage: Req2 enumerates hidden-test roster), but that is a separate leakage gate; for spec-fidelity/too-weak the requirements faithfully pin the changed behavior and reject weak fixes.

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
# Positive control (Req1.1/1.2/1.5): Indexed p[0] prints as "p[0]" with no unsupported warning.
from sympy import IndexedBase, symbols
from sympy.printing.pycode import pycode
p = IndexedBase("p")
s = pycode(p[0])
print("pycode(p[0]) =", repr(s))
assert s == "p[0]", s
assert "not supported" not in s.lower(), s
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1.1-1.5 and Req2 regression. Results (exit 0=holds): PATCHED all pass (1,2,3,4,5,6=0). BASE: probe_1..4,6 fail (exit1), probe_5 (regression, non-indexed unchanged) holds at base as expected. Positive control probe_1 (pycode(p[0])=='p[0]', no 'not supported') HOLDS patched, FAILS base -> discriminates. Two wrong-fix candidates BOTH REJECTED by the suite: weak_a (comma without space -> 'p[0,1]') and weak_b (only first index printed -> 'p[0]') each fail probe_2 (single-bracket 'p[0, 1]'), probe_3 (multi-index order+space), and probe_6 (NumPyPrinter path). So the suite discriminates wrong single/multi-index implementations. Probe values (sqrt->'sqrt(x)', sign, Abs->'abs(x)') empirically confirmed in-image. Note: meta.json records G-PANEL-3=fail (leakage: Req2 enumerates hidden-test roster), but that is a separate leakage gate; for spec-fidelity/too-weak the requirements faithfully pin the changed behavior and reject weak fixes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch adds only _print_Indexed on PythonCodePrinter returning '{}[{}]'.format(str(base), ', '.join(printed indices)). Requirements pin exactly this changed observable behavior at the correct boundary (Indexed -> Python subscription), matching str(base) semantics for IndexedBase whose str is the symbol name. G-PANEL-3 in meta flags a leakage concern about Req2 enumerating the hidden-test roster, but (a) that is a leakage/traceability concern, not a faithfulness one, and (b) the actual requirements.md Req2 contains only two generic no-regression criteria (no verbatim hidden-test assertions), so it does not misdescribe or contradict the patched behavior. Faithfulness verdict is FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is unusually complete: it names IndexedBase("p"), shows pycode(p[0]), describes the '# Not supported in Python:' / '# Indexed' warning, and even quotes the exact gold fix (_print_Indexed with str(base) and ', '.join([self._print(ind) for ind in index])). Every element of requirements.md is derivable from that public text. The two-index example 'p[0, 1]' (Req 1 §3) coincides with the hidden test assertion prntr.doprint(p[0, 1]) == 'p[0, 1]', but base 'p' is public and the comma-space multi-index behavior follows directly from the public fix code's ', '.join(...) — a natural minimal behavioral illustration, not a reconstruction of the test suite. No hidden-only content leaks: no test function/file names (test_PythonCodePrinter, sympy/printing/tests/test_pycode.py), no parametrization ids, no fix-invented identifiers, no case enumeration mirroring test parametrization. Naming pycode.py/PythonCodePrinter/lambdify is legitimate localization. Verdict: NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
