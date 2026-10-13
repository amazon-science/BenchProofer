# P2 adversarial audit — django__django-11099

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
Weak candidate patches only ASCIIUsernameValidator's regex to \Z, leaving UnicodeUsernameValidator's trailing '$'. probe_2 (Req1.2) rejects it: UnicodeUsernameValidator still ACCEPTS 'abc\n' at base-with-partial-patch. This is a probe-conforming-in-part alternative the suite discriminates.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (Req1.1): ASCIIUsernameValidator rejects a trailing-newline value.
Holds on patched, must FAIL at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError

v = ASCIIUsernameValidator()
val = "abc\n"
try:
    v(val)
    print("ACCEPTED trailing-newline value (BAD):", repr(val))
    raise SystemExit(1)
except ValidationError:
    print("Rejected trailing-newline value (GOOD):", repr(val))
    raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2: UnicodeUsernameValidator rejects trailing-newline value."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

v = UnicodeUsernameValidator()
val = "abc\n"
try:
    v(val)
    print("ACCEPTED (BAD):", repr(val))
    raise SystemExit(1)
except ValidationError:
    print("Rejected (GOOD):", repr(val))
    raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3 / Req2.2: newline anywhere (middle) causes rejection for both validators.
Also covers non-final newline position."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

bad = ["ab\ncd", "\nabc"]
ok = True
for cls in (ASCIIUsernameValidator, UnicodeUsernameValidator):
    v = cls()
    for val in bad:
        try:
            v(val)
            print("ACCEPTED (BAD):", cls.__name__, repr(val))
            ok = False
        except ValidationError:
            print("Rejected (GOOD):", cls.__name__, repr(val))
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.3: legitimate usernames still accepted.
ASCII letters, ASCII+punctuation, and Unicode non-English script."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

ok = True
va = ASCIIUsernameValidator()
for val in ["JohnDoe", "john", "user.name@host+tag-1_2"]:
    try:
        va(val); print("Accepted (GOOD) ASCII:", repr(val))
    except ValidationError:
        print("REJECTED (BAD) ASCII:", repr(val)); ok = False

vu = UnicodeUsernameValidator()
for val in ["Jean-Luc", "反社会人格", "Ω_user.1"]:
    try:
        vu(val); print("Accepted (GOOD) Unicode:", repr(val))
    except ValidationError:
        print("REJECTED (BAD) Unicode:", repr(val)); ok = False
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.1/4.2/4.3: previously-invalid values stay rejected.
space/whitespace, apostrophe/disallowed punct, non-ASCII letter for ASCII validator."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

ok = True
def must_reject(v, val, tag):
    global ok
    try:
        v(val); print("ACCEPTED (BAD)", tag, repr(val)); ok = False
    except ValidationError:
        print("Rejected (GOOD)", tag, repr(val))

va = ASCIIUsernameValidator()
vu = UnicodeUsernameValidator()
# whitespace between chars
must_reject(va, "a b", "ASCII-space")
must_reject(vu, "a\tb", "Unicode-tab")
# apostrophe / disallowed punctuation
must_reject(va, "O'Brien", "ASCII-apostrophe")
must_reject(vu, "a!b", "Unicode-bang")
# non-ASCII letter rejected by ASCII validator
must_reject(va, "Jérôme", "ASCII-nonascii")
# empty rejected (Req2.1 non-empty)
must_reject(va, "", "ASCII-empty")
must_reject(vu, "", "Unicode-empty")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.4: ASCII validator metadata unchanged — message text and ASCII-only flag (re.ASCII)."""
import re
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import ASCIIUsernameValidator

v = ASCIIUsernameValidator()
expected_msg = ("Enter a valid username. This value may contain only English letters, "
                "numbers, and @/./+/-/_ characters.")
ok = True
if str(v.message) != expected_msg:
    print("MESSAGE CHANGED (BAD):", repr(str(v.message))); ok = False
else:
    print("Message unchanged (GOOD)")
# ASCII-only matching mode: flags include re.ASCII
if not (v.flags & re.ASCII):
    print("ASCII flag missing (BAD): flags=", v.flags); ok = False
else:
    print("ASCII flag present (GOOD): flags=", v.flags)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req1.1): ASCIIUsernameValidator rejects a trailing-newline value.
Holds on patched, must FAIL at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError

v = ASCIIUsernameValidator()
val = "abc\n"
try:
    v(val)
    print("ACCEPTED trailing-newline value (BAD):", repr(val))
    raise SystemExit(1)
except ValidationError:
    print("Rejected trailing-newline value (GOOD):", repr(val))
    raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree.
- probe_1 (Req1.1, positive control): ASCII validator rejects 'abc\n'. HOLDS patched, VIOLATED at base (accepts) -> discriminates.
- probe_2 (Req1.2): Unicode validator rejects 'abc\n'. HOLDS patched, VIOLATED at base, VIOLATED under ascii-only weak patch.
- probe_3 (Req1.3/2.2): newline mid/leading rejected by both validators.
- probe_4 (Req3.1/3.2/3.3): legit ASCII, ASCII+punct, non-English-script Unicode usernames still accepted.
- probe_5 (Req4.1/4.2/4.3 + 2.1 non-empty): whitespace, apostrophe, disallowed punct, non-ASCII letter for ASCII validator, and empty string all rejected.
- probe_6 (Req3.4): ASCII validator message text unchanged and re.ASCII flag preserved.
Weak candidate (ascii-only partial fix) REJECTED by probe_2 -> suite discriminates a plausible incomplete fix that would not resolve hidden tests (Unicode validator still lets trailing newline through). Verdict SOUND: >=5 probes hold, positive control discriminates base vs patched, >=1 candidate exercised and rejected.

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
Weak candidate patches only ASCIIUsernameValidator's regex to \Z, leaving UnicodeUsernameValidator's trailing '$'. probe_2 (Req1.2) rejects it: UnicodeUsernameValidator still ACCEPTS 'abc\n' at base-with-partial-patch. This is a probe-conforming-in-part alternative the suite discriminates.
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
"""Positive control (Req1.1): ASCIIUsernameValidator rejects a trailing-newline value.
Holds on patched, must FAIL at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError

