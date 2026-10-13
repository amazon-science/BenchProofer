# P2 adversarial audit — django__django-15098

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('en-latn-us','English Latn US'),('de','German')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/en-latn-us/')
print("Req1.1 /en-latn-us/ ->", repr(r))
sys.exit(0 if r == 'en-latn-us' else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('en-latn-us','English Latn US'),('de','German')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/en-Latn-US/')
print("Req1.2 /en-Latn-US/ ->", repr(r))
sys.exit(0 if r == 'en-latn-us' else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('en-latn','English Latn'),('de','German')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/en-latn-us/')
print("Req1.3 /en-latn-us/ (only en-latn supported) ->", repr(r))
sys.exit(0 if r == 'en-latn' else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('en-latn-us','English Latn US'),('de','German')])
from django.utils.translation.trans_real import get_language_from_path as g
a = g('/en-latn-us'); b = g('/en-latn-us/')
print("Req1.4 no-slash ->", repr(a), "; slash ->", repr(b))
sys.exit(0 if a == b == 'en-latn-us' else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()
setup([('en','English')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/en-a-b-c/')
print("Req2.1 /en-a-b-c/ (4 subtags; only 'en' supported) ->", repr(r))
sys.exit(0 if r is None else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('de-at','Austrian German'),('en','English')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/de-at/'); r2 = g('/de-at')
print("Req3.2 /de-at/ ->", repr(r), "; /de-at ->", repr(r2))
sys.exit(0 if r == r2 == 'de-at' else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('de-at@euro','Austrian euro'),('en','English')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/de-at@euro/')
print("Req3.5 /de-at@euro/ (second subtag via @) ->", repr(r))
sys.exit(0 if r == 'de-at@euro' else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('en','English')], language_code='en-us')
from django.utils.translation import trans_null as tn
ok = True
p = tn.get_language_from_path('/en/')
print("Req4.1 disabled get_language_from_path ->", repr(p)); ok &= (p is None)
c = tn.get_supported_language_variant('en-us')
print("Req4.2 disabled gsl(LANGUAGE_CODE) ->", repr(c)); ok &= (c == 'en-us')
try:
    tn.get_supported_language_variant('fr')
    print("Req4.3 gsl('fr') did NOT raise"); ok = False
except LookupError:
    print("Req4.3 gsl('fr') raised LookupError -> ok")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('en-latn-us','English Latn US'),('de','German')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/en-latn-us/')
print("Req1.1 /en-latn-us/ ->", repr(r))
sys.exit(0 if r == 'en-latn-us' else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django-15098: gold widens language_code_prefix_re from ^/(\w+([@-]\w+)?)(/|$) to {0,2}, recognizing language-script-region URL prefixes.

Probe suite (8), all HOLD on gold-patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): /en-latn-us/ with en-latn-us supported -> 'en-latn-us'. FAILS at base (->None). Discriminates.
- probe_2 (Req1.2): case-insensitive /en-Latn-US/ -> supported code 'en-latn-us' as listed. base->None.
- probe_3 (Req1.3): generic fallback, only en-latn supported, /en-latn-us/ -> 'en-latn'. base->None.
- probe_4 (Req1.4): /en-latn-us == /en-latn-us/ (end-of-path terminates tag).
- probe_5 (Req2.1): only 'en' supported, over-long /en-a-b-c/ -> None (no over-match).
- probe_6 (Req3.2): one-subtag /de-at/ and /de-at both -> 'de-at' (regression preserved).
- probe_7 (Req3.5): second subtag via @ separator, /de-at@euro/ -> 'de-at@euro'. base->None.
- probe_8 (Req4.1/4.2/4.3): trans_null disabled variant: get_language_from_path->None, gsl(LANGUAGE_CODE)->'en-us', gsl('fr') raises LookupError.

Candidate wrong-fix patches, BOTH REJECTED by the suite (demonstrating discrimination):
- weak1 (@-blind: (\w+([@-]\w+)?(-\w+)?)): satisfies a narrow reading of Req3.5 but only '-' can introduce the 2nd subtag; REJECTED by probe_7 (/de-at@euro/ -> None). This is exactly the G-PANEL-2 faithfulness concern; the probe suite catches it because Req3.5 explicitly mandates the second subtag be accepted regardless of separator.
- weak2 (over-match: (\w+([@-]\w+)*)): unbounded trailing subtags; REJECTED by probe_5 (/en-a-b-c/ -> 'en' instead of None), violating Req2.1.

No probe-conforming alternative patch found that would fail the hidden tests. Note: meta.json records G-PANEL-2=fail (faithfulness/verify-not-correct gap re: @-second-subtag), but for the G-EQ (spec-too-weak) question the requirements text as encoded is NOT too weak: both natural weak fixes are rejected by probes anchored on explicit criteria (Req2.1 no-over-match, Req3.5 either-separator second subtag). Verdict SOUND for G-EQ.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import django
from django.conf import settings
def setup(languages, language_code="en-us"):
    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=True, LANGUAGE_CODE=language_code, LANGUAGES=languages)
        django.setup()

setup([('en-latn-us','English Latn US'),('de','German')])
from django.utils.translation.trans_real import get_language_from_path as g
r = g('/en-latn-us/')
print("Req1.1 /en-latn-us/ ->", repr(r))
sys.exit(0 if r == 'en-latn-us' else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django-15098: gold widens language_code_prefix_re from ^/(\w+([@-]\w+)?)(/|$) to {0,2}, recognizing language-script-region URL prefixes.

Probe suite (8), all HOLD on gold-patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): /en-latn-us/ with en-latn-us supported -> 'en-latn-us'. FAILS at base (->None). Discriminates.
- probe_2 (Req1.2): case-insensitive /en-Latn-US/ -> supported code 'en-latn-us' as listed. base->None.
- probe_3 (Req1.3): generic fallback, only en-latn supported, /en-latn-us/ -> 'en-latn'. base->None.
- probe_4 (Req1.4): /en-latn-us == /en-latn-us/ (end-of-path terminates tag).
- probe_5 (Req2.1): only 'en' supported, over-long /en-a-b-c/ -> None (no over-match).
- probe_6 (Req3.2): one-subtag /de-at/ and /de-at both -> 'de-at' (regression preserved).
- probe_7 (Req3.5): second subtag via @ separator, /de-at@euro/ -> 'de-at@euro'. base->None.
- probe_8 (Req4.1/4.2/4.3): trans_null disabled variant: get_language_from_path->None, gsl(LANGUAGE_CODE)->'en-us', gsl('fr') raises LookupError.

Candidate wrong-fix patches, BOTH REJECTED by the suite (demonstrating discrimination):
- weak1 (@-blind: (\w+([@-]\w+)?(-\w+)?)): satisfies a narrow reading of Req3.5 but only '-' can introduce the 2nd subtag; REJECTED by probe_7 (/de-at@euro/ -> None). This is exactly the G-PANEL-2 faithfulness concern; the probe suite catches it because Req3.5 explicitly mandates the second subtag be accepted regardless of separator.
- weak2 (over-match: (\w+([@-]\w+)*)): unbounded trailing subtags; REJECTED by probe_5 (/en-a-b-c/ -> 'en' instead of None), violating Req2.1.

No probe-conforming alternative patch found that would fail the hidden tests. Note: meta.json records G-PANEL-2=fail (faithfulness/verify-not-correct gap re: @-second-subtag), but for the G-EQ (spec-too-weak) question the requirements text as encoded is NOT too weak: both natural weak fixes are rejected by probes anchored on explicit criteria (Req2.1 no-over-match, Req3.5 either-separator second subtag). Verdict SOUND for G-EQ.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Regex verified directly: {0,2} admits primary + up to two [@-]\w+ trailing subtags; base admits only zero-or-one. Req 3.5 correctly captures the exact modeling boundary — the SOLE change is admission of a second [@-]-introduced trailing subtag, with mixed @/- separators allowed (matches the [@-] character class). Requirements pin the changed observable get_language_from_path behavior, not merely one branch/helper. Probe: probe.py -> 'ALL OK' patched, AssertionError(None) at base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the behavioral change generically. Every concrete tag it cites (en-latn-us, en-Latn-US, de-at, single/three-part shapes) is already public in the problem_statement, which explicitly gives the LANGUAGES=[('en-us'),('en-latn-us'),('en-Latn-US')] example and quotes the RFC 5646 langtag=language[-script][-region] grammar. The 'up to two trailing subtags' framing derives from that public RFC grammar, not from the tests. No hidden-test artifacts are transmitted: none of the distinctive parametrized ids (de-1996, de-ch-1901, i-mingo, kl-tunumiit, nan-hani-tw, /de-simple-page-test/, /xyz/) appear, nor any test names/paths (test_get_language_from_path_real, i18n.tests.MiscTests), nor quoted test/gold code. Naming get_language_from_path, language_code_prefix_re, get_supported_language_variant, and trans_real.py is legitimate localization of the change. The @-modifier separator detail describes the pre-existing consumer-visible source regex, not hidden tests. The disabled-variant requirements (Req 4) map to test_get_supported_language_variant_null but are stated as behavior, not as test reconstruction. No case enumeration mirrors the test list beyond what the problem statement already covers.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
