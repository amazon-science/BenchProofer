# P2 adversarial audit — django__django-14349

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
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Positive control / Req1.1: a URL with a trailing line-feed must be rejected.
v = URLValidator()
val = 'http://www.djangoproject.com/\n'
try:
    v(val)
    print("NO ValidationError raised for trailing \\n -> ACCEPTED (bad)")
    sys.exit(1)
except ValidationError as e:
    print("ValidationError raised for trailing \\n (good)")
    sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Req1.1 & 1.2: tab/CR/LF anywhere (start, middle, end) must be rejected.
v = URLValidator()
cases = [
    'http://www.djangoproject.com/\r',   # trailing CR
    'http://www.django\rproject.com/',   # middle CR
    'http://\twww.djangoproject.com/',   # middle/host TAB
    '\nhttp://www.djangoproject.com/',   # leading LF
    'http://www.djangoproject.com/\t',   # trailing TAB
]
ok = True
for val in cases:
    try:
        v(val)
        print("ACCEPTED (bad):", repr(val))
        ok = False
    except ValidationError:
        print("rejected (good):", repr(val))
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Req1.3: disallowed char inside host portion incl. bracketed IPv6 host.
v = URLValidator()
cases = [
    'http://[::ffff:192.9.5.5]\n',
    'http://[::ffff:192.9.5.5]\r',
    'http://[::\rffff:192.9.5.5]',
    'http://\t[::ffff:192.9.5.5]',
]
ok = True
for val in cases:
    try:
        v(val)
        print("ACCEPTED (bad):", repr(val))
        ok = False
    except ValidationError:
        print("rejected (good):", repr(val))
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Req1.4: rejection due to disallowed char carries same message & code as any
# other invalid URL, and params includes offending value under 'value'.
v = URLValidator()

# reference: message/code for a generic invalid URL (no disallowed chars)
try:
    v('no_scheme')
    print("reference invalid URL unexpectedly accepted")
    sys.exit(1)
except ValidationError as ref:
    ref_code = ref.code
    ref_msg = ref.messages

val = 'http://www.djangoproject.com/\n'
try:
    v(val)
    print("ACCEPTED (bad)")
    sys.exit(1)
except ValidationError as e:
    print("code:", e.code, "ref_code:", ref_code)
    print("messages:", e.messages, "ref_messages:", ref_msg)
    print("params:", getattr(e, 'params', None))
    ok = (e.code == ref_code
          and e.messages == ref_msg
          and getattr(e, 'params', None) is not None
          and e.params.get('value') == val)
    sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Req2: preserve existing behavior for values without disallowed chars.
v = URLValidator()
ok = True

# 2.3: well-formed URLs accepted
for val in ['http://www.djangoproject.com/', 'https://example.com/path?q=1',
            'ftp://ftp.example.com/', 'http://[::ffff:192.9.5.5]']:
    try:
        v(val)
        print("accepted (good):", repr(val))
    except ValidationError:
        print("REJECTED valid url (bad):", repr(val))
        ok = False

# 2.1: non-string raises
for bad in [None, 56]:
    try:
        v(bad)
        print("non-string accepted (bad):", repr(bad))
        ok = False
    except ValidationError:
        print("non-string rejected (good):", repr(bad))

# 2.4: bad scheme raises
try:
    v('imap://example.com/')
    print("bad scheme accepted (bad)")
    ok = False
except ValidationError:
    print("bad scheme rejected (good)")

# 2.5: structural failures still rejected
for val in ['no_scheme', 'http://www.asdasdasdasdsadfm.com.br ',
            'http://www.asdasdasdasdsadfm.com.br z']:
    try:
        v(val)
        print("malformed accepted (bad):", repr(val))
        ok = False
    except ValidationError:
        print("malformed rejected (good):", repr(val))

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import warnings
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django.core.validators import (
    URLValidator, RegexValidator, EmailValidator, validate_ipv4_address,
)
from django.core.exceptions import ValidationError

