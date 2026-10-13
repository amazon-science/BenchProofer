# P2 adversarial audit — pydata__xarray-4629

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
# Req1.1 + positive control: override returns a DISTINCT object from first source
import sys
from xarray.core.merge import merge_attrs
first = {"a": 1, "b": 2}
res = merge_attrs([first, {"c": 3}], "override")
print("first id:", id(first), "res id:", id(res), "same?", res is first)
if res is first:
    print("FAIL: returned first source object identity")
    sys.exit(1)
print("OK: distinct object")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.2: reassign merged attr -> source unchanged (via Dataset.merge)
import sys
import xarray as xr
import numpy as np
a = xr.Dataset({"v": ("x", np.arange(3))}, attrs={"units": "m"})
b = xr.Dataset({"w": ("x", np.arange(3))}, attrs={"units": "s"})
merged = xr.merge([a, b], combine_attrs="override")
print("before: merged", merged.attrs, "a", a.attrs)
merged.attrs["units"] = "CHANGED"
print("after : merged", merged.attrs, "a", a.attrs)
if a.attrs.get("units") != "m":
    print("FAIL: source leaked")
    sys.exit(1)
print("OK: source unchanged")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.3 + Req1.4: mutate source in place -> merged retains key set / values
import sys
from xarray.core.merge import merge_attrs
first = {"a": 1, "b": 2}
res = merge_attrs([first], "override")
res_keys_before = set(res.keys())
res_a_before = res.get("a")
first["c"] = 99          # add key to source
del first["a"]           # remove key from source
first["b"] = 12345       # reassign existing (Req1.3)
print("res:", dict(res), "keys_before:", res_keys_before)
if set(res.keys()) != res_keys_before:
    print("FAIL: merged key set changed with source mutation")
    sys.exit(1)
if res.get("a") != res_a_before or res.get("b") != 2:
    print("FAIL: merged values changed with source reassignment")
    sys.exit(1)
print("OK: merged independent of in-place source mutation")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2.1 + 2.2: override returns equal-to-first contents; others don't contribute
import sys
from xarray.core.merge import merge_attrs
first = {"a": 1, "b": 2}
res = merge_attrs([first, {"c": 3, "a": 999}], "override")
print("res:", dict(res))
if dict(res) != {"a": 1, "b": 2}:
    print("FAIL: not equal to first / other sources contributed")
    sys.exit(1)
print("OK: equals first, no foreign keys")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2.3: shallow copy - values are the SAME value objects
import sys
from xarray.core.merge import merge_attrs
val = ["mutable", "list"]
first = {"a": val, "b": object()}
res = merge_attrs([first], "override")
print("val same?", res["a"] is val, "b same?", res["b"] is first["b"])
if res["a"] is not val or res["b"] is not first["b"]:
    print("FAIL: not a shallow copy (values copied)")
    sys.exit(1)
if res is first:
    print("FAIL: not a copy at all")
    sys.exit(1)
print("OK: shallow copy")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3: other policies unchanged (regression coverage)
import sys
from xarray.core.merge import merge_attrs
from xarray.core.merge import MergeError

ok = True
# 3.1 empty -> None regardless of policy
for pol in ["override","drop","no_conflicts","identical"]:
    r = merge_attrs([], pol)
    if r is not None:
        print("FAIL empty/%s -> %r" % (pol, r)); ok=False
# 3.2 drop -> {}
if merge_attrs([{"a":1}], "drop") != {}:
    print("FAIL drop"); ok=False
# 3.3 no_conflicts union + independent
f = {"a":1}
r = merge_attrs([f, {"b":2}], "no_conflicts")
if r != {"a":1,"b":2} or r is f:
    print("FAIL no_conflicts union/indep:", r, r is f); ok=False
# 3.4 no_conflicts disagree -> raise
try:
    merge_attrs([{"a":1},{"a":2}], "no_conflicts")
    print("FAIL no_conflicts should raise"); ok=False
except MergeError:
    pass
# 3.5 identical equal -> common, independent
f2={"a":1}
r=merge_attrs([f2,{"a":1}], "identical")
if r != {"a":1} or r is f2:
    print("FAIL identical equal:", r, r is f2); ok=False
# 3.6 identical differ -> raise
try:
    merge_attrs([{"a":1},{"a":2}], "identical")
    print("FAIL identical should raise"); ok=False
except MergeError:
    pass
# 3.7 unrecognised -> ValueError
try:
    merge_attrs([{"a":1}], "bogus")
    print("FAIL bogus should raise"); ok=False
except ValueError:
    pass
