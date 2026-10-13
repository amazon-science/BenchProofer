#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9461 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `assembleModifierTokens` / `annotationTokens` over the two
              independent boolean modifier flags, then the fixed space-join
              `' '.join(tokens) + ' '` (the unchanged trailing R/I op the modeled
              token list feeds into). The bundle has NO axioms (mapping.md §3),
              so the whole shadow is in scope for G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `sphinx.domains.python.PyProperty.get_signature_prefix`. That
              method reads only `self.options` (a dict whose membership decides
              each modifier flag) and returns the joined prefix string; we feed
              it a DUCK-TYPED stand-in carrying the option set, so the real
              patched code path computes the prefix.

The Lean↔Python bijection (mapping.md §2):
  firstFlag  ↔ ('abstractmethod' in self.options)
  secondFlag ↔ ('classmethod'    in self.options)
  out (List String) ↔ the tokens whose ' '.join(...) + ' ' is the returned str.

Observed projection (exactly what the F2P `test_pyproperty` sees): the returned
prefix string. They must agree on every input. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), stdlib
+ the in-image Sphinx only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 9461
N_FUZZ = 100_000


# --- ORACLE setup: the REAL gold-patched get_signature_prefix ----------------

def _load_real():
    """Bind the gold-patched PyProperty.get_signature_prefix. The harness applies
    patch.diff before this runs (PYTHONPATH=/testbed picks up the patched repo)."""
    from sphinx.domains.python import PyProperty
    return PyProperty.get_signature_prefix


class _FakeProperty:
    """Duck-typed stand-in exposing exactly what get_signature_prefix reads:
    `self.options` membership for the two modifier flags. `get_signature_prefix`
    is an ordinary (unbound) method, so we pass an instance whose only relevant
    attribute is `options`."""
    def __init__(self, options):
        self.options = options


def oracle_prefix(real_method, first_flag, second_flag):
    options = {}
    if first_flag:
        options['abstractmethod'] = None   # directives.flag stores None when present
    if second_flag:
        options['classmethod'] = None
    inst = _FakeProperty(options)
    # `sig` is unused by get_signature_prefix; pass an empty signature string.
    return real_method(inst, "")


# --- SHADOW: Solution.lean's impl, transliterated ----------------------------

def shadow_tokens(first_flag, second_flag):
    """annotationTokens (firstFlag secondFlag) transliterated to a Python list."""
    toks = []
    if first_flag:
        toks = toks + ["abstract"]
    if second_flag:
        toks = toks + ["class"]
    toks = toks + ["property"]
    return toks


def shadow_prefix(first_flag, second_flag):
    """The full R/I shadow: assemble the modeled token list, then the unchanged
    space-join trailing op (mapping.md §2: the join is an R/I identity the modeled
    `out : List String` feeds into)."""
    return ' '.join(shadow_tokens(first_flag, second_flag)) + ' '


def fuzz_inputs(n, rng):
    # all four boundary combinations first (the entire input space is finite:
    # two booleans; the fuzz loop re-samples it to honour the §4.1 ≥10^5 budget
    # and the pinned-seed determinism convention).
    for fa in (False, True):
        for sb in (False, True):
            yield (fa, sb)
    for _ in range(n):
        yield (rng.random() < 0.5, rng.random() < 0.5)


def main():
    try:
        real_method = _load_real()
    except Exception as exc:  # pragma: no cover
        print("G-CONF ERROR: could not import patched get_signature_prefix: %r" % exc)
        return 2

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for fa, sb in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_prefix(fa, sb)
        oracle = oracle_prefix(real_method, fa, sb)
        if shadow != oracle:
            disagreements.append(((fa, sb), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  flags=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of assembleModifierTokens agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
