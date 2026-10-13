#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8593.

The bundle models ONE routine: collecting the documentable entries of a target
module (mapping.md). The soundness-critical behaviour the patch changes is that
each collected entry now carries the DOCUMENTATION COMMENT recorded for its name
(`docstring="\\n".join(attr_docs.get(('', name), []))`), whereas pre-patch the
entries were built from bare `(name, value)` tuples and carried no comment. Every
other aspect of the routine — the per-name value lookup, the dir-order then
annotation-order table construction, the three resolution modes (`want_all` with
no `__all__`, `want_all` with `__all__`, explicit name list) — is unchanged.

ORACLE = faithful in-process replica of the POST-PATCH
`get_object_members`/`get_module_members` logic. SHADOW = op-for-op
transliteration of `implementation_collectModuleEntries` (Solution.lean impl
region), per refinement.md. The two per-name observations (`val`, `doc`) are the
SAME input on both sides, so the diff isolates the modeled construction/resolution.

stdlib-only. Pinned seed: 8593 (also in mapping.md).
"""
import random
import sys

SEED = 8593
N = 120_000

# A member: (name, value, doc, skipped). value=None models the annotation-only
# sentinel (INSTANCEATTR).


def base_table(dir_names, annot_names, val, doc):
    members = []
    for name in dir_names:
        members.append((name, val(name), doc(name), False))
    for name in annot_names:
        if all(m[0] != name for m in members):
            members.append((name, None, doc(name), False))
    return members


def has_exports(all_names):
    return all_names is not None and len(all_names) > 0


# --- ORACLE: faithful replica of the POST-PATCH routine -----------------------
def oracle(want_all, all_names, memberlist, dir_names, annot_names, val, doc):
    table = base_table(dir_names, annot_names, val, doc)
    if want_all:
        if not has_exports(all_names):
            return (True, list(table))
        else:
            ret = []
            for (n, v, d, s) in table:
                if n in all_names:
                    ret.append((n, v, d, s))
                else:
                    ret.append((n, v, d, True))
            return (False, ret)
    else:
        ret = []
        for name in memberlist:
            found = next((m for m in table if m[0] == name), None)
            if found is not None:
                ret.append(found)
        return (False, ret)


# --- SHADOW of implementation_collectModuleEntries (the R/I legs) -------------
# Mirrors Solution.lean impl region exactly.
def shadow(want_all, all_names, memberlist, dir_names, annot_names, val, doc):
    members = []
    for name in dir_names:
        members.append((name, val(name), doc(name), False))
    for name in annot_names:
        if next((m for m in members if m[0] == name), None) is None:
            members.append((name, None, doc(name), False))
    if want_all:
        if all_names is not None and len(all_names) != 0:
            ret = []
            for m in members:
                if m[0] in all_names:
                    ret.append(m)
                else:
                    ret.append((m[0], m[1], m[2], True))
            return (False, ret)
        else:
            return (True, members)
    else:
        ret = []
        for name in memberlist:
            m = next((x for x in members if x[0] == name), None)
            if m is not None:
                ret.append(m)
        return (False, ret)


def disagree(case):
    got = oracle(*case)
    want = shadow(*case)
    if got != want:
        return (case[:5], got, want)
    return None


NAME_POOL = ["a", "b", "_c", "_PUBLIC_CONSTANT", "PRIVATE_CONSTANT",
             "_public_function", "x", "_y", "z", "foo"]
DOC_POOL = ["", ":meta public:", ":meta private:", "some docstring", "None"]
VAL_POOL = ["None", "42", "'s'", "obj", ""]


def _distinct_sublist(rng, k):
    pool = list(NAME_POOL)
    rng.shuffle(pool)
    return pool[:k]


def _mk_fns(rng):
    # val and doc are per-name maps over the whole name pool (total functions)
    vmap = {n: rng.choice(VAL_POOL) for n in NAME_POOL}
    dmap = {n: rng.choice(DOC_POOL) for n in NAME_POOL}
    return (lambda n: vmap[n]), (lambda n: dmap[n])


def _edge_cases():
    cases = []
    val = lambda n: "None"
    doc = lambda n: ":meta public:" if n == "_PUBLIC_CONSTANT" else ""
    # F2P scenario: an underscore-prefixed name documented :meta public: is
    # collected carrying its comment (want_all, no __all__).
    cases.append((True, None, [], ["_PUBLIC_CONSTANT", "_public_function"], [], val, doc))
    # explicit-name request collects the documented entry with its comment.
    cases.append((False, None, ["_PUBLIC_CONSTANT", "_public_function"],
                  ["_PUBLIC_CONSTANT", "_public_function"], [], val, doc))
    # __all__ present: names not listed get skipped=True, comments preserved.
    cases.append((True, ["a"], [], ["a", "_PUBLIC_CONSTANT"], [], val, doc))
    # empty __all__ behaves like no export list.
    cases.append((True, [], [], ["a", "b"], [], val, doc))
    # annotation-only member not in dir gets the sentinel value None + comment.
    cases.append((True, None, [], ["a"], ["a", "_b"], val,
                  lambda n: ":meta private:" if n == "_b" else ""))
    # explicit-name request for an absent name silently drops it.
    cases.append((False, None, ["nope", "a"], ["a", "b"], [], val, doc))
    return cases


def _rand_case(rng):
    want_all = rng.random() < 0.6
    if rng.random() < 0.4:
        all_names = None
    else:
        all_names = _distinct_sublist(rng, rng.randint(0, 4))
    memberlist = [rng.choice(NAME_POOL) for _ in range(rng.randint(0, 4))]
    dir_names = _distinct_sublist(rng, rng.randint(0, 6))
    annot_names = _distinct_sublist(rng, rng.randint(0, 4))
    val, doc = _mk_fns(rng)
    return (want_all, all_names, memberlist, dir_names, annot_names, val, doc)


def main() -> int:
    checked = 0
    for case in _edge_cases():
        d = disagree(case)
        if d:
            print(f"DISAGREE edge: case={d[0]} oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        case = _rand_case(rng)
        d = disagree(case)
        if d:
            print(f"DISAGREE fuzz: case={d[0]} oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
