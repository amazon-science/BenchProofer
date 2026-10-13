# P2 adversarial audit — django__django-16082

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_mod_decimal.py`, `probe_2_mod_float.py`, `probe_3_mod_autofield.py`, `probe_4_other_ops_regression.py`, `probe_5_mod_sametype.py`, `probe_6_null_fielderror.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_mod_decimal.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_mod_decimal.py` → holds on the patched tree (good)

```python
# Requirement 1, criteria 1 & 2: MOD of Integer/Decimal (both orders) -> DecimalField.
# POSITIVE CONTROL: must HOLD patched, FAIL at base.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import IntegerField, DecimalField
from django.db.models.expressions import Combinable, CombinedExpression, Expression

def out(lhs, conn, rhs):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    return e.output_field.__class__.__name__

ok = True
for lhs, rhs in [(IntegerField, DecimalField), (DecimalField, IntegerField)]:
    got = out(lhs, Combinable.MOD, rhs)
    print(f"MOD {lhs.__name__} % {rhs.__name__} -> {got}")
    if got != "DecimalField":
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_mod_float.py` → holds on the patched tree (good)

```python
# Requirement 1, criteria 3 & 4: MOD of Integer/Float (both orders) -> FloatField.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import IntegerField, FloatField
from django.db.models.expressions import Combinable, CombinedExpression, Expression

def out(lhs, conn, rhs):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    return e.output_field.__class__.__name__

ok = True
for lhs, rhs in [(IntegerField, FloatField), (FloatField, IntegerField)]:
    got = out(lhs, Combinable.MOD, rhs)
    print(f"MOD {lhs.__name__} % {rhs.__name__} -> {got}")
    if got != "FloatField":
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_mod_autofield.py` → holds on the patched tree (good)

```python
# Requirement 1, criterion 5: MOD of Integer/AutoField (both orders) -> IntegerField.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import IntegerField, AutoField
from django.db.models.expressions import Combinable, CombinedExpression, Expression

def out(lhs, conn, rhs):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    return e.output_field.__class__.__name__

ok = True
for lhs, rhs in [(IntegerField, AutoField), (AutoField, IntegerField)]:
    got = out(lhs, Combinable.MOD, rhs)
    print(f"MOD {lhs.__name__} % {rhs.__name__} -> {got}")
    if got != "IntegerField":
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_other_ops_regression.py` → holds on the patched tree (good)

```python
# Requirement 2: existing ADD/SUB/MUL/DIV still resolve mixed numeric types,
# and same-type combinations still resolve to that type. (SHALL keep regression.)
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import IntegerField, DecimalField, FloatField, AutoField
from django.db.models.expressions import Combinable, CombinedExpression, Expression

def out(lhs, conn, rhs):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    return e.output_field.__class__.__name__

ops = [Combinable.ADD, Combinable.SUB, Combinable.MUL, Combinable.DIV]
mixed = [
    (IntegerField, DecimalField, "DecimalField"),
    (DecimalField, IntegerField, "DecimalField"),
    (IntegerField, FloatField, "FloatField"),
    (FloatField, IntegerField, "FloatField"),
    (IntegerField, AutoField, "IntegerField"),
    (AutoField, IntegerField, "IntegerField"),
]
same = [
    (IntegerField, "IntegerField"),
    (DecimalField, "DecimalField"),
    (FloatField, "FloatField"),
]
ok = True
for op in ops:
    for lhs, rhs, exp in mixed:
        got = out(lhs, op, rhs)
        print(f"{op} {lhs.__name__}/{rhs.__name__} -> {got} (exp {exp})")
        if got != exp:
            ok = False
    for f, exp in same:
        got = out(f, op, f)
        print(f"{op} {f.__name__}/{f.__name__} -> {got} (exp {exp})")
        if got != exp:
            ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_mod_sametype.py` → holds on the patched tree (good)

```python
# Requirement 2 criterion 2 (applied to MOD) + Req1 criterion 6 consistency:
# MOD of same numeric types resolves to that type (int%int->int, dec%dec->dec,
# float%float->float). These were already supported same-type combos.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import IntegerField, DecimalField, FloatField
from django.db.models.expressions import Combinable, CombinedExpression, Expression

def out(lhs, conn, rhs):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    return e.output_field.__class__.__name__

ok = True
for f, exp in [(IntegerField, "IntegerField"), (DecimalField, "DecimalField"), (FloatField, "FloatField")]:
    got = out(f, Combinable.MOD, f)
    print(f"MOD {f.__name__}/{f.__name__} -> {got} (exp {exp})")
    if got != exp:
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_null_fielderror.py` → holds on the patched tree (good)

```python
# Requirement 3: numeric-with-null combinations with no registered result type
# STILL raise FieldError (both for MOD and for ADD). SHALL NOT silently resolve.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import AutoField, IntegerField, Value
from django.db.models.expressions import Combinable, CombinedExpression, Expression
from django.core.exceptions import FieldError

