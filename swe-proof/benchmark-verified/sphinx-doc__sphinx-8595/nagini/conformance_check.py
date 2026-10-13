#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8595 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert incl. the ghost Asserts inside the
loop) stripped; every executable statement is otherwise byte-identical. The
@Pure helpers (`contains`, `exclusion_flags`) copy over as plain functions on
top of a tuple-backed PSeq shim (drop/take/len/index/+/==). There are no
@ContractOnly callees in this bundle (no consumed axioms).

ORACLE: the REAL repo function the model models per mapping.md —
`sphinx.ext.autodoc.ModuleDocumenter.get_object_members(want_all=True)`,
imported from /testbed (the gate applies the diff before this script runs;
this script never applies any diff itself). The method is driven through a
minimal subclass that supplies only the two things the modelled path reads:
the upstream discovered-member dict (the result of `get_module_members`,
which mapping.md classifies as upstream input, not part of the modelled
behaviour) and the module's optional export list attribute. The inherited
`get_object_members` body — the code under specification — runs unmodified.

Type bridge (mapping.md section 2):
  - the optional export list Optional[Sequence[str]] -> (all_present: bool,
    all_names: List[int]): attribute None -> all_present=False, all_names=[];
    a declared list/tuple (possibly empty) -> all_present=True, all_names =
    the interned integer ids of its entries;
  - member/export name str -> int identifier via per-case interning (equal
    strings <-> equal ids; only name equality is observed, so the bridge is
    exact);
  - the member dict -> two index-aligned lists in dict iteration order:
    member_names (the ObjectMember name ids, read-only) and excluded (the
    per-member exclusion flags, all False on entry per the ObjectMember
    constructor default — this satisfies the model's cleared-flags Requires
    by construction);
  - the returned Tuple[bool, members]: the first element diffs against the
    model's Result(); the members' final per-member flags diff against the
    shadow's excluded carrier; member names and count must come back
    unchanged (the preserved-carrier Ensures).

Member names are unique per input (they are dict keys in the real callee);
export lists may contain duplicates and names absent from the member set.
Both str-shaped and int-shaped name pools are exercised (the bridge interns
either into ids).

