#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-10356 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean transliterated to Python over
              the *real* repo types, via the mapping.md bijection: `flattenSeq`
              (the in-order per-source flatten), `canonicalize` (element-wise
              annotation extraction with a first-offender refusal), `collectMarks`
              (select sources, assemble, canonicalize) and `attachMark`
              (own-only collection extended by the new annotation, refusal
              propagated).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `_pytest.mark.structures.get_unpacked_marks` / `store_mark`
              applied at base_commit (the real correctness oracle, G-RESOLVE).

Both sides are compared on TWO observables, not one:
  (1) the value produced on success, and
  (2) the REFUSAL — that an exception is raised at all, and WHICH object its
      message names. A shadow that skipped the canonicalizing step at post:386,
      or that named a different offender, disagrees here. (An earlier revision of
      this bundle folded that step away as an identity, so its shadow could not
      have observed either.)

The input generator covers every leg of refinement.md §A/§B:
  * class hierarchies of varying MRO depth and branching (A1/A2/A3), with
    per-class own lists assigned directly into `__dict__`;
  * lists mixing all three element shapes of mapping.md §2 — `Mark`,
    `MarkDecorator`, and objects that are neither — including several offenders
    in one assembly, so the first-offender rule is exercised (A4);
  * a class whose `pytestmark` is NOT a list (post:378-379 appends it as one
    element);
  * NON-class objects (A5) whose `pytestmark` is a list, a non-list, or absent —
    the leg the existing test at testing/test_mark.py:590-602 drives;
  * `store_mark` on classes whose own list is empty, canonical, wrapped, or holds
    an offender (B1/B2/B3), asserting additionally that a refused store leaves the
    stored attribute UNCHANGED.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch.diff applied),
stdlib + pytest only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys
import types

import pytest
from _pytest.mark.structures import Mark, get_unpacked_marks, store_mark

SEED = 10356
N_FUZZ = 20_000
MAX_REPORTED = 5

_NAMES = ["foo", "bar", "baz", "qux", "m1", "m2", "m3", "m4"]
_MARKS = {n: getattr(pytest.mark, n).mark for n in _NAMES}
_DECOS = {n: getattr(pytest.mark, n) for n in _NAMES}


class _Plain:
    """An element that is not, and does not carry, a Mark (mapping.md §2:
    Item.foreign)."""

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "<Plain %s>" % self.tag


class _WrapsJunk:
    """An element whose `.mark` exists but is not a Mark: the unwrap succeeds and
    the check still refuses, naming the UNWRAPPED value (post:400 then 402)."""

    def __init__(self, payload):
        self.mark = payload

    def __repr__(self):
        return "<WrapsJunk>"


# --- the R/I shadow: Solution.lean flattenSeq / canonicalize / collectMarks --

def flatten_seq(groups):
    """flattenSeq : List (List Item) -> List Item, in-order concatenation (the
    backward `while` fold of collectMarks computes exactly this; an empty source
    contributes nothing and does not end the assembly)."""
    out = []
    for g in groups:
        out.extend(g)
    return out


def mark_of(elem):
    """markOf : Item -> Option Mark (post:400-401)."""
    unwrapped = getattr(elem, "mark", elem)
    return unwrapped if isinstance(unwrapped, Mark) else None


def name_of(elem):
    """nameOf : Item -> Int — the object a refusal names (post:402)."""
    return getattr(elem, "mark", elem)


def canonicalize(elems):
    """canonicalize : List Item -> Outcome. ("collected", marks) or
    ("refused", offending_object), refusing at the FIRST offender."""
    out = []
    for elem in elems:
        m = mark_of(elem)
        if m is None:
            return ("refused", name_of(elem))
        out.append(m)
    return ("collected", out)


def with_mark(outcome, mark):
    """withMark : Outcome -> Mark -> Outcome — extend a collected sequence,
    propagate a refusal unchanged."""
    if outcome[0] == "refused":
        return outcome
    return ("collected", outcome[1] + [mark])


def shadow_collect(lineage, whole):
    """collectMarks (lineage) (whole): select sources, assemble, canonicalize."""
    selected = lineage if whole else [lineage[0] if lineage else []]
    return canonicalize(flatten_seq(selected))


def shadow_store(lineage, mark):
    """attachMark (lineage) (mark) = withMark (collectMarks lineage false) mark."""
    return with_mark(shadow_collect(lineage, False), mark)


# --- oracle side: run the patched functions, package the same Outcome shape ---

def oracle_collect(obj, whole):
    try:
        return ("collected", list(get_unpacked_marks(obj, consider_mro=whole)))
    except TypeError as exc:
        return ("refused", str(exc))


def same(shadow, oracle):
    """Compare the two Outcomes, refusal payload included."""
    if shadow[0] != oracle[0]:
        return False
    if shadow[0] == "collected":
        return shadow[1] == oracle[1]
    return oracle[1] == "got %s instead of Mark" % repr(shadow[1])


# --- the mapping.md §2 bijection from a real object to the Lean `lineage` ----

def own_elems(raw):
    """One source's `List Item`: the stored value if it is a list, else the
    singleton holding it (post:376-379 / post:382-385)."""
    return list(raw) if isinstance(raw, list) else [raw]


def lineage_of_class(cls):
    """The per-class OWN-element sequence along cls.__mro__ (class first)."""
    return [own_elems(x.__dict__.get("pytestmark", [])) for x in cls.__mro__]