# Operands are wrapped exactly as the gold test does: Expression(field()).
def null():
    return Value(None)  # a null-typed operand (NullField)

def check(lhs, conn, rhs, label):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    try:
        of = e.output_field
        print(f"{label}: NO ERROR, got {of.__class__.__name__} (expected FieldError)")
        return False
    except FieldError as exc:
        msg = str(exc)
        print(f"{label}: FieldError: {msg}")
        # Req3: message states the type of the expression involving those types
        # cannot be inferred. Django phrases this as:
        #   "Cannot infer type of {connector!r} expression involving these types: ..."
        return ("involving these types" in msg) and ("infer" in msg.lower())

ok = True
# AutoField + null : unregistered -> FieldError (Req3 criterion 1 example)
ok &= check(AutoField, Combinable.ADD, null, "AutoField + Null (ADD)")
# null + IntegerField : unregistered -> FieldError (from gold test list)
ok &= check(null, Combinable.ADD, IntegerField, "Null + IntegerField (ADD)")
# AutoField % null : MOD must not have introduced a resolution here
ok &= check(AutoField, Combinable.MOD, null, "AutoField % Null (MOD)")
# IntegerField % null : MOD null combo still unresolved
ok &= check(IntegerField, Combinable.MOD, null, "IntegerField % Null (MOD)")

import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_mod_decimal.py`

```python
# Requirement 1, criteria 1 & 2: MOD of Integer/Decimal (both orders) -> DecimalField.
# POSITIVE CONTROL: must HOLD patched, FAIL at base.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import IntegerField, DecimalField
from django.db.models.expressions import Combinable, CombinedExpression, Expression

def out(lhs, conn, rhs):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    return e.output_field.__class__.__name__

ok = True
for lhs, rhs in [(IntegerField, DecimalField), (DecimalField, IntegerField)]:
    got = out(lhs, Combinable.MOD, rhs)
    print(f"MOD {lhs.__name__} % {rhs.__name__} -> {got}")
    if got != "DecimalField":
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16082: gold adds Combinable.MOD to the mixed-numeric-type registry in django/db/models/expressions.py so CombinedExpression.output_field resolves MOD like ADD/SUB/MUL/DIV.

Probe suite (all run in the instance Docker image; operands wrapped Expression(field()) exactly as the gold test):
- probe_1_mod_decimal (Req1 c1,c2 — POSITIVE CONTROL): int%dec and dec%int -> DecimalField. FAIL at base (base raises FieldError 'Cannot infer type of \'%%\' expression...'), HOLD patched. Discriminates.
- probe_2_mod_float (Req1 c3,c4): int%float and float%int -> FloatField. FAIL at base, HOLD patched.
- probe_3_mod_autofield (Req1 c5): int%auto and auto%int -> IntegerField. HOLDS at base and patched (AutoField same-type-integer combos already covered) — regression-style criterion.
- probe_4_other_ops_regression (Req2 c1,c2 — SHALL keep): ADD/SUB/MUL/DIV over all mixed pairs + same-type; HOLDS base and patched (patch does not touch them).
- probe_5_mod_sametype (Req2 c2 / Req1 c6): int%int,dec%dec,float%float -> same type; HOLDS.
- probe_6_null_fielderror (Req3 c1,c2,c3): AutoField+Null(ADD), Null+Int(ADD), Auto%Null(MOD), Int%Null(MOD) all raise FieldError with 'involving these types'; HOLDS base and patched — no null combo silently resolved, MOD did not introduce a null resolution.

CANDIDATE PATCH weak_partial.diff (naive partial fix a weak reading permits — registers MOD only for the decimal mixed pair, omitting float and auto): probe_2_mod_float REJECTS it (VIOLATED: int%float still raises FieldError). This proves the suite discriminates a wrong/partial implementation. Because a probe-conforming patch must register ALL six mixed MOD promotions (int/dec both orders, int/float both orders, int/auto both orders) — exactly the gold behavior encoded by the F2P test_resolve_output_field_number — there is no requirements-conforming patch that would fail the hidden tests. No too-weak finding.

Verdict SOUND: 6 distinct probes all hold on the patched tree; positive control (probe_1) fails at base and holds patched (prepatch reproduced); >=1 candidate patch exercised and rejected (weak_partial rejected by probe_2).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_mod_decimal.py`, `probe_2_mod_float.py`, `probe_3_mod_autofield.py`, `probe_4_other_ops_regression.py`, `probe_5_mod_sametype.py`, `probe_6_null_fielderror.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_mod_decimal.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_mod_decimal.py` → holds on the patched tree (good)

Attack 2 — `probe_2_mod_float.py` → holds on the patched tree (good)

Attack 3 — `probe_3_mod_autofield.py` → holds on the patched tree (good)

Attack 4 — `probe_4_other_ops_regression.py` → holds on the patched tree (good)

Attack 5 — `probe_5_mod_sametype.py` → holds on the patched tree (good)

Attack 6 — `probe_6_null_fielderror.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_mod_decimal.py`

```python
# Requirement 1, criteria 1 & 2: MOD of Integer/Decimal (both orders) -> DecimalField.
# POSITIVE CONTROL: must HOLD patched, FAIL at base.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import IntegerField, DecimalField
from django.db.models.expressions import Combinable, CombinedExpression, Expression

