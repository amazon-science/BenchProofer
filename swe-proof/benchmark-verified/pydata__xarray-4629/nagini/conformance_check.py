#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4629 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Invariant lines) stripped. There are no @Pure helpers and no
@ContractOnly callees in this bundle; the module-level mode tokens DROP /
OVERRIDE copy over as plain constants.

ORACLE: the REAL patched repo function the model models per mapping.md —
`xarray.core.merge.merge_attrs` (the per-source attribute-mapping combiner).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  * an attribute mapping (a dict) <-> its value-content List[int]: the shadow
    input for a mapping d is list(d.values()) with int value tokens, so two
    mappings are model-equal iff content-equal for the generated key sets
    (each generated first-mapping uses a fixed deterministic key order, so
    values() is a faithful content sequence);
  * the collection variable_attrs (list of mappings) <-> List[List[int]];
  * the str mode ("drop" / "override") <-> the int token (DROP=0, OVERRIDE=1);
  * OBJECT IDENTITY of the returned mapping vs variable_attrs[0] <-> Python
    `is` on the shadow's returned list vs its leading input list. This is the
    decisive observable: both sides must report an independent result whose
    mutation leaves the leading source untouched.

Observables diffed per input, both modes:
  1. content: list(oracle_result.values()) == shadow_result;
  2. identity: (oracle_result is variable_attrs[0]) ==
     (shadow_result is shadow_input[0]);
  3. frame: after mutating each side's result, each side's leading source is
     content-unchanged (and the two "source unchanged" booleans agree).

Input domain: the Requires demand len(variable_attrs) >= 1 and mode in
{DROP, OVERRIDE}; every generated input satisfies them (a non-empty
collection, both modes exercised on each draw).

>= 1e5 Requires-satisfying inputs: boundary cases (empty leading mapping,
singleton, the issue-report shapes, multi-entry, duplicate values, varying
trailing sources) + 60000 fuzz draws x 2 modes. Pinned fuzz seed: 4629.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo module only.
"""
import random
import sys

from xarray.core.merge import merge_attrs

SEED = 4629
N_FUZZ = 60_000

# --- model.py module-level mode tokens, verbatim ------------------------------

DROP = 0
OVERRIDE = 1

# the real function's corresponding str modes (bridge for the int tokens)
MODE_STR = {DROP: "drop", OVERRIDE: "override"}


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def combine_attrs(variable_attrs, mode):
    if mode == DROP:
        empty = []  # type: ignore
        return empty
    src = variable_attrs[0]
    result = []
    i = 0
    while i < len(src):
        result.append(src[i])
        i = i + 1
    return result


# --- bridge + differential check ----------------------------------------------

def as_token_list(mapping):
    """A mapping's value-content sequence (mapping.md section 2): the list of
    its per-entry int value tokens in the mapping's own iteration order."""
    return list(mapping.values())


def check_one(dict_attrs, mode):
    """Run oracle and shadow on one input; return an error string on
    disagreement, else None. dict_attrs: non-empty list of dicts with int
    values; mode: DROP or OVERRIDE."""
    # Independent snapshots for the frame observation.
    snapshots = [dict(d) for d in dict_attrs]

    # Shadow side: value-content lists (fresh lists each call).
    shadow_input = [as_token_list(d) for d in dict_attrs]
    shadow_out = combine_attrs(shadow_input, mode)

    # Oracle side: the real patched combiner.
    oracle_out = merge_attrs(dict_attrs, MODE_STR[mode])

    label = "attrs=%r mode=%s" % (dict_attrs, MODE_STR[mode])

    # 1. content agreement under the value-token bridge.
    if oracle_out is None or as_token_list(oracle_out) != shadow_out:
        return ("content disagreement: %s :: shadow=%r oracle=%r"
                % (label, shadow_out, oracle_out))

    # 2. identity agreement: does each side hand back its own leading source?
    oracle_aliases = oracle_out is dict_attrs[0]
    shadow_aliases = shadow_out is shadow_input[0]
    if oracle_aliases != shadow_aliases:
        return ("identity disagreement: %s :: shadow aliases leading "
                "source=%r, oracle aliases leading source=%r"
                % (label, shadow_aliases, oracle_aliases))

    # 3. frame agreement: mutate each result; every source must be unchanged
    #    on both sides (the behaviour the spec pins down).
    oracle_out["__probe_key__"] = -1
    shadow_out.append(-1)
    oracle_sources_intact = all(d == s for d, s in zip(dict_attrs, snapshots))
    shadow_sources_intact = all(
        lst == as_token_list(s) for lst, s in zip(shadow_input, snapshots))
    if oracle_sources_intact != shadow_sources_intact:
        return ("frame disagreement: %s :: mutating the result left sources "
                "intact shadow=%r oracle=%r (oracle leading source now %r)"
                % (label, shadow_sources_intact, oracle_sources_intact,
                   dict_attrs[0]))
    if not oracle_sources_intact:
        return ("frame violation on BOTH sides: %s :: leading source now %r "
                "(was %r)" % (label, dict_attrs[0], snapshots[0]))
    return None


def _rand_map(rng, max_keys=6):
    """A mapping with int keys and int value tokens; deterministic key order
    (insertion order = ascending fresh keys) so values() is a faithful
    content sequence."""
    n = rng.randint(0, max_keys)
    return {k: rng.randrange(-50, 50) for k in range(n)}


def main():
    n = 0

    # --- boundary cases --------------------------------------------------
    boundary = [
        [{}],                                        # single empty source
        [{0: 0}],                                    # singleton
        [{0: 0}, {0: 1}],                            # two sources, same key
        [{0: 0, 1: 1}, {2: 7}],                      # multi-entry leading
        [{0: 5, 1: 5, 2: 5}],                        # duplicate value tokens
        [{}, {0: 1}, {1: 2}],                        # empty leading, more
        [{k: k for k in range(6)}, {}, {9: 9}],      # wide leading
    ]
    for attrs in boundary:
        for mode in (DROP, OVERRIDE):
            err = check_one([dict(d) for d in attrs], mode)
            if err:
                print(err)
                return 1
            n += 1

    # --- randomized fuzz (pinned seed) ------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        attrs = [_rand_map(rng)
                 for _ in range(rng.randint(1, 4))]
        for mode in (DROP, OVERRIDE):
            err = check_one([dict(d) for d in attrs], mode)
            if err:
                print(err)
                return 1
            n += 1

    print("G-CONF OK: shadow (impl region of combine_attrs) agrees with the "
          "real patched attribute-mapping combiner on %d Requires-satisfying "
          "inputs (%d boundary + %d fuzz draws x 2 modes, seed %d): content, "
          "result-vs-leading-source identity, and source-intact-after-"
          "mutation all match on every input."
          % (n, len(boundary) * 2, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
