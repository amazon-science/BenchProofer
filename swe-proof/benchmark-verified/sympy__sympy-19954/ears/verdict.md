# P2 adversarial audit — sympy__sympy-19954

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: DihedralGroup(18).sylow_subgroup(2) order == 4, no IndexError
# Req 4.1, 4.2
import sys
from sympy.combinatorics.named_groups import DihedralGroup
try:
    g = DihedralGroup(18)
    s = g.sylow_subgroup(2)
    o = s.order()
    print("DihedralGroup(18).sylow_subgroup(2).order() =", o)
    if o != 4:
        print("FAIL: expected 4")
        sys.exit(1)
    sys.exit(0)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 4.3: DihedralGroup(50).sylow_subgroup(2).order() == 4
import sys
from sympy.combinatorics.named_groups import DihedralGroup
try:
    o = DihedralGroup(50).sylow_subgroup(2).order()
    print("DihedralGroup(50).sylow_subgroup(2).order() =", o)
    sys.exit(0 if o == 4 else 1)
except Exception as e:
    print("FAIL raised", type(e).__name__, e)
    sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3.3: DihedralGroup(6) yields exactly two minimal block systems:
# one with blocks of size 3 (two blocks), one with blocks of size 2 (three blocks);
# no trivial single-block system.
import sys
from sympy.combinatorics.named_groups import DihedralGroup

g = DihedralGroup(6)
blocks = g.minimal_blocks()
print("minimal_blocks =", blocks)
if blocks is False:
    print("FAIL: returned False on transitive group")
    sys.exit(1)
# Each block system is a per-point labeling list over 6 points.
sigs = []
for bs in blocks:
    # number of distinct labels = number of blocks
    labels = set(bs)
    nblocks = len(labels)
    # block sizes
    from collections import Counter
    sizes = sorted(Counter(bs).values())
    sigs.append((nblocks, tuple(sizes)))
print("signatures (nblocks, sizes) =", sigs)

# must be exactly 2 systems
if len(blocks) != 2:
    print("FAIL: expected exactly 2 minimal block systems, got", len(blocks))
    sys.exit(1)

# no trivial single-block system (all points in one block => nblocks==1)
if any(nb == 1 for nb, _ in sigs):
    print("FAIL: trivial single-block system present")
    sys.exit(1)

# one partition = 2 blocks of 3, other = 3 blocks of 2
want = {(2, (3, 3)), (3, (2, 2, 2))}
if set(sigs) != want:
    print("FAIL: signatures mismatch, want", want)
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1 & 3.2: minimal_blocks returns exactly one rep per distinct minimal
# system (no duplicate numbered form, no system strictly refined by another);
# non-transitive group returns False.
import sys
from collections import Counter
from sympy.combinatorics.named_groups import DihedralGroup, CyclicGroup
from sympy.combinatorics.permutations import Permutation
from sympy.combinatorics.perm_groups import PermutationGroup

def numbered(bs):
    # canonical numbered form of a per-point labeling
    remap = {}
    out = []
    for x in bs:
        if x not in remap:
            remap[x] = len(remap)
        out.append(remap[x])
    return tuple(out)

def cells(bs):
    d = {}
    for pt, lab in enumerate(bs):
        d.setdefault(lab, set()).add(pt)
    return [frozenset(v) for v in d.values()]

ok = True
for n in (6, 12, 18, 20):
    g = DihedralGroup(n)
    blocks = g.minimal_blocks()
    if blocks is False:
        print("FAIL: DihedralGroup(%d) transitive but returned False" % n)
        ok = False
        continue
    nf = [numbered(b) for b in blocks]
    if len(set(nf)) != len(nf):
        print("FAIL: duplicate numbered form for n=%d: %s" % (n, nf))
        ok = False
    # no system strictly refined by another (superseded)
    cellsets = [cells(b) for b in blocks]
    # represent each system by size of one block cell (all cells same size for these)
    for i in range(len(blocks)):
        for j in range(len(blocks)):
            if i == j:
                continue
            ci = cellsets[i]
            cj = cellsets[j]
            # system j refines system i if every cell of j is subset of a cell of i and j is strictly finer
            refines = all(any(cjx <= cix for cix in ci) for cjx in cj)
            si = len(next(iter(ci)))
            sj = len(next(iter(cj)))
            if refines and sj < si:
                # i is superseded by finer j -> should not both be present
                print("FAIL: n=%d system %d superseded by finer system %d" % (n, i, j))
                ok = False
    print("n=%d numbered forms=%s" % (n, nf))

