# P2 adversarial audit — psf__requests-6028

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
"""R1.1 + positive control: full userinfo (user:pass) preserved; scheme'd input round-trips identically."""
import sys
from requests.utils import prepend_scheme_if_needed
url = "http://user:pass@proxy.example"
out = prepend_scheme_if_needed(url, "http")
print("in :", url)
print("out:", out)
ok = out == url
print("identical round-trip:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2: username-only userinfo (no password) preserved; scheme'd input round-trips."""
import sys
from requests.utils import prepend_scheme_if_needed
url = "http://user@proxy.example"
out = prepend_scheme_if_needed(url, "http")
print("in :", url)
print("out:", out)
ok = out == url and "user@proxy.example" in out
print("username preserved & identical:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.3 + R3.2: parsed userinfo joined with single @, port retained -> authority reads userinfo@host:port.
Uses a '//'-prefixed scheme-less input so the parser actually extracts an auth component and a default scheme is added."""
import sys
from requests.utils import prepend_scheme_if_needed
# scheme'd input with userinfo+port -> faithful round-trip
u1 = "http://user:pass@proxy.example:8080"
o1 = prepend_scheme_if_needed(u1, "https")
print("u1 ->", o1)
ok1 = o1 == u1 and o1.count("@") == 1 and ":8080" in o1

# '//'-prefixed scheme-less with userinfo+port -> default scheme prepended, single @, port retained
u2 = "//user:pass@proxy.example:8080"
o2 = prepend_scheme_if_needed(u2, "http")
print("u2 ->", o2)
ok2 = o2 == "http://user:pass@proxy.example:8080" and o2.count("@") == 1

print("ok1,ok2:", ok1, ok2)
sys.exit(0 if (ok1 and ok2) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.4 + R2.2 + R3: no userinfo => no spurious @; existing scheme kept; host/port/path/query/fragment preserved."""
import sys
from requests.utils import prepend_scheme_if_needed
fails = []

# no userinfo, has scheme -> unchanged, no spurious @
u1 = "http://proxy.example:8080/pa%20th?q=1&x=2#frag"
o1 = prepend_scheme_if_needed(u1, "https")
print("u1 ->", o1)
if o1 != u1: fails.append(("u1 unchanged", o1))
if "@" in o1: fails.append(("u1 spurious @", o1))

# existing scheme kept, not replaced with new_scheme
u2 = "https://proxy.example"
o2 = prepend_scheme_if_needed(u2, "http")
print("u2 ->", o2)
if not o2.startswith("https://"): fails.append(("u2 scheme replaced", o2))

# query & fragment & port preserved on scheme'd input
if "?q=1&x=2" not in o1: fails.append(("query lost", o1))
if o1 and not o1.endswith("#frag"): fails.append(("fragment lost", o1))
if ":8080" not in o1: fails.append(("port lost", o1))

print("fails:", fails)
sys.exit(0 if not fails else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R2.1 + R4: scheme-less host-only input gets default scheme with host in authority (no spurious @)."""
import sys
from requests.utils import prepend_scheme_if_needed
fails = []

# scheme-less host-only (parser reports empty authority -> path treated as authority)
u1 = "proxy.example"
o1 = prepend_scheme_if_needed(u1, "http")
print("u1 ->", o1)
if o1 != "http://proxy.example": fails.append(("u1", o1))

# scheme-less host-only, no userinfo => must NOT add spurious @
if "@" in o1: fails.append(("u1 spurious @", o1))

# // followed by host => default scheme prepended, host in authority
u2 = "//proxy.example"
o2 = prepend_scheme_if_needed(u2, "http")
print("u2 ->", o2)
if o2 != "http://proxy.example": fails.append(("u2", o2))
if "@" in o2: fails.append(("u2 spurious @", o2))

print("fails:", fails)
sys.exit(0 if not fails else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 + positive control: full userinfo (user:pass) preserved; scheme'd input round-trips identically."""
import sys
from requests.utils import prepend_scheme_if_needed
url = "http://user:pass@proxy.example"
out = prepend_scheme_if_needed(url, "http")
print("in :", url)
print("out:", out)
ok = out == url
print("identical round-trip:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

prepend_scheme_if_needed must re-attach parsed userinfo to the reassembled netloc.

Probe->requirement mapping and results (patched / base):
- probe_1 (R1.1 + POSITIVE CONTROL): 'http://user:pass@proxy.example' round-trips identically. HOLDS patched / VIOLATED base (base drops creds -> 'http://proxy.example'). Discriminates.
- probe_2 (R1.2): username-only 'http://user@proxy.example' preserved & identical. HOLDS patched / VIOLATED base.
- probe_3 (R1.3 + R3.2): scheme'd userinfo+port faithful round-trip; '//user:pass@proxy.example:8080' -> 'http://user:pass@proxy.example:8080', single '@', port retained. HOLDS patched / VIOLATED base.
- probe_4 (R1.4 + R2.2 + R3.1/3/4 + R3.2): no-userinfo scheme'd URL unchanged (no spurious '@'); existing scheme kept not replaced; query/fragment/port preserved. HOLDS both trees (regression criterion).
- probe_5 (R2.1 + R4.1/4.2): scheme-less host-only 'proxy.example' and '//proxy.example' both -> 'http://proxy.example', no spurious '@'. HOLDS both trees (regression criterion).

All 5 hold on the gold-patched tree. Positive control (probe_1) fails at base and holds patched -> discriminating power confirmed.

Weak candidate 'weak.diff' (naive fix: only re-attach userinfo when a password is present, `if auth and ':' in auth`). It resolves the headline user:pass case (probe_1,3 HOLD) but REJECTED by probe_2 (username-only, R1.2 requires preservation) -> the suite discriminates this too-weak reading. No requirements-conforming alternative found that would fail hidden tests.

Note: an earlier over-strong draft of probe_3 used scheme-less 'user:pass@host' which the urllib3 parser reads with 'user' as the scheme (path='/pass@...'), so no userinfo is extracted and gold correctly does not re-attach; corrected to a '//'-prefixed input that actually exercises the auth path. This confirms the requirements' userinfo criteria only bind when the parser yields an auth component.

Verdict: SOUND. >=5 probes hold on patched, positive control discriminates base vs patched, >=1 wrong-fix candidate exercised and rejected.

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
"""R1.1 + positive control: full userinfo (user:pass) preserved; scheme'd input round-trips identically."""
import sys
from requests.utils import prepend_scheme_if_needed
url = "http://user:pass@proxy.example"
out = prepend_scheme_if_needed(url, "http")
print("in :", url)
print("out:", out)
ok = out == url
print("identical round-trip:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

prepend_scheme_if_needed must re-attach parsed userinfo to the reassembled netloc.

Probe->requirement mapping and results (patched / base):
- probe_1 (R1.1 + POSITIVE CONTROL): 'http://user:pass@proxy.example' round-trips identically. HOLDS patched / VIOLATED base (base drops creds -> 'http://proxy.example'). Discriminates.
- probe_2 (R1.2): username-only 'http://user@proxy.example' preserved & identical. HOLDS patched / VIOLATED base.
- probe_3 (R1.3 + R3.2): scheme'd userinfo+port faithful round-trip; '//user:pass@proxy.example:8080' -> 'http://user:pass@proxy.example:8080', single '@', port retained. HOLDS patched / VIOLATED base.
- probe_4 (R1.4 + R2.2 + R3.1/3/4 + R3.2): no-userinfo scheme'd URL unchanged (no spurious '@'); existing scheme kept not replaced; query/fragment/port preserved. HOLDS both trees (regression criterion).
- probe_5 (R2.1 + R4.1/4.2): scheme-less host-only 'proxy.example' and '//proxy.example' both -> 'http://proxy.example', no spurious '@'. HOLDS both trees (regression criterion).

All 5 hold on the gold-patched tree. Positive control (probe_1) fails at base and holds patched -> discriminating power confirmed.

Weak candidate 'weak.diff' (naive fix: only re-attach userinfo when a password is present, `if auth and ':' in auth`). It resolves the headline user:pass case (probe_1,3 HOLD) but REJECTED by probe_2 (username-only, R1.2 requires preservation) -> the suite discriminates this too-weak reading. No requirements-conforming alternative found that would fail hidden tests.

Note: an earlier over-strong draft of probe_3 used scheme-less 'user:pass@host' which the urllib3 parser reads with 'user' as the scheme (path='/pass@...'), so no userinfo is extracted and gold correctly does not re-attach; corrected to a '//'-prefixed input that actually exercises the auth path. This confirms the requirements' userinfo criteria only bind when the parser yields an auth component.

Verdict: SOUND. >=5 probes hold on patched, positive control discriminates base vs patched, >=1 wrong-fix candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Focus is faithfulness (G-PANEL-2 role); leakage concerns (G-PANEL-3 fail) are out of scope for this verdict. Function source confirmed in checkout: patch adds userinfo re-join. All 4 requirements / 14 criteria verified observably against the patched tree. Verdict FAITHFUL.

Counterexample / evidence:

```
None applicable. (Note: scheme-less userinfo input 'user:pass@proxy.example' produces the odd 'user:///pass@proxy.example', but no requirement claims a round-trip or specific output for scheme-less userinfo inputs — Req1.1/1.2 scope the identity claim explicitly to inputs that already carry a scheme — so this is not a divergence from the requirements.)
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the userinfo-preservation behavior and localize the change to requests.utils.prepend_scheme_if_needed (legitimate). The two acceptance criteria splitting username:password vs username-only mirror the two hidden test cases in count, but this is the natural, standard decomposition of URL userinfo syntax, not a test-shaped over-enumeration. Example URLs used (proxy.example, generic user:pass@host) differ from the hidden test's concrete example.com/path?query fixtures. No test file paths, function/class names, parametrization ids, verbatim gold-patch lines ('@'.join([auth, netloc])), or fix-invented identifiers are quoted. The description of joining userinfo with a single '@' is a behavioral translation of the fix, which is the intended purpose of the spec, not a transmission of the test/gold code itself.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
