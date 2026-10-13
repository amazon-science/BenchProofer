#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25479
(nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert lines) stripped:
  * the `Cmap` constructor (the model of the independent-snapshot primitive:
    a fresh object whose lookup-table list is rebuilt element by element);
  * `colormaps_equal` (extension-flag check, length check, elementwise loop);
  * `register_named` (fresh snapshot, snapshot relabelled to the chosen
    registration label, stored under that label).
The @Pure helper `seq_eq` copies over as a plain function on a tuple-backed
PSeq shim and is kept as a redundant internal cross-check of the equality
loop's result. There is no @ContractOnly callee.

ORACLES: the REAL patched repo functions the model models per mapping.md --
`matplotlib.colors.Colormap.__eq__` (invoked as `a == b` on real colormap
objects) and `matplotlib.cm.ColormapRegistry.register` (invoked on a fresh
real registry per trial, pre-seeded with unrelated entries so the
no-other-entry-disturbed frame clauses are observable). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched modules importable.

TYPE BRIDGE (mapping.md section 2):
  * label `int` token <-> `str`: the injective map t -> "label-%d" % t.
    Only label equality/inequality is observed, so any injection is faithful.
  * lookup-table `List[int]` <-> real `_lut` ndarray: a NON-NEGATIVE entry
    token maps injectively to a determinate RGBA row
    ((t>>16)/255, (t>>8&255)/255, (t&255)/255, 1); a NEGATIVE entry token maps
    to an INDETERMINATE row, one carrying a NaN channel. The real colormap is a
    `ListedColormap` over those rows, initialised. The initialised table is the
    colour rows plus trailing rows that are a pure function of the colour rows
    (identical defaults across trials). The relation the real table comparison
    supplies is therefore NOT plain token identity: it is elementwise `==`
    folded over the rows, under which an indeterminate row compares unequal to
    every row including one holding the same value. That is exactly the
    relation the model's `entry_eq` states, and both sides of it -- determinate
    and indeterminate -- are generated below. Token lists are kept non-empty:
    a real initialised lookup table always has at least one colour row.
  * extension flag `int` token <-> the flag's full value domain
    False/True/'neither'/'min'/'max'/'both', by the injection in
    EXTEND_DOMAIN. The flag is observed through ==/!= only, so any injection is
    faithful; injectivity over the WHOLE domain is what the bridge must supply,
    because with equal tables the real comparison separates every one of the 15
    distinct pairs. A two-valued carrier would merge 4 of the 6 values, so the
    generators draw the token over the whole index range and the boundary table
    below enumerates all 15 pairs explicitly.
  * registry `Dict[int, Cmap]` <-> a real registry's by-label store
    (`_cmaps`, the binding named in mapping.md), key-bridged by the label
    injection. Registration labels are kept distinct from pre-seeded labels:
    per mapping.md the modelled behaviour is the explicit-fresh-label path
    (the label-collision path raises in the real registry and is outside
    the modelled domain).

Per register trial the compared observables are: membership of the chosen
label; independence of the stored snapshot from the supplied object; the
snapshot's own label / extension flag / lookup-table contents; the supplied
mapping left untouched; and every other registry entry keeping exactly its
previous membership and bound object (frame clauses). Per equality trial the
compared observable is the boolean verdict, plus a read-only check that
neither operand was mutated.

Note on the register-side table comparison: `copy()` reproduces the stored
rows BITWISE, so the snapshot-fidelity checks compare tables with
`equal_nan=True`. Copy fidelity is a claim about bit patterns, which holds for
an indeterminate row too; the ==-relation used by the equality oracle is a
different question and is compared with the default there.

>= 1e5 Requires-satisfying inputs: boundary cases + 70000 equality fuzz
trials + 30000 registration fuzz trials. Pinned fuzz seed: 25479.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib.colors import ListedColormap          # real colormap objects
from matplotlib.cm import ColormapRegistry            # REAL patched registry

SEED = 25479
N_FUZZ_EQ = 70_000
N_FUZZ_REG = 30_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def of(cls, iterable):
        s = cls()
        s._t = tuple(iterable)
        return s

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def drop(self, m):
        return PSeq.of(self._t[m:])

    def take(self, m):
        return PSeq.of(self._t[:m])

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq.of(lst)