>= 1e5 Requires-satisfying inputs: structured boundary cases (absent /
empty-present / disjoint / overlapping / superset export lists, empty member
sets, duplicate export entries, tuple-shaped export lists) plus 100000 fuzz
cases. Pinned fuzz seed: 85950.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; no hypothesis needed).
"""
import json
import random
import sys

SEED = 85950
N_FUZZ = 100_000


# --- PSeq / ToSeq shim: pure Viper sequences as plain tuples ------------------

class PSeq(tuple):
    def __new__(cls, *elems):
        return super().__new__(cls, elems)

    def drop(self, n):
        return PSeq(*tuple.__getitem__(self, slice(n, None)))

    def take(self, n):
        return PSeq(*tuple.__getitem__(self, slice(None, n)))

    def __add__(self, other):
        return PSeq(*(tuple.__add__(self, tuple(other))))


def ToSeq(xs):
    return PSeq(*xs)


# --- pure region of model.py, contracts stripped ------------------------------

def contains(names, v):
    if len(names) == 0:
        return False
    return names[0] == v or contains(names.drop(1), v)


def exclusion_flags(member_names, all_names):
    if len(member_names) == 0:
        return PSeq(False).take(0)
    return (PSeq(not contains(all_names, member_names[0])) +
            exclusion_flags(member_names.drop(1), all_names))


# --- impl region of model.py, verbatim, contract calls stripped ---------------

def select_module_members(member_names, excluded, all_present, all_names):
    if not all_present:
        # for implicit module members, every discovered member is a candidate:
        # none is excluded (the flags are already clear), and implicit
        # membership is signalled.
        return True
    else:
        seq = ToSeq(all_names)
        i = len(excluded)
        while i > 0:
            c = member_names[i - 1]
            if not contains(seq, c):
                excluded[i - 1] = True
            else:
                excluded[i - 1] = False
            i = i - 1
        return False
    # (the Invariant/Assert ghost statements of the verified loop are proof
    # bookkeeping only and are stripped; no executable statement depended on
    # them)


# --- bridge + differential check ----------------------------------------------

def intern_ids(*name_lists):
    """Per-case interning: equal names <-> equal integer identifiers."""
    table = {}
    out = []
    for names in name_lists:
        ids = []
        for n in names:
            if n not in table:
                table[n] = len(table)
            ids.append(table[n])
        out.append(ids)
    return out


def real_outcome(ModuleDocumenter, ObjectMember, member_names, all_value):
    """Run the REAL inherited get_object_members on the want_all=True path.
    The subclass supplies only the upstream inputs (the discovered-member
    dict and the export-list attribute); the method body under test is the
    unmodified repo code."""
    class _Probe(ModuleDocumenter):
        def __init__(self, members_dict, all_val):
            self._members_dict = members_dict
            self.__all__ = all_val

        def get_module_members(self):
            return self._members_dict

    members_dict = {n: ObjectMember(n, object()) for n in member_names}
    probe = _Probe(members_dict, all_value)
    flag, returned = probe.get_object_members(True)
    return flag, list(returned)


def check_one(ModuleDocumenter, ObjectMember, member_names, all_value):
    """One differential probe. member_names: unique str/int names (dict-key
    faithful); all_value: None or a list/tuple of names (duplicates allowed)."""
    export_names = list(all_value) if all_value is not None else []
    member_ids, all_ids = intern_ids(member_names, export_names)
    all_present = all_value is not None

    # shadow: cleared flags on entry (the model's Requires; matches the
    # ObjectMember constructor default in the real callee)
    excluded = [False] * len(member_ids)
    shadow_flag = select_module_members(member_ids, excluded,
                                        all_present, all_ids)

    real_flag, returned = real_outcome(ModuleDocumenter, ObjectMember,
                                       member_names, all_value)
    real_skipped = [m.skipped for m in returned]
    real_names = [m.__name__ for m in returned]

    problems = []
    if bool(real_flag) != bool(shadow_flag):
        problems.append("discriminating bool: shadow=%r real=%r"
                        % (shadow_flag, real_flag))
    if real_skipped != excluded:
        problems.append("exclusion flags: shadow=%r real=%r"
                        % (excluded, real_skipped))
    if real_names != list(member_names):
        problems.append("member set not preserved: sent=%r got=%r"
                        % (list(member_names), real_names))
    if problems:
        return ("DISAGREEMENT\n  member_names=%r\n  export_list=%r\n  %s"
                % (list(member_names), all_value, "\n  ".join(problems)))
    return None


def boundary_cases():
    """Structured cases covering both branches and the flag vector shapes."""
    cases = []
    # absent export list: implicit membership, nothing excluded
    cases.append((["foo", "bar", "baz"], None))
    cases.append(([], None))
    cases.append((["only"], None))
    # PRESENT but EMPTY export list: everything excluded (the crux shape)
    cases.append((["foo", "bar", "baz"], []))
    cases.append((["foo", "bar", "baz"], ()))
    cases.append(([], []))
    cases.append((["x"], []))
    # all members listed: nothing excluded
    cases.append((["foo", "bar", "baz"], ["foo", "bar", "baz"]))
    cases.append((["a"], ["a"]))
    # partial overlap
    cases.append((["foo", "bar", "baz"], ["bar"]))
    cases.append((["foo", "bar", "baz"], ["baz", "foo"]))
    # disjoint: everything excluded
    cases.append((["foo", "bar", "baz"], ["zzz"]))
    cases.append((["m1", "m2"], ["x", "y", "z"]))
    # export list superset of members / names not in the member set
    cases.append((["a"], ["a", "b", "c"]))
    cases.append(([], ["ghost"]))
    # duplicate entries in the export list
    cases.append((["foo", "bar"], ["foo", "foo", "foo"]))
    cases.append((["foo"], ["bar", "bar"]))
    # tuple-shaped export list
    cases.append((["foo", "bar"], ("foo",)))
    # underscore / dunder-ish names (plain data here; membership is equality)
    cases.append((["_private", "__weird__", "pub"], ["pub", "_private"]))
    # single member both ways
    cases.append((["solo"], ["solo"]))
    cases.append((["solo"], ["other"]))
    return cases


def main():
    # REAL repo symbols (the module the model models, per mapping.md):
    from sphinx.ext.autodoc import ModuleDocumenter, ObjectMember

    checked = 0
    n_boundary = 0
    for member_names, all_value in boundary_cases():
        err = check_one(ModuleDocumenter, ObjectMember,
                        member_names, all_value)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    str_pool = ["foo", "bar", "baz", "qux", "_x", "A", "zz", "m1", "m2",
                "__d__", "CamelCase", "with space", "unicode_é"]
    for _ in range(N_FUZZ):
        use_str = rng.random() < 0.5
        pool = str_pool if use_str else list(range(12))
        nm = rng.randint(0, 8)
        # member names are dict keys in the real callee: sample without
        # replacement so each case is dict-faithful
        member_names = rng.sample(pool, min(nm, len(pool)))
        r = rng.random()
        if r < 0.25:
            all_value = None                       # absent
        elif r < 0.40:
            all_value = [] if rng.random() < 0.5 else ()   # present, empty
        else:
            na = rng.randint(1, 6)
            exports = [rng.choice(pool) for _ in range(na)]  # dups allowed
            all_value = tuple(exports) if rng.random() < 0.3 else exports
        err = check_one(ModuleDocumenter, ObjectMember,
                        member_names, all_value)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real module-member selection on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
