# P2 adversarial audit — sphinx-doc__sphinx-9281

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: Req1.1 - enum member renders as ClassName.MemberName (not repr)
import enum
from sphinx.util.inspect import object_description
class MyEnum(enum.Enum):
    ValueA = 10
    ValueB = 20
r = object_description(MyEnum.ValueA)
print("observed:", repr(r))
assert r == "MyEnum.ValueA", r
print("PASS")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.2 - no underlying value, no angle brackets/repr decoration; uses class __name__ and .name
import enum
from sphinx.util.inspect import object_description
class Color(enum.Enum):
    RED = 999
r = object_description(Color.RED)
print("observed:", repr(r))
assert r == "Color.RED", r
assert "<" not in r and ">" not in r, r
assert "999" not in r, r
assert ":" not in r, r
print("PASS")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.3 - two distinct members differ only in member-name portion
import enum
from sphinx.util.inspect import object_description
class E(enum.Enum):
    A = 1
    B = 2
ra = object_description(E.A)
rb = object_description(E.B)
print("A:", ra, "B:", rb)
assert ra == "E.A" and rb == "E.B", (ra, rb)
# differ only in last segment
pa, pb = ra.rsplit(".",1), rb.rsplit(".",1)
assert pa[0] == pb[0], (pa,pb)
assert pa[1] != pb[1], (pa,pb)
print("PASS")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2.1 - dict rendering unchanged, sorted keys
from sphinx.util.inspect import object_description
r = object_description({"b": 2, "a": 1})
print("observed:", repr(r))
assert r == "{'a': 1, 'b': 2}", r
print("PASS")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2.2 - set sorted rendering; unsortable falls back to generic repr
from sphinx.util.inspect import object_description
r = object_description({3, 1, 2})
print("set observed:", repr(r))
assert r == "{1, 2, 3}", r
# unsortable set (int vs str) -> generic repr fallback, no exception
r2 = object_description({1, "a"})
print("unsortable set observed:", repr(r2))
assert r2.startswith("{") and r2.endswith("}"), r2
print("PASS")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req2.3 - frozenset sorted rendering
from sphinx.util.inspect import object_description
r = object_description(frozenset({3, 1, 2}))
print("observed:", repr(r))
assert r == "frozenset({1, 2, 3})", r
print("PASS")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req2.5 - general path: newline flattening + memory-address stripping, unchanged
from sphinx.util.inspect import object_description
class Foo:
    def __repr__(self):
        return "a\nb"
r = object_description(Foo())
print("newline observed:", repr(r))
assert r == "a b", r  # embedded newline flattened to space
# plain int unchanged
assert object_description(42) == "42"
# default object repr -> memory address stripped
class Bar: pass
rb = object_description(Bar())
print("obj observed:", repr(rb))
assert "0x" not in rb, rb
print("PASS")
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Req2.6 - exception in general path: enum feature does not change exception behavior.
# Gold wraps repr errors as ValueError chained from original; must still raise a ValueError.
from sphinx.util.inspect import object_description
class Bad:
    def __repr__(self):
        raise KeyError("boom")
try:
    object_description(Bad())
    print("no exception - FAIL"); raise SystemExit(1)
except ValueError as e:
    print("raised ValueError, cause:", repr(e.__cause__))
    assert isinstance(e.__cause__, KeyError), e.__cause__
except SystemExit:
    raise
print("PASS")
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
import enum
from sphinx.util.inspect import object_description
class Outer:
    class Inner(enum.Enum):
        X = 1
r = object_description(Outer.Inner.X)
print("observed:", repr(r))
# Req1.2: unqualified class __name__ ('Inner'), not qualname ('Outer.Inner')
assert r == "Inner.X", r
print("PASS")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req1.1 - enum member renders as ClassName.MemberName (not repr)
import enum
from sphinx.util.inspect import object_description
class MyEnum(enum.Enum):
    ValueA = 10
    ValueB = 20
r = object_description(MyEnum.ValueA)
print("observed:", repr(r))
assert r == "MyEnum.ValueA", r
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

Instance renders enum default values in autodoc signatures via object_description in sphinx/util/inspect.py. Gold adds `elif isinstance(object, enum.Enum): return '%s.%s' % (object.__class__.__name__, object.name)`.

