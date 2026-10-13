# P2 adversarial audit — matplotlib__matplotlib-25332

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
# Req 1.1 (POSITIVE CONTROL): a Grouper with objects joined survives pickling
# (no TypeError about pickling a weakref). Must HOLD patched, FAIL at base.
import pickle
import matplotlib.cbook as cbook


class Foo:
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return "Foo(%r)" % self.s


def main():
    a, b, c, d = Foo('a'), Foo('b'), Foo('c'), Foo('d')
    g = cbook.Grouper()
    g.join(a, b)
    g.join(c, d)
    try:
        blob = pickle.dumps(g)
    except TypeError as e:
        print("VIOLATION: pickling joined Grouper raised TypeError:", e)
        return 1
    print("OK: pickled joined Grouper, %d bytes" % len(blob))
    return 0


raise SystemExit(main())
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2.1 & 2.2: after a pickle round trip, the restored Grouper reports the
# SAME partition as the original WHEN OBSERVED THROUGH its membership test
# (__contains__) and its sibling query (get_siblings). Req 2.1 EXPLICITLY does
# NOT require preservation of the internal per-group list-object identity used
# by joined()/__iter__ dedup -- so we derive the partition ONLY from the two
# constrained operations (membership + get_siblings), never from __iter__ or
# joined().
#
# Grouper stores WEAK refs, so we keep referents alive across the round trip
# by pickling the objects together with the grouper (as a Figure keeps strong
# refs to its Axes).
import pickle
import matplotlib.cbook as cbook


class Foo:
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return "Foo(%r)" % self.s


def sib_set(g, o):
    return frozenset(x.s for x in g.get_siblings(o))


def main():
    a, b, c, d, e = (Foo(x) for x in 'abcde')
    g = cbook.Grouper()
    g.join(a, b)
    g.join(b, c)
    g.join(d, e)
    objs = [a, b, c, d, e]
    # original sibling-set per object (observed through get_siblings)
    orig = {o.s: sib_set(g, o) for o in objs}

    payload = {"objs": objs, "grp": g}
    r = pickle.loads(pickle.dumps(payload))
    rg = r["grp"]
    robjs = {o.s: o for o in r["objs"]}

    for lbl, want in orig.items():
        o = robjs[lbl]
        # membership must hold
        if o not in rg:
            print("VIOLATION: membership test fails for restored", lbl)
            return 1
        got = sib_set(rg, o)
        if got != want:
            print("VIOLATION: siblings for", lbl, "want", sorted(want),
                  "got", sorted(got))
            return 1

    # "two objects are siblings in restored iff siblings in original"
    for i in range(len(objs)):
        for j in range(len(objs)):
            li, lj = objs[i].s, objs[j].s
            orig_sib = lj in orig[li]
            rest_sib = robjs[lj].s in sib_set(rg, robjs[li])
            if orig_sib != rest_sib:
                print("VIOLATION: sibling relation differs for", li, lj,
                      "orig", orig_sib, "restored", rest_sib)
                return 1

    print("OK: membership+sibling partition preserved across round trip:",
          {k: sorted(v) for k, v in orig.items()})
    return 0


