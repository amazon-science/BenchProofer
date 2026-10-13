# P2 adversarial audit — psf__requests-5414

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
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL

# Req1.1 + 1.2 + 1.3 (positive control): host beginning with a dot must raise
# InvalidURL with message 'URL has an invalid label.' and NOT leak a UnicodeError.
pr = PreparedRequest()
try:
    pr.prepare_url("http://.example.com", None)
    print("NO EXCEPTION raised for http://.example.com")
    sys.exit(1)
except InvalidURL as e:
    print("InvalidURL raised:", repr(str(e)))
    if "URL has an invalid label." in str(e):
        sys.exit(0)
    print("wrong message")
    sys.exit(1)
except Exception as e:
    print("WRONG exception type:", type(e).__name__, repr(str(e)))
    sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL

# Req2.1: host beginning with wildcard '*' must keep raising InvalidURL
# with message 'URL has an invalid label.'
pr = PreparedRequest()
try:
    pr.prepare_url("http://*.example.com", None)
    print("NO EXCEPTION for http://*.example.com")
    sys.exit(1)
except InvalidURL as e:
    print("InvalidURL raised:", repr(str(e)))
    sys.exit(0 if "URL has an invalid label." in str(e) else 1)
except Exception as e:
    print("WRONG exception:", type(e).__name__, repr(str(e)))
    sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL

# Req3.1 / Req2.2: a normal all-ASCII host NOT beginning with * or . must be
# accepted (no InvalidURL for the leading-character reason) and preparation completes.
pr = PreparedRequest()
try:
    pr.prepare_url("http://example.com/path?a=1", None)
except InvalidURL as e:
    print("UNEXPECTED InvalidURL for valid host:", repr(str(e)))
    sys.exit(1)
print("prepared url:", pr.url)
if pr.url and pr.url.startswith("http://example.com/path"):
    sys.exit(0)
print("url not prepared as expected")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL, MissingSchema

pr = PreparedRequest()
ok = True

# Req3.4: non-HTTP scheme (mailto) left unchanged, no host validation applied.
p = PreparedRequest()
p.prepare_url("mailto:user@example.com", None)
print("mailto ->", p.url)
if p.url != "mailto:user@example.com":
    print("mailto altered")
    ok = False

# Req3.3: no host component -> InvalidURL about missing host (not leading-char).
p2 = PreparedRequest()
try:
    p2.prepare_url("http://", None)
    print("no-exception for http://")
    ok = False
except InvalidURL as e:
    print("http:// InvalidURL:", repr(str(e)))
    if "URL has an invalid label." in str(e):
        print("wrong message: reports invalid label instead of missing host")
        ok = False
except Exception as e:
    print("http:// wrong exc:", type(e).__name__)
    ok = False

# Req3.5: no scheme -> MissingSchema.
p3 = PreparedRequest()
try:
    p3.prepare_url("example.com/path", None)
    print("no-exception for schemeless")
    ok = False
except MissingSchema as e:
    print("schemeless MissingSchema OK")
except Exception as e:
    print("schemeless wrong exc:", type(e).__name__)
    ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL

# Req3.2 + 3.6: non-ASCII host delegated to IDNA encoder (leading-char guard NOT
# applied). A valid non-ASCII host encodes successfully; an invalid one raises
# InvalidURL. Also IPv6 literal preserved, query before fragment.
ok = True

# valid IDNA host
p = PreparedRequest()
try:
    p.prepare_url("http://éxample.com/p", None)  # éxample.com
    print("idna host ->", p.url)
    if "xn--" not in p.url:
        print("expected punycode encoding")
        ok = False
except InvalidURL as e:
    print("unexpected InvalidURL for valid idna:", repr(str(e)))
    ok = False

# IPv6 literal preserved
p2 = PreparedRequest()
p2.prepare_url("http://[::1]:8080/x", None)
print("ipv6 ->", p2.url)
if "[::1]" not in p2.url:
    print("ipv6 literal not preserved")
    ok = False

# query before fragment
p3 = PreparedRequest()
p3.prepare_url("http://example.com/p?b=2&a=1#frag", None)
print("query/frag ->", p3.url)
if p3.url.index("?b=2&a=1") > p3.url.index("#frag"):
    print("query not before fragment")
    ok = False
if "b=2&a=1" not in p3.url:
    print("param order not preserved")
    ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL

# Req2.2: guard applies ONLY to first char '*' or '.'. Hosts beginning with
# other punctuation/chars must NOT be rejected for the leading-character reason.
ok = True
for host in ["-example.com", "1example.com", "_example.com"]:
    p = PreparedRequest()
    try:
        p.prepare_url("http://%s/x" % host, None)
        print("accepted:", host, "->", p.url)
    except InvalidURL as e:
        print("REJECTED (should not be):", host, repr(str(e)))
        ok = False
    except Exception as e:
        print("other exc for", host, type(e).__name__)
        # a non-InvalidURL error is not the leading-char guard; acceptable? No -
        # spec says accept host unchanged. Treat as failure of accept.
        ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL

# Req1.1 + 1.2 + 1.3 (positive control): host beginning with a dot must raise
# InvalidURL with message 'URL has an invalid label.' and NOT leak a UnicodeError.
pr = PreparedRequest()
try:
    pr.prepare_url("http://.example.com", None)
    print("NO EXCEPTION raised for http://.example.com")
    sys.exit(1)
