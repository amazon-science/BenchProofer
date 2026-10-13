#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10097 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's impl region transliterated
             to Python over the *real* repo type (``str``), via the mapping.md
             bijection (``List Char`` ↔ ``str``, ``Char.toNat`` ↔ ``ord``).
             This is the backward per-code-point fold of ``validateAuthsegment``
             computing ``good`` / ``ncolon`` and returning
             ``good ∧ ncolon ≤ 1 ∧ headNotColon``. The bundle has NO consumed
             axiom, so the shadow is pure R/I.
  * ORACLE — ``patch.diff``'s behaviour: a FULL match of the post-patch
             ``URLValidator`` user:pass authentication group
             ``[^\\s:@/]+(?::[^\\s:@/]*)?`` (re.IGNORECASE) on the candidate
             segment, the real correctness oracle for the changed regex literal.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs stdlib only; the fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import re
import random
import sys

SEED = 10097
N_FUZZ = 100000

# The post-patch user:pass authentication group, compiled as the validator does.
USERINFO = re.compile(r'[^\s:@/]+(?::[^\s:@/]*)?', re.IGNORECASE)

_WS = (set(range(9, 14)) | {32}
       | set(range(0x1c, 0x20)) | {0x85, 0xa0, 0x1680}
       | set(range(0x2000, 0x200b)) | {0x2028, 0x2029, 0x202f, 0x205f, 0x3000})


def shadow_decision(seg):
    """validateAuthsegment transliterated to str (the R/I impl shadow): the
    backward per-code-point fold, returning non-empty ∧ no leading ':' ∧ every
    non-':' code point an authentication char ∧ at most one ':'."""
    cps = [ord(ch) for ch in seg]
    if len(cps) == 0:
        return False
    if cps[0] == 58:
        return False
    good = True
    ncolon = 0
    for c in cps:
        if c == 58:
            ncolon += 1
        elif not (c not in _WS and c != 64 and c != 47):
            good = False
    return good and ncolon <= 1


def oracle_decision(seg):
    """patch.diff's behaviour: a FULL match of the post-patch userinfo group."""
    return USERINFO.fullmatch(seg) is not None


def fuzz_inputs(n, rng):
    ws_extra = [chr(c) for c in sorted(_WS) if c not in (9, 10, 11, 12, 13, 32)]
    forbidden = [':', '@', '/', ' ', '\t', '\n', '\r'] + ws_extra
    ordinary = list("aZ09-.%482f!$&'()*+,;=~_") + ['\U0001F600', '\xe9', '•']
    alphabet = forbidden + ordinary
    # boundary cases first (plan §4.1 step 4)
    yield ""
    for c in forbidden:
        yield c
        yield c + c
        yield "foo" + c
        yield "foo" + c + "bar"
    for s in ["foo", "foo:bar", "foo:bar:baz", "foo/bar", "foo@bar",
              "foo:bar@baz", "foo:bar/baz", ":pass", ":", "user:", "a:b",
              "-.~_!$&'()*+,;=%40:80%2f", "m=foo", "m=foo@example.com",
              "foo\xa0bar", "user　pass"]:
        yield s
    for _ in range(n):
        k = rng.randint(0, 16)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_decision(s)
        oracle = oracle_decision(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of validateAuthsegment agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
