#!/usr/bin/env python3
r"""G-CONF differential conformance check for matplotlib__matplotlib-25775
(plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. Every op
in Solution.lean's impl region is pure R/I (no A-tagged callee).

The modeled observable is the EFFECTIVE per-object antialiasing flag a text
object carries, refined as follows (mapping.md §2):

  * SHADOW  — `textAntialiased`/`resolveAA` transliterated to Python over the
              real repo types: the per-object kwarg `antialiased` (`None` <->
              Lean `none`, `True`/`False` <-> `some true`/`some false`) and the
              ambient default `rcParams['text.antialiased']` (<-> the `ambient`
              Bool):
                  shadow_aa(requested, ambient)
                      = ambient     if requested is None
                      = requested   otherwise
  * ORACLE  — `patch.diff`'s behaviour: build the REAL patched
              `matplotlib.text.Text` (and `Annotation`) with that kwarg and that
              rcParam installed, and read `obj.get_antialiased()` (== the value
              `Text.draw` forwards to `gc.set_antialiased`, refinement.md §B).

Equivalence checked on every fuzzed configuration (requested, ambient):

      shadow_aa(requested, ambient)  ==  obj.get_antialiased()

for obj built as Text(.5,.5,"foo\nbar", antialiased=requested) and
Annotation("foo\nbar",(.5,.5), antialiased=requested), with
rcParams['text.antialiased'] = ambient at construction time (the resolution
happens in __init__, exactly when the F2P state tests observe it).

stdlib + matplotlib only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 25775
N_FUZZ = 100_000

# `antialiased` is omitted (None) by passing a sentinel: we must distinguish
# "no kwarg / None" from "True/False". The patched __init__ defaults the kwarg
# to None and only overrides when it is not None, so passing antialiased=None is
# observationally identical to omitting it.
REQUESTED_DOMAIN = [None, True, False]
AMBIENT_DOMAIN = [True, False]


def shadow_aa(requested, ambient):
    """resolveAA: the explicit per-object choice if supplied, else ambient."""
    if requested is None:
        return ambient
    return requested


def _setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    return matplotlib


def oracle_text_aa(mpl, requested, ambient):
    """patch.diff behaviour for a Text object: build it with the kwarg and the
    rcParam installed, then read get_antialiased()."""
    from matplotlib.text import Text
    mpl.rcParams["text.antialiased"] = ambient
    txt = Text(.5, .5, "foo\nbar", antialiased=requested)
    return txt.get_antialiased()


def oracle_annotation_aa(mpl, requested, ambient):
    """patch.diff behaviour for an Annotation object (antialiased forwarded
    through **kwargs to Text.__init__)."""
    from matplotlib.text import Annotation
    mpl.rcParams["text.antialiased"] = ambient
    annot = Annotation("foo\nbar", (.5, .5), antialiased=requested)
    return annot.get_antialiased()


def configs(n, rng):
    # boundary cases first (plan §4.1 step 4): the full product matrix
    for requested in REQUESTED_DOMAIN:
        for ambient in AMBIENT_DOMAIN:
            yield (requested, ambient)
    # discriminating cases the F2P tests exercise: explicit choice that differs
    # from the ambient default (the change the prepatch fails on)
    yield (True, False)
    yield (False, True)
    for _ in range(n):
        yield (rng.choice(REQUESTED_DOMAIN), rng.choice(AMBIENT_DOMAIN))


def main():
    mpl = _setup_mpl()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for requested, ambient in configs(N_FUZZ, rng):
        count += 1
        shadow = shadow_aa(requested, ambient)
        for kind, oracle_fn in (("Text", oracle_text_aa),
                                ("Annotation", oracle_annotation_aa)):
            oracle = oracle_fn(mpl, requested, ambient)
            # bool comparison: get_antialiased returns the raw stored value
            if bool(shadow) != bool(oracle):
                disagreements.append((kind, requested, ambient, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d configs:"
              % (len(disagreements), count))
        for kind, req, amb, sh, orc in disagreements:
            print("  [%s] requested=%r ambient=%r shadow=%r oracle=%r"
                  % (kind, req, amb, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of textAntialiased agrees with patch.diff "
          "behaviour (Text + Annotation get_antialiased()) on %d configs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