print("regression ok" if ok else "regression FAILED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.1 + positive control: override returns a DISTINCT object from first source
import sys
from xarray.core.merge import merge_attrs
first = {"a": 1, "b": 2}
res = merge_attrs([first, {"c": 3}], "override")
print("first id:", id(first), "res id:", id(res), "same?", res is first)
if res is first:
    print("FAIL: returned first source object identity")
    sys.exit(1)
print("OK: distinct object")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: merge_attrs override returns dict(variable_attrs[0]) instead of variable_attrs[0] (independent shallow copy).

Probes (all HOLD on patched, criterion in parens):
- probe_1 (Req1.1) POSITIVE CONTROL: override returns object distinct from first source. PATCHED: distinct (exit0). BASE: same identity (exit1) -> discriminates.
- probe_2 (Req1.2): Dataset.merge override; reassigning merged attr leaves source unchanged. PATCHED ok; BASE leaks -> exit1.
- probe_3 (Req1.3 + Req1.4): in-place source mutation (add/del/reassign keys) after merge; merged retains its key set & values. PATCHED ok; BASE follows source -> exit1.
- probe_4 (Req2.1 + 2.2): result equals first source contents; other sources contribute no keys/values (incl. colliding key 'a'). PATCHED ok.
- probe_5 (Req2.3): result is a SHALLOW copy - value objects identical (is) to first source's, but mapping is a distinct object. PATCHED ok; BASE not-a-copy -> exit1.
- probe_6 (Req3.1-3.7): regression across other policies - empty->None all policies, drop->{}, no_conflicts union+independent, no_conflicts/identical conflict raises, identical equal->common+independent, unrecognised->ValueError. PATCHED ok; BASE also ok (unchanged, as required).

Candidate wrong patch exercised & REJECTED:
- deepcopy.diff: copy.deepcopy(variable_attrs[0]). Satisfies independence (Req1.*, Req2.1/2.2) but VIOLATES Req2.3 shallow-copy -> probe_5 fails (val/b value objects not identical). Demonstrates suite discriminates the over-copying wrong fix.

>=5 distinct probes all hold on patched; positive control (probe_1) holds patched & fails at base (prepatch reproduced); deepcopy candidate rejected by probe_5. Requirements are faithful and discriminating.

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
# Req1.1 + positive control: override returns a DISTINCT object from first source
import sys
from xarray.core.merge import merge_attrs
first = {"a": 1, "b": 2}
res = merge_attrs([first, {"c": 3}], "override")
print("first id:", id(first), "res id:", id(res), "same?", res is first)
if res is first:
    print("FAIL: returned first source object identity")
    sys.exit(1)
print("OK: distinct object")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: merge_attrs override returns dict(variable_attrs[0]) instead of variable_attrs[0] (independent shallow copy).

Probes (all HOLD on patched, criterion in parens):
- probe_1 (Req1.1) POSITIVE CONTROL: override returns object distinct from first source. PATCHED: distinct (exit0). BASE: same identity (exit1) -> discriminates.
- probe_2 (Req1.2): Dataset.merge override; reassigning merged attr leaves source unchanged. PATCHED ok; BASE leaks -> exit1.
- probe_3 (Req1.3 + Req1.4): in-place source mutation (add/del/reassign keys) after merge; merged retains its key set & values. PATCHED ok; BASE follows source -> exit1.
- probe_4 (Req2.1 + 2.2): result equals first source contents; other sources contribute no keys/values (incl. colliding key 'a'). PATCHED ok.
- probe_5 (Req2.3): result is a SHALLOW copy - value objects identical (is) to first source's, but mapping is a distinct object. PATCHED ok; BASE not-a-copy -> exit1.
- probe_6 (Req3.1-3.7): regression across other policies - empty->None all policies, drop->{}, no_conflicts union+independent, no_conflicts/identical conflict raises, identical equal->common+independent, unrecognised->ValueError. PATCHED ok; BASE also ok (unchanged, as required).

Candidate wrong patch exercised & REJECTED:
- deepcopy.diff: copy.deepcopy(variable_attrs[0]). Satisfies independence (Req1.*, Req2.1/2.2) but VIOLATES Req2.3 shallow-copy -> probe_5 fails (val/b value objects not identical). Demonstrates suite discriminates the over-copying wrong fix.

>=5 distinct probes all hold on patched; positive control (probe_1) holds patched & fails at base (prepatch reproduced); deepcopy candidate rejected by probe_5. Requirements are faithful and discriminating.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a single-line fix: `override` branch now returns `dict(variable_attrs[0])` instead of the aliased `variable_attrs[0]`. The requirements pin exactly this changed observable behavior (Req 1: independence), correctly bound it to a shallow copy preserving first-source contents (Req 2), and correctly assert the other policies are unchanged (Req 3) — matching the code that already used dict()/copies for those branches. The modeling boundary is the changed behavior itself (aliasing of the override result), not a narrow slice. Probes on the patched image confirmed all 12 acceptance criteria hold; base image would fail R1.1/R1.2 (aliasing). No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already discloses everything load-bearing: the bug ('override does not copy attrs but references first object'), the exact file/line (xarray/core/merge.py, combine_attrs=='override': return variable_attrs[0]), the proposed fix (return dict(variable_attrs[0])), and a mutation MCVE showing the merged result's edit leaking into the first source. The requirements translate this into behavioral acceptance criteria (independent mapping, equal contents, shallow copy, other policies unchanged). Naming merge_attrs and the merge machinery is legitimate localization. Requirement 3's enumeration of the drop/no_conflicts/identical/unknown-policy behaviors describes the function's own contract as visible in merge.py source, not the hidden test parametrization. The single hidden FAIL_TO_PASS test (test_merge_attrs_override_copy) — its name, file path, function/class ids, and literal fixtures (Dataset attrs {'x':0}/{'x':1}, reassign to 2, assert ds1.x==0) — appear nowhere in the document. No fix-invented identifiers, no quoted test/gold code, no case list mirroring the PASS_TO_PASS parametrization ids. No semantic leak beyond the problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
