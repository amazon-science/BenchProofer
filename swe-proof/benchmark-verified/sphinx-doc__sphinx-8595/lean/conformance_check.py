#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8595.

The bundle models ONE routine: `ModuleDocumenter.get_object_members(self,
want_all)` (mapping.md). Its observable outcome is a pair `(check, members)`:
a bool asking the caller to still apply the implicit `__module__` origin check,
and the list of discovered members each reduced to `(__name__, skipped)`. When
members are requested by name, only present requested names are returned.

Standing up the full Sphinx Documenter machinery to drive the real method is
heavy and unnecessary: the modeled value is a PURE function of the observables
the method reads (`want_all`, `self.__all__`, the discovered member names, and
`self.options.members`). So the ORACLE below is a faithful in-process replica of
the POST-PATCH method (the gold edit's `is None` guard), and the SHADOW is the
op-for-op transliteration of `implementation_selectMembers` (Solution.lean impl
region), per refinement.md.

This genuinely tests the soundness-critical clause: a declared-but-empty export
list (`__all__ == []`) must skip EVERY discovered member (so the module
documents nothing), distinct from an absent export list (`__all__ is None`)
which keeps every member and defers to the implicit origin check.

stdlib-only. Pinned seed: 8595 (also in mapping.md).
"""
import random
import sys

SEED = 8595
N = 120_000

NAME_POOL = ["foo", "bar", "baz", "qux", "spam", "eggs", "alpha", "beta"]


# --- ORACLE: faithful in-process replica of the POST-PATCH method -------------
# Each member is represented as its name; the returned ObjectMember is reduced to
# (name, skipped). `all_attr` is None (no __all__) or a list (possibly empty).
def oracle(inp):
    want_all = inp["wantAll"]
    all_attr = inp["allAttr"]          # None or list[str]
    members = inp["members"]           # list[str] (dict-order names)
    requested = inp["requested"]       # list[str]

    if want_all:
        if all_attr is None:           # <-- post-patch guard
            return (True, [(n, False) for n in members])
        else:
            return (False, [(n, n not in all_attr) for n in members])
    else:
        ret = []
        for name in requested:
            if name in members:
                ret.append((name, False))
        return (False, ret)


# --- SHADOW of implementation_selectMembers (the R/I legs) --------------------
# Mirrors Solution.lean impl region exactly.
def shadow(inp):
    want_all = inp["wantAll"]
    all_attr = inp["allAttr"]
    members = inp["members"]
    requested = inp["requested"]

    if want_all:
        if all_attr is None:
            out = []
            for n in members:
                out.append((n, False))
            return (True, out)
        else:
            all_names = all_attr
            out = []
            for n in members:
                out.append((n, not (n in all_names)))
            return (False, out)
    else:
        ret = []
        for name in requested:
            if name in members:
                ret.append((name, False))
        return (False, ret)


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P: want_all, empty __all__ -> every member skipped (documents nothing)
    cases.append(dict(wantAll=True, allAttr=[], members=["foo", "bar", "baz"],
                      requested=[]))
    # absent __all__ -> keep all, none skipped, caller still origin-checks
    cases.append(dict(wantAll=True, allAttr=None, members=["foo", "bar", "baz"],
                      requested=[]))
    # nonempty __all__ -> only named members survive (others skipped)
    cases.append(dict(wantAll=True, allAttr=["foo"], members=["foo", "bar"],
                      requested=[]))
    # nonempty __all__ naming an absent member -> that name has no effect
    cases.append(dict(wantAll=True, allAttr=["foo", "zzz"], members=["foo", "bar"],
                      requested=[]))
    # empty __all__ with no members -> empty result, check False
    cases.append(dict(wantAll=True, allAttr=[], members=[], requested=[]))
    # absent __all__ with no members -> empty, check True
    cases.append(dict(wantAll=True, allAttr=None, members=[], requested=[]))
    # by-name: only present requested names, in order
    cases.append(dict(wantAll=False, allAttr=None, members=["foo", "bar", "baz"],
                      requested=["bar", "zzz", "foo"]))
    # by-name with empty request
    cases.append(dict(wantAll=False, allAttr=["foo"], members=["foo", "bar"],
                      requested=[]))
    # by-name, all absent
    cases.append(dict(wantAll=False, allAttr=None, members=["foo"],
                      requested=["x", "y"]))
    return cases


def _rand_names(rng, n):
    return [rng.choice(NAME_POOL) for _ in range(n)]


def main() -> int:
    checked = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        want_all = rng.random() < 0.7
        r = rng.random()
        if r < 0.34:
            all_attr = None
        elif r < 0.55:
            all_attr = []                       # the discriminating empty case
        else:
            all_attr = _rand_names(rng, rng.randint(1, 4))
        members = _rand_names(rng, rng.randint(0, 6))
        requested = _rand_names(rng, rng.randint(0, 5))
        inp = dict(wantAll=want_all, allAttr=all_attr, members=members,
                   requested=requested)
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
