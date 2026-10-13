# P2 adversarial audit — django__django-11211

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_string_forms.py`, `probe_2_uuid_input.py`, `probe_3_int_input.py`, `probe_4_none.py`, `probe_5_string_eq_uuid.py`, `probe_6_invalid_raises.py`, `probe_7_db_prep_preserved.py`, `probe_8_topython_internal.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5_string_eq_uuid.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_string_forms.py` → holds on the patched tree (good)

```python
# Req1.1: prep hook on string spellings returns the uuid.UUID denoted
import uuid, sys
from django.db.models.fields import UUIDField
f = UUIDField()
target = uuid.UUID("12345678-1234-5678-1234-567812345678")
forms = [
    "12345678-1234-5678-1234-567812345678",  # hyphenated
    "12345678123456781234567812345678",       # 32 hex
    "urn:uuid:12345678-1234-5678-1234-567812345678",
    "{12345678-1234-5678-1234-567812345678}",
]
ok = True
for s in forms:
    r = f.get_prep_value(s)
    print(repr(s), "->", repr(r), type(r).__name__)
    if not (isinstance(r, uuid.UUID) and r == target):
        ok = False
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_uuid_input.py` → holds on the patched tree (good)

```python
# Req1.2: prep on an already-uuid.UUID returns equal UUID unchanged
import uuid, sys
from django.db.models.fields import UUIDField
f = UUIDField()
u = uuid.uuid4()
r = f.get_prep_value(u)
print("in:", repr(u), "out:", repr(r))
sys.exit(0 if isinstance(r, uuid.UUID) and r == u else 1)
```

Attack 3 — `probe_3_int_input.py` → holds on the patched tree (good)

```python
# Req1.3: prep on an integer returns uuid.UUID with that int value
import uuid, sys
from django.db.models.fields import UUIDField
f = UUIDField()
n = 0x12345678123456781234567812345678
r = f.get_prep_value(n)
print("int:", n, "-> ", repr(r))
sys.exit(0 if isinstance(r, uuid.UUID) and r.int == n else 1)
```

Attack 4 — `probe_4_none.py` → holds on the patched tree (good)

```python
# Req1.4: prep on None returns None
import sys
from django.db.models.fields import UUIDField
f = UUIDField()
r = f.get_prep_value(None)
print("None ->", repr(r))
sys.exit(0 if r is None else 1)
```

Attack 5 — `probe_5_string_eq_uuid.py` → holds on the patched tree (good)

```python
# Req1.5 (POSITIVE CONTROL): string spelling and uuid.UUID prepare to EQUAL keys.
# On base this FAILS: string prepares to itself (a str) != UUID object.
import uuid, sys
from django.db.models.fields import UUIDField
f = UUIDField()
u = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")
s = str(u)
ps = f.get_prep_value(s)
pu = f.get_prep_value(u)
print("prep(str)=", repr(ps), "| prep(uuid)=", repr(pu), "| equal:", ps == pu)
sys.exit(0 if ps == pu else 1)
```

Attack 6 — `probe_6_invalid_raises.py` → holds on the patched tree (good)

```python
# Req1.6: invalid value raises the same ValidationError as to_python does today
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
import django
try:
    django.setup()
except Exception:
    pass
from django.db.models.fields import UUIDField
from django.core.exceptions import ValidationError
f = UUIDField()
try:
    r = f.get_prep_value("not-a-uuid")
    print("NO ERROR, returned:", repr(r)); sys.exit(1)
except ValidationError as e:
    print("raised ValidationError:", list(e.messages)); sys.exit(0)
except Exception as e:
    print("raised WRONG type:", type(e).__name__, e); sys.exit(1)
```

Attack 7 — `probe_7_db_prep_preserved.py` → holds on the patched tree (good)

```python
# Req3.1: get_db_prep_value preserved. non-native -> 32-hex string; None -> None; native -> uuid.UUID
import uuid, sys
from django.db.models.fields import UUIDField
f = UUIDField()
u = uuid.UUID("12345678-1234-5678-1234-567812345678")
class Feat:
    def __init__(self, native): self.has_native_uuid_field = native
class Conn:
    def __init__(self, native): self.features = Feat(native)
