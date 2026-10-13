# P2 adversarial audit — psf__requests-2931

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from requests.models import RequestEncodingMixin

# Req1.1 & Req1.3: bytes scalar returned unchanged (type + contents), not coerced.
b = u"ööö".encode("utf-8")
out = RequestEncodingMixin._encode_params(b)
print("in type", type(b), "out type", type(out), "out repr", repr(out))
ok = isinstance(out, bytes) and out == b
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from requests.models import RequestEncodingMixin

# Req1.2: str scalar returned unchanged (type + contents).
s = u"hello-world"
out = RequestEncodingMixin._encode_params(s)
print("out type", type(out), "out repr", repr(out))
ok = isinstance(out, str) and out == s
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import requests

# Req2: full prepare with non-ASCII bytes body -> body is bytes, equal, no exception.
body = u"ööö".encode("utf-8")
try:
    p = requests.Request("PUT", "http://example.com/", data=body).prepare()
except Exception as e:
    print("EXCEPTION during prepare:", repr(e))
    sys.exit(1)
print("body type", type(p.body), "body repr", repr(p.body))
ok = isinstance(p.body, bytes) and p.body == body
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import requests

# Req3.1 & 3.2: bytes/str params encoded into query identically.
pb = requests.Request("GET", "http://example.com/", params=b"a=1&b=2").prepare()
ps = requests.Request("GET", "http://example.com/", params="a=1&b=2").prepare()
print("bytes-params url", pb.url)
print("str-params   url", ps.url)
ok = pb.url == ps.url == "http://example.com/?a=1&b=2"
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import requests
from requests.models import RequestEncodingMixin

# Req3.3 & 3.4: dict / list-of-2-tuples still encoded; ordering preserved; params before fragment.
d = RequestEncodingMixin._encode_params([("a", "1"), ("b", "2")])
print("list encode:", repr(d))
ok_list = d == "a=1&b=2"

# fragment placement: query goes before fragment
p = requests.Request("GET", "http://example.com/path#frag", params={"x": "9"}).prepare()
print("frag url:", p.url)
ok_frag = p.url == "http://example.com/path?x=9#frag"

# Req4.2: scalar body does not set Content-Type via body encoding
pb = requests.Request("PUT", "http://example.com/", data=b"raw").prepare()
print("content-type header present:", "Content-Type" in pb.headers, pb.headers.get("Content-Type"))
ok_ct = "Content-Type" not in pb.headers

print("ok_list", ok_list, "ok_frag", ok_frag, "ok_ct", ok_ct)
sys.exit(0 if (ok_list and ok_frag and ok_ct) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
import sys
import requests

# Req2: full prepare with non-ASCII bytes body -> body is bytes, equal, no exception.
body = u"ööö".encode("utf-8")
try:
    p = requests.Request("PUT", "http://example.com/", data=body).prepare()
except Exception as e:
    print("EXCEPTION during prepare:", repr(e))
    sys.exit(1)
print("body type", type(p.body), "body repr", repr(p.body))
ok = isinstance(p.body, bytes) and p.body == body
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1 (_encode_params returns bytes/str unchanged, no ASCII decode - probe_1,2), Req2 (full prepare of non-ASCII bytes body -> bytes body, no exception - probe_3), Req3.1/3.2 (bytes & str params encode to identical query - probe_4), and Req3.3/3.4 + Req4.2 regression 'SHALL keep' criteria (list-of-2-tuples ordering, query-before-fragment, Content-Type unset for scalar body - probe_5). All 5 HOLD on gold-patched tree. Positive controls probe_1 and probe_3 FAIL at base with UnicodeDecodeError (ascii codec on 0xc3), confirming discriminating power; probe_4 HOLDS at base (params path unchanged by gold). Candidate patch 'body_only_missing_params_coercion' applies only the _encode_params fix and omits the prepare_url to_native_string(params) coercion: it PASSES body probes 1,3,5 but is REJECTED by probe_4 (bytes params -> TypeError 'Cannot mix str and non-str arguments' in urlunparse). This proves the requirement set (Req3.1 mandating bytes params still encode to native text) rules out the naive body-only fix, so the requirements are not too weak. No probe failed on the patched tree; suite discriminates a plausibly-wrong partial fix.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
import sys
import requests

# Req2: full prepare with non-ASCII bytes body -> body is bytes, equal, no exception.
body = u"ööö".encode("utf-8")
try:
    p = requests.Request("PUT", "http://example.com/", data=body).prepare()
except Exception as e:
    print("EXCEPTION during prepare:", repr(e))
    sys.exit(1)
print("body type", type(p.body), "body repr", repr(p.body))
ok = isinstance(p.body, bytes) and p.body == body
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1 (_encode_params returns bytes/str unchanged, no ASCII decode - probe_1,2), Req2 (full prepare of non-ASCII bytes body -> bytes body, no exception - probe_3), Req3.1/3.2 (bytes & str params encode to identical query - probe_4), and Req3.3/3.4 + Req4.2 regression 'SHALL keep' criteria (list-of-2-tuples ordering, query-before-fragment, Content-Type unset for scalar body - probe_5). All 5 HOLD on gold-patched tree. Positive controls probe_1 and probe_3 FAIL at base with UnicodeDecodeError (ascii codec on 0xc3), confirming discriminating power; probe_4 HOLDS at base (params path unchanged by gold). Candidate patch 'body_only_missing_params_coercion' applies only the _encode_params fix and omits the prepare_url to_native_string(params) coercion: it PASSES body probes 1,3,5 but is REJECTED by probe_4 (bytes params -> TypeError 'Cannot mix str and non-str arguments' in urlunparse). This proves the requirement set (Req3.1 mandating bytes params still encode to native text) rules out the naive body-only fix, so the requirements are not too weak. No probe failed on the patched tree; suite discriminates a plausibly-wrong partial fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirement 4.1 precisely captures the asymmetry the patch introduces: to_native_string is applied only on the params/URL path, never on the body path. Req 3.4 (fragment ordering, no double-encode) reflects pre-existing prepare_url behavior left untouched by the patch — consistent with the diff. No unfaithful mandates, forbidden behaviors, or invented behavior found.

Counterexample / evidence:

```
N/A — no diverging input exists; patched probe exits 0 on all four requirements, base exits 1 exactly where Req 1/2 predict.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to real pre-existing symbols (requests.models.PreparedRequest.prepare_body/prepare_url, RequestEncodingMixin._encode_params, to_native_string) — legitimate, not fix-invented. The u"ööö".encode("utf-8") example and the to_native_string regression are both drawn verbatim from the public problem_statement. Requirement 2 (prepared body must be bytes) restates the FAIL_TO_PASS test_binary_put's assertion behaviorally, and Requirement 3 restates PASS_TO_PASS test_params_bytes_are_encoded (b'test=foo' -> query) behaviorally — both are behavior descriptions, not transmissions of test code, test names/paths, parametrization ids, or gold-patch lines. No test-shaped case enumeration mirrors the parametrization. The gold edit (return data unchanged; to_native_string(params) in prepare_url) is described only as behavioral outcomes, not quoted. No leakage beyond the public problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
