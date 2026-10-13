#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15554 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The @Pure helpers ``reusable``,
``matches_default`` and ``matches_constrained`` — the ones the impl region
calls — copy over as plain functions (Requires stripped). The fourth pure
predicate ``no_eligible_match`` is contract-side only (an unbounded Forall
used in the postcondition, never called by the impl) and so has no executable
role in the shadow. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
``django.db.models.sql.query.Query.join`` imported from /testbed (the gate
applies patch.diff before this script runs; this script does NOT apply it).
Each trial builds a real ``Query`` whose ``alias_map`` holds real ``Join``
objects mirroring the model's slot registry, calls ``Query.join`` with the
incoming ``Join`` and the reuse configuration under test, and observes the
single behavior the model pins: whether a FRESH alias was created (the
returned alias is not one of the pre-existing slot aliases) or an existing
slot was reused.

Type bridge (mapping.md section 2, the interning bijection):
  - slot base identity ``base[i]`` (int)  <->  the identity-minus-refinement
    part of a real ``Join``: distinct ints map to distinct
    (table_name, join_field) pairs (parent_alias/class held constant), equal
    ints to the identical pair, so int equality mirrors ``identity[:-1]``
    equality exactly;
  - refinement tag ``frel[i]`` (int, 0 = none)  <->  ``Join.filtered_relation``:
    tag 0 maps to ``None``; a positive tag t maps to a ``FilteredRelation``
    built deterministically from t (same relation_name/alias/condition), so
    equal tags give ``==`` refinements and distinct tags give ``!=`` ones;
  - ``reuse_all=True``  <->  ``reuse=None``; ``reuse_all=False``  <->
    ``reuse`` = the set of slot aliases flagged in ``reuse_mask``;
  - ``constrained``  <->  the keyword-selected branch of the real function
    (True is exercised with the keyword set and the mask-derived reuse set;
    the empty-mask corner, where the real guard falls back to the other
    branch, is included — both sides must then report a fresh slot).

Input domain: exactly the Requires of install_join — three aligned arrays
(base, frel int arrays plus a bool mask of the same length) and
Implies(constrained, not reuse_all). Generation covers boundary registries
(empty; singletons; the decisive same-base distinct-refinement pair;
duplicate slots; all-True/all-False masks) crossed with every reuse mode,
plus randomized fuzz registries.

