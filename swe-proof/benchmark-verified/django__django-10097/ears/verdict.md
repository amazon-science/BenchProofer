# P2 adversarial audit — django__django-10097

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: R1.1 - '/' in credentials segment must be rejected.
# http://foo/bar@example.com : at base '\S+' accepts 'foo/bar' as user; patched rejects.
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
url = "http://foo/bar@example.com"
try:
    v(url)
    print("ACCEPTED (no ValidationError) for", url)
    raise SystemExit(1)
except ValidationError:
    print("REJECTED with ValidationError for", url, "-> criterion holds")
    raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.2: credentials with more than one ':' -> reject
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
url = "http://user:pa:ss@example.com"
try:
    v(url); print("ACCEPTED", url); raise SystemExit(1)
except ValidationError:
    print("REJECTED", url, "holds"); raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.3: authority with more than one '@' (literal @ inside creds) -> reject
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
url = "http://user@name@example.com"
try:
    v(url); print("ACCEPTED", url); raise SystemExit(1)
except ValidationError:
    print("REJECTED", url, "holds"); raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R1.4: creds begins with ':' (user part absent) -> reject
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
bad = ["http://:pass@example.com", "http://@example.com"]
for url in bad:
    try:
        v(url); print("ACCEPTED (should reject)", url); raise SystemExit(1)
    except ValidationError:
        print("REJECTED", url)
print("all hold"); raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R1.5: whitespace in credentials -> reject
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
url = "http://us er@example.com"
try:
    v(url); print("ACCEPTED", url); raise SystemExit(1)
except ValidationError:
    print("REJECTED", url, "holds"); raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R2.2/R2.3/R2.1/R2.4: well-formed creds & credential-less URLs must be ACCEPTED
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
good = [
    "http://example.com",                 # no creds
    "http://user@example.com",            # user only
    "http://user:pass@example.com",       # user:pass
    "http://user:@example.com",           # empty password
    "http://user%40name:p%2fass@example.com",  # percent-encoded reserved
]
for url in good:
    try:
        v(url); print("ACCEPTED", url)
    except ValidationError:
        print("WRONGLY REJECTED", url); raise SystemExit(1)
print("all accepted -> holds"); raise SystemExit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# R3.1/R3.2: reserved chars in path/query/fragment must NOT cause rejection;
# and an appended ?...@... query must NOT rescue an otherwise-invalid URL.
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
# valid URLs with reserved chars in path/query/fragment
ok = [
    "http://example.com/a:b@c/d",
    "http://example.com/p?x=1@2:3",
    "http://example.com/p#frag@:/",
]
for url in ok:
    try:
        v(url); print("ACCEPTED (good)", url)
    except ValidationError:
        print("WRONGLY REJECTED", url); raise SystemExit(1)
# R3.2: previously-invalid URL extended with ?...@... stays invalid
bad = "http://foo/bar?m=foo@example.com"
try:
    v(bad); print("WRONGLY ACCEPTED (should stay invalid)", bad); raise SystemExit(1)
except ValidationError:
    print("REJECTED (stays invalid)", bad)
print("holds"); raise SystemExit(0)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# R3.3: keep accepting variety of previously-valid URLs (IDN, IPv4/6, localhost, ports, paths)
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
good = [
    "http://localhost",
    "http://127.0.0.1:8000/path?q=1#f",
    "http://[2001:db8::1]:443/",
    "http://xn--fsq.jp/",
    "https://example.com:65535/a/b/c?d=e&f=g#h",
    "http://例え.テスト/",
]
for url in good:
    try:
        v(url); print("ACCEPTED", url)
    except ValidationError:
        print("WRONGLY REJECTED", url); raise SystemExit(1)
print("all accepted -> holds"); raise SystemExit(0)
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
# R3.5: existing message + code preserved; public interface/schemes unchanged
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, INSTALLED_APPS=[])
    django.setup()
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
try:
    v("http://foo/bar@example.com")
    print("no error?"); raise SystemExit(1)
except ValidationError as e:
    code = getattr(e, "code", None)
    msgs = list(e.messages)
    print("code=", code, "messages=", msgs)
    assert code == "invalid", code
    assert any("Enter a valid URL" in m for m in msgs), msgs
assert v.schemes == ['http', 'https', 'ftp', 'ftps'], v.schemes
print("holds"); raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: R1.1 - '/' in credentials segment must be rejected.
# http://foo/bar@example.com : at base '\S+' accepts 'foo/bar' as user; patched rejects.
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
url = "http://foo/bar@example.com"
try:
    v(url)
    print("ACCEPTED (no ValidationError) for", url)
    raise SystemExit(1)
except ValidationError:
    print("REJECTED with ValidationError for", url, "-> criterion holds")
    raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

