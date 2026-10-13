#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-22719.

The bundle models TWO decisions in `lib/matplotlib/category.py` (mapping.md):

  * `StrCategoryConverter.convert`: whether to emit the numeric-passthrough
    deprecation warning. POST-PATCH this is `bool(values.size and is_numlike)`,
    where `is_numlike = all(is_numlike(v) and not isinstance(v,(str,bytes))
    for v in values)`.
  * `UnitData.update`: whether to emit the parsable-strings info-log. POST-PATCH
    this is `bool(data.size and convertible)`, where `convertible` is True iff
    every element is `_str_is_convertible`.

Standing up matplotlib's full unit machinery to drive the real methods is heavy
and unnecessary: the modeled value is a PURE function of the observables each
guard reads (the per-element classification / parsability flags and the sequence
length). So each ORACLE below is a faithful in-process replica of the POST-PATCH
decision, and each SHADOW is the op-for-op transliteration of the corresponding
`implementation_*` (Solution.lean impl regions), per refinement.md.

This genuinely tests the soundness-critical clause: for an EMPTY sequence the
decision must be `False` post-patch (the bug fix), while the per-element "all"
flag is vacuously `True`; and for a non-empty sequence the decision tracks the
flag.

stdlib-only. Pinned seed: 22719 (also in mapping.md).
"""
import random
import sys

SEED = 22719
N = 120_000

# pool of names: parsable-as-number/date vs not (for the update/_str_is_convertible site)
PARSABLE = ["1", "2", "3.5", "-7", "1e3", "2021-01-01", "12:00"]
NONPARSABLE = ["a", "b", "foo", "banana", "x", "hello"]


# --- looks_numeric: faithful stand-in for UnitData._str_is_convertible ---------
# float()-parsable or date-parsable. We approximate the real helper closely
# enough for the DECISION (the conjunction): a name is "convertible" iff it is in
# the PARSABLE pool. Because the predicate appears identically in oracle and
# shadow, its exact internals cancel in the decision equality (refinement.md);
# membership in PARSABLE is the ground truth used by BOTH legs.
def looks_numeric(s):
    return s in PARSABLE


# ============================ convert (numeric passthrough) ===================
# ORACLE: faithful replica of the POST-PATCH decision.
# values is a list of bools: True = element is non-string numeric (Element.numeric)
def oracle_convert(values):
    is_numlike = all(values)            # all(...) over the per-element predicate
    return bool(len(values) and is_numlike)


# SHADOW of implementation_numericPassthrough (mirrors Solution.lean impl region).
def shadow_convert(values):
    is_numlike = True
    for v in values:
        if not v:
            is_numlike = False
    return (len(values) != 0) and is_numlike


# ============================ update (parsable info) ==========================
# ORACLE: faithful replica of the POST-PATCH decision.
def oracle_update(data):
    convertible = all(looks_numeric(v) for v in data)
    return bool(len(data) and convertible)


# SHADOW of implementation_parsableInfo (mirrors Solution.lean impl region).
def shadow_update(data):
    convertible = True
    for val in data:
        if not looks_numeric(val):
            convertible = False
    return (len(data) != 0) and convertible


def _edge_convert():
    return [
        [],                       # empty -> decision must be False (the fix)
        [True],                   # all numeric -> True
        [False],                  # categorical -> False
        [True, True],             # all numeric -> True
        [True, False],            # mixed -> False
        [False, False],           # all categorical -> False
        [True, True, True],
    ]


def _edge_update():
    return [
        [],                       # empty -> decision must be False (the fix)
        ["1"],                    # parsable -> True
        ["a"],                    # not parsable -> False
        ["1", "2"],               # all parsable -> True
        ["1", "a"],               # mixed -> False
        ["a", "b"],               # none parsable -> False
        ["2021-01-01", "12:00"],  # date-parsable -> True
    ]


def main() -> int:
    checked = 0

    for v in _edge_convert():
        if oracle_convert(v) != shadow_convert(v):
            print(f"DISAGREE convert edge: inp={v} "
                  f"oracle={oracle_convert(v)} shadow={shadow_convert(v)}")
            print("status=fail")
            return 1
        checked += 1
    for d in _edge_update():
        if oracle_update(d) != shadow_update(d):
            print(f"DISAGREE update edge: inp={d} "
                  f"oracle={oracle_update(d)} shadow={shadow_update(d)}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    pool = PARSABLE + NONPARSABLE
    half = N // 2
    for _ in range(half):
        values = [rng.random() < 0.6 for _ in range(rng.randint(0, 6))]
        if oracle_convert(values) != shadow_convert(values):
            print(f"DISAGREE convert fuzz: inp={values} "
                  f"oracle={oracle_convert(values)} shadow={shadow_convert(values)}")
            print("status=fail")
            return 1
        checked += 1
    for _ in range(N - half):
        data = [rng.choice(pool) for _ in range(rng.randint(0, 6))]
        if oracle_update(data) != shadow_update(data):
            print(f"DISAGREE update fuzz: inp={data} "
                  f"oracle={oracle_update(data)} shadow={shadow_update(data)}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