def out(lhs, conn, rhs):
    e = CombinedExpression(Expression(lhs()), conn, Expression(rhs()))
    return e.output_field.__class__.__name__

ok = True
for lhs, rhs in [(IntegerField, DecimalField), (DecimalField, IntegerField)]:
    got = out(lhs, Combinable.MOD, rhs)
    print(f"MOD {lhs.__name__} % {rhs.__name__} -> {got}")
    if got != "DecimalField":
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16082: gold adds Combinable.MOD to the mixed-numeric-type registry in django/db/models/expressions.py so CombinedExpression.output_field resolves MOD like ADD/SUB/MUL/DIV.

Probe suite (all run in the instance Docker image; operands wrapped Expression(field()) exactly as the gold test):
- probe_1_mod_decimal (Req1 c1,c2 — POSITIVE CONTROL): int%dec and dec%int -> DecimalField. FAIL at base (base raises FieldError 'Cannot infer type of \'%%\' expression...'), HOLD patched. Discriminates.
- probe_2_mod_float (Req1 c3,c4): int%float and float%int -> FloatField. FAIL at base, HOLD patched.
- probe_3_mod_autofield (Req1 c5): int%auto and auto%int -> IntegerField. HOLDS at base and patched (AutoField same-type-integer combos already covered) — regression-style criterion.
- probe_4_other_ops_regression (Req2 c1,c2 — SHALL keep): ADD/SUB/MUL/DIV over all mixed pairs + same-type; HOLDS base and patched (patch does not touch them).
- probe_5_mod_sametype (Req2 c2 / Req1 c6): int%int,dec%dec,float%float -> same type; HOLDS.
- probe_6_null_fielderror (Req3 c1,c2,c3): AutoField+Null(ADD), Null+Int(ADD), Auto%Null(MOD), Int%Null(MOD) all raise FieldError with 'involving these types'; HOLDS base and patched — no null combo silently resolved, MOD did not introduce a null resolution.

CANDIDATE PATCH weak_partial.diff (naive partial fix a weak reading permits — registers MOD only for the decimal mixed pair, omitting float and auto): probe_2_mod_float REJECTS it (VIOLATED: int%float still raises FieldError). This proves the suite discriminates a wrong/partial implementation. Because a probe-conforming patch must register ALL six mixed MOD promotions (int/dec both orders, int/float both orders, int/auto both orders) — exactly the gold behavior encoded by the F2P test_resolve_output_field_number — there is no requirements-conforming patch that would fail the hidden tests. No too-weak finding.

Verdict SOUND: 6 distinct probes all hold on the patched tree; positive control (probe_1) fails at base and holds patched (prepatch reproduced); >=1 candidate patch exercised and rejected (weak_partial rejected by probe_2).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: the requirements pin the changed observable behavior (MOD mixed-numeric-type output_field resolution across all promotion pairs) rather than a single branch or the leaf helper. Minor cosmetic gap: Req3.1 paraphrases the FieldError message as stating the type 'cannot be inferred', while the actual raised message is 'Cannot resolve expression type, unknown output_field'. This is not a faithfulness break — a FieldError is genuinely raised for numeric-with-null unregistered combos (verified via CombinedExpression(Value(int), MOD/ADD, Value(None)).output_field), and the requirement does not mandate the exact wording. No requirement mandates behavior the patched code lacks, forbids behavior it has, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit is a single line adding Combinable.MOD to the arithmetic-operator registry tuple; the hidden tests are test_resolve_output_field_number (parametrized over numeric field-type combos × connectors, now including MOD) and test_resolve_output_field_with_null. The requirements document names only genuine source identifiers (CombinedExpression, _resolve_combined_type, Combinable, ADD/SUB/MUL/DIV/MOD/POW, IntegerField/DecimalField/FloatField/AutoField, FieldError) — legitimate localization, none fix-invented. The public problem_statement already states MOD should resolve mixed numeric types (Decimal/Integer) like other math operators. Req 1's fuller enumeration (Int×Dec, Dec×Int, Int×Float, Float×Int, Int×AutoField) and Req 3's null cases go beyond the single problem-statement example and do parallel the test parametrization, BUT they describe the actual type-promotion semantics of the registry that the fix activates — i.e., behavioral requirements, which is the intended translation. No test file paths, test/class/function names, parametrization ids, subTest usage, or verbatim test/gold code are transmitted. No content is derivable only from the hidden tests rather than from the source behavior.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