9 probes covering all three requirements, all HOLD on gold-patched tree. Coverage: probe_1 R1.1 ('/' in creds rejected; also positive control), probe_2 R1.2 (>1 ':' rejected), probe_3 R1.3 (>1 '@'/literal '@' in creds rejected), probe_4 R1.4 (empty user / leading ':' rejected), probe_5 R1.5 (whitespace in creds rejected), probe_6 R2.1-2.4 (no-creds, user-only, user:pass, empty-pass, percent-encoded reserved all accepted), probe_7 R3.1/R3.2 (reserved chars in path/query/fragment accepted; appended ?...@... does not rescue invalid URL), probe_8 R3.3 (localhost, IPv4/IPv6, punycode/IDN, ports, paths still accepted), probe_9 R3.5 (code=='invalid', message 'Enter a valid URL.', schemes unchanged).

Positive control probe_1 FAILS at base (base accepts http://foo/bar@example.com) and HOLDS patched -> discriminating power confirmed (prepatch_reproduced=true). Wrong-fix candidate weak.diff forbids only '/' in userinfo ([^\s/] instead of [^\s:@/]); the probe suite REJECTS it on probe_2 (multi-':' accepted), probe_3 (multi-'@' accepted), and probe_4 (leading-':'/empty-user accepted), demonstrating the suite discriminates a plausible partial fix. No requirements-conforming-but-wrong patch found; suite is tight. Note: probe_9 self-configures Django settings for lazy gettext message access; all others need no settings.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: R1.1 - '/' in credentials segment must be rejected.
# http://foo/bar@example.com : at base '\S+' accepts 'foo/bar' as user; patched rejects.
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
v = URLValidator()
url = "http://foo/bar@example.com"
try:
    v(url)
    print("ACCEPTED (no ValidationError) for", url)
    raise SystemExit(1)
except ValidationError:
    print("REJECTED with ValidationError for", url, "-> criterion holds")
    raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

9 probes covering all three requirements, all HOLD on gold-patched tree. Coverage: probe_1 R1.1 ('/' in creds rejected; also positive control), probe_2 R1.2 (>1 ':' rejected), probe_3 R1.3 (>1 '@'/literal '@' in creds rejected), probe_4 R1.4 (empty user / leading ':' rejected), probe_5 R1.5 (whitespace in creds rejected), probe_6 R2.1-2.4 (no-creds, user-only, user:pass, empty-pass, percent-encoded reserved all accepted), probe_7 R3.1/R3.2 (reserved chars in path/query/fragment accepted; appended ?...@... does not rescue invalid URL), probe_8 R3.3 (localhost, IPv4/IPv6, punycode/IDN, ports, paths still accepted), probe_9 R3.5 (code=='invalid', message 'Enter a valid URL.', schemes unchanged).

Positive control probe_1 FAILS at base (base accepts http://foo/bar@example.com) and HOLDS patched -> discriminating power confirmed (prepatch_reproduced=true). Wrong-fix candidate weak.diff forbids only '/' in userinfo ([^\s/] instead of [^\s:@/]); the probe suite REJECTS it on probe_2 (multi-':' accepted), probe_3 (multi-'@' accepted), and probe_4 (leading-':'/empty-user accepted), demonstrating the suite discriminates a plausible partial fix. No requirements-conforming-but-wrong patch found; suite is tight. Note: probe_9 self-configures Django settings for lazy gettext message access; all others need no settings.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes the userinfo sub-pattern from (?:\S+(?::\S*)?@)? to (?:[^\s:@/]+(?::[^\s:@/]*)?@)?. This exactly encodes: non-empty user part of chars that are neither whitespace nor : @ /, an optional single ':' + possibly-empty password of the same admissible chars, then '@'. Requirements 1-3 pin precisely this observable accept/reject boundary of URLValidator.__call__ (raising ValidationError), not a narrow slice. Req6's admissible-character set and Req2.3's optional/empty password both match the regex character classes. Percent-encoded forms (%40) contain no literal delimiter and remain accepted (2.4), consistent with code. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior. Probed live in the instance image on py3.5; base vs patched diff confirmed direction.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe URLValidator behavior in behavioral terms derived from the PUBLIC problem_statement (RFC 1738 §3.1: within user/password fields, ':', '@', '/' must be encoded) and the public example http://foo/bar@example.com plus the public '?m=foo@example.com' query-appending pattern. Naming URLValidator / django/core/validators.py / __call__ is legitimate localization. The acceptance criteria (reject '/', >1 ':', '@' inside creds, empty/leading-':' user, whitespace; admit exactly one ':' separator) are a faithful translation of the gold regex '(?:[^\s:@/]+(?::[^\s:@/]*)?@)?' into behavior, all following directly from the publicly quoted RFC rule — not a transcription of the hidden parametrized test URLs (foo@bar@example.com, foo:bar:baz@example.com, foo:bar@baz@example.com, foo:bar/baz@example.com, invalid-.com/?m=...). No test function/class names, test file identifiers beyond the public invalid_urls.txt reference, parametrization ids, verbatim gold/test lines, or fix-invented identifiers appear. The %40/%2f mention corresponds to canonical percent-encodings of the RFC-reserved chars (illustrative), not leaked test tokens. This is behavioral requirement-writing, not test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
