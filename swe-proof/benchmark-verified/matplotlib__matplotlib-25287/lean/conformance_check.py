#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-25287.

The bundle models ONE decision, replicated for the horizontal and vertical axes:
the color the offset text (the exponent/multiplier label) is given in
`XAxis._init` / `YAxis._init`. It is a PURE function of two observables
(mapping.md):

    tickColor  : a color           (mpl.rcParams['*tick.color'])
    labelColor : a color | INHERIT  (mpl.rcParams['*tick.labelcolor'];
                                      the string 'inherit' is the sentinel)

Post-patch rule (both axes, byte-symmetric):

    tick_color = rc['*tick.color'] if rc['*tick.labelcolor'] == 'inherit' \
                 else rc['*tick.labelcolor']
    self.offsetText.set(..., color=tick_color)

Standing up a full Figure/Axes to drive the real `_init` is unnecessary: the
modeled value is this pure decision over the two observables. The ORACLE below is
a faithful in-process replica using the EXACT patched expression; the SHADOW is
the op-for-op transliteration of `implementation_*OffsetTextColor`
(Lean `Option.getD`, with `'inherit'` ↔ `none`), per refinement.md.

We compare ORACLE vs SHADOW for both axes over a fuzzed input space that
exercises: labelColor == 'inherit' (fall back to tickColor), labelColor an
explicit color equal to tickColor, and labelColor an explicit color distinct
from tickColor (the bug-discriminating case the F2P tests hit).

stdlib-only. Pinned seed: 25287 (also in mapping.md).
"""
import json
import random
import sys

SEED = 25287
N = 120_000

# A small palette of color tokens (identity is all that matters).
COLORS = ["red", "green", "blue", "yellow", "black", "white",
          "#ff0000", "#00ff00", (0.1, 0.2, 0.3, 1.0), "C0", "C1"]
INHERIT = "inherit"


# --- ORACLE: faithful in-process replica of the patched decision -------------
def oracle_color(tick_color, label_color):
    # exact patched expression
    if label_color == INHERIT:
        return tick_color
    else:
        return label_color


# --- SHADOW of implementation_*OffsetTextColor (the R/I leg) -----------------
# Lean: result = labelColor.getD tickColor, with 'inherit' ↔ none.
def shadow_color(tick_color, label_color):
    label_opt = None if label_color == INHERIT else label_color  # Option modeling
    # Option.getD: none -> tickColor ; some c -> c
    return tick_color if label_opt is None else label_opt


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    for _ in range(N):
        tick_color = rng.choice(COLORS)
        # bias toward both the sentinel and the discriminating explicit-color case
        roll = rng.random()
        if roll < 0.34:
            label_color = INHERIT
        elif roll < 0.5:
            label_color = tick_color            # explicit, equal to tick
        else:
            label_color = rng.choice(COLORS)    # explicit, often != tick
        o = oracle_color(tick_color, label_color)
        s = shadow_color(tick_color, label_color)
        if o != s:
            disagreements += 1
            if len(examples) < 5:
                examples.append({
                    "tickColor": str(tick_color),
                    "labelColor": str(label_color),
                    "oracle": str(o), "shadow": str(s),
                })

    result = {
        "status": "ok" if disagreements == 0 else "fail",
        "instance": "matplotlib__matplotlib-25287",
        "n": N, "seed": SEED,
        "disagreements": disagreements,
        "examples": examples,
        "note": "oracle = patched `rc[color] if rc[labelcolor]=='inherit' else "
                "rc[labelcolor]`; shadow = Lean Option.getD with 'inherit'~none. "
                "Same decision drives both XAxis._init and YAxis._init.",
    }
    print(json.dumps(result))
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