raise SystemExit(main())
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.2 & 1.4: captured state contains NO live weakref objects (every handle
# represented by its referent), and restoring wraps referents back into weak
# references (internal representation identical to a freshly-constructed
# Grouper: _mapping keys are weakref.ref, values are lists of weakref.ref).
import weakref
import matplotlib.cbook as cbook


class Foo:
    def __init__(self, s):
        self.s = s


def main():
    a, b, c = Foo('a'), Foo('b'), Foo('c')
    g = cbook.Grouper()
    g.join(a, b)
    g.join(b, c)

    # __getstate__ must exist (Req 1: explicit pickle-protocol support).
    if not hasattr(g, "__getstate__"):
        print("VIOLATION: Grouper has no __getstate__")
        return 1
    state = g.__getstate__()
    mapping = state["_mapping"]

    # Req 1.2: no live weakref objects anywhere in captured mapping.
    for k, vs in mapping.items():
        if isinstance(k, weakref.ReferenceType):
            print("VIOLATION: captured key is a weakref:", k)
            return 1
        for v in vs:
            if isinstance(v, weakref.ReferenceType):
                print("VIOLATION: captured value is a weakref:", v)
                return 1
        # referents must be the actual objects
        if not all(isinstance(v, Foo) for v in vs):
            print("VIOLATION: captured values are not referents:", vs)
            return 1
    print("OK getstate: no weakrefs in captured state; referents present")

    # Req 1.4: setstate rewraps into weakref.ref keys / lists of weakref.ref,
    # matching a freshly-constructed grouper's representation.
    if not hasattr(g, "__setstate__"):
        print("VIOLATION: Grouper has no __setstate__")
        return 1
    g2 = cbook.Grouper()
    g2.__setstate__(state)
    m2 = g2._mapping
    # reference type of a directly-constructed grouper
    fresh = cbook.Grouper(init=[a])
    fresh_key = next(iter(fresh._mapping))
    if type(fresh_key) is not weakref.ReferenceType:
        print("VIOLATION: fresh grouper key not weakref.ref?", type(fresh_key))
        return 1
    for k, vs in m2.items():
        if type(k) is not weakref.ReferenceType:
            print("VIOLATION: restored key not weakref.ref:", type(k))
            return 1
        if not all(type(v) is weakref.ReferenceType for v in vs):
            print("VIOLATION: restored values not weakref.ref:", [type(v) for v in vs])
            return 1
    print("OK setstate: restored representation uses weakref-keyed mapping")
    return 0


raise SystemExit(main())
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1 & 3.2: a Figure with aligned x/y labels can be pickled (no TypeError)
# and unpickled into a valid figure whose _align_label_groups are restored in
# the weakref-backed form used by a fresh figure.
import weakref
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    fig, axs = plt.subplots(2, 2)
    for ax in axs.flat:
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.set_xlabel("x")
        ax.set_ylabel("y")
    fig.align_labels()

    # groupers now hold weakrefs -> base would fail here
    try:
        blob = pickle.dumps(fig)
    except TypeError as e:
        print("VIOLATION: pickling aligned figure raised TypeError:", e)
        return 1
    print("OK: pickled aligned figure, %d bytes" % len(blob))

    fig2 = pickle.loads(blob)
    grps = fig2._align_label_groups
    if set(grps) != {"x", "y"}:
        print("VIOLATION: restored _align_label_groups keys:", set(grps))
        return 1
    import matplotlib.cbook as cbook
    for k in ("x", "y"):
        g = grps[k]
        if not isinstance(g, cbook.Grouper):
            print("VIOLATION: restored group", k, "not a Grouper:", type(g))
            return 1
        for key, vs in g._mapping.items():
            if type(key) is not weakref.ReferenceType:
                print("VIOLATION: restored figure grouper key not weakref:", type(key))
                return 1
            if not all(type(v) is weakref.ReferenceType for v in vs):
                print("VIOLATION: restored figure grouper vals not weakref")
                return 1
    # sanity: reconstructed figure is a valid Figure
    from matplotlib.figure import Figure
    if not isinstance(fig2, Figure):
        print("VIOLATION: unpickled object is not a Figure:", type(fig2))
        return 1
    print("OK: aligned figure round-trips; groupers weakref-backed & valid figure")
    return 0


raise SystemExit(main())
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.3 & 4.2: pickling a figure that has NOT had its labels aligned must
# still work (regression), and a populated figure with aligned labels must
# round-trip without error.
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    # (a) unaligned figure still pickles
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 2, 1])
    try:
        blob = pickle.dumps(fig)
        pickle.loads(blob)
    except Exception as e:
        print("VIOLATION: unaligned figure failed to pickle round-trip:", repr(e))
        return 1
    print("OK: unaligned figure round-trips")

    # (b) populated figure with several plot types + aligned labels round-trips
    fig2, axs = plt.subplots(2, 2)
    x = np.linspace(0, 2 * np.pi, 50)
    axs[0, 0].plot(x, np.sin(x))
    axs[0, 1].scatter(x, np.cos(x))
    axs[1, 0].bar(range(5), range(5))
    axs[1, 1].imshow(np.random.RandomState(0).rand(5, 5))
    for ax in axs.flat:
        ax.set_xlabel("xl")
        ax.set_ylabel("yl")
    fig2.align_labels()
    try:
        b2 = pickle.dumps(fig2)
        fig3 = pickle.loads(b2)
    except Exception as e:
        print("VIOLATION: populated aligned figure failed round-trip:", repr(e))
        return 1
    # render both to ensure reconstructed figure is drawable
    fig2.canvas.draw()
    fig3.canvas.draw()
    print("OK: populated aligned figure round-trips and renders")
    return 0


