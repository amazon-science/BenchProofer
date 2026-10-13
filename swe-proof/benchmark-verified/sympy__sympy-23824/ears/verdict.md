# P2 adversarial audit — sympy__sympy-23824

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
"""Req 1.2 / positive control: rho*sigma*mu*(-mu) -> 4*rho*sigma (order preserved)."""
import sys
from sympy.physics.hep.gamma_matrices import GammaMatrix as G, kahane_simplify, LorentzIndex
from sympy.tensor.tensor import tensor_indices

rho, sigma, mu = tensor_indices('rho sigma mu', LorentzIndex)

expr = G(rho)*G(sigma)*G(mu)*G(-mu)
res = kahane_simplify(expr)
expected = 4*G(rho)*G(sigma)
wrong = 4*G(sigma)*G(rho)
print("result :", res)
print("expected:", expected)
print("wrong   :", wrong)

def canon(e):
    return str(e)

ok = canon(res) == canon(expected)
is_wrong = canon(res) == canon(wrong)
print("matches expected:", ok, "| matches wrong(reversed):", is_wrong)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1: mu*(-mu)*rho*sigma (contraction first, free matrices trailing) -> 4*rho*sigma."""
import sys
from sympy.physics.hep.gamma_matrices import GammaMatrix as G, kahane_simplify, LorentzIndex
from sympy.tensor.tensor import tensor_indices

rho, sigma, mu = tensor_indices('rho sigma mu', LorentzIndex)
res = kahane_simplify(G(mu)*G(-mu)*G(rho)*G(sigma))
expected = 4*G(rho)*G(sigma)
print("result  :", res)
print("expected:", expected)
ok = str(res) == str(expected)
print("match:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.3: three leading free matrices before a contraction keep left-to-right order.
a*b*c*mu*(-mu) -> 4*a*b*c (not any reordering of a,b,c)."""
import sys
from itertools import permutations
from sympy.physics.hep.gamma_matrices import GammaMatrix as G, kahane_simplify, LorentzIndex
from sympy.tensor.tensor import tensor_indices