# --- pure region of model.py, contracts stripped ------------------------------

def entry_eq(x, y):
    return x == y and x >= 0


def seq_eq(a, b):
    if len(a) == 0 or len(b) == 0:
        return len(a) == 0 and len(b) == 0
    return entry_eq(a[0], b[0]) and seq_eq(a.drop(1), b.drop(1))


# --- the Cmap constructor of model.py, verbatim, contract calls stripped ------

class Cmap:
    def __init__(self, name, colorbar_extend, lut):
        self.name = name
        self.colorbar_extend = colorbar_extend
        self.lut = []
        i = 0
        while i < len(lut):
            # (Invariant(...) contract calls stripped here)
            self.lut.append(lut[i])
            i = i + 1
        # (one Assert(...) contract call stripped here)


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def colormaps_equal(self, other):
    if self.colorbar_extend != other.colorbar_extend:
        return False
    if len(self.lut) != len(other.lut):
        # (two Assert(...) contract calls stripped here)
        return False
    i = 0
    while i < len(self.lut):
        # (Invariant(...) and Assert(...) contract calls stripped here)
        if not entry_eq(self.lut[i], other.lut[i]):
            return False
        i = i + 1
    # (two Assert(...) contract calls stripped here)
    return True


def register_named(reg, name, cmap):
    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)
    # The published snapshot is relabelled to the chosen registration label, so
    # that a later lookup by that label yields a mapping whose own label matches
    # the label it was looked up under.
    snapshot.name = name
    reg[name] = snapshot


# --- bridge: int tokens <-> concrete labels / colour rows ----------------------

def label_str(t):
    """Injective label bridge: int token -> a distinct string label."""
    return "label-%d" % t


# The extension flag's FULL documented value domain, indexed by the model's int
# token. The model compares the flag with ==/!= only, so any injection is
# faithful; injectivity over the whole domain is what matters, because with
# equal luts the real __eq__ separates every pair of these values.
EXTEND_DOMAIN = (False, True, "neither", "min", "max", "both")


def extend_value(t):
    """Injective extension-flag bridge: int token -> a distinct real flag value."""
    return EXTEND_DOMAIN[t]


def entry_color(t):
    """Injective lookup-table-entry bridge: int token -> a distinct RGBA row.
    A NON-NEGATIVE token is a DETERMINATE row: deterministic float arithmetic,
    so equal tokens give bitwise-equal rows and distinct tokens (within the
    24-bit fuzz domain) give distinct rows. A NEGATIVE token is an
    INDETERMINATE row: it carries a NaN channel, which the elementwise `==`
    inside np.array_equal reports unequal to every row, itself included --
    exactly what the model's entry_eq encodes by requiring x >= 0."""
    if t < 0:
        u = -t
        return (float("nan"), ((u >> 8) & 0xFF) / 255.0, (u & 0xFF) / 255.0, 1.0)
    return (((t >> 16) & 0xFF) / 255.0,
            ((t >> 8) & 0xFF) / 255.0,
            (t & 0xFF) / 255.0,
            1.0)


def make_real(name_token, extend_token, lut_tokens):
    """A real, initialised colormap carrying the bridged state."""
    cm = ListedColormap([entry_color(t) for t in lut_tokens],
                        name=label_str(name_token))
    cm.colorbar_extend = extend_value(extend_token)
    cm._init()
    return cm


def real_lut_for(lut_tokens):
    """The initialised real lookup table a token list bridges to."""
    return make_real(0, 0, lut_tokens)._lut


# --- equality trials ------------------------------------------------------------

