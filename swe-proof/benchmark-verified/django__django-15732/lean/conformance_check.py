#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
`implementation_selectUniqueToDrop` against the patch.diff behaviour (the
post-patch constraint-selection decision in `_delete_composed_index`).

The impl region is entirely I/R-tagged (no A-tagged callees: the helper outputs
`candidates` and `defaultName` are free inputs). The shadow therefore reproduces
the post-patch decision op-for-op; we assert zero disagreements vs an
independent reconstruction of the patched block over >=10^5 fuzzed inputs.

Modeling of the boundary `raise ValueError` <-> `Except.error ()`:
  - patched returns ("error", None) when narrowed candidates != exactly 1
  - patched returns ("ok", name)  when narrowed candidates == exactly 1

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 15732          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(candidates, is_unique, allows_multiple, default_name):
    """R/I shadow of implementation_selectUniqueToDrop.

    names := candidates
    if isUnique and names and allowsMultiple and defaultName in names:
        names := [defaultName]
    if len(names) != 1: error
    else: ok names[0]
    """
    names = list(candidates)
    if is_unique and len(names) > 0 and allows_multiple and default_name in names:
        names = [default_name]
    if len(names) != 1:
        return ("error", None)
    return ("ok", names[0])


def patched_decision(candidates, is_unique, allows_multiple, default_name):
    """Independent reconstruction of the post-patch block:

        if (constraint_kwargs.get("unique") is True
                and constraint_names
                and ...allows_multiple_constraints_on_same_fields):
            default_name = str(self._unique_constraint_name(...))
            if default_name in constraint_names:
                constraint_names = [default_name]
        if len(constraint_names) != 1:
            raise ValueError(...)
        ...constraint_names[0]
    """
    constraint_names = list(candidates)
    if is_unique is True and constraint_names and allows_multiple:
        if default_name in constraint_names:
            constraint_names = [default_name]
    if len(constraint_names) != 1:
        return ("error", None)
    return ("ok", constraint_names[0])


def main() -> int:
    rng = random.Random(SEED)
    # Small identifier alphabet so `default_name in candidates` is frequently hit.
    IDS = ["t_id_pkey", "t_name_key", "t_id_fb61f881_uniq",
           "t_name_694f3b9f_uniq", "other_uniq", "x"]

    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        ([], True, True, "t_name_694f3b9f_uniq"),                       # empty -> error
        (["only_uniq"], True, True, "only_uniq"),                       # single -> ok
        (["only_uniq"], True, True, "other"),                           # single, no narrow -> ok
        (["t_name_key", "t_name_694f3b9f_uniq"], True, True,
         "t_name_694f3b9f_uniq"),                                       # F2P unique_field: narrow -> ok
        (["t_id_pkey", "t_id_fb61f881_uniq"], True, True,
         "t_id_fb61f881_uniq"),                                         # F2P pk_field: narrow -> ok
        (["a", "b"], True, False, "a"),                                 # multi disallowed -> error
        (["a", "b"], False, True, "a"),                                 # not unique -> error
        (["a", "b"], True, True, "zzz"),                                # default absent -> error
        (["a", "b", "c"], True, True, "b"),                             # narrow from 3 -> ok
    ]
    cases = list(fixed)
    for _ in range(N):
        k = rng.randint(0, 4)
        cands = [rng.choice(IDS) for _ in range(k)]
        is_unique = rng.choice([True, False])
        allows_multiple = rng.choice([True, False])
        default_name = rng.choice(IDS)
        cases.append((cands, is_unique, allows_multiple, default_name))

    for c, iu, am, dn in cases:
        got = shadow(c, iu, am, dn)
        want = patched_decision(c, iu, am, dn)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((c, iu, am, dn, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for c, iu, am, dn, g, w in examples:
            print(f"  in=({c},{iu},{am},{dn!r}) shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