raise SystemExit(main())
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4.1: existing Grouper operations retain their semantics on a LIVE
# (non-deserialized) container, unaffected by added serialization support.
# Exercises join / __contains__ / joined / iter (disjoint groups) /
# get_siblings / remove. Uses only live-grouper guarantees (no cross-pickle).
import matplotlib.cbook as cbook


class Foo:
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return "Foo(%r)" % self.s


def main():
    a, b, c, d, e = (Foo(x) for x in 'abcde')
    g = cbook.Grouper()
    g.join(a, b)
    g.join(b, c)
    g.join(d, e)

    # membership
    for o in (a, b, c, d, e):
        if o not in g:
            print("VIOLATION: __contains__ says", o, "not present")
            return 1
    f = Foo('f')
    if f in g:
        print("VIOLATION: __contains__ true for never-joined object")
        return 1

    # joined
    if not g.joined(a, c):
        print("VIOLATION: a,c should be joined (transitively)")
        return 1
    if g.joined(a, d):
        print("VIOLATION: a,d should NOT be joined")
        return 1

    # disjoint groups via iteration
    groups = sorted(sorted(x.s for x in grp) for grp in g)
    if groups != [['a', 'b', 'c'], ['d', 'e']]:
        print("VIOLATION: disjoint groups wrong:", groups)
        return 1

    # siblings
    sibs = sorted(x.s for x in g.get_siblings(a))
    if sibs != ['a', 'b', 'c']:
        print("VIOLATION: get_siblings(a) wrong:", sibs)
        return 1

    # remove
    g.remove(a)
    if a in g:
        print("VIOLATION: a still present after remove")
        return 1
    sibs2 = sorted(x.s for x in g.get_siblings(b))
    if sibs2 != ['b', 'c']:
        print("VIOLATION: after removing a, siblings(b) wrong:", sibs2)
        return 1

    print("OK: live Grouper operations preserved:", groups, "-> removed a ->", sibs2)
    return 0


raise SystemExit(main())
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1 (POSITIVE CONTROL): a Grouper with objects joined survives pickling
# (no TypeError about pickling a weakref). Must HOLD patched, FAIL at base.
import pickle
import matplotlib.cbook as cbook


class Foo:
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return "Foo(%r)" % self.s


def main():
    a, b, c, d = Foo('a'), Foo('b'), Foo('c'), Foo('d')
    g = cbook.Grouper()
    g.join(a, b)
    g.join(c, d)
    try:
        blob = pickle.dumps(g)
    except TypeError as e:
        print("VIOLATION: pickling joined Grouper raised TypeError:", e)
        return 1
    print("OK: pickled joined Grouper, %d bytes" % len(blob))
    return 0


raise SystemExit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib-25332: gold adds Grouper.__getstate__/__setstate__ (resolve weakrefs->strong on capture, re-wrap on restore) so figures with aligned labels pickle. Base Grouper is weakref.ref/list-based.

