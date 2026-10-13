# P2 adversarial audit — django__django-11532

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.3 (positive control): get_fqdn returns pure-ASCII (punycode) for a non-ASCII host.
import socket
socket.getfqdn = lambda *a, **k: 'bücher.example.com'  # bücher.example.com
from django.core.mail.utils import CachedDnsName
name = CachedDnsName().get_fqdn()
print("get_fqdn ->", repr(name))
ok = isinstance(name, str) and all(ord(c)<128 for c in name) and 'xn--' in name
print("ascii+xn--:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2: for an already-ASCII host, get_fqdn equals IDNA ACE encoding (unchanged label content).
import socket
host = 'plainhost.example.com'
socket.getfqdn = lambda *a, **k: host
from django.core.mail.utils import CachedDnsName
name = CachedDnsName().get_fqdn()
expected = host.encode('idna').decode('ascii')
print("get_fqdn ->", repr(name), "expected", repr(expected))
import sys; sys.exit(0 if name == expected else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.4: lazy + cached: getfqdn resolved at most once, reused.
import socket
calls = {'n': 0}
def fake(*a, **k):
    calls['n'] += 1
    return 'bücher.example.com'
socket.getfqdn = fake
from django.core.mail.utils import CachedDnsName
d = CachedDnsName()
n1 = d.get_fqdn(); n2 = d.get_fqdn(); n3 = d.get_fqdn()
print("calls:", calls['n'], "vals:", n1, n2, n3)
ok = calls['n'] == 1 and n1 == n2 == n3
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.2: EmailMessage.message() with non-ASCII DNS_NAME and iso-8859-1 encoding
# succeeds (no UnicodeEncodeError) and Message-ID contains xn-- (punycode).
import django.core.mail.utils as u
# force DNS_NAME to a non-ASCII fqdn
u.DNS_NAME._fqdn = 'bücher.example.com'.encode('idna').decode('ascii') if False else None
u.DNS_NAME._fqdn = None
import socket
socket.getfqdn = lambda *a, **k: 'bücher.example.com'
# reset cache so it recomputes via patched get_fqdn
if hasattr(u.DNS_NAME, '_fqdn'):
    del u.DNS_NAME._fqdn
from django.conf import settings
if not settings.configured:
    settings.configure(EMAIL_USE_LOCALTIME=False, USE_I18N=False, USE_TZ=False)
from django.core.mail import EmailMessage
m = EmailMessage('subj', 'body', 'from@example.com', ['to@example.com'])
m.encoding = 'iso-8859-1'
try:
    msg = m.message()
except UnicodeEncodeError as e:
    print("FAIL UnicodeEncodeError:", e)
    import sys; sys.exit(1)
mid = msg['Message-ID']
print("Message-ID:", mid)
ok = 'xn--' in mid and all(ord(c)<128 for c in mid)
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2: sanitize_address punycodes non-ASCII domain, leaves ASCII domain unchanged.
from django.core.mail.message import sanitize_address
r1 = sanitize_address('to@bücher.example.com', 'utf-8')
print("nonascii domain ->", r1)
r2 = sanitize_address('to@plain.example.com', 'utf-8')
print("ascii domain ->", r2)
ok = ('xn--' in r1 and all(ord(c)<128 for c in r1)) and ('plain.example.com' in r2)
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 6.1/6.2: punycode helper exists in django.utils.encoding and equals idna ACE.
from django.utils.encoding import punycode
for d in ['bücher.de', 'example.com', '漢字.example.com']:
    got = punycode(d)
    exp = d.encode('idna').decode('ascii')
    print(d, "->", got, "exp", exp)
    if got != exp:
        import sys; sys.exit(1)
import sys; sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 4.1: URLValidator converts non-ASCII host to ACE and validates.
from django.core.validators import URLValidator
v = URLValidator()
try:
    v('http://bücher.example.com/path')
    print("valid IDN URL accepted")
except Exception as e:
    print("FAIL rejected:", type(e).__name__, e)
    import sys; sys.exit(1)
import sys; sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.3 (positive control): get_fqdn returns pure-ASCII (punycode) for a non-ASCII host.
import socket
socket.getfqdn = lambda *a, **k: 'bücher.example.com'  # bücher.example.com
from django.core.mail.utils import CachedDnsName
name = CachedDnsName().get_fqdn()
print("get_fqdn ->", repr(name))
ok = isinstance(name, str) and all(ord(c)<128 for c in name) and 'xn--' in name
print("ascii+xn--:", ok)
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering Reqs 1-6. All HOLD on gold-patched tree. Positive controls probe_1 (Req 1.3: get_fqdn returns pure-ASCII/xn-- for non-ASCII host) and probe_4 (Req 2.2: EmailMessage.message() with iso-8859-1 succeeds and Message-ID carries xn--) both FAIL at base -> discriminating power confirmed. Probe map: p1=Req1.3(+pos-ctrl), p2=Req1.2(ASCII host == idna ACE), p3=Req1.4(lazy+cached, getfqdn called once), p4=Req2.2(pos-ctrl), p5=Req3.1/3.2(sanitize_address punycodes non-ASCII domain, leaves ASCII unchanged), p6=Req6.1/6.2(punycode helper exists & == idna ACE), p7=Req4.1(URLValidator accepts IDN).

Candidate wrong-fix weak.diff applies every hunk of gold EXCEPT the django/core/mail/utils.py get_fqdn punycode change (the true F2P behavior) — it is REJECTED by probe_1 and probe_4 (the hostname still flows raw into Message-ID and crashes under iso-8859-1), while p2/p3/p5/p6/p7 still hold. This demonstrates the suite discriminates the lazy fix that satisfies the refactor requirements (shared punycode helper, unchanged validators/html/sanitize semantics) but leaves the core mail-metadata bug unfixed. Env note: instance image is py3.6 so str.isascii() unavailable — probes use all(ord(c)<128 ...). Docker probe runs completed cleanly; not inconclusive.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.3 (positive control): get_fqdn returns pure-ASCII (punycode) for a non-ASCII host.
import socket
socket.getfqdn = lambda *a, **k: 'bücher.example.com'  # bücher.example.com
from django.core.mail.utils import CachedDnsName
name = CachedDnsName().get_fqdn()
print("get_fqdn ->", repr(name))
ok = isinstance(name, str) and all(ord(c)<128 for c in name) and 'xn--' in name
print("ascii+xn--:", ok)
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering Reqs 1-6. All HOLD on gold-patched tree. Positive controls probe_1 (Req 1.3: get_fqdn returns pure-ASCII/xn-- for non-ASCII host) and probe_4 (Req 2.2: EmailMessage.message() with iso-8859-1 succeeds and Message-ID carries xn--) both FAIL at base -> discriminating power confirmed. Probe map: p1=Req1.3(+pos-ctrl), p2=Req1.2(ASCII host == idna ACE), p3=Req1.4(lazy+cached, getfqdn called once), p4=Req2.2(pos-ctrl), p5=Req3.1/3.2(sanitize_address punycodes non-ASCII domain, leaves ASCII unchanged), p6=Req6.1/6.2(punycode helper exists & == idna ACE), p7=Req4.1(URLValidator accepts IDN).

Candidate wrong-fix weak.diff applies every hunk of gold EXCEPT the django/core/mail/utils.py get_fqdn punycode change (the true F2P behavior) — it is REJECTED by probe_1 and probe_4 (the hostname still flows raw into Message-ID and crashes under iso-8859-1), while p2/p3/p5/p6/p7 still hold. This demonstrates the suite discriminates the lazy fix that satisfies the refactor requirements (shared punycode helper, unchanged validators/html/sanitize semantics) but leaves the core mail-metadata bug unfixed. Env note: instance image is py3.6 so str.isascii() unavailable — probes use all(ord(c)<128 ...). Docker probe runs completed cleanly; not inconclusive.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements 1-6 map exactly onto the six diff hunks. The patch adds punycode() helper in encoding.py (Req6.1), wraps socket.getfqdn in punycode in mail/utils.py (Req1/Req2), and replaces the inline try/except domain.encode('idna').decode('ascii') idiom with punycode() in sanitize_address (Req3), validators.URLValidator + EmailValidator (Req4), and html.urlize/is_email_simple (Req5). Modeling boundary is correct: requirements pin the observable changed behavior (ASCII-safe host in Message-ID under any encoding) rather than a narrow branch. Regression requirements (3-5) correctly assert unchanged semantics, consistent with punycode being a literal extraction of the same idiom (note: the extracted helper always calls encode('idna'), dropping the old ASCII-fast-path try/except, but for ASCII input .encode('idna') is a no-op equal to the original result, so behavior is preserved — verified punycode('example.com')=='example.com'). Probe HELD on gold-patched tree (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the punycode/IDNA-ACE fix behaviorally. Every specific detail overlapping the hidden test is ALREADY PUBLIC in the problem_statement: 'punycode' as the fix approach, iso-8859-1 encoding, Message-ID header, make_msgid(domain=DNS_NAME), EmailMessage.message, UnicodeEncodeError, and even the exact ACE string 'xn--p8s937b' (present in the problem_statement's suggested test). The requirements notably do NOT quote the specific test hostname ('漢字'), the specific encoded value 'xn--p8s937b', the test file path (tests/mail/tests.py), the test function name (test_non_ascii_dns_non_unicode_email), the mock.patch('socket.getfqdn', ...) mechanism, or the delattr(DNS_NAME, '_fqdn') cache-reset — using only the generic 'xn--' prefix. The single FAIL_TO_PASS test is fully derivable from the public problem_statement; requirements 3-6 describe pre-existing regression-protected behavior in the gold-touched modules generically, not mirroring any test parametrization (PASS_TO_PASS covers pre-existing tests). Naming the touched modules (message.py, utils.py, encoding.py, validators.py, html.py) and the shared helper 'punycode' localizes the change — legitimate, and 'punycode' matches public fix vocabulary; the hidden tests never reference that identifier so nothing is reconstructed. No quoted test/gold code, no test-shaped case enumeration.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
