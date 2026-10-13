# P2 adversarial audit — django__django-11815

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / R1.1: an enum member serializes to
`<module>.<ClassName>[<name-repr>]` subscript form, NOT call-by-value form.
Uses re.RegexFlag.DOTALL (a real importable enum). Patched -> "re.RegexFlag['DOTALL']";
base -> "re.RegexFlag(16)".
"""
import re
from django.db.migrations.serializer import serializer_factory

val = re.RegexFlag.DOTALL
s, imports = serializer_factory(val).serialize()
print("serialized:", repr(s))
print("imports:", imports)

expected = "re.RegexFlag['DOTALL']"
ok = (s == expected)
# extra structural guards
ok = ok and s.endswith("['DOTALL']") and "(" not in s
print("expected:", repr(expected), "ok:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2 + R1.3 + R1.4: rendered text does not contain the stored value in any
form, and imports are exactly {import <module>}. Uses a custom str-valued enum
whose value is a distinctive sentinel string so we can assert it is absent.
Also tests type-independence: str, int, bytes value enums all render by name.
"""
import enum
import datetime
from django.db.migrations.serializer import serializer_factory


class StrEnum(enum.Enum):
    ALPHA = "VALUE_SENTINEL_XYZ"


class IntEnum(enum.Enum):
    ONE = 12345


class BytesEnum(enum.Enum):
    B = b"BYTES_SENTINEL"


class DateEnum(enum.Enum):
    # value type that itself needs an import to reconstruct -> exercises R1.3:
    # the rendered imports must NOT include the value-only 'import datetime'.
    D = datetime.date(2020, 1, 2)


ok = True
for E, member, name, forbidden in [
    (StrEnum, StrEnum.ALPHA, "ALPHA", ["VALUE_SENTINEL_XYZ"]),
    (IntEnum, IntEnum.ONE, "ONE", ["12345"]),
    (BytesEnum, BytesEnum.B, "B", ["BYTES_SENTINEL", "b'"]),
    (DateEnum, DateEnum.D, "D", ["2020", "datetime.date("]),
]:
    s, imports = serializer_factory(member).serialize()
    print(name, "->", repr(s), imports)
    # name-based subscript form, key is the member name repr
    if not s.endswith("[%r]" % name):
        print("  FAIL: not subscript by name"); ok = False
    if "(" in s:
        print("  FAIL: call form present"); ok = False
    for f in forbidden:
        if f in s:
            print("  FAIL: value leaked:", f); ok = False
    mod = E.__module__
    if imports != {"import %s" % mod}:
        print("  FAIL: imports not exactly {import module}:", imports); ok = False

raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.5 + R2.3: round-trip fidelity for an enum member, including a flag/int
enum that also subclasses a built-in type (re.RegexFlag). Executing the emitted
source (with declared imports) reproduces the exact same member.
"""
import re
from django.db.migrations.serializer import serializer_factory

ok = True
for val in [re.RegexFlag.DOTALL, re.RegexFlag.IGNORECASE]:
    s, imports = serializer_factory(val).serialize()
    print("val", val, "->", repr(s), imports)
    ns = {}
    for imp in imports:
        exec(imp, ns)
    got = eval(s, ns)
    print("   round-trip ->", got, "is same:", got is val)
    if got is not val:
        print("   FAIL round-trip"); ok = False
    # flag/int enum still rendered by name, not call
    if "(" in s or not s.endswith("[%r]" % val.name):
        print("   FAIL not name-subscript form"); ok = False

raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.1 + R2.2: full field serialization via MigrationWriter. A CharField whose
default is an enum member emits default=<module>.<ClassName>['NAME']; a field
whose choices contain enum members renders each member by name while the display
component serializes by its own rules.
"""
import enum
from django.db import models
from django.db.migrations.writer import MigrationWriter


class Suit(enum.Enum):
    HEARTS = "he value translated"
    SPADES = "sp value translated"


ok = True

