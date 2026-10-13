#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15128.

The bundle models ONE operation: the change-map construction inside
`Query.bump_prefix` (`django/db/models/sql/query.py`). Its Lean implementation
(`implementation_renumberAliases`) walks the current aliases in order, paired
with their 0-based positions, and records `(alias, '<prefix><pos>')` for each
alias that is NOT reserved:

    change_map = []
    for pos, alias in enumerate(aliases):
        if alias in reserved:        # post-fix `if alias not in exclude`
            continue
        change_map.append((alias, prefix + str(pos)))
    return change_map

The position `pos` is the alias's index in the FULL enumeration — a reserved
alias still consumes its index (faithful to `enumerate(self.alias_map)` running
over the whole map with the `if` filtering only which entries are emitted).

This script transliterates that R/I impl into Python (`shadow_change_map`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH change-map comprehension of `bump_prefix`:

    {alias: '%s%d' % (prefix, pos)
     for pos, alias in enumerate(alias_map)
     if alias not in exclude}

We do NOT stand up a Django Query / ORM (heavy, and the modeled value is a pure
function of the alias keys, the exclude set, and the prefix). Instead we
reproduce the patched comprehension over light stand-in alias lists carrying the
SAME observables the real `enumerate(self.alias_map)` exposes (mapping.md): the
ordered alias keys. Alias names are modeled as small ints (an injective encoding
of the distinct alias strings; only equality/membership and position are
observed).

The differential genuinely tests the Lean modeling: the shadow uses the Lean
`isReserved` membership guard and `zipIdx` positional numbering, whereas the
oracle reproduces the patched `if alias not in exclude` comprehension over
realistically shaped alias lists. They must agree for every input — in
particular when the reserved/exclude set names the base (initial) alias, the case
the patch is built around.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 15128 (also recorded in
mapping.md).
"""
import sys

SEED = 15128
N = 120_000


# --- ORACLE: the post-patch bump_prefix change-map comprehension -------------
# `alias_map` is the ordered list of current alias keys (distinct). `exclude` is
# the `exclude` set (None modeled as empty). `prefix` is the bumped alias_prefix.
def oracle_change_map(prefix, exclude, alias_map):
    if exclude is None:
        exclude = set()
    # Build the dict via the comprehension, then materialize as an ordered list
    # of (old, new) pairs in alias_map order (dicts preserve insertion order).
    d = {
        alias: '%s%d' % (prefix, pos)
        for pos, alias in enumerate(alias_map)
        if alias not in exclude
    }
    return list(d.items())


# --- shadow of implementation_renumberAliases (the R/I leg) ------------------
# Mirrors Solution.lean: isReserved (membership in `reserved`) + positional
# naming over the full enumeration (zipIdx). `reserved` is a list (None == []).
def is_reserved(reserved, a):
    return a in reserved


def fresh_name(prefix, pos):
    return prefix + str(pos)


def shadow_change_map(prefix, reserved, aliases):
    change_map = []
    for pos, alias in enumerate(aliases):
        if is_reserved(reserved, alias):
            continue
        change_map.append((alias, fresh_name(prefix, pos)))
    return change_map


def disagree(prefix, reserved, aliases):
    # `reserved`/`exclude` feed BOTH legs identically (None -> []/set()).
    exclude = set(reserved) if reserved is not None else None
    res_list = reserved if reserved is not None else []
    got = oracle_change_map(prefix, exclude, aliases)
    want = shadow_change_map(prefix, res_list, aliases)
    if got != want:
        return ((prefix, reserved, aliases), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases exercising the reserve-base-alias fix."""
    base = [10, 11, 12, 13]          # four distinct aliases, base == 10
    cases = [
        # no reservation -> every alias renamed (pre-existing behavior)
        ("T", None, base),
        ("T", [], base),
        # reserve the BASE/initial alias (the combine() use): it keeps its name,
        # the others are renumbered, and crucially keep their FULL-enumeration pos
        ("T", [10], base),
        # reserve a middle alias: 11 dropped, others keep positions 0,2,3
        ("T", [11], base),
        # reserve an absent alias: no effect
        ("T", [99], base),
        # reserve several
        ("T", [10, 12], base),
        # multi-char prefix
        ("AB", [10], base),
        # empty alias list
        ("T", None, []),
        ("T", [10], []),
        # single alias, reserved
        ("T", [5], [5]),
    ]
    return cases


def _rand_alias_list(rnd):
    length = next(rnd) % 9            # 0..8 aliases
    pool = list(range(8))            # small pool so reservation membership bites
    aliases = []
    for _ in range(length):
        a = pool[next(rnd) % len(pool)]
        if a not in aliases:         # alias keys are distinct within a map
            aliases.append(a)
    return aliases


def _rand_reserved_or_none(rnd, aliases):
    tag = next(rnd) % 4
    if tag == 0:
        return None                  # exclude not supplied
    length = next(rnd) % 4           # 0..3 reserved (0 => empty list)
    pool = list(range(8))
    return [pool[next(rnd) % len(pool)] for _ in range(length)]


def _rand_prefix(rnd):
    prefixes = ["T", "U", "AB", "Z", "AA"]
    return prefixes[next(rnd) % len(prefixes)]


def main() -> int:
    checked = 0

    for prefix, reserved, aliases in _enumerate_edge():
        d = disagree(prefix, reserved, aliases)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        aliases = _rand_alias_list(rnd)
        reserved = _rand_reserved_or_none(rnd, aliases)
        prefix = _rand_prefix(rnd)
        d = disagree(prefix, reserved, aliases)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
