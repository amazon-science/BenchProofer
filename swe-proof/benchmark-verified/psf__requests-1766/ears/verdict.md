# P2 adversarial audit — psf__requests-1766

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import requests.auth as a
auth = a.HTTPDigestAuth('user', 'pass')
auth.chal = {'realm': 'me@host', 'nonce': 'abc123', 'qop': 'auth'}
hdr = auth.build_digest_header('GET', 'http://host/path')
print("HEADER:", hdr)
assert hdr is not None, "header is None"
assert 'qop="auth"' in hdr, 'expected qop="auth" quoted form'
assert 'qop=auth,' not in hdr, 'bare token qop=auth present'
print("OK: qop value double-quoted")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import requests.auth as a
auth = a.HTTPDigestAuth('user', 'pass')
auth.chal = {'realm': 'r', 'nonce': 'n', 'qop': 'auth'}
hdr = auth.build_digest_header('GET', 'http://host/p')
print("HEADER:", hdr)
assert '"auth"' in hdr, 'quoted "auth" substring missing'
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import re, requests.auth as a
# with qop present: order qop, nc, cnonce
auth = a.HTTPDigestAuth('u', 'p')
auth.chal = {'realm': 'r', 'nonce': 'n', 'qop': 'auth'}
hdr = auth.build_digest_header('GET', 'http://h/p')
print("WITH QOP:", hdr)
m = re.search(r'qop="auth",\s*nc=([0-9a-f]{8}),\s*cnonce="[^"]*"', hdr)
assert m, 'qop,nc,cnonce group not in required order/format'
# no qop -> group omitted
auth2 = a.HTTPDigestAuth('u', 'p')
auth2.chal = {'realm': 'r', 'nonce': 'n'}
hdr2 = auth2.build_digest_header('GET', 'http://h/p')
print("NO QOP:", hdr2)
assert 'qop' not in hdr2 and 'nc=' not in hdr2 and 'cnonce' not in hdr2, 'qop group not omitted when no qop'
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import re, requests.auth as a
auth = a.HTTPDigestAuth('bob', 'secret')
auth.chal = {'realm': 'testrealm', 'nonce': 'deadbeef', 'qop': 'auth'}
hdr = auth.build_digest_header('GET', 'http://h/dir/index.html')
print("HEADER:", hdr)
assert hdr.startswith('Digest '), 'missing Digest prefix'
body = hdr[len('Digest '):]
# mandatory directives in order, each double-quoted
pat = (r'^username="bob", realm="testrealm", nonce="deadbeef", '
       r'uri="/dir/index\.html", response="[0-9a-f]+"')
assert re.match(pat, body), 'mandatory directive order/quoting wrong: '+body
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import re, requests.auth as a
auth = a.HTTPDigestAuth('u', 'p')
auth.chal = {'realm': 'r', 'nonce': 'n', 'qop': 'auth'}
hdr = auth.build_digest_header('GET', 'http://h/p')
print("HEADER:", hdr)
# nc bare (no quotes), cnonce quoted
assert re.search(r'nc=[0-9a-f]{8}(,|$)', hdr), 'nc not bare token'
assert not re.search(r'nc="', hdr), 'nc must not be quoted'
assert re.search(r'cnonce="[^"]+"', hdr), 'cnonce not quoted'
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import requests.auth as a
# supplied
auth = a.HTTPDigestAuth('u', 'p')
auth.chal = {'realm': 'r', 'nonce': 'n', 'qop': 'auth', 'opaque': 'OPQ', 'algorithm': 'MD5'}
hdr = auth.build_digest_header('GET', 'http://h/p')
print("WITH:", hdr)
assert 'opaque="OPQ"' in hdr, 'opaque not quoted/present'
assert 'algorithm="MD5"' in hdr, 'algorithm not quoted/present'
# omitted
auth2 = a.HTTPDigestAuth('u', 'p')
auth2.chal = {'realm': 'r', 'nonce': 'n', 'qop': 'auth'}
hdr2 = auth2.build_digest_header('GET', 'http://h/p')
print("WITHOUT:", hdr2)
assert 'opaque' not in hdr2, 'opaque should be omitted'
assert 'algorithm' not in hdr2, 'algorithm should be omitted'
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import requests.auth as a
auth = a.HTTPDigestAuth('user', 'pass')
auth.chal = {'realm': 'me@host', 'nonce': 'abc123', 'qop': 'auth'}
hdr = auth.build_digest_header('GET', 'http://host/path')
print("HEADER:", hdr)
assert hdr is not None, "header is None"
assert 'qop="auth"' in hdr, 'expected qop="auth" quoted form'
assert 'qop=auth,' not in hdr, 'bare token qop=auth present'
print("OK: qop value double-quoted")
```

Prepatch bug re-encoded as an attack: `True`.

psf__requests-1766: gold change is one line `qop=auth` -> `qop="auth"` in requests/auth.py build_digest_header. 6 probes cover the requirements:
- probe_1 (Req1.1, POSITIVE CONTROL): qop value emitted as qop="auth" (double-quoted, no bare qop=auth). HOLDS patched, FAILS at base (AssertionError expected qop="auth") => discriminating.
- probe_2 (Req1.2): header contains substring "auth" quoted. HOLDS patched.
- probe_3 (Req1.3): qop group is exactly qop,nc,cnonce in that order, and the whole group is omitted when no qop challenge. HOLDS.
- probe_4 (Req2.1/2.2): `Digest ` prefix + mandatory directives username,realm,nonce,uri,response in order each double-quoted. HOLDS.
- probe_5 (Req2.6): nc bare token (unquoted), cnonce double-quoted. HOLDS patched.
- probe_6 (Req2.3/2.4): opaque and algorithm quoted when supplied, omitted otherwise. HOLDS.

Weak candidate `cnonce_unquoted` (weak.diff): quotes qop correctly BUT drops the quotes on cnonce (`cnonce=%s`). It's a requirements-non-conforming wrong fix that a lazy reading might permit. probe_1 (qop) still HOLDS under it, but probe_5 REJECTS it (cnonce not quoted) => the suite discriminates wrong implementations; this is not a too-weak finding.

All 6 probes HOLD on the gold-patched tree; positive control FAILS at base and HOLDS patched. No violation found; the requirement suite is neither too strong (no mandated behavior the gold lacks) nor demonstrably too weak (the one alternative patch tried is rejected by the suite). Verdict SOUND.

Note: bundle meta records G-PANEL-3 (leakage) fail — Req3 enumerates unrelated PASS_TO_PASS behaviors (cookies-on-redirect, content-type, case-sensitive param merge) traceable only to hidden tests. That is a leakage concern, orthogonal to G-EQ spec-fidelity, which is the gate under audit here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import requests.auth as a
auth = a.HTTPDigestAuth('user', 'pass')
auth.chal = {'realm': 'me@host', 'nonce': 'abc123', 'qop': 'auth'}
hdr = auth.build_digest_header('GET', 'http://host/path')
print("HEADER:", hdr)
assert hdr is not None, "header is None"
assert 'qop="auth"' in hdr, 'expected qop="auth" quoted form'
assert 'qop=auth,' not in hdr, 'bare token qop=auth present'
print("OK: qop value double-quoted")
```

