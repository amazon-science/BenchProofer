# P2 adversarial audit — psf__requests-1921

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

Counterexample / evidence:

```
Weak candidate 'truthiness_filter' replaces `if v is not None` with `if v`. It suppresses None (satisfying probes 1,2,4) but ALSO drops empty-string/0/False values. probe_3 (Req1.5) REJECTS it: merged becomes {} for session {'empty':'','zero':0,'false':False,'gone':None}, proving the suite discriminates the wrong reading of Req1.5.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.2 (positive control): session maps key to None, per-request lacks it -> key omitted.
# This is the core fixed behavior: FAILS at base, HOLDS patched.
import sys
from requests.sessions import merge_setting

session = {'Accept-Encoding': None, 'Keep-Alive': 'yes'}
request = {}
merged = merge_setting(request, session)
print("merged:", dict(merged))
if 'Accept-Encoding' in merged:
    print("FAIL: session-provided None survived merge:", merged.get('Accept-Encoding'))
    sys.exit(1)
if merged.get('Keep-Alive') != 'yes':
    print("FAIL: non-null session value lost")
    sys.exit(1)
print("OK: session None key omitted")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1 & 1.3: no key in merged has value None, regardless of source.
# per-request None also suppresses (already worked at base), session None too.
import sys
from requests.sessions import merge_setting

session = {'A': 'sv', 'B': None, 'C': 'cv'}
request = {'A': None, 'D': 'dv'}
merged = merge_setting(request, session)
print("merged:", dict(merged))
none_vals = [k for k, v in merged.items() if v is None]
if none_vals:
    print("FAIL: keys with None survived:", none_vals)
    sys.exit(1)
# A suppressed by per-request None, B suppressed by session None
if 'A' in merged or 'B' in merged:
    print("FAIL: expected A and B suppressed")
    sys.exit(1)
if merged.get('C') != 'cv' or merged.get('D') != 'dv':
    print("FAIL: surviving values wrong")
    sys.exit(1)
print("OK: no null entries, correct suppression")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.5: suppress ONLY exactly None. Empty string, 0, False must survive.
import sys
from requests.sessions import merge_setting

session = {'empty': '', 'zero': 0, 'false': False, 'gone': None}
request = {}
merged = merge_setting(request, session)
print("merged:", dict(merged))
for k, expected in [('empty', ''), ('zero', 0), ('false', False)]:
    if k not in merged:
        print("FAIL: non-None falsy key wrongly removed:", k)
        sys.exit(1)
    if merged[k] != expected:
        print("FAIL: value changed for", k, merged[k])
        sys.exit(1)
if 'gone' in merged:
    print("FAIL: None key survived")
    sys.exit(1)
print("OK: only exact None suppressed; falsy non-None preserved")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req1.4 + Req4.1: end-to-end prepared request. Session default header None -> absent;
# ordinary session header -> present unchanged.
import sys
import requests

s = requests.Session()
s.headers['Accept-Encoding'] = None
s.headers['X-Keep'] = 'stay'
req = requests.Request('GET', 'http://example.com/')
prepped = s.prepare_request(req)
print("prepared headers:", dict(prepped.headers))
if 'Accept-Encoding' in prepped.headers:
    print("FAIL: Accept-Encoding present:", prepped.headers.get('Accept-Encoding'))
    sys.exit(1)
if prepped.headers.get('X-Keep') != 'stay':
    print("FAIL: ordinary header missing/changed")
    sys.exit(1)
print("OK: None default header omitted; ordinary header kept")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2: override + ordering preserved; inputs unmodified.
import sys
from collections import OrderedDict
from requests.sessions import merge_setting

session = OrderedDict([('a', '1'), ('b', '2'), ('c', '3')])
request = OrderedDict([('b', 'override'), ('d', '4')])
sess_copy = dict(session)
req_copy = dict(request)
merged = merge_setting(request, session)
print("merged:", list(merged.items()))
# Req2.1 override
if merged.get('b') != 'override':
    print("FAIL: per-request override not applied")
    sys.exit(1)
# Req2.2 / 2.3 presence
if merged.get('a') != '1' or merged.get('c') != '3' or merged.get('d') != '4':
    print("FAIL: values wrong")
    sys.exit(1)
# Req2.4 ordering: session keys keep order (a,b,c), b keeps its slot, d appended
keys = list(merged.keys())
if keys != ['a', 'b', 'c', 'd']:
    print("FAIL: ordering wrong:", keys)
    sys.exit(1)
# Req2.5 inputs unmodified
if dict(session) != sess_copy or dict(request) != req_copy:
    print("FAIL: input mappings mutated")
    sys.exit(1)
print("OK: override, ordering, immutability preserved")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3: early-return / non-mapping bypass branches intact.
import sys
from requests.sessions import merge_setting

# Req3.1 session None -> return request unchanged
r = merge_setting({'x': 1}, None)
if r != {'x': 1}:
    print("FAIL 3.1:", r); sys.exit(1)
# Req3.2 request None -> return session unchanged
r = merge_setting(None, {'y': 2})
if r != {'y': 2}:
    print("FAIL 3.2:", r); sys.exit(1)
# 3.2 with session None value present should be returned unchanged (still None in it)
r = merge_setting(None, {'y': None})
if r != {'y': None}:
    print("FAIL 3.2 null preserved on bypass:", r); sys.exit(1)
# Req3.3 non-dict operand (scalar verify flag) -> return request unchanged
r = merge_setting(True, False)
if r is not True:
    print("FAIL 3.3 scalar:", r); sys.exit(1)
r = merge_setting(False, True)
if r is not False:
    print("FAIL 3.3 scalar2:", r); sys.exit(1)
print("OK: early-return and bypass branches intact")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.2 (positive control): session maps key to None, per-request lacks it -> key omitted.
# This is the core fixed behavior: FAILS at base, HOLDS patched.
import sys
from requests.sessions import merge_setting

session = {'Accept-Encoding': None, 'Keep-Alive': 'yes'}
request = {}
merged = merge_setting(request, session)
print("merged:", dict(merged))
if 'Accept-Encoding' in merged:
    print("FAIL: session-provided None survived merge:", merged.get('Accept-Encoding'))
    sys.exit(1)
if merged.get('Keep-Alive') != 'yes':
    print("FAIL: non-null session value lost")
    sys.exit(1)
print("OK: session None key omitted")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all requirements. probe_1 = positive control (Req1.2): session-None key omitted — HOLDS patched, FAILS at base (Accept-Encoding:None survives). probe_2 (Req1.1/1.3): no null entries regardless of source. probe_3 (Req1.5): ONLY exact None suppressed; ''/0/False preserved. probe_4 (Req1.4/4.1): end-to-end prepare_request — None default header absent, ordinary header kept; FAILS at base. probe_5 (Req2.1-2.5): override, ordering [a,b,c,d], input immutability. probe_6 (Req3.1-3.3): early-return (session None -> request; request None -> session, incl. None value preserved on bypass) and non-dict scalar bypass. All 6 HOLD patched; probes 1,2,3,4 FAIL at base (control discriminates). Weak candidate rejected by probe_3, confirming discrimination; no requirements-conforming patch found that fails the hidden tests.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate 'truthiness_filter' replaces `if v is not None` with `if v`. It suppresses None (satisfying probes 1,2,4) but ALSO drops empty-string/0/False values. probe_3 (Req1.5) REJECTS it: merged becomes {} for session {'empty':'','zero':0,'false':False,'gone':None}, proving the suite discriminates the wrong reading of Req1.5.
```

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
# Req1.2 (positive control): session maps key to None, per-request lacks it -> key omitted.
# This is the core fixed behavior: FAILS at base, HOLDS patched.
import sys
from requests.sessions import merge_setting

