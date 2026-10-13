# P2 adversarial audit — astropy__astropy-14369

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
"""Positive control. Req1.3: km/s/Mpc == km * s^-1 * Mpc^-1.
Holds on patched, must FAIL at base (base mis-associates)."""
import sys
import astropy.units as u
from astropy.units.format import CDS

def close(parsed, expected):
    q = (parsed / expected).decompose()
    return q.physical_type == u.dimensionless_unscaled.physical_type and abs(float(q.scale) - 1.0) < 1e-12

parsed = CDS.parse("km/s/Mpc")
expected = u.km / (u.s * u.Mpc)
print("parsed =", parsed, "decompose=", parsed.decompose())
print("expected=", expected, "decompose=", expected.decompose())
ratio = (parsed / expected).decompose()
print("ratio =", ratio)
ok = close(parsed, expected)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4 & 1.5: 10+3J/m/s/kpc2 == 1000 * J * m^-1 * s^-1 * kpc^-2."""
import sys
import astropy.units as u
from astropy.units.format import CDS

parsed = CDS.parse("10+3J/m/s/kpc2")
expected_unit = u.J / (u.m * u.s * u.kpc**2)   # pure Unit (no numeric factor)
ratio = (parsed / expected_unit).decompose()   # Unit; scale should be 1000
print("parsed =", parsed.decompose())
print("ratio  =", repr(ratio), "scale=", ratio.scale, "ptype=", ratio.physical_type)
ok = (ratio.physical_type == "dimensionless") and abs(float(ratio.scale) - 1000.0) < 1e-6
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1 & 2.2: km/(s.Mpc) == km*s^-1*Mpc^-1, and equals km/s/Mpc."""
import sys
import astropy.units as u
from astropy.units.format import CDS

paren = CDS.parse("km/(s.Mpc)")
chain = CDS.parse("km/s/Mpc")
expected = u.km / (u.s * u.Mpc)
r1 = (paren / expected).decompose()
r2 = (paren / chain).decompose()
print("paren=", paren.decompose(), "chain=", chain.decompose())
print("r1=", r1, "r2=", r2)
ok = (r1.physical_type == u.dimensionless_unscaled.physical_type and abs(float(r1.scale)-1.0) < 1e-12
      and r2.physical_type == u.dimensionless_unscaled.physical_type and abs(float(r2.scale)-1.0) < 1e-12)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.3 & Req3: /s == s^-1 ; km/s.Mpc-1 rejected ; /s.Mpc rejected."""
import sys
import astropy.units as u
from astropy.units.format import CDS

ok = True

recip = CDS.parse("/s")
r = (recip / (u.s**-1)).decompose()
good = r.physical_type == u.dimensionless_unscaled.physical_type and abs(float(r.scale)-1.0) < 1e-12
print("/s ->", recip.decompose(), "ratio", r, "OK" if good else "BAD")
ok = ok and good

for bad in ["km/s.Mpc-1", "/s.Mpc"]:
    try:
        res = CDS.parse(bad)
        print(bad, "-> ACCEPTED (should reject):", res)
        ok = False
    except ValueError as e:
        print(bad, "-> rejected OK")

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4 regression: single division, product-neg-power, product forms, powers,
numeric factors, dimensionless, bracketed log units still parse correctly;
spaces/*/**/func-call/malformed still rejected."""
import sys
import astropy.units as u
from astropy.units.format import CDS

ok = True

def unit_eq(parsed, expected_unit, want_scale, tol=1e-6):
    r = (parsed / expected_unit).decompose()  # pure Unit
    return r.physical_type == "dimensionless" and abs(float(r.scale) - want_scale) < tol

# 4.1 km/s
kms = CDS.parse("km/s")
g = unit_eq(kms, u.km/u.s, 1.0); ok = ok and g
print("km/s", kms.decompose(), "OK" if g else "BAD")

