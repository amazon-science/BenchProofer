#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25287
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model IS Python: the two contracted
functions `offset_color_primary` / `offset_color_secondary` and the pure
helpers `sentinel_inherit` / `effective_color` run directly once `PSeq` is
shimmed as a plain tuple constructor and `ToSeq` as tuple(). There are no
@ContractOnly callees (mapping.md section 3: the selection is expressed
directly), so nothing calls back into the repo from the shadow.

ORACLE: the REAL patched repo operation the model models per mapping.md --
the colour that `matplotlib.axis.XAxis._init` (site 1) and
`matplotlib.axis.YAxis._init` (site 2) give the axis offset text, as a
function of the configured pair rcParams['<axis>tick.color'] /
rcParams['<axis>tick.labelcolor']. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched package
importable. The driver sets the two rcParams, re-runs the real `_init` on a
live axis, and reads `axis.offsetText.get_color()` (`Text.set(color=v)`
stores the value verbatim and `get_color` returns it unchanged --
mapping.md section 2), which IS the selected colour value.

Type bridge (mapping.md section 2):
  * a colour value is a colour-name str in the repo and a List[int] of
    Unicode code points in the model: enc(s) = [ord(c) for c in s],
    dec = the inverse; equality of names <-> equality of code-point lists.
  * the sentinel value meaning "defer to the base colour" is the fixed word
    whose code points the model pins as a constant sequence.
  * rcParams validation may canonicalise a value on assignment (e.g. case
    folding of special names, '#'-prefixing of bare hex digit strings), so
    the model inputs are the values READ BACK from rcParams after
    assignment -- exactly the values the modelled site reads.

Input domain: the model's Requires demand only read permission on the two
lists, so every code-point list is Requires-satisfying; the bridgeable
subdomain is the set of colour values rcParams accepts for the two keys
(the base-colour key rejects the sentinel; the label-colour key accepts it).
Boundary cases: a cross product of representative colour names / hex strings
/ grayscale strings / single-letter and cycle shorthands for the base, times
the same pool plus the sentinel for the label -- including label == base,
the sentinel, and near-sentinel distinct colour names. Fuzz draws random
hex colours (with and without alpha), named colours, grayscale strings, and
the sentinel with elevated probability for the label slot.

>= 1e5 Requires-satisfying site-inputs: each driver iteration configures
BOTH sites independently and checks both, so 110 boundary pairs x 2 sites
+ 52,000 fuzz iterations x 2 sites = 104,220 checks.
Pinned fuzz seed: 25287.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 25287
N_FUZZ = 52_000


# --- shims for the model's pure-sequence carrier -------------------------------

def PSeq(*args):
    return tuple(args)


def ToSeq(xs):
    return tuple(xs)


# --- pure helpers from model.py, verbatim, decorators stripped -----------------

def sentinel_inherit():
    # the code points of the word that means "defer to the base colour"
    # i n h e r i t
    return PSeq(105, 110, 104, 101, 114, 105, 116)


def effective_color(base_color, label_color):
    """The colour the derived annotation should take: the explicit label colour,
    except when the label colour is the sentinel, in which case the base
    colour."""
    if label_color == sentinel_inherit():
        return base_color
    return label_color


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def offset_color_primary(base_color, label_color):
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: list
    else:
        tick_color = list(label_color)
    return tick_color


def offset_color_secondary(base_color, label_color):
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: list
    else:
        tick_color = list(label_color)
    return tick_color


# --- bridge: colour-name str <-> List[int] of code points ----------------------

def enc(s):
    return [ord(c) for c in s]


def dec(lst):
    return "".join(chr(i) for i in lst)


def check_one(mpl, xaxis, yaxis, base_x, label_x, base_y, label_y):
    """Configure both sites, re-run the real initialisation, and diff each
    site's selected offset-text colour against the corresponding shadow.
    Returns an error string on disagreement, else None."""
    mpl.rcParams["xtick.color"] = base_x
    mpl.rcParams["xtick.labelcolor"] = label_x
    mpl.rcParams["ytick.color"] = base_y
    mpl.rcParams["ytick.labelcolor"] = label_y

    # The model inputs are the configured values as the site reads them.
    eff = mpl.rcParams
    inputs = {
        "x": (eff["xtick.color"], eff["xtick.labelcolor"]),
        "y": (eff["ytick.color"], eff["ytick.labelcolor"]),
    }

    xaxis._init()  # the REAL patched operation under test, site 1
    yaxis._init()  # the REAL patched operation under test, site 2

    for site, axis, shadow_fn in (("x", xaxis, offset_color_primary),
                                  ("y", yaxis, offset_color_secondary)):
        base, label = inputs[site]
        shadow = shadow_fn(enc(base), enc(label))
        real = axis.offsetText.get_color()
        if not isinstance(real, str) or enc(real) != shadow:
            return ("DISAGREEMENT site=%s\n  base=%r label=%r\n"
                    "  shadow=%r (=%r)\n  real=%r"
                    % (site, base, label, shadow, dec(shadow), real))
    return None


# Values the base-colour key accepts (its validator rejects the sentinel).
BOUNDARY_BASES = [
    "black", "blue", "red", "#00ff00", "#123456", "white",
    "b", "C0", "tab:orange", "0.5",
]
# The label-colour key additionally accepts the sentinel.
BOUNDARY_LABELS = BOUNDARY_BASES + ["inherit"]

NAMED_POOL = [
    "black", "white", "red", "green", "blue", "yellow", "cyan", "magenta",
    "orange", "purple", "brown", "pink", "gray", "olive", "navy", "teal",
    "b", "g", "r", "c", "m", "y", "k", "w",
    "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9",
    "tab:blue", "tab:orange", "tab:green", "tab:red", "xkcd:sky blue",
]


def rand_color(rng):
    kind = rng.randrange(4)
    if kind == 0:
        return "#%06x" % rng.getrandbits(24)
    if kind == 1:
        return "#%08x" % rng.getrandbits(32)
    if kind == 2:
        return rng.choice(NAMED_POOL)
    return "%.3f" % rng.random()


def rand_label(rng):
    if rng.random() < 0.25:
        return "inherit"
    return rand_color(rng)


def main():
    import matplotlib as mpl
    mpl.use("Agg")
    from matplotlib.figure import Figure

    fig = Figure()
    ax = fig.add_subplot()
    xaxis, yaxis = ax.xaxis, ax.yaxis

    checked = 0

    # Boundary: full base x label cross product, applied to both sites (the
    # y site gets the reversed pairing so the two sites see distinct inputs
    # in the same iteration).
    pairs = [(b, l) for b in BOUNDARY_BASES for l in BOUNDARY_LABELS]
    n_boundary = len(pairs)
    for i, (b, l) in enumerate(pairs):
        b2, l2 = pairs[(i + 1) % n_boundary]
        err = check_one(mpl, xaxis, yaxis, b, l, b2, l2)
        if err:
            print(err)
            return 1
        checked += 2

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_one(mpl, xaxis, yaxis,
                        rand_color(rng), rand_label(rng),
                        rand_color(rng), rand_label(rng))
        if err:
            print(err)
            return 1
        checked += 2

    print("G-CONF OK: shadow impl == real patched offset-text colour "
          "selection on %d site-inputs (%d boundary pairs + %d fuzz "
          "iterations, 2 sites each, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "no axiomatized callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