session = {'Accept-Encoding': None, 'Keep-Alive': 'yes'}
request = {}
merged = merge_setting(request, session)
print("merged:", dict(merged))
if 'Accept-Encoding' in merged:
    print("FAIL: session-provided None survived merge:", merged.get('Accept-Encoding'))
    sys.exit(1)
if merged.get('Keep-Alive') != 'yes':
    print("FAIL: non-null session value lost")
    sys.exit(1)
print("OK: session None key omitted")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all requirements. probe_1 = positive control (Req1.2): session-None key omitted — HOLDS patched, FAILS at base (Accept-Encoding:None survives). probe_2 (Req1.1/1.3): no null entries regardless of source. probe_3 (Req1.5): ONLY exact None suppressed; ''/0/False preserved. probe_4 (Req1.4/4.1): end-to-end prepare_request — None default header absent, ordinary header kept; FAILS at base. probe_5 (Req2.1-2.5): override, ordering [a,b,c,d], input immutability. probe_6 (Req3.1-3.3): early-return (session None -> request; request None -> session, incl. None value preserved on bypass) and non-dict scalar bypass. All 6 HOLD patched; probes 1,2,3,4 FAIL at base (control discriminates). Weak candidate rejected by probe_3, confirming discrimination; no requirements-conforming patch found that fails the hidden tests.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: `merged_setting = dict((k,v) for (k,v) in merged_setting.items() if v is not None)` appended before return. Probed on patched py3.9 image:
- Req1: None from session side suppressed (Accept-Encoding omitted, session None-> [('X',5)]); None from request side suppressed; prepared request omits Accept-Encoding header set to None; '', 0, False preserved (falsy non-None kept). HOLDS.
- Req2.1-2.4: per-request override wins; session-only/request-only non-null retained; ordering [s1, s2(20), s3, r1] preserved (session order kept, override in place, new request key appended). HOLDS.
- Req2.5: returned obj is fresh (r is not sess/req), inputs unmodified, type is plain dict — spec explicitly allows type not matching dict_class. HOLDS.
- Req3.1-3.4: session None -> returns request; request None -> returns session; scalar/non-Mapping operands bypass to request_setting (True/False cases). HOLDS.
- Req4: ordinary headers preserved; merge applied consistently to dict settings; unrelated behaviors untouched by the one-line patch. HOLDS.
Boundary is correct: spec pins the observable None-suppression behavior of merge_setting (both operand sides + prepared-request effect), not a narrow single branch. Modeling boundary matches the changed behavior. Verdict FAITHFUL.