# default=
f = models.CharField(default=Suit.HEARTS, max_length=1)
s, imports = MigrationWriter.serialize(f)
print("default field ->", s)
if "Suit['HEARTS']" not in s:
    print("  FAIL default not name-based"); ok = False
if "he value translated" in s:
    print("  FAIL default leaked value"); ok = False

# choices=
f2 = models.CharField(
    choices=[(Suit.HEARTS, "Hearts label"), (Suit.SPADES, "Spades label")],
    max_length=1,
)
s2, imports2 = MigrationWriter.serialize(f2)
print("choices field ->", s2)
if "Suit['HEARTS']" not in s2 or "Suit['SPADES']" not in s2:
    print("  FAIL choices members not name-based"); ok = False
if "Hearts label" not in s2 or "Spades label" not in s2:
    print("  FAIL choices display component not serialized normally"); ok = False
if "he value translated" in s2:
    print("  FAIL choices leaked enum value"); ok = False

raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.1 + R3.2 + R3.3: non-enum values serialize unchanged and round-trip.
Checks a plain string, an int, bytes, and a compiled regex. These must produce
the standard expected source and imports (unaffected by the enum change).
"""
import re
from django.db.migrations.serializer import serializer_factory

ok = True

cases = [
    ("hello", "'hello'", set()),
    (42, "42", set()),
    (b"abc", "b'abc'", set()),
]
for val, expect_src, expect_imp in cases:
    s, imports = serializer_factory(val).serialize()
    print(repr(val), "->", repr(s), imports)
    if s != expect_src:
        print("  FAIL src changed"); ok = False
    if imports != expect_imp:
        print("  FAIL imports changed"); ok = False
    ns = {}
    for imp in imports:
        exec(imp, ns)
    if eval(s, ns) != val:
        print("  FAIL round-trip"); ok = False

# compiled regex
rx = re.compile(r"ab+c", re.IGNORECASE)
s, imports = serializer_factory(rx).serialize()
print("regex ->", repr(s), imports)
ns = {}
for imp in imports:
    exec(imp, ns)
got = eval(s, ns)
if not (got.pattern == rx.pattern and got.flags == rx.flags):
    print("  FAIL regex round-trip"); ok = False
if "re.compile" not in s:
    print("  FAIL regex not via re.compile"); ok = False

raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.4 + R3.1: class-based (deconstructible) validator continues to render via
its deconstructed import path and args, and dispatch still routes it to the
deconstructible serializer (NOT the enum serializer). Also confirm round-trip.
"""
from django.core.validators import RegexValidator
from django.db.migrations.serializer import serializer_factory, DeconstructableSerializer

ok = True
v = RegexValidator(regex=r"\d+", message="must be digits")

# dispatch: deconstructible -> DeconstructableSerializer (unchanged routing)
ser = serializer_factory(v)
print("serializer class:", type(ser).__name__)
if not isinstance(ser, DeconstructableSerializer):
    print("  FAIL wrong serializer dispatched"); ok = False

s, imports = ser.serialize()
print("validator ->", repr(s), imports)
if "django.core.validators.RegexValidator" not in s:
    print("  FAIL not deconstructed import path"); ok = False
if not any("import django.core.validators" in i for i in imports):
    print("  FAIL import missing"); ok = False
if "regex=" not in s or "message=" not in s:
    print("  FAIL args not rendered"); ok = False

# round-trip
ns = {}
for imp in imports:
    exec(imp, ns)
got = eval(s, ns)
if not (got.regex.pattern == v.regex.pattern and got.message == v.message):
    print("  FAIL round-trip"); ok = False
else:
    print("  round-trip OK")

raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / R1.1: an enum member serializes to
`<module>.<ClassName>[<name-repr>]` subscript form, NOT call-by-value form.
Uses re.RegexFlag.DOTALL (a real importable enum). Patched -> "re.RegexFlag['DOTALL']";
base -> "re.RegexFlag(16)".
"""
import re
from django.db.migrations.serializer import serializer_factory

val = re.RegexFlag.DOTALL
s, imports = serializer_factory(val).serialize()
print("serialized:", repr(s))
print("imports:", imports)

expected = "re.RegexFlag['DOTALL']"
ok = (s == expected)
# extra structural guards
ok = ok and s.endswith("['DOTALL']") and "(" not in s
print("expected:", repr(expected), "ok:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Audited django__django-11815 (EnumSerializer: render enum members by name via subscript lookup). 6 probes, all HOLD on gold-patched tree; positive control discriminates base vs patched.

Probes -> requirement:
- probe_1 (R1.1, POSITIVE CONTROL): re.RegexFlag.DOTALL serializes to "re.RegexFlag['DOTALL']" (subscript-by-name, no call). HOLDS patched; at base gives "re.RegexFlag(16)" -> FAILS. Discriminates.
- probe_2 (R1.2/R1.3/R1.4): str/int/bytes/date-valued enums all render `<mod>.<Cls>['NAME']`; rendered text never contains the stored value; imports are EXACTLY {import <module>}. The DateEnum case (value=datetime.date) exercises R1.3 'no value-only import'. HOLDS patched.
- probe_3 (R1.5/R2.3): round-trip fidelity; flag/int enum (re.RegexFlag) rendered by name and re-executes to the same member. HOLDS.
- probe_4 (R2.1/R2.2): via MigrationWriter, CharField default enum -> default=...['HEARTS']; choices enum members rendered by name while display labels serialize normally; no leaked value. HOLDS.
- probe_5 (R3.1/R3.2/R3.3): non-enum values (str/int/bytes/compiled regex) serialize to identical expected source+imports and round-trip. HOLDS.
- probe_6 (R3.4/R3.1): deconstructible RegexValidator dispatched to DeconstructableSerializer (routing unchanged), rendered via deconstructed import path+args, round-trips. HOLDS.

Candidate wrong patches (REQUIRED floor, both REJECTED by suite):
- weak_stronly.diff: lazy 'str-only' fix (name-subscript only when value is str, else old call form). REJECTED by probe_1, probe_2, probe_3 (re.RegexFlag int value still renders as (16)). This is exactly the naive reading a weak spec would permit, and it would not resolve the hidden re.RegexFlag F2P test.
- weak_imports.diff: renders name-subscript form but KEEPS the value-derived imports (imports = {import module, *v_imports}). REJECTED by probe_2 via the DateEnum case (imports contained a spurious 'import datetime'), directly demonstrating R1.3 discrimination.

All needed runs completed in the official image. Note: this bundle's G-PANEL-3 is a fail (leakage: re.RegexFlag named in prose reconstructs the hidden validator test) — that is a leakage judgment, orthogonal to G-EQ spec-fidelity, which is SOUND: >=5 probes hold, positive control discriminates, and >=1 requirements-permitted wrong candidate is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control / R1.1: an enum member serializes to
`<module>.<ClassName>[<name-repr>]` subscript form, NOT call-by-value form.
Uses re.RegexFlag.DOTALL (a real importable enum). Patched -> "re.RegexFlag['DOTALL']";
base -> "re.RegexFlag(16)".
"""
import re
from django.db.migrations.serializer import serializer_factory

val = re.RegexFlag.DOTALL
s, imports = serializer_factory(val).serialize()
print("serialized:", repr(s))
print("imports:", imports)

