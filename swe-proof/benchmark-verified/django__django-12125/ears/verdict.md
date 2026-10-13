# P2 adversarial audit — django__django-12125

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1 c1/c2/c3 + positive control: nested class -> module.Outer.Inner, imports {import module}
from django.db import models
from django.db.migrations.serializer import serializer_factory

class Outer(object):
    class Inner(models.CharField):
        pass

s = serializer_factory(Outer.Inner)
string, imports = s.serialize()
mod = Outer.Inner.__module__
print("string=", string)
print("imports=", imports)
expected = "%s.Outer.Inner" % mod
ok = (string == expected) and (imports == {"import %s" % mod})
print("expected=", expected)
assert ok, "nested class not serialized with full qualname"
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1 c4: nested enum class serialized with full qualname
import enum
from django.db.migrations.serializer import serializer_factory

class Wrap(object):
    class Color(enum.Enum):
        RED = 1

s = serializer_factory(Wrap.Color)
string, imports = s.serialize()
mod = Wrap.Color.__module__
print("string=", string, "imports=", imports)
expected = "%s.Wrap.Color" % mod
assert string == expected and imports == {"import %s" % mod}, "nested enum wrong"
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2: top-level class -> module.Name, imports {import module}
from django.db import models
from django.db.migrations.serializer import serializer_factory

class TopField(models.CharField):
    pass

s = serializer_factory(TopField)
string, imports = s.serialize()
mod = TopField.__module__
print("string=", string, "imports=", imports)
expected = "%s.TopField" % mod
assert string == expected and imports == {"import %s" % mod}, "top-level wrong"
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3: builtin type -> bare leaf name, empty imports
from django.db.migrations.serializer import serializer_factory

s = serializer_factory(int)
string, imports = s.serialize()
print("string=", string, "imports=", imports)
assert string == "int" and imports == set(), "builtin wrong"
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req4: special-cased types models.Model and type(None)
from django.db import models
from django.db.migrations.serializer import serializer_factory

s1 = serializer_factory(models.Model).serialize()
s2 = serializer_factory(type(None)).serialize()
print("model=", s1, "none=", s2)
assert s1 == ("models.Model", set()), "models.Model wrong"
assert s2 == ("type(None)", set()), "type(None) wrong"
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req5 c2: Decimal serialization + c1 floats round-trip
import decimal
from django.db.migrations.serializer import serializer_factory

string, imports = serializer_factory(decimal.Decimal("1.3")).serialize()
print("decimal=", string, imports)
assert string == "Decimal('1.3')" and imports == {'from decimal import Decimal'}, "decimal wrong"

# float non-finite round trip
import math
for val, chk in [(float('inf'), lambda x: math.isinf(x) and x>0),
                 (float('-inf'), lambda x: math.isinf(x) and x<0),
                 (float('nan'), lambda x: math.isnan(x))]:
    st, im = serializer_factory(val).serialize()
    v = eval(st, {'float': float, 'nan': float('nan'), 'inf': float('inf')})
    print("float", val, "->", st, "=>", v)
    assert chk(v), "float roundtrip wrong for %r" % val
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req1 c2: EVERY enclosing class name (deep 3-level nesting)
from django.db import models
from django.db.migrations.serializer import serializer_factory

class A(object):
    class B(object):
        class C(models.CharField):
            pass

s = serializer_factory(A.B.C)
string, imports = s.serialize()
mod = A.B.C.__module__
print("string=", string, "imports=", imports)
expected = "%s.A.B.C" % mod
assert string == expected and imports == {"import %s" % mod}, "deep nested wrong"
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1 c1/c2/c3 + positive control: nested class -> module.Outer.Inner, imports {import module}
from django.db import models
from django.db.migrations.serializer import serializer_factory

class Outer(object):
    class Inner(models.CharField):
        pass

