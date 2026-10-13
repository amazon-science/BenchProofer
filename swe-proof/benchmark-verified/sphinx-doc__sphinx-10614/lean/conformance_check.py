#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-10614.

The bundle models ONE behavior: the URL-map construction loop inside
`html_visit_inheritance_diagram` (`sphinx/ext/inheritance_diagram.py`). For a
diagram node, this loop walks the pending cross-reference children and builds a
`urls` dict from a key to the link string recorded for that node, branching on
the graphviz output format ('SVG' vs the raster default) and on whether each
child has a resolved `refuri`, an in-page `refid`, or neither.

Standing up a full Sphinx HTML builder, environment, and graphviz just to drive
the real loop is heavy and unnecessary: the modeled value is a PURE function of
each child's observable attributes plus the SVG flag and the current document
name. So the ORACLE below is a faithful in-process replica of the POST-PATCH
loop (the exact patched control flow: no '../' prefix in either SVG branch; the
external-reference key is `refuri.rsplit('#', 1)[-1]`; the internal key is the
title), and the SHADOW is the op-for-op transliteration of
`implementation_buildUrls` (`entryFor` per child via `uriTail`), per
refinement.md.

The Lean model returns the entries as an ORDERED LIST of (key, url) pairs, while
the real loop builds a `dict` (`urls[key] = url`). The list -> dict step is the
type-refinement R declared in mapping.md / refinement.md. To validate THAT
refinement faithfully (not just list-vs-list), the ORACLE builds a real `dict`
with exact Python semantics (last write wins per key, first-occurrence insertion
order), and we compare `dict(shadow_list)` against it. This is faithful even when
two children share a key: Python's dict collapse and `dict(...)` over the shadow
list collapse identically (both keep the last value at the first position), so a
genuine divergence would still be caught.

stdlib-only. Pinned seed: 10614 (also in mapping.md).
"""
import random
import sys

SEED = 10614
N = 120_000


# --- ORACLE: faithful in-process replica of the PATCHED loop -----------------
# Mirrors, per child:
#   if child.get('refuri') is not None:
#       if not child.get('internal', True):
#           refname = child['refuri'].rsplit('#', 1)[-1]
#       else:
#           refname = child['reftitle']
#       urls[refname] = child.get('refuri')
#   elif child.get('refid') is not None:
#       if graphviz_output_format == 'SVG':
#           urls[reftitle] = current_filename + '#' + refid
#       else:
#           urls[reftitle] = '#' + refid
def oracle_dict(is_svg, current_filename, children):
    urls = {}
    for c in children:
        refuri, refid, reftitle, internal = c
        if refuri is not None:
            if not internal:
                refname = refuri.rsplit('#', 1)[-1]
            else:
                refname = reftitle
            urls[refname] = refuri
        elif refid is not None:
            if is_svg:
                urls[reftitle] = current_filename + '#' + refid
            else:
                urls[reftitle] = '#' + refid
        # neither refuri nor refid -> contributes nothing
    return urls


# --- SHADOW of implementation_buildUrls (the R/I leg) ------------------------
def _uri_tail(s):
    # uriTail: trailing component after the final '#'; no '#' -> whole string.
    parts = s.split('#')
    return parts[-1]


def shadow_entries(is_svg, current_filename, children):
    urls = []
    for c in children:
        refuri, refid, reftitle, internal = c
        if refuri is not None:
            refname = reftitle
            if not internal:
                refname = _uri_tail(refuri)
            urls = urls + [(refname, refuri)]
        else:
            if refid is not None:
                if is_svg:
                    urls = urls + [(reftitle, current_filename + '#' + refid)]
                else:
                    urls = urls + [(reftitle, '#' + refid)]
                # else: pure ()
    return urls


def disagree(is_svg, current_filename, children):
    # Oracle: the real post-patch dict (last-write-wins, first-occurrence order).
    got = list(oracle_dict(is_svg, current_filename, children).items())
    # Shadow: collapse the Lean ordered-list result through Python dict semantics
    # (this IS the list->dict refinement R declared in refinement.md).
    want = list(dict(shadow_entries(is_svg, current_filename, children)).items())
    if got != want:
        return ((is_svg, current_filename, children), got, want)
    return None


# pools
URI_POOL = [
    None, "foo.html", "../foo.html", "my_package/my_class_1.html#my_package.MyClass1",
    "https://example.org/foo.html#subdir.other.Bob", "a#b#c", "#frag", "nohash",
    "", "x.html#", "deep/path/page.html#anchor.Name",
]
RID_POOL = [None, "test.Foo", "id1", "subdir.other.Bob", "", "a.b.c", "x"]
TITLE_POOL = ["test.Foo", "subdir.other.Bob", "Class", "a.B", "", "MyClass1"]
FN_POOL = ["index", "subdir/index", "my_package/index", "", "a/b/c"]


def _rand_child(rng):
    # refuri may be None; refid may be None; both-None exercises the drop path.
    refuri = rng.choice(URI_POOL)
    refid = rng.choice(RID_POOL)
    reftitle = rng.choice(TITLE_POOL)
    internal = rng.choice([True, False])
    return (refuri, refid, reftitle, internal)


def main() -> int:
    checked = 0

    # structured edge cases: single-child, every (uri/refid/neither) x svg x internal
    edge_children = [
        (None, None, "test.Foo", True),
        (None, "test.Foo", "test.Foo", True),
        (None, "test.Foo", "test.Foo", False),
        ("p/q.html#X", None, "test.Foo", True),
        ("p/q.html#X", None, "test.Foo", False),
        ("https://example.org/foo.html#subdir.other.Bob", None, "subdir.other.Bob", False),
        ("nohash", None, "T", False),
        ("nohash", None, "T", True),
        # refuri present AND refid present -> refuri branch wins (elif)
        ("u.html#a", "rid", "Title", True),
        ("u.html#a", "rid", "Title", False),
    ]
    for is_svg in (True, False):
        for fn in FN_POOL:
            for ch in edge_children:
                d = disagree(is_svg, fn, [ch])
                if d:
                    print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
                    print("status=fail")
                    return 1
                checked += 1

    # multi-child edge cases incl. KEY COLLISIONS (dict collapse must match)
    collision_children = [
        [("u1.html#a", None, "T", True), ("u2.html#b", None, "T", True)],   # same title key
        [(None, "r1", "T", True), (None, "r2", "T", True)],                  # same refid key
        [("x.html#Bob", None, "T", False), ("y.html#Bob", None, "Q", False)],# same uriTail key
        [("a.html", None, "T", True), (None, "rid", "T", True)],             # refuri then refid, same key
        [(None, "rid", "T", True), ("a.html", None, "T", True)],             # refid then refuri, same key
    ]
    for is_svg in (True, False):
        for fn in FN_POOL:
            for chs in collision_children:
                d = disagree(is_svg, fn, chs)
                if d:
                    print(f"DISAGREE collision {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
                    print("status=fail")
                    return 1
                checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        is_svg = rng.choice([True, False])
        fn = rng.choice(FN_POOL)
        n = rng.randint(0, 5)
        children = [_rand_child(rng) for _ in range(n)]
        d = disagree(is_svg, fn, children)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