expected = "re.RegexFlag['DOTALL']"
ok = (s == expected)
# extra structural guards
ok = ok and s.endswith("['DOTALL']") and "(" not in s
print("expected:", repr(expected), "ok:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Audited django__django-11815 (EnumSerializer: render enum members by name via subscript lookup). 6 probes, all HOLD on gold-patched tree; positive control discriminates base vs patched.

Probes -> requirement:
- probe_1 (R1.1, POSITIVE CONTROL): re.RegexFlag.DOTALL serializes to "re.RegexFlag['DOTALL']" (subscript-by-name, no call). HOLDS patched; at base gives "re.RegexFlag(16)" -> FAILS. Discriminates.
- probe_2 (R1.2/R1.3/R1.4): str/int/bytes/date-valued enums all render `<mod>.<Cls>['NAME']`; rendered text never contains the stored value; imports are EXACTLY {import <module>}. The DateEnum case (value=datetime.date) exercises R1.3 'no value-only import'. HOLDS patched.
- probe_3 (R1.5/R2.3): round-trip fidelity; flag/int enum (re.RegexFlag) rendered by name and re-executes to the same member. HOLDS.
- probe_4 (R2.1/R2.2): via MigrationWriter, CharField default enum -> default=...['HEARTS']; choices enum members rendered by name while display labels serialize normally; no leaked value. HOLDS.
- probe_5 (R3.1/R3.2/R3.3): non-enum values (str/int/bytes/compiled regex) serialize to identical expected source+imports and round-trip. HOLDS.
- probe_6 (R3.4/R3.1): deconstructible RegexValidator dispatched to DeconstructableSerializer (routing unchanged), rendered via deconstructed import path+args, round-trips. HOLDS.

Candidate wrong patches (REQUIRED floor, both REJECTED by suite):
- weak_stronly.diff: lazy 'str-only' fix (name-subscript only when value is str, else old call form). REJECTED by probe_1, probe_2, probe_3 (re.RegexFlag int value still renders as (16)). This is exactly the naive reading a weak spec would permit, and it would not resolve the hidden re.RegexFlag F2P test.
- weak_imports.diff: renders name-subscript form but KEEPS the value-derived imports (imports = {import module, *v_imports}). REJECTED by probe_2 via the DateEnum case (imports contained a spurious 'import datetime'), directly demonstrating R1.3 discrimination.

All needed runs completed in the official image. Note: this bundle's G-PANEL-3 is a fail (leakage: re.RegexFlag named in prose reconstructs the hidden validator test) — that is a leakage judgment, orthogonal to G-EQ spec-fidelity, which is SOUND: >=5 probes hold, positive control discriminates, and >=1 requirements-permitted wrong candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-hunk change to EnumSerializer.serialize: value-based module.Class(value) → name-based module.Class['name'] with only {'import module'}. Requirement 1 (subscript-by-name form, repr'd name literal, single module import, no value, round-trip), Requirement 2 (applies to default and choices via the single dispatch point; 2.3 flag/int enums — probed IntEnum and IntFlag both render by name), and Requirement 3 (non-enum values routed to existing serializers unchanged) all match. Requirement 2.1/2.2 (default=/choices) are consequences of EnumSerializer being the sole enum dispatch path — no separate code path exists that could diverge. Modeling boundary is the changed observable behavior (enum member rendering), not a narrow slice. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the fix into behavioral EARS requirements and legitimately localize the change (serializer.py, EnumSerializer, MigrationWriter.serialize, serializer_factory). All concrete surface content — the subscript form ClassName['NAME'], Status['GOOD'], the gettext_lazy/translation motivation, the CharField-default scenario — is already in the PUBLIC problem_statement. No hidden-only content is transmitted: no test names (test_serialize_enums, test_serialize_class_based_validators), no test file path, no test-invented enum class names (TextEnum/TextTranslatedEnum/BinaryEnum/IntEnum), no quoted test/gold code, no fix-invented identifiers (self.value.name / %r rendered only behaviorally). The RegexFlag gold-consequence (re.RegexFlag['DOTALL']) is described only as a generic 'flag/bit-mask enum rendered by name' rule (Req 2.3), never naming re.RegexFlag, DOTALL, or the value 16. Borderline but acceptable: Req 1.4 enumerates value types (string, lazy string, integer, bytes) that loosely track the four test enum classes, but string+translated are public and integer/bytes are the natural exhaustive value-type categories for the 'render by name regardless of value type' generalization — a behavioral spec, not a verbatim mirror of the parametrization (no member names or expected output strings).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