a, b, c, mu = tensor_indices('a b c mu', LorentzIndex)
res = kahane_simplify(G(a)*G(b)*G(c)*G(mu)*G(-mu))
expected = 4*G(a)*G(b)*G(c)
print("result  :", res)
print("expected:", expected)
ok = str(res) == str(expected)
print("match expected:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.4: full contraction to a pure scalar returns scalar * 4x4 identity (matrix form)."""
import sys
from sympy.physics.hep.gamma_matrices import GammaMatrix as G, kahane_simplify, LorentzIndex
from sympy.tensor.tensor import tensor_indices
from sympy import eye

mu = tensor_indices('mu', LorentzIndex)
res = kahane_simplify(G(mu)*G(-mu))
print("result:", res, "| type:", type(res))
# Expect 4 * identity(4).  Compare to sympy ImmutableMatrix / eye(4)*4
ok = False
try:
    m = res.doit() if hasattr(res, 'doit') else res
except Exception:
    m = res
try:
    ok = (res == 4*eye(4))
except Exception:
    ok = False
if not ok:
    # fallback: shape 4x4 and equals 4*I
    try:
        ok = res.shape == (4,4) and res == 4*eye(4)
    except Exception:
        ok = False
print("equals 4*eye(4):", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.2/2.3/2.5: enclosed contraction with a leading free matrix.
a * mu * rho * (-mu): identity gamma^mu gamma^rho gamma_mu = -2 gamma^rho,
so result must equal -2 * a * rho (sign, factor, non-leading order preserved;
leading free 'a' stays in front)."""
import sys
from sympy.physics.hep.gamma_matrices import GammaMatrix as G, kahane_simplify, LorentzIndex
from sympy.tensor.tensor import tensor_indices

a, rho, mu = tensor_indices('a rho mu', LorentzIndex)
res = kahane_simplify(G(a)*G(mu)*G(rho)*G(-mu))
expected = -2*G(a)*G(rho)
print("result  :", res)
print("expected:", expected)
ok = str(res) == str(expected)
print("match:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.2 / positive control: rho*sigma*mu*(-mu) -> 4*rho*sigma (order preserved)."""
import sys
from sympy.physics.hep.gamma_matrices import GammaMatrix as G, kahane_simplify, LorentzIndex
from sympy.tensor.tensor import tensor_indices

rho, sigma, mu = tensor_indices('rho sigma mu', LorentzIndex)

expr = G(rho)*G(sigma)*G(mu)*G(-mu)
res = kahane_simplify(expr)
expected = 4*G(rho)*G(sigma)
wrong = 4*G(sigma)*G(rho)
print("result :", res)
print("expected:", expected)
print("wrong   :", wrong)

def canon(e):
    return str(e)

ok = canon(res) == canon(expected)
is_wrong = canon(res) == canon(wrong)
print("matches expected:", ok, "| matches wrong(reversed):", is_wrong)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover the requirements: probe_1 (Req 1.2, positive control) rho*sigma*mu*(-mu)->4*rho*sigma; HOLDS patched, VIOLATED at base (base gives 4*sigma*rho, the reversed defect). probe_2 (Req 2.1) contraction-first mu*(-mu)*rho*sigma->4*rho*sigma. probe_3 (Req 1.1/1.3) three leading free matrices a*b*c*mu*(-mu)->4*a*b*c order preserved. probe_4 (Req 2.4) mu*(-mu)->4*eye(4), scalar returned in matrix form. probe_5 (Req 2.2/2.3/2.5) enclosed contraction a*mu*rho*(-mu)->-2*a*rho, sign/factor/non-leading order intact. All 5 HOLD on gold-patched tree.

Candidate wrong-fix (weak.diff): prepends leading free positions in REVERSED order (the lazy fix a weak reading permits). Probe suite REJECTS it: probe_1 -> 4*sigma*rho (VIOLATED), probe_3 -> 4*c*b*a (VIOLATED). probes 2/4/5 still hold (they don't involve >=2 leading free matrices), confirming the suite's discriminating power is concentrated exactly on the ordering criterion. This candidate would also fail the hidden tests, so it is correctly a rejected wrong-fix, not a too-weak finding. Suite discriminates: >=1 candidate exercised and rejected.

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
"""Req 1.2 / positive control: rho*sigma*mu*(-mu) -> 4*rho*sigma (order preserved)."""
import sys
from sympy.physics.hep.gamma_matrices import GammaMatrix as G, kahane_simplify, LorentzIndex
from sympy.tensor.tensor import tensor_indices

rho, sigma, mu = tensor_indices('rho sigma mu', LorentzIndex)

expr = G(rho)*G(sigma)*G(mu)*G(-mu)
res = kahane_simplify(expr)
expected = 4*G(rho)*G(sigma)
wrong = 4*G(sigma)*G(rho)
print("result :", res)
print("expected:", expected)
print("wrong   :", wrong)

def canon(e):
    return str(e)

ok = canon(res) == canon(expected)
is_wrong = canon(res) == canon(wrong)
print("matches expected:", ok, "| matches wrong(reversed):", is_wrong)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover the requirements: probe_1 (Req 1.2, positive control) rho*sigma*mu*(-mu)->4*rho*sigma; HOLDS patched, VIOLATED at base (base gives 4*sigma*rho, the reversed defect). probe_2 (Req 2.1) contraction-first mu*(-mu)*rho*sigma->4*rho*sigma. probe_3 (Req 1.1/1.3) three leading free matrices a*b*c*mu*(-mu)->4*a*b*c order preserved. probe_4 (Req 2.4) mu*(-mu)->4*eye(4), scalar returned in matrix form. probe_5 (Req 2.2/2.3/2.5) enclosed contraction a*mu*rho*(-mu)->-2*a*rho, sign/factor/non-leading order intact. All 5 HOLD on gold-patched tree.

Candidate wrong-fix (weak.diff): prepends leading free positions in REVERSED order (the lazy fix a weak reading permits). Probe suite REJECTS it: probe_1 -> 4*sigma*rho (VIOLATED), probe_3 -> 4*c*b*a (VIOLATED). probes 2/4/5 still hold (they don't involve >=2 leading free matrices), confirming the suite's discriminating power is concentrated exactly on the ordering criterion. This candidate would also fail the hidden tests, so it is correctly a rejected wrong-fix, not a too-weak finding. Suite discriminates: >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly one line: the leading-free-matrix re-attachment loop `[ri.insert(0, free_pos[i]) for i in range(first_dum_pos)]` (which prepends in reverse) is replaced by `free_pos[0:first_dum_pos] + ri` (forward order). Requirements 1.1-1.4 pin precisely this observable: preserve left-to-right order of leading uncontracted gammas before the first contraction, prepended to every term. Requirement 2 correctly fences off the unchanged behaviors (contraction-first, interior/enclosed frees, scalar factor/sign, identity-matrix scalar form). The modeling boundary is the changed observable behavior, not a narrower slice — the enclosed/interior case (Req2.2) is explicitly stated as unchanged, consistent with the patch touching only leading frees. No invented behavior, no forbidden-but-present or mandated-but-absent behavior found. Probe HOLDS on patched, VIOLATED on base for the same assertions.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Every concrete example in requirements.md is already in the PUBLIC problem_statement: the two products `GammaMatrix(rho)*GammaMatrix(sigma)*GammaMatrix(mu)*GammaMatrix(-mu)` and `GammaMatrix(mu)*GammaMatrix(-mu)*GammaMatrix(rho)*GammaMatrix(sigma)` both simplifying to `4*GammaMatrix(rho)*GammaMatrix(sigma)` appear in the public bug report. The index names (mu, rho, sigma) are public. The hidden test_patch's discriminating content is NOT transmitted: the test function name `test_kahane_simplify1` is absent, and the enclosed-contraction case `G(mu)*G(nu)*G(rho)*G(sigma)*G(-mu)` → `-2*G(sigma)*G(rho)*G(nu)` (with its specific -2 sign and reordered result) is described only in general behavioral terms in Req 2.2, never with the concrete expression, sign, or index ordering. Naming the function `kahane_simplify` and its module is legitimate localization. Req 2.4 (scalar → 4x4 identity) is general behavior, not a mirror of any parametrized case. No fix-invented identifiers leak (the gold edit introduces no new public names; `free_pos`/`first_dum_pos` are pre-existing internals not surfaced).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