ok = True
r = f.get_db_prep_value(u, Conn(False), prepared=True)
print("non-native db_prep:", repr(r)); ok = ok and (r == u.hex)
rn = f.get_db_prep_value(None, Conn(False), prepared=True)
print("None db_prep:", repr(rn)); ok = ok and rn is None
r2 = f.get_db_prep_value(u, Conn(True), prepared=True)
print("native db_prep:", repr(r2)); ok = ok and isinstance(r2, uuid.UUID) and r2 == u
# also non-native with string input still hexes
r3 = f.get_db_prep_value(str(u), Conn(False), prepared=True)
print("non-native str db_prep:", repr(r3)); ok = ok and (r3 == u.hex)
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8_topython_internal.py` → holds on the patched tree (good)

```python
# Req3.2/3.3: to_python still converts accepted inputs & raises on invalid; internal type unchanged
import uuid, sys
from django.db.models.fields import UUIDField
from django.core.exceptions import ValidationError
f = UUIDField()
ok = True
if f.get_internal_type() != "UUIDField":
    print("internal type changed!", f.get_internal_type()); ok = False
u = uuid.uuid4()
if f.to_python(str(u)) != u: print("to_python str fail"); ok=False
if f.to_python(u) != u: print("to_python uuid fail"); ok=False
if f.to_python(None) is not None: print("to_python None fail"); ok=False
try:
    f.to_python("garbage"); print("to_python did not raise"); ok=False
except ValidationError:
    pass