# Req3: preserve unrelated validator behaviors.
ok = True

# 3.1 equality semantics
if not (RegexValidator('a') == RegexValidator('a')):
    print("equal validators compared unequal (bad)"); ok = False
if RegexValidator('a') == RegexValidator('b'):
    print("unequal validators compared equal (bad)"); ok = False
print("equality semantics ok")

# 3.4 regex flags honored
v = RegexValidator('^[a-z]+$', flags=__import__('re').IGNORECASE)
try:
    v('ABC')
    print("regex flags honored (good)")
except ValidationError:
    print("regex flags NOT honored (bad)"); ok = False

# 3.2 deprecated domain_whitelist emits deprecation warning
try:
    from django.utils.deprecation import RemovedInDjango41Warning
except Exception:
    RemovedInDjango41Warning = DeprecationWarning
ev = EmailValidator()
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    _ = ev.domain_whitelist
    got = any(issubclass(x.category, DeprecationWarning) or 'Deprecat' in x.category.__name__ for x in w)
    if got:
        print("deprecation warning emitted (good)")
    else:
        print("no deprecation warning (bad)"); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Positive control / Req1.1: a URL with a trailing line-feed must be rejected.
v = URLValidator()
val = 'http://www.djangoproject.com/\n'
try:
    v(val)
    print("NO ValidationError raised for trailing \\n -> ACCEPTED (bad)")
    sys.exit(1)
except ValidationError as e:
    print("ValidationError raised for trailing \\n (good)")
    sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14349: URLValidator must reject any URL containing tab/CR/LF regardless of urllib.parse stripping.

Probes (all run in the official image on the gold-PATCHED tree unless noted):
- probe_1 (Req1.1, POSITIVE CONTROL): trailing '\n' rejected. HOLDS patched (exit0). At BASE it is ACCEPTED (exit1) -> prepatch reproduced, discriminating power confirmed.
- probe_2 (Req1.1/1.2): '\r' trailing, '\r' middle, '\t' host, leading '\n', trailing '\t' all rejected. HOLDS patched.
- probe_3 (Req1.3): disallowed chars inside host incl. bracketed IPv6 ([::ffff:...]\n, \r, \r-in-middle, leading \t) rejected. HOLDS patched.
- probe_4 (Req1.4): char-based rejection carries same code ('invalid') and message ('Enter a valid URL.') as generic invalid URL, and params['value'] == offending value. HOLDS patched.
- probe_5 (Req2.1/2.3/2.4/2.5): well-formed URLs accepted; non-string (None,56) rejected; bad scheme rejected; structural failures (no_scheme, trailing junk) rejected. HOLDS patched.
- probe_6 (Req3.1/3.2/3.4): validator equality semantics; EmailValidator.domain_whitelist emits DeprecationWarning; RegexValidator honors re.IGNORECASE flag. HOLDS patched. (domain_whitelist lives on EmailValidator, not URLValidator.)

CANDIDATE WRONG PATCH (weak_newline_only, weak.diff): rejects only '\n' (naive/partial fix a weak reading of Req1 permits, missing \r and \t). Applied cleanly at base. Result: probe_2 REJECTS it (exit1: \r, \t cases accepted) and probe_3 REJECTS it (exit1: \r, \t IPv6-host cases accepted). probes 1,4,5,6 pass under it. => The suite discriminates this wrong implementation; it would also fail the official FAIL_TO_PASS (test cases include \r and \t values). Not a too-weak finding.

All 6 probes HOLD on the gold-patched tree; positive control HOLDS patched and FAILS at base; >=1 candidate patch REJECTED by the suite. Verdict SOUND.

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
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Positive control / Req1.1: a URL with a trailing line-feed must be rejected.
v = URLValidator()
val = 'http://www.djangoproject.com/\n'
try:
    v(val)
    print("NO ValidationError raised for trailing \\n -> ACCEPTED (bad)")
    sys.exit(1)