def eq_trial(a_spec, b_spec):
    """a_spec/b_spec = (name_token, extend, lut_tokens). Returns an error
    string on disagreement, else None."""
    (an, ae, alut), (bn, be, blut) = a_spec, b_spec

    A = Cmap(an, ae, list(alut))          # ae/be are the model's int tokens
    B = Cmap(bn, be, list(blut))
    shadow = colormaps_equal(A, B)
    # redundant cross-check against the pure-region content fold
    spec_pred = (A.colorbar_extend == B.colorbar_extend
                 and seq_eq(ToSeq(A.lut), ToSeq(B.lut)))
    assert shadow == spec_pred, "shadow internal cross-check (seq_eq)"
    # read-only operands (model directive 5): neither side mutated
    assert (A.name, A.colorbar_extend, tuple(A.lut)) == (an, ae, tuple(alut))
    assert (B.name, B.colorbar_extend, tuple(B.lut)) == (bn, be, tuple(blut))

    ra = make_real(an, ae, alut)
    rb = make_real(bn, be, blut)
    real = (ra == rb)                                 # REAL __eq__

    if bool(real) != bool(shadow):
        return ("DISAGREEMENT (equality verdict)\n"
                "  a=(name=%r, extend=%r, lut=%r)\n"
                "  b=(name=%r, extend=%r, lut=%r)\n"
                "  shadow=%r  real=%r"
                % (an, ae, list(alut), bn, be, list(blut), shadow, real))
    return None


# --- registration trials ---------------------------------------------------------

def reg_trial(seeded, name_token, cmap_spec):
    """seeded = list of (key_token, spec); cmap_spec = (name_token', extend,
    lut_tokens); name_token is fresh (not among the seeded keys). Returns an
    error string on disagreement, else None."""
    cn, ce, clut = cmap_spec

    # shadow side
    sreg = {k: Cmap(kn, ke, list(klut)) for k, (kn, ke, klut) in seeded}
    s_before = dict(sreg)
    scmap = Cmap(cn, ce, list(clut))
    register_named(sreg, name_token, scmap)

    # real side: a fresh registry pre-seeded with the bridged entries
    rreg = ColormapRegistry(
        {label_str(k): make_real(kn, ke, klut)
         for k, (kn, ke, klut) in seeded})
    r_before = dict(rreg._cmaps)
    rcmap = make_real(cn, ce, clut)
    saved = (rcmap.name, rcmap.colorbar_extend, np.array(rcmap._lut, copy=True))
    rreg.register(rcmap, name=label_str(name_token))   # REAL register

    ctx = ("  seeded_keys=%r reg_label_token=%r supplied=(name=%r, extend=%r, "
           "lut=%r)" % ([k for k, _ in seeded], name_token, cn, ce, list(clut)))

    # (1) membership of the chosen label, and key sets correspond
    if name_token not in sreg or label_str(name_token) not in rreg._cmaps:
        return ("DISAGREEMENT (chosen label not registered)\n%s\n"
                "  shadow_keys=%r real_keys=%r"
                % (ctx, sorted(sreg), sorted(rreg._cmaps)))
    if {label_str(k) for k in sreg} != set(rreg._cmaps):
        return ("DISAGREEMENT (registry key sets differ)\n%s\n"
                "  shadow_keys=%r real_keys=%r"
                % (ctx, sorted(sreg), sorted(rreg._cmaps)))

    s_snap = sreg[name_token]
    r_snap = rreg._cmaps[label_str(name_token)]

    # (2) the stored snapshot is an independent object on both sides
    if (s_snap is scmap) != (r_snap is rcmap):
        return ("DISAGREEMENT (snapshot independence)\n%s\n"
                "  shadow_stored_is_supplied=%r real_stored_is_supplied=%r"
                % (ctx, s_snap is scmap, r_snap is rcmap))

    # (3) the snapshot's own label, extension flag, and lookup-table contents
    if label_str(s_snap.name) != r_snap.name:
        return ("DISAGREEMENT (stored snapshot's own label)\n%s\n"
                "  shadow=%r (token %r)  real=%r"
                % (ctx, label_str(s_snap.name), s_snap.name, r_snap.name))
    # No bool() coercion here: the flag domain has more than two mutually
    # distinguishable values, and coercing would hide a carrier that dropped the
    # distinction. The shadow's token is bridged and compared to the real value.
    if extend_value(s_snap.colorbar_extend) != r_snap.colorbar_extend:
        return ("DISAGREEMENT (stored snapshot's extension flag)\n%s\n"
                "  shadow=%r (token %r)  real=%r"
                % (ctx, extend_value(s_snap.colorbar_extend),
                   s_snap.colorbar_extend, r_snap.colorbar_extend))
    if not np.array_equal(r_snap._lut, real_lut_for(s_snap.lut), equal_nan=True):
        return ("DISAGREEMENT (stored snapshot's lookup-table contents)\n%s\n"
                "  shadow_lut_tokens=%r\n  real_lut=%r"
                % (ctx, s_snap.lut, r_snap._lut))

    # (4) the supplied mapping is left untouched on both sides
    if (scmap.name, scmap.colorbar_extend, tuple(scmap.lut)) != \
            (cn, ce, tuple(clut)):
        return ("DISAGREEMENT (shadow mutated the supplied mapping)\n%s\n"
                "  after=(name=%r, extend=%r, lut=%r)"
                % (ctx, scmap.name, scmap.colorbar_extend, scmap.lut))
    if (rcmap.name != saved[0] or rcmap.colorbar_extend != saved[1]
            or not np.array_equal(rcmap._lut, saved[2], equal_nan=True)):
        return ("DISAGREEMENT (real call mutated the supplied mapping)\n%s\n"
                "  before=(name=%r, extend=%r)  after=(name=%r, extend=%r)"
                % (ctx, saved[0], saved[1], rcmap.name, rcmap.colorbar_extend))

    # (5) frame clauses: every other entry keeps its membership and its object
    for k, _ in seeded:
        if k == name_token:
            continue
        if sreg.get(k) is not s_before[k]:
            return ("DISAGREEMENT (shadow disturbed another registry entry)\n"
                    "%s\n  key=%r" % (ctx, k))
        if rreg._cmaps.get(label_str(k)) is not r_before[label_str(k)]:
            return ("DISAGREEMENT (real call disturbed another registry "
                    "entry)\n%s\n  key=%r" % (ctx, k))
    return None