print("to_python/internal ok:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5_string_eq_uuid.py`

```python
# Req1.5 (POSITIVE CONTROL): string spelling and uuid.UUID prepare to EQUAL keys.
# On base this FAILS: string prepares to itself (a str) != UUID object.
import uuid, sys
from django.db.models.fields import UUIDField
f = UUIDField()
u = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")
s = str(u)
ps = f.get_prep_value(s)
pu = f.get_prep_value(u)
print("prep(str)=", repr(ps), "| prep(uuid)=", repr(pu), "| equal:", ps == pu)
sys.exit(0 if ps == pu else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: UUIDField.get_prep_value = to_python(super().get_prep_value(value)) so string spellings canonicalize to uuid.UUID, letting GFK prefetch join succeed for UUID-PK targets.

Probe suite (all HOLD on gold-patched tree):
- probe_1 (Req1.1): all string forms (hyphenated/32-hex/urn/braced) -> equal uuid.UUID object. HOLDS patched, VIOLATED base (returns str).
- probe_2 (Req1.2): uuid.UUID input -> equal uuid.UUID unchanged.
- probe_3 (Req1.3): int input -> uuid.UUID with matching .int.
- probe_4 (Req1.4): None -> None.
- probe_5 (Req1.5, POSITIVE CONTROL): prep(str) == prep(uuid). HOLDS patched, FAILS base (str != UUID) -> discriminates.
- probe_6 (Req1.6): invalid value raises ValidationError ('... is not a valid UUID'). HOLDS patched (raises), VIOLATED base (returns str, no error).
- probe_7 (Req3.1): get_db_prep_value preserved — non-native backend -> 32-hex string, native -> uuid.UUID, None -> None.
- probe_8 (Req3.2/3.3): to_python still converts accepted inputs / raises on invalid; internal type stays 'UUIDField'.

Early probe_6/probe_7 failures were probe bugs (unconfigured Django settings for message rendering; fake connection used a method instead of the has_native_uuid_field attribute), fixed and re-run — not real violations.

Wrong-fix candidate weak_str.diff: canonicalizes to str(self.to_python(value)) instead of the uuid.UUID object. It satisfies probe_5 (keys equal as strings) and probe_7, but is REJECTED by probe_1/2/3 because Req1.1-1.3 mandate returning a uuid.UUID object, not its string spelling. This demonstrates the suite discriminates a plausible weak reading. No requirements-conforming-yet-wrong patch found.

Verdict SOUND: 8 distinct probes all hold on patched; positive control fails at base and holds patched (discriminating power confirmed); wrong-fix candidate rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_string_forms.py`, `probe_2_uuid_input.py`, `probe_3_int_input.py`, `probe_4_none.py`, `probe_5_string_eq_uuid.py`, `probe_6_invalid_raises.py`, `probe_7_db_prep_preserved.py`, `probe_8_topython_internal.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5_string_eq_uuid.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_string_forms.py` → holds on the patched tree (good)

Attack 2 — `probe_2_uuid_input.py` → holds on the patched tree (good)

Attack 3 — `probe_3_int_input.py` → holds on the patched tree (good)

Attack 4 — `probe_4_none.py` → holds on the patched tree (good)

Attack 5 — `probe_5_string_eq_uuid.py` → holds on the patched tree (good)

Attack 6 — `probe_6_invalid_raises.py` → holds on the patched tree (good)

Attack 7 — `probe_7_db_prep_preserved.py` → holds on the patched tree (good)

Attack 8 — `probe_8_topython_internal.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5_string_eq_uuid.py`

```python
# Req1.5 (POSITIVE CONTROL): string spelling and uuid.UUID prepare to EQUAL keys.
# On base this FAILS: string prepares to itself (a str) != UUID object.
import uuid, sys
from django.db.models.fields import UUIDField
f = UUIDField()
u = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")
s = str(u)
ps = f.get_prep_value(s)
pu = f.get_prep_value(u)
print("prep(str)=", repr(ps), "| prep(uuid)=", repr(pu), "| equal:", ps == pu)
sys.exit(0 if ps == pu else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: UUIDField.get_prep_value = to_python(super().get_prep_value(value)) so string spellings canonicalize to uuid.UUID, letting GFK prefetch join succeed for UUID-PK targets.

Probe suite (all HOLD on gold-patched tree):
- probe_1 (Req1.1): all string forms (hyphenated/32-hex/urn/braced) -> equal uuid.UUID object. HOLDS patched, VIOLATED base (returns str).
- probe_2 (Req1.2): uuid.UUID input -> equal uuid.UUID unchanged.
- probe_3 (Req1.3): int input -> uuid.UUID with matching .int.
- probe_4 (Req1.4): None -> None.
- probe_5 (Req1.5, POSITIVE CONTROL): prep(str) == prep(uuid). HOLDS patched, FAILS base (str != UUID) -> discriminates.
- probe_6 (Req1.6): invalid value raises ValidationError ('... is not a valid UUID'). HOLDS patched (raises), VIOLATED base (returns str, no error).
- probe_7 (Req3.1): get_db_prep_value preserved — non-native backend -> 32-hex string, native -> uuid.UUID, None -> None.
- probe_8 (Req3.2/3.3): to_python still converts accepted inputs / raises on invalid; internal type stays 'UUIDField'.

Early probe_6/probe_7 failures were probe bugs (unconfigured Django settings for message rendering; fake connection used a method instead of the has_native_uuid_field attribute), fixed and re-run — not real violations.

Wrong-fix candidate weak_str.diff: canonicalizes to str(self.to_python(value)) instead of the uuid.UUID object. It satisfies probe_5 (keys equal as strings) and probe_7, but is REJECTED by probe_1/2/3 because Req1.1-1.3 mandate returning a uuid.UUID object, not its string spelling. This demonstrates the suite discriminates a plausible weak reading. No requirements-conforming-yet-wrong patch found.

Verdict SOUND: 8 distinct probes all hold on patched; positive control fails at base and holds patched (discriminating power confirmed); wrong-fix candidate rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Req1.7 (apply base get_prep_value before canonicalizing) matches the patch line-for-line (super().get_prep_value first, then to_python). Req2 pins the actual issue behavior (GFK prefetch resolving UUID-PK targets) which is the downstream consequence of the prep change; Req3 correctly requires preservation of untouched behavior (get_db_prep_value, to_python, get_internal_type, non-UUID/unset-content-type prefetch) — none of which the one-method patch alters. Boundary is the changed observable behavior, nothing invented or forbidden that the code exhibits.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes behavior, not the hidden tests. It never names the hidden test (test_prefetch_GFK_uuid_pk), its file (tests/prefetch_related/tests.py), the added models/fields (Article, content_object_uuid, content_type_uuid, object_pk_uuid), nor the gold-invented method name get_prep_value. Naming UUIDField, django/db/models/fields/__init__.py, and contenttypes/fields.py is legitimate localization. The gold edit is UUIDField.get_prep_value = super().get_prep_value() then to_python(); Req 1.7 ('first apply the base field's preliminary preparation ... before producing the canonical identifier') paraphrases this composition behaviorally without transmitting the code or the method name. Req 1's enumeration of UUID spelling forms (hyphenated/32-hex/urn:uuid:/brace), integer, None, and invalid mirrors UUIDField.to_python's documented accepted-input contract — general field behavior, NOT the test parametrization: the single hidden test uses only one uuid4-default pk case and exercises none of those forms, so the enumeration cannot be reconstructing the tests. Req 2/3 restate the public problem_statement (GFK prefetch to UUID-pk target returning None) plus standard preservation/non-regression clauses (db_prep_value native vs 32-hex, to_python, internal type, non-UUID pk, unset content-type). Nothing is derivable only from the hidden tests or gold beyond public material.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