# Req 3.2 non-transitive -> False
# Build an intransitive group on 4 points: <(0 1)>
p = Permutation([1, 0, 2, 3])
G = PermutationGroup([p])
res = G.minimal_blocks()
print("intransitive minimal_blocks =", res)
if res is not False:
    print("FAIL: non-transitive should return False")
    ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4.4: sylow order == largest power of p dividing group order, and is subgroup.
# Req 5.1: is_primitive/is_transitive preserved (DihedralGroup(10).is_primitive() False).
import sys
from sympy.combinatorics.named_groups import DihedralGroup

ok = True

def largest_power(n, p):
    e = 0
    while n % p == 0:
        n //= p
        e += 1
    return p ** e

for n, p in [(6, 2), (18, 2), (50, 2), (12, 3), (30, 2), (30, 3), (30, 5)]:
    g = DihedralGroup(n)
    s = g.sylow_subgroup(p)
    order = s.order()
    gord = g.order()
    want = largest_power(gord, p)
    issub = g.is_subgroup(g) and all(g.contains(gen) for gen in s.generators)
    print("D(%d) |G|=%d p=%d sylow_order=%d want=%d issub=%s" % (n, gord, p, order, want, issub))
    if order != want:
        print("  FAIL order mismatch")
        ok = False
    if not issub:
        print("  FAIL not a subgroup")
        ok = False

# Req 5.1
ip = DihedralGroup(10).is_primitive()
print("DihedralGroup(10).is_primitive() =", ip)
if ip is not False:
    ok = False
it = DihedralGroup(10).is_transitive()
print("DihedralGroup(10).is_transitive() =", it)
if it is not True:
    ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: DihedralGroup(18).sylow_subgroup(2) order == 4, no IndexError
# Req 4.1, 4.2
import sys
from sympy.combinatorics.named_groups import DihedralGroup
try:
    g = DihedralGroup(18)
    s = g.sylow_subgroup(2)
    o = s.order()
    print("DihedralGroup(18).sylow_subgroup(2).order() =", o)
    if o != 4:
        print("FAIL: expected 4")
        sys.exit(1)
    sys.exit(0)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-19954: minimal_blocks index-aligned supersession removal fix.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 4.1/4.2, POSITIVE CONTROL): DihedralGroup(18).sylow_subgroup(2).order()==4, no IndexError. PATCHED: HOLDS (4). BASE: VIOLATED (raises IndexError: list assignment index out of range) -> discriminates.
- probe_2 (Req 4.3): DihedralGroup(50).sylow_subgroup(2).order()==4. PATCHED HOLDS.
- probe_3 (Req 3.3): DihedralGroup(6) yields exactly 2 minimal block systems {(2 blocks of 3),(3 blocks of 2)}, no trivial single-block system. PATCHED HOLDS.
- probe_4 (Req 3.1/3.2): for D(6,12,18,20) no duplicate numbered form and no system strictly refined by another; intransitive group <(0 1)> on 4 pts returns False. PATCHED HOLDS.
- probe_5 (Req 4.4/5.1): sylow order == largest power of p dividing |G| and is a subgroup across D(6,18,50,12,30@p2/3/5); DihedralGroup(10).is_primitive()==False, is_transitive()==True. PATCHED HOLDS.

Candidate wrong-fix (weak.diff): removes the crashing `del num_blocks[i],blocks[i]` but does NOT prune blocks/num_blocks in step with rep_blocks, so superseded (coarser) systems are never discarded — the naive 'just stop the crash' fix a weak reading permits. REJECTED by probes 1,2,3,4,5: it retains the trivial single-block/coarser systems, causing sylow_subgroup to return the whole group (order 36/100/60 instead of 4). This demonstrates the suite discriminates a requirements-conforming-looking but incorrect implementation, and that the requirements are not too weak in this dimension.

All 5 probes hold on patched; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: DihedralGroup(18).sylow_subgroup(2) order == 4, no IndexError
# Req 4.1, 4.2
import sys
from sympy.combinatorics.named_groups import DihedralGroup
try:
    g = DihedralGroup(18)
    s = g.sylow_subgroup(2)
    o = s.order()
    print("DihedralGroup(18).sylow_subgroup(2).order() =", o)
    if o != 4:
        print("FAIL: expected 4")
        sys.exit(1)
    sys.exit(0)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-19954: minimal_blocks index-aligned supersession removal fix.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 4.1/4.2, POSITIVE CONTROL): DihedralGroup(18).sylow_subgroup(2).order()==4, no IndexError. PATCHED: HOLDS (4). BASE: VIOLATED (raises IndexError: list assignment index out of range) -> discriminates.