# --- input generation --------------------------------------------------------------

BOUNDARY_EQ = [
    # (a_spec, b_spec): specs are (name_token, extend_token, lut_tokens).
    # extend_token indexes EXTEND_DOMAIN; a NEGATIVE lut token is an
    # indeterminate (NaN-carrying) row.
    ((1, 0, [10, 20, 30]), (1, 0, [10, 20, 30])),   # identical
    ((1, 0, [10, 20, 30]), (2, 0, [10, 20, 30])),   # labels differ only
    ((1, 1, [10, 20, 30]), (2, 1, [10, 20, 30])),   # ... with flag True
    ((1, 0, [10, 20, 30]), (1, 1, [10, 20, 30])),   # flag flipped
    ((1, 0, [10, 20, 30]), (2, 1, [10, 20, 30])),   # label+flag differ
    ((1, 0, [10, 20, 30]), (1, 0, [10, 20, 31])),   # last entry differs
    ((1, 0, [10, 20, 30]), (1, 0, [11, 20, 30])),   # first entry differs
    ((1, 0, [10, 20, 30]), (1, 0, [10, 21, 30])),   # middle entry differs
    ((1, 0, [10, 20, 30]), (1, 0, [10, 20])),       # shorter table
    ((1, 0, [10, 20]), (1, 0, [10, 20, 30])),       # longer table
    ((1, 0, [10]), (2, 0, [10])),                   # single-entry tables
    ((1, 0, [10]), (1, 0, [20])),                   # single-entry differ
    ((7, 1, [0, 0, 0]), (8, 1, [0, 0, 0])),         # duplicate entries
    ((7, 0, [5, 5]), (7, 0, [5, 5, 5])),            # dup, length differs
    # --- every pair of DISTINCT extension-flag values over IDENTICAL tables:
    # the real __eq__ separates all of them, so this is what a non-injective
    # flag carrier would fail.
    ((1, 0, [10, 20, 30]), (1, 2, [10, 20, 30])),   # False  vs 'neither'
    ((1, 0, [10, 20, 30]), (1, 3, [10, 20, 30])),   # False  vs 'min'
    ((1, 0, [10, 20, 30]), (1, 4, [10, 20, 30])),   # False  vs 'max'
    ((1, 0, [10, 20, 30]), (1, 5, [10, 20, 30])),   # False  vs 'both'
    ((1, 1, [10, 20, 30]), (1, 2, [10, 20, 30])),   # True   vs 'neither'
    ((1, 1, [10, 20, 30]), (1, 3, [10, 20, 30])),   # True   vs 'min'
    ((1, 1, [10, 20, 30]), (1, 4, [10, 20, 30])),   # True   vs 'max'
    ((1, 1, [10, 20, 30]), (1, 5, [10, 20, 30])),   # True   vs 'both'
    ((1, 2, [10, 20, 30]), (1, 3, [10, 20, 30])),   # 'neither' vs 'min'
    ((1, 2, [10, 20, 30]), (1, 4, [10, 20, 30])),   # 'neither' vs 'max'
    ((1, 2, [10, 20, 30]), (1, 5, [10, 20, 30])),   # 'neither' vs 'both'
    ((1, 3, [10, 20, 30]), (1, 4, [10, 20, 30])),   # 'min'  vs 'max'
    ((1, 3, [10, 20, 30]), (1, 5, [10, 20, 30])),   # 'min'  vs 'both'  <-- witness
    ((1, 4, [10, 20, 30]), (1, 5, [10, 20, 30])),   # 'max'  vs 'both'
    # ... and each flag value against ITSELF over identical tables (equal),
    # so the flag leg is exercised in the passing direction too.
    ((1, 2, [10, 20, 30]), (2, 2, [10, 20, 30])),   # 'neither', labels differ
    ((1, 3, [10, 20, 30]), (2, 3, [10, 20, 30])),   # 'min', labels differ
    ((1, 4, [10, 20, 30]), (2, 4, [10, 20, 30])),   # 'max', labels differ
    ((1, 5, [10, 20, 30]), (2, 5, [10, 20, 30])),   # 'both', labels differ
    # --- indeterminate rows: the elementwise == is not reflexive there, so each
    # of these is UNEQUAL even when the token lists are identical.
    ((1, 0, [-7, 20, 30]), (1, 0, [-7, 20, 30])),   # indeterminate HEAD, same
    ((1, 0, [10, -7, 30]), (1, 0, [10, -7, 30])),   # indeterminate MIDDLE, same
    ((1, 0, [10, 20, -7]), (1, 0, [10, 20, -7])),   # indeterminate TAIL, same
    ((1, 0, [-7]), (1, 0, [-7])),                   # singleton indeterminate
    ((1, 0, [-7, -7]), (1, 0, [-7, -7])),           # all rows indeterminate
    ((1, 0, [-7, 20, 30]), (1, 0, [-8, 20, 30])),   # two DIFFERENT indeterminate
    ((1, 0, [-7, 20, 30]), (1, 0, [7, 20, 30])),    # indeterminate vs determinate
    ((1, 3, [-7, 20, 30]), (1, 3, [-7, 20, 30])),   # indeterminate + equal str flag
    ((1, 3, [-7, 20, 30]), (1, 5, [-7, 20, 30])),   # indeterminate + differing flag
    ((1, 0, [-7, 20]), (1, 0, [-7, 20, 30])),       # indeterminate + length differs
]