except ValidationError as e:
    print("ValidationError raised for trailing \\n (good)")
    sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14349: URLValidator must reject any URL containing tab/CR/LF regardless of urllib.parse stripping.

Probes (all run in the official image on the gold-PATCHED tree unless noted):
- probe_1 (Req1.1, POSITIVE CONTROL): trailing '\n' rejected. HOLDS patched (exit0). At BASE it is ACCEPTED (exit1) -> prepatch reproduced, discriminating power confirmed.
- probe_2 (Req1.1/1.2): '\r' trailing, '\r' middle, '\t' host, leading '\n', trailing '\t' all rejected. HOLDS patched.
- probe_3 (Req1.3): disallowed chars inside host incl. bracketed IPv6 ([::ffff:...]\n, \r, \r-in-middle, leading \t) rejected. HOLDS patched.
- probe_4 (Req1.4): char-based rejection carries same code ('invalid') and message ('Enter a valid URL.') as generic invalid URL, and params['value'] == offending value. HOLDS patched.
- probe_5 (Req2.1/2.3/2.4/2.5): well-formed URLs accepted; non-string (None,56) rejected; bad scheme rejected; structural failures (no_scheme, trailing junk) rejected. HOLDS patched.
- probe_6 (Req3.1/3.2/3.4): validator equality semantics; EmailValidator.domain_whitelist emits DeprecationWarning; RegexValidator honors re.IGNORECASE flag. HOLDS patched. (domain_whitelist lives on EmailValidator, not URLValidator.)

CANDIDATE WRONG PATCH (weak_newline_only, weak.diff): rejects only '\n' (naive/partial fix a weak reading of Req1 permits, missing \r and \t). Applied cleanly at base. Result: probe_2 REJECTS it (exit1: \r, \t cases accepted) and probe_3 REJECTS it (exit1: \r, \t IPv6-host cases accepted). probes 1,4,5,6 pass under it. => The suite discriminates this wrong implementation; it would also fail the official FAIL_TO_PASS (test cases include \r and \t values). Not a too-weak finding.

All 6 probes HOLD on the gold-patched tree; positive control HOLDS patched and FAILS at base; >=1 candidate patch REJECTED by the suite. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `unsafe_chars = frozenset('\t\r\n')` and rejects any value whose intersection is non-empty, placed before URL splitting — exactly the changed observable behavior the requirements pin. Modeling boundary is correct: requirements target the raw-input character check (the actual fix) rather than a narrow slice. Probe on gold-patched tree: ALL PASS (exit 0); base probe confirms newline/IPv6-newline previously accepted.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to URLValidator.__call__ in django/core/validators.py (legitimate) and translate the fix into behavioral rules: reject any string containing \t/\r/\n regardless of urllib.parse stripping. All specifics are either already public in the problem_statement or are behavioral generalizations, not test transmission:

- The problem_statement already names bpo-43882, the LF/CR/tab stripping in urllib.parse splitting, and gives the concrete examples 'http://www.djangoproject.com/\n' and 'http://[::ffff:192.9.5.5]\n'. So the tab/CR/LF characters AND the bracketed IPv6 host example are public.
- Req 1.2 (start/middle/end) and 1.3 (inside host portion incl. bracketed IPv6) generalize position — this is behavioral description, not a verbatim case list. The test_patch cases (trailing \r, host-embedded \r, leading \t, \t before IPv6) are all instances of the general 'reject anywhere' rule; the document does NOT enumerate them one-for-one.
- The gold-invented identifier `unsafe_chars` (frozenset('\t\r\n')) does NOT appear anywhere in requirements.md. No test names, file paths, function/class names, parametrization ids, or quoted test/gold code appear.
- Req 3's enumeration (equality, deprecation warning, single/list/dict messages, length-limited messages, regex flags) corresponds to PASS_TO_PASS regression areas, but these are pre-existing public tests in the repo and are described as behaviors to preserve, not as test identifiers — standard 'no regression' spec hygiene, the intended behavioral translation.

No content derivable only from the hidden tests or gold edit is transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
