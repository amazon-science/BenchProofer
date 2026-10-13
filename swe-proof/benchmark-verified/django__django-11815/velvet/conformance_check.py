#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11815 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (`str`, `set[str]`), via the
              mapping.md bijection (`List Char` ↔ `str`,
              `List (List Char)` ↔ `set[str]`). The impl region has NO A-tagged
              callee (mapping.md §3.1), so the whole shadow is pure R/I:
                  ref     = "%s.%s[%r]" % (module, class_name, member_name)
                  imports = {"import %s" % module}
              The `%r` is reproduced as `"'" + name + "'"`; the fuzz alphabet is
              restricted to the enum-identifier alphabet so this is exact
              (mapping.md §3.2).
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `EnumSerializer.serialize` (the correctness oracle, G-RESOLVE),
              driven on a real enum member built dynamically with the fuzzed
              module / class / member names and a (deliberately varied) payload.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + Django only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import enum
import random
import string
import sys

SEED = 11815
N_FUZZ = 100_000

# The enum-identifier alphabet (mapping.md §3.2): a name is a valid Python
# identifier, so repr(name) == "'" + name + "'" exactly (no double quotes, no
# backslash escaping). First char a letter or underscore; rest add digits.
FIRST = string.ascii_letters + "_"
REST = string.ascii_letters + string.digits + "_"
# Module strings are dotted identifiers (e.g. "migrations.test_writer").
MOD_PART = string.ascii_letters + string.digits + "_"


def _valid_member(name):
    """The enum machinery rejects `_sunder_` / `__dunder__` names as members, so
    a real enum member name is never one (mapping.md §3.2). Restrict the fuzz
    domain to the names that can actually occur."""
    if len(name) >= 2 and name[0] == "_" and name[-1] == "_":
        return False
    return True


def ident(rng, lo=1, hi=8):
    while True:
        n = rng.randint(lo, hi)
        s = rng.choice(FIRST) + "".join(rng.choice(REST) for _ in range(n - 1))
        if _valid_member(s):
            return s


def module_name(rng):
    nparts = rng.randint(1, 3)
    parts = []
    for _ in range(nparts):
        k = rng.randint(1, 6)
        parts.append("".join(rng.choice(MOD_PART) for _ in range(k)) or "m")
    return ".".join(parts)


# --- the R/I shadow: Solution.lean memberReference + referenceImports --------
def quoted_name(name):
    # quotedName: ['\''] ++ name ++ ['\'']  (exact repr for identifier names)
    return "'" + name + "'"


def shadow(module, class_name, member_name):
    ref = module + "." + class_name + "[" + quoted_name(member_name) + "]"
    imports = {"import " + module}
    return ref, imports


# --- the oracle: the REAL patched EnumSerializer.serialize -------------------
def oracle(module, class_name, member_name, payload):
    """Build a genuine enum member with the given names + payload, then run the
    patched EnumSerializer.serialize on it (mapping.md §1)."""
    from django.db.migrations.serializer import EnumSerializer
    # Dynamically construct the enum type so __name__/__module__/member .name
    # are exactly the fuzzed strings (the three reads serialize() performs).
    EnumCls = enum.Enum(class_name, {member_name: payload})
    EnumCls.__module__ = module
    member = EnumCls[member_name]
    return EnumSerializer(member).serialize()


def boundary_cases():
    # The F2P scenarios and neighbours (test_writer): identifier member names,
    # varied payloads (str, translatable str, bytes, int) — all unused post-patch.
    yield ("migrations.test_writer", "TextEnum", "A", "a-value")
    yield ("migrations.test_writer", "TextTranslatedEnum", "A", "a-value")
    yield ("migrations.test_writer", "BinaryEnum", "A", b"a-value")
    yield ("migrations.test_writer", "IntEnum", "B", 2)
    yield ("re", "RegexFlag", "DOTALL", 16)
    yield ("a", "C", "GOOD", "Good")
    yield ("x.y.z", "Status", "BAD", "Bad")
    yield ("m", "E", "_underscore", 0)


def main():
    rng = random.Random(SEED)
    payloads = ["a-value", "value-b", "Good", b"bytes", 1, 2, 16, "", "x'y", 'q"r']
    disagreements = []
    count = 0

    cases = list(boundary_cases())
    cases += [(module_name(rng), ident(rng), ident(rng),
               rng.choice(payloads)) for _ in range(N_FUZZ)]

    for module, class_name, member_name, payload in cases:
        count += 1
        sh = shadow(module, class_name, member_name)
        try:
            orc = oracle(module, class_name, member_name, payload)
        except Exception as e:  # pragma: no cover
            disagreements.append((module, class_name, member_name, payload,
                                  sh, "EXC: %r" % e))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append((module, class_name, member_name, payload, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for mod, cn, mn, pl, sh, orc in disagreements:
            print("  module=%r class=%r member=%r payload=%r\n    shadow=%r\n    oracle=%r"
                  % (mod, cn, mn, pl, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of referenceEnumMember agrees with the real "
          "patched EnumSerializer.serialize on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
