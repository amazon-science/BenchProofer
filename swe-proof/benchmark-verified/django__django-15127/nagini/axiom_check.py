#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15127.

This bundle consumes NO `@ContractOnly` axiom. The only callee distance is the
unchanged Python mapping merge `{**defaults, **override}` (as composed by
`get_level_tags()`), which `model.py` models DEEPLY as the pure `merge_slot`
per-level choice. G-AX validates that deep model (the A-reference) against the
REAL Python primitive, plus the unchanged per-level read `.get(level, '')` the
`Message.level_tag` property performs.

Two checks, both against real Python (no repo import needed — the merge and the
`.get` are language/stdlib primitives the gold patch composes):

  (A-reference) `merge_slot(d_slot, o_slot)` == the per-level value of the real
      merge `{**defaults, **override}`, under the None<->absent encoding:
        - a level the override carries -> the override's value (override wins)
        - else a level only the defaults carry -> the default's value
        - else the level is absent
      i.e. for every level k: `{**d, **o}.get(k) == merge_slot(d.get(k), o.get(k))`.

  (read)        `read_slot(slot)` == the real `.get(level, '')` read:
        - a present level reads its tag; an absent level reads the empty tag.

It also reproduces the F2P scenario (a custom level the defaults never had) and
asserts the re-derived mapping reads the override tag there, not the empty tag.

Imports only the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

# model.py encodings (kept in lock-step with the spec) -----------------------
EMPTY_TAG = ""          # model: empty_tag()  (the '' default of .get(level,''))
ABSENT = None           # model: an Optional[int] slot of None == level absent


def merge_slot(d_slot, o_slot):
    """Reference of model.py's deep model merge_slot on one level's slots:
    the override value wins where the override carries the level, else the
    default value (None == absent)."""
    if o_slot is not None:
        return o_slot
    return d_slot


def read_slot(slot):
    """Reference of model.py's read (LEVEL_TAGS.get(level, '')): a present slot
    reads its tag, an absent slot reads the empty tag."""
    if slot is None:
        return EMPTY_TAG
    return slot


def real_merge(defaults, override):
    """The REAL Python primitive the gold patch composes in get_level_tags():
    {**DEFAULT_TAGS, **MESSAGE_TAGS}."""
    return {**defaults, **override}


def check_merge_reference(defaults, override):
    """Assert merge_slot == the real {**d, **o} merge, per level, under the
    None<->absent encoding. Covers every level either dict mentions plus a
    level neither has (must stay absent)."""
    merged = real_merge(defaults, override)                       # real callee
    levels = set(defaults) | set(override) | {-999, 0, 12, 20, 30, 40}
    for k in levels:
        real_val = merged.get(k, ABSENT)                          # None == absent
        model_val = merge_slot(defaults.get(k, ABSENT),           # deep model
                               override.get(k, ABSENT))
        assert real_val == model_val, (
            "merge_slot deep model unsound at level %r: real {**d,**o} -> %r, "
            "deep model -> %r (defaults=%r override=%r)"
            % (k, real_val, model_val, defaults, override))
        # the .get(level, '') read agrees too (the Message.level_tag read)
        real_read = merged.get(k, EMPTY_TAG)                      # real .get
        model_read = read_slot(model_val)                         # model read
        assert real_read == model_read, (
            "read mismatch at level %r: real .get -> %r, model read -> %r"
            % (k, real_read, model_read))


def main():
    default_tags = {10: "debug", 20: "info", 25: "success",
                    30: "warning", 40: "error"}

    # --- boundary cases ----------------------------------------------------
    boundary = [
        {},                                              # no override -> defaults
        {20: "info-new"},                                # re-tag one built-in
        {30: ""},                                        # re-tag to empty string
        {12: "custom"},                                  # a custom level (the F2P)
        {10: "", 20: "info", 30: "", 40: "bad", 25: "", 12: "custom"},  # F2P dict
        {20: "x", 30: "y", 99: "z"},                     # mixed + custom
        {10: "debug"},                                   # override == a default
    ]
    for ov in boundary:
        check_merge_reference(default_tags, ov)
        # defaults themselves vary too (e.g. a future default family)
        check_merge_reference({}, ov)
        check_merge_reference(ov, {})

    # --- the F2P scenario: a custom level reads the override tag, not '' ----
    f2p_override = {20: "info", 10: "", 30: "", 40: "bad", 25: "", 12: "custom"}
    merged = real_merge(default_tags, f2p_override)
    # base.LEVEL_TAGS == MESSAGE_TAGS in the F2P (override re-tags every default
    # level and adds the custom one); the custom level reads its tag.
    assert merged == f2p_override, (
        "F2P merge mismatch: %r != %r" % (merged, f2p_override))
    assert read_slot(merge_slot(default_tags.get(12, ABSENT),
                                f2p_override.get(12, ABSENT))) == "custom", (
        "custom level 12 must read 'custom' after re-derivation, not the empty tag")
    # pre-patch contrast: the stale mapping (defaults only) reads '' at level 12
    assert read_slot(default_tags.get(12, ABSENT)) == EMPTY_TAG, (
        "stale defaults-only mapping must read the empty tag at the custom level")

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(15127)
    tag_pool = ["", "a", "info", "bad", "custom", "warning", "x", "y"]
    level_pool = list(range(0, 60)) + [10, 20, 25, 30, 40, 12, 99]
    for _ in range(20000):
        d = {rng.choice(level_pool): rng.choice(tag_pool)
             for _ in range(rng.randint(0, 6))}
        o = {rng.choice(level_pool): rng.choice(tag_pool)
             for _ in range(rng.randint(0, 6))}
        check_merge_reference(d, o)

    print("G-AX OK: merge_slot deep model (== real {**d,**o}) + read_slot "
          "(== real .get(level,'')) sound on %d boundary + 20000 fuzz merges; "
          "F2P custom-level re-derivation verified." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
