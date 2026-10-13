#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7757 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the *real* repo types, via the mapping.md bijection.
              The modeled behaviour is the per-position default vector
                  distributed(n, defaults) = [empty]*(n-d) ++ defaults
              i.e. the supplied defaults RIGHT-ALIGNED across all
              n = p + q = len(posonlyargs) + len(args) positional parameters.
              There are NO A-tagged callees in the impl region (mapping.md §3),
              so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sphinx.util.inspect.signature_from_str` applied at base_commit
              (the real correctness oracle, G-RESOLVE). We read off, for each
              positional parameter in declaration order, its `Parameter.default`
              (`Parameter.empty` where absent) and compare to the shadow.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 7757
N_FUZZ = 100_000


def shadow_distribution(posonly, ordinary, defaults):
    """distributed(p+q, defaults) transliterated to Python: the supplied
    `defaults` right-aligned across all p+q positional parameters.  Returns a
    list of length p+q whose entries are either the sentinel EMPTY or a default
    payload (here the rendered default string)."""
    n = len(posonly) + len(ordinary)
    d = len(defaults)
    assert d <= n, "Requires violated: more defaults than positional params"
    return [EMPTY] * (n - d) + list(defaults)


# sentinel for "no default" on the shadow side (compared against Parameter.empty)
class _Empty:
    def __repr__(self):
        return "<empty>"


EMPTY = _Empty()


def oracle_distribution(signature_str):
    """patch.diff's behaviour: per-position Parameter.default vector over the
    positional parameters, in declaration order."""
    from sphinx.util.inspect import signature_from_str
    import inspect as _inspect
    empty = _inspect.Parameter.empty
    sig = signature_from_str(signature_str)
    out = []
    for name, param in sig.parameters.items():
        if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
            out.append(EMPTY if param.default is empty else param.default)
    return out


def build_signature(posonly, ordinary, defaults):
    """Construct a Python signature source string with `posonly` positional-only
    names and `ordinary` positional-or-keyword names, with the supplied
    `defaults` (rendered source strings) right-aligned across them — i.e. the
    last len(defaults) parameters carry `=<value>`.  Returns the signature str
    plus the shadow's expected vector built from the SAME inputs."""
    names = posonly + ordinary
    n = len(names)
    d = len(defaults)
    # which positions get a default (right-aligned)
    pos_default = {}
    for j in range(n - d, n):
        pos_default[j] = defaults[j - (n - d)]
    # render parameter list with the '/' separator after the posonly group
    parts = []
    for j, nm in enumerate(names):
        if j in pos_default:
            parts.append("%s=%s" % (nm, pos_default[j]))
        else:
            parts.append(nm)
    if posonly:
        parts.insert(len(posonly), "/")
    sig_str = "(" + ", ".join(parts) + ")"
    shadow = shadow_distribution(posonly, ordinary, defaults)
    return sig_str, shadow


def eq(a, b):
    """observable equality: EMPTY==EMPTY, else compare rendered default strings."""
    if a is EMPTY or b is EMPTY:
        return a is EMPTY and b is EMPTY
    return str(a) == str(b)


def fuzz_cases(n, rng):
    # boundary cases first (plan §4.1 step 4)
    fixed = [
        ([], ["a"]),                         # one ordinary, no default
        (["a"], ["b"]),                      # the original (a, /, b), no defaults
        (["a", "b"], ["c"]),                 # the F2P shape (a, b, /, c)
        (["a"], []),                         # (a, /)
        (["a", "b"], []),                    # (a, b, /)
        ([], []),                            # ()
        (["x", "y"], ["z", "w"]),
    ]
    default_pool = ["0", "1", "2", "None", "'s'", "[]", "3.5", "True"]
    for posonly, ordinary in fixed:
        n_pos = len(posonly) + len(ordinary)
        for d in range(0, n_pos + 1):
            yield posonly, ordinary, default_pool[:d]
    for _ in range(n):
        p = rng.randint(0, 4)
        q = rng.randint(0, 4)
        n_pos = p + q
        posonly = ["p%d" % i for i in range(p)]
        ordinary = ["a%d" % i for i in range(q)]
        d = rng.randint(0, n_pos)
        defaults = [rng.choice(default_pool) for _ in range(d)]
        yield posonly, ordinary, defaults


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for posonly, ordinary, defaults in fuzz_cases(N_FUZZ, rng):
        sig_str, shadow = build_signature(posonly, ordinary, defaults)
        count += 1
        try:
            oracle = oracle_distribution(sig_str)
        except Exception as exc:  # pragma: no cover
            disagreements.append((sig_str, shadow, "EXC:%r" % exc))
            if len(disagreements) >= 5:
                break
            continue
        if len(shadow) != len(oracle) or not all(eq(a, b) for a, b in zip(shadow, oracle)):
            disagreements.append((sig_str, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sig_str, sh, orc in disagreements:
            print("  sig=%r shadow=%r oracle=%r" % (sig_str, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of distributePositionalDefaults agrees with "
          "patch.diff behaviour on %d signatures (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
