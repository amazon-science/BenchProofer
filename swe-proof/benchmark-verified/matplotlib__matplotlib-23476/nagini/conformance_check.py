#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-23476 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/MustTerminate) stripped, together with the two @Pure
entry-name helpers it calls. No @ContractOnly callee exists (mapping.md
section 3: the axioms region is empty).

ORACLE: the REAL patched repo function the model maps to per mapping.md
section 1 -- the reconciliation step inside
``matplotlib.figure.Figure.__getstate__``. The gate applies patch.diff to
/testbed and sets PYTHONPATH=/testbed before this script runs, so the import
resolves to the patched module. A single real ``Figure`` (with a
``FigureCanvasBase`` attached, so ``__getstate__``'s canvas handling works)
is reused across cases; each case writes the relevant ``__dict__`` entries
directly, calls ``__getstate__``, and reads the produced state.

Type bridge (mapping.md section 2): the model state is ``Dict[int, int]``;
``key_dpi() = 0`` maps to the ``"_dpi"`` entry, ``key_reference() = 1``
maps to the ``"_original_dpi"`` entry, and every other integer key token k
maps to a fresh attribute name ``_conf_tok_<k>`` (an arbitrary untouched
state entry). Value tokens are ints; they lower to the equivalent ``float``
(the repo carrier), kept within exact float-int range so the bijection is
lossless. The modeled step only selects among stored values, so numeric
equality is the faithful comparison.

Only the entries the model observes are compared: the dpi entry's value,
the reference entry's membership and value, and every other injected token
entry's membership and value. Entries that OTHER statements of
``__getstate__`` legitimately create or rewrite (version tag, renderer cache,
canvas handling) are outside the modeled step and excluded from the frame
comparison, exactly as mapping.md section 1 scopes the binding to the added
hunk.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz states.
Pinned fuzz seed: 23476 (the instance number; recorded in mapping.md).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import sys
import tempfile

# Keep matplotlib's config/cache out of any unwritable HOME in-container.
os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp(prefix="mplconf_"))
os.environ.setdefault("MPLBACKEND", "agg")

SEED = 23476
N_FUZZ = 100000

# Attribute-name bridge for token keys other than 0/1.
TOK_PREFIX = "_conf_tok_"


# --- pure region of model.py, contracts stripped ------------------------------

def key_dpi():
    # The entry name of the dpi entry of the mapping.
    return 0


def key_reference():
    # The entry name of the reference-dpi entry, when present. Distinct
    # from the dpi entry name.
    return 1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def normalize_state_dpi(state, reference_present, reference_value):
    if key_reference() in state:
        state[key_dpi()] = state[key_reference()]
    else:
        state[key_dpi()] = state[key_dpi()]


# --- oracle: the real patched repo function -----------------------------------

class Oracle(object):
    """Drives the patched ``Figure.__getstate__`` on a controlled state.

    One Figure is built once; per case the ``__dict__`` entries the model
    observes are written directly (the modeled step is pure mapping logic on
    the state, so this exercises exactly the bound behavior), then
    ``__getstate__`` produces the serialisable state that is read back.
    """

    def __init__(self):
        from matplotlib.figure import Figure
        from matplotlib.backend_bases import FigureCanvasBase
        self.fig = Figure()
        # Attach a canvas so __getstate__'s canvas handling has its normal
        # shape; FigureCanvasBase also records _original_dpi, which each case
        # below overwrites or removes as its input demands.
        FigureCanvasBase(self.fig)

    def run(self, dpi_value, ref_value_or_none, extras):
        """extras: dict of attribute-name -> value. Returns the state dict
        produced by the real patched __getstate__."""
        d = self.fig.__dict__
        d["_dpi"] = dpi_value
        if ref_value_or_none is None:
            d.pop("_original_dpi", None)
        else:
            d["_original_dpi"] = ref_value_or_none
        for name, v in extras.items():
            d[name] = v
        try:
            state = self.fig.__getstate__()
        finally:
            for name in extras:
                d.pop(name, None)
        return state


# --- differential driver -------------------------------------------------------

def lower_value(tok):
    """Value-token bridge: int token -> the float the repo carries."""
    return float(tok)