Prepatch bug re-encoded as an attack: `True`.

psf__requests-1766: gold change is one line `qop=auth` -> `qop="auth"` in requests/auth.py build_digest_header. 6 probes cover the requirements:
- probe_1 (Req1.1, POSITIVE CONTROL): qop value emitted as qop="auth" (double-quoted, no bare qop=auth). HOLDS patched, FAILS at base (AssertionError expected qop="auth") => discriminating.
- probe_2 (Req1.2): header contains substring "auth" quoted. HOLDS patched.
- probe_3 (Req1.3): qop group is exactly qop,nc,cnonce in that order, and the whole group is omitted when no qop challenge. HOLDS.
- probe_4 (Req2.1/2.2): `Digest ` prefix + mandatory directives username,realm,nonce,uri,response in order each double-quoted. HOLDS.
- probe_5 (Req2.6): nc bare token (unquoted), cnonce double-quoted. HOLDS patched.
- probe_6 (Req2.3/2.4): opaque and algorithm quoted when supplied, omitted otherwise. HOLDS.

Weak candidate `cnonce_unquoted` (weak.diff): quotes qop correctly BUT drops the quotes on cnonce (`cnonce=%s`). It's a requirements-non-conforming wrong fix that a lazy reading might permit. probe_1 (qop) still HOLDS under it, but probe_5 REJECTS it (cnonce not quoted) => the suite discriminates wrong implementations; this is not a too-weak finding.

All 6 probes HOLD on the gold-patched tree; positive control FAILS at base and HOLDS patched. No violation found; the requirement suite is neither too strong (no mandated behavior the gold lacks) nor demonstrably too weak (the one alternative patch tried is rejected by the suite). Verdict SOUND.

Note: bundle meta records G-PANEL-3 (leakage) fail — Req3 enumerates unrelated PASS_TO_PASS behaviors (cookies-on-redirect, content-type, case-sensitive param merge) traceable only to hidden tests. That is a leakage concern, orthogonal to G-EQ spec-fidelity, which is the gate under audit here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base probe VIOLATED (qop=auth unquoted), patched probe HOLDS with all assertions passing. Requirements precisely and correctly model the qop-quoting change with no over/under-specification. FAIL_TO_PASS test_DIGESTAUTH_QUOTES_QOP_VALUE aligns with R1.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes build_digest_header behavior derived from the public problem_statement (RFC 2617 qop quoting, value "auth", curl parity) and the public source module requests/auth.py. Req 1.2 restates that the Authorization header contains the substring "auth"; while this parallels the hidden test's assertion, the value "auth" and the quoting requirement are both public (RFC value quoted in problem_statement; gold edit emits qop="auth"), so it is a behavioral restatement, not test transmission. Directive ordering/quoting enumeration reflects the actual source function (which the test does not check). No test names/paths (test_DIGESTAUTH_QUOTES_QOP_VALUE), no httpbin('digest-auth',...) call shape, no quoted test/gold code, no fix-invented identifiers.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
