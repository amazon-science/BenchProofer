#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-20826
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model IS Python, so no transliteration
is needed: `reinit_tick_kw_major` / `reinit_tick_kw_minor` run directly on
plain dicts. The one @ContractOnly callee, `dict_carry_over`, is the modelled
mapping-copy primitive; per the contract it calls the REAL callee it stands
for -- Python's `dict(d)` (mapping.md section 3.1; the same binding
axiom_check.py validates).

ORACLE: the REAL patched repo operation the model models per mapping.md --
the tick-keyword re-initialisation performed by
`matplotlib.axis.Axis.clear` on `self._major_tick_kw` and
`self._minor_tick_kw`. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched package importable. One
`clear()` call exercises BOTH modelled sites (major and minor), so each call
yields two checked site-inputs.

Type bridge (mapping.md section 2):
  * model `Dict[int, bool]` (setting-name token -> on/off) <-> the repo's
    str-keyed tick-keyword dict: a fixed bijection between int tokens and
    distinct setting-name strings, with token 0 (`refreshed_key()`) <->
    'gridOn'. The real result dict is tokenised back and compared to the
    shadow's result in token space (key membership + boolean values -- the
    only observations the model makes).
  * `flag_enabled` <-> `mpl.rcParams['axes.grid']`.
  * `selection_covers` <-> the outcome of the which-selection membership test
    for the site's tick class: rcParams['axes.grid.which'] in
    ('both', 'major') for the major site, in ('both', 'minor') for the minor
    site (the membership test is evaluated outside the modelled site; its
    boolean outcome is the model input).
  * The model returns a fresh mapping while the repo mutates the same dict in
    place; the consumer reads by content, so the comparison is on the
    resulting content (the pre-call content is snapshotted as the input).

Input domain: Requires demands only dict permission on a Dict[int, bool], so
any boolean-valued token dict is Requires-satisfying. Boundary cases mirror
axiom_check.py (empty, designated-key-only both ways, the side-hiding
visibility flags a caller stores for linked shared axes, mixtures), each
crossed with all reachable ambient combinations; fuzz draws random token
dicts over a 12-token space plus random ambient flags.

>= 1e5 Requires-satisfying site-inputs: 2 * (boundary + 55000 fuzz clears).
Pinned fuzz seed: 20826.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 20826
N_FUZZ = 55_000


# --- the @ContractOnly callee: per the contract it IS the real mapping-copy
# --- primitive (a fresh dict with the same key/value content) -----------------

def dict_carry_over(d):
    return dict(d)


# --- pure helper from model.py, contracts stripped -----------------------------

def refreshed_key():
    # The setting-name token for the one designated entry that is refreshed.
    return 0


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def reinit_tick_kw_major(tick_kw, flag_enabled, selection_covers):
    result = dict_carry_over(tick_kw)  # type: dict
    result[refreshed_key()] = flag_enabled and selection_covers
    return result


def reinit_tick_kw_minor(tick_kw, flag_enabled, selection_covers):
    result = dict_carry_over(tick_kw)  # type: dict
    result[refreshed_key()] = flag_enabled and selection_covers
    return result


# --- bridge: token <-> setting-name bijection -----------------------------------

# Token 0 is the designated refreshed entry; the others are distinct
# setting-name strings (real per-side visibility flags plus further distinct
# names -- the mapping is generic in its keys).
TOKEN_TO_NAME = {
    0: "gridOn",
    1: "tick1On",
    2: "tick2On",
    3: "label1On",
    4: "label2On",
    5: "labelsize_flag",
    6: "labelcolor_flag",
    7: "pad_flag",
    8: "zorder_flag",
    9: "direction_flag",
    10: "width_flag",
    11: "length_flag",
}
NAME_TO_TOKEN = {v: k for k, v in TOKEN_TO_NAME.items()}


def to_names(token_dict):
    return {TOKEN_TO_NAME[k]: v for k, v in token_dict.items()}


def to_tokens(name_dict):
    out = {}
    for k, v in name_dict.items():
        if k not in NAME_TO_TOKEN:
            return None  # a key outside the bijection: reported as spurious
        out[NAME_TO_TOKEN[k]] = v
    return out


def check_one(axis, mpl, major_in, minor_in, flag_enabled, which):
    """Drive ONE real re-initialisation and diff both sites against the
    shadow. Returns an error string on disagreement, else None."""
    mpl.rcParams["axes.grid"] = flag_enabled
    mpl.rcParams["axes.grid.which"] = which
    covers_major = which in ("both", "major")
    covers_minor = which in ("both", "minor")

    # Install the pre-call mapping contents (the model inputs).
    axis._major_tick_kw.clear()
    axis._major_tick_kw.update(to_names(major_in))
    axis._minor_tick_kw.clear()
    axis._minor_tick_kw.update(to_names(minor_in))

    axis.clear()  # the REAL patched operation under test

    for site, tick_in, covers, real_dict in (
            ("major", major_in, covers_major, axis._major_tick_kw),
            ("minor", minor_in, covers_minor, axis._minor_tick_kw)):
        shadow_fn = reinit_tick_kw_major if site == "major" else reinit_tick_kw_minor
        shadow = shadow_fn(dict(tick_in), flag_enabled, covers)
        real_tokens = to_tokens(dict(real_dict))
        # Compare in token space; normalise value truthiness to bool (the
        # model observes on/off values).
        norm = lambda d: {k: bool(v) for k, v in d.items()}
        if real_tokens is None or norm(shadow) != norm(real_tokens):
            return ("DISAGREEMENT site=%s\n  input=%r\n  flag_enabled=%r which=%r"
                    " (covers=%r)\n  shadow=%r\n  real=%r"
                    % (site, tick_in, flag_enabled, which, covers,
                       shadow, dict(real_dict)))
    return None


def boundary_dicts():
    return [
        {},
        {0: True},
        {0: False},
        {3: False},                          # a hidden label flag alone
        {1: False, 3: False},                # side-hiding pair a caller stores
        {0: True, 1: False, 3: False},
        {0: False, 1: True, 2: False, 3: True},
        {1: True, 2: True, 3: True, 4: True},
        {k: bool(k % 2) for k in range(12)},  # full token space
    ]


def main():
    import matplotlib as mpl
    mpl.use("Agg")
    from matplotlib.figure import Figure

    fig = Figure()
    ax = fig.add_subplot()
    axis = ax.xaxis

    checked = 0
    boundary = boundary_dicts()
    ambient = [(f, w) for f in (False, True) for w in ("both", "major", "minor")]

    # Boundary: every (major, minor) pairing drawn from the boundary dicts
    # (paired diagonally and crosswise) under every ambient combination.
    for i, dmaj in enumerate(boundary):
        for dmin in (boundary[i], boundary[(i + 1) % len(boundary)]):
            for f, w in ambient:
                err = check_one(axis, mpl, dmaj, dmin, f, w)
                if err:
                    print(err)
                    return 1
                checked += 2

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        def rand_dict():
            n = rng.randint(0, 8)
            keys = rng.sample(range(0, 12), n)
            return {k: bool(rng.getrandbits(1)) for k in keys}
        f = bool(rng.getrandbits(1))
        w = rng.choice(("both", "major", "minor"))
        err = check_one(axis, mpl, rand_dict(), rand_dict(), f, w)
        if err:
            print(err)
            return 1
        checked += 2

    print("G-CONF OK: shadow impl == real patched re-initialisation on %d "
          "site-inputs (%d boundary clears + %d fuzz clears, seed %d)."
          % (checked, len(boundary) * 2 * 6, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee = real dict copy)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
