#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25775
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (this model's impl regions contain no Requires/Ensures calls
inline -- the contracts live outside the marked impl regions, so the copy is
literal). There are no @Pure helpers and no @ContractOnly callees in this
bundle; the modelled behaviour is plain in-object state, so the shadow is
directly executable with no PSeq shim needed.

ORACLE: the REAL patched repo symbols the model models per mapping.md --
`matplotlib.text.Text`. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.
Headless Agg backend; Text artists need no live canvas for the state under
test.

Type bridge (mapping.md section 2), all identity-on-booleans:
  - Glyph.pref            <-> Text._antialiased, observed via get_antialiased()
  - Glyph.dirty           <-> Text.stale
  - build_glyph(default,supplied)
                          <-> Text(...) constructed with
                              mpl.rcParams['text.antialiased'] = default and
                              the optional keyword `antialiased`; the model's
                              absent value None corresponds both to omitting
                              the keyword and to passing antialiased=None
                              (the constructor's own default) -- the fuzzer
                              exercises both spellings of "absent"
  - set_pref              <-> Text.set_antialiased
  - get_pref              <-> Text.get_antialiased
  - copy_state(dst, src)  <-> dst.update_from(src)
For the update/copy trials the redraw flag is driven to False on both sides
first, so the postcondition "flag ends True" is observed as a fresh effect
rather than a leftover; the constructor trials compare the flag as-is (both
sides construct with the flag True).

Input domain: every parameter is a bool or Optional[bool] and the Requires
clauses demand only heap access, so every element of the finite value domain
is Requires-satisfying. Boundary section enumerates the whole cross product
(including the Annotation subclass, which mapping.md records as forwarding
the keyword through unchanged); the fuzz section then runs 100000 randomized
stateful trials (random interleavings of construct / set / get / copy over a
pool of live object pairs) with a PINNED seed.

Pinned fuzz seed: 25775.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
from matplotlib.text import Annotation, Text

SEED = 25775
N_FUZZ = 100_000


# --- shadow: model.py class + impl regions, verbatim, contracts stripped ------

class Glyph:
    def __init__(self, pref):
        self.pref = pref      # type: bool
        self.dirty = True     # type: bool


def build_glyph(default, supplied):
    g = Glyph(default)
    if supplied is not None:
        set_pref(g, supplied)
    return g


def set_pref(g, value):
    g.pref = value
    g.dirty = True


def get_pref(g):
    return g.pref


def copy_state(dst, src):
    dst.pref = src.pref
    dst.dirty = True


# --- oracle plumbing -----------------------------------------------------------

def make_real(default, supplied, omit_kwarg, cls=Text):
    """Construct the real artist under global default `default`; `supplied`
    is the optional per-object value (None = absent). When absent,
    `omit_kwarg` picks between the two equivalent spellings: leaving the
    keyword out entirely vs. passing its own None default explicitly."""
    mpl.rcParams["text.antialiased"] = default
    kwargs = {}
    if supplied is not None or not omit_kwarg:
        kwargs["antialiased"] = supplied
    if cls is Annotation:
        return Annotation("t", xy=(0.0, 0.0), **kwargs)
    return Text(0.0, 0.0, "t", **kwargs)


def fmt(pair_desc, shadow_pref, shadow_dirty, real_pref, real_dirty):
    return ("DISAGREEMENT\n  input: %s\n"
            "  shadow: pref=%r dirty=%r\n  real:   pref=%r stale=%r"
            % (pair_desc, shadow_pref, shadow_dirty, real_pref, real_dirty))


def check_pair(desc, g, t):
    """Compare the modelled observables of a shadow/real pair."""
    if get_pref(g) != t.get_antialiased() or bool(g.dirty) != bool(t.stale):
        return fmt(desc, get_pref(g), g.dirty, t.get_antialiased(), t.stale)
    return None


def build_trial(default, supplied, omit_kwarg, cls=Text):
    g = build_glyph(default, supplied)
    t = make_real(default, supplied, omit_kwarg, cls)
    desc = ("construct cls=%s default=%r supplied=%r omit_kwarg=%r"
            % (cls.__name__, default, supplied, omit_kwarg))
    return check_pair(desc, g, t), (g, t)


def set_trial(g, t, value):
    g.dirty = False
    t.stale = False
    set_pref(g, value)
    t.set_antialiased(value)
    return check_pair("set value=%r" % (value,), g, t)


def get_trial(g, t):
    if get_pref(g) != t.get_antialiased():
        return ("DISAGREEMENT\n  input: read-back\n  shadow=%r\n  real=%r"
                % (get_pref(g), t.get_antialiased()))
    return None


def copy_trial(gd, td, gs, ts):
    src_before = get_pref(gs)
    gd.dirty = False
    td.stale = False
    copy_state(gd, gs)
    td.update_from(ts)
    err = check_pair("copy src.pref=%r" % (src_before,), gd, td)
    if err:
        return err
    # the source must be untouched on both sides (read-only frame)
    if get_pref(gs) != src_before or ts.get_antialiased() != src_before:
        return ("DISAGREEMENT\n  input: copy source frame src.pref=%r\n"
                "  shadow src=%r real src=%r"
                % (src_before, get_pref(gs), ts.get_antialiased()))
    return None


def main():
    checked = 0
    bools = (True, False)
    opts = (None, True, False)

    # --- boundary: full cross product of the finite domain -------------------
    for cls in (Text, Annotation):
        for default in bools:
            for supplied in opts:
                for omit in (True, False):
                    if supplied is not None and not omit:
                        continue  # a present value has one spelling
                    err, _ = build_trial(default, supplied, omit, cls)
                    if err:
                        print(err)
                        return 1
                    checked += 1
    for default in bools:
        for supplied in opts:
            for value in bools:
                err, (g, t) = build_trial(default, supplied, True)
                if err is None:
                    err = set_trial(g, t, value)
                if err is None:
                    err = get_trial(g, t)
                if err:
                    print(err)
                    return 1
                checked += 3
    for d_pref in bools:
        for s_pref in bools:
            e1, (gd, td) = build_trial(True, d_pref, True)
            e2, (gs, ts) = build_trial(True, s_pref, True)
            err = e1 or e2 or copy_trial(gd, td, gs, ts)
            if err:
                print(err)
                return 1
            checked += 3
    n_boundary = checked

    # --- fuzz: randomized stateful interleavings, pinned seed -----------------
    rng = random.Random(SEED)
    pool = []          # live (shadow, real) pairs evolving in parallel
    POOL_MAX = 32
    while checked - n_boundary < N_FUZZ:
        op = rng.random()
        if not pool or op < 0.25:
            default = rng.choice(bools)
            supplied = rng.choice(opts)
            omit = rng.choice((True, False)) if supplied is None else True
            err, pair = build_trial(default, supplied, omit)
            if err:
                print(err)
                return 1
            pool.append(pair)
            if len(pool) > POOL_MAX:
                pool.pop(rng.randrange(len(pool)))
        elif op < 0.55:
            g, t = pool[rng.randrange(len(pool))]
            err = set_trial(g, t, rng.choice(bools))
            if err:
                print(err)
                return 1
        elif op < 0.75:
            g, t = pool[rng.randrange(len(pool))]
            err = get_trial(g, t)
            if err:
                print(err)
                return 1
        else:
            gd, td = pool[rng.randrange(len(pool))]
            gs, ts = pool[rng.randrange(len(pool))]
            if td is ts:
                continue
            err = copy_trial(gd, td, gs, ts)
            if err:
                print(err)
                return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched methods on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