Counterexample / evidence:

```
The earlier failing G-EQ/G-PANEL-1/G-PANEL-2 stamps (07:44) cited probe_8_type_dictclass asserting type(r)==dict_class(OrderedDict/MyDict). That probe encodes a requirement the CURRENT spec does not make; Req 2.5 was revised to disclaim the container-type guarantee. So no live requirement disagrees with the code.
```

- Req1: None from session side suppressed (Accept-Encoding omitted, session None-> [('X',5)]); None from request side suppressed; prepared request omits Accept-Encoding header set to None; '', 0, False preserved (falsy non-None kept). HOLDS.
- Req2.1-2.4: per-request override wins; session-only/request-only non-null retained; ordering [s1, s2(20), s3, r1] preserved (session order kept, override in place, new request key appended). HOLDS.
- Req2.5: returned obj is fresh (r is not sess/req), inputs unmodified, type is plain dict — spec explicitly allows type not matching dict_class. HOLDS.
- Req3.1-3.4: session None -> returns request; request None -> returns session; scalar/non-Mapping operands bypass to request_setting (True/False cases). HOLDS.
- Req4: ordinary headers preserved; merge applied consistently to dict settings; unrelated behaviors untouched by the one-line patch. HOLDS.
Boundary is correct: spec pins the observable None-suppression behavior of merge_setting (both operand sides + prepared-request effect), not a narrow single branch. Modeling boundary matches the changed behavior. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to merge_setting(request_setting, session_setting, dict_class=OrderedDict) in requests/sessions.py — this is the pre-existing public source signature, legitimate localization, not gold-invented. The core scenario (session.headers['Accept-Encoding']=None sent as literal 'None', del workaround) comes verbatim from the public problem_statement, so Req 1.4 is public. Reqs 1-3 are behavioral translations of the null-suppression fix (the intended purpose of the doc), not quoted gold code — the gold line `dict((k,v) ... if v is not None)` is described behaviorally, not reproduced, and introduces no fix-invented identifiers. The hidden test name (test_headers_on_session_with_None_are_not_sent) and file (test_requests.py) do not appear. Req 4's mention of cookies/redirects/auth is generic regression-safety prose, too coarse to reconstruct the FAIL_TO_PASS/PASS_TO_PASS test list (those extra FAIL_TO_PASS entries are live-internet drift artifacts, not fix behavior). Req 2.5's note that the returned container type is not guaranteed to match dict_class is a behavioral consequence of the fix, not a test/gold leak. No test paths, ids, parametrization enumerations, or verbatim gold lines transmitted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
