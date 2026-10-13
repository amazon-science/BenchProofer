#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_serializeEnum
against the patch.diff behaviour (post-patch enum-member reference rendering).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: concatenate the module path, '.', the class name,
'[', the quoted member identifier, ']'; the payload is discarded. We diff that
against an independent reconstruction of the post-patch rendering: substitution of
the module path, class name, and member identifier into the literal template
'%s.%s[%r]' exactly as the patched return statement does. Zero disagreements
required over >=10^5 fuzzed inputs.

The member identifier is a Python identifier (name characters only), so its `%r`
(== repr) is the identifier wrapped in single quotes; the shadow's `quoted`
models exactly that. The fuzz draws identifiers ONLY from identifier characters,
matching the real `Enum` member-name domain (mapping.md).

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import string
import sys

SEED = 11815          # pinned in mapping.md
N = 120_000           # >= 10^5

TEMPLATE = "%s.%s[%r]"

# Module-path and class-name alphabets (dotted identifiers / CamelCase names).
MODULE_PARTS = ["migrations", "test_writer", "app", "models", "re", "enum",
                "django", "core", "validators", "a", "x_y"]
CLASS_NAMES = ["TextEnum", "BinaryEnum", "IntEnum", "TextTranslatedEnum",
               "RegexFlag", "Status", "E", "MyEnum123"]
# Member identifiers: drawn from identifier characters only (the real domain of
# Enum member names). First char a letter/underscore.
NAME_HEAD = string.ascii_letters + "_"
NAME_TAIL = string.ascii_letters + string.digits + "_"
# Payload text: an arbitrary already-rendered repr; the post-patch path must
# ignore it, so we oversample chars (quotes, parens, brackets) that would break a
# naive renderer that still consulted it.
PAYLOAD_ALPHABET = list("abcXYZ_0123 '\"()[]b.-=,")


def rand_dotted(rng) -> str:
    return ".".join(rng.choice(MODULE_PARTS)
                    for _ in range(rng.randint(1, 3)))


def rand_name(rng) -> str:
    n = rng.randint(1, 12)
    return rng.choice(NAME_HEAD) + "".join(rng.choice(NAME_TAIL)
                                           for _ in range(n - 1))


def quoted(s: str) -> str:
    """Model of `%r` of a member identifier: identifier wrapped in single quotes."""
    return "'" + s + "'"


def shadow(module: str, class_name: str, name: str, payload: str) -> str:
    """R/I shadow of implementation_serializeEnum (payload discarded)."""
    return module + "." + class_name + "[" + quoted(name) + "]"


def patched_render(module: str, class_name: str, name: str, payload: str) -> str:
    """Independent reconstruction of the post-patch return[0]: substitute into the
    literal template '%s.%s[%r]' with the member identifier as the `%r` arg."""
    return TEMPLATE % (module, class_name, name)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shapes.
    fixed = [
        ("migrations.test_writer", "TextEnum", "A", "'a-value'"),
        ("migrations.test_writer", "TextEnum", "B", "'value-b'"),
        ("migrations.test_writer", "BinaryEnum", "A", "b'a-value'"),
        ("migrations.test_writer", "IntEnum", "B", "2"),
        ("re", "RegexFlag", "DOTALL", "16"),
        ("a", "E", "X", ""),
        ("x_y.app.models", "MyEnum123", "Z9", "'(weird)payload'"),
    ]
    cases = fixed + [
        (
            rand_dotted(rng),
            rng.choice(CLASS_NAMES),
            rand_name(rng),
            "".join(rng.choice(PAYLOAD_ALPHABET)
                    for _ in range(rng.randint(0, 24))),
        )
        for _ in range(N)
    ]

    for module, class_name, name, payload in cases:
        got = shadow(module, class_name, name, payload)
        want = patched_render(module, class_name, name, payload)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((module, class_name, name, payload), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