v = ASCIIUsernameValidator()
val = "abc\n"
try:
    v(val)
    print("ACCEPTED trailing-newline value (BAD):", repr(val))
    raise SystemExit(1)
except ValidationError:
    print("Rejected trailing-newline value (GOOD):", repr(val))
    raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree.
- probe_1 (Req1.1, positive control): ASCII validator rejects 'abc\n'. HOLDS patched, VIOLATED at base (accepts) -> discriminates.
- probe_2 (Req1.2): Unicode validator rejects 'abc\n'. HOLDS patched, VIOLATED at base, VIOLATED under ascii-only weak patch.
- probe_3 (Req1.3/2.2): newline mid/leading rejected by both validators.
- probe_4 (Req3.1/3.2/3.3): legit ASCII, ASCII+punct, non-English-script Unicode usernames still accepted.
- probe_5 (Req4.1/4.2/4.3 + 2.1 non-empty): whitespace, apostrophe, disallowed punct, non-ASCII letter for ASCII validator, and empty string all rejected.
- probe_6 (Req3.4): ASCII validator message text unchanged and re.ASCII flag preserved.
Weak candidate (ascii-only partial fix) REJECTED by probe_2 -> suite discriminates a plausible incomplete fix that would not resolve hidden tests (Unicode validator still lets trailing newline through). Verdict SOUND: >=5 probes hold, positive control discriminates base vs patched, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeling boundary is correct: requirements cover the full observable admissibility change (whole-value anchoring via \Z rejecting trailing newline) for BOTH validators, not just one branch/helper. R1 captures the core fix ($ matching before a trailing \n), R2 the end-to-end allowed-set semantics, R3 preserved acceptances incl. ASCII-flag/message metadata, R4 preserved rejections. No requirement mandates behavior absent in the patch, forbids present behavior, or invents behavior. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The problem_statement is unusually complete: it names both validator classes (ASCIIUsernameValidator, UnicodeUsernameValidator), their package (django.contrib.auth.validators), the exact defective regex r'^[\w.@+-]+$', the $-matches-trailing-newline quirk, the allowed character set (alphanumerics + .@+-), and even the gold fix (\A...\Z). Thus the one gold-edit artifact and all identifiers are already public. requirements.md translates test-checked behaviors into generic properties: rejects trailing newline, accepts end-to-end-allowed values, preserves acceptance of legit usernames (mixed case, letter+punctuation, non-English script), preserves rejection of whitespace/apostrophe/non-ASCII-letter/visually-similar-unicode. These parallel the hidden test's case CATEGORIES but quote NO test values (no 'o''connell', 'jean marc', 'Eric', 'en-dash', 'trailingnewline\n'), no test/function/class names (test_ascii_validator, test_unicode_validator, UsernameValidatorsTests), no file path (tests/auth_tests/test_validators.py), no parametrization ids, and no fix-invented identifiers. Req 4.4's 'visually similar ... cannot be smuggled in on the basis of appearance' is the most test-shaped line (echoing zero-width/non-breaking/en-dash cases) but is phrased as a behavioral generalization, not an enumeration of those specific characters — legitimate behavioral translation, not test reconstruction. No leak beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
