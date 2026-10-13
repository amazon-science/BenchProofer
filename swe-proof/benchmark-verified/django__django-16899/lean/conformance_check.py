#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_checkReadonlyFieldsItem against the patch.diff behaviour
(post-patch `_check_readonly_fields_item`).

The impl region is NOT all-A-tagged (it is all R/I, refinement.md), so this
runs a real fuzz. The four UNCHANGED resolution checks are R-refined to the
booleans (isCallable, hasAttrObj, hasAttrModel, fieldExists); the changed op
(the error message, row 5) is modeled deeply as the concrete format string. We
assert zero disagreements vs an independent reconstruction of the patched
function over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16899          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(obj_class, model_label, field_name, label,
           is_callable, has_attr_obj, has_attr_model, field_exists):
    """R/I shadow of implementation_checkReadonlyFieldsItem.

    Four short-circuit acceptances, then the single error message.
    Returns a list of 0 or 1 message strings.
    """
    if is_callable:
        return []
    if has_attr_obj:
        return []
    if has_attr_model:
        return []
    if field_exists:
        return []
    msg = ("The value of '%s' refers to '%s', which is not a callable, "
           "an attribute of '%s', or an attribute of '%s'."
           % (label, field_name, obj_class, model_label))
    return [msg]


def patched(obj_class, model_label, field_name, label,
            is_callable, has_attr_obj, has_attr_model, field_exists):
    """Independent reconstruction of the post-patch django
    _check_readonly_fields_item behaviour. The four checks short-circuit to []
    (matching the original `if callable / elif hasattr / elif hasattr /
    try get_field ... else` ladder); otherwise the post-patch E035 message."""
    if is_callable or has_attr_obj or has_attr_model or field_exists:
        return []
    msg = ("The value of '%s' refers to '%s', which is not a callable, "
           "an attribute of '%s', or an attribute of '%s'."
           % (label, field_name, obj_class, model_label))
    return [msg]


# A spread of realistic + adversarial string values.
STRINGS = [
    "", "x", "nonexistent", "i_dont_exist", "readonly_fields[0]",
    "readonly_fields[1]", "SongAdmin", "CityInline", "admin_checks.Song",
    "admin_checks.City", "a'b", 'q"r', "field with spaces", "%s%d",
    "üñîçödé", "field\nname", "'", "''",
]


def rand_str(rng):
    return rng.choice(STRINGS)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    cases = []
    # Deterministic boundary: every boolean combination with fixed strings,
    # plus the F2P-shaped error cases.
    for bits in range(16):
        flags = [(bits >> k) & 1 == 1 for k in range(4)]
        cases.append(("SongAdmin", "admin_checks.Song", "nonexistent",
                      "readonly_fields[1]", *flags))
        cases.append(("CityInline", "admin_checks.City", "i_dont_exist",
                      "readonly_fields[0]", *flags))

    # Oversample the all-false combination (the changed message branch).
    for _ in range(N):
        if rng.random() < 0.55:
            flags = [False, False, False, False]
        else:
            flags = [rng.random() < 0.25 for _ in range(4)]
        cases.append((rand_str(rng), rand_str(rng), rand_str(rng),
                      rand_str(rng), *flags))

    for c in cases:
        got = shadow(*c)
        want = patched(*c)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((c, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for c, g, w in examples:
            print(f"  in={c!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
