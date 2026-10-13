# P2 adversarial audit — sympy__sympy-21930

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import Bd

s = Symbol('s')
out = Bd(s)._latex(None) if False else latex(Bd(s))
print("CreateBoson latex:", repr(out))
# Req1.1: grouped token {b^\dagger_{s}}
expected = r"{b^\dagger_{s}}"
sys.exit(0 if out == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import Bd

s = Symbol('s')
out = latex(Bd(s)**2)
print("CreateBoson**2 latex:", repr(out))
# Req1.2: exponent binds to whole grouped token
expected = r"{b^\dagger_{s}}^{2}"
sys.exit(0 if out == expected else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import Fd

s = Symbol('s')
out = latex(Fd(s))
print("CreateFermion latex:", repr(out))
# Req2.1: grouped token {a^\dagger_{s}}
expected = r"{a^\dagger_{s}}"
sys.exit(0 if out == expected else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import AntiSymmetricTensor

i, j, k, l = map(Symbol, 'ijkl')
t = AntiSymmetricTensor('t', (i, j), (k, l))
out = latex(t)
print("AntiSymmetricTensor latex:", repr(out))
# Req3.1/3.2: {t^{ij}_{kl}}
expected = r"{t^{ij}_{kl}}"
sys.exit(0 if out == expected else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import B, F

s = Symbol('s')
ob = latex(B(s))
of = latex(F(s))
print("AnnihilateBoson latex:", repr(ob))
print("AnnihilateFermion latex:", repr(of))
# Req4: b_{s} and a_{s} with no outer brace
ok = (ob == r"b_{s}") and (of == r"a_{s}")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import B, Bd, Commutator

s = Symbol('0')
c = Commutator(Bd(s)**2, B(s))
out = latex(c)
print("Commutator latex:", repr(out))
# Req5.3: well-formed, exponent binds grouped token, annihilator plain
expected = r"- \left[b_{0},{b^\dagger_{0}}^{2}\right]"
sys.exit(0 if out == expected else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
from sympy import Symbol, srepr
from sympy.physics.secondquant import Bd, Fd

s = Symbol('s')
rb = repr(Bd(s)); sb = str(Bd(s)); zb = srepr(Bd(s))
rf = repr(Fd(s)); sf = str(Fd(s)); zf = srepr(Fd(s))
print("Bd repr/str/srepr:", rb, sb, zb)
print("Fd repr/str/srepr:", rf, sf, zf)
# Req5.4: textual forms unchanged (no braces / latex leakage)
ok = (rb == "CreateBoson(s)" and sb == "b+(s)" and
      zb == "CreateBoson(Symbol('s'))" and
      rf == "CreateFermion(s)" and sf == "f+(s)" and
      zf == "CreateFermion(Symbol('s'))")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import Bd

s = Symbol('s')
out = latex(Bd(s)**2)
print("CreateBoson**2 latex:", repr(out))
# Req1.2: exponent binds to whole grouped token
expected = r"{b^\dagger_{s}}^{2}"
sys.exit(0 if out == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 5 requirements. probe_1 (Req1.1 {b^\dagger_{s}}), probe_2 (Req1.2 exponent binds: {b^\dagger_{s}}^{2}; POSITIVE CONTROL — HOLDS patched, FAILS at base where output is b^\dagger_{s}^{2}), probe_3 (Req2.1 {a^\dagger_{s}}), probe_4 (Req3.1/3.2 {t^{ij}_{kl}} with in-order index concatenation), probe_5 (Req4 annihilators unchanged: b_{s}, a_{s}), probe_6 (Req5.3 commutator - \left[b_{0},{b^\dagger_{0}}^{2}\right]), probe_7 (Req5.4 repr/str/srepr unchanged). All 7 HOLD on gold-patched tree. Positive control discriminates (fails at base). Candidate patch 'partial_boson_only' patches only CreateBoson._latex — a weak reading fixing just the reported operator; probe suite REJECTS it (probe_3 and probe_4 fail: fermion and tensor still emit bare tokens), demonstrating discrimination. No requirements-conforming patch that would fail the hidden tests was found; the three renderers are exactly the changed behavior and all are pinned. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import sys
from sympy import latex, Symbol
from sympy.physics.secondquant import Bd

s = Symbol('s')
out = latex(Bd(s)**2)
print("CreateBoson**2 latex:", repr(out))
# Req1.2: exponent binds to whole grouped token
expected = r"{b^\dagger_{s}}^{2}"
sys.exit(0 if out == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 5 requirements. probe_1 (Req1.1 {b^\dagger_{s}}), probe_2 (Req1.2 exponent binds: {b^\dagger_{s}}^{2}; POSITIVE CONTROL — HOLDS patched, FAILS at base where output is b^\dagger_{s}^{2}), probe_3 (Req2.1 {a^\dagger_{s}}), probe_4 (Req3.1/3.2 {t^{ij}_{kl}} with in-order index concatenation), probe_5 (Req4 annihilators unchanged: b_{s}, a_{s}), probe_6 (Req5.3 commutator - \left[b_{0},{b^\dagger_{0}}^{2}\right]), probe_7 (Req5.4 repr/str/srepr unchanged). All 7 HOLD on gold-patched tree. Positive control discriminates (fails at base). Candidate patch 'partial_boson_only' patches only CreateBoson._latex — a weak reading fixing just the reported operator; probe suite REJECTS it (probe_3 and probe_4 fail: fermion and tensor still emit bare tokens), demonstrating discrimination. No requirements-conforming patch that would fail the hidden tests was found; the three renderers are exactly the changed behavior and all are pinned. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch changes exactly the three _latex methods (AntiSymmetricTensor, CreateBoson, CreateFermion) by wrapping the emitted token in an outer brace pair. The requirements pin precisely these three renderers and correctly forbid changes to annihilation ops and container printers (verified: base emits unbraced 'b^\dagger_{0}' -> double-superscript 'b^\dagger_{0}^{2}', patched emits '{...}'). Modeling boundary is the changed observable behavior, not a narrow slice. R5.3's leading minus sign in the example is illustrative ('e.g.') and non-binding; the patch does not alter sign logic. Requirement 5.4 (repr/str/srepr unchanged) is consistent with the patch, which touches only _latex. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes the observable LaTeX-rendering behavior of the three affected `_latex` methods (CreateBoson/Bd, CreateFermion/Fd, AntiSymmetricTensor/AT) and localizes the fix there — legitimate localization. The specific tokens it cites either come straight from the public problem_statement (bosonic `{b^\dagger_{0}}^{2}` and the full commutator `- \left[b_{0},{b^\dagger_{0}}^{2}\right]`, = test_issue_19661) or are the observable output of the module's public `_latex` source (fermionic `{a^\dagger_{s}}`, tensor `{t^{<upper>}_{<lower>}}`); the gold fix invents no new identifiers, it only wraps the existing token in braces. Req 3 abstracts the test's concrete `t^{ab}_{ij}` into generic <upper>/<lower> blocks rather than copying the parametrized values. No test file path, test/function names, parametrization ids, or quoted test code appear; the Req1–5 enumeration tracks the affected renderers vs unchanged annihilation/container printers, which is derivable from the source and gold-patch structure, not a mirror of the hidden test cases. This is the intended translation of tests-into-behavior, not transmission of the tests themselves.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
