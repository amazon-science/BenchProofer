#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13033.

The bundle models ONE decision: the default-ordering-expansion guard in
`SQLCompiler.find_ordering_name` (`django/db/models/sql/compiler.py`). Its Lean
implementation (`implementation_orderingExpandsRelation`) decides whether
ordering a queryset by a related-field lookup expands into the related model's
default ordering, returning a bool:

    last = path.split("__")[-1]
    return (field_is_relation and related_has_ordering
            and (field_attr != last) and (path != "pk"))

This script transliterates that R/I impl into Python (`shadow_decide`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH guard — the third conjunct compares the field's stored attribute
against the lookup path's FINAL SEGMENT (`pieces[-1]`), NOT the whole path.

We do NOT stand up Django's ORM / query compiler (heavy; the modeled value is a
pure boolean decision over four already-resolved observations). Both legs are
total functions over the modeled abstraction, so the edge set EXHAUSTIVELY
enumerates the modeled input space (is_relation × has_ordering × attname ∈
{None, a value matching / not matching the final segment} × a set of single- and
multi-segment lookup paths including the `pk` shortcut); the fuzz loop
additionally samples random structured paths. The discriminating case — a
multi-segment path whose final segment equals the field's attname (e.g.
`record__root_id` with attname `root_id`) — is covered: oracle (post-patch)
returns `False` (compare against `root_id`), whereas comparing against the whole
path would return `True` (that is the PRE-patch behavior).

stdlib-only. Pinned seed: 13033 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 13033
N = 120_000


def last_segment(path):
    # pieces = name.split('__'); pieces[-1]  (str.split never yields []).
    return path.split("__")[-1]


# --- ORACLE: the post-patch find_ordering_name guard, faithful replica --------
def oracle_decide(field_is_relation, related_has_ordering, field_attr, path):
    # field.is_relation and opts.ordering
    #   and getattr(field,'attname',None) != pieces[-1] and name != 'pk'
    return bool(
        field_is_relation
        and related_has_ordering
        and (field_attr != last_segment(path))
        and (path != "pk")
    )


# --- shadow of implementation_orderingExpandsRelation (the R/I leg) ------------
# Mirrors Solution.lean op-for-op. `field_attr` is None (no attname) or a str;
# the Lean `Option String` inequality `none != some _` is always true, matching
# Python's `None != "<str>"`.
def shadow_decide(field_is_relation, related_has_ordering, field_attr, path):
    last = last_segment(path)
    if field_is_relation and related_has_ordering and (field_attr != last) and (path != "pk"):
        return True
    return False


def disagree(fr, ro, fa, path):
    got = oracle_decide(fr, ro, fa, path)
    want = shadow_decide(fr, ro, fa, path)
    if got != want:
        return (fr, ro, fa, path, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0
    BOOLS = (False, True)
    SEGS = ("id", "root_id", "author", "editor", "editor_id")
    # attname candidates: None, plus values that may or may not equal a segment.
    ATTNS = (None, "id", "root_id", "editor_id", "author", "nomatch")
    # lookup paths: single- and multi-segment, plus the pk shortcut.
    PATHS = (
        "pk",
        "id",
        "root_id",
        "author",
        "editor_id",
        "record__root",
        "record__root_id",
        "author__editor",
        "author__editor_id",
        "a__b__c__editor_id",
        "",
    )

    # Edge set = EXHAUSTIVE over the modeled abstraction.
    for fr, ro, fa, path in itertools.product(BOOLS, BOOLS, ATTNS, PATHS):
        d = disagree(fr, ro, fa, path)
        if d:
            print(f"DISAGREE exhaustive fr={d[0]} ro={d[1]} attr={d[2]!r} "
                  f"path={d[3]!r}: oracle={d[4]} shadow={d[5]}")
            print("status=fail")
            return 1
        checked += 1

    # Redundant random fuzz over assembled multi-segment paths.
    rnd = _lcg(SEED)
    seg_alpha = SEGS + ("x", "y", "twoval", "oneval", "record", "root", "pk")
    for _ in range(N):
        def pick(seq):
            return seq[next(rnd) % len(seq)]
        nseg = 1 + (next(rnd) % 4)
        path = "__".join(pick(seg_alpha) for _ in range(nseg))
        fr = bool(next(rnd) & 1)
        ro = bool(next(rnd) & 1)
        fa = pick(ATTNS)
        d = disagree(fr, ro, fa, path)
        if d:
            print(f"DISAGREE fuzz fr={d[0]} ro={d[1]} attr={d[2]!r} "
                  f"path={d[3]!r}: oracle={d[4]} shadow={d[5]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