# 4.2 km.s-1 == km/s
knp = CDS.parse("km.s-1")
g = unit_eq(knp, u.km/u.s, 1.0); ok = ok and g
print("km.s-1", knp.decompose(), "OK" if g else "BAD")

# 4.3 powers / factors (expected as pure Unit + expected scale)
checks = [
    ("m2", u.m**2, 1.0),
    ("s-1", u.s**-1, 1.0),
    ("2.54cm", u.cm, 2.54),
    ("10+21m", u.m, 1e21),
    ("1.5x10+11m", u.m, 1.5e11),
]
for s, exp_unit, want in checks:
    parsed = CDS.parse(s)
    g = unit_eq(parsed, exp_unit, want)
    ok = ok and g
    print(s, "->", parsed, "OK" if g else "BAD")

# dimensionless ---
try:
    d = CDS.parse("---")
    g = (d == u.dimensionless_unscaled)
    ok = ok and g
    print("--- ->", d, "OK" if g else "BAD")
except Exception as e:
    ok = False; print("--- raised", e)

# bracketed log units should parse without error
for s in ["[cm/s2]", "[K]", "[-]"]:
    try:
        r = CDS.parse(s)
        print(s, "->", r, "parsed OK")
    except Exception as e:
        ok = False; print(s, "raised", e)