def check(oracle, dpi_tok, orig_tok, extra_toks):
    """One Requires-satisfying input.

    dpi_tok: int value token of the dpi entry (always present).
    orig_tok: int value token of the reference entry, or None when absent.
    extra_toks: dict {int key token >= 2: int value token} of other entries.
    Returns an error string on disagreement, else None.
    """
    # shadow side: the token state
    state = {key_dpi(): dpi_tok}
    if orig_tok is not None:
        state[key_reference()] = orig_tok
    for k, v in extra_toks.items():
        state[k] = v
    reference_present = key_reference() in state
    reference_value = state[key_reference()] if reference_present else 0
    snapshot = dict(state)
    normalize_state_dpi(state, reference_present, reference_value)

    # internal frame check of the shadow against its own pre-state (mirrors
    # the postconditions; cheap, and catches a mangled shadow copy)
    if set(state) != set(snapshot):
        return ("INTERNAL: shadow changed the key set on input %r -> %r"
                % (snapshot, state))
    for k in snapshot:
        if k != key_dpi() and state[k] != snapshot[k]:
            return ("INTERNAL: shadow changed entry %r on input %r -> %r"
                    % (k, snapshot, state))

    # oracle side: the real patched __getstate__
    real_state = oracle.run(
        lower_value(dpi_tok),
        None if orig_tok is None else lower_value(orig_tok),
        {TOK_PREFIX + str(k): lower_value(v) for k, v in extra_toks.items()})

    def fail(what, shadow_val, real_val):
        return ("DISAGREEMENT on input (dpi_tok=%r, orig_tok=%r, extras=%r): "
                "%s\n  shadow (impl region)              = %r\n"
                "  real (patched Figure.__getstate__) = %r"
                % (dpi_tok, orig_tok, extra_toks, what, shadow_val, real_val))

    # dpi entry: present, and value per the selection
    if "_dpi" not in real_state:
        return fail("dpi entry missing from real state",
                    state.get(key_dpi()), None)
    if lower_value(state[key_dpi()]) != real_state["_dpi"]:
        return fail("dpi entry value", lower_value(state[key_dpi()]),
                    real_state["_dpi"])

    # reference entry: membership and value preserved
    shadow_has_orig = key_reference() in state
    real_has_orig = "_original_dpi" in real_state
    if shadow_has_orig != real_has_orig:
        return fail("reference entry membership", shadow_has_orig,
                    real_has_orig)
    if shadow_has_orig and \
            lower_value(state[key_reference()]) != real_state["_original_dpi"]:
        return fail("reference entry value",
                    lower_value(state[key_reference()]),
                    real_state["_original_dpi"])

    # every other injected entry: membership and value preserved
    for k, v in extra_toks.items():
        name = TOK_PREFIX + str(k)
        if k not in state or name not in real_state:
            return fail("entry %r membership" % k, k in state,
                        name in real_state)
        if lower_value(state[k]) != real_state[name]:
            return fail("entry %r value" % k, lower_value(state[k]),
                        real_state[name])
    return None


def boundary_cases():
    """(dpi_tok, orig_tok_or_None, extras) triples."""
    cases = [
        # reference absent: the dpi entry keeps its recorded value
        (100, None, {}),
        (0, None, {}),
        (1, None, {}),
        (42, None, {2: 7}),
        (2 ** 31, None, {}),
        # reference present and equal to the dpi value
        (100, 100, {}),
        (0, 0, {}),
        # reference present and different (scaled-vs-reference shapes)
        (294, 42, {}),          # 42 * 7
        (400, 200, {}),         # 200 * 2
        (200 * 2 ** 20, 200, {}),
        (84, 42, {2: 1, 3: 2}),
        (1, 0, {}),
        (0, 1, {}),
        # large exact-float tokens
        (2 ** 49, 2 ** 48, {}),
        (2 ** 48, None, {5: 2 ** 40}),
        # negatives (the selection is value-agnostic)
        (-100, -50, {}),
        (-1, None, {}),
        # many untouched entries
        (144, 72, {k: k * 11 for k in range(2, 40)}),
        (144, None, {k: -k for k in range(2, 40)}),
        # entry whose value token equals another entry's
        (72, 72, {2: 72, 3: 72}),
    ]
    return cases


def main():
    oracle = Oracle()

    checked = 0
    boundary = boundary_cases()
    for dpi_tok, orig_tok, extras in boundary:
        err = check(oracle, dpi_tok, orig_tok, extras)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz over the Requires domain (pinned seed): the dpi entry
    # always present; reference entry present in ~2/3 of the states; 0-5 other
    # entries with distinct key tokens; value tokens span small, boundary-ish
    # and large exact-float ints, negatives included
    rng = random.Random(SEED)

    def value_tok():
        r = rng.random()
        if r < 0.4:
            return rng.randint(0, 500)
        if r < 0.7:
            return rng.choice([0, 1, 42, 72, 100, 144, 200, 294, 400,
                               2 ** 31, 2 ** 40, 2 ** 49])
        if r < 0.85:
            return rng.randint(-(2 ** 20), 2 ** 20)
        return rng.randint(0, 2 ** 49)

    for _ in range(N_FUZZ):
        dpi_tok = value_tok()
        orig_tok = value_tok() if rng.random() < (2.0 / 3.0) else None
        n_extra = rng.randint(0, 5)
        keys = rng.sample(range(2, 100), n_extra)
        extras = {k: value_tok() for k in keys}
        err = check(oracle, dpi_tok, orig_tok, extras)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched Figure.__getstate__ "
          "reconciliation on %d inputs (%d boundary + %d fuzz, seed %d); "
          "0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
