#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15503 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's `compileRhsPath` impl region
             transliterated to Python over the *real* repo types (`str`,
             `list[str]`), via the mapping.md bijection (`List Char` ↔ `str`,
             `List (List Char)` ↔ `list[str]`). The deep models `compilePrefix`
             and `memberSeg` are transliterated here (their I legs); their
             equality to the real callees is the A-reference leg validated
             separately by G-AX.
  * ORACLE — `patch.diff`'s behaviour: the patched right-hand-side path
             construction for the base `HasKeyLookup` (the class the has_key /
             has_keys / has_any_keys lookups inherit, exercised by the F2P
             tests). Reconstructed from the REAL patched repo callees
             `compile_json_path` and `HasKeyLookup.compile_json_path_final_key`
             (the harness applies patch.diff before this runs).

They must agree on every Requires-satisfying input (non-empty key list, every
key a "simple" ASCII-alphanumeric run — mapping.md §2). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + in-tree django only. The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import json
import random
import sys

SEED = 15503
N_FUZZ = 100_000

_LETTERS = [chr(c) for c in range(ord("a"), ord("z") + 1)]
_LETTERS += [chr(c) for c in range(ord("A"), ord("Z") + 1)]
_DIGITS = [chr(c) for c in range(ord("0"), ord("9") + 1)]
_SIMPLE_ALPHABET = _LETTERS + _DIGITS


# --- the R/I shadow: Solution.lean compileRhsPath, transliterated ------------
def _is_numeric_key(k):
    return len(k) > 0 and all(ch in _DIGITS for ch in k)


def _canonical_digits(k):
    i = 0
    while i < len(k) and k[i] == "0":
        i += 1
    r = k[i:]
    return r if r else "0"


def _key_seg(k):
    if _is_numeric_key(k):
        return "[" + _canonical_digits(k) + "]"
    return '."' + k + '"'


def _compile_prefix(keys):
    return "".join(_key_seg(k) for k in keys)


def _member_seg(k):
    return '."' + k + '"'


def shadow_rhs_path(lhs_path, keys):
    """compileRhsPath (lhsPath) (keys) transliterated to str:
       lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!"""
    prefix_keys = keys[:-1]
    final_key = keys[-1]
    return lhs_path + _compile_prefix(prefix_keys) + _member_seg(final_key)


# --- the oracle: patch.diff's behaviour via the REAL patched callees ---------
def oracle_rhs_path(lhs_path, keys):
    """The patched right-hand-side path the base HasKeyLookup builds:
        *rhs, final = keys
        rhs_json_path  = compile_json_path(rhs, include_root=False)
        rhs_json_path += self.compile_json_path_final_key(final)
        result = lhs_json_path + rhs_json_path
    using the REAL patched repo callees (base HasKeyLookup variant)."""
    from django.db.models.fields.json import compile_json_path, HasKeyLookup
    rhs_key_transforms = keys[:-1]
    final_key = keys[-1]
    rhs_json_path = compile_json_path(rhs_key_transforms, include_root=False)
    # base HasKeyLookup.compile_json_path_final_key ignores self; the patch body
    # is `return ".%s" % json.dumps(key_transform)`. Call the REAL method.
    rhs_json_path += HasKeyLookup.compile_json_path_final_key(None, final_key)
    return lhs_path + rhs_json_path


def _random_simple_key(rng):
    n = rng.randint(1, 8)
    return "".join(rng.choice(_SIMPLE_ALPHABET) for _ in range(n))


def _random_lhs_path(rng):
    # lhsPath is an opaque already-compiled prefix; both legs prepend it
    # identically. Use realistic compiled-path shapes plus the root sentinel.
    choices = ["$", '$."a"', '$."nested"', '$."array"[0]', "", '$."x"[3]."y"']
    return rng.choice(choices)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4) — the F2P shapes
    yield ("$", ["123"])
    yield ("$", ["foo"])
    yield ("$", ["nested", "456"])
    yield ("$", ["array", "0", "789"])
    yield ("$", ["000"])
    yield ("$", ["007"])
    yield ("$", ["0"])
    yield ("$", ["nested", "999"])
    yield ("$", ["array", "0", "777"])
    yield ("", ["abc"])
    yield ('$."a"[5]', ["1a"])
    yield ("$", ["1000000000000000000000"])
    yield ("$", ["a", "1", "b", "00", "c"])
    for _ in range(n):
        m = rng.randint(0, 4)
        keys = [_random_simple_key(rng) for _ in range(m)] + [_random_simple_key(rng)]
        yield (_random_lhs_path(rng), keys)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for lhs_path, keys in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_rhs_path(lhs_path, keys)
        oracle = oracle_rhs_path(lhs_path, keys)
        if shadow != oracle:
            disagreements.append((lhs_path, keys, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for lhs, ks, sh, orc in disagreements:
            print("  lhs=%r keys=%r shadow=%r oracle=%r" % (lhs, ks, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of compileRhsPath agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
