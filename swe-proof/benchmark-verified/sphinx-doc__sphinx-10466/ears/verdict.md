# P2 adversarial audit — sphinx-doc__sphinx-10466

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_dedup.py`, `probe_2_distinct.py`, `probe_3_order.py`, `probe_4_uuids.py`, `probe_5_msgset.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3_order.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_dedup.py` → holds on the patched tree (good)

```python
# Req 1.1 / 1.2 / 3.3: same (source,line) recorded multiple times -> appears once.
import sys
from sphinx.builders.gettext import Catalog, MsgOrigin

cat = Catalog()
# record same message at same source+line three times (distinct uids each)
for _ in range(3):
    cat.add("hello", MsgOrigin("a.rst", 10))
# and a distinct position once
cat.add("hello", MsgOrigin("a.rst", 20))

msgs = list(cat)
assert len(msgs) == 1, msgs
m = msgs[0]
print("text=", m.text)
print("locations=", m.locations)
locs = list(m.locations)
# each distinct pair exactly once, none omitted
if locs.count(("a.rst", 10)) != 1:
    print("FAIL: (a.rst,10) count=", locs.count(("a.rst", 10)))
    sys.exit(1)
if ("a.rst", 20) not in locs:
    print("FAIL: (a.rst,20) missing")
    sys.exit(1)
if len(locs) != 2:
    print("FAIL: expected 2 distinct locations, got", locs)
    sys.exit(1)
print("PASS: duplicate position collapsed to one, distinct kept")
sys.exit(0)
```

Attack 2 — `probe_2_distinct.py` → holds on the patched tree (good)

```python
# Req 1.3: positions differing in EITHER source OR line are each reported.
import sys
from sphinx.builders.gettext import Catalog, MsgOrigin

cat = Catalog()
cat.add("msg", MsgOrigin("a.rst", 10))
cat.add("msg", MsgOrigin("a.rst", 11))  # differ in line
cat.add("msg", MsgOrigin("b.rst", 10))  # differ in source
cat.add("msg", MsgOrigin("a.rst", 10))  # dup of first

m = list(cat)[0]
locs = list(m.locations)
print("locations=", locs)
expected = {("a.rst", 10), ("a.rst", 11), ("b.rst", 10)}
if set(locs) != expected:
    print("FAIL: set mismatch", set(locs), expected)
    sys.exit(1)
if len(locs) != 3:
    print("FAIL: dup not collapsed / distinct dropped", locs)
    sys.exit(1)
print("PASS: all distinct positions reported, dup collapsed")
sys.exit(0)
```

Attack 3 — `probe_3_order.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2/2.3 + POSITIVE CONTROL: ascending order by (source,line),
# order-independent, strictly increasing. This FAILS at base (raw order, dups).
import sys
from sphinx.builders.gettext import Catalog, MsgOrigin

# insertion order deliberately jumbled and with duplicates
inserts = [("b.rst", 5), ("a.rst", 30), ("a.rst", 2), ("b.rst", 5),
           ("a.rst", 2), ("c.rst", 1), ("a.rst", 30)]

def build(seq):
    cat = Catalog()
    for s, l in seq:
        cat.add("m", MsgOrigin(s, l))
    return list(list(cat)[0].locations)

locs = build(inserts)
print("locations=", locs)

expected_sorted = sorted(set(inserts))
if locs != expected_sorted:
    print("FAIL: not ascending/deduped. expected", expected_sorted)
    sys.exit(1)

# strictly increasing
if any(locs[i] >= locs[i+1] for i in range(len(locs)-1)):
    print("FAIL: not strictly increasing")
    sys.exit(1)

# order independence: reversed insertion yields identical result
locs_rev = build(list(reversed(inserts)))
if locs != locs_rev:
    print("FAIL: order-dependent", locs, locs_rev)
    sys.exit(1)

print("PASS: ascending, strictly increasing, order-independent")
sys.exit(0)
```

Attack 4 — `probe_4_uuids.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: uuids has one entry per recorded occurrence (NOT deduped/reordered).
import sys
from sphinx.builders.gettext import Catalog, MsgOrigin

cat = Catalog()
origins = [MsgOrigin("a.rst", 10), MsgOrigin("a.rst", 10),
           MsgOrigin("a.rst", 10), MsgOrigin("b.rst", 20)]
for o in origins:
    cat.add("m", o)

m = list(cat)[0]
print("n_uuids=", len(m.uuids), "n_locations=", len(m.locations))
# 4 occurrences -> 4 uuids even though 3 share a position
if len(m.uuids) != 4:
    print("FAIL: expected 4 uuids, got", len(m.uuids))
    sys.exit(1)
# uuids not deduped and preserve recording order
expected_uids = [o.uid for o in origins]
if list(m.uuids) != expected_uids:
    print("FAIL: uuids reordered/deduped", m.uuids, expected_uids)
    sys.exit(1)
# locations deduped to 2
if len(m.locations) != 2:
    print("FAIL: locations not deduped", m.locations)
    sys.exit(1)
