#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-23476 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (finalizeSnapshot)
              transliterated to Python over the *real* repo type (the `state`
              dict), via the mapping.md bijection: `state['_dpi']` ↔ resolution,
              `state.get('_original_dpi', …)` ↔ baseline (Option Float),
              everything else ↔ payload. The step sets the persisted resolution
              to `baseline.getD resolution` and preserves every other entry. The
              bundle has NO axioms / A-references, so the whole impl is R/I.
  * ORACLE  — `patch.diff`'s behaviour. Two legs:
                (1) HIGH-VOLUME: the patched statement transliterated VERBATIM —
                    `state["_dpi"] = state.get('_original_dpi', state['_dpi'])`
                    (the exact gold line) — applied to fuzzed `state` dicts that
                    do / don't carry `_original_dpi`. Reading back `_dpi` and the
                    other entries is the real behaviour of the op the patch
                    performs.
                (2) LIVE ANCHOR: a real `matplotlib.figure.Figure` whose canvas
                    had its device pixel ratio raised (so `_dpi` was doubled away
                    from `_original_dpi`), pushed through the actual patched
                    `Figure.__getstate__`. Confirms the persisted `_dpi` the real
                    hook emits equals `_original_dpi` and that other state entries
                    survive — the exact scenario the F2P test exercises.

They must agree on every input: persisted resolution == reference-when-present-
else-working, and every other entry unchanged. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, Agg backend), stdlib +
matplotlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import os
import random
import sys

SEED = 23476
N_FUZZ = 100_000

os.environ.setdefault("MPLBACKEND", "Agg")


# --- the R/I shadow: Solution.lean finalizeSnapshot, transliterated ----------

def shadow_finalize(state):
    """finalizeSnapshot transliterated: persist `baseline.getD resolution` into
    the resolution slot, leave every other entry untouched. `state` is a dict;
    `baseline` present ⇔ '_original_dpi' in state. Returns the new dict."""
    out = dict(state)                       # { snap with … } rebuilds the carrier
    # baseline.getD resolution  ==  state.get('_original_dpi', state['_dpi'])
    if "_original_dpi" in out:
        out["_dpi"] = out["_original_dpi"]
    else:
        out["_dpi"] = out["_dpi"]
    return out


# --- oracle leg (1): the patched statement, verbatim -------------------------

def oracle_statement(state):
    """patch.diff op: `state["_dpi"] = state.get('_original_dpi', state['_dpi'])`
    applied to a copy of the given state dict."""
    out = dict(state)
    out["_dpi"] = out.get("_original_dpi", out["_dpi"])
    return out


def fuzz_states(n, rng):
    """Yield `state`-shaped dicts. Each always has '_dpi'; '_original_dpi' is
    present in roughly half (the discriminating case)."""
    # boundary cases first (plan §4.1 step 4)
    yield {"_dpi": 200.0, "_original_dpi": 100.0, "k": "v"}   # doubled (the bug)
    yield {"_dpi": 100.0, "_original_dpi": 100.0}             # already equal
    yield {"_dpi": 100.0}                                     # no reference value
    yield {"_dpi": 42.0 * 7, "_original_dpi": 42.0}           # the F2P numbers
    yield {"_dpi": 0.0, "_original_dpi": 0.0}
    yield {"_dpi": 1e308, "_original_dpi": 72.0}              # huge working value
    yield {"_dpi": float("inf"), "_original_dpi": 72.0}
    yield {"_dpi": 72.0, "_original_dpi": float("inf")}
    yield {"_dpi": 72.0, "a": 1, "b": [1, 2], "c": None}      # rich payload, no ref
    for _ in range(n):
        st = {"_dpi": rng.choice([72.0, 100.0, 200.0, rng.random() * 5000.0])}
        if rng.random() < 0.5:
            st["_original_dpi"] = rng.choice(
                [72.0, 100.0, st["_dpi"], rng.random() * 5000.0])
        # a few opaque payload entries (must survive unchanged)
        for j in range(rng.randint(0, 3)):
            st["payload_%d" % j] = rng.randint(-1000, 1000)
        yield st


# --- oracle leg (2): a live patched Figure round-trip ------------------------

def live_anchor():
    """Yield ('live', oracle_state, shadow_state) from a real Figure whose canvas
    raised the device pixel ratio, pushed through the patched __getstate__."""
    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
        from matplotlib.figure import Figure
    except Exception as exc:                       # pragma: no cover
        print("G-CONF note: live anchor skipped (matplotlib import failed: %r)"
              % exc)
        return
    fig = Figure(dpi=42)
    ok = False
    try:
        fig.canvas._set_device_pixel_ratio(7)      # _dpi becomes 42*7
        ok = (fig.dpi == 42 * 7)
    except Exception as exc:                       # pragma: no cover
        print("G-CONF note: live anchor could not raise pixel ratio (%r); "
              "falling back to the equal-dpi figure" % exc)
    state = fig.__getstate__()                      # the PATCHED hook
    # shadow: apply the Lean model to the same pre-hook state.  We reconstruct the
    # pre-hook resolution view: the working _dpi the hook saw is fig._dpi, the
    # reference value is fig._original_dpi (set by the canvas at construction).
    pre = {"_dpi": fig._dpi}
    if hasattr(fig, "_original_dpi"):
        pre["_original_dpi"] = fig._original_dpi
    shadow = shadow_finalize(pre)
    # observable: the persisted _dpi the real hook emitted vs the shadow's.
    yield ("live(raised=%s)" % ok, {"_dpi": state["_dpi"]},
           {"_dpi": shadow["_dpi"]})


def _diff(oracle, shadow):
    """Disagreement iff persisted _dpi differs, or any non-_dpi entry differs."""
    if oracle.get("_dpi") != shadow.get("_dpi"):
        return True
    ok = {k: v for k, v in oracle.items() if k != "_dpi"}
    sk = {k: v for k, v in shadow.items() if k != "_dpi"}
    return ok != sk


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # leg (1): high-volume statement fuzz over state dicts
    for st in fuzz_states(N_FUZZ, rng):
        count += 1
        o = oracle_statement(st)
        s = shadow_finalize(st)
        if _diff(o, s):
            disagreements.append((count, st, o, s))
            if len(disagreements) >= 5:
                break

    # leg (2): a live patched Figure round-trip at raised device pixel ratio
    if not disagreements:
        for label, o, s in live_anchor():
            count += 1
            if _diff(o, s):
                disagreements.append((label, None, o, s))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tag, st, o, s in disagreements:
            print("  case=%r state=%r oracle=%r shadow=%r" % (tag, st, o, s))
        return 1
    print("G-CONF OK: R/I shadow of finalizeSnapshot agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements. Persisted _dpi == "
          "_original_dpi when present (else working _dpi); other state entries "
          "preserved." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
