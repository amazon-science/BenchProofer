#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-7671 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch). The
              impl computes `out = labelGE have_ (cleanLabel version) inclusive`:
                - `cleanLabel` is the R/I leg — the spelled-out leading-portion
                  parser, transliterated here as `clean_label`.
                - `labelGE` is the A-tagged UNCHANGED ordering callee; per
                  §4.1 it is NOT replaced by its (opaque) axiom model — the
                  shadow runs the REAL callee `LooseVersion(...) >= / > ...`,
                  the same one the oracle reaches.
              Its observable outcome is therefore a Bool verdict OR a raise.
  * ORACLE  — `patch.diff`'s behaviour: the patched `minversion` applied at
              base_commit (the real correctness oracle, G-RESOLVE), driven with
              a synthetic module whose `__version__` is the chosen `have`.

They must agree on every input — including agreeing on WHICH inputs raise. Exit
0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Modeled domain: the required label is ASCII (`meetsRequirement`'s
precondition `∀ c ∈ version, c.toNat < 128`; mapping.md §2.1); the fuzz
alphabets below are ASCII accordingly.

Runs in-container (the prebuilt SWE-Bench instance image after patch.diff is
applied), stdlib + astropy only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
import types
import warnings

warnings.filterwarnings("ignore")
from distutils.version import LooseVersion

SEED = 7671
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean cleanLabel, transliterated ----------------
def is_digit(c):
    return '0' <= c <= '9'


def digit_run(s, i):
    j = i
    while j < len(s) and is_digit(s[j]):
        j += 1
    return j - i


def seg_len(s, i):
    if i >= len(s):
        return 0
    c = s[i]
    if c == '0':
        return 1
    if is_digit(c):
        return 1 + digit_run(s, i + 1)
    return 0


def dotted_tail(s, i):
    total = 0
    while i < len(s) and s[i] == '.':
        sl = seg_len(s, i + 1)
        if sl == 0:
            break
        total += 1 + sl
        i += 1 + sl
    return total


def epoch_len(s):
    if not s:
        return 0
    c = s[0]
    if is_digit(c) and c != '0':
        r = 1 + digit_run(s, 1)
        if r < len(s) and s[r] == '!':
            if seg_len(s, r + 1) == 0:
                return 0
            return r + 1
        return 0
    return 0


def clean_label(version):
    e = epoch_len(version)
    r = seg_len(version, e)
    if r == 0:
        return version
    d = dotted_tail(version, e + r)
    return version[:e + r + d]


def shadow_outcome(have, version, inclusive):
    """The impl: labelGE have_ (cleanLabel version) inclusive. The A-tagged
    callee labelGE is the REAL LooseVersion ordering (run, not axiom-modeled).
    Returns ('ok', bool) or ('raise',)."""
    cleaned = clean_label(version)
    try:
        if inclusive:
            return ('ok', bool(LooseVersion(have) >= LooseVersion(cleaned)))
        return ('ok', bool(LooseVersion(have) > LooseVersion(cleaned)))
    except Exception:
        return ('raise',)


def oracle_outcome(have, version, inclusive):
    """patch.diff behaviour: the patched astropy minversion, driven with a
    synthetic module carrying __version__ = have. Returns ('ok', bool) or
    ('raise',)."""
    from astropy.utils.introspection import minversion
    mod = types.ModuleType("conf_probe_module")
    mod.__version__ = have
    try:
        return ('ok', bool(minversion(mod, version, inclusive)))
    except Exception:
        return ('raise',)


def fuzz_inputs(n, rng):
    # The available (installed) version `have`: clean dotted numbers, the shape
    # a real __version__ takes.
    def clean_have():
        k = rng.randint(1, 4)
        return ".".join(str(rng.randint(0, 30)) for _ in range(k))

    # The required `version`: may carry trailing annotation (the dirty case the
    # patch must tolerate).
    ver_alpha = list("0123456789.!abrcdev-+ ")

    # boundary cases first (plan §4.1 step 4): the F2P matrix and edges.
    boundary_haves = ["0.12.2", "1.14.3", "2.0", "1"]
    boundary_versions = [
        "0.12", "0.12.1", "0.12.0.dev", "0.12dev", "1", "1.2rc1",
        "1.14dev", "1.14.3", "", "0", "1!2.3", "1.2.3rc4.dev5", "0.0",
        "12.3", "a", ".5",
    ]
    for hv in boundary_haves:
        for vv in boundary_versions:
            for inc in (True, False):
                yield (hv, vv, inc)

    for _ in range(n):
        hv = clean_have()
        kv = rng.randint(0, 12)
        vv = "".join(rng.choice(ver_alpha) for _ in range(kv))
        inc = rng.random() < 0.5
        yield (hv, vv, inc)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for hv, vv, inc in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_outcome(hv, vv, inc)
        oracle = oracle_outcome(hv, vv, inc)
        if shadow != oracle:
            disagreements.append((hv, vv, inc, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for hv, vv, inc, sh, orc in disagreements:
            print("  have=%r version=%r inclusive=%s shadow=%r oracle=%r"
                  % (hv, vv, inc, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of meetsRequirement agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
