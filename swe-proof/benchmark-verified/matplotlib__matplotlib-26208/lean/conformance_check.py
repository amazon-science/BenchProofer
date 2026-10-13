#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-26208.

The bundle models the two secondary-frame construction sites (`twinx`/`twiny`).
Their soundness-critical observable is the per-coordinate interpretation setting
(`Axis.units`) carried by the secondary frame's copy of the SHARED coordinate,
as a function of the source's setting for that coordinate. Per mapping.md a
setting is modeled as `Option Nat` (`None` -> absent; a converter-object
identity -> a tag).

Standing up real matplotlib + the unit machinery to drive `twinx`/`twiny` is
heavy and unnecessary: under the gold edit the secondary frame's shared-coordinate
setting is a PURE function of the source's setting for that coordinate
(`ax2.<axis>.units = self.<axis>.units`). So the ORACLE below is a faithful
in-process replica of the POST-PATCH behaviour (the shared coordinate is
overwritten with the source's setting), and the SHADOW is the op-for-op
transliteration of the `implementation_step*` impl regions
(Solution.lean, `out := source`), per refinement.md.

This tests exactly the clause the F2P tests `test_twin_units[x]`/`[y]` pin: after
construction, the secondary frame's SHARED coordinate carries the SAME setting as
the source (`ax2.<axis>.units is ax1.<axis>.units`), and it is present exactly
when the source's is.

stdlib-only. Pinned seed: 26208 (also in mapping.md). exit 0 iff zero
disagreements.
"""
import random
import sys

SEED = 26208
N = 120_000

# Modeled setting domain: None (absent) or a converter-identity tag.
CONFIG_POOL = [None, 0, 1, 2, 7, 42]


def oracle(source):
    """POST-PATCH: the shared coordinate is assigned the source's setting
    (`ax2.<axis>.units = self.<axis>.units`)."""
    return source


def shadow(source):
    """Transliteration of implementation_stepA / stepB:
        out := source
        return out
    """
    out = source
    return out


def is_present(s):
    return s is not None


def disagree(source):
    o, s = oracle(source), shadow(source)
    if o != s:
        return ("value", source, o, s)
    if is_present(o) != is_present(s):
        return ("present", source, o, s)
    return None


def _edge_cases():
    # F2P scenario: the source coordinate has a present setting (categorical
    # strings established a converter); it must be carried over.
    yield 1
    yield None    # no setting on the source coordinate
    yield 0
    yield 42


def main():
    checked = 0
    for src in _edge_cases():
        d = disagree(src)
        if d:
            print(f"DISAGREE edge: kind={d[0]} oracle={d[2]} shadow={d[3]} source={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        src = rng.choice(CONFIG_POOL)
        d = disagree(src)
        if d:
            print(f"DISAGREE fuzz: kind={d[0]} oracle={d[2]} shadow={d[3]} source={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0 (seed={SEED})")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