except InvalidURL as e:
    print("InvalidURL raised:", repr(str(e)))
    if "URL has an invalid label." in str(e):
        sys.exit(0)
    print("wrong message")
    sys.exit(1)
except Exception as e:
    print("WRONG exception type:", type(e).__name__, repr(str(e)))
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: `elif host.startswith((u'*', u'.'))` in PreparedRequest.prepare_url. Probes cover: probe_1 Req1.1/1.2/1.3 (dot host -> InvalidURL 'URL has an invalid label.', no UnicodeError leak; POSITIVE CONTROL: FAILS at base [no exception], HOLDS patched); probe_2 Req2.1 (wildcard '*' still rejected); probe_3 Req3.1/2.2 (normal host accepted, url prepared); probe_4 Req3.3/3.4/3.5 (no-host->'No host supplied' InvalidURL, mailto unchanged, schemeless->MissingSchema); probe_5 Req3.2/3.6 (non-ASCII->IDNA punycode, IPv6 literal preserved, query-before-fragment & param order); probe_6 Req2.2 (hosts starting with -,1,_ NOT rejected). All 6 HOLD on patched tree. Wrong-fix candidate 'drop_wildcard_guard' replaces the guard with only '.' (drops '*'): REJECTED by probe_2 (Req2.1 regression) — demonstrates the suite discriminates weak implementations. No requirements-conforming candidate that resolves differently was found; suite is faithful to gold behavior.

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
import sys
from requests.models import PreparedRequest
from requests.exceptions import InvalidURL

# Req1.1 + 1.2 + 1.3 (positive control): host beginning with a dot must raise
# InvalidURL with message 'URL has an invalid label.' and NOT leak a UnicodeError.
pr = PreparedRequest()
try:
    pr.prepare_url("http://.example.com", None)
    print("NO EXCEPTION raised for http://.example.com")
    sys.exit(1)
except InvalidURL as e:
    print("InvalidURL raised:", repr(str(e)))
    if "URL has an invalid label." in str(e):
        sys.exit(0)
    print("wrong message")
    sys.exit(1)
except Exception as e:
    print("WRONG exception type:", type(e).__name__, repr(str(e)))
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: `elif host.startswith((u'*', u'.'))` in PreparedRequest.prepare_url. Probes cover: probe_1 Req1.1/1.2/1.3 (dot host -> InvalidURL 'URL has an invalid label.', no UnicodeError leak; POSITIVE CONTROL: FAILS at base [no exception], HOLDS patched); probe_2 Req2.1 (wildcard '*' still rejected); probe_3 Req3.1/2.2 (normal host accepted, url prepared); probe_4 Req3.3/3.4/3.5 (no-host->'No host supplied' InvalidURL, mailto unchanged, schemeless->MissingSchema); probe_5 Req3.2/3.6 (non-ASCII->IDNA punycode, IPv6 literal preserved, query-before-fragment & param order); probe_6 Req2.2 (hosts starting with -,1,_ NOT rejected). All 6 HOLD on patched tree. Wrong-fix candidate 'drop_wildcard_guard' replaces the guard with only '.' (drops '*'): REJECTED by probe_2 (Req2.1 regression) — demonstrates the suite discriminates weak implementations. No requirements-conforming candidate that resolves differently was found; suite is faithful to gold behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed in the instance image on both patched and base trees. Patched: http://.example.com and https://.foo raise InvalidURL('URL has an invalid label.'); http://*.example.com same; http://-example.com accepted (only *,. rejected); http://example.com/path?q=1#frag prepared normally; mailto:foo@bar.com unchanged; bare 'example.com' -> MissingSchema; 'http://' -> InvalidURL no-host. Base (--base): http://.example.com does NOT raise InvalidURL (VIOLATED), confirming Req1 pins the actual change. Req3.2 subtlety verified: a non-ASCII host with an empty leading label (http://.üexample.com) still reaches the IDNA encoder branch and is rejected with exactly 'URL has an invalid label.' — the leading-char elif is not applied to non-ASCII hosts, matching Req3.2's 'if and only if the encoder rejects' + 'guard SHALL NOT be applied to a non-ASCII host'. (Other IDNA rejections surface as 'Failed to parse: ...' which the requirements do not over-specify the exact text for beyond the empty-label case.) Modeling boundary is the changed behavior, not a narrow slice or invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document is a behavioral translation of the fix. Every specific detail — the offending host `http://.example.com`, the leaked `UnicodeError`, the target `InvalidURL` with message `URL has an invalid label.`, and the location `PreparedRequest.prepare_url` in `requests/models.py` — is present in the PUBLIC problem_statement (which links directly to models.py L401). The wildcard (`*`) guard and the exact message string derive from the pre-existing code that the problem_statement references, not from the hidden gold edit. The hidden test adds two parametrized cases (`http://*example.com`, `http://.example.com`) to `test_invalid_url`; the requirements do NOT reproduce test names/paths/ids, do not quote test or gold code, invent no fix-specific identifiers, and the gold one-liner (`host.startswith((u'*', u'.'))`) is described as behavior (reject leading `*` or `.`) rather than transmitted verbatim. Requirement 3's enumeration (no-host, non-HTTP scheme, no scheme/MissingSchema, IPv6, IDNA) reads as general behavior preservation, consistent with the public spec, not a mirror of the PASS_TO_PASS parametrization. No semantic leak beyond the problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
