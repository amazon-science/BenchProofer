#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8035.

The bundle models ONE decision: the keep/drop choice for a *private* member in
`Documenter.filter_members` (`sphinx/ext/autodoc/__init__.py`). Its Lean
implementation (`implementation_keepPrivateMember`) decides whether a private,
documented member is kept, given the `:private-members:` selection (post-patch:
None / ALL / a list of names), the member's name, whether it is documented,
whether undocumented members are being kept, and whether it is a dropped
inherited member:

    if has_doc or undoc_members:
        if private_members is None:            keep = False        # disabled
        elif private_members is ALL:           keep = True         # all
        elif is_filtered_inherited_member:     keep = False        # names + inherited
        else:                                  keep = name in private_members
    else:
        keep = False

This script transliterates that R/I impl into Python (`shadow_keep`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH private-member arm of `filter_members`.

We do NOT stand up Sphinx's autodoc machinery (heavy; the modeled value is a pure
decision over the option shape, the member name, and three booleans). Both legs
are total functions over the modeled abstraction, so the edge set EXHAUSTIVELY
enumerates the modeled input space (3 option shapes × a small ASCII name
alphabet × hasDoc/undocMembers/dropAsInherited booleans × list contents); the
fuzz loop additionally samples random points. The discriminating case —
`private_members` is an explicit list and the member's name is NOT in it —
is covered exhaustively: oracle (post-patch) returns False, while the pre-patch
bool-flag code would return True.

stdlib-only. Pinned seed: 8035 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 8035
N = 120_000

# Sentinel standing for the `ALL` object() used by `members_option`.
ALL = object()
# ASCII member-name alphabet (autodoc member identifiers, leading-underscore
# private names included).
NAMES = ("_a", "_b", "_public_function", "private_function")
# Candidate list contents for the `names` shape.
LISTS = ((), ("_a",), ("_public_function",), ("_a", "_b"))


def _options():
    """Enumerate the modeled `private_members` shapes:
    None (disabled), ALL, and explicit lists."""
    yield None
    yield ALL
    for lst in LISTS:
        yield list(lst)


# --- ORACLE: the post-patch private-member arm, faithful in-process replica ----
def oracle_keep(private_members, name, has_doc, undoc_members, drop_as_inherited):
    if has_doc or undoc_members:
        if private_members is None:
            return False
        elif private_members is ALL:
            return True
        elif drop_as_inherited:
            return False
        else:
            return name in private_members
    else:
        return False


# --- shadow of implementation_keepPrivateMember (the R/I leg) -----------------
# Mirrors Solution.lean op-for-op.
def shadow_keep(private_members, name, has_doc, undoc_members, drop_as_inherited):
    keep = False
    if has_doc or undoc_members:
        if private_members is None:
            keep = False
        elif private_members is ALL:
            keep = True
        else:
            if drop_as_inherited:
                keep = False
            else:
                keep = name in private_members
    else:
        keep = False
    return keep


def disagree(pm, name, hd, um, di):
    got = oracle_keep(pm, name, hd, um, di)
    want = shadow_keep(pm, name, hd, um, di)
    if got != want:
        return (pm, name, hd, um, di, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0
    bools = (False, True)

    # Edge set = EXHAUSTIVE over the modeled abstraction.
    for pm in _options():
        for name, hd, um, di in itertools.product(NAMES, bools, bools, bools):
            d = disagree(pm, name, hd, um, di)
            if d:
                print(f"DISAGREE exhaustive pm={d[0]!r} name={d[1]!r} "
                      f"hd={d[2]} um={d[3]} di={d[4]}: oracle={d[5]} shadow={d[6]}")
                print("status=fail")
                return 1
            checked += 1

    # Redundant random fuzz over a wider name alphabet.
    rnd = _lcg(SEED)
    alpha = ("_a", "_b", "_c", "_public_function", "private_function", "_x", "_y")
    listpool = [None, ALL] + [list(l) for l in LISTS] + [["_x"], ["_y", "_a"]]

    def pick(seq):
        return seq[next(rnd) % len(seq)]

    for _ in range(N):
        pm = pick(listpool)
        name = pick(alpha)
        hd = bool(next(rnd) & 1)
        um = bool(next(rnd) & 1)
        di = bool(next(rnd) & 1)
        d = disagree(pm, name, hd, um, di)
        if d:
            print(f"DISAGREE fuzz pm={d[0]!r} name={d[1]!r} "
                  f"hd={d[2]} um={d[3]} di={d[4]}: oracle={d[5]} shadow={d[6]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