s = serializer_factory(Outer.Inner)
string, imports = s.serialize()
mod = Outer.Inner.__module__
print("string=", string)
print("imports=", imports)
expected = "%s.Outer.Inner" % mod
ok = (string == expected) and (imports == {"import %s" % mod})
print("expected=", expected)
assert ok, "nested class not serialized with full qualname"
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 5 requirements. probe_1 (Req1 c1-3, nested Outer.Inner CharField, positive control), probe_2 (Req1 c4 nested enum), probe_3 (Req2 top-level), probe_4 (Req3 builtin int -> bare, no imports), probe_5 (Req4 models.Model / type(None) special-cased), probe_6 (Req5 c1/c2 Decimal + non-finite float round-trip), probe_7 (Req1 c2 deep 3-level A.B.C -> full qualname). All 7 HOLD on gold-patched tree. Positive controls probe_1 and probe_7 FAIL at base (leaf-name form gives module.Inner / module.C). Two wrong-fix candidates BOTH rejected by the suite: 'leaf_only' (base-equivalent __name__.split('.')[-1]) rejected by probe_1 & probe_7; 'last_two' (last 2 qualname components) passes 2-level but rejected by probe_7's 3-level nesting. No requirement-conforming alternative found that would evade the hidden tests. Gold patch = single-line __name__ -> __qualname__. Suite discriminates; verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req1 c1/c2/c3 + positive control: nested class -> module.Outer.Inner, imports {import module}
from django.db import models
from django.db.migrations.serializer import serializer_factory

class Outer(object):
    class Inner(models.CharField):
        pass

s = serializer_factory(Outer.Inner)
string, imports = s.serialize()
mod = Outer.Inner.__module__
print("string=", string)
print("imports=", imports)
expected = "%s.Outer.Inner" % mod
ok = (string == expected) and (imports == {"import %s" % mod})
print("expected=", expected)
assert ok, "nested class not serialized with full qualname"
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 5 requirements. probe_1 (Req1 c1-3, nested Outer.Inner CharField, positive control), probe_2 (Req1 c4 nested enum), probe_3 (Req2 top-level), probe_4 (Req3 builtin int -> bare, no imports), probe_5 (Req4 models.Model / type(None) special-cased), probe_6 (Req5 c1/c2 Decimal + non-finite float round-trip), probe_7 (Req1 c2 deep 3-level A.B.C -> full qualname). All 7 HOLD on gold-patched tree. Positive controls probe_1 and probe_7 FAIL at base (leaf-name form gives module.Inner / module.C). Two wrong-fix candidates BOTH rejected by the suite: 'leaf_only' (base-equivalent __name__.split('.')[-1]) rejected by probe_1 & probe_7; 'last_two' (last 2 qualname components) passes 2-level but rejected by probe_7's 3-level nesting. No requirement-conforming alternative found that would evade the hidden tests. Gold patch = single-line __name__ -> __qualname__. Suite discriminates; verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch is a single-line change: '%s.%s' % (module, self.value.__name__) -> self.value.__qualname__ in TypeSerializer.serialize (django/db/migrations/serializer.py). Requirements model exactly this observable output boundary (the full module+qualname reference for non-builtin types), correctly preserve the builtins branch (empty imports, bare name), the special-cased models.Model/type(None) short-circuits, and R5's numeric/decimal/class-as-arg regression paths. R1.4 (uniform across Field/enum/Choices subclasses) is faithful because __qualname__ is kind-agnostic. No requirement mandates behavior the patch lacks, forbids behavior it has, or pins a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md localizes the change to django/db/migrations/serializer.py TypeSerializer.serialize and describes emitting the fully-qualified in-module path (__qualname__) — legitimate localization; __qualname__ is a Python builtin, not a fix-invented identifier, and the Outer.Inner / <module>.Outer.Inner example is taken directly from the public problem_statement. No hidden-test artifacts appear: not the test name test_serialize_nested_class, not the path migrations.test_writer.WriterTests, not the parametrization identifiers NestedEnum/NestedChoices, not the DeconstructibleInstances class, not the 'migrations.test_writer.WriterTests.%s' id format. Req 1.4's Field/enum/Choices enumeration reads as behavioral kind-agnosticism (Field+enum are in the problem_statement; Choices is a public Django feature) rather than mirroring the [NestedEnum, NestedChoices] test param list. Req 5 (numbers/decimals/inf/-inf/NaN, Decimal('1.3')) corresponds to the test_serialize_numbers regression case but is stated as generic serializer round-trip behavior with natural example values — no test code, ids, or structure is reconstructable. All content is either public or a behavioral translation of what tests check, which is the intended purpose.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
