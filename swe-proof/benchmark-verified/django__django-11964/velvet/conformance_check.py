#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11964 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `memberToStr` impl region
              (the deep model `renderValue`) transliterated to Python over the
              real repo types, via the mapping.md §2 bijection:
                  renderValue (intVal n) = (toString n).toList   <->  str(n)
                  renderValue (strVal s) = s                     <->  s
              (Int n <-> Python int; List Char <-> str). There are NO A-tagged
              callees in the impl region (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: a REAL `IntegerChoices` / `TextChoices`
              member built (via the enum functional API) carrying the fuzzed
              payload, rendered by the patched `Choices.__str__` i.e.
              `str(self.value)`. The harness applies patch.diff at base_commit
              before this runs (G-RESOLVE), so the imported `models.Choices`
              already has the new `__str__`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib + django only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import string
import sys

SEED = 11964
N_FUZZ = 100_000


# --- the R/I shadow: renderValue transliterated ----------------------------
def shadow_int(n):
    """renderValue (MemberValue.intVal n) = (toString n).toList, as str.
    Lean `toString (n : Int)` == Python `str(n)` on every integer (decimal,
    optional leading '-', no '+', no leading zeros, no separators)."""
    return str(n)


def shadow_str(s):
    """renderValue (MemberValue.strVal s) = s (identity on List Char)."""
    return s


# --- the oracle: patch.diff's behaviour ------------------------------------
def oracle_int(n):
    """str(member) for a REAL IntegerChoices member with value n, under the
    patched Choices.__str__ (returns str(self.value))."""
    from django.db import models
    C = models.IntegerChoices("C", [("MEMBER", (n, "L"))])
    return str(C.MEMBER)


def oracle_str(s):
    """str(member) for a REAL TextChoices member with value s, under the
    patched Choices.__str__."""
    from django.db import models
    C = models.TextChoices("C", [("MEMBER", (s, "L"))])
    return str(C.MEMBER)


# --- fuzz generators -------------------------------------------------------
def fuzz_ints(n, rng):
    # boundary cases first (plan §4.1 step 4)
    for b in [0, 1, -1, 9, 10, -10, 250, 99, 100, -123456,
              2 ** 31 - 1, -(2 ** 31), 2 ** 63 - 1, -(2 ** 63),
              10 ** 25, -(10 ** 25)]:
        yield b
    for _ in range(n):
        r = rng.random()
        if r < 0.4:
            yield rng.randint(-1000, 1000)
        elif r < 0.7:
            yield rng.randint(-(10 ** 18), 10 ** 18)
        else:
            yield rng.randint(-(10 ** 40), 10 ** 40)


def fuzz_strs(n, rng):
    # boundary cases first: empty, the qualified-name token shape the pre-fix
    # rendering produced (must NOT leak through), whitespace, unicode, quotes.
    for b in ["", "FR", "first", "MyChoice.FIRST_CHOICE", "Suit.DIAMOND",
              " ", "  ", "0", "-5", "x.y 1", 'has"quote', "it's",
              "unicode-é•", "tab\tend", "new\nline", "<a>&amp;"]:
        yield b
    alphabet = list(string.ascii_letters + string.digits + " .,-_'\"\t") + \
        ["é", "•", "中"]
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # split the budget between the two payload shapes
    half = N_FUZZ // 2
    for n in fuzz_ints(half, rng):
        count += 1
        sh = shadow_int(n)
        orc = oracle_int(n)
        if sh != orc:
            disagreements.append(("int", n, sh, orc))
            if len(disagreements) >= 5:
                break
    if len(disagreements) < 5:
        for s in fuzz_strs(half, rng):
            count += 1
            sh = shadow_str(s)
            orc = oracle_str(s)
            if sh != orc:
                disagreements.append(("str", s, sh, orc))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, v, sh, orc in disagreements:
            print("  kind=%s input=%r shadow=%r oracle=%r" % (kind, v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of memberToStr agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
