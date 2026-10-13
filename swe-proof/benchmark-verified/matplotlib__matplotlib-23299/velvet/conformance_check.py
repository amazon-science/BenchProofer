#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-23299 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's `restoreSnapshot` impl region, transliterated to
              Python over the real repo type (a `dict[str, str]` rcParams-like
              mapping, mapping.md §2). The impl is two ops:
                restore_src = eraseKey(saved, "backend")   # I op (concrete)
                params      = updateDict(params, restore_src)
              `updateDict` is an A-reference (refinement.md), so it is left as
              the REAL builtin overlay `dict.update`; only the I op `eraseKey`
              is transliterated (drop the "backend" binding).
  * ORACLE  — patch.diff's behaviour: the patched `rc_context` finally block at
              base_commit, transliterated VERBATIM from the gold hunk:
                orig = dict(saved.copy())
                del orig['backend']            # the patch's added line
                dict.update(params, orig)      # Revert to the original rcs.
              i.e. revert every key to its entry-snapshot value EXCEPT
              'backend', which keeps the value it holds in `params`.

They must agree on the full resulting mapping for every Requires-satisfying
input. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench image), stdlib only. The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 23299
N_FUZZ = 100_000

# rcParams always contains a 'backend' key; values are short tokens. The other
# keys/values are arbitrary str -> str bindings the context body may rewrite.
KEYS = ["backend", "interactive", "figure.dpi", "lines.linewidth",
        "axes.grid", "font.size", "savefig.format", "toolbar"]
VALS = ["module://aardvark", "Agg", "QtAgg", "TkAgg", "0", "1", "100", "true",
        "false", "png", "pdf", "", "x", "Y", "module://m.n"]


# --- the R/I shadow: Solution.lean restoreSnapshot, A-ref left as builtin -----

def eraseKey(d, name):
    """eraseKey (I op): drop every binding for `name` (dicts have unique keys,
    so this removes exactly the one binding)."""
    return {k: v for k, v in d.items() if k != name}


def shadow_restore(params, saved):
    """restoreSnapshot impl transliterated. `updateDict` (A-reference) is left
    as the REAL builtin `dict.update`; `eraseKey` (I) is the concrete drop."""
    restore_src = eraseKey(saved, "backend")     # I op
    result = dict(params)
    dict.update(result, restore_src)              # updateDict == real dict.update
    return result


# --- the oracle: patch.diff's patched rc_context finally block ----------------

def oracle_restore(params, saved):
    """The patched finally block (gold patch.diff), verbatim semantics:
        orig = dict(rcParams.copy()); del orig['backend']
        dict.update(rcParams, orig)
    Here `saved` is the entry snapshot (== orig before the del) and `params`
    is the live mapping at restore time."""
    orig = dict(saved)            # dict(rcParams.copy()) taken at entry
    del orig['backend']           # <-- the patch's added line
    result = dict(params)
    dict.update(result, orig)     # Revert to the original rcs (minus backend)
    return result


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the F2P scenario and edges.
    # F2P: entry backend 'X', body sets backend 'module://aardvark', restore
    # must keep 'module://aardvark'.
    yield ({"backend": "module://aardvark", "font.size": "10"},
           {"backend": "Agg", "font.size": "12"})
    # backend unchanged across the context
    yield ({"backend": "Agg"}, {"backend": "Agg"})
    # only backend present
    yield ({"backend": "TkAgg"}, {"backend": "QtAgg"})
    # body added a new key not in snapshot (kept), and changed others (reverted)
    yield ({"backend": "Z", "new.key": "kept", "font.size": "99"},
           {"backend": "Agg", "font.size": "12"})
    # empty value strings
    yield ({"backend": "", "x": ""}, {"backend": "Agg", "x": "y"})
    for _ in range(n):
        # build a snapshot (always has 'backend') and a current mapping that is
        # the snapshot with some values rewritten / keys added / dropped.
        keys = ["backend"] + rng.sample(KEYS[1:], rng.randint(0, len(KEYS) - 1))
        saved = {k: rng.choice(VALS) for k in keys}
        params = dict(saved)
        # rewrite a random subset of values (incl. possibly 'backend')
        for k in list(params.keys()):
            if rng.random() < 0.5:
                params[k] = rng.choice(VALS)
        # maybe add a body-only key (not in snapshot)
        if rng.random() < 0.3:
            params["body.only." + str(rng.randint(0, 9))] = rng.choice(VALS)
        # 'backend' must remain present in params (rcParams never drops it)
        params.setdefault("backend", rng.choice(VALS))
        yield (params, saved)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for params, saved in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_restore(params, saved)
        oracle = oracle_restore(params, saved)
        if shadow != oracle:
            disagreements.append((params, saved, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for p, s, sh, orc in disagreements:
            print("  params=%r saved=%r shadow=%r oracle=%r" % (p, s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of restoreSnapshot agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