# rejections
for bad in ["km / s", "km s-1", "km*s", "km**2", "dB(mW)", "dex(cm s-2)", "-m", "m-", "--", "[--]"]:
    try:
        res = CDS.parse(bad)
        print(bad, "-> ACCEPTED (should reject):", res)
        ok = False
    except ValueError:
        print(bad, "-> rejected OK")

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req1.3: km/s/Mpc == km * s^-1 * Mpc^-1.
Holds on patched, must FAIL at base (base mis-associates)."""
import sys
import astropy.units as u
from astropy.units.format import CDS

def close(parsed, expected):
    q = (parsed / expected).decompose()
    return q.physical_type == u.dimensionless_unscaled.physical_type and abs(float(q.scale) - 1.0) < 1e-12

parsed = CDS.parse("km/s/Mpc")
expected = u.km / (u.s * u.Mpc)
print("parsed =", parsed, "decompose=", parsed.decompose())
print("expected=", expected, "decompose=", expected.decompose())
ratio = (parsed / expected).decompose()
print("ratio =", ratio)
ok = close(parsed, expected)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover all 4 requirements. probe_1 (Req1.3, positive control): km/s/Mpc==km*s^-1*Mpc^-1 HOLDS patched, FAILS at base (base gives km*Mpc/s). probe_2 (Req1.4/1.5): 10+3J/m/s/kpc2 == 1000*J*m^-1*s^-1*kpc^-2 (scale 1000, denominator units) HOLDS. probe_3 (Req2.1/2.2): km/(s.Mpc) correct and equals km/s/Mpc HOLDS. probe_4 (Req2.3/Req3): /s==s^-1, km/s.Mpc-1 and /s.Mpc rejected HOLDS. probe_5 (Req4 regressions): km/s, km.s-1, m2, s-1, 2.54cm, 10+21m, 1.5x10+11m, ---, [cm/s2]/[K]/[-], and all reject cases (spaces, *, **, func-call, malformed sign/dimensionless) HOLD. Candidate weak.diff = the lazy fix: edit division_of_units in cds.py to combined_units DIVISION unit_expression but do NOT regenerate the LALR table cds_parsetab.py (which actually drives parsing).

Rejected by probes 1,2,3,4 (parsing still left-recursive-wrong: km/s/Mpc->km*Mpc/s, and km/s.Mpc-1 wrongly accepted); probe_5 regressions still green under it. Suite discriminates wrong implementations and the positive control discriminates base vs patched. All required runs completed. Note: comparing a parsed Unit against an expected Quantity-with-scale via (a/b).decompose() yields a Quantity lacking physical_type; probes compare against pure Units and check .scale separately.

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
"""Positive control. Req1.3: km/s/Mpc == km * s^-1 * Mpc^-1.
Holds on patched, must FAIL at base (base mis-associates)."""
import sys
import astropy.units as u
from astropy.units.format import CDS

def close(parsed, expected):
    q = (parsed / expected).decompose()
    return q.physical_type == u.dimensionless_unscaled.physical_type and abs(float(q.scale) - 1.0) < 1e-12

parsed = CDS.parse("km/s/Mpc")
expected = u.km / (u.s * u.Mpc)
print("parsed =", parsed, "decompose=", parsed.decompose())
print("expected=", expected, "decompose=", expected.decompose())
ratio = (parsed / expected).decompose()
print("ratio =", ratio)
ok = close(parsed, expected)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover all 4 requirements. probe_1 (Req1.3, positive control): km/s/Mpc==km*s^-1*Mpc^-1 HOLDS patched, FAILS at base (base gives km*Mpc/s). probe_2 (Req1.4/1.5): 10+3J/m/s/kpc2 == 1000*J*m^-1*s^-1*kpc^-2 (scale 1000, denominator units) HOLDS. probe_3 (Req2.1/2.2): km/(s.Mpc) correct and equals km/s/Mpc HOLDS. probe_4 (Req2.3/Req3): /s==s^-1, km/s.Mpc-1 and /s.Mpc rejected HOLDS. probe_5 (Req4 regressions): km/s, km.s-1, m2, s-1, 2.54cm, 10+21m, 1.5x10+11m, ---, [cm/s2]/[K]/[-], and all reject cases (spaces, *, **, func-call, malformed sign/dimensionless) HOLD. Candidate weak.diff = the lazy fix: edit division_of_units in cds.py to combined_units DIVISION unit_expression but do NOT regenerate the LALR table cds_parsetab.py (which actually drives parsing).

Rejected by probes 1,2,3,4 (parsing still left-recursive-wrong: km/s/Mpc->km*Mpc/s, and km/s.Mpc-1 wrongly accepted); probe_5 regressions still green under it. Suite discriminates wrong implementations and the positive control discriminates base vs patched. All required runs completed. Note: comparing a parsed Unit against an expected Quantity-with-scale via (a/b).decompose() yields a Quantity lacking physical_type; probes compare against pure Units and check .scale separately.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch flips the division_of_units production from `unit_expression DIVISION combined_units` (right-associative) to `combined_units DIVISION unit_expression` (left-associative), plus regenerated parsetab. Requirements pin the changed OBSERVABLE behavior (left-to-right division chains) rather than a narrow slice: R1 covers the chain semantics and scale-factor, R2 the parenthesised/leading-division equivalences, R3 the now-forbidden div-then-product form (a genuine consequence of the left-assoc rule — confirmed base accepted km/s.Mpc-1, patched rejects), R4 the no-regression set. Probed both patched and base trees in the instance image; all assertions hold on patched and the discriminating cases genuinely differ from base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the CDS division-chain fix as behavioral rules (left-to-right association; each post-leading term into the denominator; leading scale factor applied to the whole reduced chain; parenthesized/leading-division equivalences; reject division-then-unparenthesised-product), then instantiate each rule with a canonical minimal example. Example strings km/s/Mpc, km/(s.Mpc), /s, km/s.Mpc-1, /s.Mpc coincide with hidden test inputs, but each is the obvious minimal illustration of a rule the prose already fully states (e.g. Req 3.1 gives the reject rule; 3.2 just instantiates it). 10+3J/m/s/kpc2 and the cds.py / division_of_units names are already public in the problem_statement (legitimate localization; these are pre-existing source identifiers, not fix-invented names). No test names, file paths, parametrization ids, or verbatim test/gold code appear. Positive signal of independent derivation rather than copying the test diff: Req 4.3 cites 1.5x10+11m, which the test_patch actually REMOVES (replaced with 1.5x10+11/m); a leak transcribed from the test file would not cite the deleted case. The document translates what the tests check into requirements, which is the intended activity, and does not reconstruct the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