>= 1e5 Requires-satisfying inputs in total (each generated registry is
checked under several reuse configurations; every configuration is one
input). Pinned fuzz seed: 155540 (recorded here per the bundle contract).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; no hypothesis needed).
"""
import random
import sys

SEED = 155540
N_FUZZ = 30000  # x >=4 reuse configurations each => >= 120000 inputs


# --- shadow: @Pure helpers from model.py, contracts stripped ------------------

def reusable(i, n, reuse_all, reuse_mask):
    """A slot index i is reuse-eligible if all slots are reusable (the
    unconstrained case) or i is flagged in the supplied reuse mask."""
    return reuse_all or reuse_mask[i]


def matches_default(i, n, jb, jf, base, frel):
    """The default-mode match predicate: slot i matches the incoming
    descriptor (jb, jf) on BOTH the base relation identity AND the refinement
    tag."""
    return base[i] == jb and frel[i] == jf


def matches_constrained(i, n, jb, base):
    """The constrained-mode match predicate: slot i matches on the base
    relation identity alone."""
    return base[i] == jb


# --- shadow: impl region of install_join, copied verbatim (contracts and ------
# --- loop-invariant calls stripped) --------------------------------------------

def install_join(base, frel, reuse_all, reuse_mask, jb, jf, constrained):
    n = len(base)
    found = False
    i = 0
    while i < n:
        if constrained:
            if reuse_mask[i] and matches_constrained(i, n, jb, base):
                found = True
        else:
            if reusable(i, n, reuse_all, reuse_mask) and \
                    matches_default(i, n, jb, jf, base, frel):
                found = True
        i = i + 1
    return not found
    # (True iff a FRESH slot must be created)


# --- oracle plumbing: the real patched repo objects ---------------------------

def _load_real():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.db.models import Q
    from django.db.models.query_utils import FilteredRelation
    from django.db.models.sql.query import Query
    from django.db.models.sql.datastructures import Join
    return Q, FilteredRelation, Query, Join


class _StubField(object):
    """Minimal join-field stand-in: Join.__init__ only asks it for its
    joining columns; identity comparison is by object identity, which the
    interning below keeps consistent (one instance per base int)."""

    def get_joining_columns(self):
        return ()


class Bridge(object):
    """Realizes the mapping.md section 2 bijection on real repo objects."""

    def __init__(self):
        self.Q, self.FilteredRelation, self.Query, self.Join = _load_real()
        self._fields = {}

    def _field(self, b):
        if b not in self._fields:
            self._fields[b] = _StubField()
        return self._fields[b]

    def _fr(self, tag):
        if tag == 0:
            return None
        fr = self.FilteredRelation("rel%d" % tag,
                                   condition=self.Q(flag=tag))
        fr.alias = "fra%d" % tag
        return fr

    def make_join(self, b, tag):
        # distinct b -> distinct (table_name, join_field); equal b -> equal.
        return self.Join("tab%d" % b, "basetab", None, None,
                         self._field(b), False,
                         filtered_relation=self._fr(tag))

    def build_query(self, slots):
        q = self.Query(None)
        for i, (b, tag) in enumerate(slots):
            j = self.make_join(b, tag)
            alias = "slot%d" % i
            q.table_map.setdefault(j.table_name, []).append(alias)
            q.alias_refcount[alias] = 0
            j.table_alias = alias
            q.alias_map[alias] = j
        return q

    def real_fresh_needed(self, slots, reuse_set_indices, jb, jf,
                          keyword_branch):
        """Drive the REAL Query.join and observe the pinned behavior: True
        iff a fresh alias was created (not one of the pre-existing slots)."""
        q = self.build_query(slots)
        pre = set(q.alias_map)
        inc = self.make_join(jb, jf)
        if reuse_set_indices is None:
            reuse = None
        else:
            reuse = set("slot%d" % i for i in reuse_set_indices)
        alias = q.join(inc, reuse=reuse,
                       reuse_with_filtered_relation=keyword_branch)
        return alias not in pre


# --- differential harness ------------------------------------------------------

FAILURES = [0]
CASES = [0]


def check_one(bridge, slots, reuse_mask, jb, jf, mode):
    """mode: 'default-all' (reuse_all, unconstrained), 'default-mask'
    (mask-derived reuse set, unconstrained), 'constrained' (mask-derived
    reuse set, constrained branch), 'default-all-kw' (reuse_all with the
    branch keyword set — the real guard ignores it when no reuse set is
    supplied, and the model's precondition ties constrained to a supplied
    reuse set, so the shadow runs unconstrained)."""
    base = [b for b, _ in slots]
    frel = [t for _, t in slots]
    masked = [i for i, m in enumerate(reuse_mask) if m]

    if mode == "default-all":
        shadow = install_join(base, frel, True, reuse_mask, jb, jf, False)
        real = bridge.real_fresh_needed(slots, None, jb, jf, False)
    elif mode == "default-all-kw":
        shadow = install_join(base, frel, True, reuse_mask, jb, jf, False)
        real = bridge.real_fresh_needed(slots, None, jb, jf, True)
    elif mode == "default-mask":
        shadow = install_join(base, frel, False, reuse_mask, jb, jf, False)
        real = bridge.real_fresh_needed(slots, masked, jb, jf, False)
    elif mode == "constrained":
        shadow = install_join(base, frel, False, reuse_mask, jb, jf, True)
        real = bridge.real_fresh_needed(slots, masked, jb, jf, True)
    else:
        raise AssertionError(mode)

    CASES[0] += 1
    if shadow != real:
        FAILURES[0] += 1
        print("DISAGREEMENT mode=%s slots=%r mask=%r jb=%d jf=%d -> "
              "shadow=%r real=%r"
              % (mode, slots, reuse_mask, jb, jf, shadow, real))
        return False
    return True


MODES = ("default-all", "default-all-kw", "default-mask", "constrained")


def boundary_cases(bridge):
    """Small exhaustive sweep: registries of size 0..2 over 2 base ids x
    3 refinement tags, all masks, all incoming descriptors, all modes.
    Includes the decisive pair: same base, distinct refinements."""
    ids = (1, 2)
    tags = (0, 1, 2)
    slot_vocab = [(b, t) for b in ids for t in tags]
    registries = [[]]
    registries += [[s] for s in slot_vocab]
    registries += [[s1, s2] for s1 in slot_vocab for s2 in slot_vocab]
    for slots in registries:
        n = len(slots)
        for mask_bits in range(1 << n):
            mask = [(mask_bits >> i) & 1 == 1 for i in range(n)]
            for jb in ids:
                for jf in tags:
                    for mode in MODES:
                        check_one(bridge, slots, mask, jb, jf, mode)


def fuzz_cases(bridge, rng):
    ids = (1, 2, 3)
    tags = (0, 1, 2, 3)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 6)
        slots = [(rng.choice(ids), rng.choice(tags)) for _ in range(n)]
        mask = [rng.random() < 0.5 for _ in range(n)]
        jb = rng.choice(ids)
        jf = rng.choice(tags)
        for mode in MODES:
            check_one(bridge, slots, mask, jb, jf, mode)


def main():
    bridge = Bridge()
    boundary_cases(bridge)
    fuzz_cases(bridge, random.Random(SEED))
    if FAILURES[0]:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs"
              % (FAILURES[0], CASES[0]))
        return 1
    print("G-CONF OK: shadow install_join == real patched reuse-vs-fresh "
          "decision over %d Requires-satisfying inputs "
          "(boundary sweep + %d fuzz registries x %d modes, seed %d); "
          "0 disagreements" % (CASES[0], N_FUZZ, len(MODES), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
