# P2 adversarial audit — django__django-13023

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

Counterexample / evidence:

```
Weak candidate (catch only TypeError, omit ValueError) leaks a raw ValueError for list/tuple values ([] and ()): 'argument must be a sequence of length 3'. Rejected by probe_2 (Req1.2) and probe_4 (Req1.5).
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1/1.3 positive control: dict (no decimal interpretation) -> ValidationError, not TypeError."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()

from django.core.exceptions import ValidationError
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
try:
    f.to_python({})
    print("NO EXCEPTION raised for dict")
    raise SystemExit(1)
except ValidationError as e:
    print("ValidationError raised for dict:", e.messages)
    raise SystemExit(0)
except TypeError as e:
    print("RAW TypeError leaked:", e)
    raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2: undecodable value -> code='invalid' with value param in message."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()
from django.core.exceptions import ValidationError
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
ok = True
for v in [{}, [], object(), complex(1, 2)]:
    try:
        f.to_python(v)
        print("no error for", type(v)); ok = False
    except ValidationError as e:
        code = e.error_list[0].code
        params = e.error_list[0].params or {}
        msg = e.messages[0]
        if code != 'invalid':
            print("wrong code", code); ok = False
        if params.get('value') != v:
            print("value param not carried for", type(v), params); ok = False
        if str(v) not in msg:
            print("value not in rendered message:", msg); ok = False
        else:
            print("OK", type(v).__name__, "code=invalid value-in-msg:", msg)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4: malformed textual/byte-string -> ValidationError (not raw error)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()
from django.core.exceptions import ValidationError
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
ok = True
for v in ['non-numeric string', b'non-numeric byte-string']:
    try:
        f.to_python(v)
        print("no error for", repr(v)); ok = False
    except ValidationError as e:
        print("ValidationError for", repr(v), "code=", e.error_list[0].code)
        if e.error_list[0].code != 'invalid':
            ok = False
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req1.5: Field.clean(undecodable) -> ValidationError identifying value, regardless of type.
Also covers the full hidden-test value list."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()
from django.core.exceptions import ValidationError
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
values = [(), [], {}, set(), object(), complex(), 'non-numeric string', b'non-numeric byte-string']
ok = True
for v in values:
    try:
        f.clean(v, None)
        print("clean did NOT raise for", type(v).__name__); ok = False
    except ValidationError as e:
        msg = e.messages[0]
        if str(v) not in msg:
            print("value not identified in message for", type(v).__name__, ":", msg); ok = False
        else:
            print("OK clean", type(v).__name__, "->", msg)
    except (TypeError, ValueError) as e:
        print("RAW low-level leaked from clean for", type(v).__name__, ":", e); ok = False
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2: pass-through/valid values unchanged. None, float (ROUND_HALF_EVEN, max_digits precision),
int, numeric string, trailing zeros; get_prep_value(None)->None, numeric string->Decimal."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()
import decimal
from decimal import Decimal
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
ok = True

if f.to_python(None) is not None:
    print("to_python(None) != None"); ok = False
else:
    print("OK None passthrough")

# float: honors max_digits as precision with ROUND_HALF_EVEN (context-based conversion).
# Compare against the canonical context to avoid pinning a wrong specific literal.
ctx = decimal.Context(prec=f.max_digits, rounding=decimal.ROUND_HALF_EVEN)
for fv in [1.23456, 12.345, 2.675, 0.1]:
    got = f.to_python(fv)
    want = ctx.create_decimal_from_float(fv)
    if got != want:
        print("float conv wrong for", fv, "got", got, "want", want); ok = False
    else:
        print("OK float conv", fv, "->", got)
# precision must equal max_digits significant digits for a 6-sig input
sig = len(f.to_python(1.23456).as_tuple().digits)
if sig != f.max_digits:
    print("float precision != max_digits sig digits:", sig); ok = False
else:
    print("OK float precision sig-digits == max_digits:", sig)

if f.to_python(5) != Decimal('5'):
    print("int wrong"); ok = False
else:
    print("OK int")

if f.to_python('3.14') != Decimal('3.14'):
    print("numeric str wrong"); ok = False
else:
    print("OK numeric str")

# trailing zeros preserved
tz = f.to_python('1.10')
if tz.as_tuple().exponent != -2:
    print("trailing zero not preserved:", tz, tz.as_tuple()); ok = False
else:
    print("OK trailing zeros preserved:", tz)

if f.get_prep_value(None) is not None:
    print("get_prep_value(None) != None"); ok = False
else:
    print("OK get_prep_value(None)")

if f.get_prep_value('2.50') != Decimal('2.50'):
    print("get_prep_value numeric str wrong:", f.get_prep_value('2.50')); ok = False
else:
    print("OK get_prep_value numeric str")

raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.1: preparing a huge integer for a query lookup succeeds (no raise),
even beyond declared precision. Uses get_prep_value / get_db_prep_value path."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()
from decimal import Decimal
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
big = 10 ** 30  # well beyond max_digits=4
try:
    r = f.get_prep_value(big)
    print("get_prep_value(bigint) ->", r)
    if r != Decimal(big):
        print("wrong value"); raise SystemExit(1)
except Exception as e:
    print("RAISED on big int prep:", type(e).__name__, e)
    raise SystemExit(1)
raise SystemExit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req4: range validation preserved. max_digits, decimal_places, whole-digit limits still raise
ValidationError with appropriate codes; valid value cleans fine."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
ok = True

def codes(v):
    try:
        f.clean(v, None)
        return None
    except ValidationError as e:
        return [x.code for x in e.error_list]

# too many total digits (max_digits=4)
c = codes(Decimal('123.45'))  # 5 digits
if not c or 'max_digits' not in c:
    print("max_digits not enforced:", c); ok = False
else:
    print("OK max_digits:", c)

# too many decimal places
c = codes(Decimal('1.234'))
if not c or 'max_decimal_places' not in c:
    print("max_decimal_places not enforced:", c); ok = False
else:
    print("OK max_decimal_places:", c)

# too many whole digits
c = codes(Decimal('123'))
if not c or 'max_whole_digits' not in c:
    print("max_whole_digits not enforced:", c); ok = False
else:
    print("OK max_whole_digits:", c)

# valid value passes
try:
    f.clean(Decimal('12.34'), None)
    print("OK valid cleans")
except ValidationError as e:
    print("valid value wrongly rejected:", e.messages); ok = False

raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1/1.3 positive control: dict (no decimal interpretation) -> ValidationError, not TypeError."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()

from django.core.exceptions import ValidationError
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
try:
    f.to_python({})
    print("NO EXCEPTION raised for dict")
    raise SystemExit(1)
except ValidationError as e:
    print("ValidationError raised for dict:", e.messages)
    raise SystemExit(0)
except TypeError as e:
    print("RAW TypeError leaked:", e)
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 distinct probes, all HOLD on the gold-patched tree. Positive control (probe_1: dict -> ValidationError not raw TypeError) HOLDS patched and FAILS at base (base leaks 'conversion from dict to Decimal is not supported'), so it discriminates. Coverage: Req1.1/1.3 (probe_1), Req1.2 code='invalid'+value param+rendered message (probe_2), Req1.4 malformed str/bytes (probe_3), Req1.5 Field.clean over full type list ()/[]/{}/set/object/complex/str/bytes (probe_4), Req2 pass-through None/float(context precision=max_digits, ROUND_HALF_EVEN)/int/numeric-str/trailing-zeros/get_prep_value (probe_5), Req3.1 huge-int query prep no crash (probe_6), Req4 range validation max_digits/decimal_places/whole_digits preserved (probe_7).

Wrong-fix candidate 'catch only TypeError' was exercised under --patch and REJECTED by probes 2 & 4, demonstrating the suite discriminates the lazy partial fix a weak reading permits. Note: meta.json records G-PANEL-3=fail (leakage — the requirements enumerate the exact hidden-test value list tuple/list/dict/set/object/complex/bytes and Req3's very-large-integer case, derivable only from the hidden test_patch, not the public dict-only problem statement); that is a leakage concern, not a spec-fidelity/too-weak defect, and is outside this G-EQ (spec-too-weak) verdict.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (catch only TypeError, omit ValueError) leaks a raw ValueError for list/tuple values ([] and ()): 'argument must be a sequence of length 3'. Rejected by probe_2 (Req1.2) and probe_4 (Req1.5).
```

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
"""Req1.1/1.3 positive control: dict (no decimal interpretation) -> ValidationError, not TypeError."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False)
django.setup()

from django.core.exceptions import ValidationError
from django.db.models import DecimalField

f = DecimalField(max_digits=4, decimal_places=2)
try:
    f.to_python({})
    print("NO EXCEPTION raised for dict")
    raise SystemExit(1)
except ValidationError as e:
    print("ValidationError raised for dict:", e.messages)
    raise SystemExit(0)
except TypeError as e:
    print("RAW TypeError leaked:", e)
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 distinct probes, all HOLD on the gold-patched tree. Positive control (probe_1: dict -> ValidationError not raw TypeError) HOLDS patched and FAILS at base (base leaks 'conversion from dict to Decimal is not supported'), so it discriminates. Coverage: Req1.1/1.3 (probe_1), Req1.2 code='invalid'+value param+rendered message (probe_2), Req1.4 malformed str/bytes (probe_3), Req1.5 Field.clean over full type list ()/[]/{}/set/object/complex/str/bytes (probe_4), Req2 pass-through None/float(context precision=max_digits, ROUND_HALF_EVEN)/int/numeric-str/trailing-zeros/get_prep_value (probe_5), Req3.1 huge-int query prep no crash (probe_6), Req4 range validation max_digits/decimal_places/whole_digits preserved (probe_7).

Wrong-fix candidate 'catch only TypeError' was exercised under --patch and REJECTED by probes 2 & 4, demonstrating the suite discriminates the lazy partial fix a weak reading permits. Note: meta.json records G-PANEL-3=fail (leakage — the requirements enumerate the exact hidden-test value list tuple/list/dict/set/object/complex/bytes and Req3's very-large-integer case, derivable only from the hidden test_patch, not the public dict-only problem statement); that is a leakage concern, not a spec-fidelity/too-weak defect, and is outside this G-EQ (spec-too-weak) verdict.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirement boundary is correct and biconditional: it pins the CHANGED observable behavior (uniform ValidationError for TypeError AND ValueError AND InvalidOperation decode failures, exposing value param) rather than a narrow slice like only the dict case from the issue. Req 1.3 correctly names TypeError (dict/object) and 1.4 correctly names ValueError-inducing text (byte-string/malformed str) — both new except branches. Reqs 2-4 correctly preserve pass-through/range validation which the patch does not touch. Minor non-normative imperfection: Req 2.2's parenthetical 'e.g. ... yields three significant digits' is arithmetically wrong (max_digits=4 => precision-4 context => 1.234 has four sig digits), but this is an illustrative 'e.g.' whose governing normative clause ('honoring max_digits as the precision') is correct, and it concerns unchanged pass-through behavior outside the patched boundary. Not enough to flag UNFAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate test-checked behavior into behavioral criteria rather than transmitting the tests. The hidden test enumerates a parametrized list ((), [], {}, set(), object(), complex(), 'non-numeric string', b'non-numeric byte-string') applied via field.clean(value, None) with msg '"%s" value must be a decimal number.', plus test_lookup_really_big_value. The document does NOT reconstruct this: it generalizes to 'non-numeric object or container' and 'a string, or a byte-string' (genuine behavioral distinctions between TypeError/ValueError-raising types and malformed-literal InvalidOperation), never spelling out the tuple/list/set/complex cases as a mirror of the parametrization. No test names/paths/ids, no quoted test or gold code, no fix-invented identifiers. Named symbols (to_python, get_prep_value, clean, file path, error code 'invalid', 'value' message param) are pre-existing Django API used for legitimate localization, not gold-invented. Borderline but acceptable: Req 2.2's max_digits=4/decimal_places=2 example matches the test's field config, but it is used as a generic illustration of ROUND_HALF_EVEN precision behavior (a common example), not a reconstruction of hidden assertions. Req 3.1's 'integers too large to fit' renders test_lookup_really_big_value behaviorally without leaking its name/code.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
