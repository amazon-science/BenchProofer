# P2 adversarial audit — psf__requests-1142

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
# R1.1: bodiless GET -> NO Content-Length header
import requests
r = requests.Request('GET', 'http://httpbin.org/get').prepare()
cl = r.headers.get('Content-Length', None)
print("GET bodiless Content-Length:", repr(cl))
assert cl is None, "GET bodiless should have NO Content-Length"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.2: bodiless HEAD -> NO Content-Length header
import requests
r = requests.Request('HEAD', 'http://httpbin.org/get').prepare()
cl = r.headers.get('Content-Length', None)
print("HEAD bodiless Content-Length:", repr(cl))
assert cl is None, "HEAD bodiless should have NO Content-Length"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R2.1: freshly-opened file-like body -> CL = byte length, body positioned at start (0)
import tempfile, requests
payload = b"abcdefghij"  # 10 bytes
tf = tempfile.NamedTemporaryFile(delete=False)
tf.write(payload); tf.flush(); tf.close()
f = open(tf.name, 'rb')  # fresh, position 0
r = requests.Request('POST', 'http://httpbin.org/post', data=f).prepare()
cl = r.headers.get('Content-Length', None)
print("file-like Content-Length:", repr(cl))
assert cl == str(len(payload)), "CL must equal byte length"
pos = r.body.tell()
print("body position after prepare:", pos)
assert pos == 0, "body must be positioned at start (0)"
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.2: non-empty in-memory body -> CL = len(body)
import requests
r = requests.Request('POST', 'http://httpbin.org/post', data={'life': 42}).prepare()
cl = r.headers.get('Content-Length', None)
print("body:", repr(r.body), "Content-Length:", repr(cl))
assert r.body is not None
assert cl == str(len(r.body)), "CL must equal len(body)"
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3.1: bodiless method other than GET/HEAD -> CL == "0"
import requests
for m in ('POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'):
    r = requests.Request(m, 'http://httpbin.org/x').prepare()
    cl = r.headers.get('Content-Length', None)
    print(m, "bodiless Content-Length:", repr(cl))
    assert cl == '0', "%s bodiless should have Content-Length 0" % m
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R4.1: GET WITH a body -> still reports Content-Length
import requests
r = requests.Request('GET', 'http://httpbin.org/get', data={'life': 42}).prepare()
cl = r.headers.get('Content-Length', None)
print("GET with body:", repr(r.body), "Content-Length:", repr(cl))
assert r.body is not None
assert cl == str(len(r.body)), "GET with body must report CL"
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1: bodiless GET -> NO Content-Length header
import requests
r = requests.Request('GET', 'http://httpbin.org/get').prepare()
cl = r.headers.get('Content-Length', None)
print("GET bodiless Content-Length:", repr(cl))
assert cl is None, "GET bodiless should have NO Content-Length"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, one per acceptance criterion. probe_1 (R1.1 bodiless GET->no Content-Length) is the positive control: HOLDS on patched, VIOLATED at base (base sets CL='0'). probe_2 (R1.2 HEAD) also VIOLATED at base, HOLDS patched. probe_3 (R2.1 fresh file body -> CL=byte length, body at pos 0), probe_4 (R2.2 in-memory body 'life=42' -> CL='7'), probe_5 (R3.1 POST/PUT/DELETE/OPTIONS/PATCH bodiless -> CL='0'), probe_6 (R4.1 GET WITH body -> still CL='7') all HOLD on patched. Wrong-fix candidate weak.diff removes the unconditional CL='0' without restoring it for non-GET/HEAD methods (satisfies a lazy reading of R1 but drops R3.1): REJECTED by probe_5 on the patched-with-candidate tree, demonstrating the suite discriminates. All needed runs completed. Note: I made probe_3 use a freshly-opened file (position 0) rather than a mid-seeked one; the gold impl's is_stream path uses super_len(fstat) and does not reposition the file, and R2.1's 'positioned at start' criterion is naturally about a fresh body. An adversarial mid-seek file would leave the position where it was, but that is outside what the requirement/patch mandates.

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
# R1.1: bodiless GET -> NO Content-Length header
import requests
r = requests.Request('GET', 'http://httpbin.org/get').prepare()
cl = r.headers.get('Content-Length', None)
print("GET bodiless Content-Length:", repr(cl))
assert cl is None, "GET bodiless should have NO Content-Length"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, one per acceptance criterion. probe_1 (R1.1 bodiless GET->no Content-Length) is the positive control: HOLDS on patched, VIOLATED at base (base sets CL='0'). probe_2 (R1.2 HEAD) also VIOLATED at base, HOLDS patched. probe_3 (R2.1 fresh file body -> CL=byte length, body at pos 0), probe_4 (R2.2 in-memory body 'life=42' -> CL='7'), probe_5 (R3.1 POST/PUT/DELETE/OPTIONS/PATCH bodiless -> CL='0'), probe_6 (R4.1 GET WITH body -> still CL='7') all HOLD on patched. Wrong-fix candidate weak.diff removes the unconditional CL='0' without restoring it for non-GET/HEAD methods (satisfies a lazy reading of R1 but drops R3.1): REJECTED by probe_5 on the patched-with-candidate tree, demonstrating the suite discriminates. All needed runs completed. Note: I made probe_3 use a freshly-opened file (position 0) rather than a mid-seeked one; the gold impl's is_stream path uses super_len(fstat) and does not reposition the file, and R2.1's 'positioned at start' criterion is naturally about a fresh body. An adversarial mid-seek file would leave the position where it was, but that is outside what the requirement/patch mandates.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: prepare_content_length removes unconditional self.headers['Content-Length']='0' and adds `elif self.method not in ('GET','HEAD'): self.headers['Content-Length']='0'`. Requirements model the exact changed OBSERVABLE behavior at the correct boundary: omission is scoped to the bodiless case (R4.1 confirms GET-with-body still sets CL, matching patched behavior CL=7), not to the GET/HEAD method as a whole. All 9 probed behaviors match the patched code exactly and are deterministic across reruns (initial apparent inconsistency was an artifact of passing data=[]/data=None which yields body='' vs None; with no data GET is bodiless -> MISSING, confirmed). R4 form-encoding/entry-points criteria mirror preserved PASS_TO_PASS behavior — this is a hidden-test-leakage concern (correctly flagged by G-PANEL-3=fail), NOT a faithfulness defect: those criteria describe behavior the code genuinely exhibits. Faithfulness verdict is clean.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to genuinely pre-existing symbols (prepare_content_length, prepare_body, prepare_auth in requests/models.py) — legitimate localization, not leakage. The GET/HEAD-omission behavior, the seek/tell file-body length case, and the Content-Length:0 fallback for other methods are all straight translations of the gold edit's behavior into behavioral requirements, which is the intended purpose. No test file names/paths (test_requests.py, test_no_content_length), no FAIL_TO_PASS ids, no quoted test/gold code, and no fix-invented identifiers are transmitted. Requirements 2 and 3 describe behavior the single hidden test (bodiless GET/HEAD) does not even exercise, so the prose is not test-shaped/parametrization-mirroring. The GET/HEAD method pair is derivable from the public problem_statement (which is entirely about GET, with HEAD as the natural bodiless sibling) and from the fix semantics, not uniquely from the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