9 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): enum member -> 'MyEnum.ValueA'. HOLDS patched; at base yields raw repr '<MyEnum.ValueA: 10>' (VIOLATED) => discriminates.
- probe_2 (Req1.2): no underlying value, no angle brackets, no ':' repr decoration; uses class name + .name.
- probe_3 (Req1.3): two members differ only in member-name portion (E.A vs E.B).
- probe_4 (Req2.1): dict rendering unchanged, sorted keys.
- probe_5 (Req2.2): set sorted rendering; unsortable set falls back to generic repr without exception.
- probe_6 (Req2.3): frozenset({...}) sorted rendering.
- probe_7 (Req2.5): general path newline flattening + memory-address stripping unchanged.
- probe_8 (Req2.6): repr-raising object still raises ValueError chained from the original error (unchanged behavior).
- probe_9 (Req1.2): nested enum class -> unqualified __name__ ('Inner.X'), not qualname.

Candidate wrong patches (both apply at base_commit, both REJECTED by suite):
- weak_value.diff: uses object.value instead of object.name -> REJECTED by probes 1,2,3,9.
- weak_qualname.diff: uses __class__.__qualname__ instead of __name__ -> passes top-level probes 1/3 but REJECTED by nested-class probe_9 (Req1.2 mandates unqualified __name__).

Both alternatives that a weak reading permits are caught; suite discriminates. Probes 7 and 8 were initially buggy (repr escapes \n; generic path raises a NEW chained ValueError not the original) and were corrected to match true unchanged semantics before all passed. SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Positive control: Req1.1 - enum member renders as ClassName.MemberName (not repr)
import enum
from sphinx.util.inspect import object_description
class MyEnum(enum.Enum):
    ValueA = 10
    ValueB = 20
r = object_description(MyEnum.ValueA)
print("observed:", repr(r))
assert r == "MyEnum.ValueA", r
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

Instance renders enum default values in autodoc signatures via object_description in sphinx/util/inspect.py. Gold adds `elif isinstance(object, enum.Enum): return '%s.%s' % (object.__class__.__name__, object.name)`.

9 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): enum member -> 'MyEnum.ValueA'. HOLDS patched; at base yields raw repr '<MyEnum.ValueA: 10>' (VIOLATED) => discriminates.
- probe_2 (Req1.2): no underlying value, no angle brackets, no ':' repr decoration; uses class name + .name.
- probe_3 (Req1.3): two members differ only in member-name portion (E.A vs E.B).
- probe_4 (Req2.1): dict rendering unchanged, sorted keys.
- probe_5 (Req2.2): set sorted rendering; unsortable set falls back to generic repr without exception.
- probe_6 (Req2.3): frozenset({...}) sorted rendering.
- probe_7 (Req2.5): general path newline flattening + memory-address stripping unchanged.
- probe_8 (Req2.6): repr-raising object still raises ValueError chained from the original error (unchanged behavior).
- probe_9 (Req1.2): nested enum class -> unqualified __name__ ('Inner.X'), not qualname.

Candidate wrong patches (both apply at base_commit, both REJECTED by suite):
- weak_value.diff: uses object.value instead of object.name -> REJECTED by probes 1,2,3,9.
- weak_qualname.diff: uses __class__.__qualname__ instead of __name__ -> passes top-level probes 1/3 but REJECTED by nested-class probe_9 (Req1.2 mandates unqualified __name__).

Both alternatives that a weak reading permits are caught; suite discriminates. Probes 7 and 8 were initially buggy (repr escapes \n; generic path raises a NEW chained ValueError not the original) and were corrected to match true unchanged semantics before all passed. SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `elif isinstance(object, enum.Enum): return '%s.%s' % (object.__class__.__name__, object.name)` and converts the preceding set/frozenset `if`s to `elif`. Requirements pin exactly the changed observable behavior (the enum branch) while explicitly preserving all other branches; modeling boundary is correct, not a narrow slice. Probes run in the instance image on both patched and base trees.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the enum-rendering behavior in EARS form. It names object_description and sphinx/util/inspect.py (legitimate change localization) and translates the fix into behavioral criteria. No hidden-test content is transmitted: the F2P test test_object_description_enum, its path, the MyEnum/FOO/BAR fixture, and the MyEnum.FOO assertion are not quoted or named. No fix-invented identifiers appear — the class-name/name rendering (object.__class__.__name__, object.name) is standard Python and directly implied by the public problem_statement's <MyEnum.ValueA: 10> -> MyEnum.ValueA expectation. The container precedence (dict/set/frozenset) and elif-chain semantics are reconstructible from the public code and are described as behavior, not as parametrized cases. Req 1.3 (two distinct members differ only in member-name) is a behavioral generalization, not present in the single-case test — so it does not mirror the test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