Suite (all HOLD patched):
- probe_1 (Req 1.1, POSITIVE CONTROL): joined Grouper pickles without TypeError. Patched HOLDS; base VIOLATED (TypeError: cannot pickle weakref.ReferenceType). Discriminates.
- probe_2 (Req 2.1/2.2): round trip preserves partition observed ONLY through __contains__ and get_siblings (deliberately NOT through joined()/__iter__, which Req 2.1 explicitly disclaims). Referents kept alive by pickling objects alongside grouper (as a Figure keeps strong refs to its Axes). Patched HOLDS; base VIOLATED (TypeError).
- probe_3 (Req 1.2/1.4): __getstate__ captures NO live weakrefs (referents present); __setstate__ re-wraps into weakref.ref-keyed mapping matching a fresh Grouper. HOLDS.
- probe_4 (Req 3.1/3.2): figure with align_labels() pickles + unpickles to a valid Figure with weakref-backed groupers. Patched HOLDS; base VIOLATED (TypeError).
- probe_5 (Req 3.3/4.2/4.3): unaligned figure still pickles (regression) + populated multi-plot-type figure with aligned labels round-trips and renders. HOLDS.
- probe_6 (Req 4.1): live Grouper ops (join/contains/joined/iter/get_siblings/remove) retain semantics. HOLDS.

Candidate patch lazy_drop_mapping (weak.diff): __getstate__ returns {'_mapping': {}} / __setstate__ sets empty mapping — the lazy fix that makes pickling merely SUCCEED. REJECTED by probe_2 (membership/partition lost after round trip: 'membership test fails for restored a'); probes 1,3,4,5,6 pass under it. This demonstrates the suite discriminates a wrong-but-pickles fix, so it is NOT a too-weak finding. (This candidate would also fail the hidden test_complete round-trip.)

IMPORTANT re prior stamp: the previously recorded G-EQ VIOLATION used a probe asserting joined() is preserved across a round trip. Requirement 2.1 EXPLICITLY disclaims that: it constrains ONLY membership/sibling queries and states the joined() identity query is NOT required to report objects as joined after a round trip. That prior probe was spec-violating (too strong), not a real defect. Gold indeed does not preserve joined() across pickle (per-group list identity is not restored), exactly as the requirements permit. My probe_2 correctly avoids joined()/__iter__ and passes.

All needed runs completed: 6/6 probes HOLD patched; positive control HOLDS patched & FAILS base (prepatch reproduced); >=1 candidate exercised and REJECTED. Verdict SOUND.

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
# Req 1.1 (POSITIVE CONTROL): a Grouper with objects joined survives pickling
# (no TypeError about pickling a weakref). Must HOLD patched, FAIL at base.
import pickle
import matplotlib.cbook as cbook


class Foo:
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return "Foo(%r)" % self.s


def main():
    a, b, c, d = Foo('a'), Foo('b'), Foo('c'), Foo('d')
    g = cbook.Grouper()
    g.join(a, b)
    g.join(c, d)
    try:
        blob = pickle.dumps(g)
    except TypeError as e:
        print("VIOLATION: pickling joined Grouper raised TypeError:", e)
        return 1
    print("OK: pickled joined Grouper, %d bytes" % len(blob))
    return 0


raise SystemExit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib-25332: gold adds Grouper.__getstate__/__setstate__ (resolve weakrefs->strong on capture, re-wrap on restore) so figures with aligned labels pickle. Base Grouper is weakref.ref/list-based.

Suite (all HOLD patched):
- probe_1 (Req 1.1, POSITIVE CONTROL): joined Grouper pickles without TypeError. Patched HOLDS; base VIOLATED (TypeError: cannot pickle weakref.ReferenceType). Discriminates.
- probe_2 (Req 2.1/2.2): round trip preserves partition observed ONLY through __contains__ and get_siblings (deliberately NOT through joined()/__iter__, which Req 2.1 explicitly disclaims). Referents kept alive by pickling objects alongside grouper (as a Figure keeps strong refs to its Axes). Patched HOLDS; base VIOLATED (TypeError).
- probe_3 (Req 1.2/1.4): __getstate__ captures NO live weakrefs (referents present); __setstate__ re-wraps into weakref.ref-keyed mapping matching a fresh Grouper. HOLDS.
- probe_4 (Req 3.1/3.2): figure with align_labels() pickles + unpickles to a valid Figure with weakref-backed groupers. Patched HOLDS; base VIOLATED (TypeError).
- probe_5 (Req 3.3/4.2/4.3): unaligned figure still pickles (regression) + populated multi-plot-type figure with aligned labels round-trips and renders. HOLDS.
- probe_6 (Req 4.1): live Grouper ops (join/contains/joined/iter/get_siblings/remove) retain semantics. HOLDS.