def lineage_of_nonclass(obj):
    """A non-class object is a LENGTH-1 lineage (refinement.md A5)."""
    return [own_elems(getattr(obj, "pytestmark", []))]


# --- input generation -------------------------------------------------------

def rand_element(rng, tag):
    r = rng.random()
    if r < 0.55:
        return _MARKS[rng.choice(_NAMES)]
    if r < 0.80:
        return _DECOS[rng.choice(_NAMES)]
    kind = rng.randrange(4)
    if kind == 0:
        return _Plain(tag)
    if kind == 1:
        return type("pytestmark", (object,), {})
    if kind == 2:
        return "mark-%s" % tag
    return _WrapsJunk("junk-%s" % tag)


def rand_own_value(rng, tag):
    """A class's stored `pytestmark`: usually a list (possibly empty), sometimes
    a bare non-list value (which post:378-379 appends as one element)."""
    if rng.random() < 0.10:
        return rand_element(rng, tag)
    return [rand_element(rng, "%s.%d" % (tag, j))
            for j in range(rng.randint(0, 3))]


def build_random_class(rng):
    """A small random class hierarchy with own lists assigned DIRECTLY into
    __dict__ (store_mark itself refuses offenders, so it cannot be used to plant
    them). Returns the leaf class."""
    depth = rng.randint(1, 4)
    bases = (object,)
    leaf = None
    for level in range(depth):
        cls = type("C%d" % level, bases, {})
        if rng.random() < 0.85:
            cls.pytestmark = rand_own_value(rng, "L%d" % level)
        if level > 0 and rng.random() < 0.5:
            sib = type("S%d" % level, (object,), {})
            if rng.random() < 0.85:
                sib.pytestmark = rand_own_value(rng, "S%d" % level)
            bases = (cls, sib)
        else:
            bases = (cls,)
        leaf = cls
    return leaf


def build_random_nonclass(rng):
    """A module-like object: `pytestmark` a list, a bare value, or absent."""
    obj = types.SimpleNamespace()
    r = rng.random()
    if r < 0.45:
        obj.pytestmark = [rand_element(rng, "N%d" % j)
                          for j in range(rng.randint(0, 3))]
    elif r < 0.85:
        obj.pytestmark = rand_element(rng, "Nb")
    return obj


def main():
    rng = random.Random(SEED)
    disagreements = []
    stats = {"collect": 0, "store": 0, "nonclass": 0,
             "refused": 0, "collected": 0, "store_refused": 0}

    def record(site, detail, sh, orc):
        disagreements.append((site, detail, sh, orc))

    for _ in range(N_FUZZ):
        # ---- site A, class branch: both consider_mro settings ---------------
        leaf = build_random_class(rng)
        lineage = lineage_of_class(leaf)
        for whole in (True, False):
            sh = shadow_collect(lineage, whole)
            orc = oracle_collect(leaf, whole)
            stats["collect"] += 1
            stats["refused" if sh[0] == "refused" else "collected"] += 1
            if not same(sh, orc):
                record("collect", "whole=%r" % whole, sh, orc)

        # ---- site A, NON-class branch (refinement.md A5) ---------------------
        obj = build_random_nonclass(rng)
        nl = lineage_of_nonclass(obj)
        for whole in (True, False):
            sh = shadow_collect(nl, whole)
            orc = oracle_collect(obj, whole)
            stats["nonclass"] += 1
            if not same(sh, orc):
                record("nonclass", "whole=%r" % whole, sh, orc)

        # ---- site B: store_mark extends the OWN list only -------------------
        new_mark = _MARKS[rng.choice(_NAMES)]
        before_raw = leaf.__dict__.get("pytestmark", [])
        before_own = own_elems(before_raw)
        sh = shadow_store([before_own] + lineage[1:], new_mark)
        try:
            store_mark(leaf, new_mark)
            orc = ("collected", list(leaf.__dict__.get("pytestmark", [])))
        except TypeError as exc:
            orc = ("refused", str(exc))
            stats["store_refused"] += 1
            # a refused store must leave the stored attribute untouched
            after_raw = leaf.__dict__.get("pytestmark", [])
            if after_raw is not before_raw and after_raw != before_raw:
                record("store-frame", "attribute mutated by a refused store",
                       before_raw, after_raw)
        stats["store"] += 1
        if not same(sh, orc):
            record("store", "mark=%r" % (new_mark,), sh, orc)

        if len(disagreements) >= MAX_REPORTED:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s):" % len(disagreements))
        for site, detail, sh, orc in disagreements:
            print("  site=%s %s shadow=%r oracle=%r" % (site, detail, sh, orc))
        return 1

    # A run that never produced a refusal would attest nothing about the
    # canonicalizing leg (A4), which is half of what this check exists for.
    if stats["refused"] < 100 or stats["collected"] < 100:
        print("G-CONF FAIL: degenerate input distribution %r" % stats)
        return 1
    if stats["store_refused"] < 100:
        print("G-CONF FAIL: the store site never refused %r" % stats)
        return 1

    print("G-CONF OK: R/I shadow of flattenSeq/canonicalize/collectMarks/"
          "attachMark agrees with patch.diff behaviour on %d class-branch "
          "collections (%d collected, %d refused), %d non-class-branch "
          "collections and %d stores (%d refused), seed=%d, 0 disagreements; "
          "success values and refusal identities compared."
          % (stats["collect"], stats["collected"], stats["refused"],
             stats["nonclass"], stats["store"], stats["store_refused"], SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