BOUNDARY_REG = [
    # (seeded, name_token, cmap_spec); cmap_spec = (name_token, extend_token, luts)
    ([], 100, (1, 0, [10, 20, 30])),              # fresh label != supplied label
    ([], 100, (100, 0, [10, 20, 30])),            # label == supplied label
    ([], 100, (1, 1, [10, 20, 30])),              # extension flag True
    ([], 100, (1, 0, [10])),                      # single-entry table
    ([(50, (50, 0, [1, 2])), (51, (51, 1, [3]))],
     100, (1, 0, [10, 20])),                      # pre-seeded entries kept
    ([(50, (50, 0, [1, 2]))],
     100, (50, 0, [1, 2])),                       # supplied label collides with
                                                  # a seeded KEY; registration
                                                  # label is still fresh
    # every extension-flag value must survive into the stored snapshot EXACTLY,
    # which is what a collapsed flag carrier would fail:
    ([], 100, (1, 2, [10, 20, 30])),              # 'neither'
    ([], 100, (1, 3, [10, 20, 30])),              # 'min'
    ([], 100, (1, 4, [10, 20, 30])),              # 'max'
    ([], 100, (1, 5, [10, 20, 30])),              # 'both'
    # indeterminate rows are copied BITWISE by copy(), so the snapshot's table
    # must still match the supplied one row for row:
    ([], 100, (1, 0, [-7, 20, 30])),              # indeterminate head
    ([], 100, (1, 5, [-7, -8])),                  # all indeterminate + str flag
    ([(50, (50, 3, [-1, 2]))],
     100, (1, 4, [-3, 20])),                      # seeded + supplied both odd
]