Candidate patch lazy_drop_mapping (weak.diff): __getstate__ returns {'_mapping': {}} / __setstate__ sets empty mapping — the lazy fix that makes pickling merely SUCCEED. REJECTED by probe_2 (membership/partition lost after round trip: 'membership test fails for restored a'); probes 1,3,4,5,6 pass under it. This demonstrates the suite discriminates a wrong-but-pickles fix, so it is NOT a too-weak finding. (This candidate would also fail the hidden test_complete round-trip.)

IMPORTANT re prior stamp: the previously recorded G-EQ VIOLATION used a probe asserting joined() is preserved across a round trip. Requirement 2.1 EXPLICITLY disclaims that: it constrains ONLY membership/sibling queries and states the joined() identity query is NOT required to report objects as joined after a round trip. That prior probe was spec-violating (too strong), not a real defect. Gold indeed does not preserve joined() across pickle (per-group list identity is not restored), exactly as the requirements permit. My probe_2 correctly avoids joined()/__iter__ and passes.

All needed runs completed: 6/6 probes HOLD patched; positive control HOLDS patched & FAILS base (prepatch reproduced); >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds Grouper.__getstate__/__setstate__ in cbook.py, resolving weakrefs to strong on capture and re-wrapping to weak on restore. Verified via probes on the patched image: (1) Req1 — __getstate__ produces {_mapping: strong-ref keys/values, no weakrefs, full partition}; __setstate__ rebuilds weakref-keyed mapping (restored grouper keys all weakref.ref). (2) Req2 — with referents kept alive across the pickle, get_siblings(a) and __contains__ preserved (sibling set matches {a,b}); joined() NOT preserved (False), which Req2.1 explicitly permits; empty grouper restores to empty {} (Req2.3). (3) Req3 — aligned figure pickles (len 97812) and unpickles to a Figure with weakref-backed _align_label_groups; non-aligned figure still pickles. (4) Req4 — live-container ops unchanged. The meta.json G-EQ=fail is an ADEQUACY verdict (a probe demanding joined() preservation the spec deliberately omits), a separate axis from faithfulness; on faithfulness the requirements and patched code agree everywhere.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes only behavior derivable from the PUBLIC problem_statement (align_labels + pickle failing with 'cannot pickle weakref.ReferenceType' TypeError) plus legitimate source localization. Checks: (1) No hidden test artifacts appear — no test file path (test_pickle.py), no test function/class names (test_complete, test_simple, etc.), no parametrization ids (cmapN, [png]). (2) Identifiers named (Grouper, _mapping, _align_label_groups, cbook.py, figure.py, align_xlabels/ylabels) are pre-existing source symbols, legitimate for localizing the change — none invented by the fix. (3) __getstate__/__setstate__ are standard pickle-protocol methods, not fix-invented names; the weak->strong-on-capture / strong->weak-on-restore description is the behavioral translation of the requirement and the only sensible mechanism, not a copy of gold code. (4) Req 4.2/4.3 reference a 'comprehensively populated figure combining many plot types with label alignment' — this gestures at the existing _generate_complete_test_figure fixture but does NOT enumerate the specific plot types (contourf/imshow/pcolor/errorbar/...) that the test uses, so there is no case-enumeration that mirrors the test rather than behavior. (5) Req 2.1's carve-out (the 'joined' identity query need not survive a round trip) reflects understanding of the gold implementation's semantics expressed as behavioral scope, not test transmission. Overall: translation of test-verified behavior into requirements + legitimate localization, which is the intended purpose — no transmission of the hidden tests or gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