- probe_2 (Req 4.3): DihedralGroup(50).sylow_subgroup(2).order()==4. PATCHED HOLDS.
- probe_3 (Req 3.3): DihedralGroup(6) yields exactly 2 minimal block systems {(2 blocks of 3),(3 blocks of 2)}, no trivial single-block system. PATCHED HOLDS.
- probe_4 (Req 3.1/3.2): for D(6,12,18,20) no duplicate numbered form and no system strictly refined by another; intransitive group <(0 1)> on 4 pts returns False. PATCHED HOLDS.
- probe_5 (Req 4.4/5.1): sylow order == largest power of p dividing |G| and is a subgroup across D(6,18,50,12,30@p2/3/5); DihedralGroup(10).is_primitive()==False, is_transitive()==True. PATCHED HOLDS.

Candidate wrong-fix (weak.diff): removes the crashing `del num_blocks[i],blocks[i]` but does NOT prune blocks/num_blocks in step with rep_blocks, so superseded (coarser) systems are never discarded — the naive 'just stop the crash' fix a weak reading permits. REJECTED by probes 1,2,3,4,5: it retains the trivial single-block/coarser systems, causing sylow_subgroup to return the whole group (order 36/100/60 instead of 4). This demonstrates the suite discriminates a requirements-conforming-looking but incorrect implementation, and that the requirements are not too weak in this dimension.

All 5 probes hold on patched; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patched code (perm_groups.py minimal_blocks) has two mutually-exclusive branches on each retained rep_blocks entry r vs candidate cell rep: B1 = `if len(r) > len(rep) and rep.issubset(r)` -> candidate is finer -> mark RETAINED entry for removal (blocks_remove_mask[i]=True). B2 = `elif len(r) < len(rep) and r.issubset(rep)` -> a retained entry of strictly smaller cardinality is a subset of the candidate -> minimal=False; break -> the CANDIDATE is dropped (not appended).

Requirement mapping is exact: Req 2.2 = B1 (candidate rep strict subset of larger retained r -> discard retained), Req 2.3 = B2 (retained r strictly smaller and subset of candidate -> drop candidate). These are OPPOSITE subset directions; the requirement text explicitly says so ("This is the opposite direction of Requirement 2.2").

Instrumented Dih(18): B1 events=[(rep=9,r=18),(3,9),(3,6)], B2 events=[(rep=18,r=9),(18,3),(9,3)]. B2 (Req 2.3's condition) demonstrably fires and drops candidates -> Req 2.3 is faithful and observable. Dih(50)/Dih(25) similarly show B2_dropCandidate events.

The recorded G-PANEL-2 fail is INCORRECT: it cited the B1 event (rep_len=9 < r_len=18) and claimed 'the candidate Req 2.3 says to discard is in fact retained.' But that event has the candidate cell SMALLER than the retained cell, i.e. Req 2.2's precondition, not Req 2.3's (which requires a strictly-smaller RETAINED cell that is a subset of the candidate). The panel misidentified the branch and wrongly asserted Req 2.2/2.3 describe 'the identical condition' and 'self-contradict'; they describe opposite directions and the code implements both correctly.

All probes pass on patched tree: Dih(18)/Dih(50)/Dih(6).sylow_subgroup(2).order()==4 (Req 4), Dih(6).minimal_blocks()==[[0,1,0,1,0,1],[0,1,2,0,1,2]] (Req 3.3), non-transitive group -> False (Req 3.2), Dih(10).is_primitive()==False (Req 5.1). (Note: G-PANEL-3's leakage concern about the literal expected list is a separate leakage matter, not a faithfulness divergence — behavior itself is correct.)


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The two test-derived inputs (DihedralGroup(18), DihedralGroup(50)=2*25, sylow_subgroup(p=2)) and the IndexError at the del-during-iteration site are ALL present verbatim in the public problem_statement, so Req 4.1-4.3 leak nothing new. The asserted order==4 matches the test but is the correct mathematical result of the publicly-named computation — legitimate behavioral translation. The gold-invented identifier blocks_remove_mask never appears; the document describes the three parallel collections generically (block systems / numbered forms / representative cells), which is legitimate change localization, not gold-code transmission. Illustrative examples DihedralGroup(6) two-block-systems (Req 3.3) and DihedralGroup(10).is_primitive()==False (Req 5.1) are NOT in the test_patch (which only adds the 18/50 sylow assertions); they are independently reasoned behavioral facts, not reconstructions of hidden parametrized cases. No test names, file paths, FAIL_TO_PASS ids, quoted test/gold lines, or test-shaped enumerations found.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