def fuzz_extend_token(rng):
    """An extension-flag token drawn over the flag's WHOLE value domain, not
    just its two-valued part: the real comparison separates all six values, so
    a generator that only ever produced two of them would leave the rest of the
    domain unshadowed."""
    return rng.randrange(len(EXTEND_DOMAIN))


def fuzz_entry_token(rng):
    """A lookup-table-entry token. A NEGATIVE token bridges to an
    indeterminate row (see entry_color), which the real elementwise comparison
    treats as unequal to everything; drawn often enough that both the
    determinate and the indeterminate side of the entry relation are shadowed,
    and rarely enough that determinate tables still dominate."""
    if rng.random() < 0.15:
        return -rng.randrange(1, 1 << 16)
    return rng.randrange(1 << 24)


def fuzz_eq_pair(rng):
    """A Requires-satisfying operand pair, biased toward near-equal shapes so
    both verdicts are exercised."""
    def fresh_lut():
        return [fuzz_entry_token(rng) for _ in range(rng.randint(1, 6))]

    an = rng.randrange(1 << 20)
    ae = fuzz_extend_token(rng)
    alut = fresh_lut()
    bn = an if rng.random() < 0.5 else rng.randrange(1 << 20)
    be = ae if rng.random() < 0.5 else fuzz_extend_token(rng)
    r = rng.random()
    if r < 0.40:
        blut = list(alut)                       # identical contents
    elif r < 0.55 and len(alut) >= 1:
        blut = list(alut)                       # single-entry perturbation
        blut[rng.randrange(len(blut))] = fuzz_entry_token(rng)
    elif r < 0.70:
        blut = list(alut)[:-1] if len(alut) > 1 else list(alut) + [fuzz_entry_token(rng)]
    else:
        blut = fresh_lut()
    return (an, ae, alut), (bn, be, blut)


def fuzz_reg_input(rng):
    """A Requires-satisfying registration input with a fresh registration
    label (the modelled domain) over a small pre-seeded registry."""
    n_seed = rng.randint(0, 3)
    seed_keys = rng.sample(range(1000), n_seed)
    seeded = [(k, (k if rng.random() < 0.5 else rng.randrange(1 << 20),
                   fuzz_extend_token(rng),
                   [fuzz_entry_token(rng) for _ in range(rng.randint(1, 4))]))
              for k in seed_keys]
    name_token = rng.randrange(1000, 2000)      # disjoint from seeded keys
    cn = name_token if rng.random() < 0.3 else rng.randrange(1 << 20)
    ce = fuzz_extend_token(rng)
    clut = [fuzz_entry_token(rng) for _ in range(rng.randint(1, 6))]
    return seeded, name_token, (cn, ce, clut)


def main():
    rng = random.Random(SEED)
    checked = 0

    for a_spec, b_spec in BOUNDARY_EQ:
        err = eq_trial(a_spec, b_spec)
        if err:
            print(err)
            return 1
        checked += 1
    for seeded, name_token, cmap_spec in BOUNDARY_REG:
        err = reg_trial(seeded, name_token, cmap_spec)
        if err:
            print(err)
            return 1
        checked += 1
    n_boundary = checked

    for _ in range(N_FUZZ_EQ):
        a_spec, b_spec = fuzz_eq_pair(rng)
        err = eq_trial(a_spec, b_spec)
        if err:
            print(err)
            return 1
        checked += 1

    for _ in range(N_FUZZ_REG):
        seeded, name_token, cmap_spec = fuzz_reg_input(rng)
        err = reg_trial(seeded, name_token, cmap_spec)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched functions on %d inputs "
          "(%d boundary + %d equality fuzz + %d registration fuzz, seed %d); "
          "operands and registries undisturbed outside the specified writes "
          "on every trial."
          % (checked, n_boundary, N_FUZZ_EQ, N_FUZZ_REG, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