print("PASS: uuids complete & in-order; locations deduped")
sys.exit(0)
```

Attack 5 — `probe_5_msgset.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3 + 5.1: message set & first-recorded order preserved;
# add ignores origins with no uid; text preserved.
import sys
from sphinx.builders.gettext import Catalog, MsgOrigin

cat = Catalog()
# distinct messages recorded in this first-seen order
cat.add("zebra", MsgOrigin("a.rst", 1))
cat.add("apple", MsgOrigin("a.rst", 2))
cat.add("zebra", MsgOrigin("a.rst", 3))   # repeat, must not create new message
cat.add("mango", MsgOrigin("b.rst", 1))

# origin without a uid attribute -> ignored (Req 5.1)
class NoUid:
    source = "x.rst"
    line = 99
cat.add("ghost", NoUid())

msgs = list(cat)
texts = [m.text for m in msgs]
print("texts=", texts)
if texts != ["zebra", "apple", "mango"]:
    print("FAIL: message set/order wrong", texts)
    sys.exit(1)
if "ghost" in texts:
    print("FAIL: no-uid origin not ignored")
    sys.exit(1)
# text attribute equals recorded text
for m in msgs:
    if not isinstance(m.text, str):
        print("FAIL: text not str", m.text); sys.exit(1)
print("PASS: message set, first-seen order, no-uid ignored, text preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3_order.py`

```python
# Req 2.1/2.2/2.3 + POSITIVE CONTROL: ascending order by (source,line),
# order-independent, strictly increasing. This FAILS at base (raw order, dups).
import sys
from sphinx.builders.gettext import Catalog, MsgOrigin

# insertion order deliberately jumbled and with duplicates
inserts = [("b.rst", 5), ("a.rst", 30), ("a.rst", 2), ("b.rst", 5),
           ("a.rst", 2), ("c.rst", 1), ("a.rst", 30)]

def build(seq):
    cat = Catalog()
    for s, l in seq:
        cat.add("m", MsgOrigin(s, l))
    return list(list(cat)[0].locations)

locs = build(inserts)
print("locations=", locs)

expected_sorted = sorted(set(inserts))
if locs != expected_sorted:
    print("FAIL: not ascending/deduped. expected", expected_sorted)
    sys.exit(1)

# strictly increasing
if any(locs[i] >= locs[i+1] for i in range(len(locs)-1)):
    print("FAIL: not strictly increasing")
    sys.exit(1)

# order independence: reversed insertion yields identical result
locs_rev = build(list(reversed(inserts)))
if locs != locs_rev:
    print("FAIL: order-dependent", locs, locs_rev)
    sys.exit(1)

print("PASS: ascending, strictly increasing, order-independent")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-10466: gold fix changes Catalog.__iter__ so positions = sorted(set((source,line) ...)) — de-duplicate AND sort the (source,line) locations while keeping uuids as-is.

Probe suite (all standalone python, repo package only), results on gold-PATCHED tree:
- probe_1_dedup (Req 1.1/1.2/3.3): same (source,line) recorded 3x collapses to one occurrence, distinct pair kept -> HOLDS patched.
- probe_2_distinct (Req 1.3): positions differing in either source OR line each reported, dup collapsed -> HOLDS patched.
- probe_3_order (Req 2.1/2.2/2.3, POSITIVE CONTROL): jumbled+duplicated inserts yield ascending, strictly-increasing, order-independent locations. HOLDS patched, VIOLATED at base (base returns raw recording order with dups) -> discriminates.
- probe_4_uuids (Req 4.1/4.2): 4 occurrences (3 sharing a position) -> 4 uuids in recording order (not deduped/reordered) while locations dedup to 2 -> HOLDS patched.
- probe_5_msgset (Req 3.1/3.2/3.3 + 5.1): message set = distinct texts in first-seen order; origin lacking a 'uid' attribute is ignored (matches hasattr(origin,'uid') check); text preserved -> HOLDS patched. (Initial version used uid=None; corrected after confirming the code guards with hasattr, per Req 5.1 'carries no uid'.)

Candidate wrong-fix patches (both apply at base):
- weak_dedup_nosort: dedups via dict.fromkeys but does NOT sort. REJECTED by probe_3_order (order not ascending/deterministic). Passes 1,2,4,5.
- weak_sort_nodedup: sorts but does NOT dedup. REJECTED by probes 1,2,3,4 (duplicate positions survive). Passes 5.

No requirements-conforming candidate found that fails hidden tests: the two natural partial fixes are each caught by the suite. Both dedup and ascending sort are independently mandated (Req 1 and Req 2) and independently probed, so a spec-conforming implementation must be equivalent to the gold behavior. All 5 probes hold on the patched tree; positive control discriminates base vs patched. No violation, no admitted weak fix -> SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_dedup.py`, `probe_2_distinct.py`, `probe_3_order.py`, `probe_4_uuids.py`, `probe_5_msgset.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3_order.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_dedup.py` → holds on the patched tree (good)

Attack 2 — `probe_2_distinct.py` → holds on the patched tree (good)

Attack 3 — `probe_3_order.py` → holds on the patched tree (good)

Attack 4 — `probe_4_uuids.py` → holds on the patched tree (good)

Attack 5 — `probe_5_msgset.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3_order.py`

```python
# Req 2.1/2.2/2.3 + POSITIVE CONTROL: ascending order by (source,line),
# order-independent, strictly increasing. This FAILS at base (raw order, dups).
import sys
from sphinx.builders.gettext import Catalog, MsgOrigin

# insertion order deliberately jumbled and with duplicates
inserts = [("b.rst", 5), ("a.rst", 30), ("a.rst", 2), ("b.rst", 5),
           ("a.rst", 2), ("c.rst", 1), ("a.rst", 30)]

def build(seq):
    cat = Catalog()
    for s, l in seq:
        cat.add("m", MsgOrigin(s, l))
    return list(list(cat)[0].locations)

locs = build(inserts)
print("locations=", locs)

expected_sorted = sorted(set(inserts))
if locs != expected_sorted:
    print("FAIL: not ascending/deduped. expected", expected_sorted)
    sys.exit(1)

# strictly increasing
if any(locs[i] >= locs[i+1] for i in range(len(locs)-1)):
    print("FAIL: not strictly increasing")
    sys.exit(1)

# order independence: reversed insertion yields identical result
locs_rev = build(list(reversed(inserts)))
if locs != locs_rev:
    print("FAIL: order-dependent", locs, locs_rev)
    sys.exit(1)

print("PASS: ascending, strictly increasing, order-independent")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-10466: gold fix changes Catalog.__iter__ so positions = sorted(set((source,line) ...)) — de-duplicate AND sort the (source,line) locations while keeping uuids as-is.

Probe suite (all standalone python, repo package only), results on gold-PATCHED tree:
- probe_1_dedup (Req 1.1/1.2/3.3): same (source,line) recorded 3x collapses to one occurrence, distinct pair kept -> HOLDS patched.
- probe_2_distinct (Req 1.3): positions differing in either source OR line each reported, dup collapsed -> HOLDS patched.
- probe_3_order (Req 2.1/2.2/2.3, POSITIVE CONTROL): jumbled+duplicated inserts yield ascending, strictly-increasing, order-independent locations. HOLDS patched, VIOLATED at base (base returns raw recording order with dups) -> discriminates.
- probe_4_uuids (Req 4.1/4.2): 4 occurrences (3 sharing a position) -> 4 uuids in recording order (not deduped/reordered) while locations dedup to 2 -> HOLDS patched.
- probe_5_msgset (Req 3.1/3.2/3.3 + 5.1): message set = distinct texts in first-seen order; origin lacking a 'uid' attribute is ignored (matches hasattr(origin,'uid') check); text preserved -> HOLDS patched. (Initial version used uid=None; corrected after confirming the code guards with hasattr, per Req 5.1 'carries no uid'.)

Candidate wrong-fix patches (both apply at base):
- weak_dedup_nosort: dedups via dict.fromkeys but does NOT sort. REJECTED by probe_3_order (order not ascending/deterministic). Passes 1,2,4,5.
- weak_sort_nodedup: sorts but does NOT dedup. REJECTED by probes 1,2,3,4 (duplicate positions survive). Passes 5.

No requirements-conforming candidate found that fails hidden tests: the two natural partial fixes are each caught by the suite. Both dedup and ascending sort are independently mandated (Req 1 and Req 2) and independently probed, so a spec-conforming implementation must be equivalent to the gold behavior. All 5 probes hold on the patched tree; positive control discriminates base vs patched. No violation, no admitted weak fix -> SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a single line: positions changed from `[(source,line) for ...]` to `sorted(set((source,line) for ...))`. Base-commit probe fails (locations=[('b.rst',5),('a.rst',0),('a.rst',0),('a.rst',0),('a.rst',10)]) confirming the observable behavior change is the dedup+sort. Requirements pin the full changed observable (dedup AND ascending order) at the correct Catalog.__iter__/Message.locations boundary, not a narrower slice. R5.2/R5.3 (full gettext .pot build) are broader end-to-end claims but consistent with the fix and not contradicted. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the gettext Catalog location de-duplication behavior (gold: positions = sorted(set(...)) in Catalog.__iter__) purely as behavioral requirements. All named entities (Catalog, Catalog.add, __iter__, Message, locations, uuids, origin.source/line/uid, sphinx/builders/gettext.py) are legitimate localization; most already appear in the public problem_statement's suggested solution (the Message.__init__ signature with self.uuids, gettext.py). No hidden-test content is transmitted: no test file path/name (test_build_gettext.py::test_Catalog_duplicated_message), no test literals ('hello'/'world', '/path/to/filename', line numbers 1/2), no fix-invented identifiers (the gold introduces none), and no case enumeration mirroring the test's specific 5-record scenario — Req 1 AC2 ('some identical, others differ') is a generic behavioral statement. Ordering described as 'ascending by source then line' translates sorted(tuple) behavior, not test-specific expected values. Note the doc targets __iter__ (the true gold site) rather than the problem_statement's mistaken __init__ suggestion; that is faithful localization, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
